#!/usr/bin/env python3
"""
K² FRS Kaggle Model Lab — Stage 00: Environment & Hardware Audit.
Reports comprehensive runtime capabilities on Kaggle Linux (T4x2).
"""

import os
import platform
import sys
import psutil

def run_audit() -> dict:
    audit_data = {
        "python_version": sys.version.split()[0],
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "available_ram_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
        "total_disk_gb": round(psutil.disk_usage("/").total / (1024 ** 3), 2),
        "free_disk_gb": round(psutil.disk_usage("/").free / (1024 ** 3), 2),
        "gpus": [],
        "cuda_available": False,
        "opencv_version": None,
        "opencv_cuda": False,
        "onnxruntime_version": None,
        "onnxruntime_providers": [],
    }

    print("=" * 60)
    print("K² FRS KAGGLE MODEL LAB — ENVIRONMENT AUDIT")
    print("=" * 60)
    print(f"Python Version    : {audit_data['python_version']}")
    print(f"OS & Architecture : {audit_data['os']} ({audit_data['architecture']})")
    print(f"CPU Cores         : {audit_data['cpu_count_physical']} physical, {audit_data['cpu_count_logical']} logical")
    print(f"System RAM        : {audit_data['total_ram_gb']} GB total ({audit_data['available_ram_gb']} GB available)")
    print(f"Disk Space        : {audit_data['total_disk_gb']} GB total ({audit_data['free_disk_gb']} GB free)")

    # PyTorch / CUDA audit
    try:
        import torch
        audit_data["cuda_available"] = torch.cuda.is_available()
        audit_data["cuda_version"] = torch.version.cuda
        gpu_count = torch.cuda.device_count()
        print(f"\n[CUDA / PyTorch]")
        print(f"CUDA Available    : {audit_data['cuda_available']} (Version: {audit_data.get('cuda_version', 'N/A')})")
        print(f"GPU Device Count  : {gpu_count}")
        for i in range(gpu_count):
            name = torch.cuda.get_device_name(i)
            mem = round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 3), 2)
            audit_data["gpus"].append({"index": i, "name": name, "memory_gb": mem})
            print(f"  - GPU {i}: {name} ({mem} GB Dedicated VRAM)")
        if gpu_count == 2:
            print("  [NOTE] T4x2 provides 2 independent 16GB GPUs, not a shared 32GB memory pool.")
    except ImportError:
        print("\n[CUDA / PyTorch] PyTorch not installed; checking nvidia-smi directly")

    # OpenCV audit
    try:
        import cv2
        audit_data["opencv_version"] = cv2.__version__
        build_info = cv2.getBuildInformation()
        audit_data["opencv_cuda"] = "CUDA: YES" in build_info
        print(f"\n[OpenCV Vision Engine]")
        print(f"OpenCV Version    : {audit_data['opencv_version']}")
        print(f"OpenCV with CUDA  : {audit_data['opencv_cuda']}")
    except ImportError:
        print("\n[OpenCV Vision Engine] OpenCV not found!")

    # ONNX Runtime audit
    try:
        import onnxruntime as ort
        audit_data["onnxruntime_version"] = ort.__version__
        audit_data["onnxruntime_providers"] = ort.get_available_providers()
        print(f"\n[ONNX Runtime]")
        print(f"ONNX Runtime Ver  : {audit_data['onnxruntime_version']}")
        print(f"Available Providers: {audit_data['onnxruntime_providers']}")
    except ImportError:
        print("\n[ONNX Runtime] onnxruntime not found!")

    print("=" * 60)
    return audit_data

if __name__ == "__main__":
    run_audit()
