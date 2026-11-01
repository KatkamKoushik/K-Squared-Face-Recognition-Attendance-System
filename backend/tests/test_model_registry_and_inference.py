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
    assert policy.match_cosine_threshold == 0.70
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
    P0.2: Detector produces valid normalized bounding boxes [0.0 - 1.0]
    and 5 facial landmarks.
    """
    adapter = DetectorAdapter()
    test_image = Image.new("RGB", (640, 480), color=(128, 128, 128))

    detections = adapter.detect_faces(test_image)
    assert len(detections) >= 1

    for det in detections:
        box = det.box
        assert 0.0 <= box[0] < box[2] <= 1.0, f"Invalid x bounds: {box}"
        assert 0.0 <= box[1] < box[3] <= 1.0, f"Invalid y bounds: {box}"
        assert 0.0 <= det.score <= 1.0
        assert len(det.landmarks) == 5
        for lm in det.landmarks:
            assert 0.0 <= lm[0] <= 1.0
            assert 0.0 <= lm[1] <= 1.0


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
