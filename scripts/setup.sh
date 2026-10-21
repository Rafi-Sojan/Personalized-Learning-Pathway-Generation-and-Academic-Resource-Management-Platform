#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt -r ml/requirements.txt
echo "Backend dependencies installed. Run: uvicorn app.main:app --reload --app-dir backend"
