# FRS V7.1 K² — Control Plane & Vision Worker

This package provides the FastAPI control plane API and asynchronous ONNX vision worker for the FRS V7.1 K² classroom attendance proposal system.

---

## Architecture Overview

* **Control Plane (`app/api/v1`):** FastAPI application enforcing role-based access control (ADMIN, FACULTY, OPERATOR, WORKER), immutable roster snapshots, and atomic ACID attendance commits.
* **Worker Daemon (`app/worker`):** Asynchronous background worker polling a PostgreSQL-backed job queue to perform SCRFD face detection and ArcFace 512-dimensional embedding extraction.
* **Database Migrations (`alembic/`):** Version-controlled schema migrations managing all 27 domain, ledger, and queue tables.

---

## Quickstart

### 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Run Database Migrations
```bash
alembic upgrade head
```

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```

### 4. Start Local Development Server
```bash
uvicorn app.main:create_application --factory --reload --port 8000
```

