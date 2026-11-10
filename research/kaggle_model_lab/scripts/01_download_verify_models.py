#!/usr/bin/env python3
"""
FRS V7.1 K² Kaggle Model Lab — Stage 01: Model Download & SHA-256 Integrity Verification.
"""

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_and_verify(models_dir: Path, manifest_path: Path) -> dict:
    models_dir.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {}
    print("=" * 60)
    print("FRS V7.1 K² — MODEL DOWNLOAD & INTEGRITY VERIFICATION")
    print("=" * 60)

    for key, spec in manifest.get("models", {}).items():
        fname = spec["filename"]
        expected_hash = spec["sha256"]
        url = spec["source_url"]
        target = models_dir / fname

        print(f"\nProcessing [{spec['name']}] ({fname})...")

        # Download if not present
        if not target.is_file():
            print(f"  Downloading from {url}...")
            urllib.request.urlretrieve(url, target)
            print(f"  Downloaded: {target.stat().st_size} bytes")

        # Verify SHA-256
        actual_hash = compute_sha256(target)
        if actual_hash.lower() != expected_hash.lower():
            target.unlink(missing_ok=True)
            raise ValueError(
                f"FATAL INTEGRITY FAILURE for {fname}!\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual  : {actual_hash}\n"
                f"Corrupt artifact removed. Execution halted."
            )

        print(f"  [PASS] SHA-256 Verified: {actual_hash[:16]}... (matches manifest)")
        results[key] = {
            "name": spec["name"],
            "filename": fname,
            "path": str(target.resolve()),
            "sha256": actual_hash,
            "verified": True,
            "size_bytes": target.stat().st_size,
        }

    print("\n" + "=" * 60)
    print("All model artifacts cryptographically verified against repository manifest.")
    print("=" * 60)
    return results

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    lab_root = script_dir.parent
    m_dir = lab_root / "models"
    manifest_p = lab_root / "config" / "model_manifest.json"
    download_and_verify(m_dir, manifest_p)
