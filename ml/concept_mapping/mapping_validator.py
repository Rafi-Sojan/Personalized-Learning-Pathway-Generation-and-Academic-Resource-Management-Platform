def validate_mapping(mapping: dict[str, list[str]]) -> list[str]:
    errors = []
    for source, targets in mapping.items():
        if not source.strip():
            errors.append("source concept cannot be empty")
        if len(targets) != len(set(targets)):
            errors.append(f"duplicate targets for {source}")
    return errors
