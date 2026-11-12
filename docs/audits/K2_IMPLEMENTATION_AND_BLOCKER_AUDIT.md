# K² FRS — Implementation & Blocker Audit

**Document ID:** `K2-AUDIT-2026-11-09-MONOREPO-UPGRADE`  
**Date:** 9 November 2026  
**Repository:** `KatkamKoushik/K-Squared-Face-Recognition-Attendance-System`  
**Starting Commit Baseline:** `97b6f8a` (`feat: live demo readiness with real camera capture, onnx inference, and 5-landmark face alignment`)  
**Target Feature Branch:** `feat/k2-kaggle-strict-enrollment-admin`  

---

## 1. Executive Summary & Audit Methodology

This audit inspects the checked-out codebase across backend Python services, Flutter mobile client, Next.js admin console, Docker infrastructure, and CI/CD pipelines. Every finding has been verified against the physical files on disk rather than inherited assumptions.

The inspection surveyed exact occurrences of `strict_mode`, `fallback`, `mock`, `synthetic`, `dummy`, `placeholder`, `default`, `except Exception`, `return PASS`, `absentConfirmed`, and `debug keystore`.

---

## 2. Classified Findings Matrix

### 2.1 Confirmed Defects

| ID | Component | Location | Defect Description |
| :--- | :--- | :--- | :--- |
| **DEF-01** | **PAD Gate Fail-Open** | `backend/app/worker/adapters/pad_adapter.py` (lines 42–49 & 87–94) | When `face_crop is None` or any texture analysis exception occurs, PAD returns `SecurityResult(is_live=True, score=0.92, status="PASS")` or `score=0.88, status="PASS"`. Also `mandatory=False` returns `SKIPPED` with `is_live=True`. An error, missing crop, or uncertain texture variance must fail closed into distinct states (`PASS`, `FAIL`, `UNCERTAIN`, `ERROR`, `NOT_CONFIGURED`). |
| **DEF-02** | **Fabricated Inference & Random Vectors** | `backend/app/worker/adapters/detector_adapter.py` (lines 128–142) & `recognizer_adapter.py` (lines 91–101, 133–140) | When `strict_mode=False` or models fail to initialize, `detector_adapter` manufactures two fixed bounding boxes, and `recognizer_adapter` generates pseudorandom 128-D vectors on $S^{127}$. Furthermore, `backend/app/api/v1/health.py` instantiated both adapters with `strict_mode=False`, masking missing weight conditions. |
| **DEF-03** | **Silent Attendance Absence Fallback** | `apps/teacher_mobile/lib/core/network/api_service.dart` (line 277) & `session_provider.dart` (line 275) | In Flutter, unreviewed candidate decisions silently fell back to `AttendanceStatus.absentConfirmed` (`units[i] ??= c.proposalStatus ?? AttendanceStatus.absentConfirmed`). Faculty decisions must be explicitly required for each conducted unit, failing validation in UI if unadjudicated. |
| **DEF-04** | **Docker Model Delivery & Compose Volume Gaps** | `docker-compose.yml`, `docker-compose.prod.yml`, `.github/workflows/deploy.yml` | Neither compose file mounts the host `backend/models` directory into containers. In `docker-compose.prod.yml`, `vision-worker` points to `Dockerfile` instead of `Dockerfile.worker`. In `deploy.yml`, container builds run without downloading vision models first, meaning GHCR images lack ONNX weights. |
| **DEF-05** | **Insecure Android Release Keystore Fallback** | `apps/teacher_mobile/android/app/build.gradle.kts` (lines 43–61) & `.github/workflows/deploy.yml` (lines 78–86) | Gradle builds automatically generate a temporary `debug.keystore` when release signing variables are absent. The CD workflow does not fail if `KEYSTORE_BASE64` is missing, risking non-reproducible releases signed with debug keys. |
| **DEF-06** | **Admin Console Route Inversion & Hardcoded Mock Data** | `apps/admin_console/app/page.tsx` & `layout.tsx` | The root page (`/`) renders an admin dashboard with hardcoded statistics (`1,420` students) and mock sessions instead of a public student enrollment portal. `layout.tsx` renders the admin sidebar and header on all pages, preventing a public landing experience. |

### 2.2 Potential Defects Requiring Verification

| ID | Component | Location | Risk & Verification Plan |
| :--- | :--- | :--- | :--- |
| **POT-01** | **Model Hash Integrity Check** | `detector_adapter.py`, `recognizer_adapter.py` | Adapters have `MODEL_HASH` class constants, but they do not actively compute the SHA-256 checksum of the resolved file on disk before calling OpenCV C++ bindings. If a corrupted ONNX file is present, it could crash the C++ runtime. Active hash verification against an approved manifest must be added. |
| **POT-02** | **Image Metadata & Sanitization** | `backend/app/services/ingress_service.py` | Uploaded frames and student enrollment portraits must be decoded, checked for dimension/aspect limits, and stripped of sensitive EXIF/GPS metadata before disk persistence. |

