"""Source-aware identities for versioned syllabus concept maps."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from .text_cleaner import canonical_key


@dataclass(frozen=True)
class SourceConceptIdentity:
    """Distinguish repeated labels by their printed unit and parent heading."""

    name: str
    unit: str
    parent: str


def source_concept_identity(name: str, unit_label: str | None, parent_label: str | None) -> SourceConceptIdentity:
    """Create a conservative identity from normalized source hierarchy fields."""
    return SourceConceptIdentity(
        name=canonical_key(name),
        unit=canonical_key(unit_label or ""),
        parent=canonical_key(parent_label or ""),
    )


def unique_name_keys(names: Iterable[str]) -> set[str]:
    """Return normalized names that occur exactly once in the submitted source."""
    counts = Counter(canonical_key(name) for name in names if canonical_key(name))
    return {name for name, count in counts.items() if count == 1}
