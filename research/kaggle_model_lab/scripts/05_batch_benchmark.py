#!/usr/bin/env python3
"""
K² FRS Kaggle Model Lab — Stage 05: Batch Benchmark (Latency, Throughput, Memory).
Evaluates inference performance across batch sizes on CPU / CUDA execution providers.
"""

import time
from pathlib import Path
from typing import List, Dict
import numpy as np
import cv2
import psutil

def run_benchmark(sface_path: Path, batch_sizes: List[int] = [1, 4, 8, 16, 32], iterations: int = 15) -> Dict:
    print("=" * 60)
    print("STAGE 05 — INFERENCE BATCH BENCHMARK")
    print("=" * 60)

    if not sface_path.is_file():
        raise FileNotFoundError(f"SFace model missing at {sface_path}. Run Stage 01 first.")

    recognizer = cv2.FaceRecognizerSF.create(model=str(sface_path.resolve()), config="")
    results = {}

    # Dummy face crop (112x112x3)
    crop = np.full((112, 112, 3), 120, dtype=np.uint8)

    # Warmup
    for _ in range(3):
        _ = recognizer.feature(crop)

    print(f"{'Batch Size':<12} | {'p50 Latency':<14} | {'p95 Latency':<14} | {'Throughput (FPS)':<18} | {'RAM Used (MB)':<12}")
    print("-" * 75)

    for b in batch_sizes:
        latencies = []
        # Pre-allocate batch
        batch_crops = [crop for _ in range(b)]

        for _ in range(iterations):
            t0 = time.perf_counter()
            for c in batch_crops:
                _ = recognizer.feature(c)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)

        latencies.sort()
        p50 = float(np.percentile(latencies, 50))
        p95 = float(np.percentile(latencies, 95))
        throughput = float((b / (p50 / 1000.0))) if p50 > 0 else 0.0
        mem_mb = float(psutil.Process().memory_info().rss / (1024 * 1024))

        results[str(b)] = {
            "batch_size": b,
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "throughput_fps": round(throughput, 2),
            "memory_mb": round(mem_mb, 2),
        }

        print(f"{b:<12} | {p50:8.2f} ms     | {p95:8.2f} ms     | {throughput:10.2f} img/s     | {mem_mb:8.1f} MB")

    print("-" * 75)
    print("Benchmark complete.")
    return results

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    lab_root = script_dir.parent
    sface = lab_root / "models" / "face_recognition_sface_2021dec.onnx"
    run_benchmark(sface)
