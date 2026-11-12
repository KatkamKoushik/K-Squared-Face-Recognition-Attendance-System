# K² FRS — Canonical Domain Contracts

`@frs/contracts` is the central source of truth for all domain entities, state enums, request envelopes, and API DTOs across the K² FRS monorepo.

---

## Package Structure

* **`openapi.json`**: Frozen canonical OpenAPI 3.1 specification exported directly from FastAPI.
* **`src/domain_contracts.ts`**: TypeScript interfaces and string enums for the Next.js Admin Console.
* **`lib/domain_contracts.dart`**: Strongly-typed Dart models and bidirectional wire extensions for Flutter Mobile.

---

## Core Domain Enums

| Enum | Permitted Values | Wire Serialization |
| :--- | :--- | :--- |
| `SessionState` | `DRAFT`, `ROSTER_FROZEN`, `CAPTURING`, `PROCESSING`, `IN_REVIEW`, `FINALIZED`, `CANCELLED` | Snake-case string |
| `AttendanceStatus` | `PRESENT_CONFIRMED`, `ABSENT_CONFIRMED`, `EXCUSED` | Snake-case string |
| `EvidenceState` | `CAPTURED`, `VALIDATING`, `QUEUED`, `PROCESSING`, `CANDIDATE`, `UNKNOWN`, `INSUFFICIENT_EVIDENCE`, `RECAPTURE_REQUIRED`, `REVIEW`, `SECURITY_FAIL`, `SECURITY_UNCERTAIN`, `PIPELINE_ERROR` | Snake-case string |
| `UnitStatus` | `PENDING`, `CONDUCTED_CONFIRMED`, `NOT_CONDUCTED`, `COMMITTED` | Snake-case string |
| `UserRole` | `ADMIN`, `FACULTY`, `OPERATOR`, `WORKER` | Uppercase string |

