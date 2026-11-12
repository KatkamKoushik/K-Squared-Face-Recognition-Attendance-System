# FRS V7.1 K² — Kaggle Environment Guide

**Institution**: Kakatiya University College of Engineering & Technology (KUCET), Warangal  
**Target Environment**: Kaggle Notebooks (`Ubuntu 22.04 LTS`, Python 3.10+, Dual Tesla T4 GPUs — `GPU T4 x 2` or P100)  
**Hugging Face Hub Repository**: `https://huggingface.co/Koushik-Katkam/kucet-frs-face-recognition`

---

## 1. Hugging Face Access Token Requirements

Before running or fine-tuning models in Kaggle:

| Requirement | Value | Notes |
| :--- | :--- | :--- |
| **Token Quantity** | **Exactly 1 (one)** User Access Token | One token covers all repositories under user account `Koushik-Katkam`. |
| **Provider** | **Hugging Face (`https://huggingface.co`)** | Access tokens are generated under user settings. |
| **Token Role / Permissions** | **Write** (or Fine-Grained `repo.write`, `repo.content.read`, `repo.access.read`) | Grants permission to push ONNX checkpoints, PyTorch weights, manifests, and Model Cards to `Koushik-Katkam/kucet-frs-face-recognition`. |
| **Active Token Key** | Already configured in `.env` as `HF_TOKEN` | Stored securely in Kaggle Secrets under label `HF_TOKEN`. |

---

## 2. Blueprint Model Candidates (Master Handbook Section 5 & 10)

The V7.1 Master Blueprint specifies 4 candidate models plus the YuNet face detector:

| Model Architecture | Task | Resolution | Loss / Head | Output Latent Space | Target ONNX Artifact | Calibrated Threshold ($\tau$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YuNet Detector** | Face Detection & 5 Landmarks | Dynamic / 320x320 | NMS & Bounding Box Reg | 15-element face vector | `face_detection_yunet_2023mar.onnx` | Score: 0.60, NMS: 0.30 |
| **SFace / MobileFaceNet** | Primary Recognizer | 112x112 RGB | ArcFace ($s=30, m=0.35$) | 128-D on $S^{127}$ ($||v||_2=1.0$) | `kucet_frs_sface_finetuned.onnx` | $\tau = 0.363$ |
| **EdgeFace-Base** | High-Accuracy Edge Recognizer | 112x112 RGB | ArcFace ($s=30, m=0.35$) | 512-D on $S^{511}$ ($||v||_2=1.0$) | `kucet_frs_edgeface_finetuned.onnx` | $\tau = 0.420$ |
| **GhostFaceNets** | Low-FLOPs Ghost Bottleneck | 112x112 RGB | ArcFace ($s=30, m=0.35$) | 128-D on $S^{127}$ ($||v||_2=1.0$) | `kucet_frs_ghostfacenet_finetuned.onnx` | $\tau = 0.380$ |
| **MiniFASNetV2** | Presentation Attack Detection (PAD) | 80x80 BGR | Focal Cross-Entropy | 2-class (Live vs. Spoof) | `kucet_frs_minifasnet_finetuned.onnx` | $\tau_{\text{spoof}} = 0.500$ |

---

## 3. Notebooks and Scripts in this Folder

| File | Purpose | Key Features |
| :--- | :--- | :--- |
| [`FRS_Kaggle_Model_Fine_Tuning.ipynb`](file:///d:/k^2/kaggle/FRS_Kaggle_Model_Fine_Tuning.ipynb) | **Model Fine-Tuning & Hugging Face Hub** | - Supports `TARGET_MODEL = "ALL"` or individual models<br>- Dual Tesla T4 multi-GPU training with PyTorch AMP<br>- Metric learning with Additive Angular Margin Loss (ArcFace)<br>- Hypersphere unit-norm invariant check on $S^{127}$ / $S^{511}$<br>- Separation margin ($\Delta s$) and decision threshold calibration<br>- Production ONNX export with numerical parity check ($< 10^{-4}$)<br>- Pushes models, weights, manifests, and Model Cards to Hugging Face Hub |
| [`FRS_Kaggle_Demo_Session.ipynb`](file:///d:/k^2/kaggle/FRS_Kaggle_Demo_Session.ipynb) | **Live Classroom Inference & Bridge** | - Downloads & verifies YuNet and all blueprint models<br>- Ingests classroom photo sweep<br>- Resolution-adaptive cosine thresholding ($\tau_{\text{effective}}$ based on face pixel width)<br>- Department cohort filter scoping (`ALL`, `CSD`, `CSE`)<br>- 1:N cosine retrieval & open-set unknown rejection<br>- Visualizes sweep annotations & similarity heatmaps<br>- Cryptographic HMAC-SHA256 commit receipts<br>- Live bi-directional FastAPI bridge over Ngrok |
| [`train_models.py`](file:///d:/k^2/kaggle/train_models.py) | **Standalone Training CLI Script** | - Run directly via terminal: `python train_models.py --model ALL --steps 5000`<br>- Exports `.onnx` and `.pt` weights into `./output/` |

---

## 4. How to Import and Run Directly in Kaggle

1. Go to [kaggle.com](https://www.kaggle.com) and click **Create** > **New Notebook**.
2. In the notebook top menu, click **File** > **Import Notebook**.
3. Select either:
   - `FRS_Kaggle_Model_Fine_Tuning.ipynb` (to fine-tune models & upload to Hugging Face)
   - `FRS_Kaggle_Demo_Session.ipynb` (to run classroom inference & Ngrok bridge)
4. In the **Notebook options / Settings panel** on the right side:
   - **Accelerator**: Select **GPU T4 x 2** (Dual Tesla T4 GPUs) or **GPU P100**.
   - **Language**: `Python`.
   - **Internet**: Toggle **On** (required to download dependencies and push to Hugging Face Hub).
5. Add Hugging Face Secret:
   - In Kaggle, click **Add-ons** > **Secrets**.
   - Label: `HF_TOKEN`
   - Value: paste your personal Hugging Face token (from your institutional `.env` file).
6. Click **Run All** (`>>`) or execute cell by cell from top to bottom.

---

## 5. Biometric Data Governance & Privacy Invariants

- **DPDP Act 2023 Conformance**: Provision of facial biometric data is governed strictly by institutional policy.
- Raw classroom images are processed in volatile memory and purged; only mathematical representations (vectors on $S^{127}$ / $S^{511}$) are preserved in the authoritative ledger.
- Never upload unconsented student personal identification data to public Kaggle datasets.
