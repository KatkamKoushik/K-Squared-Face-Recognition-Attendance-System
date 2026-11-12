# K² FRS — Repository Layout & Contract Architecture (CLI-02 / Shot 42)

## 1. Directory Structure & Boundary Separation

To maintain strict boundaries between the backend control plane and the frontend clients (Flutter Teacher App and Next.js Admin Console) without cross-contamination, the repository is partitioned as follows:

```
D:\k^2\
├── docs/                        # Architecture decisions, audit records, and contract definitions
│   ├── BASELINE_AUDIT.md
│   └── CONTRACT_ARCHITECTURE.md
├── backend/                     # [OUR SOLE WORKSPACE BOUNDARY]
│   ├── pyproject.toml           # Python dependencies and build config
│   ├── alembic.ini              # Database migration tool configuration
│   ├── .env.example             # Documented environment template (safe defaults)
│   ├── alembic/                 # Versioned database migrations
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory & lifespan
│   │   ├── core/                # Settings, DB session, errors, security, logs
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── errors.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── domain/              # Pure domain entities, enums & invariants (Hexagonal core)
│   │   │   ├── enums.py
│   │   │   └── models/
│   │   │       ├── academic.py
│   │   │       ├── student.py
│   │   │       ├── session.py
│   │   │       ├── capture.py
│   │   │       ├── job.py
│   │   │       ├── model_registry.py
│   │   │       ├── attendance.py
│   │   │       └── audit.py
│   │   ├── schemas/             # Pydantic V2 DTOs (The Single Source of Truth for API)
│   │   │   ├── common.py
│   │   │   ├── auth.py
│   │   │   ├── academic.py
│   │   │   ├── session.py
│   │   │   ├── capture.py
│   │   │   ├── review.py
│   │   │   ├── attendance.py
│   │   │   └── audit.py
│   │   ├── services/            # Application use cases / orchestration logic
│   │   │   ├── academic_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── roster_service.py
│   │   │   ├── session_service.py
│   │   │   ├── ingress_service.py
│   │   │   ├── queue_service.py
│   │   │   ├── review_service.py
│   │   │   ├── commit_service.py
│   │   │   └── analytics_service.py
│   │   ├── api/                 # HTTP routers & route dependencies
│   │   │   ├── dependencies.py
│   │   │   └── v1/
│   │   │       ├── api_router.py
│   │   │       ├── auth.py
│   │   │       ├── academic.py
│   │   │       ├── sessions.py
│   │   │       ├── capture.py
│   │   │       ├── review.py
│   │   │       ├── attendance.py
│   │   │       ├── audit.py
│   │   │       └── health.py
│   │   └── worker/              # Asynchronous vision worker & inference adapters
│   │       ├── worker.py
│   │       ├── contracts.py
│   │       ├── registry.py
│   │       ├── preprocessor.py
│   │       ├── adapters/
│   │       │   ├── detector_adapter.py
│   │       │   ├── recognizer_adapter.py
│   │       │   └── pad_adapter.py
│   │       └── reconciliation.py
│   └── tests/                   # Pytest test suites (unit, integration, invariants)
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_academic_schema.py
│       ├── test_roster_snapshot.py
│       ├── test_state_machine.py
│       ├── test_commit_acid.py
│       └── test_arithmetic.py
├── frontend/                    # [STRICTLY UNTOUCHED BY BACKEND DEVELOPER]
│   ├── teacher_app/             # Flutter / Dart client (Managed by IDE Frontend prompts)
│   └── admin_web/               # Next.js / TypeScript console (Managed by IDE Frontend prompts)
└── FRS_K2_K2_Master_Project_Handbook_85_Prompt_Shot_Plan.md
```

---

## 2. Shared API Contract Governance

1. **Source of Truth**: The FastAPI control plane in `backend/app/schemas/` is the authoritative source for all API contracts.
2. **OpenAPI Generation**: FastAPI automatically publishes OpenAPI 3.1 specification at `/openapi.json` and interactive docs at `/docs`.
3. **No Frontend Contamination**: The frontend clients must never invent endpoints, DTOs, or domain states not published in this contract.

---

## 3. Standard Response & Error Envelope

Every API response follows a deterministic typed envelope structure:

### Successful Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "correlation_id": "req-98f3b14a-7182",
  "timestamp": "2026-11-01T20:30:00Z"
}
```

### Error Response Envelope
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_FORBIDDEN",
    "message": "Faculty assignment has expired or is unauthorized for this subject offering.",
    "details": {},
    "reason_code": "FACULTY_ASSIGNMENT_NOT_EFFECTIVE"
  },
  "correlation_id": "req-98f3b14a-7182",
  "timestamp": "2026-11-01T20:30:00Z"
}
```

---

## 4. Standard Domain Status Enums

To prevent semantic drift, enums are strictly frozen across backend and client contracts:

* **Session States**: `DRAFT`, `ROSTER_FROZEN`, `CAPTURING`, `PROCESSING`, `IN_REVIEW`, `FINALIZED`, `CANCELLED`
* **Unit Finalization States**: `PENDING`, `CONDUCTED_CONFIRMED`, `NOT_CONDUCTED`, `COMMITTED`
* **Vision Evidence States**: `CAPTURED`, `VALIDATING`, `QUEUED`, `PROCESSING`, `CANDIDATE`, `UNKNOWN`, `INSUFFICIENT_EVIDENCE`, `RECAPTURE_REQUIRED`, `REVIEW`, `SECURITY_FAIL`, `SECURITY_UNCERTAIN`, `PIPELINE_ERROR`
* **Attendance Ledger States**: `PRESENT_CONFIRMED`, `ABSENT_CONFIRMED`, `EXCUSED`
