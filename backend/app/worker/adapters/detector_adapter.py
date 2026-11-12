"""
K² FRS -- Face Detector Adapter Interface.
Executes rights-cleared YuNet face detector with strict fail-closed inference.
"""

import hashlib
import os
from pathlib import Path
from typing import List, Optional
import numpy as np
from PIL import Image
import cv2
from app.worker.contracts import DetectionResult


class DetectorAdapter:
    """
    Standardized face detection adapter.
    Executes rights-cleared OpenCV Zoo YuNet ONNX detector with strict SHA-256
    integrity verification and strict fail-closed behavior.
    """

    MODEL_HASH = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
    DEFAULT_FILENAME = "face_detection_yunet_2023mar.onnx"

    def __init__(self, model_path: Optional[Path] = None, strict_mode: Optional[bool] = None):
        self.strict_mode = strict_mode if strict_mode is not None else (os.getenv("STRICT_INFERENCE", "1") == "1")
        self.model_path = self._resolve_model_path(model_path)
        self._detector: Optional[cv2.FaceDetectorYN] = None
        self._init_detector()

    def _compute_sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _resolve_model_path(self, explicit_path: Optional[Path]) -> Path:
        """Discovers the YuNet ONNX model path across local, repo-relative, and container locations."""
        if explicit_path:
            return Path(explicit_path)
        candidates = [
            Path("backend/models") / self.DEFAULT_FILENAME,
            Path("models") / self.DEFAULT_FILENAME,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / self.DEFAULT_FILENAME,
            Path("/app/models") / self.DEFAULT_FILENAME,
        ]
        for p in candidates:
            resolved = p.resolve()
            if resolved.is_file():
                return resolved
        return Path("backend/models") / self.DEFAULT_FILENAME

    def _init_detector(self):
        resolved = Path(self.model_path).resolve()
        if not resolved.is_file():
            if self.strict_mode:
                raise FileNotFoundError(
                    f"YuNet face detector ONNX model file not found at {resolved}. "
                    "Run scripts/download_vision_models.py to download weights."
                )
            self._detector = None
            return

        actual_hash = self._compute_sha256(resolved)
        if actual_hash != self.MODEL_HASH:
            if self.strict_mode:
                raise ValueError(
                    f"YuNet model SHA-256 hash mismatch: expected {self.MODEL_HASH}, got {actual_hash}"
                )
            self._detector = None
            return

        try:
            self._detector = cv2.FaceDetectorYN.create(
                model=str(resolved),
                config="",
                input_size=(320, 320),
                score_threshold=0.6,
                nms_threshold=0.3,
                top_k=5000,
            )
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(f"Failed to initialize cv2.FaceDetectorYN from {resolved}: {exc}") from exc
            self._detector = None

    def detect_faces(self, image: Image.Image) -> List[DetectionResult]:
        """
        Discovers faces in an image using YuNet ONNX inference.
        Enforces fail-closed behavior: returns zero detections on blank images,
        and raises a typed RuntimeError in strict mode if the model is unavailable.
        """
        w, h = image.size
        if w <= 0 or h <= 0:
            return []

        if self._detector is None:
            raise RuntimeError(
                f"YuNet face detector ONNX model is not available or failed to initialize from {self.model_path}. "
                "Ensure model weights are present and valid."
            )

        try:
            # Convert PIL RGB to OpenCV BGR
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            self._detector.setInputSize((w, h))
            _, faces = self._detector.detect(cv_img)

            if faces is not None and len(faces) > 0:
                results: List[DetectionResult] = []
                for face in faces:
                    # face format: [x, y, w_box, h_box, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rc, y_rc, x_lc, y_lc, score]
                    fx, fy, fw, fh = float(face[0]), float(face[1]), float(face[2]), float(face[3])
                    score = float(face[14])

                    # Normalize box
                    norm_box = (
                        max(0.0, min(1.0, fx / w)),
                        max(0.0, min(1.0, fy / h)),
                        max(0.0, min(1.0, (fx + fw) / w)),
                        max(0.0, min(1.0, (fy + fh) / h)),
                    )

                    # Extract 5 landmarks (right eye, left eye, nose tip, right mouth, left mouth)
                    landmarks = [
                        (float(face[4]) / w, float(face[5]) / h),
                        (float(face[6]) / w, float(face[7]) / h),
                        (float(face[8]) / w, float(face[9]) / h),
                        (float(face[10]) / w, float(face[11]) / h),
                        (float(face[12]) / w, float(face[13]) / h),
                    ]

                    results.append(
                        DetectionResult(
                            box=norm_box,
                            score=round(score, 4),
                            landmarks=landmarks,
                            raw_face=[float(x) for x in face],
                            detector_model_hash=self.MODEL_HASH,
                        )
                    )
                return results

            # Detector ran successfully but found zero faces (e.g. blank or empty image)
            return []
        except Exception as e:
            raise RuntimeError(f"YuNet ONNX inference failed: {e}") from e
