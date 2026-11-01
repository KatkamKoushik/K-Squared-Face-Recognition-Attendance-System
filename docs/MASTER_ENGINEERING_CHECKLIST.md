# FRS V7.1 K² — Complete Software Project Engineering Master Checklist
*Consolidated Engineering Inventory for Designing, Building, Securing, Operating, and Retiring the KUCET Attendance Infrastructure*

**Project:** FRS V7.1 K² — Classroom-Photo Attendance Proposal System  
**Lead Architect & Owner:** KatkamKoushik (`koushikkatkam@gmail.com`)  
**Target Environment:** Kakatiya University College of Engineering and Technology (KUCET)  
**Standard Status Convention:** `Complete` · `In progress` · `Not started` · `N/A` (with technical rationale)  
**Priority Hierarchy:** `P0` (Release Blocker / Critical Risk) · `P1` (Required for Production) · `P2` (Maturity & Scale) · `P3` (Conditional / Institutional Context)  

---

## 1. Product Definition, Goals, and Scope

- [x] **Define problem statement and target users**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Problem documented: manual roll-calls consume 15+ minutes per lecture. Users: Faculty taking attendance, Academic Administrators verifying reports.
  - **Verification / evidence:** `README.md`, `wiki/Home.md`, `docs/BASELINE_AUDIT.md`.
  - **Last reviewed:** 2026-11-01

- [x] **Define functional requirements and mathematical invariants**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Per-conducted-unit denominator rule ($1 \le |U_c| \le 4$), immutable roster freeze, non-binding AI proposals, idempotent commit receipts.
  - **Verification / evidence:** `docs/adr/0001-per-conducted-unit-denominator-rule.md`, `backend/verify_backend.py`.
  - **Last reviewed:** 2026-11-01

- [x] **Define explicit out-of-scope items**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Continuous CCTV surveillance, autonomous unreviewed absences, and public cloud AI transmission are explicitly excluded.
  - **Verification / evidence:** `docs/adr/0003-on-premise-onnx-vision-pipeline.md`, `wiki/Security-Privacy-and-Governance.md`.
  - **Last reviewed:** 2026-11-01

---

## 2. Architecture, Boundaries, and Design Decisions

- [x] **Document high-level architecture and component boundaries**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Monorepo with Clean Architecture separating Control Plane API, Vision Worker, Teacher Mobile Client, Admin Console, and Shared Contracts.
  - **Verification / evidence:** `wiki/System-Architecture.md`, `README.md`, `docs/CONTRACT_ARCHITECTURE.md`.
  - **Last reviewed:** 2026-11-01

- [x] **Record Architecture Decision Records (ADRs) for material choices**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Five foundational ADRs documented in `docs/adr/`.
  - **Verification / evidence:** `docs/adr/0001-per-conducted-unit-denominator-rule.md` through `0005-cryptographic-idempotent-commit-receipts.md`.
  - **Last reviewed:** 2026-11-01

---

## 3. Repository and Source-Control Hygiene

- [x] **Use clear and consistent repository structure**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Monorepo organized under `/apps`, `/backend`, `/packages`, `/docs`, `/wiki`, `/.github`.
  - **Verification / evidence:** `README.md` Repository Map.
  - **Last reviewed:** 2026-11-01

- [x] **Cryptographic Commit Signing**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** All repository commits cryptographically signed using SSH ED25519 key.
  - **Verification / evidence:** `git log -n 1 --show-signature` (`SHA256:vGEnfBe4hJGLYc45Eir66LMsExAFzhKs4nY6vO2IqkY`).
  - **Last reviewed:** 2026-11-01

- [x] **Configure CODEOWNERS and Dependabot**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Subsystem owners mapped in `.github/CODEOWNERS`; automated update schedules in `.github/dependabot.yml`.
  - **Verification / evidence:** `.github/CODEOWNERS`, `.github/dependabot.yml`.
  - **Last reviewed:** 2026-11-01

---

## 4. Languages, Frameworks, and Code Quality

- [x] **Standardize language runtimes and pin toolchains**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Python 3.12, Node.js 22, Flutter 3.27 / Dart 3.6, PostgreSQL 16.
  - **Verification / evidence:** `backend/pyproject.toml`, `apps/admin_console/package.json`, `apps/teacher_mobile/pubspec.yaml`.
  - **Last reviewed:** 2026-11-01

- [x] **Zero Linter and Static Analysis Errors**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `dart analyze` reports 0 issues; TypeScript `tsc --noEmit` reports 0 issues.
  - **Verification / evidence:** `run.ps1 lint`, `Makefile`.
  - **Last reviewed:** 2026-11-01

---

## 5. Dependency Management & Software Supply Chain

- [x] **Automated Dependency Vulnerability Scanning**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Weekly Dependabot sweeps configured across Python, NPM, Pub, and Actions.
  - **Verification / evidence:** `.github/dependabot.yml`.
  - **Last reviewed:** 2026-11-01

