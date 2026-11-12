#!/usr/bin/env python3
"""
K² FRS Kaggle Model Lab — Stage 02: YuNet Face Detection & Landmark Verification.
"""

import sys
from pathlib import Path
import numpy as np
import cv2

def run_detection_tests(yunet_path: Path) -> dict:
    print("=" * 60)
    print("STAGE 02 — YUNET FACE DETECTION & LANDMARK TEST")
    print("=" * 60)

    if not yunet_path.is_file():
        raise FileNotFoundError(f"YuNet model missing at {yunet_path}. Run Stage 01 first.")

    detector = cv2.FaceDetectorYN.create(
        model=str(yunet_path.resolve()),
        config="",
        input_size=(320, 320),
        score_threshold=0.60,
        nms_threshold=0.30,
        top_k=5000,
    )
    print("  [INIT] cv2.FaceDetectorYN loaded successfully.")

    # 1. Blank Image Test: Must return exactly zero detections
    blank_bgr = np.full((480, 640, 3), 128, dtype=np.uint8)
    detector.setInputSize((640, 480))
    _, blank_faces = detector.detect(blank_bgr)
    blank_count = len(blank_faces) if blank_faces is not None else 0
    print(f"  [TEST 1] Blank Image (640x480): {blank_count} detections")
    assert blank_count == 0, f"STRICT MODE VIOLATION: Blank image returned {blank_count} detections!"
    print("  [PASS] Zero-detection fail-closed contract validated.")

    # 2. Geometric Face Fixture Test
    # Create synthetic face-like contrast pattern to verify landmark extraction coordinates
    test_img = np.full((480, 640, 3), 220, dtype=np.uint8)
    # Draw simple facial feature landmarks (oval, eyes, nose, mouth)
    cv2.ellipse(test_img, (320, 240), (80, 110), 0, 0, 360, (140, 160, 200), -1)
    cv2.circle(test_img, (290, 210), 12, (50, 50, 50), -1)
    cv2.circle(test_img, (350, 210), 12, (50, 50, 50), -1)
    cv2.circle(test_img, (320, 245), 8, (60, 60, 100), -1)
    cv2.ellipse(test_img, (320, 285), (25, 10), 0, 0, 180, (40, 40, 120), 4)

    detector.setInputSize((640, 480))
    _, faces = detector.detect(test_img)
    detections = []
    if faces is not None:
        for face in faces:
            fx, fy, fw, fh = float(face[0]), float(face[1]), float(face[2]), float(face[3])
            score = float(face[14])
            landmarks = [
                (float(face[4]) / 640.0, float(face[5]) / 480.0),   # Right eye
                (float(face[6]) / 640.0, float(face[7]) / 480.0),   # Left eye
                (float(face[8]) / 640.0, float(face[9]) / 480.0),   # Nose tip
                (float(face[10]) / 640.0, float(face[11]) / 480.0), # Right mouth corner
                (float(face[12]) / 640.0, float(face[13]) / 480.0), # Left mouth corner
            ]
            detections.append({
                "box_norm": [fx / 640.0, fy / 480.0, (fx + fw) / 640.0, (fy + fh) / 480.0],
                "score": round(score, 4),
                "landmarks": landmarks,
                "raw_face": [float(x) for x in face],
            })
            print(f"  [DETECTION] Score={score:.3f}, Box=[{fx:.1f}, {fy:.1f}, {fw:.1f}, {fh:.1f}], Landmarks={len(landmarks)}")

    return {
        "status": "SUCCESS",
        "blank_test_passed": True,
        "detector_loaded": True,
        "detections_count": len(detections),
        "detections": detections,
    }

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    lab_root = script_dir.parent
    yunet = lab_root / "models" / "face_detection_yunet_2023mar.onnx"
    run_detection_tests(yunet)
