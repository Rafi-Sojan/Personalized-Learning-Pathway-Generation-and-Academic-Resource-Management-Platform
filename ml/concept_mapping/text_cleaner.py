"""Unicode-safe normalization shared by syllabus and question matching."""

from __future__ import annotations

import re
import unicodedata


_SPACE = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^a-z0-9\s]")


def normalize_unicode(text: str) -> str:
    """Return a stable Unicode representation without invisible formatting marks.

    Uploaded PDFs frequently contain ligatures, soft hyphens, non-breaking spaces,
    and presentation-form punctuation.  Normalizing those characters before any
    token comparison prevents visually identical syllabus phrases from receiving
    different identities while retaining the original source text elsewhere.
    """
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = normalized.replace("\u00ad", "").replace("\u200b", "")
    normalized = normalized.replace("&", " and ")
    # Preserve the meaning of common technical-language punctuation before the
    # generic punctuation pass (for example, C++ and C#).
    normalized = normalized.replace("++", " plus plus ").replace("#", " sharp ")
    return normalized


def clean_text(text: str) -> str:
    """Return lowercase, punctuation-free text with deterministic whitespace."""
    normalized = normalize_unicode(text)
    return _SPACE.sub(" ", _NON_WORD.sub(" ", normalized)).strip()


def canonical_key(text: str) -> str:
    """Return a compact identity key suitable for conservative exact reuse."""
    return " ".join(clean_text(text).split())
