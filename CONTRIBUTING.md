# Contributing to FRS V7.1 K²

Thank you for your interest in contributing to the **Facial Recognition System (FRS) V7.1 K²** for Kakatiya University College of Engineering & Technology (KUCET).

To maintain academic governance, mathematical accuracy, and data security, all contributions must adhere to the standards outlined in this guide.

---

## Code of Conduct

All contributors and maintainers are expected to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat colleagues, faculty, students, and open-source collaborators with respect.

---

## Architectural Guardrails (Non-Negotiable)

When contributing code, you must preserve the core institutional invariants:

1. **Human-in-the-Loop Principle:** Computer vision algorithms generate candidate evidence proposals. They must never directly write final attendance records without explicit faculty review and commit.
2. **Denominator Invariant:** Attendance is evaluated per student per conducted instructional unit ($1 \le \text{units} \le 4$). If zero units are conducted, the attendance percentage must strictly evaluate to `N/A`. It must never be coerced to $0\%$ or $100\%$.
3. **Immutable Snapshots:** Eligible student enrollments are frozen at session initialization (`ROSTER_FROZEN`). Mid-session mutations must never retroactively alter session eligibility.
4. **Biometric Privacy:** Raw facial crops, coordinates, and 512-dimensional embedding vectors must remain strictly on-premise and must never be committed to repository logs, exported to third-party cloud APIs, or exposed in administrative telemetry views.

---

## Development Workflow

### 1. Branching Strategy
* `main`: Protected production branch. All code must pass CI pipelines and code review.
* Feature branches: Use conventional prefixes:
  * `feat/<scope>-<description>` (e.g. `feat/mobile-offline-cache`)
  * `fix/<scope>-<description>` (e.g. `fix/api-envelope-unwrapping`)
  * `docs/<description>` (e.g. `docs/update-wiki-vision`)

### 2. Local Verification Checklist
Before submitting a pull request, run the test suites across all three tiers:

```bash
# 1. Teacher Mobile App
cd apps/teacher_mobile
flutter analyze
flutter test

# 2. Next.js Admin Console
cd ../admin_console
npm run typecheck
npm run build

# 3. Control Plane Backend
cd ../../backend
python -m pytest tests/ -v
```

All commands must exit with code 0 without unhandled warnings or regressions.

### 3. Commit Message Convention
We adhere to [Conventional Commits v1.0.0](https://www.conventionalcommits.org/):
* `feat`: A new feature or endpoint.
* `fix`: A bug fix or discrepancy resolution.
* `docs`: Documentation updates (README, wiki, comments).
* `refactor`: Code change that neither fixes a bug nor adds a feature.
* `test`: Adding or modifying automated test cases.
* `chore`: Build process, Dockerfile, or auxiliary tool changes.

---

## Pull Request Submission

1. Submit PRs against the `main` branch.
2. Complete all sections of the [Pull Request Template](.github/pull_request_template.md).
3. Ensure automated GitHub Actions CI passes completely.
4. Request review from a designated repository maintainer.

