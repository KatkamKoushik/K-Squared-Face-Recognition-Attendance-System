"""
FRS V7.1 K² — Cloudinary Object Storage and Image Management Service.
Handles Cloudinary uploads for student enrollment portraits and classroom frames,
storing HTTPS CDN URLs in PostgreSQL and providing seamless remote-or-local byte retrieval.
"""

import io
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import urllib.request
import uuid

import cloudinary
import cloudinary.uploader
from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudinaryStorageService:
    _configured: bool = False

    @classmethod
    def _ensure_configured(cls) -> bool:
        if cls._configured:
            return True

        cloud_name = settings.CLOUDINARY_CLOUD_NAME or os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = settings.CLOUDINARY_API_KEY or os.getenv("CLOUDINARY_API_KEY")
        api_secret = settings.CLOUDINARY_API_SECRET or os.getenv("CLOUDINARY_API_SECRET")

        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True,
            )
            cls._configured = True
            logger.info("Cloudinary storage configured for cloud: %s", cloud_name)
            return True

        logger.warning("Cloudinary credentials not provided. Falling back to local storage.")
        return False

    @classmethod
    def upload_image(
        cls,
        file_bytes: bytes,
        folder: str = "k2_frs/general",
        public_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        authenticated: bool = True,
    ) -> Dict[str, Any]:
        """
        Uploads image buffer to Cloudinary with authenticated delivery mode and fallback to local filesystem.
        Returns dict containing 'url', 'public_id', and 'provider'.
        """
        is_ready = cls._ensure_configured()
        if is_ready:
            try:
                buf = io.BytesIO(file_bytes)
                options: Dict[str, Any] = {
                    "folder": folder,
                    "resource_type": "image",
                    "overwrite": True,
                }
                if authenticated:
                    options["type"] = "authenticated"
                if public_id:
                    options["public_id"] = public_id
                if tags:
                    options["tags"] = tags

                res = cloudinary.uploader.upload(buf, **options)
                secure_url = res.get("secure_url") or res.get("url")
                return {
                    "url": secure_url,
                    "public_id": res.get("public_id"),
                    "provider": "cloudinary",
                    "authenticated": authenticated,
                }
            except Exception as e:
                logger.error("Cloudinary upload failed: %s. Falling back to local disk.", e)

        # Local fallback if Cloudinary is unavailable
        local_dir = Path(settings.STORAGE_DIR) / folder.replace("/", "_")
        local_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{public_id or uuid.uuid4().hex}.jpg"
        target_path = local_dir / fname
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        return {
            "url": str(target_path.resolve()),
            "public_id": fname,
            "provider": "local",
            "authenticated": authenticated,
        }

    @classmethod
    def generate_signed_url(
        cls,
        public_id: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """
        Generates a short-lived cryptographically signed URL for an authenticated asset.
        Prevents unauthorized public retrieval of raw biometric images.
        """
        if cls._ensure_configured():
            try:
                import cloudinary.utils
                url, _ = cloudinary.utils.cloudinary_url(
                    public_id,
                    type="authenticated",
                    sign_url=True,
                    secure=True,
                    expires_at=int(datetime.now(timezone.utc).timestamp()) + expiration_seconds,
                )
                return url
            except Exception as e:
                logger.error("Failed to generate signed Cloudinary URL: %s", e)
        return public_id

    @classmethod
    def delete_image(cls, public_id_or_path: str, is_authenticated: bool = True) -> bool:
        """
        Physically deletes an image from Cloudinary or local disk for cryptographic retention purges.
        """
        if not public_id_or_path:
            return False

        if cls._ensure_configured() and not os.path.isabs(public_id_or_path):
            try:
                options = {"type": "authenticated"} if is_authenticated else {}
                res = cloudinary.uploader.destroy(public_id_or_path, invalidate=True, **options)
                return res.get("result") == "ok"
            except Exception as e:
                logger.error("Failed to delete Cloudinary asset '%s': %s", public_id_or_path, e)

        # Check local disk
        p = Path(public_id_or_path)
        if p.exists() and p.is_file():
            try:
                p.unlink()
                return True
            except Exception as e:
                logger.error("Failed to delete local image file '%s': %s", public_id_or_path, e)
        return False

    @classmethod
    def upload_enrollment_portrait(
        cls,
        file_bytes: bytes,
        roll_number: str,
    ) -> str:
        """
        Uploads an approved or staged student enrollment portrait to Cloudinary.
        Folder: k2_frs/enrollments
        Returns public HTTPS URL.
        """
        clean_roll = roll_number.strip().upper().replace("/", "_").replace(" ", "_")
        pid = f"portrait_{clean_roll}_{uuid.uuid4().hex[:8]}"
        res = cls.upload_image(
            file_bytes=file_bytes,
            folder="k2_frs/enrollments",
            public_id=pid,
            tags=["enrollment", clean_roll],
        )
        return res["url"]

    @classmethod
    def upload_classroom_frame(
        cls,
        file_bytes: bytes,
        session_id: str,
        frame_index: int,
    ) -> str:
        """
        Uploads classroom capture frame to Cloudinary.
        Folder: k2_frs/sessions/<session_id>
        Returns public HTTPS URL.
        """
        pid = f"frame_{frame_index}_{uuid.uuid4().hex[:8]}"
        res = cls.upload_image(
            file_bytes=file_bytes,
            folder=f"k2_frs/sessions/{session_id}",
            public_id=pid,
            tags=["session", session_id],
        )
        return res["url"]

    @classmethod
    def load_image_bytes(cls, path_or_url: str) -> bytes:
        """
        Transparently retrieves raw bytes from either Cloudinary HTTPS URL or local file path.
        """
        if not path_or_url:
            raise ValueError("Empty image path or URL provided.")

        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            req = urllib.request.Request(
                path_or_url,
                headers={"User-Agent": "FRS-K2-Storage/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        else:
            p = Path(path_or_url)
            if not p.is_file():
                raise FileNotFoundError(f"Local image file not found: {path_or_url}")
            with open(p, "rb") as f:
                return f.read()
