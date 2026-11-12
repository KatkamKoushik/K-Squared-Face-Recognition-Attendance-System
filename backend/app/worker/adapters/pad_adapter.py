"""
K² FRS — Presentation Attack Detection (PAD) Gate & Threat Model Policy.
Enforces that PAD is an independent fail-closed gate; identity score CANNOT bypass PAD.

Institutional Threat Model Disclosure:
In accordance with KUCET Biometric Governance Policy Section 4.3, still single-frame
RGB capture cannot unconditionally guarantee spoof rejection against high-definition
screen replays or 3D masks without hardware depth or challenge-response motion.
Therefore, the physical supervision of the university instructor serves as the
primary anti-spoofing boundary ("Faculty-in-the-Loop Supervision").
The automated gate performs passive spectral and texture variance screening.

STRICT FAIL-CLOSED POLICY:
- Missing face crop -> ERROR (is_live=False, never PASS).
- Corrupt/invalid crop -> ERROR (is_live=False).
- Analysis exception -> ERROR (is_live=False).
- Suspicious low texture (flat screens/paper) -> UNCERTAIN (is_live=False).
- Inconclusive texture score -> UNCERTAIN (is_live=False).
- Only verified natural skin gradient above threshold -> PASS (is_live=True).
"""

from typing import Optional
from PIL import Image
import numpy as np
from app.worker.contracts import SecurityResult


class PadAdapter:

    MODEL_HASH = "kucet_passive_pad_k2_supervised"

    def verify_liveness(
        self,
        face_crop: Optional[Image.Image],
        mandatory: bool = True,
        threshold: float = 0.85,
    ) -> SecurityResult:
        """
        Evaluates face liveness through passive texture analysis and fail-closed security policy.
        Never returns PASS on missing crop, analysis error, or inconclusive texture.
        """
        if not mandatory:
            return SecurityResult(
                is_live=False,
                score=0.0,
                status="SKIPPED",
                reason_code="FACULTY_SUPERVISED_ATTENDANCE_POLICY",
            )

        if face_crop is None:
            return SecurityResult(
                is_live=False,
                score=0.0,
                status="ERROR",
                reason_code="PAD_MISSING_FACE_CROP",
            )

        try:
            w, h = face_crop.size
            if w <= 0 or h <= 0:
                return SecurityResult(
                    is_live=False,
                    score=0.0,
                    status="ERROR",
                    reason_code="PAD_INVALID_DIMENSIONS",
                )

            crop_rgb = face_crop.convert("RGB")
            crop_arr = np.array(crop_rgb, dtype=np.float32)

            if crop_arr.size == 0 or np.all(np.isnan(crop_arr)):
                return SecurityResult(
                    is_live=False,
                    score=0.0,
                    status="ERROR",
                    reason_code="PAD_INVALID_PIXEL_DATA",
                )

            # 1. Grayscale luminance calculation
            gray = 0.2989 * crop_arr[:, :, 0] + 0.5870 * crop_arr[:, :, 1] + 0.1140 * crop_arr[:, :, 2]

            # 2. High-frequency spatial gradient analysis (Laplacian approximation)
            gy, gx = np.gradient(gray)
            gnorm = np.sqrt(gx**2 + gy**2)
            texture_variance = float(np.var(gnorm))

            # Normalize texture score to [0.0, 1.0] bounded range
            # Flat displays/screens typically exhibit abnormal uniformity or extreme moire
            if texture_variance < 5.0:
                # Suspiciously flat / low frequency (possible paper printout or blurred screen)
                score = round(max(0.20, texture_variance / 25.0), 4)
                return SecurityResult(
                    is_live=False,
                    score=score,
                    status="UNCERTAIN",
                    reason_code="PAD_LOW_TEXTURE_REQUIRES_FACULTY_INSPECTION",
                )

            # Normal human facial skin texture under classroom lighting
            score = round(min(0.98, 0.70 + (texture_variance / 100.0) * 0.25), 4)
            status = "PASS" if score >= threshold else "UNCERTAIN"
            reason = "PAD_TEXTURE_VERIFIED_PASS" if status == "PASS" else "PAD_INCONCLUSIVE_TEXTURE_VARIANCE"

            return SecurityResult(
                is_live=(status == "PASS"),
                score=score,
                status=status,
                reason_code=reason,
            )
        except Exception as exc:
            # STRICT FAIL-CLOSED: exceptions must never return PASS or is_live=True
            return SecurityResult(
                is_live=False,
                score=0.0,
                status="ERROR",
                reason_code=f"PAD_TEXTURE_ANALYSIS_EXCEPTION: {type(exc).__name__}",
            )
