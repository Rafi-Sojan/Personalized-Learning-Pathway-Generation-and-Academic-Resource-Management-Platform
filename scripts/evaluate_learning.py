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
    parser.add_argument("--minimum", action="append", default=[], metavar="METRIC=VALUE", help="Fail unless a reported metric meets the minimum value.")
    args = parser.parse_args()
    cases = json.loads(args.benchmark.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise SystemExit("Benchmark file must contain a JSON array")
    result = evaluate_cases(cases)
    print(json.dumps(result, indent=2, sort_keys=True))
    failures: list[str] = []
    for minimum in args.minimum:
        try:
            name, raw_value = minimum.split("=", 1)
            threshold = float(raw_value)
        except ValueError as exc:
            raise SystemExit(f"Invalid --minimum value: {minimum}") from exc
        if name not in result:
            failures.append(f"unknown metric: {name}")
        elif result[name] < threshold:
            failures.append(f"{name}={result[name]:.4f} is below {threshold:.4f}")
    if failures:
        print("Evaluation gate failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
