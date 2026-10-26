"""Small dependency-free HTTP smoke/load test for a running API."""

from __future__ import annotations

import argparse
import concurrent.futures
import time
from urllib.request import Request, urlopen


def request_once(url: str) -> tuple[bool, float]:
    started = time.perf_counter()
    try:
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=10) as response:
            response.read(32)
            return response.status < 500, time.perf_counter() - started
    except Exception:
        return False, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/health")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    if args.requests < 1 or args.workers < 1:
        raise SystemExit("requests and workers must be positive")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(lambda _: request_once(args.url), range(args.requests)))
    successful = sum(1 for ok, _ in results if ok)
    latencies = sorted(duration for _, duration in results)
    percentile_index = min(len(latencies) - 1, int(len(latencies) * 0.95))
    print(f"successful={successful}/{args.requests} p95_ms={latencies[percentile_index] * 1000:.2f}")
    return 0 if successful == args.requests else 1


if __name__ == "__main__":
    raise SystemExit(main())
