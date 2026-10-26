"""Create a PostgreSQL logical backup using pg_dump.

Usage: python scripts/backup_database.py [output-file]
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL must point to PostgreSQL for a logical backup")
    output = Path(sys.argv[1] if len(sys.argv) > 1 else f"backups/learning-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.dump")
    output.parent.mkdir(parents=True, exist_ok=True)
    pg_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    subprocess.run(["pg_dump", "--format=custom", "--file", str(output), pg_url], check=True)
    print(f"Created database backup: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
