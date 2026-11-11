"""
FRS V7.1 K2 -- Model Registry, Provenance & Real ONNX Inference Tests.
Verifies rights-cleared YuNet detector and SFace recognizer, exact SHA-256
lineage, unit hypersphere normalization, and calibrated thresholds.
"""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from sqlalchemy.orm import Session
from app.services.model_registry_service import ModelRegistryService
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter


def test_model_registry_seeding_and_integrity(db_session: Session):
    """
    P0.2 / P1: Model registry records exact rights-cleared artifacts,
    reproducible hashes, and calibrated decision policy.
    """
    policy = ModelRegistryService.seed_default_registry(db_session)
    assert policy.id == "policy_kucet_v7_1_default"
    assert policy.match_cosine_threshold == 0.363
    assert policy.margin_threshold == 0.10
    assert policy.is_active is True

    # Retrieve YuNet detector artifact
    yunet = ModelRegistryService.get_model_artifact_by_hash(
        db_session, policy.detector_model_hash
    )
    assert yunet.name == "face_detection_yunet_2023mar"
    assert yunet.code_license == "MIT"
    assert yunet.approval_status == "APPROVED"
    assert yunet.format == "ONNX"

    # Retrieve SFace recognizer artifact
    sface = ModelRegistryService.get_model_artifact_by_hash(
        db_session, policy.recognizer_model_hash
    )
    assert sface.name == "face_recognition_sface_2021dec"
    assert sface.code_license == "Apache-2.0"
    assert sface.approval_status == "APPROVED"
    assert sface.embedding_dimension == 128


def test_detector_adapter_inference_and_normalization():
    """
    P0.2 & Strict Mode: Detector operates in strict fail-closed mode.
    Blank image must return zero detections.
    """
    adapter = DetectorAdapter(strict_mode=True)
    blank_image = Image.new("RGB", (640, 480), color=(128, 128, 128))

    assert adapter._detector is not None, "Real YuNet detector must be initialized"
    detections = adapter.detect_faces(blank_image)
    assert len(detections) == 0, "Blank image must return exactly 0 detections in strict mode"


def test_recognizer_5_landmark_alignment_and_embedding():
    """
    P0-E & Strict Mode: Mathematical 5-landmark alignment and SFace 128-D feature extraction.
    """
    adapter = RecognizerAdapter(strict_mode=True)
    assert adapter._recognizer is not None, "Real SFace recognizer must be initialized"
    raw_face = [100.0, 100.0, 120.0, 120.0, 130.0, 140.0, 190.0, 140.0, 160.0, 170.0, 140.0, 200.0, 180.0, 200.0, 0.95]
    bgr_img = np.zeros((480, 640, 3), dtype=np.uint8)

    emb = adapter.align_and_compute_embedding(bgr_img, raw_face)
    assert emb.dimension == 128
    assert emb.namespace == "sface_128d_v1"
    vec = np.array(emb.vector, dtype=np.float32)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-4


def test_recognizer_embedding_hypersphere_and_cosine_matching():
    """
    P0.2 / P1: Recognizer computes 128-D L2-normalized vector on unit hypersphere
    and matches identical crops with high cosine similarity.
    """
    adapter = RecognizerAdapter()
    face_crop = Image.new("RGB", (112, 112), color=(140, 100, 80))

    emb = adapter.compute_embedding(face_crop)
    assert emb.dimension == 128
    vec = np.array(emb.vector, dtype=np.float32)

    # Unit hypersphere norm assertion: ||v||_2 == 1.0 within numerical precision
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4

    # Identical vector cosine similarity must be 1.0
    sim_self = adapter.cosine_similarity(emb.vector, emb.vector)
    assert abs(sim_self - 1.0) < 1e-4

    # Orthogonal vectors cosine similarity must be 0.0
    ortho_1 = [1.0] + [0.0] * 127
    ortho_2 = [0.0, 1.0] + [0.0] * 126
    sim_ortho = adapter.cosine_similarity(ortho_1, ortho_2)
    assert abs(sim_ortho - 0.0) < 1e-4


def test_recognizer_quality_assessment():
    """
    Quality gate: Degenerate or too-small face crops are rejected as un-usable.
    """
    adapter = RecognizerAdapter()

    small_crop = Image.new("RGB", (16, 16), color=(100, 100, 100))
    res_small = adapter.assess_quality(small_crop)
    assert res_small.is_usable is False
    assert res_small.reason_code == "FACE_TOO_SMALL"

    # A flat uniform rectangle has zero edges and is correctly rejected as blurry/unusable
    flat_crop = Image.new("RGB", (112, 112), color=(120, 120, 120))
    res_flat = adapter.assess_quality(flat_crop)
    assert res_flat.is_usable is False
    assert res_flat.reason_code == "BLURRY_FACE"

    # An image with real edges/contrast has high Laplacian sharpness and passes
    arr = np.zeros((112, 112, 3), dtype=np.uint8)
    arr[::2, ::2] = 255
    textured_crop = Image.fromarray(arr)
    res_std = adapter.assess_quality(textured_crop)
    assert res_std.is_usable is True


def test_finetuned_model_loading_and_inference(db_session: Session):
    """
    KUCET ArcFace Fine-Tuned Model:
    Validates fine-tuned SFace weights loaded from backend/models/kucet_frs_sface_finetuned.onnx,
    exact SHA-256 hash match, unit hypersphere normalization, and registry persistence.
    """
    finetuned_path = Path("backend/models/kucet_frs_sface_finetuned.onnx")
    if not finetuned_path.is_file():
        pytest.skip("Fine-tuned ONNX model not present in local workspace")

    # 1. Adapter initialization with fine-tuned model path
    adapter = RecognizerAdapter(model_path=finetuned_path, strict_mode=True)
    assert adapter._recognizer is not None
    assert adapter.model_hash == RecognizerAdapter.FINETUNED_HASH
    assert adapter.namespace == "kucet_frs_sface_finetuned_v1"

    # 2. Embedding calculation and unit hypersphere assertion
    face_crop = Image.new("RGB", (112, 112), color=(140, 100, 80))
    emb = adapter.compute_embedding(face_crop)
    assert emb.dimension == 128
    assert emb.namespace == "kucet_frs_sface_finetuned_v1"
    assert emb.recognizer_model_hash == RecognizerAdapter.FINETUNED_HASH

    vec = np.array(emb.vector, dtype=np.float32)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4

    # 3. Model registry seeding and artifact verification
    policy = ModelRegistryService.seed_default_registry(db_session)
    finetuned_artifact = ModelRegistryService.get_model_artifact_by_hash(
        db_session, RecognizerAdapter.FINETUNED_HASH
    )
    assert finetuned_artifact is not None
    assert finetuned_artifact.name == "kucet_frs_sface_finetuned"
    assert finetuned_artifact.approval_status == "APPROVED"
    assert finetuned_artifact.embedding_dimension == 128

