# FRS V7.1 K² — Universal Monorepo Automation & Engineering Operations
# Conforms to Checklist Section 24, 25, and 61.

.PHONY: help test verify lint build clean up down db-migrate contracts e2e

help:
	@echo "FRS V7.1 K² Production Monorepo Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make test        Run all test suites (Backend, Mobile, Admin, Contracts)"
	@echo "  make e2e         Run Playwright browser automation E2E suite"
	@echo "  make verify      Run full backend acceptance & mathematical invariant suite"
	@echo "  make lint        Run static analyzers across all workspaces"
	@echo "  make build       Compile and package all production artifacts"
	@echo "  make contracts   Validate shared TypeScript & OpenAPI contracts"
	@echo "  make up          Spin up Docker Compose environment"
	@echo "  make down        Stop Docker Compose environment"
	@echo "  make db-migrate  Apply database migrations via Alembic"

test:
	@echo "[TEST] Running backend pytest..."
	cd backend && python -m pytest tests/ -v
	@echo "[TEST] Running admin console typecheck..."
	npm --prefix apps/admin_console run typecheck
	@echo "[TEST] Running mobile analyzer..."
	dart analyze apps/teacher_mobile
	@echo "[TEST] Running contracts validation..."
	node apps/admin_console/node_modules/typescript/bin/tsc --noEmit packages/contracts/src/index.ts

e2e:
	@echo "[E2E] Running Playwright browser automation suite..."
	cd backend && python -m pytest tests/test_playwright_admin_console.py -v

verify:
	@echo "[VERIFY] Executing mathematical invariants and acceptance verification..."
	python backend/verify_backend.py

lint:
	@echo "[LINT] Analyzing mobile app..."
	dart analyze apps/teacher_mobile
	@echo "[LINT] Checking admin console..."
	npm --prefix apps/admin_console run typecheck

build:
	@echo "[BUILD] Building Next.js Admin Console..."
	npm --prefix apps/admin_console run build

contracts:
	@echo "[CONTRACTS] Verifying TypeScript contracts..."
	node apps/admin_console/node_modules/typescript/bin/tsc --noEmit packages/contracts/src/index.ts

up:
	docker compose up -d

down:
	docker compose down

db-migrate:
	cd backend && alembic upgrade head