### 2.3 Missing Implementations

| ID | Component | Location | Required Implementation |
| :--- | :--- | :--- | :--- |
| **MIS-01** | **Kaggle Model Lab** | `research/kaggle_model_lab/` | Self-contained model lab folder with `README.md`, `requirements-kaggle.txt`, valid `.ipynb` notebook, modular scripts `00_environment_audit.py` through `06_export_model_manifest.py`, and configuration files targeting Kaggle T4x2 environment. |
| **MIS-02** | **Public Student Enrollment Website** | `apps/admin_console/app/page.tsx` (Route `/`) | Clean, responsive, mobile-first student enrollment portal explaining biometric usage, capturing institutional roll number, name, email, department, cohort, consent acknowledgment, and photo upload. |
| **MIS-03** | **Protected Admin Portal** | `apps/admin_console/app/admin/` | Dedicated `/admin` route structure with login guard, live database-backed metrics, student enrollment queue review, image inspection, approval/rejection actions, and audit trail view. |
| **MIS-04** | **Backend Enrollment Submission Lifecycle** | `backend/app/domain/models/student.py` & `backend/app/api/v1/enrollment.py` | Persistent `EnrollmentSubmission` model (`PENDING_REVIEW`, `RECAPTURE_REQUIRED`, `APPROVED`, `REJECTED`, `WITHDRAWN`), Alembic migration, private photo storage, and approval endpoint triggering real YuNet + SFace embedding generation. |

### 2.4 Already Fixed and Verified

| ID | Component | Evidence |
| :--- | :--- | :--- |
| **FIX-01** | **Real Camera Byte Upload** | `apps/teacher_mobile/lib/presentation/screens/capture_gallery_screen.dart` uploads physical JPEG bytes via multipart `uploadFrame`. Simulated capture removed. |
| **FIX-02** | **5-Landmark SFace Face Alignment** | `backend/app/worker/adapters/recognizer_adapter.py` applies `cv2.FaceRecognizerSF.alignCrop` with 5 facial landmarks from YuNet. |
| **FIX-03** | **Git Main History Protection** | All changes squashed and merged into `main` at `97b6f8a`. New work strictly isolated on feature branch `feat/k2-kaggle-strict-enrollment-admin`. |
| **FIX-04** | **Release APK CI/CD Delivery** | Release workflow fixed in `deploy.yml`, generating `1.0.0` release asset successfully. |

### 2.5 Blocked by External Dependencies or Authorization

| ID | Component | Blocker Description |
| :--- | :--- | :--- |
| **BLK-01** | **Institutional Biometric Dataset** | Official KUCET student photographs cannot be collected or processed without formal institutional ethics review and biometric consent agreements. Synthetic smoke tests and consented volunteer profiles must be used for testing. |
| **BLK-02** | **Physical Kaggle Hardware Execution** | Kaggle T4x2 GPUs exist in Google Kaggle cloud infrastructure. The notebook and scripts can be fully authored, tested for syntax, and validated locally, but execution on T4x2 occurs when imported into Kaggle. |

---

## 3. Action Plan & Phased Implementation Path

1. **Phase 2 — Strict Mode & Error Transparency:** Remove all synthetic detection/embedding fallbacks. Make missing models, bad hashes, and unreadable files fail closed with typed errors. Fix `pad_adapter.py` to never return `PASS` on error, missing crop, or uncertain textures.
2. **Phase 3 — Attendance Decision Integrity:** Enforce explicit faculty adjudication in `session_provider.dart` and `api_service.dart`. Reject unadjudicated submissions without silent defaults.
3. **Phase 4 — Model Delivery Pipeline:** Add volume mounts in `docker-compose.yml` and `docker-compose.prod.yml`. Update `Dockerfile.worker` usage. Add model download step in CD container build.
4. **Phase 5 — Persistent Android Release Signing:** Remove debug keystore generation in release builds. Fail build if `KEYSTORE_BASE64` is missing.
5. **Phase 6 — Kaggle Model Lab:** Build complete `research/kaggle_model_lab/` directory, notebook, scripts, and documentation.
6. **Phase 7 & 8 — Public Student Portal & Admin Portal:** Create public student enrollment at `/` and protected administrative portal at `/admin`. Implement backend `EnrollmentSubmission` model, private storage, and approval workflow.
7. **Phase 9, 10 & 11 — Integration, Migrations, Tests & CI Verification:** Create Alembic migrations, write backend/frontend tests, and verify tests pass.
8. **Phase 12 — Commit & Push Feature Branch:** Verify `main` remains untouched, commit to `feat/k2-kaggle-strict-enrollment-admin`, and push.
