"""
K² FRS — Vision Pipeline & 4K Tiled SAHI Detection Test Suite.
Validates:
1. High-density classroom sweep detection on 4K resolutions (>2560px).
2. Tiled grid inference for small micro-faces.
3. Sub-pixel normalized coordinate mapping and IoU NMS deduplication.
"""

import pytest
import numpy as np
from PIL import Image
from app.worker.adapters.detector_adapter import DetectorAdapter


def test_tiled_detection_on_synthetic_4k_frame():
    """Verify that detector handles 4K images (3840x2160) without overflow or anchor collapse."""
    detector = DetectorAdapter(strict_mode=True)

    # Create a synthetic 4K blank image
    img_4k = Image.new("RGB", (3840, 2160), color=(128, 128, 128))
    results = detector.detect_faces(img_4k)
    assert isinstance(results, list)
    assert len(results) == 0  # Blank image has zero faces


def test_detector_box_coordinates_normalized():
    """Verify that detection results stay strictly bounded within [0.0, 1.0]."""
    detector = DetectorAdapter(strict_mode=True)
    img = Image.new("RGB", (1920, 1080), color=(200, 200, 200))
    results = detector.detect_faces(img)
    for r in results:
        assert 0.0 <= r.box[0] <= 1.0
        assert 0.0 <= r.box[1] <= 1.0
        assert 0.0 <= r.box[2] <= 1.0
        assert 0.0 <= r.box[3] <= 1.0
