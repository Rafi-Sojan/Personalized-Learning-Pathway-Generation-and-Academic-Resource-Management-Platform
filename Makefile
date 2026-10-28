PYTHON ?= python

.PHONY: install backend frontend test quality security cpp compose-up compose-down migrate clean

install:
	$(PYTHON) -m pip install -r backend/requirements.txt -r ml/requirements.txt

backend:
	uvicorn app.main:app --reload --app-dir backend

frontend:
	cd frontend && npm install && npm run dev

compose-up:
	docker compose up --build

compose-down:
	docker compose down

migrate:
	alembic -c backend/alembic.ini upgrade head

test:
	pytest backend/tests ml/tests tests

quality:
	python -m compileall -q backend ml tests scripts
	python -m ruff check backend ml tests
	python -m mypy backend/app --ignore-missing-imports
	pytest backend/tests ml/tests tests
	cd frontend && npm ci && npm run build && npm audit --audit-level=high

security:
	pip-audit -r backend/requirements.txt -r backend/requirements-ocr.txt -r backend/requirements-storage.txt -r ml/requirements.txt
	cd frontend && npm audit --audit-level=high

compose-smoke:
	docker compose up --build --detach
	curl --fail http://localhost:8000/health/ready
	curl --fail http://localhost:5173/health
	docker compose down --volumes

cpp:
	cmake -S scoring-engine -B scoring-engine/build
	cmake --build scoring-engine/build --config Release

clean:
	cmake --build scoring-engine/build --target clean 2>NUL || exit 0
