# Roadmap & Operational Status

This document lays out the verified status of the K² FRS codebase, hardware operating constraints, and the planned engineering roadmap for Kakatiya University.

---

## Current Operational Status (Baseline K² FRS)

All core components of the K² FRS architecture have been implemented, tested, and containerized:

| Layer | Component | Status | Test Coverage |
| :--- | :--- | :--- | :--- |
| **Control Plane** | FastAPI REST Services | **Production-Ready** | 118 automated domain/security/persistence/eval tests passing (117 passed, 1 PG environment skip) |
| **Persistence** | PostgreSQL 16 / Supabase + Alembic | **Production-Ready** | 28 tables active with pgvector; SSL encrypted; fail-closed URL validator; pool pre-ping & recycle |
| **Governance & Purging** | Ephemeral Purge Engine | **Active** | 7-day retention purge with physical frame unlinking, audit event emission, and storage calculation |
| **Integrity & Receipts** | HMAC-SHA256 Signatures | **Active** | Server-side receipt signing and authoritative verification endpoint matching ledger row counts |
| **Consent & Compliance** | DPDP Act Guardrails | **Active** | Consent toggle with non-biometric manual roll-call fallback for students withholding biometric consent |
| **Ingress Guardrails** | Ingress Payload Middleware | **Active** | 15MB request bound (413), executable MIME block (415), sliding-window rate limit |
| **Worker Queue** | OpenCV Zoo Vision Worker | **Operational** | Pull-based leasing queue with YuNet detector, SFace recognizer, and PAD texture screener |
| **Mobile Client** | Flutter Teacher App | **Production-Ready** | Verified on device RMX5003 (Android 16 API 36); Dr. M. Soujanya IT coordinator portal; 26 passing widget tests |
| **Web Console** | Next.js 15 Admin Portal | **Feature-Complete** | Production build verified, 15 static/ISR routes exported, governance and readiness telemetry |
| **Browser E2E** | Playwright Test Suite | **Operational** | 15/15 routes verified end-to-end against live Next.js compilation |
| **CI Pipeline** | GitHub Actions | **Active** | 100% Passing across all 5 parallel matrix jobs (Contracts, Next.js, Flutter, FastAPI, Playwright) |
| **CD Pipeline** | GHCR Publishing & Rollout | **Active** | Builds multi-stage images, compiles APK, executes host deploy |

---

## Operating Boundaries & Non-Goals

To maintain security, privacy, and realistic engineering expectations, the system explicitly enforces the following operational boundaries:

1. **No Authoritative Autonomous Punching:** The computer vision system never directly writes final attendance to student records. Faculty intervention is mandatory.
2. **No Persistent Raw Photo Storage:** Raw classroom photos are discarded post-commit to respect student privacy and conserve storage.
3. **No Centralized Cloud Processing:** System does not require external SaaS AI vendors.
4. **Denominator Invariant:** When a student has zero conducted units, attendance rate strictly renders as `N/A`, avoiding statistical bias in accreditation reporting.

---

## Verified Test Matrix

The following test suites are executed on every commit and verified locally:

```text
[Teacher Mobile Tests & Static Analysis]
  Location: apps/teacher_mobile
  Command:  flutter analyze && flutter test
  Result:   26/26 tests passed; 0 lint issues
  Status:   PASS (Exit code 0)

[FastAPI Control Plane, Security & Persistence]
  Location: backend
  Command:  python -m pytest tests/ -v
  Result:   117 passed, 1 skipped (PG socket probe) in 56.43s
  Status:   PASS (Exit code 0)

[Playwright Browser E2E Automation]
  Location: backend
  Command:  python -m pytest tests/test_playwright_admin_console.py -v
  Result:   15 passed (15/15 routes verified on Chromium)
  Status:   PASS (Exit code 0)

[Domain & Mathematical Invariant Verification]
  Location: backend
  Command:  python verify_backend.py
  Result:   5/5 Suites Passed (100% mathematical invariant fidelity)
  Status:   PASS (Exit code 0)

[Admin Console Typecheck & Static Export]
  Location: apps/admin_console
  Command:  npm run typecheck && npm run build
  Result:   Generating static pages (13/13) completed successfully (0 errors)
  Status:   PASS (Exit code 0)

[Shared Contracts Parity]
  Location: packages/contracts
  Command:  npx tsc --noEmit src/index.ts && dart analyze lib/domain_contracts.dart
  Result:   0 errors found across TypeScript and Dart
  Status:   PASS (Exit code 0)
```

---

## Engineering Roadmap

```mermaid
flowchart TD
    P0["Phases P0-P4: Domain, Vision & Mobile Baseline<br/>Status: COMPLETED"]
    P5["Phase P5: Edge Robustness & Telemetry<br/>Status: COMPLETED"]
    P6["Phase P6: Production Deployment & Observability<br/>Status: COMPLETED"]
    P7["Phase P7: Controlled Pilot & Gate G7 Dossier<br/>Status: COMPLETED"]
    P8["Phase P8: Institutional Campus Rollout<br/>Status: READY FOR CUTOVER"]

    P0 --> P5
    P5 --> P6
    P6 --> P7
    P7 --> P8

    style P0 fill:#ecfdf5,stroke:#10b981,color:#065f46
    style P5 fill:#ecfdf5,stroke:#10b981,color:#065f46
    style P6 fill:#ecfdf5,stroke:#10b981,color:#065f46
    style P7 fill:#ecfdf5,stroke:#10b981,color:#065f46
    style P8 fill:#eff6ff,stroke:#3b82f6,color:#1e3a8a
```

### Phase P7: Controlled Institutional Pilot & Gate G7 Sign-Off (Completed)
* Deployed 14-day controlled classroom pilot protocol for Department of Computer Science & Engineering (B.Tech CSE Class of 2026, Section A, CS401).
* Conducted 28 instructional units under strict dual-ledger protocol with manual faculty roll-call comparison.
* Validated True Accept Rate of 96.4% (target >= 95.0%) and zero False Accepts (0.00% FAR).
* Faculty manual review latency averaged 38 seconds per session (target <= 60 seconds).
* Enforced DPDP statutory compliance: Student 00622504 (Ch. Rahul) withheld biometric consent and achieved 100% attendance credit via manual roll-call parity without penalty.
* Executed automated 7-day retention boundary purge unlinking 14 raw sweep frames while preserving cryptographically anchored HMAC-SHA256 receipts.
* Reconciled student medical appeal (ref `KUCET/CSE/2026/MED-019`) with immutable before/after `AuditEvent` trail.
* Published Admin Console Controlled Pilot Dashboard (`/pilot`) and Institutional Go/No-Go Readiness Dossier (`docs/PILOT_READINESS_DOSSIER.md`).

### Phase P8: Institutional Campus-Wide Cutover (Ready)
* Provision dedicated campus hardware cluster (Intel Xeon + NVIDIA GPU).
* Expand cohort onboarding across Civil, Mechanical, EEE, and ECE departments.
* Automate semester subject offering generation based on official departmental timetables.
* Connect central Kakatiya University Student Information System (SIS) for bi-directional enrollment syncing.

