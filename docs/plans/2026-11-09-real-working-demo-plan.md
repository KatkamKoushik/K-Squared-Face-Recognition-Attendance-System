# FRS V7.1 K² — Live Demo Remediation & Action Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **Branch Constraint:** All changes are isolated on `feat/real-demo-readiness`. No commits to `main` without explicit user permission.

**Goal:** Remediate all P0 blockers identified in the Live Demo Readiness Audit (Doc ID: `K2-LIVE-DEMO-2026-11-10`) to deliver an authentic, controlled end-to-end classroom attendance proof for 10 November 2026 with real physical camera capture, genuine YuNet/SFace ONNX inference, 5-landmark alignment, consented volunteer enrollments, and server-verified HMAC receipts.

**Architecture:**
1. **Model Runtime & Fail-Closed Integrity**: Download verified OpenCV Zoo YuNet and SFace ONNX artifacts to `backend/models/`. Strip synthetic mock fallbacks from `DetectorAdapter` and `RecognizerAdapter` under live mode.
2. **5-Landmark SFace Alignment**: Replace simple rectangular bounding-box cropping with `cv2.FaceRecognizerSF.alignCrop` using YuNet's 5 facial landmarks for mathematical consistency between enrollment and query images.
3. **Real Ingress & Volunteer Enrollment**:
   - Provide `scripts/enroll_student_face.py` to extract and persist real 128-D aligned embeddings for 2–3 consenting demo volunteers.
   - Wire `CaptureGalleryScreen` to retain actual camera bytes and upload them via `_api.uploadFrame()`.
4. **Client Hardening & Server Adjudication**: Remove client-side default-to-absent behavior (`c.unitAttendance[i] ?? absentConfirmed`) and eliminate all silent substitutions of `MockTeacherData`. Provide a runtime Server URL configuration dialog on `LoginScreen`.
5. **Rehearsal & Operational Runbook**: Create `docs/DEMO_RUNBOOK.md` detailing the 8–10 minute demonstration sequence, LAN/hotspot setup, and fail/retry gates.

**Tech Stack:**
- **Mobile Client**: Flutter 3.27, Dart 3.6, Riverpod 2.6, Image Picker, Crypto, HTTP.
- **Backend & Vision**: Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, OpenCV 4.x (`FaceDetectorYN`, `FaceRecognizerSF`).
- **Tooling**: Docker Compose, Python CLI scripts.

---

### Task 1: Download Real ONNX Model Weights & Enforce Fail-Closed Live Inference (P0-B, P0-D)

**Files:**
- Create: `scripts/download_vision_models.py`
- Modify: `backend/app/worker/adapters/detector_adapter.py`
- Modify: `backend/app/worker/adapters/recognizer_adapter.py`
- Modify: `backend/app/api/v1/health.py`
- Test: `backend/tests/test_model_registry_and_inference.py`

**Step 1: Create `scripts/download_vision_models.py`**
- Downloads:
  - YuNet: `https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx`
  - SFace: `https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx`
