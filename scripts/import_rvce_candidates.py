"""Submit extracted RVCE candidates to the admin-only batch import API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    """Submit locally validated RVCE candidate batches to the administrator-only API."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000/api/v1/catalog/rvce/courses/import")
    parser.add_argument("--token", required=True, help="Admin bearer token")
    parser.add_argument("--records", type=Path, default=Path("database/rvce_course_candidates.json"))
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 500:
        raise SystemExit("batch-size must be between 1 and 500")
    records = json.loads(args.records.read_text(encoding="utf-8"))
    submitted = 0
    for start in range(0, len(records), args.batch_size):
        body = json.dumps(records[start : start + args.batch_size]).encode("utf-8")
        request = Request(args.api, data=body, method="POST", headers={
            "Authorization": f"Bearer {args.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            with urlopen(request, timeout=30) as response:
                created = json.loads(response.read().decode("utf-8"))
                submitted += len(created)
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")[:2000]
            raise SystemExit(f"Import batch failed with HTTP {exc.code}: {message}") from exc
        except URLError as exc:
            raise SystemExit(f"Could not reach RVCE import API: {exc.reason}") from exc
    print(f"Imported {submitted} RVCE candidate records for academic review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
