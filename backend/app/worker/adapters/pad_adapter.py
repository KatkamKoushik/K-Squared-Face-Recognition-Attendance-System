"""
FRS V7.1 K² — Presentation Attack Detection (PAD) Gate Adapter.
Enforces that PAD is an independent gate; identity score CANNOT bypass PAD.
"""

from PIL import Image
from app.worker.contracts import SecurityResult


class PadAdapter:

    MODEL_HASH = "sha256_minifasnet_v7_1_mock"

    def verify_liveness(self, face_crop: Image.Image, mandatory: bool = False, threshold: float = 0.85) -> SecurityResult:
        """
        Evaluates face liveness.
        If mandatory is False, returns SKIPPED unless explicitly triggered.
        """
        if not mandatory:
            return SecurityResult(
                is_live=True,
                score=1.0,
                status="SKIPPED",
                reason_code="PAD_NOT_MANDATORY_FOR_POLICY",
            )

        # In production, runs MiniFASNet ONNX model
        liveness_score = 0.94
        if liveness_score >= threshold:
            return SecurityResult(
                is_live=True,
                score=liveness_score,
                status="PASS",
                reason_code="LIVENESS_CONFIRMED",
            )
        else:
            return SecurityResult(
                is_live=False,
                score=liveness_score,
                status="FAIL",
                reason_code="SPOOF_PRESENTATION_DETECTED",
            )
