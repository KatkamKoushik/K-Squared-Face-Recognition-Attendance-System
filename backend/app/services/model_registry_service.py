"""
FRS V7.1 K2 -- Model Registry Service & Integrity Gate.
Enforces governance, provenance checks, SHA-256 integrity verification,
and policy version binding for vision models.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.models.model_registry import ModelArtifact, PolicyVersion


class ModelRegistryService:

    DEFAULT_POLICY_ID = "policy_kucet_v7_1_default"

    @staticmethod
    def compute_file_sha256(file_path: Path) -> str:
        """Calculates exact cryptographic SHA-256 checksum of an on-disk model artifact."""
        if not file_path.is_file():
            raise FileNotFoundError(f"Model file does not exist: {file_path}")
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify_model_integrity(file_path: Path, expected_sha256: str) -> bool:
        """Fails closed if the model artifact on disk does not match the approved registry hash."""
        actual_hash = ModelRegistryService.compute_file_sha256(file_path)
        return actual_hash.lower() == expected_sha256.lower()

    @staticmethod
    def register_model_artifact(
        db: Session,
        name: str,
        task: str,
        format: str,
        source_uri: str,
        source_revision: str,
        sha256_hash: str,
        code_license: str,
        weight_license: str,
        data_provenance: str,
        approval_status: str = "APPROVED",
        input_width: int = 112,
        input_height: int = 112,
        color_order: str = "BGR",
        embedding_dimension: int = 128,
    ) -> ModelArtifact:
        """Registers an immutable model artifact record."""
        existing = db.execute(
            select(ModelArtifact).where(ModelArtifact.sha256_hash == sha256_hash)
        ).scalar_one_or_none()
        if existing:
            return existing

        artifact = ModelArtifact(
            name=name,
            task=task,
            format=format,
            source_uri=source_uri,
            source_revision=source_revision,
            sha256_hash=sha256_hash,
            code_license=code_license,
            weight_license=weight_license,
            data_provenance=data_provenance,
            approval_status=approval_status,
            input_width=input_width,
            input_height=input_height,
            color_order=color_order,
            embedding_dimension=embedding_dimension,
        )
        db.add(artifact)
        db.flush()
        return artifact

    @staticmethod
    def get_model_artifact_by_hash(db: Session, sha256_hash: str) -> ModelArtifact:
        """Retrieves a model artifact by its SHA-256 hash."""
        artifact = db.execute(
            select(ModelArtifact).where(ModelArtifact.sha256_hash == sha256_hash)
        ).scalar_one_or_none()
        if not artifact:
            raise ResourceNotFoundError(resource="ModelArtifact", identifier=sha256_hash)
        return artifact

    @staticmethod
    def get_active_policy(db: Session, policy_id: Optional[str] = None) -> PolicyVersion:
        """Retrieves active operational policy version."""
        target_id = policy_id or ModelRegistryService.DEFAULT_POLICY_ID
        policy = db.get(PolicyVersion, target_id)
        if not policy:
            # Create default policy if absent
            policy = ModelRegistryService.seed_default_registry(db)
        return policy

    @staticmethod
    def seed_default_registry(db: Session) -> PolicyVersion:
        """
        Seeds rights-cleared, approved OpenCV Zoo model artifacts and default institutional policy.
        """
        # 1. YuNet Face Detector
        yunet_hash = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
        yunet = db.execute(
            select(ModelArtifact).where(ModelArtifact.sha256_hash == yunet_hash)
        ).scalar_one_or_none()
        if not yunet:
            yunet = ModelArtifact(
                name="face_detection_yunet_2023mar",
                task="DETECTION",
                format="ONNX",
                source_uri="https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
                source_revision="2023mar",
                sha256_hash=yunet_hash,
                code_license="MIT",
                weight_license="MIT",
                data_provenance="WIDER FACE benchmark validation",
                approval_status="APPROVED",
                input_width=320,
                input_height=320,
                color_order="BGR",
                embedding_dimension=0,
            )
            db.add(yunet)
            db.flush()

        # 2. SFace Face Recognizer
        sface_hash = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
        sface = db.execute(
            select(ModelArtifact).where(ModelArtifact.sha256_hash == sface_hash)
        ).scalar_one_or_none()
        if not sface:
            sface = ModelArtifact(
                name="face_recognition_sface_2021dec",
                task="RECOGNITION",
                format="ONNX",
                source_uri="https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
                source_revision="2021dec",
                sha256_hash=sface_hash,
                code_license="Apache-2.0",
                weight_license="Apache-2.0",
                data_provenance="CASIA-WebFace / OpenCV Zoo",
                approval_status="APPROVED",
                input_width=112,
                input_height=112,
                color_order="BGR",
                embedding_dimension=128,
            )
            db.add(sface)
            db.flush()

        # 3. KUCET Fine-Tuned ArcFace Model Artifact (Hugging Face Hub)
        finetuned_hash = "61c33636f356cd235ac42526231ff54733985a00848a74cf0860d7ccb9617a3e"
        finetuned = db.execute(
            select(ModelArtifact).where(ModelArtifact.sha256_hash == finetuned_hash)
        ).scalar_one_or_none()
        if not finetuned:
            finetuned = ModelArtifact(
                name="kucet_frs_sface_finetuned",
                task="RECOGNITION",
                format="ONNX",
                source_uri="https://huggingface.co/Koushik-Katkam/kucet-frs-face-recognition/resolve/main/kucet_frs_sface_finetuned.onnx",
                source_revision="7.1.0",
                sha256_hash=finetuned_hash,
                code_license="Apache-2.0",
                weight_license="Apache-2.0",
                data_provenance="KUCET ArcFace 5000-Step Fine-Tuned Model (Hugging Face Hub)",
                approval_status="APPROVED",
                input_width=112,
                input_height=112,
                color_order="BGR",
                embedding_dimension=128,
            )
            db.add(finetuned)
            db.flush()

        # 4. Default Institutional Policy
        policy = db.get(PolicyVersion, ModelRegistryService.DEFAULT_POLICY_ID)
        if not policy:
            policy = PolicyVersion(
                id=ModelRegistryService.DEFAULT_POLICY_ID,
                policy_name="KUCET Institutional Attendance Policy V7.1",
                detector_model_hash=yunet_hash,
                recognizer_model_hash=sface_hash,
                match_cosine_threshold=0.363,
                margin_threshold=0.10,
                min_face_size_pixels=32,
                pad_mandatory=False,
                pad_threshold=0.85,
                is_active=True,
            )
            db.add(policy)
            db.flush()

        return policy
