# K² FRS — Definition of Done (DoD) & Acceptance Quality Gate
*Standard Engineering Quality Gate for Features, Bug Fixes, and Architectural Changes*
*Conforms to Checklist Section 55 (Definition of done for each feature) and Section 52 (Quality gates)*

---

## 1. Feature Definition of Done Checklist

Every pull request, architectural change, or feature increment must satisfy the following criteria before being merged into the authoritative `main` branch:

### Core Domain & Business Invariants (Priority: P0)
- [ ] **Mathematical Invariant Fidelity:** Attendance rate calculations strictly adhere to the per-conducted-unit denominator rule ($1 \le |U_c| \le 4$). Unconducted units are never coerced into 0% or 100%. If $|U_c| = 0$, rate strictly evaluates to `N/A`.
- [ ] **Snapshot Immutability:** Candidate roster freeze on `DRAFT` $\rightarrow$ `ROSTER_FROZEN` is immutable and quarantined from mid-session enrolment changes.
- [ ] **Human-in-the-Loop Gate:** Machine vision predictions surface strictly as non-binding candidate proposals. Autonomous absence marking without faculty review is prohibited.
- [ ] **Idempotent Replay Safety:** Any state-altering endpoint (especially session commit) enforces idempotency keys, guaranteeing duplicate network deliveries do not double-write records.

### Backend & API Engineering (Priority: P0)
- [ ] **Input Validation:** Request bodies, query parameters, and route paths validated via typed Pydantic V2 schemas with strict bounds.
- [ ] **Server-Side Authorization:** RBAC checks enforced server-side. Faculty can only manipulate sessions for assigned course offerings.
- [ ] **Envelope Conformity:** Successful responses wrapped in `ResponseEnvelope[T]`; failures wrapped in `ErrorEnvelope[ErrorDetail]` with standard reason codes.
- [ ] **Security Headers & Ingress Protection:** Response headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. Requests checked against sliding-window rate limiters.

### Frontend & Mobile Engineering (Priority: P1)
- [ ] **Zero Secrets in Bundles:** No database credentials, JWT secrets, or administrative keys bundled in client code.
- [ ] **Error Boundaries & Recovery:** Client error boundaries (`app/error.tsx`) and 404 handlers (`app/not-found.tsx`) catch runtime exceptions gracefully with retry options.
- [ ] **WCAG 2.2 AA Accessibility:** Semantic HTML, skip-to-content anchors, visible keyboard focus rings, and high contrast text ($> 4.5:1$).
- [ ] **Mobile Offline Resilience:** Riverpod providers support pull-to-refresh with deterministic local mock fallbacks during network interruptions.

### Quality Assurance & Automated Testing (Priority: P0)
- [ ] **Backend Test Suite:** All Pytest tests pass (`python -m pytest tests/ -v`).
- [ ] **Invariant Verification Suite:** `python backend/verify_backend.py` passes 5/5 core invariant suites with 100% fidelity.
- [ ] **Admin Console Typecheck & Build:** `npm --prefix apps/admin_console run typecheck` and `npm --prefix apps/admin_console run build` complete with 0 errors.
- [ ] **Mobile Static Analysis:** `dart analyze apps/teacher_mobile` completes with 0 errors/warnings.
- [ ] **Contract Synchronization:** `node apps/admin_console/node_modules/typescript/bin/tsc --noEmit packages/contracts/src/index.ts` completes with 0 errors.

### Security, Privacy & Git Hygiene (Priority: P0)
- [ ] **PII Redaction:** Facial bounding boxes, crops, and embedding arrays are never written to operational logs or audit tables.
- [ ] **Cryptographic Signing:** Commit is cryptographically signed using the authorized SSH ED25519 key.
- [ ] **Exclusion Policy:** `docs/FRS_K2_K2_Master_Project_Handbook_85_Prompt_Shot_Plan.md` and local `.env` files are strictly excluded from git tracking.

