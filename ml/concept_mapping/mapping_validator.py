"""Validation rules for generated or imported concept crosswalks."""

from __future__ import annotations

from collections.abc import Collection

from .text_cleaner import canonical_key


def validate_mapping(
    mapping: dict[str, list[str]],
    *,
    valid_targets: Collection[str] | None = None,
    maximum_targets: int = 10,
) -> list[str]:
    """Report blank, duplicate, self-referential, unknown, or excessive mappings."""
    errors: list[str] = []
    normalized_sources: set[str] = set()
    normalized_valid = {canonical_key(item) for item in valid_targets} if valid_targets is not None else None
    for source, targets in mapping.items():
        source_key = canonical_key(source)
        if not source_key:
            errors.append("source concept cannot be empty")
        elif source_key in normalized_sources:
            errors.append(f"duplicate normalized source: {source}")
        normalized_sources.add(source_key)
        if len(targets) > maximum_targets:
            errors.append(f"too many targets for {source}: {len(targets)} > {maximum_targets}")
        target_keys = [canonical_key(target) for target in targets]
        if any(not target for target in target_keys):
            errors.append(f"blank target for {source}")
        if len(target_keys) != len(set(target_keys)):
            errors.append(f"duplicate targets for {source}")
        if source_key and source_key in target_keys:
            errors.append(f"self mapping for {source}")
        if normalized_valid is not None:
            unknown = sorted(target for target, key in zip(targets, target_keys, strict=False) if key not in normalized_valid)
            if unknown:
                errors.append(f"unknown targets for {source}: {', '.join(unknown)}")
    return errors
