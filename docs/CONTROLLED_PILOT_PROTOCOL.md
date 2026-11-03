# FRS V7.1 K² — Controlled Institutional Pilot Protocol & Operational Plan

Document ID: `KUCET-PILOT-PROTO-V7.1`  
Target Institution: Kakatiya University College of Engineering & Technology (KUCET), Warangal - 506009  
Academic Term: Odd Semester 2026-2027 (VII Semester)  
Supervising Department: Department of Computer Science & Engineering  
Lead Faculty Coordinator: Mr. V. Ramana Babu, Assistant Professor & Coordinator (CSE)  
Target Cohort: B.Tech CSE Class of 2026 (Final Year IV/IV Sec A) — 66 Students  
Target Course Offering: CS401 — Distributed Systems & Cloud Computing  
Protocol Status: APPROVED FOR SUPERVISED CONTROLLED EXECUTION  

---

## 1. Executive Mission & Controlled Scope

The objective of this protocol is to conduct an authoritative, controlled 14-day institutional pilot of the **FRS V7.1 K² Classroom Attendance Proposal System** at KUCET Warangal.

Under this protocol, the computer vision subsystem functions strictly as an **evidence producer**, not an autonomous decision maker. Attendance recording operates in a **Dual-Ledger Mode**:
1. **Primary Legal Ledger**: The physical university attendance register maintained by the course instructor.
2. **Evaluation Ledger**: The FRS V7.1 K² PostgreSQL immutable transaction ledger populated via multi-photo camera sweeps, faculty review adjudication, and cryptographic HMAC-SHA256 commit receipts.

> [!IMPORTANT]
> At no point during the 14-day controlled pilot shall an automated computer vision inference result directly disadvantage a student. Any discrepancy between the physical roll call and the proposal system must be resolved in favor of the instructor's physical observation.

---

## 2. Predeclared Quantitative Performance Targets

Before initiating classroom photo sweeps, the pilot team establishes strict mathematical acceptance thresholds:

| Metric | Target Specification | Mathematical Definition | Pilot Gate Requirement |
| :--- | :--- | :--- | :--- |
| **True Accept Rate (TAR)** | $\ge 95.0\%$ | $\frac{\text{Correctly Proposed Present Students}}{\text{Physically Present Students}}$ | Must exceed 95% under standard classroom lighting ($\ge 300\text{ lux}$) |
| **Open-Set False Accept Rate (FAR)** | Strictly $0.0\%$ | $\frac{\text{Unregistered / Impostor Sightings Accepted}}{\text{Total Impostor Sightings}}$ | Zero tolerance ($0/N$ false matches). Unknowns must route to `UNKNOWN` or `REVIEW` |
| **Ambiguity Safety Margin** | $T_{\text{margin}} \ge 0.10$ | $s_{\text{top1}} - s_{\text{top2}} \ge 0.10$ | Lookalikes with margin $< 0.10$ must force faculty adjudication |
| **Faculty Review Overhead** | $\le 60\text{ seconds}$ | Median instructor review time per session | Must not disrupt lecture instructional delivery |
| **DPDP Consent Compliance** | $100.0\%$ | $\frac{\text{Manual Roll-Calls for Withheld Consent}}{\text{Eligible Withheld Students}}$ | Zero academic disadvantage for students exercising non-biometric rights |
| **Ledger ACID Invariant** | $100.0\%$ | Total records $= N_{\text{students}} \times N_{\text{conducted\_units}}$ | Zero missing Cartesian cells; zero duplicate student-unit records |

---

## 3. Approved Vision Model Registry & Integrity Constraints

All inference during the pilot executes exclusively on approved on-premise artifacts registered in the institutional model catalog:

```
+---------------------------------------------------------------------------------------+
| Approved Face Detector: face_detection_yunet_2023mar.onnx                            |
| Task: DETECTION | Format: ONNX | License: MIT | Provenance: WIDER FACE Benchmark       |
| SHA-256: 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4           |
| Input Dimensions: 320x320 | Color Order: BGR                                          |
+---------------------------------------------------------------------------------------+
| Approved Face Recognizer: face_recognition_sface_2021dec.onnx                        |
| Task: RECOGNITION | Format: ONNX | License: Apache-2.0 | Provenance: CASIA-WebFace    |
| SHA-256: 0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79           |
| Embedding Space: 128-D L2-Normalized on S^127 | Match Threshold: T_match = 0.70       |
+---------------------------------------------------------------------------------------+
```

---

## 4. Standard Operating Procedure (SOP) for Course Faculty

