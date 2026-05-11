# BioLink Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help install dev test lint format clean docker-up docker-down

# Default target
help:
	@echo "BioLink Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install all dependencies"
	@echo "  make setup            Run initial setup (first time)"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start development environment"
	@echo "  make dev-backend      Start backend only"
	@echo "  make dev-frontend     Start frontend only"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-frontend    Run frontend tests"
	@echo "  make test-e2e         Run E2E tests"
	@echo "  make coverage         Generate coverage reports"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters"
	@echo "  make lint-backend     Run Python linters"
	@echo "  make lint-frontend    Run JS/TS linters"
	@echo "  make format           Format all code"
	@echo "  make format-backend   Format Python code"
	@echo "  make format-frontend  Format JS/TS code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start all Docker services"
	@echo "  make docker-down      Stop all Docker services"
	@echo "  make docker-build     Build all Docker images"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Run database migrations"
	@echo "  make db-seed          Seed database with test data"
	@echo "  make db-reset         Reset database"
	@echo ""
	@echo "Pipeline:"
	@echo "  make harmonize        Run full harmonization pipeline"
	@echo "  make stage-data       Stage CSV chunks for NiFi"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean build artifacts"
	@echo "  make pre-commit       Install and run pre-commit hooks"
	@echo "  make docs             Generate documentation"
	@echo "  make security-scan    Run security scans"

# ============================================
# Setup & Installation
# ============================================

install:
	@echo "Installing backend dependencies..."
	cd backend-py && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	npm install

setup:
	@echo "Running initial setup..."
	./bin/setup-and-test.sh

# ============================================
# Development
# ============================================

dev:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "Services starting..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend API: http://localhost:3001"
	@echo "API Docs: http://localhost:3001/api/docs"

dev-backend:
	@echo "Starting backend only..."
	cd backend-py && python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

dev-frontend:
	@echo "Starting frontend only..."
	npm run dev || npx vite

# ============================================
# Testing
# ============================================

test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend-py && pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	npm run test:unit || npx vitest run

test-e2e:
	@echo "Running E2E tests..."
	npx playwright test

coverage:
	@echo "Generating coverage reports..."
	cd backend-py && pytest tests/ --cov=app --cov-report=html --cov-report=xml
	npx vitest run --coverage || true

# ============================================
# Code Quality
# ============================================

lint: lint-backend lint-frontend

lint-backend:
	@echo "Running Python linters..."
	cd backend-py && ruff check .
	cd backend-py && mypy app/ --ignore-missing-imports || true

lint-frontend:
	@echo "Running JS/TS linters..."
	npx eslint src/ --ext .ts,.tsx || true
	
format: format-backend format-frontend

format-backend:
	@echo "Formatting Python code..."
	cd backend-py && black .
	cd backend-py && ruff check . --fix

format-frontend:
	@echo "Formatting JS/TS code..."
	npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"

# ============================================
# Docker
# ============================================

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

docker-clean:
	@echo "Cleaning Docker containers and volumes..."
	docker-compose down -v
	docker system prune -f

# ============================================
# Database
# ============================================

db-migrate:
	@echo "Running database migrations..."
	cd backend-py && python -m app.db_bootstrap

db-seed:
	@echo "Seeding database..."
	cd backend-py && python -m app.scripts.import_patients_csv

db-reset:
	@echo "Resetting database..."
	docker-compose restart postgres
	@echo "Waiting for PostgreSQL..."
	sleep 5
	$(MAKE) db-migrate
	$(MAKE) db-seed

stage-data:
	@echo "Staging CSV chunks for NiFi ingestion..."
	python3 nifi/scripts/stage_nifi_chunks.py
	@echo "Chunks written to nifi/data-input/ — NiFi will consume them automatically."

harmonize:
	@echo "Running replacement db/test pipeline..."
	python3 db/test/run_pipeline.py
	@echo "Replacement pipeline complete. Outputs in outputs/"

# ============================================
# Utilities
# ============================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "coverage" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage coverage.xml 2>/dev/null || true
	@echo "Cleaning NiFi processor cache..."
	rm -rf nifi/processors/__pycache__ 2>/dev/null || true

pre-commit:
	@echo "Setting up pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	pre-commit run --all-files

docs:
	@echo "Generating documentation..."
	@echo "API docs available at: http://localhost:3001/api/docs (when running)"
	cd backend-py && python -c "from app.main import app; import json; from fastapi.openapi.utils import get_openapi; print(json.dumps(get_openapi(title=app.title, version=app.version, routes=app.routes), indent=2))" > ../docs/openapi.json 2>/dev/null || echo "Run backend first to generate OpenAPI spec"

security-scan:
	@echo "Running security scans..."
	@echo "Python dependencies..."
	cd backend-py && pip-audit || true
	@echo "JavaScript dependencies..."
	npm audit || true
	@echo "Secret detection..."
	$(MAKE) detect-secrets

detect-secrets:
	detect-secrets scan > .secrets.baseline || true

# ============================================
# Deployment
# ============================================

deploy-staging:
	@echo "Deploying to staging..."
	@echo "Add your staging deployment commands here"

deploy-production:
	@echo "Deploying to production..."
	@echo "Add your production deployment commands here"
