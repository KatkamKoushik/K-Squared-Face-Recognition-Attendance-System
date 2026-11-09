#!/usr/bin/env python3
"""
FRS V7.1 K² — Vision Model Weight Downloader & Integrity Verifier.
Downloads official OpenCV Zoo YuNet and SFace ONNX model artifacts and verifies SHA-256 checksums.
"""

import hashlib
import os
import sys
import urllib.request
from pathlib import Path

MODELS = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "description": "OpenCV Zoo YuNet Face Detection (2023mar, ONNX)",
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "description": "OpenCV Zoo SFace 128-D Face Recognition (2021dec, ONNX)",
    },
}


def compute_sha256(file_path: Path) -> str:
    """Computes exact SHA-256 hex digest of file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def download_model(name: str, config: dict, target_dir: Path) -> bool:
    """Downloads model if missing and verifies SHA-256 integrity."""
    target_path = target_dir / name
    expected_hash = config["sha256"].lower()

    if target_path.exists():
        actual_hash = compute_sha256(target_path)
        if actual_hash == expected_hash:
            print(f"[OK] {name} already exists and passes SHA-256 integrity check.")
            return True
        else:
            print(f"[WARN] {name} exists but hash mismatch (got {actual_hash[:8]}..., expected {expected_hash[:8]}...). Re-downloading...")
            target_path.unlink()

    print(f"[DOWNLOADING] {config['description']} from {config['url']}...")
    try:
        # Stream download
        req = urllib.request.Request(
            config["url"],
            headers={"User-Agent": "FRS-K2-Model-Downloader/1.0"},
        )
        with urllib.request.urlopen(req) as response, open(target_path, "wb") as out_file:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            while chunk := response.read(65536):
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end="", flush=True)
            print()

        actual_hash = compute_sha256(target_path)
        if actual_hash != expected_hash:
            target_path.unlink(missing_ok=True)
            raise ValueError(
                f"SHA-256 integrity failure for {name}: expected {expected_hash}, got {actual_hash}"
            )

        print(f"[VERIFIED] {name} verified successfully ({actual_hash}).")
        return True
    except Exception as e:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        print(f"[ERROR] Failed to download {name}: {e}", file=sys.stderr)
        return False


def main():
    repo_root = Path(__file__).resolve().parent.parent
    target_dir = repo_root / "backend" / "models"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== FRS V7.1 OpenCV Zoo ONNX Model Downloader ===")
    print(f"Target directory: {target_dir}")

    all_ok = True
    for name, config in MODELS.items():
        if not download_model(name, config, target_dir):
            all_ok = False

    if not all_ok:
        print("\n[FAIL] One or more models failed to download or verify.")
        sys.exit(1)

    print("\n[SUCCESS] All approved vision models verified and ready for live demo inference.")


if __name__ == "__main__":
    main()