### Step 1: Pre-Lecture Setup (T - 2 minutes)
1. Faculty launches the **Teacher Mobile Application** on the institutional tablet.
2. Selects course offering `CS401: Distributed Systems & Cloud Computing`.
3. Selects number of instructional units conducted for the session (1 to 4 units; typically 2 units for standard lecture blocks).
4. System freezes the roster snapshot of eligible students enrolled in the offering.

### Step 2: Multi-Photo Classroom Sweep (T + 5 minutes)
1. Faculty captures 2 to 4 wide-angle burst sweep photographs covering:
   - Left classroom rows (desks 1–11).
   - Center classroom rows (desks 12–22).
   - Right classroom rows (desks 23–33).
2. The mobile client computes a local SHA-256 checksum over the raw frame bytes before transmission to the on-premise FastAPI control plane.
3. The background ONNX vision worker leases the job, executes YuNet face detection and SFace feature extraction, and populates candidate proposals.

### Step 3: Candidate Proposal Review & Adjudication (T + 8 minutes)
1. Faculty opens the **Review Proposals Screen**:
   - **Green Cards (`CANDIDATE`)**: Sightings exceeding $T_{\text{match}} \ge 0.70$ with ambiguity margin $\ge 0.10$. Pre-populated as `PRESENT_CONFIRMED`.
   - **Amber Cards (`REVIEW`)**: Ambiguous lookalikes or low-quality sightings. Requires one-tap faculty confirmation (`PRESENT` or `ABSENT`).
   - **Purple Cards (`DPDP NON-BIOMETRIC ALTERNATIVE`)**: Students who withheld biometric consent. Faculty verbally checks student presence and marks status.
   - **Orange Cards (`NO CAMERA SIGHTING`)**: Unsighted students. Faculty confirms physical absence or manually overrides if seated outside camera angle.

### Step 4: Atomic Commit & Cryptographic Receipt (T + 10 minutes)
1. Faculty taps **Review Units & Confirm Commit**.
2. Client submits the complete $N \times U$ decision matrix with a cryptographic idempotency key.
3. Control plane commits the records in an atomic PostgreSQL transaction and emits an **HMAC-SHA256 signed Commit Receipt**.
4. Both physical register and mobile receipt are archived.

---

## 5. DPDP Act Student Rights & Dispute Resolution

### 5.1 Biometric Consent Register
1. Under Sections 6 and 12 of the Digital Personal Data Protection Act, every student has the statutory right to withhold or withdraw biometric consent without prejudice to their academic standing.
2. For students with withheld consent (`is_active = False` on `enrollment_profiles`), the vision pipeline strictly ignores their facial features. The mobile app prompts the instructor for a non-biometric manual roll call.

### 5.2 Post-Commit Corrections & Student Appeals
If a student disputes an absence:
1. Student submits an academic attendance appeal to the CSE Department Head within 7 academic days.
2. Upon verification with classroom attendance logs or medical certification, the authorized instructor or administrator invokes:
   ```http
   POST /api/v1/ledger/corrections
   Content-Type: application/json
   
   {
     "student_id": "STU-KUCET-00622504",
     "unit_index": 1,
     "new_status": "PRESENT_CONFIRMED",
     "action_type": "APPEAL",
     "reason": "HOD approved medical memo ref: KUCET/CSE/2026/MED-019",
     "reference_document": "KUCET/CSE/2026/MED-019"
   }
   ```
3. The correction creates an immutable `audit_ledger_events` row linking previous status, new status, justification, and timestamp.

---

## 6. Ephemeral Data Purging & Retention Schedule

To respect student privacy and conserve institutional server storage:
1. Raw classroom photograph sweeps are stored in temporary volume storage (`/data/frames`).
2. Post-finalization, a background retention daemon executes `GovernanceService.purge_ephemeral_storage(retention_days=7)`.
3. Physical frame files older than 7 days are wiped from disk (`os.unlink`).
4. An immutable audit event (`DATA_PURGE_EXECUTED`) records total purged frames and freed storage bytes.

---

## 7. Pilot Success Criteria & Go/No-Go Decision Rules

At the conclusion of the 14-day pilot, the Institutional Review Board shall review the **Pilot Readiness Dossier**:

1. **GO Decision**:
   - Zero open-set false acceptance events across all 14 days ($0.0\%$ FAR).
   - True Accept Rate $\ge 95.0\%$.
   - $100.0\%$ student appeal resolution within policy timelines.
   - Zero physical frame leakage or unpurged images beyond the 7-day retention policy.
   - Zero data corruption or mathematical denominator errors in attendance reports.

2. **NO-GO Decision**:
   - Any unadjudicated wrong-person attendance commit.
   - Failure of the non-biometric fallback causing academic penalty to a consent-withheld student.
   - Unauthorized database tampering or broken receipt HMAC signatures.

