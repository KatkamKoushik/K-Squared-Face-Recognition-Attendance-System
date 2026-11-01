## Description

Briefly describe the purpose of this pull request and the changes introduced.

---

## Category of Change

- [ ] `feat`: New feature or endpoint
- [ ] `fix`: Bug fix or discrepancy resolution
- [ ] `refactor`: Code refactoring without behavioral alteration
- [ ] `docs`: Documentation, wiki, or comment update
- [ ] `test`: New or modified test cases
- [ ] `chore`: CI/CD, Docker, or build tooling update

---

## Invariant Checklist

Please confirm that this pull request complies with core system invariants:

- [ ] **Human-in-the-Loop:** Computer vision does not automatically commit authoritative attendance records.
- [ ] **Denominator Rule:** Zero eligible conducted units strictly renders as `N/A`, never 0% or 100%.
- [ ] **Biometric Privacy:** No raw facial crops or 512-d embeddings are logged or exposed in audit views.
- [ ] **Envelopes:** API responses conform to `ResponseEnvelope` / `ErrorEnvelope`.
- [ ] **State Parity:** Canonical enums in Dart, TypeScript, and Python match exactly.

---

## Verification Evidence

Run and confirm local verification outcomes:

- [ ] **Mobile:** `cd apps/teacher_mobile && flutter analyze && flutter test`
- [ ] **Web:** `cd apps/admin_console && npm run typecheck && npm run build`
- [ ] **Backend:** `cd backend && python -m pytest tests/ -v`

