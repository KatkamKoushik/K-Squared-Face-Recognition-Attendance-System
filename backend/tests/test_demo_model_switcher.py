"""
K² FRS — Verification Suite for Dynamic Multi-Model Selection in Demo Visualizer.
Verifies switching between Option 1 (ArcFace 512-D), Option 3 (SFace 128-D), and Fine-Tuned SFace.
"""

import io
import pytest
from PIL import Image
from starlette.testclient import TestClient

from app.main import create_application
from app.core.database import SessionLocal, get_db
from app.domain.models.student import Student, EnrollmentProfile
from app.schemas.demo import DemoModelsResponse


@pytest.fixture
def client():
    app = create_application()
    with TestClient(app) as test_client:
        yield test_client


def test_get_available_models(client: TestClient):
    """Verifies that GET /demo/models returns all 3 models with required metadata."""
    res = client.get("/api/v1/demo/models")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "active_model_id" in data
    assert "models" in data
    models = data["models"]
    assert len(models) >= 3

    model_ids = [m["id"] for m in models]
    assert "option_1" in model_ids
    assert "option_3" in model_ids
    assert "finetuned_v2" in model_ids

    opt1 = next(m for m in models if m["id"] == "option_1")
    assert opt1["dimension"] == 512
    assert "SCRFD-500M" in opt1["name"]
    assert opt1["namespace"] == "mobilefacenet_512d_v1"

    opt3 = next(m for m in models if m["id"] == "option_3")
    assert opt3["dimension"] == 128
    assert "OpenCV Zoo SFace" in opt3["name"]
    assert opt3["namespace"] == "sface_128d_v1"


def test_select_active_model(client: TestClient):
    """Verifies that POST /demo/models/select switches active model."""
    res = client.post("/api/v1/demo/models/select", json={"model_id": "option_3"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["active_model_id"] == "option_3"

    res_check = client.get("/api/v1/demo/models")
    assert res_check.json()["data"]["active_model_id"] == "option_3"

    # Switch back to option_1
    res_back = client.post("/api/v1/demo/models/select", json={"model_id": "option_1"})
    assert res_back.status_code == 200
    assert res_back.json()["data"]["active_model_id"] == "option_1"


def test_enrolled_students_scoped_by_model(client: TestClient):
    """Verifies that GET /demo/enrolled-students?model_id=... returns profiles for the requested model."""
    res_opt1 = client.get("/api/v1/demo/enrolled-students?model_id=option_1")
    assert res_opt1.status_code == 200
    opt1_students = res_opt1.json()["data"]
    assert len(opt1_students) >= 28

    res_opt3 = client.get("/api/v1/demo/enrolled-students?model_id=option_3")
    assert res_opt3.status_code == 200
    opt3_students = res_opt3.json()["data"]
    assert len(opt3_students) >= 28

    res_ft = client.get("/api/v1/demo/enrolled-students?model_id=finetuned_v2")
    assert res_ft.status_code == 200
    ft_students = res_ft.json()["data"]
    assert len(ft_students) >= 28


def test_analyze_photo_with_explicit_model(client: TestClient):
    """Verifies that POST /demo/analyze works with both option_1 and option_3."""
    blank = Image.new("RGB", (320, 320), color=(255, 255, 255))
    buf = io.BytesIO()
    blank.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    # Analyze with Option 1
    res_opt1 = client.post(
        "/api/v1/demo/analyze",
        files={"file": ("blank.jpg", raw_bytes, "image/jpeg")},
        data={"model_id": "option_1"},
    )
    assert res_opt1.status_code == 200
    data_opt1 = res_opt1.json()["data"]
    assert data_opt1["model_id"] == "option_1"
    assert data_opt1["embedding_dimension"] == 512

    # Analyze with Option 3
    res_opt3 = client.post(
        "/api/v1/demo/analyze",
        files={"file": ("blank.jpg", raw_bytes, "image/jpeg")},
        data={"model_id": "option_3"},
    )
    assert res_opt3.status_code == 200
    data_opt3 = res_opt3.json()["data"]
    assert data_opt3["model_id"] == "option_3"
    assert data_opt3["embedding_dimension"] == 128