- Validates exact SHA-256 checksums:
  - YuNet: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
  - SFace: `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
- Places them into `backend/models/`.

**Step 2: Enforce fail-closed inference in adapters**
- In `DetectorAdapter`:
  - When `LIVE_DEMO` or production environment is active, remove the synthetic two-box fallback. Missing model files or initialization failures must raise `RuntimeError("YuNet ONNX model missing or failed to initialize.")`.
  - On a blank or no-face image, return empty list `[]` (not manufactured boxes).
- In `RecognizerAdapter`:
  - When `LIVE_DEMO` or production environment is active, remove pseudorandom vector generation. If model is unavailable, raise `RuntimeError("SFace ONNX model missing or failed to initialize.")`.

**Step 3: Update `/health/readiness` probe (P0-H)**
- Verify that `backend/models/face_detection_yunet_2023mar.onnx` and `backend/models/face_recognition_sface_2021dec.onnx` physically exist on disk, their SHA-256 hashes match, and both OpenCV detector/recognizer instances successfully initialize.

**Step 4: Verify with pytest**
Run: `python scripts/download_vision_models.py`
Run: `pytest backend/tests/test_model_registry_and_inference.py -v`
Commit: `git commit -m "feat(vision): enforce fail-closed onnx model runtime and verified readiness probe"`

---

### Task 2: Implement 5-Landmark SFace Face Alignment (P0-E)

**Files:**
- Modify: `backend/app/worker/adapters/recognizer_adapter.py`
- Modify: `backend/app/worker/preprocessor.py`
- Modify: `backend/app/worker/worker.py`
- Test: `backend/tests/test_landmark_alignment.py`

**Step 1: Write test for 5-landmark aligned face feature extraction**
- Verify that extracting embedding with `alignCrop(cv_img, face_det_15)` produces consistent embeddings for the same person under varied head tilts and angles.

**Step 2: Implement `align_and_compute_embedding` in `RecognizerAdapter`**
- Use OpenCV's native `FaceRecognizerSF.alignCrop(cv_bgr_img, face_det)` with the 15-float detection output from YuNet.
- Compute the L2-normalized 128-D feature vector from the aligned crop.
- Ensure the exact same alignment method is used for both enrollment photos and query photos.

**Step 3: Update `worker.py` to pass 5 landmarks to recognizer**
- In `execute_job()`, pass the original OpenCV BGR image and the full detection array (including landmarks) to the aligned recognizer path.

**Step 4: Verify and commit**
Run: `pytest backend/tests/test_landmark_alignment.py -v`
Commit: `git commit -m "feat(vision): implement 5-landmark face alignment using FaceRecognizerSF.alignCrop"`

---

### Task 3: Create Real Volunteer Face Enrollment Tool (P0-C)

**Files:**
- Create: `scripts/enroll_student_face.py`
- Create: `scripts/seed_demo_volunteers.py`
- Modify: `backend/app/seeds/kucet_seed.py`
- Test: `backend/tests/test_volunteer_enrollment.py`

**Step 1: Create `scripts/enroll_student_face.py`**
- Command-line tool:
  ```bash
  python scripts/enroll_student_face.py --roll 00622501 --image path/to/selfie.jpg
  ```
- Workflow:
  1. Load image and detect face with YuNet.
  2. Align face using the 5 detected landmarks via `FaceRecognizerSF.alignCrop`.
  3. Extract 128-D L2-normalized SFace embedding.
  4. Find student by roll number in PostgreSQL.
  5. Upsert active `EnrollmentProfile` with the real embedding vector and `sface_128d_v1` namespace.
  6. Confirm output: `"Enrolled Katkam Koushik (00622501) with verified real SFace biometric profile."`

**Step 2: Create `scripts/seed_demo_volunteers.py`**
- Dedicated demo class offering (`CS401-DEMO`) with 2–3 consenting volunteer identities:
  - `00622501`: Katkam Koushik
  - `00622502`: Demo Volunteer A
  - `00622503`: Demo Volunteer B (Withheld consent / manual roll-call)
- Leaves room for genuine `UNKNOWN` observations when a non-enrolled person is captured.

**Step 3: Verify and commit**
Run: `python scripts/enroll_student_face.py --help`
Commit: `git commit -m "feat(enrollment): add cli face enrollment tool and consented volunteer seed script"`

---

### Task 4: Connect Physical Camera Capture & Multipart Upload in Mobile App (P0-A)

**Files:**
- Modify: `apps/teacher_mobile/lib/logic/session_provider.dart`
- Modify: `apps/teacher_mobile/lib/presentation/screens/capture_gallery_screen.dart`
- Modify: `apps/teacher_mobile/lib/core/network/api_service.dart`

**Step 1: Retain real image file path and bytes in `capturedFrames`**
- In `CaptureGalleryScreen`:
  - When `ImagePicker.pickImage` succeeds, retain `photo.path` and file length in `capturedFrames`.
  - Remove `_simulateCapture()` fallback on camera error. If camera access fails, display a clear user-facing error snackbar and stop.

**Step 2: Implement sequential multipart upload in `submitBatchForProcessing()`**
- In `session_provider.dart`:
  - Set state to `SessionState.processing`.
  - Sequentially upload each frame using `_api.uploadFrame(sessionId: state.sessionId, batchId: state.batchId, frameIndex: i, imageBytes: bytes, filename: 'frame_$i.jpg')`.
  - Show upload progress: `"Uploading photo 1 of 2 to server..."`.
  - Verify that the server returns HTTP 201 with matching SHA-256 checksum.

**Step 3: Poll server proposal with fail-closed handling**
- Poll `GET /sessions/{id}/proposal`.
- If server returns candidates, set `state.candidates`.
- Set `state.unassignedObservations` from server data (remove all `MockTeacherData` injection).
- If server returns an error or times out, display an explicit retry banner. Do NOT substitute mock candidates.

**Step 4: Verify with mobile tests**
Run: `cd apps/teacher_mobile && flutter analyze && flutter test`
Commit: `git commit -m "feat(mobile): upload real camera bytes via multipart and remove simulated capture"`

---

### Task 5: Eliminate Mock Fallbacks & Enforce Complete Adjudication Matrix (P0-F, P0-G)

**Files:**
- Modify: `apps/teacher_mobile/lib/core/network/api_service.dart`
- Modify: `apps/teacher_mobile/lib/presentation/screens/login_screen.dart`
- Modify: `apps/teacher_mobile/lib/presentation/screens/proposal_review_screen.dart`

**Step 1: Add dynamic Server Configuration on `LoginScreen`**
- Add a settings icon button in AppBar opening a Server Endpoint configuration dialog.
- Allow entering Server URL (e.g. `http://192.168.1.15:8000/api/v1` or an ngrok tunnel).
- Include "Test Connection" button hitting `/health/liveness` and displaying green/red status badge.
- Persist configured URL so it survives app restarts.

