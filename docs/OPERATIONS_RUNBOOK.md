# FRS V7.1 K² — Production Operations Runbook
*Authoritative Operational Guide for Institutional Attendance Infrastructure at Kakatiya University College of Engineering & Technology (KUCET)*

---

## 1. System Overview & Component Topography

| Subsystem | Technology Stack | Runtime Mode | Default Port / Target | Health Check Probe |
| :--- | :--- | :--- | :--- | :--- |
| **Control Plane API** | FastAPI, SQLAlchemy 2.0 async, Pydantic V2 | Multi-worker Uvicorn (ASGI) | `TCP/8000` (`http://localhost:8000`) | `GET /api/v1/health/readiness` |
| **Vision Worker** | Python 3.12, ONNX Runtime, OpenCV | Background Polling Daemon | Internal Process Queue | Ingress Lease Heartbeat (`job.status == LEASED`) |
| **Admin Web Console** | Next.js 15.5, React 19, Tailwind CSS | Standalone Node.js server | `TCP/3000` (`http://localhost:3000`) | `GET /system/readiness` |
| **Relational Store** | PostgreSQL 16 (Alpine) | ACID Database Container | `TCP/5432` (`postgres_data` volume) | `pg_isready -U postgres -d frs_k2` |
| **Teacher Mobile App** | Flutter 3.27, Dart 3.6+, Riverpod | Client Android APK / iOS binary | Dynamic backend target (`--dart-define`) | Client-side connectivity status listener |

---

## 2. Standard Service Lifecycle Operations

### Starting the Production Stack
```bash
# Launch persistent services with health dependencies
docker compose up -d

# Verify container liveness and container health status
docker compose ps
```

### Checking Real-Time Logs
```bash
# Stream API logs with correlation identifiers
docker compose logs -f backend-api

# Stream vision worker ONNX inference telemetry
docker compose logs -f vision-worker
```

### Applying Database Schema Migrations
```bash
# Execute backward-compatible Alembic upgrade
docker compose exec backend-api alembic upgrade head
```

### Graceful Teardown
```bash
# Gracefully signal SIGTERM and stop containers
docker compose down
```

---

## 3. Database Backup & Disaster Recovery Procedures (Checklist Section 34)

### Recovery Objectives
* **Recovery Point Objective (RPO):** $\le 1$ hour.
* **Recovery Time Objective (RTO):** $\le 15$ minutes.

### Automated Database Backup
Execute the scheduled backup script or run manual dump:
```bash
# Create timestamped SQL snapshot
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -t postgres pg_dump -U postgres -d frs_k2 -F c -b -v -f /tmp/frs_backup_${TIMESTAMP}.dump

# Copy backup archive out of container to secure isolated storage
docker cp frs-k2-postgres:/tmp/frs_backup_${TIMESTAMP}.dump ./backups/
```

### Disaster Restore Drill
To restore the authoritative database from backup:
```bash
# 1. Stop write-capable API and Worker containers
docker compose stop backend-api vision-worker

# 2. Restore PostgreSQL schema and ledger data
docker compose exec -T postgres pg_restore -U postgres -d frs_k2 --clean --if-exists -v < ./backups/frs_backup_TARGET.dump

# 3. Restart Control Plane and Worker
docker compose start backend-api vision-worker

# 4. Verify post-restore readiness
curl -f http://localhost:8000/api/v1/health/readiness
```

---

## 4. Emergency Faculty Override & Adjudication Protocol (Checklist Section 44)

In the event of network disruption, sensor failure, or lighting anomalies:
1. **Mobile Fallback:** Faculty opens the **Manual Roll-Call** screen (`manual_attendance_screen.dart`) directly from the mobile app.
2. **Adjudication Sheet:** For ambiguous lookalikes or unrecognized sightings (`UNKNOWN`), faculty manually selects `PRESENT_CONFIRMED` or `ABSENT_CONFIRMED`.
3. **Audit Anchorage:** All post-proposal modifications append an unalterable `ATTENDANCE_COMMITTED` event with `reason_code = FACULTY_FINAL_COMMIT` and a verified cryptographic SHA-256 receipt hash.
4. **Administrative Audit Review:** Administrative officers review overrides on the Next.js Admin Console via `/audit/logs`.

---

## 5. Model Weight Certification & Rotation Gates (Checklist Section 49)

* **Face Detection Artifact:** `scrfd_2.5g_k2_v7.onnx` (G1 Certification Gate Approved).
* **Face Embedding Artifact:** `arcface_w600k_r50_v7.onnx` (512-dimensional output, normalized $\|\mathbf{v}\|_2 = 1.0$).
* **Gate Requirement:** Before deploying updated model weights, candidate ONNX binaries must pass the offline validation benchmark on the golden evaluation gallery with:
  * False Match Rate (FMR) $\le 0.01\%$.
  * False Non-Match Rate (FNMR) $\le 1.5\%$.
  * Deterministic cosine similarity margin $\Delta s \ge 0.15$.

---

## 6. Incident Severity & Escalation Matrix (Checklist Section 35)

| Severity | Definition | Examples | SLA Response | Escalation Channel |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Entire attendance infrastructure unavailable; faculty cannot conduct or commit sessions during exam/class hours. | Database connectivity outage, API crash loop, corrupted attendance receipts. | $\le 15$ minutes | DevOps Lead, Dean Academics |
| **SEV-2 (High)** | Degradation in vision inference; batch jobs queueing without worker processing. | GPU out-of-memory, vision worker starvation, ONNX runtime failure. | $\le 45$ minutes | Computer Vision Engineer, Platform Admin |
| **SEV-3 (Medium)** | Individual mobile device synchronization error; non-blocking UI anomaly. | Rate limit triggered on single IP, image upload retry needed. | $\le 4$ hours | Helpdesk, App Maintainer |
| **SEV-4 (Low)** | Minor cosmetic or documentation inconsistency. | Typo in report text, non-blocking telemetry delay. | Next Sprint | Repository Maintainers |

