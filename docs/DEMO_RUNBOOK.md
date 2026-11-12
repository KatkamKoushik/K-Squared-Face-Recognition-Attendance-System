# K² FRS — Live Demonstration Runbook

**Document ID:** `K2-DEMO-RUNBOOK-2026-11-10`  
**Target Date:** 10 November 2026  
**Demonstration Scope:** Controlled Technical Proof (Real Camera &rarr; Real YuNet &rarr; 5-Landmark SFace &rarr; Server Consensus &rarr; HMAC Ledger)

---

## 🛑 Pre-Flight Go / No-Go Checklist

Before presenting to an audience, verify all 6 exit gates pass:
- [ ] **Gate 1 (Models Present & Verified):** Both `face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx` are in `backend/models/` and pass SHA-256 verification.
- [ ] **Gate 2 (Readiness Probe 200 OK):** `curl -s http://localhost:8000/api/v1/health/readiness | jq .data.models_runtime` reports `runtime_ready: true`.
- [ ] **Gate 3 (Demo Volunteer Enrolled):** At least one presenter/volunteer face enrolled into PostgreSQL via `python scripts/enroll_student_face.py`.
- [ ] **Gate 4 (Network Reachable):** Mobile app taps "Test Connection" on Login Screen and displays green `Connected successfully (HTTP 200)`.
- [ ] **Gate 5 (Real Upload Verified):** Camera photo bytes are uploaded via multipart POST; server responds HTTP 201 with matching hash.
- [ ] **Gate 6 (Server Receipt):** Final commit generates an authoritative server HMAC-SHA256 receipt (no local client-minted receipts).

---

## ⚡ 15-Minute Pre-Demo Setup

### Step 1: Start Backend Infrastructure
```bash
# Start PostgreSQL database, FastAPI control plane, and vision worker
docker compose up -d postgres backend-api vision-worker

# Or if running locally without Docker:
cd backend
alembic upgrade head
python -m uvicorn app.main:create_application --factory --host 0.0.0.0 --port 8000 &
python -m app.worker.worker &
```

### Step 2: Download & Verify Approved Vision Weights
```bash
python scripts/download_vision_models.py
```
*Expected Output:*
```
[VERIFIED] face_detection_yunet_2023mar.onnx verified successfully (8f2383e4...)
[VERIFIED] face_recognition_sface_2021dec.onnx verified successfully (0ba9fbfa...)
[SUCCESS] All approved vision models verified and ready for live demo inference.
```

### Step 3: Prime Controlled Demo Offering & Roster
```bash
python scripts/seed_demo_volunteers.py
```
*Expected Output:*
```
[SUCCESS] Controlled demo environment successfully primed.
          Faculty     : Dr. V. Ramana (ramana.vrb@gmail.com)
          Offering    : CS401 Section DEMO
          Demo Roster : 3 students (including 1 consent-withheld manual check)
```

### Step 4: Enroll Presenter's Face (Real Biometric Profile)
Take a quick, clear selfie on your phone or laptop camera (`presenter.jpg`):
```bash
python scripts/enroll_student_face.py --roll 00622501 --image presenter.jpg
```
*Expected Output:*
```
[INFO] Detected primary face: score=0.982, box=(...)
[INFO] Computing 5-landmark aligned SFace 128-D embedding (FaceRecognizerSF.alignCrop)...
[SUCCESS] Successfully enrolled Katkam Koushik (00622501)!
```

### Step 5: Verify API & Worker Readiness
```bash
curl -s http://localhost:8000/api/v1/health/readiness | jq .
```
Verify `"status": "READY"` and `"runtime_ready": true`.

---

## 📶 Network Setup: Connecting Android Phone to Laptop

### Option A: Local Wi-Fi / Mobile Hotspot (Recommended)
1. Connect both laptop and Android phone to the same Wi-Fi router or turn on Phone Mobile Hotspot and connect laptop.
2. Find laptop LAN IP:
   - Linux/Mac: `ip addr show` or `ifconfig` &rarr; look for `192.168.x.x` (e.g. `192.168.1.55`)
   - Windows: `ipconfig`
