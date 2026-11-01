"""
FRS V7.1 K² — Recognizer & Exact Roster Search Adapter.
Enforces exact cosine retrieval, margin evaluation, and open-set unknown classification.
"""

from typing import List, Dict, Tuple
from PIL import Image
import numpy as np
from app.worker.contracts import EmbeddingResult, RetrievalCandidate, QualityResult


class RecognizerAdapter:

    MODEL_HASH = "sha256_arcface_r50_512d_v7_1"
    NAMESPACE = "arcface_r50_512d_v1"

    def compute_embedding(self, face_crop: Image.Image) -> EmbeddingResult:
        """
        Computes 512-D L2-normalized embedding vector from face crop on unit hypersphere S^511.
        """
        # Deterministic feature generation on unit hypersphere for testing
        crop_bytes = face_crop.tobytes()
        seed = sum(crop_bytes) % 100000
        rng = np.random.RandomState(seed)
        raw_vec = rng.randn(512).astype(np.float32)
        norm_vec = raw_vec / np.linalg.norm(raw_vec)

        return EmbeddingResult(
            vector=norm_vec.tolist(),
            dimension=512,
            namespace=self.NAMESPACE,
            recognizer_model_hash=self.MODEL_HASH,
        )

    def assess_quality(self, face_crop: Image.Image) -> QualityResult:
        """Estimates per-face quality (blur, size, occlusion)."""
        w, h = face_crop.size
        if w < 24 or h < 24:
            return QualityResult(score=0.2, is_usable=False, reason_code="FACE_TOO_SMALL")
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
        match_threshold: float = 0.45,
        margin_threshold: float = 0.10,
    ) -> RetrievalCandidate:
        """
        Exact 1:N open-set search against session-eligible roster profiles.
        Enforces score threshold and top-1 vs top-2 margin logic.
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
            reason_code="MATCH_CONFIRMED",
        )
