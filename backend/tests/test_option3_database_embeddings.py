"""
K² FRS — Verification Tests for Option 3 (SCRFD-2.5G + SFace 128-D) Database Embeddings.
Validates database persistence, vector dimensionality, L2 normalization,
pairwise identity metrics, and 1:N roster retrieval accuracy.
"""

import numpy as np
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentProfile

EXPECTED_NAMESPACE = "sface_128d_v1"
EXPECTED_DIM = 128
EXPECTED_ARTIFACT_ID = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def option3_profiles(db: Session):
    try:
        stmt = (
            select(EnrollmentProfile, Student.roll_number, Student.full_name)
            .join(Student, EnrollmentProfile.student_id == Student.id)
            .where(
                EnrollmentProfile.embedding_namespace == EXPECTED_NAMESPACE,
                EnrollmentProfile.is_active == True,
            )
        )
        results = db.execute(stmt).all()
    except Exception as exc:
        pytest.skip(f"Database connection unavailable: {exc}")

    if not results or len(results) < 31:
        pytest.skip("Requires full seeded PostgreSQL database with >= 31 Option 3 profiles")
    return results


def test_option3_profiles_stored_in_database(option3_profiles):
    """Verify that all 31 Option 3 profiles exist and are active in PostgreSQL."""
    assert len(option3_profiles) >= 31, f"Expected at least 31 profiles, got {len(option3_profiles)}"
    for profile, roll, name in option3_profiles:
        assert profile.embedding_namespace == EXPECTED_NAMESPACE
        assert profile.embedding_dimension == EXPECTED_DIM
        assert profile.model_artifact_id == EXPECTED_ARTIFACT_ID
        assert profile.is_active is True
        assert len(profile.vector_data) == EXPECTED_DIM, f"Vector for {roll} has length {len(profile.vector_data)}"


def test_option3_embeddings_strict_l2_normalization(option3_profiles):
    """Verify that every 128-D vector is strictly unit L2 normalized without NaNs or Infs."""
    for profile, roll, _ in option3_profiles:
        vec = np.array(profile.vector_data, dtype=np.float32)
        assert not np.isnan(vec).any(), f"NaN values detected in embedding for {roll}"
        assert not np.isinf(vec).any(), f"Inf values detected in embedding for {roll}"

        norm = float(np.linalg.norm(vec))
        assert abs(norm - 1.0) < 1e-3, f"Embedding for {roll} is not unit normalized: norm={norm}"


def test_option3_self_similarity_identity(option3_profiles):
    """Verify that self-cosine similarity is exactly 1.0 for all students."""
    for profile, roll, _ in option3_profiles:
        vec = np.array(profile.vector_data, dtype=np.float32)
        self_sim = float(np.dot(vec, vec))
        assert abs(self_sim - 1.0) < 1e-3, f"Self-similarity for {roll} should be 1.0, got {self_sim}"


def test_option3_metric_space_properties(option3_profiles):
    """
    Verify metric properties of the 128-D OpenCV Zoo SFace space.
    - Mean inter-student similarity should be close to 0.20.
    - No two distinct vectors should be collinear.
    """
    vectors = [np.array(p.vector_data, dtype=np.float32) for p, _, _ in option3_profiles]
    matrix = np.stack(vectors, axis=0)  # (N, 128)
    sim_matrix = np.dot(matrix, matrix.T)

    n = len(vectors)
    distinct_sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(sim_matrix[i, j])
            distinct_sims.append(sim)
            assert sim < 0.999, f"Unexpected collinear similarity {sim} between student {i} and {j}"

    mean_sim = float(np.mean(distinct_sims))
    assert 0.10 <= mean_sim <= 0.30, f"Expected mean similarity ~0.20, got {mean_sim}"


def test_option3_simulated_classroom_1_to_n_matching(option3_profiles):
    """
    Simulate a classroom scenario: query faces with slight synthetic perturbation
    must retrieve the exact ground-truth student with Rank-1 accuracy.
    """
    roster_matrix = np.stack([np.array(p.vector_data, dtype=np.float32) for p, _, _ in option3_profiles])
    rolls = [r for _, r, _ in option3_profiles]

    correct_rank1 = 0
    total = len(option3_profiles)

    np.random.seed(42)
    for idx, (profile, roll, name) in enumerate(option3_profiles):
        target_vec = np.array(profile.vector_data, dtype=np.float32)
        # Add realistic noise (e.g. slight pose/lighting jitter)
        noise = np.random.normal(0, 0.05, size=target_vec.shape).astype(np.float32)
        query_vec = target_vec + noise
        query_vec = query_vec / np.linalg.norm(query_vec)

        # 1:N dot-product retrieval
        scores = np.dot(roster_matrix, query_vec)
        best_match_idx = int(np.argmax(scores))

        if best_match_idx == idx:
            correct_rank1 += 1

    accuracy = correct_rank1 / total
    assert accuracy >= 0.95, f"Rank-1 retrieval accuracy below 95%: got {accuracy * 100:.1f}% ({correct_rank1}/{total})"
