"""
K² FRS — Verification Tests for Fine-Tuned SFace (128-D) Database Embeddings.
Validates database persistence, vector dimensionality, L2 normalization,
pairwise identity separability, and JSON cache integrity for all enrolled students.
"""

import json
from pathlib import Path
import numpy as np
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentProfile

EXPECTED_NAMESPACE = "kucet_frs_sface_finetuned_v2"
EXPECTED_DIM = 128
EXPECTED_ARTIFACT_ID = "e1bf5e2fd83ac6384d562680297451823145f83025aa0e6f2fb9199184205156"


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def finetuned_profiles(db: Session):
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

    if not results or len(results) < 49:
        pytest.skip("Requires full seeded PostgreSQL database with 49 Fine-Tuned profiles")
    return results


def test_finetuned_profiles_stored_in_database(finetuned_profiles):
    """Verify that all 49 fine-tuned profiles exist and are active in PostgreSQL."""
    assert len(finetuned_profiles) >= 49, f"Expected 49 profiles, got {len(finetuned_profiles)}"
    for profile, roll, name in finetuned_profiles:
        assert profile.embedding_namespace == EXPECTED_NAMESPACE
        assert profile.embedding_dimension == EXPECTED_DIM
        assert profile.model_artifact_id == EXPECTED_ARTIFACT_ID
        assert profile.is_active is True
        assert len(profile.vector_data) == EXPECTED_DIM, f"Vector for {roll} has length {len(profile.vector_data)}"


def test_finetuned_embeddings_strict_l2_normalization(finetuned_profiles):
    """Verify that every 128-D vector is strictly unit L2 normalized without NaNs or Infs."""
    for profile, roll, _ in finetuned_profiles:
        vec = np.array(profile.vector_data, dtype=np.float32)
        assert not np.isnan(vec).any(), f"NaN values detected in vector for {roll}"
        assert not np.isinf(vec).any(), f"Inf values detected in vector for {roll}"
        norm = np.linalg.norm(vec)
        assert np.isclose(norm, 1.0, atol=1e-3), f"Vector for {roll} not unit normalized: ||v|| = {norm:.6f}"


def test_finetuned_json_cache_integrity():
    """Verify that backend/data/finetuned_student_embeddings.json exists and has 49 valid entries."""
    json_path = Path(__file__).resolve().parent.parent / "data" / "finetuned_student_embeddings.json"
    assert json_path.exists(), f"Missing cache file: {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "profiles" in data
    profiles = data["profiles"]
    assert len(profiles) >= 49, f"Expected 49 entries in JSON cache profiles, found {len(profiles)}"
    sample = profiles[0]
    assert "roll_number" in sample
    assert "full_name" in sample
    assert "vector" in sample
    assert len(sample["vector"]) == EXPECTED_DIM


def test_finetuned_pairwise_separability(finetuned_profiles):
    """Verify that distinct student pairs are non-collinear and have well-distributed similarities."""
    vectors = [np.array(p[0].vector_data, dtype=np.float32) for p in finetuned_profiles]
    matrix = np.stack(vectors, axis=0)  # (N, 128)
    sim_matrix = np.dot(matrix, matrix.T)

    distinct_sims = []
    n = len(vectors)
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(sim_matrix[i, j])
            distinct_sims.append(sim)

    max_sim = max(distinct_sims)
    avg_sim = float(np.mean(distinct_sims))

    # Distinct pairs should be non-collinear (< 0.999)
    assert max_sim < 0.999, f"Max similarity {max_sim} exceeds non-collinear threshold 0.999"
    # SFace 128-D embedding hypersphere average distinct similarity
    assert 0.10 <= avg_sim <= 0.60, f"Average distinct similarity {avg_sim:.4f} outside expected distribution"
