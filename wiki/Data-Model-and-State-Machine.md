# Data Model & State Machine Specifications

The FRS V7.1 K² persistence tier is built on PostgreSQL 16 using strict relational normalization, immutable historical tables, and transactional locking to preserve academic integrity.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    DEPARTMENT ||--o{ COHORT : "groups"
    DEPARTMENT ||--o{ SUBJECT : "offers"
    ACADEMIC_YEAR ||--o{ TERM : "spans"
    TERM ||--o{ SUBJECT_OFFERING : "schedules"
    SUBJECT ||--o{ SUBJECT_OFFERING : "instantiates"
    SUBJECT_OFFERING ||--o{ FACULTY_ASSIGNMENT : "assigned to"
    FACULTY ||--o{ FACULTY_ASSIGNMENT : "teaches"
    COHORT ||--o{ STUDENT : "enrolled in"
    STUDENT ||--o{ ENROLLMENT : "participates"
    SUBJECT_OFFERING ||--o{ ENROLLMENT : "receives"

    SUBJECT_OFFERING ||--o{ ATTENDANCE_SESSION : "conducts"
    ATTENDANCE_SESSION ||--|| ROSTER_SNAPSHOT : "freezes"
    ROSTER_SNAPSHOT ||--o{ ROSTER_SNAPSHOT_ITEM : "contains"
    ATTENDANCE_SESSION ||--o{ INSTRUCTIONAL_UNIT : "divided into"
    ATTENDANCE_SESSION ||--o{ CAPTURE_BATCH : "receives"
    CAPTURE_BATCH ||--o{ PHOTO_FRAME : "contains"

    PHOTO_FRAME ||--o{ VISION_JOB : "enqueues"
    VISION_JOB ||--o{ FACE_EVIDENCE : "produces"
    FACE_EVIDENCE ||--o{ CANDIDATE_PROPOSAL : "aggregated into"
    ROSTER_SNAPSHOT_ITEM ||--o{ CANDIDATE_PROPOSAL : "matched against"

    ATTENDANCE_SESSION ||--|| COMMIT_RECEIPT : "produces"
    INSTRUCTIONAL_UNIT ||--o{ ATTENDANCE_RECORD : "records"
    STUDENT ||--o{ ATTENDANCE_RECORD : "evaluated for"
    COMMIT_RECEIPT ||--o{ ATTENDANCE_RECORD : "commits"
```

---

## Table Categorization Matrix (27 Tables)

The schema generated in baseline migration `3a42e90c6daf` is partitioned into seven functional domains:

| Domain | Core Tables | Responsibility |
| :--- | :--- | :--- |
| **Academic Hierarchy** | `departments`, `cohorts`, `academic_years`, `terms`, `subjects` | Defines college structure, academic semesters, and course syllabus. |
| **Offerings & Teaching** | `subject_offerings`, `authorized_class_groups`, `class_group_members`, `faculties`, `faculty_assignments` | Maps which instructors teach which sections or merged joint class groups. |
| **Student Roster** | `students`, `enrollments` | Authoritative student admissions, term registration, and enrollment status (`ACTIVE`, `INACTIVE`, `DROPPED`, `SUSPENDED`). |
| **Session Lifecycle** | `attendance_sessions`, `roster_snapshots`, `roster_snapshot_items`, `instructional_units` | Manages active classroom sessions, freezes student rosters, and tracks 1 to 4 units. |
| **Photo Ingress** | `capture_batches`, `photo_frames` | Stores metadata, SHA-256 digests, dimensions, and timestamps of classroom sweeps. |
| **Worker Queue & Evidence** | `vision_jobs`, `detected_faces`, `face_embeddings`, `candidate_proposals` | Manages asynchronous background processing, bounding boxes, 512-d embeddings, and match scores. |
| **Final Ledger & Audit** | `commit_receipts`, `attendance_records`, `attendance_overrides`, `audit_ledger_events` | Immutable, append-only attendance records, tamper-evident hash receipts, and administrative audit logs. |

---

## State Machine Lifecycles

### 1. Attendance Session State (`SessionState`)

A session represents an instructor's classroom lecture. Transitions are strictly forward-only:

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Faculty selects offering
    DRAFT --> ROSTER_FROZEN : Verify assignment & freeze snapshot
    ROSTER_FROZEN --> CAPTURING : Instructor launches camera
    CAPTURING --> CAPTURING : Additional photo frames captured
    CAPTURING --> PROCESSING : Batch submitted for vision inference
    PROCESSING --> IN_REVIEW : Worker completes proposal generation
    IN_REVIEW --> IN_REVIEW : Faculty overrides / resolves candidates
    IN_REVIEW --> FINALIZED : Atomic ACID ledger commit executed
    DRAFT --> CANCELLED : Abandoned
    ROSTER_FROZEN --> CANCELLED : Discarded by instructor
    CAPTURING --> CANCELLED : Abandoned prior to review
    FINALIZED --> [*] : Session record locked permanently
    CANCELLED --> [*] : Session invalidated
```

### 2. Candidate Evidence State (`EvidenceState`)

Classroom detections transition through distinct evidence states based on recognition confidence and image quality:

```mermaid
stateDiagram-v2
    [*] --> CAPTURED : Frame decoded & EXIF stripped
    CAPTURED --> VALIDATING : Bounded aspect & size check
    VALIDATING --> QUEUED : Enqueued into PostgreSQL job queue
    QUEUED --> PROCESSING : Leased by vision worker
    PROCESSING --> CANDIDATE : Sighting matched to single student (cosine >= 0.60)
    PROCESSING --> REVIEW : Sighting conflicts with lookalike or multi-match
    PROCESSING --> UNKNOWN : Face detected, but distance > 0.60 across all roster students
    PROCESSING --> INSUFFICIENT_EVIDENCE : Face blurred, severe occluded, or low resolution (<40px)
    PROCESSING --> RECAPTURE_REQUIRED : Zero faces detected across wide-angle classroom sweep
    PROCESSING --> SECURITY_FAIL : Passive anti-spoofing check failed (presentation attack)

    CANDIDATE --> [*] : Proposed Present
    REVIEW --> [*] : Flagged for explicit faculty confirmation
    UNKNOWN --> [*] : Surfaced to faculty as unassigned candidate
    INSUFFICIENT_EVIDENCE --> [*] : Triage required
    RECAPTURE_REQUIRED --> [*] : Camera sweep prompt
    SECURITY_FAIL --> [*] : Logged in audit ledger
```

### 3. Background Job Queue State (`JobState`)

```mermaid
stateDiagram-v2
    [*] --> PENDING : Created during frame upload
    PENDING --> LEASED : Acquired by worker with 60s lease timeout
    LEASED --> RUNNING : ONNX inference executing
    RUNNING --> SUCCEEDED : Embeddings generated & proposals updated
    RUNNING --> RETRYABLE_FAILURE : Transient timeout / GPU out-of-memory
    RETRYABLE_FAILURE --> PENDING : Retried (max 3 attempts)
    RETRYABLE_FAILURE --> TERMINAL_FAILURE : Exhausted 3 attempts
    RUNNING --> TERMINAL_FAILURE : Corrupt image payload
    SUCCEEDED --> [*]
    TERMINAL_FAILURE --> [*] : Surfaced to client
```

---

## Atomic Ledger Commit Guarantees

When the faculty instructor clicks **"Sign & Finalize Attendance"**, the backend executes an atomic ACID transaction in `CommitService`:

1. **Session State Gate:** Verifies `session.state == SessionState.IN_REVIEW`.
2. **Faculty Authorization:** Verifies `session.faculty_id == current_user.faculty_id`.
3. **Idempotency Verification:** Checks `idempotency_key` against `commit_receipts`. If key already exists for this session, the existing receipt is returned immediately without double-writing.
4. **Instructional Unit Records:** Inserts `AttendanceRecord` rows for each enrolled student across all conducted unit indices ($1 \le \text{units} \le 4$).
5. **Cryptographic Receipt Hash:**
```math
H_{\mathrm{receipt}} = \operatorname{SHA-256}(\mathrm{id}_{\mathrm{session}} \parallel \mathrm{id}_{\mathrm{faculty}} \parallel t_{\mathrm{commit}} \parallel N_{\mathrm{present}} \parallel N_{\mathrm{absent}})
```
6. **Immutable Closure:** Updates `session.state = SessionState.FINALIZED`.
7. **Audit Ledger Logging:** Appends an immutable audit event (`ATTENDANCE_COMMITTED`) referencing the `receipt_hash`.

