from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import settings


def score_concept(difficulty: int, progress: float) -> float:
    """Fallback implementation matching the C++ engine's simple scoring contract."""
    return round((difficulty * 20) + max(0, 100 - progress) * 0.6, 2)


def rank_concepts(concepts: list[dict]) -> list[dict]:
    """Use the configured native scorer, falling back to the Python contract."""
    binary = Path(settings.scoring_engine_path)
    if binary.is_file():
        payload = "".join(f"{item['id']}|{int(item.get('difficulty', 1))}|{float(item.get('progress', 0))}|{int(bool(item.get('prerequisite_ready', True)))}\n" for item in concepts)
        try:
            completed = subprocess.run([str(binary), "--stdin"], input=payload, text=True, capture_output=True, timeout=5, check=True)
            return [{"id": row.split("|", 1)[0], "score": float(row.split("|", 1)[1])} for row in completed.stdout.splitlines() if "|" in row]
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return [{"id": item["id"], "score": score_concept(int(item.get("difficulty", 1)), float(item.get("progress", 0)))} for item in sorted(concepts, key=lambda value: score_concept(int(value.get("difficulty", 1)), float(value.get("progress", 0))), reverse=True)]