- [x] **Deterministic Dependency Lockfiles**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Committed `package-lock.json` and explicit ranges across pyproject and pubspec.
  - **Verification / evidence:** `apps/admin_console/package-lock.json`.
  - **Last reviewed:** 2026-11-01

---

## 6. Identity, Authentication, and Account Lifecycle

- [x] **JWT Token Security & Secret Validation**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** SHA-256 HMAC JWT with 60-min expiry; startup validation rejects insecure secrets in production.
  - **Verification / evidence:** `backend/app/core/config.py` (`validate_secret_key`), `backend/app/core/security.py`.
  - **Last reviewed:** 2026-11-01

- [x] **Rate-Limit Ingress and Abuse Defense**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** In-memory sliding-window limiter enforcing 50 req/sec burst and 240 req/min thresholds.
  - **Verification / evidence:** `backend/app/core/rate_limiter.py`, `backend/app/main.py`.
  - **Last reviewed:** 2026-11-01

---

## 7. Authorization, Tenancy, and Privileged Access

- [x] **Role-Based Access Control (RBAC)**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Distinct `ADMIN`, `FACULTY`, `STUDENT` roles enforced on server-side endpoints.
  - **Verification / evidence:** `backend/app/api/dependencies.py` (`get_current_user`).
  - **Last reviewed:** 2026-11-01

- [x] **Object-Level Authorization & IDOR Defense**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Faculty cannot access or commit sessions for course offerings they are not assigned to.
  - **Verification / evidence:** `backend/tests/test_academic_schema.py` (`test_unassigned_faculty_rejected`).
  - **Last reviewed:** 2026-11-01

---

## 8. Secrets, Keys, Certificates, and Cloud IAM

- [x] **Zero Secrets in Source Control**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `.env`, upload keystores, and master prompt plans gitignored.
  - **Verification / evidence:** `.gitignore`, `git status --ignored`.
  - **Last reviewed:** 2026-11-01

---

## 9. Application Security Engineering

- [x] **Safe Security Headers Middleware**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and HSTS.
  - **Verification / evidence:** `backend/app/main.py` (`security_headers_middleware`).
  - **Last reviewed:** 2026-11-01

- [x] **SQL Injection Defense via Parameterization**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** 100% ORM parameterized queries; zero raw dynamic SQL string interpolation.
  - **Verification / evidence:** `backend/app/services/`.
  - **Last reviewed:** 2026-11-01

---

## 10. Frontend and Browser Application Engineering

- [x] **Client Error Boundaries and 404 Recovery**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `app/error.tsx` catches client exceptions with retry action; `app/not-found.tsx` provides navigation.
  - **Verification / evidence:** `apps/admin_console/app/error.tsx`, `apps/admin_console/app/not-found.tsx`.
  - **Last reviewed:** 2026-11-01

- [x] **Accessibility (WCAG 2.2 AA) & Focus Management**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Skip-to-content anchor, visible focus rings, high contrast institutional palette.
  - **Verification / evidence:** `apps/admin_console/app/layout.tsx`.
  - **Last reviewed:** 2026-11-01

---

## 11. Web Rendering, SEO, and Distribution

- [x] **Intranet Exclusion Policy**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `robots.txt` disallows all web crawlers to prevent student data indexing.
  - **Verification / evidence:** `apps/admin_console/public/robots.txt`.
  - **Last reviewed:** 2026-11-01

---

## 12. Backend Application Engineering

- [x] **Graceful Shutdown & Connection Draining**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Lifespan context manager disposes database engine cleanly on SIGTERM.
  - **Verification / evidence:** `backend/app/main.py` (`lifespan`).
  - **Last reviewed:** 2026-11-01

- [x] **Separation of Liveness and Readiness Probes**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `GET /health/liveness` confirms process is alive; `GET /health/readiness` verifies DB and model status.
  - **Verification / evidence:** `backend/app/api/v1/health.py`, `backend/tests/test_health.py`.
  - **Last reviewed:** 2026-11-01

---

## 13. API Design, Gateways, and Contracts

- [x] **Published Canonical OpenAPI Contract**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Machine-readable OpenAPI 3.1 schema and synchronized TypeScript/Dart contracts.
  - **Verification / evidence:** `packages/contracts/openapi.json`, `packages/contracts/src/domain_contracts.ts`.
  - **Last reviewed:** 2026-11-01

- [x] **Idempotent Commit Receipts**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Client-provided `idempotency_key` ensures replay safety and returns identical receipt.
  - **Verification / evidence:** `backend/tests/test_commit_acid.py` (`test_atomic_commit_and_idempotency_receipt`).
  - **Last reviewed:** 2026-11-01

---

## 14. Database Design, Transactions, and Operations

