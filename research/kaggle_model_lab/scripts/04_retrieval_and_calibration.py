#!/usr/bin/env python3
"""
FRS V7.1 K² Kaggle Model Lab — Stage 04: Exact Roster-Scoped Retrieval & Threshold Calibration.
Tests 1:N linear search, margin evaluation, and open-set unknown rejection.
"""

from typing import Dict, List, Tuple
import numpy as np

def cosine_sim(v1: np.ndarray, v2: np.ndarray) -> float:
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def search_roster(
    query_vec: np.ndarray,
    gallery: Dict[str, np.ndarray],
    match_threshold: float = 0.45,
    margin_threshold: float = 0.10,
) -> dict:
    if not gallery:
        return {"matched": False, "reason": "GALLERY_EMPTY", "student_id": None}

    scores = [(s_id, cosine_sim(query_vec, ref_vec)) for s_id, ref_vec in gallery.items()]
    scores.sort(key=lambda x: x[1], reverse=True)

    top1_id, top1_sim = scores[0]
    top2_sim = scores[1][1] if len(scores) > 1 else 0.0
    margin = top1_sim - top2_sim

    if top1_sim < match_threshold:
        return {
            "matched": False,
            "student_id": top1_id,
            "score": round(top1_sim, 4),
            "margin": round(margin, 4),
            "reason": "LOW_SIMILARITY_BELOW_MATCH_THRESHOLD",
        }

    if len(scores) > 1 and margin < margin_threshold:
        return {
            "matched": False,
            "student_id": top1_id,
            "score": round(top1_sim, 4),
            "margin": round(margin, 4),
            "reason": "AMBIGUOUS_LOOKALIKE_CONFLICT",
        }

    return {
        "matched": True,
        "student_id": top1_id,
        "score": round(top1_sim, 4),
        "margin": round(margin, 4),
        "reason": "HIGH_CONFIDENCE_MATCH" if top1_sim >= 0.70 else "VERIFIED_MATCH",
    }

def run_retrieval_experiment() -> dict:
    print("=" * 60)
    print("STAGE 04 — EXACT ROSTER RETRIEVAL & CALIBRATION")
    print("=" * 60)

    rng = np.random.RandomState(42)

    # 1. Populate a synthetic gallery of 10 enrolled student vectors on S^127
    gallery: Dict[str, np.ndarray] = {}
    for i in range(1, 11):
        s_id = f"24KU1A05{i:02d}"
        v = rng.randn(128).astype(np.float32)
        v = v / np.linalg.norm(v)
        gallery[s_id] = v

    print(f"  [GALLERY] Initialized mock gallery with {len(gallery)} enrolled identities.")

    # Test Case A: Query identical to enrolled Student 01 (+ subtle noise simulating camera lighting)
    query_known = gallery["24KU1A0501"] + rng.randn(128).astype(np.float32) * 0.05
    query_known = query_known / np.linalg.norm(query_known)
    res_known = search_roster(query_known, gallery)
    print(f"  [TEST A - KNOWN STUDENT] Match: {res_known['student_id']}, Score: {res_known['score']}, Margin: {res_known['margin']}, Reason: {res_known['reason']}")
    assert res_known["matched"] is True
    assert res_known["student_id"] == "24KU1A0501"

    # Test Case B: Query from an Unknown Person (orthogonal to gallery)
    query_unknown = rng.randn(128).astype(np.float32)
    query_unknown = query_unknown / np.linalg.norm(query_unknown)
    res_unknown = search_roster(query_unknown, gallery)
    print(f"  [TEST B - UNKNOWN PROBE] Match: {res_unknown['student_id']}, Score: {res_unknown['score']}, Margin: {res_unknown['margin']}, Reason: {res_unknown['reason']}")
    assert res_unknown["matched"] is False
    assert res_unknown["reason"] == "LOW_SIMILARITY_BELOW_MATCH_THRESHOLD"

    # Test Case C: Lookalike Ambiguity (Query sits right between Student 02 and Student 03)
    query_ambiguous = (gallery["24KU1A0502"] + gallery["24KU1A0503"]) / 2.0
    query_ambiguous = query_ambiguous / np.linalg.norm(query_ambiguous)
    res_ambiguous = search_roster(query_ambiguous, gallery, match_threshold=0.45, margin_threshold=0.10)
    print(f"  [TEST C - LOOKALIKE AMBIGUITY] Match: {res_ambiguous['student_id']}, Score: {res_ambiguous['score']}, Margin: {res_ambiguous['margin']}, Reason: {res_ambiguous['reason']}")
    assert res_ambiguous["matched"] is False
    assert res_ambiguous["reason"] == "AMBIGUOUS_LOOKALIKE_CONFLICT"

    print("  [PASS] Retrieval logic safely distinguishes known, unknown, and lookalike candidates.")
    return {
        "status": "SUCCESS",
        "known_test": res_known,
        "unknown_test": res_unknown,
        "ambiguous_test": res_ambiguous,
    }

if __name__ == "__main__":
    run_retrieval_experiment()
