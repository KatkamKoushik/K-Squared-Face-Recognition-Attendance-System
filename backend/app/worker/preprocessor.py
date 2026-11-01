"""
FRS V7.1 K² — Preprocessing, Crop Extraction & Golden Parity Contract.
Centralizes image transforms: resize, orientation normalization, and face crop extraction.
"""

from typing import Tuple
from PIL import Image
import numpy as np


class Preprocessor:

    @staticmethod
    def extract_face_crop(
        image: Image.Image,
        normalized_box: Tuple[float, float, float, float],
        target_size: Tuple[int, int] = (112, 112),
    ) -> Image.Image:
        """
        Extracts face crop from PIL image using normalized coordinates [0.0 - 1.0]
        and resizes to the exact input dimension expected by the recognizer.
        """
        img_w, img_h = image.size
        x1 = max(0, int(normalized_box[0] * img_w))
        y1 = max(0, int(normalized_box[1] * img_h))
        x2 = min(img_w, int(normalized_box[2] * img_w))
        y2 = min(img_h, int(normalized_box[3] * img_h))

        if x2 <= x1 or y2 <= y1:
            # Fallback for degenerate box
            return Image.new("RGB", target_size, (128, 128, 128))

        crop = image.crop((x1, y1, x2, y2))
        return crop.resize(target_size, Image.Resampling.BILINEAR)

    @staticmethod
    def to_normalized_tensor(crop: Image.Image) -> np.ndarray:
        """Normalizes image pixels to standard [-1.0, 1.0] or [0.0, 1.0] float tensor."""
        arr = np.asarray(crop, dtype=np.float32)
        # Normalize to [-1.0, 1.0]
        norm = (arr - 127.5) / 128.0
        # Transpose to channel-first (C, H, W)
        return np.transpose(norm, (2, 0, 1))
