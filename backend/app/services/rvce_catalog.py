"""Read-only RVCE catalog access for the API and import tooling."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from ml.preprocessing.rvce_catalog import load_rvce_catalog


@lru_cache(maxsize=1)
def get_rvce_catalog() -> dict[str, Any]:
    """Load the repository's validated RVCE manifest from supported package layouts."""
    service_path = Path(__file__).resolve()
    candidates = (
        service_path.parents[3] / "database" / "rvce_catalog.json",
        service_path.parents[2] / "database" / "rvce_catalog.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return load_rvce_catalog(candidate)
    raise FileNotFoundError("RVCE catalog manifest was not packaged")
