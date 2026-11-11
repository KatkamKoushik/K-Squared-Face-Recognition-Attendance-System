# FRS V7.1 K² — Kaggle Environment Guide

**Institution**: Kakatiya University College of Engineering & Technology (KUCET), Warangal  
**Target Environment**: Kaggle Notebooks (`Ubuntu 22.04 LTS`, Python 3.10+, Dual Tesla T4 GPUs — `GPU T4 x 2` or P100)  
**Hugging Face Hub Integration**: `Koushik-Katkam/kucet-frs-face-recognition`

---

## 1. Notebooks in this Folder

| Notebook | Focus | Primary Capabilities |
| :--- | :--- | :--- |
| [`FRS_Kaggle_Demo_Session.ipynb`](file:///d:/k^2/kaggle/FRS_Kaggle_Demo_Session.ipynb) | **Live Classroom Inference & Bridge** | - Downloads & SHA-256 verifies YuNet & SFace<br>- Ingests classroom photo sweep<br>- Localizes faces with 5 landmarks & extracts 128-D embeddings<br>- 1:N cosine retrieval & open-set unknown rejection<br>- Visualizes sweep annotations & similarity heatmaps<br>- Generates Section 4.2 attendance proposals & HMAC-SHA256 commit receipts<br>- Latency & throughput benchmarking<br>- Live bi-directional FastAPI bridge over Ngrok |
| [`FRS_Kaggle_Model_Fine_Tuning.ipynb`](file:///d:/k^2/kaggle/FRS_Kaggle_Model_Fine_Tuning.ipynb) | **Model Fine-Tuning & Hugging Face Hub** | - Authenticates with Hugging Face token (`Koushik-Katkam`)<br>- Multi-GPU training with PyTorch AMP on Dual Tesla T4<br>- Metric learning with Additive Angular Margin Loss (ArcFace)<br>- Hyperspherical norm verification on $S^{127}$<br>- Separation margin ($\Delta s$) and decision threshold calibration<br>- Production ONNX model export with numerical parity check<br>- Automatically publishes ONNX, weights, and Model Card to Hugging Face Hub |

---

## 2. How to Import Directly into Kaggle

1. Go to [kaggle.com](https://www.kaggle.com) and click **Create** > **New Notebook** (or open an existing notebook).
2. In the notebook menu, click **File** > **Import Notebook**.
3. Select either:
   - `FRS_Kaggle_Demo_Session.ipynb` (for live inference demo & backend bridge)
   - `FRS_Kaggle_Model_Fine_Tuning.ipynb` (for fine-tuning models & uploading to Hugging Face)
4. In the **Notebook options / Settings panel** on the right side:
   - **Accelerator**: Select **GPU T4 x 2** (Dual Tesla T4 GPUs) or **GPU P100**.
   - **Language**: `Python`.
   - **Internet**: Toggle **On** (required for downloading OpenCV Zoo weights and uploading to Hugging Face Hub).
5. Click **Run All** (`>>`) or execute cell by cell from top to bottom.

---

## 3. Hugging Face Access Token Configuration

The notebooks are pre-configured to use the provided fine-grained token with write permissions:
- **HF User**: `Koushik-Katkam`
- **Permissions**: `repo.write`, `repo.content.read`, `repo.contribute.write`
- **Target Repository**: `https://huggingface.co/Koushik-Katkam/kucet-frs-face-recognition`

Alternatively, you can securely store the token in Kaggle Secrets:
1. In Kaggle, click **Add-ons** > **Secrets**.
2. Add a secret with label `HF_TOKEN` and your token value.
3. The notebooks will automatically pick up `os.environ.get("HF_TOKEN")`.

---

## 4. Biometric Data Governance & Privacy Invariants

- **DPDP Act 2023 Conformance**: Provision of facial biometric data is governed by institutional policy.
- Raw classroom images are processed in volatile memory and purged; only mathematical representations (128-D vectors on $S^{127}$) are preserved in the authoritative ledger.
- Never upload unconsented student personal identification data to public Kaggle datasets.
