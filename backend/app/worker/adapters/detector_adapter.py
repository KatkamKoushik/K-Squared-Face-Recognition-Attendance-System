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
        Enforces resolution-adaptive scaling and tiled inference for high-density 4K classroom sweeps.
        Enforces fail-closed behavior: returns zero detections on blank images,
        and raises a typed RuntimeError in strict mode if the model is unavailable.
        """
        orig_w, orig_h = image.size
        if orig_w <= 0 or orig_h <= 0:
            return []

        if self._detector is None:
            raise RuntimeError(
                f"YuNet face detector ONNX model is not available or failed to initialize from {self.model_path}. "
                "Ensure model weights are present and valid."
            )

        try:
            # 1. Base Detection Pass: Auto-scale images exceeding YuNet's anchor capacity (>2560px)
            max_dim = max(orig_w, orig_h)
            scale = 2560.0 / max_dim if max_dim > 2560 else 1.0

            if scale < 1.0:
                base_w = int(orig_w * scale)
                base_h = int(orig_h * scale)
                base_image = image.resize((base_w, base_h), Image.Resampling.LANCZOS)
            else:
                base_w, base_h = orig_w, orig_h
                base_image = image

            cv_img = cv2.cvtColor(np.array(base_image), cv2.COLOR_RGB2BGR)
            self._detector.setInputSize((base_w, base_h))
            _, faces = self._detector.detect(cv_img)

            all_results: List[DetectionResult] = []
            if faces is not None and len(faces) > 0:
                for face in faces:
                    fx, fy, fw, fh = float(face[0]), float(face[1]), float(face[2]), float(face[3])
                    score = float(face[14])

                    norm_box = (
                        max(0.0, min(1.0, fx / base_w)),
                        max(0.0, min(1.0, fy / base_h)),
                        max(0.0, min(1.0, (fx + fw) / base_w)),
                        max(0.0, min(1.0, (fy + fh) / base_h)),
                    )

                    landmarks = [
                        (float(face[4]) / base_w, float(face[5]) / base_h),
                        (float(face[6]) / base_w, float(face[7]) / base_h),
                        (float(face[8]) / base_w, float(face[9]) / base_h),
                        (float(face[10]) / base_w, float(face[11]) / base_h),
                        (float(face[12]) / base_w, float(face[13]) / base_h),
                    ]

                    # Map raw_face pixel coordinates back to original unscaled image
                    scaled_raw = [float(face[i]) / scale for i in range(14)] + [score]

                    all_results.append(
                        DetectionResult(
                            box=norm_box,
                            score=round(score, 4),
                            landmarks=landmarks,
                            raw_face=scaled_raw,
                            detector_model_hash=self.MODEL_HASH,
                        )
                    )

            # 2. Tiled Grid Inference for High-Density Classroom Sweeps (>=2000 x 1400)
            if orig_w >= 2000 and orig_h >= 1400:
                tile_w = int(orig_w * 0.58)
                tile_h = int(orig_h * 0.58)
                offsets = [
                    (0, 0),
                    (orig_w - tile_w, 0),
                    (0, orig_h - tile_h),
                    (orig_w - tile_w, orig_h - tile_h),
                ]
                for ox, oy in offsets:
                    tile_pil = image.crop((ox, oy, ox + tile_w, oy + tile_h))
                    tile_cv = cv2.cvtColor(np.array(tile_pil), cv2.COLOR_RGB2BGR)
                    self._detector.setInputSize((tile_w, tile_h))
                    _, tile_faces = self._detector.detect(tile_cv)
                    if tile_faces is not None and len(tile_faces) > 0:
                        for tf in tile_faces:
                            t_fx, t_fy, t_fw, t_fh = float(tf[0]), float(tf[1]), float(tf[2]), float(tf[3])
                            t_score = float(tf[14])

                            global_box = (
                                max(0.0, min(1.0, (ox + t_fx) / orig_w)),
                                max(0.0, min(1.0, (oy + t_fy) / orig_h)),
                                max(0.0, min(1.0, (ox + t_fx + t_fw) / orig_w)),
                                max(0.0, min(1.0, (oy + t_fy + t_fh) / orig_h)),
                            )

                            global_landmarks = [
                                ((ox + float(tf[4])) / orig_w, (oy + float(tf[5])) / orig_h),
                                ((ox + float(tf[6])) / orig_w, (oy + float(tf[7])) / orig_h),
                                ((ox + float(tf[8])) / orig_w, (oy + float(tf[9])) / orig_h),
                                ((ox + float(tf[10])) / orig_w, (oy + float(tf[11])) / orig_h),
                                ((ox + float(tf[12])) / orig_w, (oy + float(tf[13])) / orig_h),
                            ]

                            # Raw coordinates mapped to global original image
                            global_raw = [
                                ox + t_fx, oy + t_fy, t_fw, t_fh,
                                ox + float(tf[4]), oy + float(tf[5]),
                                ox + float(tf[6]), oy + float(tf[7]),
                                ox + float(tf[8]), oy + float(tf[9]),
                                ox + float(tf[10]), oy + float(tf[11]),
                                ox + float(tf[12]), oy + float(tf[13]),
                                t_score,
                            ]

                            all_results.append(
                                DetectionResult(
                                    box=global_box,
                                    score=round(t_score, 4),
                                    landmarks=global_landmarks,
                                    raw_face=global_raw,
                                    detector_model_hash=self.MODEL_HASH,
                                )
                            )

            # 3. Non-Maximum Suppression (NMS) on Merged Multi-Scale Detections
            if len(all_results) > 1:
                def _calc_iou(b1, b2):
                    ix1 = max(b1[0], b2[0])
                    iy1 = max(b1[1], b2[1])
                    ix2 = min(b1[2], b2[2])
                    iy2 = min(b1[3], b2[3])
                    iw = max(0.0, ix2 - ix1)
                    ih = max(0.0, iy2 - iy1)
                    inter = iw * ih
                    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
                    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
                    union = a1 + a2 - inter
                    return inter / union if union > 0 else 0.0

                all_results.sort(key=lambda d: d.score, reverse=True)
                filtered_results: List[DetectionResult] = []
                for det in all_results:
                    suppressed = False
                    for kept in filtered_results:
                        if _calc_iou(det.box, kept.box) > 0.45:
                            suppressed = True
                            break
                    if not suppressed:
                        filtered_results.append(det)
                return filtered_results

            return all_results
        except Exception as e:
            raise RuntimeError(f"YuNet ONNX inference failed: {e}") from e
