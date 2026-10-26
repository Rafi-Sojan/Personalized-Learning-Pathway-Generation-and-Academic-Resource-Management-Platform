"""Evaluate a JSON benchmark file.

Example case format:
[{"mapping": {"predicted": ["functions"], "expected": ["functions"]},
  "roadmap": {"completed": 3, "planned": 4},
  "ranking": {"recommended": ["functions"], "relevant": ["functions"], "k": 5}}]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.evaluation.benchmark import evaluate_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    args = parser.parse_args()
    cases = json.loads(args.benchmark.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise SystemExit("Benchmark file must contain a JSON array")
    print(json.dumps(evaluate_cases(cases), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