- [x] **ACID Atomic Commit Transactions**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Attendance records, session status update, and audit log write atomically in one transaction.
  - **Verification / evidence:** `backend/app/services/commit_service.py`, `backend/verify_backend.py`.
  - **Last reviewed:** 2026-11-01

- [x] **Versioned Schema Migrations**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Repeatable Alembic migrations tracking table creation and indexes.
  - **Verification / evidence:** `backend/alembic/versions/3a42e90c6daf_initial_v7_1_baseline.py`.
  - **Last reviewed:** 2026-11-01

---

## 16. Background Jobs & Asynchronous Ingestion

- [x] **Worker Job Leasing & Poison Message Guard**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Ingress frames enqueued asynchronously; worker leases job with 60s timeout and 3-retry limit.
  - **Verification / evidence:** `backend/app/domain/models/job.py`, `backend/app/worker/worker.py`.
  - **Last reviewed:** 2026-11-01

---

## 18. Machine Learning Model Lifecycle

- [x] **Certified On-Premise ONNX Pipeline**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** SCRFD (detection) + ArcFace ResNet-50 (embeddings) with cosine separation margin $\Delta s \ge 0.15$.
  - **Verification / evidence:** `docs/adr/0003-on-premise-onnx-vision-pipeline.md`, `wiki/Computer-Vision-Pipeline.md`.
  - **Last reviewed:** 2026-11-01

---

## 20. Native Mobile Engineering

- [x] **Offline Resilience & Fallback Roll-Call**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Pull-to-refresh dynamic offerings with fallback; Shot IDE-20 Manual Roll-Call screen.
  - **Verification / evidence:** `apps/teacher_mobile/lib/presentation/screens/manual_attendance_screen.dart`.
  - **Last reviewed:** 2026-11-01

---

## 24. Testing Strategy and Quality Assurance

- [x] **Multi-Tier Automated Test Verification**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** 15 backend tests pass; 5 acceptance suites pass; 12 Next.js pages build; Dart analyze 0 issues.
  - **Verification / evidence:** `run.ps1 test`, `Makefile test`.
  - **Last reviewed:** 2026-11-01

---

## 25. CI/CD and Release Engineering

- [x] **Automated Multi-Stage CI/CD Workflows**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** `.github/workflows/ci.yml` validates code; `deploy.yml` builds GHCR Docker images and Android APKs.
  - **Verification / evidence:** `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`.
  - **Last reviewed:** 2026-11-01

---

## 33. Incident Response and Production Operations

- [x] **Operations Runbook & Incident Escalation Matrix**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Documented RPO/RTO objectives, PostgreSQL restore drill, and SEV-1 to SEV-4 escalation SLAs.
  - **Verification / evidence:** `docs/OPERATIONS_RUNBOOK.md`.
  - **Last reviewed:** 2026-11-01

---

## 34. Backup, Restore, and Disaster Readiness

- [x] **Documented Point-in-Time Database Recovery Drill**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Step-by-step `pg_dump` and `pg_restore` instructions with post-restore readiness probe verification.
  - **Verification / evidence:** `docs/OPERATIONS_RUNBOOK.md` (Section 3).
  - **Last reviewed:** 2026-11-01

---

## 36. Billing & Financial Workflows

- [x] **Financial Processing Exemption**
  - **Priority:** P3
  - **Owner:** KatkamKoushik
  - **Status:** N/A
  - **Acceptance criteria:** FRS V7.1 is an institutional academic attendance recording system; no currency transactions exist.
  - **Verification / evidence:** Institutional governance charter.
  - **Last reviewed:** 2026-11-01

---

## 38. Privacy, Data Protection, and DPDP Compliance

- [x] **DPDP Act Compliance & Consent Gate**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Biometric templates enrolled only for students with signed DPDP consent; non-consenting students use roll-call.
  - **Verification / evidence:** `wiki/Security-Privacy-and-Governance.md`, `apps/admin_console/app/roster-preview/page.tsx`.
  - **Last reviewed:** 2026-11-01

---

## 40. Legal, Licensing, and Open-Source Governance

- [x] **Repository Governance & Compliance Documentation**
  - **Priority:** P1
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Standard MIT License, Contributing Guide, Code of Conduct, and Security Disclosure policy.
  - **Verification / evidence:** `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
  - **Last reviewed:** 2026-11-01

---

## 55. Definition of Done (DoD) Quality Gate

- [x] **Formal Feature Acceptance Quality Gate**
  - **Priority:** P0
  - **Owner:** KatkamKoushik
  - **Status:** Complete
  - **Acceptance criteria:** Strict criteria spanning domain invariants, input validation, error handling, test suites, and git signing.
  - **Verification / evidence:** `docs/DEFINITION_OF_DONE.md`.
  - **Last reviewed:** 2026-11-01

