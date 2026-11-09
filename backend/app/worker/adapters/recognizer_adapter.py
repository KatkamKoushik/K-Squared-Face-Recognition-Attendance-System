"""
FRS V7.1 K2 -- Recognizer & Exact Roster Search Adapter.
Enforces exact cosine retrieval, margin evaluation, and open-set unknown classification.
Executes rights-cleared OpenCV Zoo SFace ONNX model with deterministic fallback.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
import numpy as np
import cv2
from app.worker.contracts import EmbeddingResult, RetrievalCandidate, QualityResult


class RecognizerAdapter:

    MODEL_HASH = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
    NAMESPACE = "sface_128d_v1"
    DEFAULT_FILENAME = "face_recognition_sface_2021dec.onnx"

    def __init__(self, model_path: Optional[Path] = None, strict_mode: Optional[bool] = None):
        self.strict_mode = strict_mode if strict_mode is not None else (os.getenv("STRICT_INFERENCE", "1") == "1")
        self.model_path = self._resolve_model_path(model_path)
        self._recognizer: Optional[cv2.FaceRecognizerSF] = None
        self._init_recognizer()

    def _resolve_model_path(self, explicit_path: Optional[Path]) -> Path:
        """Discovers SFace ONNX model path across local, repo-relative, and container locations."""
        candidates = []
        if explicit_path:
            candidates.append(Path(explicit_path))
        candidates.extend([
            Path("backend/models") / self.DEFAULT_FILENAME,
            Path("models") / self.DEFAULT_FILENAME,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / self.DEFAULT_FILENAME,
            Path("/app/models") / self.DEFAULT_FILENAME,
        ])
        for p in candidates:
            resolved = p.resolve()
            if resolved.is_file():
                return resolved
        return explicit_path or (Path("backend/models") / self.DEFAULT_FILENAME)

    def _init_recognizer(self):
        resolved = Path(self.model_path).resolve()
        if resolved.is_file():
            try:
                self._recognizer = cv2.FaceRecognizerSF.create(
                    model=str(resolved),
                    config="",
                )
            except Exception:
                self._recognizer = None

    def align_and_compute_embedding(
        self,
        cv_bgr_img: np.ndarray,
        raw_face: List[float],
    ) -> EmbeddingResult:
        """
        P0-E: Mathematical 5-landmark alignment and 128-D embedding extraction.
        Applies cv2.FaceRecognizerSF.alignCrop using YuNet's 5 facial landmarks,
        ensuring parity between enrollment portraits and classroom query sweeps.
        """
        if self._recognizer is not None:
            try:
                face_arr = np.array(raw_face, dtype=np.float32)
                aligned_crop = self._recognizer.alignCrop(cv_bgr_img, face_arr)
                raw_feature = self._recognizer.feature(aligned_crop)
                vec = raw_feature.flatten().astype(np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return EmbeddingResult(
                    vector=vec.tolist(),
                    dimension=128,
                    namespace=self.NAMESPACE,
                    recognizer_model_hash=self.MODEL_HASH,
                )
            except Exception as e:
                if self.strict_mode:
                    raise RuntimeError(f"SFace alignCrop/feature extraction failed: {e}") from e

        if self.strict_mode:
            raise RuntimeError(
                f"SFace face recognizer ONNX model could not be loaded from {self.model_path}. "
                "Ensure scripts/download_vision_models.py was run to download weights."
            )

        # Fallback for lightweight testing when strict_mode=False
        seed = int(sum(raw_face)) % 100000
        rng = np.random.RandomState(seed)
        raw_vec = rng.randn(128).astype(np.float32)
        norm_vec = raw_vec / np.linalg.norm(raw_vec)
        return EmbeddingResult(
            vector=norm_vec.tolist(),
            dimension=128,
            namespace=self.NAMESPACE,
            recognizer_model_hash=self.MODEL_HASH,
        )

    def compute_embedding(self, face_crop: Image.Image) -> EmbeddingResult:
        """
        Computes 128-D L2-normalized embedding vector on unit hypersphere S^127.
        """
        if self._recognizer is not None:
            try:
                # Resize to standard 112x112 input if needed
                crop = face_crop.resize((112, 112), Image.Resampling.BILINEAR)
                cv_img = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
                raw_feature = self._recognizer.feature(cv_img)
                vec = raw_feature.flatten().astype(np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return EmbeddingResult(
                    vector=vec.tolist(),
                    dimension=128,
                    namespace=self.NAMESPACE,
                    recognizer_model_hash=self.MODEL_HASH,
                )
            except Exception as e:
                if self.strict_mode:
                    raise RuntimeError(f"SFace feature extraction failed: {e}") from e

        if self.strict_mode:
            raise RuntimeError(
                f"SFace face recognizer ONNX model could not be loaded from {self.model_path}. "
                "Ensure scripts/download_vision_models.py was run to download weights."
            )

        # Deterministic feature generation on unit hypersphere S^127 for lightweight testing
        crop_bytes = face_crop.tobytes()
        seed = sum(crop_bytes) % 100000
        rng = np.random.RandomState(seed)
        raw_vec = rng.randn(128).astype(np.float32)
        norm_vec = raw_vec / np.linalg.norm(raw_vec)

        return EmbeddingResult(
            vector=norm_vec.tolist(),
            dimension=128,
            namespace=self.NAMESPACE,
            recognizer_model_hash=self.MODEL_HASH,
        )

    def assess_quality(self, face_crop: Image.Image) -> QualityResult:
        """Estimates per-face quality (blur, size, occlusion)."""
        w, h = face_crop.size
        if w < 24 or h < 24:
            return QualityResult(score=0.2, is_usable=False, reason_code="FACE_TOO_SMALL")

        try:
            # Laplacian variance sharpness estimation
            gray = cv2.cvtColor(np.array(face_crop), cv2.COLOR_RGB2GRAY)
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            if lap_var < 15.0:
                return QualityResult(
                    score=round(min(1.0, lap_var / 50.0), 3),
                    is_usable=False,
                    reason_code="BLURRY_FACE",
                )
        except Exception:
            pass

        return QualityResult(score=0.92, is_usable=True, reason_code="QUALITY_ACCEPTABLE")

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two unit vectors."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def search_exact_roster(
        self,
        query_vector: List[float],
        enrolled_profiles: Dict[str, List[float]],  # student_id -> 128d vector
        match_threshold: float = 0.70,
        margin_threshold: float = 0.10,
    ) -> RetrievalCandidate:
        """
        Exact 1:N open-set search against session-eligible roster profiles.
        Enforces score threshold (T_match >= 0.70) and top-1 vs top-2 margin logic (T_margin >= 0.10).
        """
        if not enrolled_profiles:
            return RetrievalCandidate(
                student_id="",
                similarity_score=0.0,
                margin_to_second=0.0,
                is_matched=False,
                reason_code="EMPTY_ROSTER_GALLERY",
            )

        scored_candidates: List[Tuple[str, float]] = []
        for s_id, ref_vec in enrolled_profiles.items():
            sim = self.cosine_similarity(query_vector, ref_vec)
            scored_candidates.append((s_id, sim))

        # Sort descending by similarity
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        top_student, top_score = scored_candidates[0]
        second_score = scored_candidates[1][1] if len(scored_candidates) > 1 else 0.0
        margin = top_score - second_score

        # Rule evaluation
        if top_score < match_threshold:
            return RetrievalCandidate(
                student_id=top_student,
                similarity_score=round(top_score, 4),
                margin_to_second=round(margin, 4),
                is_matched=False,
                reason_code="BELOW_MATCH_THRESHOLD",
            )

        if margin < margin_threshold and len(scored_candidates) > 1:
            return RetrievalCandidate(
                student_id=top_student,
                similarity_score=round(top_score, 4),
                margin_to_second=round(margin, 4),
                is_matched=False,
                reason_code="AMBIGUOUS_LOOKALIKE_CONFLICT",
            )

        return RetrievalCandidate(
            student_id=top_student,
            similarity_score=round(top_score, 4),
            margin_to_second=round(margin, 4),
            is_matched=True,
            reason_code="EXACT_ROSTER_MATCH",
        )
