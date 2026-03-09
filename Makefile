.PHONY: help dev index eval test lint clean

help:
	@echo ""
	@echo "RAG Documentation Assistant — Commands"
	@echo "======================================="
	@echo "  make dev      Start backend + frontend in dev mode"
	@echo "  make index    Ingest, chunk, embed and index all docs"
	@echo "  make eval     Run evaluation script against golden Q&A set"
	@echo "  make test     Run backend unit tests"
	@echo "  make lint     Lint backend Python code"
	@echo "  make clean    Remove generated data and vector DB"
	@echo ""

# ── Development ──────────────────────────────────────────────────────────────
dev:
	@echo "Starting backend..."
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev

dev-docker:
	docker-compose -f infra/docker-compose.yml up --build

# ── Pipeline ─────────────────────────────────────────────────────────────────
index:
	@echo "Running full ingestion + indexing pipeline..."
	cd backend && python -m ingestion.ingest_and_index --source-config ../config/sources.yaml

ingest:
	cd backend && python -m ingestion.ingest --source-config ../config/sources.yaml

# ── Evaluation ───────────────────────────────────────────────────────────────
eval:
	@echo "Running evaluation against golden Q&A set..."
	cd backend && python ../eval/run_eval.py

# ── Testing ──────────────────────────────────────────────────────────────────
test:
	cd backend && pytest tests/ -v --tb=short

test-cov:
	cd backend && pytest tests/ --cov=. --cov-report=term-missing

# ── Code Quality ─────────────────────────────────────────────────────────────
lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff format .

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean:
	@echo "Cleaning generated data..."
	rm -rf data/vectordb
	rm -rf data/staging.db
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

setup-backend:
	cd backend && pip install -r requirements.txt

setup-frontend:
	cd frontend && npm install

setup: setup-backend setup-frontend
	@echo "All dependencies installed."
