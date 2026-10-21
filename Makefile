PYTHON ?= python

.PHONY: install backend frontend test cpp clean

install:
	$(PYTHON) -m pip install -r backend/requirements.txt -r ml/requirements.txt

backend:
	uvicorn app.main:app --reload --app-dir backend

frontend:
	cd frontend && npm install && npm run dev

test:
	pytest backend/tests ml/tests tests

cpp:
	cmake -S scoring-engine -B scoring-engine/build
	cmake --build scoring-engine/build --config Release

clean:
	cmake --build scoring-engine/build --target clean 2>NUL || exit 0
