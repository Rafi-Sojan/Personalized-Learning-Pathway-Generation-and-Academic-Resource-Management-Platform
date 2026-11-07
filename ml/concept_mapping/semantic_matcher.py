"""Explainable, corpus-aware matching between questions and syllabus concepts.

The engine deliberately avoids a network model dependency.  It combines lexical
rarity, phrase/acronym evidence, conservative morphology, hierarchy context, and
OCR-tolerant character similarity.  More importantly, it can abstain: a weak or
ambiguous suggestion remains unmapped until a reviewer selects a concept.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import math
from typing import Literal

from .text_cleaner import canonical_key, clean_text


MATCHER_VERSION = "rvce-hybrid-lexical-v2"

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "briefly", "by", "can", "define",
    "describe", "discuss", "do", "does", "draw", "elaborate", "explain", "for", "from",
    "give", "how", "illustrate", "in", "is", "it", "list", "mention", "of", "on", "or",
    "outline", "show", "state", "the", "to", "using", "what", "when", "where", "which",
    "why", "with", "write",
}


@dataclass(frozen=True)
class ConceptDocument:
    """Describe one reviewable syllabus concept and its matching context."""

    concept_id: str
    name: str
    aliases: tuple[str, ...] = ()
    parent_name: str | None = None
    unit_label: str | None = None


@dataclass(frozen=True)
class MatcherConfig:
    """Control conservative acceptance without changing feature definitions."""

    minimum_score: float = 0.62
    minimum_margin: float = 0.08
    high_confidence_score: float = 0.88
    high_confidence_margin: float = 0.04
    top_k: int = 5
    max_prompt_tokens: int = 512


@dataclass(frozen=True)
class MatchCandidate:
    """Expose one ranked concept and the evidence contributing to its score."""

    concept_id: str
    name: str
    score: float
    coverage: float
    lexical_score: float
    phrase_score: float
    character_score: float
    context_score: float
    matched_terms: tuple[str, ...]
    evidence: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a bounded JSON-compatible representation for audit metadata."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "score": self.score,
            "matched_terms": list(self.matched_terms[:12]),
            "evidence": list(self.evidence[:6]),
        }


MatchStatus = Literal["matched", "ambiguous", "low_confidence", "no_candidates", "no_evidence"]


@dataclass(frozen=True)
class ConceptMatch:
    """Represent an accepted match or a reasoned decision to abstain."""

    status: MatchStatus
    concept_id: str | None
    label: str
    confidence: float | None
    margin: float | None
    candidates: tuple[MatchCandidate, ...]
    explanation: str
    model_version: str = MATCHER_VERSION

    def as_metadata(self) -> dict[str, object]:
        """Serialize model identity, decision evidence, and bounded alternatives."""
        return {
            "status": self.status,
            "model_version": self.model_version,
            "margin": self.margin,
            "explanation": self.explanation,
            "candidates": [candidate.as_dict() for candidate in self.candidates[:5]],
        }


@dataclass(frozen=True)
class _IndexedConcept:
    """Cache normalized fields used repeatedly while importing one paper."""

    source: ConceptDocument
    name_key: str
    name_tokens: tuple[str, ...]
    alias_keys: tuple[str, ...]
    alias_tokens: tuple[tuple[str, ...], ...]
    acronyms: tuple[str, ...]
    context_tokens: tuple[str, ...]
    context_acronyms: tuple[str, ...]
    term_frequency: Counter[str]
    length: int


def _stem(token: str) -> str:
    """Apply small, deterministic English inflections without a language model."""
    if len(token) > 5 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 6 and token.endswith("ing"):
        base = token[:-3]
        return base[:-1] if len(base) > 3 and base[-1:] == base[-2:-1] else base
    if len(token) > 5 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 5 and token.endswith("es") and not token.endswith(("ses", "xes")):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def topic_tokens(text: str, *, keep_stop_words: bool = False) -> tuple[str, ...]:
    """Tokenize technical text with conservative morphology and exam-word removal."""
    tokens: list[str] = []
    for token in clean_text(text).split():
        if not keep_stop_words and token in _STOP_WORDS:
            continue
        normalized = _stem(token)
        if normalized and (len(normalized) > 1 or normalized.isdigit()):
            tokens.append(normalized)
    return tuple(tokens)


def _acronym(tokens: Sequence[str]) -> str | None:
    """Derive common syllabus initialisms such as CNN, DBMS, or OS."""
    words = [token for token in tokens if token not in _STOP_WORDS and token.isalnum()]
    if 2 <= len(words) <= 8:
        value = "".join(word[0] for word in words)
        if 2 <= len(value) <= 10:
            return value
    return None


def _character_ngrams(value: str, size: int = 3) -> set[str]:
    """Build whitespace-insensitive n-grams for OCR-tolerant phrase comparison."""
    compact = value.replace(" ", "")
    if not compact:
        return set()
    if len(compact) <= size:
        return {compact}
    return {compact[index : index + size] for index in range(len(compact) - size + 1)}


def _dice(left: str, right: str) -> float:
    """Return Sørensen-Dice character similarity in the inclusive zero-to-one range."""
    a, b = _character_ngrams(left), _character_ngrams(right)
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


def _contains_phrase(text_key: str, phrase_key: str) -> bool:
    """Match a normalized phrase on token boundaries, never as a substring."""
    text_tokens = text_key.split()
    phrase_tokens = phrase_key.split()
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    width = len(phrase_tokens)
    return any(text_tokens[index : index + width] == phrase_tokens for index in range(len(text_tokens) - width + 1))


def _bounded_prompt(prompt: str, maximum_tokens: int) -> tuple[str, tuple[str, ...]]:
    """Normalize and cap untrusted question text before quadratic window scoring."""
    words = canonical_key(prompt).split()[:max(1, maximum_tokens)]
    prompt_key = " ".join(words)
    return prompt_key, topic_tokens(prompt_key)


def _best_character_window(prompt_tokens: Sequence[str], candidate_key: str, candidate_length: int) -> float:
    """Compare a concept with similarly sized prompt windows instead of whole questions."""
    if not prompt_tokens or not candidate_key:
        return 0.0
    best = 0.0
    lower = max(1, candidate_length - 1)
    upper = min(len(prompt_tokens), candidate_length + 2)
    for size in range(lower, upper + 1):
        for start in range(0, len(prompt_tokens) - size + 1):
            best = max(best, _dice(" ".join(prompt_tokens[start : start + size]), candidate_key))
    return best


class ConceptMatcher:
    """Rank a fixed syllabus corpus efficiently and abstain on uncertain results."""

    def __init__(self, concepts: Iterable[ConceptDocument], config: MatcherConfig | None = None) -> None:
        """Index distinct concept identifiers and compute corpus-level rarity weights."""
        self.config = config or MatcherConfig()
        unique: dict[str, ConceptDocument] = {}
        for document in concepts:
            if document.concept_id and canonical_key(document.name):
                unique.setdefault(document.concept_id, document)
        self._concepts = tuple(self._index(document) for document in unique.values())
        self._name_frequency = Counter(indexed.name_key for indexed in self._concepts)
        document_frequency: Counter[str] = Counter()
        for indexed in self._concepts:
            document_frequency.update(set(indexed.term_frequency))
        count = len(self._concepts)
        self._idf = {
            term: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }
        self._average_length = (
            sum(indexed.length for indexed in self._concepts) / count if count else 1.0
        )

    @staticmethod
    def _index(concept: ConceptDocument) -> _IndexedConcept:
        """Normalize one concept while keeping primary and contextual evidence separate."""
        name_key = canonical_key(concept.name)
        name_tokens = topic_tokens(concept.name)
        alias_keys = tuple(filter(None, (canonical_key(alias) for alias in concept.aliases)))
        alias_tokens = tuple(topic_tokens(alias) for alias in concept.aliases if canonical_key(alias))
        primary_acronym = _acronym(name_tokens)
        alias_acronyms = tuple(filter(None, (_acronym(tokens) for tokens in alias_tokens)))
        explicit_acronyms = tuple(
            key for key in alias_keys if " " not in key and 2 <= len(key) <= 10
        )
        context_tokens = topic_tokens(" ".join(filter(None, (concept.parent_name, concept.unit_label))))
        context_acronym = _acronym(topic_tokens(concept.parent_name or ""))
        weighted_tokens = [*name_tokens]
        for tokens in alias_tokens:
            weighted_tokens.extend(tokens)
        return _IndexedConcept(
            source=concept,
            name_key=name_key,
            name_tokens=name_tokens,
            alias_keys=alias_keys,
            alias_tokens=alias_tokens,
            acronyms=tuple(dict.fromkeys(filter(None, (primary_acronym, *alias_acronyms, *explicit_acronyms)))),
            context_tokens=context_tokens,
            context_acronyms=tuple(filter(None, (context_acronym,))),
            term_frequency=Counter(weighted_tokens),
            length=max(len(weighted_tokens), 1),
        )

    def _bm25(self, query: set[str], concept: _IndexedConcept) -> float:
        """Return a normalized BM25-style lexical relevance score."""
        if not query or not concept.term_frequency:
            return 0.0
        k1, b = 1.5, 0.75
        score = 0.0
        for term in query:
            frequency = concept.term_frequency.get(term, 0)
            if not frequency:
                continue
            denominator = frequency + k1 * (
                1 - b + b * concept.length / max(self._average_length, 1.0)
            )
            score += self._idf.get(term, 0.0) * frequency * (k1 + 1) / denominator
        return 1 - math.exp(-score / 2.0)

    def _coverage(self, query: set[str], terms: Sequence[str]) -> tuple[float, tuple[str, ...]]:
        """Measure how much discriminative concept wording occurs in the question."""
        unique_terms = set(terms)
        overlap = unique_terms & query
        denominator = sum(self._idf.get(term, 1.0) for term in unique_terms)
        numerator = sum(self._idf.get(term, 1.0) for term in overlap)
        return (numerator / denominator if denominator else 0.0), tuple(sorted(overlap))

    def _score(self, prompt_key: str, prompt_tokens: tuple[str, ...], concept: _IndexedConcept) -> MatchCandidate:
        """Combine independent signals and retain a human-readable evidence trail."""
        query = set(prompt_tokens)
        variants = (concept.name_tokens, *concept.alias_tokens)
        variant_scores = [self._coverage(query, terms) for terms in variants if terms]
        coverage, matched_terms = max(variant_scores, default=(0.0, ()), key=lambda item: item[0])
        lexical = self._bm25(query, concept)

        primary_phrase = _contains_phrase(prompt_key, concept.name_key)
        alias_phrase = any(_contains_phrase(prompt_key, alias) for alias in concept.alias_keys)
        prompt_raw_tokens = set(prompt_key.split())
        acronym_match = next((value for value in concept.acronyms if value in prompt_raw_tokens), None)
        phrase = 1.0 if primary_phrase and len(concept.name_tokens) > 1 else 0.76 if primary_phrase else 0.92 if alias_phrase else 0.88 if acronym_match else 0.0

        character = max(
            [_best_character_window(prompt_tokens, concept.name_key, max(len(concept.name_tokens), 1))]
            + [
                _best_character_window(prompt_tokens, key, max(len(tokens), 1))
                for key, tokens in zip(concept.alias_keys, concept.alias_tokens, strict=False)
            ]
        )
        context_coverage, context_terms = self._coverage(query, concept.context_tokens)
        context_acronym = any(value in prompt_raw_tokens for value in concept.context_acronyms)
        context = max(context_coverage, 0.9 if context_acronym else 0.0)

        score = 0.36 * coverage + 0.21 * lexical + 0.21 * phrase + 0.11 * character + 0.11 * context
        if acronym_match:
            score = max(score, 0.78 + 0.06 * context)
        if coverage >= 0.999 and len(concept.name_tokens) > 1:
            score += 0.04
        if primary_phrase and len(concept.name_tokens) == 1 and len(query) <= 2:
            score = max(score, 0.66)
        if primary_phrase and context > 0:
            score += min(0.12, 0.18 * context)
        if len(concept.name_tokens) == 1 and len(query) > 2:
            score -= 0.08
        if primary_phrase and len(concept.name_tokens) == 1 and self._name_frequency[concept.name_key] == 1:
            score = max(score, 0.64)
        # A high character match can recover minor OCR/spelling damage, but it
        # cannot bypass the ambiguity margin applied by ``match``.
        if character >= 0.65 and coverage < 0.8:
            score = max(score, 0.58 + (character - 0.65) * 1.2)
        score = round(min(1.0, max(0.0, score)), 4)

        evidence: list[str] = []
        if primary_phrase:
            evidence.append("exact syllabus phrase")
        elif alias_phrase:
            evidence.append("exact alias phrase")
        if acronym_match:
            evidence.append(f"acronym {acronym_match.upper()}")
        if matched_terms:
            evidence.append(f"matched terms: {', '.join(matched_terms[:8])}")
        if context_terms or context_acronym:
            evidence.append("parent or unit context")
        if character >= 0.65 and coverage < 0.8:
            evidence.append("OCR-tolerant phrase similarity")
        return MatchCandidate(
            concept_id=concept.source.concept_id,
            name=concept.source.name,
            score=score,
            coverage=round(coverage, 4),
            lexical_score=round(lexical, 4),
            phrase_score=round(phrase, 4),
            character_score=round(character, 4),
            context_score=round(context, 4),
            matched_terms=matched_terms,
            evidence=tuple(evidence),
        )

    def rank(self, prompt: str, *, top_k: int | None = None) -> tuple[MatchCandidate, ...]:
        """Return deterministic candidates ordered by score, specificity, then ID."""
        prompt_key, prompt_tokens = _bounded_prompt(prompt, self.config.max_prompt_tokens)
        if not prompt_tokens or not self._concepts:
            return ()
        candidates = [self._score(prompt_key, prompt_tokens, concept) for concept in self._concepts]
        candidates.sort(
            key=lambda item: (-item.score, -item.coverage, -len(item.matched_terms), item.name.casefold(), item.concept_id)
        )
        limit = self.config.top_k if top_k is None else max(1, top_k)
        return tuple(candidate for candidate in candidates[:limit] if candidate.score > 0)

    def match(self, prompt: str) -> ConceptMatch:
        """Accept only a strong, separated first candidate; otherwise explain abstention."""
        if not self._concepts:
            return ConceptMatch("no_candidates", None, "Unmapped", None, None, (), "No verified syllabus concepts are available.")
        if not _bounded_prompt(prompt, self.config.max_prompt_tokens)[1]:
            return ConceptMatch("no_evidence", None, "Unmapped", None, None, (), "The question contains no meaningful matching terms.")
        candidates = self.rank(prompt)
        if not candidates:
            return ConceptMatch("no_evidence", None, "Unmapped", None, None, (), "No syllabus wording was found in the question.")
        best = candidates[0]
        runner_up = candidates[1].score if len(candidates) > 1 else 0.0
        margin = round(best.score - runner_up, 4)
        required_margin = (
            self.config.high_confidence_margin
            if best.score >= self.config.high_confidence_score
            else self.config.minimum_margin
        )
        if best.score < self.config.minimum_score:
            return ConceptMatch(
                "low_confidence", None, "Unmapped", best.score, margin, candidates,
                f"Best suggestion {best.name} scored {best.score:.2f}, below {self.config.minimum_score:.2f}.",
            )
        if margin < required_margin:
            return ConceptMatch(
                "ambiguous", None, "Unmapped", best.score, margin, candidates,
                f"Top suggestions are separated by only {margin:.2f}; review is required.",
            )
        return ConceptMatch(
            "matched", best.concept_id, best.name, best.score, margin, candidates,
            f"Selected {best.name} from {', '.join(best.evidence) or 'combined lexical evidence'}.",
        )


def similarity(left: str, right: str) -> float:
    """Return robust token Jaccard similarity for legacy crosswalk callers."""
    a, b = set(topic_tokens(left)), set(topic_tokens(right))
    return round(len(a & b) / len(a | b), 4) if a | b else 0.0


def topic_similarity(prompt: str, concept_name: str) -> float:
    """Return the v2 hybrid score for callers comparing a single concept."""
    matcher = ConceptMatcher([ConceptDocument("candidate", concept_name)])
    ranked = matcher.rank(prompt, top_k=1)
    return ranked[0].score if ranked else 0.0
