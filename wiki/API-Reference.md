# REST API Specification & Contract Reference

All communication between the client tiers and the FastAPI control plane is mediated through versioned, strictly typed REST endpoints following OpenAPI 3.1 specifications.

---

## Common Envelope Contracts

Every API response is packaged inside a standardized response envelope to ensure predictable client decoding and distributed trace correlation.

### Success Response (`ResponseEnvelope[DataT]`)
```json
{
  "success": true,
  "data": { ... },
  "correlation_id": "req-98fa-1204b",
  "timestamp": "2026-11-01T10:45:12.384Z"
}
```

### Error Response (`ErrorEnvelope`)
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested attendance session SES-10294 does not exist.",
    "reason_code": "SESSION_NOT_FOUND",
    "details": null
  },
  "correlation_id": "req-98fa-1204b",
  "timestamp": "2026-11-01T10:45:12.384Z"
}
```

### Ingress Guardrail Error Responses

The ingress middleware intercepts non-compliant payloads before route handler execution:

#### 1. Payload Too Large (`413 Content Too Large`)
Returned when inbound `Content-Length` exceeds the 15MB bounded limit:
```json
{
  "success": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Payload size 18452093 bytes exceeds maximum allowed limit of 15728640 bytes (15MB).",
    "reason_code": "PAYLOAD_TOO_LARGE",
    "details": null
  },
  "correlation_id": "req-98fa-1204b",
  "timestamp": "2026-11-01T10:45:12.384Z"
}
```

#### 2. Unsupported Media Type (`415 Unsupported Media Type`)
Returned when an inbound request specifies an executable or prohibited MIME type (e.g. `application/x-sh`, `application/x-msdownload`, `.exe`, `.bat`):
```json
{
  "success": false,
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "Content-Type application/x-sh is strictly prohibited.",
    "reason_code": "UNSUPPORTED_MEDIA_TYPE",
    "details": null
  },
  "correlation_id": "req-98fa-1204b",
  "timestamp": "2026-11-01T10:45:12.384Z"
}
```

### Distributed Correlation & Ingress Headers
* **`X-Correlation-ID`**: Propagated across all inbound requests and echoed in response headers and envelopes. If omitted by the client, the control plane generates a UUID4 identifier.
* **Security Headers**: All responses return `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and production HSTS.

---

## Core Endpoint Dictionary

### 1. Health & Observability

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/liveness` | Public | Confirms FastAPI process is alive and accepting connections. |
| `GET` | `/api/v1/health/readiness` | Public | Validates PostgreSQL pool connectivity and ONNX model registry readiness. |
| `GET` | `/api/v1/health/metrics` | Public | Prometheus exposition format metrics (process uptime, memory, invariants). |

---

### 2. Academic Administration

| Method | Endpoint | Role Guard | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academic/departments` | Authenticated | Lists all academic departments (e.g. CSE, ECE, ME). |
| `POST` | `/api/v1/academic/departments` | `ADMIN` | Creates an academic department. |
| `GET` | `/api/v1/academic/offerings` | Authenticated | Lists active subject offerings for the current academic term. |
| `POST` | `/api/v1/academic/offerings` | `ADMIN` | Instantiates a subject offering. |
| `GET` | `/api/v1/academic/students` | Authenticated | Retrieves student directory roster with enrollment statuses. |
| `POST` | `/api/v1/academic/students` | `ADMIN` | Registers a new student into an academic cohort. |
| `POST` | `/api/v1/academic/faculty-assignments` | `ADMIN` | Assigns an instructor to an offering or joint class group. |
| `POST` | `/api/v1/academic/groups` | `ADMIN` | Creates an approved joint class group merging multiple cohorts. |

---

### 3. Session Management & Photo Ingress

| Method | Endpoint | Role Guard | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/sessions` | `FACULTY` | Initializes session, verifies faculty assignment, and freezes immutable roster. |
| `GET` | `/api/v1/sessions/{session_id}` | `FACULTY` | Returns session lifecycle state and planned unit count. |
| `GET` | `/api/v1/sessions/{session_id}/roster` | `FACULTY` | Returns the frozen roster snapshot of eligible students. |
| `POST` | `/api/v1/sessions/{session_id}/batches/{batch_id}/frames` | `FACULTY` | Ingests classroom photo frame (`multipart/form-data`), checks SHA-256, and enqueues worker job. |
| `POST` | `/api/v1/sessions/{session_id}/units/{unit_index}/confirm` | `FACULTY` | Explicitly records whether instructional unit was conducted. |

---

### 4. Faculty Review & Atomic Commit

| Method | Endpoint | Role Guard | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/sessions/{session_id}/proposal` | `FACULTY` | Returns evidence candidate proposals aggregated across multi-frame sightings. |
| `POST` | `/api/v1/sessions/{session_id}/commit` | `FACULTY` | Executes atomic ACID commit of attendance decisions, returning a cryptographic receipt. |
| `GET` | `/api/v1/offerings/{offering_id}/analytics` | Authenticated | Computes per-student attendance percentages based on conducted unit records. |
| `GET` | `/api/v1/audit/events` | `ADMIN` | Retrieves immutable audit trail with biometric data redacted. |

---

## Detailed Payload Examples

### Session Creation (`POST /api/v1/sessions`)
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "offering_id": "OFF-CS401-2026",
    "class_group_id": null,
    "planned_units": 2
  }'
```

### Attendance Commit (`POST /api/v1/sessions/{session_id}/commit`)
```bash
curl -X POST http://localhost:8000/api/v1/sessions/SES-94A1F8/commit \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "IDEMP-9a8f2301b4c9284102941829",
    "conducted_unit_indices": [1, 2],
    "decisions": [
      {
        "student_id": "STU-001",
        "unit_index": 1,
        "status": "PRESENT_CONFIRMED",
        "reason_code": "FACULTY_FINAL_COMMIT"
      },
      {
        "student_id": "STU-001",
        "unit_index": 2,
        "status": "PRESENT_CONFIRMED",
        "reason_code": "FACULTY_FINAL_COMMIT"
      }
    ]
  }'
```

### Commit Receipt Response (`200 OK`)
```json
{
  "success": true,
  "data": {
    "id": "RCP-8FA1B920",
    "session_id": "SES-94A1F8",
    "idempotency_key": "IDEMP-9a8f2301b4c9284102941829",
    "committed_by_user_id": "FAC-CS-101",
    "total_conducted_units": 2,
    "total_present_records": 42,
    "total_absent_records": 3,
    "receipt_hash": "0x8fa1b9204c3e77a1d5e6f8a29b04c81729384910293847561029384756102938",
    "committed_at": "2026-11-01T10:48:30.120Z"
  },
  "correlation_id": "commit-sess-94a1f8",
  "timestamp": "2026-11-01T10:48:30.150Z"
}
```

