# FRS V7.1 K² — Kaggle Model Lab

**Target Environment**: Kaggle Notebooks (`Ubuntu 22.04 LTS`, Python 3.10+, Dual Tesla T4 GPUs — `GPU T4 x 2`)  
**Institutional Context**: Kakatiya University College of Engineering & Technology (KUCE&T), Warangal  
**Primary Focus**: Pretrained evaluation, landmark alignment, exact cosine retrieval, open-set rejection, and dual-GPU/CPU latency-throughput benchmarking.

---

## 1. Quickstart Guide (Kaggle Notebooks)

1. **Importing into Kaggle**:
   - In Kaggle, create a **New Notebook** (`File` > `Import Notebook`).
   - Select or upload `research/kaggle_model_lab/FRS_Kaggle_Model_Lab.ipynb`.
   - In the Notebook settings sidebar on the right:
     - **Accelerator**: Choose `GPU T4 x 2`.
     - **Language**: `Python`.
     - **Internet**: `On` (required for Stage 01 model weight verification and package installation).

2. **Sequential Cell Execution**:
   - Run the cells in order from top to bottom.
   - **Cell 0**: Installs pinned dependencies from `requirements-kaggle.txt`.
   - **Cell 1 (Stage 00)**: Audits the hardware environment, reporting CPU cores, RAM, and both Tesla T4 GPU instances (16GB each).
   - **Cell 2 (Stage 01)**: Downloads `face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx` directly from OpenCV Zoo and verifies cryptographic SHA-256 hashes against `config/model_manifest.json`.
   - **Cell 3 (Stage 02)**: Executes YuNet face detection and 5-point landmark localization. Validates fail-closed contract (blank images return 0 detections).
   - **Cell 4 (Stage 03)**: Executes SFace 5-point landmark mathematical alignment (`alignCrop`) and verifies 128-D embedding extraction on unit hypersphere $S^{127}$ ($||\mathbf{v}||_2 = 1.0$).
   - **Cell 5 (Stage 04)**: Evaluates exact roster 1:N linear search, testing known student matching, open-set unknown probe rejection ($s_1 < 0.45$), and lookalike conflict detection ($\Delta = s_1 - s_2 < 0.10$).
   - **Cell 6 (Stage 05)**: Sweeps batch sizes `[1, 4, 8, 16, 32]` measuring p50/p95 latency and throughput (FPS). Generates performance curves.
   - **Cell 7 (Stage 06)**: Exports immutable run summary to `output/kaggle_run_summary.json`.

---

## 2. Directory Structure

```
research/kaggle_model_lab/
├── README.md                           # This documentation
├── requirements-kaggle.txt             # Pinned pip dependencies
├── FRS_Kaggle_Model_Lab.ipynb          # Valid sequential Jupyter Notebook
├── config/
│   ├── model_manifest.json             # Exact SHA-256 hashes, licenses & model metadata
│   └── experiment_config.yaml          # Calibration thresholds & benchmark parameters
└── scripts/
    ├── 00_environment_audit.py         # Hardware & execution provider inspector
    ├── 01_download_verify_models.py    # Downloads and SHA-256 verifies ONNX weights
    ├── 02_face_detection_test.py       # YuNet detection and 5-landmark verification
    ├── 03_face_recognition_test.py     # SFace alignCrop and 128-D manifold verification
    ├── 04_retrieval_and_calibration.py # Exact cosine search and unknown rejection
    ├── 05_batch_benchmark.py           # Multi-batch latency and throughput benchmark
    └── 06_export_model_manifest.py     # Aggregates run telemetry into audit JSON
```

---

## 3. Approved Model Artifacts & Provenance

| Model | Task | File Name | SHA-256 Hash | License | Upstream Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YuNet** | Face Detection | `face_detection_yunet_2023mar.onnx` | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | MIT | [OpenCV Zoo YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) |
| **SFace** | Face Recognition | `face_recognition_sface_2021dec.onnx` | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache-2.0 | [OpenCV Zoo SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) |

---

## 4. Biometric Data Governance & Privacy Invariants

1. **No Public Kaggle Datasets**: Real student portraits, KUCET rosters, and biometric embeddings must NEVER be uploaded to public Kaggle datasets or public repositories.
2. **Evaluation Cohorts**: Evaluations must use consented volunteer photographs or synthetic test images only.
3. **Artifact Hygiene**: Raw student photographs and embedding vectors are excluded from default Kaggle output artifacts.
4. **Pretrained Baseline First**: Do not attempt model fine-tuning until pretrained baselines are benchmarked and verified.
