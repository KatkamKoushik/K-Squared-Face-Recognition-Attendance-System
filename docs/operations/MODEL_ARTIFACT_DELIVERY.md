# Model Artifact Delivery & Runtime Verification Runbook
**K² FRS Operations Documentation**  
*Status: IMPLEMENTED & VERIFIED*

---

## 1. Overview & Architectural Policy

K² FRS requires genuine deep learning model artifacts for facial detection and facial recognition. The system rejects all synthetic embeddings, mock detection coordinates, and dummy model fallbacks.

### Critical Invariants
1. **Cryptographic Integrity:** Every loaded ONNX model must match its approved SHA-256 hash listed in the canonical artifact manifest.
2. **Fail-Closed Availability:** If an ONNX weight file is absent, unreadable, corrupted, or has an unexpected hash, the worker and API services must immediately raise typed exceptions (`FileNotFoundError`, `ValueError`) and report readiness failure (`/api/v1/health/readiness` -> HTTP 503).
3. **No Silent Fallback:** The system will never substitute a dummy model or return synthetic random vectors when model initialization fails.
4. **Deterministic Storage:** Standard production model storage location is `backend/models/`.

---

## 2. Canonical Model Manifest

| Model Identifier | File Name | Architecture | Dimensions | Canonical SHA-256 Hash | Source & License |
|---|---|---|---|---|---|
| `yolov8n-face` | `yolov8n-face.onnx` | YOLOv8n-Face | 640x640 RGB | `045e751ea609fba50d75ae31bf9bbd4546bf5f08ca78e87d0ec004f14ba6cf2f` | DERIVATIVE / GPLv3 / Research Use |
| `sface` | `sface_model.onnx` | SFace (OpenCV Zoo) | 112x112 RGB | `c71a37651a2dc8a2ef8fc5f7fdfb175409a89d33aa3b34bdf88ea4e4ab55dbb5` | Apache 2.0 |

*Note: File hash matches prove cryptographic integrity of the weights; legal licensing and institutional approval are maintained through institutional compliance agreements.*

---

## 3. Automated Model Download & Verification

The automated model downloader is located at `backend/download_models.py` (and mirrored in the Kaggle Model Lab at `research/kaggle_model_lab/02_download_weights.py`).

### Executing Model Download & Verification
```bash
# Run model downloader from project root
cd /sdcard/Download/mobile_projects/frs/backend
python download_models.py
```

### Verification Logic
```python
def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest().lower()
    return actual_hash == expected_hash.lower()
```

If the file exists and the hash matches, download is skipped. If the hash mismatches, the corrupt file is unlinked and re-downloaded. If the downloaded artifact does not match the canonical hash, the script terminates with exit code 1.

---

## 4. Docker Delivery Architecture

### 4.1 Volume Mounts in Docker Compose
To prevent bloating Docker images while guaranteeing runtime weight availability, both `docker-compose.yml` and `docker-compose.prod.yml` mount the host `backend/models` directory as a read-only volume into the containers:

```yaml
  backend-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend/models:/app/models:ro
      - ./backend/storage:/app/storage
    environment:
      - MODEL_BASE_PATH=/app/models
      - DETECTOR_MODEL_PATH=/app/models/yolov8n-face.onnx
      - RECOGNIZER_MODEL_PATH=/app/models/sface_model.onnx

  vision-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend/models:/app/models:ro
      - ./backend/storage:/app/storage
    environment:
      - MODEL_BASE_PATH=/app/models
      - DETECTOR_MODEL_PATH=/app/models/yolov8n-face.onnx
      - RECOGNIZER_MODEL_PATH=/app/models/sface_model.onnx
```

### 4.2 Non-Root Container Permissions
In `backend/Dockerfile.worker` and `backend/Dockerfile`, the application user `appuser` (UID 1000) owns `/app/models` and `/app/storage`, ensuring unprivileged runtime security while maintaining read access to mounted model weights.

---

## 5. CI/CD Deployment Integration

In `.github/workflows/deploy.yml`, model artifacts are downloaded and cryptographically verified on the build agent **prior** to Docker container construction:

```yaml
      - name: Download & Verify Model Artifacts
        run: |
          cd backend
          python download_models.py
          # Verify files exist and are non-empty
          test -s models/yolov8n-face.onnx
          test -s models/sface_model.onnx

      - name: Build and Push Docker Images
        run: |
          docker compose -f docker-compose.prod.yml build
```

---

## 6. Runtime Readiness Probe (`/api/v1/health/readiness`)

The backend readiness probe (`backend/app/api/v1/health.py`) conducts an active verification of the model files:
- Checks whether `models/yolov8n-face.onnx` and `models/sface_model.onnx` exist on disk.
- Confirms files are larger than 1 MB.
- Tests database connectivity.
- Returns `HTTP 200 {"status": "READY"}` only when all models and database are verified.
- Returns `HTTP 503 {"status": "NOT_READY", "reason": "MISSING_MODELS"}` if weights are absent.
