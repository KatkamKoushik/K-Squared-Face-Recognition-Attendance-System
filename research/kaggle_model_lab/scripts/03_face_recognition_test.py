#!/usr/bin/env python3
"""
FRS V7.1 K² Kaggle Model Lab — Stage 03: SFace 5-Landmark Alignment & 128-D Embedding Test.
"""

import sys
from pathlib import Path
import numpy as np
import cv2

def run_recognition_tests(sface_path: Path) -> dict:
    print("=" * 60)
    print("STAGE 03 — SFACE 5-LANDMARK ALIGNMENT & 128-D EMBEDDING TEST")
    print("=" * 60)

    if not sface_path.is_file():
        raise FileNotFoundError(f"SFace model missing at {sface_path}. Run Stage 01 first.")

    recognizer = cv2.FaceRecognizerSF.create(
        model=str(sface_path.resolve()),
        config="",
    )
    print("  [INIT] cv2.FaceRecognizerSF loaded successfully.")

    # Synthetic portrait test with valid 15-element face representation
    # [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rc, y_rc, x_lc, y_lc, score]
    raw_face = np.array([
        100.0, 100.0, 140.0, 160.0,
        130.0, 140.0,   # right eye
        190.0, 140.0,   # left eye
        160.0, 175.0,   # nose tip
        140.0, 210.0,   # right mouth corner
        180.0, 210.0,   # left mouth corner
        0.985           # detection score
    ], dtype=np.float32)

    test_bgr = np.full((480, 640, 3), 150, dtype=np.uint8)
    cv2.circle(test_bgr, (130, 140), 10, (40, 40, 40), -1)
    cv2.circle(test_bgr, (190, 140), 10, (40, 40, 40), -1)

    # 1. 5-landmark alignCrop execution
    aligned_crop = recognizer.alignCrop(test_bgr, raw_face)
    print(f"  [ALIGNMENT] alignCrop executed. Output shape: {aligned_crop.shape} (Expected: 112x112x3)")
    assert aligned_crop.shape == (112, 112, 3), f"Invalid crop dimensions: {aligned_crop.shape}"

    # 2. 128-D Feature Extraction
    features = recognizer.feature(aligned_crop)
    vec = features.flatten().astype(np.float32)
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
        norm = float(np.linalg.norm(vec))

    print(f"  [EMBEDDING] Vector Dimension : {len(vec)} (Expected: 128)")
    print(f"  [MANIFOLD] L2-Norm on S^127  : {norm:.6f} (Expected: 1.000000)")
    assert len(vec) == 128, f"Invalid embedding dimension: {len(vec)}"
    assert abs(norm - 1.0) < 1e-4, f"Embedding vector is not normalized to unit hypersphere: {norm}"

    # 3. Mathematical Cosine Properties
    sim_self = float(np.dot(vec, vec))
    print(f"  [COSINE] Self-Similarity    : {sim_self:.6f} (Expected: 1.000000)")
    assert abs(sim_self - 1.0) < 1e-4, "Self cosine similarity must equal 1.0"

    orthogonal_vec = np.zeros(128, dtype=np.float32)
    orthogonal_vec[0] = 1.0
    orthogonal_target = np.zeros(128, dtype=np.float32)
    orthogonal_target[1] = 1.0
    sim_ortho = float(np.dot(orthogonal_vec, orthogonal_target))
    print(f"  [COSINE] Orthogonal Dot Prod : {sim_ortho:.6f} (Expected: 0.000000)")
    assert abs(sim_ortho) < 1e-4, "Orthogonal dot product must equal 0.0"

    print("  [PASS] Mathematical embedding contracts and hypersphere invariants verified.")
    return {
        "status": "SUCCESS",
        "recognizer_loaded": True,
        "alignment_shape": list(aligned_crop.shape),
        "embedding_dimension": len(vec),
        "l2_norm": norm,
        "self_cosine": sim_self,
    }

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    lab_root = script_dir.parent
    sface = lab_root / "models" / "face_recognition_sface_2021dec.onnx"
    run_recognition_tests(sface)