3. In the Teacher Mobile app:
   - On the Login screen, tap the ⚙️ **Settings** icon in the top right.
   - Enter `http://192.168.1.55:8000/api/v1` (replace with your laptop IP).
   - Tap **Test Connection** &rarr; Verify green badge: `Connected successfully (HTTP 200)`.
   - Tap **Apply**.

### Option B: Public Secure Tunnel (ngrok)
If university/guest Wi-Fi blocks peer-to-peer traffic between devices:
```bash
ngrok http 8000
```
Copy the forwarding URL (e.g. `https://abc-123.ngrok-free.app`). In the Teacher Mobile app:
- Set API URL: `https://abc-123.ngrok-free.app/api/v1`
- Tap **Test Connection** &rarr; Verify `Connected successfully`.

---

## 🎬 8–10 Minute Live Demonstration Script

| Time | Phase | Spoken Narrative & Actions |
| :--- | :--- | :--- |
| **0:00 - 1:00** | **Faculty Authentication** | "We begin on the KUCET Teacher Mobile Client. Tap 'Load seeded faculty account' (Dr. V. Ramana, CSE). Observe our server endpoint is pointed directly to our live FastAPI control plane. Tap **Sign In**. The client authenticates and receives an institutional JWT bearer token." |
| **1:00 - 2:00** | **Offering & Roster Freeze** | "The app queries `GET /academic/offerings` from PostgreSQL. We select **CS401 Distributed Systems (Section DEMO)**. The server permanently freezes an immutable roster snapshot with 3 enrolled students, ensuring live enrollments cannot tamper with an ongoing session." |
| **2:00 - 3:00** | **Session Setup & Invariants** | "We set 2 conducted instructional units. In accordance with Indian institutional guidelines, attendance denominators are calculated strictly per conducted unit hour rather than per day." |
| **3:00 - 4:30** | **Real Camera Photo Capture** | "Now for the classroom capture. We hold the phone in landscape and take 2 live sweeps of the room (or select our high-res classroom sample). Note the exact SHA-256 hash calculated on-device for non-repudiation." |
| **4:30 - 6:00** | **Multipart Upload & Vision Worker** | "We tap **Upload & Process Photos**. Observe the progress indicator: the app streams real JPEG bytes via multipart HTTP to `/sessions/.../frames`. The backend vision worker immediately claims the job, loads OpenCV Zoo YuNet for face detection, aligns crops using 5 facial landmarks, and computes 128-D SFace feature vectors on unit hypersphere $\mathbb{S}^{127}$." |
| **6:00 - 7:30** | **Proposal Review & DPDP Compliance** | "The server returns candidate proposals: <br>1. **Katkam Koushik (00622501)** is matched as **PRESENT** with high cosine similarity (>0.75).<br>2. **Volunteer B (00622504)** withheld biometric consent under the DPDP Act 2023—the system automatically flags them for **Manual Roll-Call** without penalizing them as absent.<br>3. Non-enrolled faces appear in the **Unassigned Observations** tray as unlinked visitors." |
| **7:30 - 8:30** | **Faculty Adjudication Matrix** | "AI proposals are strictly non-binding. The faculty instructor reviews and confirms each conducted unit. The system prevents silent defaults to absence—every student must be explicitly adjudicated." |
| **8:30 - 9:30** | **Cryptographic HMAC Receipt** | "We tap **Confirm & Commit**. The server validates idempotency, writes atomic ledger rows in PostgreSQL, and generates an authoritative HMAC-SHA256 receipt. The mobile app renders the immutable digital receipt with audit timestamp and server receipt number." |
| **9:30 - 10:00** | **Live Admin Console Verification** | "Switching to the browser at `http://localhost:3000`, the Admin Console immediately reflects the committed session, unit breakdown, and audit log entries in real-time." |

---

## 🧹 Post-Demo Cleanup

After the demonstration, purge disposable demo images and test vectors:
```bash
# Clean up temporary captured frames
rm -rf backend/data/frames/*

# Reset demo session in database
docker compose down -v && docker compose up -d
```
