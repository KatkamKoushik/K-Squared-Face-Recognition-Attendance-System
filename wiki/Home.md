# FRS V7.1 K² System Documentation

Welcome to the official technical documentation and architecture wiki for the **Facial Recognition System (FRS) V7.1 K²**, designed for institutional deployment at **Kakatiya University College of Engineering & Technology (KUCET)**.

FRS V7.1 K² is an enterprise-grade classroom attendance proposal system. It replaces single-face biometric punch kiosks and legacy attendance registers with a multi-face classroom sweep workflow that preserves strict academic governance and faculty autonomy.

---

## Core System Philosophy

```mermaid
flowchart LR
    A["Raw Classroom Photos"] --> B["ONNX Vision Worker<br/>(YuNet + SFace)"]
    C["Candidate Proposal<br/>(Probabilistic Evidence)"]
    D["Faculty Review & Resolution<br/>(Teacher Mobile Client)"]
    E["Atomic Ledger Commit<br/>(PostgreSQL Immutable Record)"]
    A --> B
    B --> C
    C --> D
    D --> E

    style A fill:#f8fafc,stroke:#94a3b8,color:#0f172a
    style B fill:#e0f2fe,stroke:#0284c7,color:#0369a1
    style C fill:#fef3c7,stroke:#d97706,color:#92400e
    style D fill:#ede9fe,stroke:#7c3aed,color:#6d28d9
    style E fill:#dcfce7,stroke:#16a34a,color:#15803d
```

Unlike commercial black-box attendance software that automatically modifies attendance databases based on opaque recognition scores, FRS V7.1 enforces the **Human-in-the-Loop Proposal Principle**:

1. **Evidence Producer, Not Decision Maker:** The computer vision pipeline acts strictly as an evidence generator. It aggregates sightings, computes cosine similarity metrics, and highlights ambiguities. It cannot unilaterally commit attendance.
2. **Faculty-Governed Commit:** Only the assigned instructor who conducted the academic session can review the proposal, override candidate statuses, resolve unassigned sightings, and execute the final atomic ledger commit.
3. **Immutable Roster Freezing:** Eligibility is evaluated at the start of each session against active semester enrollments and frozen as an immutable roster snapshot. Downstream roster mutations never alter session history.
4. **Denominator Invariant:** Attendance percentages are strictly calculated per student per conducted instructional unit ($1 \le \text{units} \le 4$). Incomplete or unconducted units never skew student records. If zero units are conducted, the attendance percentage evaluates strictly to `N/A`.

---

## Documentation Index

The wiki is organized into seven specialized reference manuals:

| Section | Scope |
| :--- | :--- |
| **[System Architecture](System-Architecture)** | Multi-tier topology, microservices, container boundaries, and network isolation. |
| **[Data Model & State Machines](Data-Model-and-State-Machine)** | Complete 28-table relational schema, entity-relationship diagrams, and state transitions. |
| **[Computer Vision Pipeline](Computer-Vision-Pipeline)** | YuNet detection, SFace 128-d embeddings, open-set rejection threshold ($\tau = 0.363$), and lookalike conflict routing. |
| **[REST API Reference](API-Reference)** | OpenAPI 3.1 endpoint dictionary, envelope specifications, error codes, and DTO contracts. |
| **[Security, Privacy & Governance](Security-Privacy-and-Governance)** | On-premise biometric boundaries, irreversible feature representations, client SHA-256 hashing, and audit trails. |
| **[Operations & Deployment](Operations-and-Deployment)** | Docker Compose deployment, Supabase PostgreSQL with pgvector, Alembic database migrations, and CI/CD pipelines. |
| **[Roadmap & Project Status](Roadmap-and-Project-Status)** | Verification matrix, current release baseline, operational constraints, and development roadmap. |

---

## Project Status At A Glance

* **Current Architecture Version:** V7.1 Canonical (Real-time Cloud & On-Premises)
* **FastAPI Control Plane:** Operational (118 automated unit, security, and persistence tests passing: 117 passed, 1 PG socket probe skip)
* **Playwright Browser E2E:** Operational (15/15 Admin Console browser automation tests passing on Chromium)
* **Database & Vector Search:** Supabase PostgreSQL with `pgvector` extension and SSL encryption active across 28 normalized tables.
* **Computer Vision Inference:** 100% genuine deep learning inference via OpenCV Zoo YuNet (face detection) and SFace (128-d cosine recognition). Zero mockups or simulations. SHA-256 is strictly enforced for ONNX model weights integrity.
* **Teacher Mobile Client:** Implemented with Flutter 3.27.x targeting Android 16 (API 36) on physical hardware (RMX5003). Features primary faculty login for Dr. M. Soujanya (IT Academic Coordinator, `soujanyavedh@gmail.com`), instant endpoint switching (Ngrok Tunnel, Wi-Fi LAN `192.168.0.2`, ADB Reverse `127.0.0.1:8000`, Emulator), and durable offline sync journal.
* **Admin Web Console:** Implemented with Next.js 15.5.28 App Router (15 prerendered routes, cross-tab session broadcasting, crawler exclusion in `public/robots.txt`).
* **Mathematical Invariants:** 5/5 verification suites passing with 100% invariant fidelity.
* **Containerization:** Multi-stage Dockerfiles for backend API, vision worker, and Next.js console validated.

