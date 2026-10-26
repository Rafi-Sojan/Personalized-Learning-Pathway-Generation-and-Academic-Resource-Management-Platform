"""Restore a PostgreSQL logical backup.

Usage: python scripts/restore_database.py path/to/backup.dump
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL must point to PostgreSQL for a restore")
    if len(sys.argv) != 2:
        raise SystemExit("Provide exactly one backup file")
    backup = Path(sys.argv[1]).resolve()
    if not backup.is_file():
        raise SystemExit(f"Backup file does not exist: {backup}")
    confirmation = input(f"Restore {backup} into DATABASE_URL? Type RESTORE to continue: ")
    if confirmation != "RESTORE":
        raise SystemExit("Restore cancelled")
    pg_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    subprocess.run(["pg_restore", "--clean", "--if-exists", "--dbname", pg_url, str(backup)], check=True)
    print("Database restore completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