**Step 2: Eliminate mock fallbacks in `FrsApiService`**
- When in live mode:
  - `getAssignedOfferings()` throws on failure instead of returning `sampleOfferings`.
  - `createSession()` throws on failure instead of generating local `SES-*` ID.
  - `getSessionProposal()` throws on failure instead of returning `getInitialCandidates()`.

**Step 3: Remove absent default on commit (P0-G)**
- In `api_service.dart` and `proposal_review_screen.dart`:
  - Remove `c.unitAttendance[i] ?? AttendanceStatus.absentConfirmed`.
  - Validate that every student in the roster has an explicit faculty-adjudicated status for each conducted unit before allowing the commit button to be enabled.

**Step 4: Verify and commit**
Run: `cd apps/teacher_mobile && flutter test`
Commit: `git commit -m "feat(mobile): eliminate silent mock substitutions and enforce complete decision matrix"`

---

### Task 6: Build Updated Android APK & Prepare Demo Runbook

**Files:**
- Create: `docs/DEMO_RUNBOOK.md`
- Build: Updated Android APK
- Update: GitHub Release asset

**Step 1: Create `docs/DEMO_RUNBOOK.md`**
- Document the 8–10 minute demonstration walkthrough:
  1. Pre-demo verification (models loaded, database migrations run, volunteer face enrolled).
  2. Mobile device connection over Wi-Fi / hotspot or ngrok.
  3. Live camera photo capture and upload acknowledgement.
  4. Real worker inference with model hashes.
  5. Live candidate review (enrolled volunteer, unknown face, low-quality observation).
  6. Explicit faculty adjudication and HMAC receipt verification.
  7. Disposable database cleanup procedure post-demo.

**Step 2: Compile & distribute release APK**
- Build release APK with dynamic server endpoint support.
- Upload/update the APK asset in GitHub Releases for immediate installation on the demo phone.

**Step 3: Final verification**
- Rehearse the full flow twice on physical device.
- Ensure `main` remains untouched.
