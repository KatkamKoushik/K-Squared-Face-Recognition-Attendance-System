"""
FRS V7.1 K2 -- Recognizer & Exact Roster Search Adapter.
Enforces exact cosine retrieval, margin evaluation, and open-set unknown classification.
Executes rights-cleared OpenCV Zoo SFace ONNX model with strict SHA-256 integrity verification
and fail-closed mathematical inference.
"""

import hashlib
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
import numpy as np
import cv2
from app.worker.contracts import EmbeddingResult, RetrievalCandidate, QualityResult


class RecognizerAdapter:

    MODEL_HASH = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
    FINETUNED_HASH = "61c33636f356cd235ac42526231ff54733985a00848a74cf0860d7ccb9617a3e"
    FINETUNED_HASH_V2 = "0d980b104c783bc4230b074d5b44b9bf329b6cc5d457ba92416b5d6b7000755f"
    NAMESPACE = "sface_128d_v1"
    DEFAULT_FILENAME = "face_recognition_sface_2021dec.onnx"
    FINETUNED_FILENAME = "kucet_frs_sface_finetuned.onnx"

    APPROVED_HASHES = {
        MODEL_HASH: "sface_128d_v1",
        FINETUNED_HASH: "kucet_frs_sface_finetuned_v1",
        FINETUNED_HASH_V2: "kucet_frs_sface_finetuned_v2",
    }

    def __init__(self, model_path: Optional[Path] = None, strict_mode: Optional[bool] = None):
        self.strict_mode = strict_mode if strict_mode is not None else (os.getenv("STRICT_INFERENCE", "1") == "1")
        self.model_hash = self.MODEL_HASH
        self.namespace = self.NAMESPACE
        self.model_path = self._resolve_model_path(model_path)
        self._recognizer: Optional[cv2.FaceRecognizerSF] = None
        self._init_recognizer()

    def _compute_sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _resolve_model_path(self, explicit_path: Optional[Path]) -> Path:
        """Discovers SFace ONNX model path across local, repo-relative, and container locations."""
        if explicit_path:
            return Path(explicit_path)
        preferred_filename = (
            self.FINETUNED_FILENAME
            if os.getenv("USE_FINETUNED_MODEL") == "1"
            else self.DEFAULT_FILENAME
        )
        candidates = [
            Path("backend/models") / preferred_filename,
            Path("models") / preferred_filename,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / preferred_filename,
            Path("/app/models") / preferred_filename,
            Path("backend/models") / self.DEFAULT_FILENAME,
            Path("models") / self.DEFAULT_FILENAME,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / self.DEFAULT_FILENAME,
            Path("/app/models") / self.DEFAULT_FILENAME,
        ]
        for p in candidates:
            resolved = p.resolve()
            if resolved.is_file():
                return resolved
        return Path("backend/models") / preferred_filename

    def _init_recognizer(self):
        resolved = Path(self.model_path).resolve()
        if not resolved.is_file():
            if self.strict_mode:
                raise FileNotFoundError(
                    f"SFace face recognizer ONNX model file not found at {resolved}. "
                    "Run scripts/download_vision_models.py to download weights."
                )
            self._recognizer = None
            return

        actual_hash = self._compute_sha256(resolved)
        if actual_hash not in self.APPROVED_HASHES:
            if self.strict_mode:
                raise ValueError(
                    f"SFace model SHA-256 hash mismatch: expected one of {list(self.APPROVED_HASHES.keys())}, got {actual_hash}"
                )
            self._recognizer = None
            return

        self.model_hash = actual_hash
        self.namespace = self.APPROVED_HASHES[actual_hash]

        try:
            self._recognizer = cv2.FaceRecognizerSF.create(
                model=str(resolved),
                config="",
            )
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(f"Failed to initialize cv2.FaceRecognizerSF from {resolved}: {exc}") from exc
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
        if self._recognizer is None:
            raise RuntimeError(
                f"SFace face recognizer ONNX model is not available or failed to load from {self.model_path}."
            )

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
                namespace=self.namespace,
                recognizer_model_hash=self.model_hash,
            )
        except Exception as e:
            raise RuntimeError(f"SFace alignCrop/feature extraction failed: {e}") from e

    def compute_embedding(self, face_crop: Image.Image) -> EmbeddingResult:
        """
        Computes 128-D L2-normalized embedding vector on unit hypersphere S^127.
        """
        if self._recognizer is None:
            raise RuntimeError(
                f"SFace face recognizer ONNX model is not available or failed to load from {self.model_path}."
            )

        try:
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
                namespace=self.namespace,
                recognizer_model_hash=self.model_hash,
            )
        except Exception as e:
            raise RuntimeError(f"SFace feature extraction failed: {e}") from e

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Computes cosine similarity between two unit vectors.
        For unit vectors ||u|| = ||v|| = 1.0, cosine similarity is identical to dot product.
        """
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
        enrolled_profiles: Dict[str, List[float]],  # student_id -> vector
        match_threshold: float = 0.363,
        margin_threshold: float = 0.10,
    ) -> RetrievalCandidate:
        """
        Exact 1:N linear search across enrolled roster gallery.
        Evaluates top-1 match score, top-2 score margin, and open-set ambiguity.
        """
        if not enrolled_profiles:
            return RetrievalCandidate(
                student_id="",
                similarity_score=0.0,
                margin_to_second=0.0,
                is_matched=False,
                reason_code="GALLERY_EMPTY_NO_ENROLLED_PROFILES",
            )

        scores: List[Tuple[str, float]] = []
        for s_id, ref_vec in enrolled_profiles.items():
            sim = self.cosine_similarity(query_vector, ref_vec)
            scores.append((s_id, sim))

        # Sort descending by similarity
        scores.sort(key=lambda x: x[1], reverse=True)

        top1_id, top1_sim = scores[0]
        top2_sim = scores[1][1] if len(scores) > 1 else 0.0
        margin = top1_sim - top2_sim

        if top1_sim < match_threshold:
            return RetrievalCandidate(
                student_id=top1_id,
                similarity_score=round(top1_sim, 4),
                margin_to_second=round(margin, 4),
                is_matched=False,
                reason_code="BELOW_MATCH_THRESHOLD",
            )

        if len(scores) > 1 and margin < margin_threshold:
            return RetrievalCandidate(
                student_id=top1_id,
                similarity_score=round(top1_sim, 4),
                margin_to_second=round(margin, 4),
                is_matched=False,
                reason_code="AMBIGUOUS_LOOKALIKE_CONFLICT",
            )

        return RetrievalCandidate(
            student_id=top1_id,
            similarity_score=round(top1_sim, 4),
            margin_to_second=round(margin, 4),
            is_matched=True,
            reason_code="VERIFIED_HIGH_CONFIDENCE_MATCH",
        )

    def assess_quality(
        self,
        face_crop: Image.Image,
        min_variance: float = 50.0,
        min_size: int = 24,
    ) -> QualityResult:
        """
        Estimates per-face quality (blur via Laplacian variance, size, contrast).
        Rejects tiny faces (< min_size px, default 24) or blurry/flat crops (< min_variance, default 50.0).
        """
        w, h = face_crop.size
        if w < min_size or h < min_size:
            return QualityResult(score=0.15, is_usable=False, reason_code="FACE_TOO_SMALL")

        try:
            crop_cv = cv2.cvtColor(np.array(face_crop.convert("RGB")), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(crop_cv, cv2.COLOR_BGR2GRAY)
            variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            if variance < min_variance:
                return QualityResult(
                    score=round(min(0.49, (variance / min_variance) * 0.49), 4),
                    is_usable=False,
                    reason_code="BLURRY_FACE",
                )
            score = round(min(0.98, 0.70 + (variance / 500.0) * 0.28), 4)
            return QualityResult(score=score, is_usable=True, reason_code="QUALITY_ACCEPTABLE")
        except Exception:
            return QualityResult(score=0.0, is_usable=False, reason_code="QUALITY_ASSESSMENT_ERROR")
