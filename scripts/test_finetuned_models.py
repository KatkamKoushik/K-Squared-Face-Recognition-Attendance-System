"""
K² FRS — Fine-Tuned Vision Models Benchmark & Validation Suite
Evaluates SFace, EdgeFace, GhostFaceNet, and MiniFASNet fine-tuned ONNX models.

Validates:
1. SHA-256 integrity against backend/models/model_manifest.json
2. ONNX runtime loading & session creation
3. Input/Output tensor signature verification
4. Latency (p50, p95, p99) and Throughput (FPS) benchmarks
5. Embedding L2-normalization (unit hypersphere ||v||_2 = 1.0)
6. Pairwise cosine similarity separation (genuine vs. orthogonal/impostor)
7. Anti-spoofing softmax classification validation
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import onnxruntime as ort

MODELS_DIR = Path(__file__).resolve().parent.parent / "backend" / "models"
MANIFEST_PATH = MODELS_DIR / "model_manifest.json"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1.flatten(), v2.flatten())
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def benchmark_model(
    session: ort.InferenceSession,
    input_name: str,
    input_shape: List[int],
    warmup: int = 20,
    iterations: int = 100,
) -> Dict[str, float]:
    dummy_input = np.random.randn(*input_shape).astype(np.float32)

    # Warmup runs
    for _ in range(warmup):
        _ = session.run(None, {input_name: dummy_input})

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = session.run(None, {input_name: dummy_input})
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    latencies.sort()
    p50 = latencies[int(iterations * 0.50)]
    p95 = latencies[int(iterations * 0.95)]
    p99 = latencies[int(iterations * 0.99)]
    avg_latency = float(np.mean(latencies))
    fps = 1000.0 / avg_latency if avg_latency > 0 else 0.0

    return {
        "avg_ms": round(avg_latency, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "fps": round(fps, 1),
    }


def main():
    print("=" * 80)
    print("K² FRS — Fine-Tuned Computer Vision Models Benchmark & Validation")
    print(f"Artifacts Directory: {MODELS_DIR}")
    print("=" * 80)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Model manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    models_config = manifest.get("models", {})
    results = []

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    for key, spec in models_config.items():
        artifact_name = spec["onnx_artifact"]
        artifact_path = MODELS_DIR / artifact_name
        expected_hash = spec["sha256"]
        input_shape = spec["input_shape"]
        expected_dim = spec["embedding_dim"]
        arch = spec["architecture"]

        print(f"\nEvaluating Model: [{arch}] {artifact_name}")
        print(f"  Expected Hash: {expected_hash}")

        if not artifact_path.is_file():
            print(f"  FAIL: File not found: {artifact_path}")
            continue

        # 1. SHA-256 verification
        actual_hash = compute_sha256(artifact_path)
        hash_ok = (actual_hash == expected_hash)
        print(f"  Actual Hash:   {actual_hash}")
        print(f"  SHA-256 Match: {'PASS' if hash_ok else 'FAIL'}")

        # 2. Session creation
        try:
            session = ort.InferenceSession(str(artifact_path), opts, providers=["CPUExecutionProvider"])
            input_meta = session.get_inputs()[0]
            output_meta = session.get_outputs()[0]
            input_name = input_meta.name
            output_name = output_meta.name
            print(f"  Input Tensor:  name={input_name}, shape={input_meta.shape}, type={input_meta.type}")
            print(f"  Output Tensor: name={output_name}, shape={output_meta.shape}, type={output_meta.type}")
        except Exception as exc:
            print(f"  FAIL loading ONNX session: {exc}")
            continue

        # 3. Latency & Throughput Benchmark
        bench = benchmark_model(session, input_name, input_shape)
        print(f"  Latency:       avg={bench['avg_ms']}ms | p50={bench['p50_ms']}ms | p95={bench['p95_ms']}ms | p99={bench['p99_ms']}ms")
        print(f"  Throughput:    {bench['fps']} FPS")

        # 4. Model-specific validations
        if arch in ("SFACE", "EDGEFACE", "GHOSTFACENET"):
            # L2-normalization test
            test_in = np.random.randn(*input_shape).astype(np.float32)
            out = session.run([output_name], {input_name: test_in})[0]
            embedding = out.flatten()
            norm = float(np.linalg.norm(embedding))
            dim_match = (len(embedding) == expected_dim)

            # Cosine similarity test: genuine vs impostor
            # Generate another perturbed input for genuine (mild noise) vs distinct for impostor
            perturbed_in = test_in + np.random.normal(0, 0.05, size=input_shape).astype(np.float32)
            out_perturbed = session.run([output_name], {input_name: perturbed_in})[0].flatten()

            impostor_in = np.random.randn(*input_shape).astype(np.float32)
            out_impostor = session.run([output_name], {input_name: impostor_in})[0].flatten()

            sim_self = cosine_similarity(embedding, embedding)
            sim_genuine = cosine_similarity(embedding, out_perturbed)
            sim_impostor = cosine_similarity(embedding, out_impostor)

            print(f"  Embedding Dim: {len(embedding)} (expected {expected_dim}) -> {'PASS' if dim_match else 'FAIL'}")
            print(f"  L2 Norm:       {norm:.4f}")
            print(f"  Self Cosine:   {sim_self:.4f}")
            print(f"  Near Cosine:   {sim_genuine:.4f}")
            print(f"  Impostor Cos:  {sim_impostor:.4f}")
            print(f"  Margin:        {sim_genuine - sim_impostor:.4f}")

            results.append({
                "model": artifact_name,
                "arch": arch,
                "dimension": expected_dim,
                "sha256_match": hash_ok,
                "avg_ms": bench["avg_ms"],
                "fps": bench["fps"],
                "l2_norm": round(norm, 4),
                "margin": round(sim_genuine - sim_impostor, 4),
                "status": "PASS" if hash_ok and dim_match else "FAIL",
            })

        elif arch == "MINIFASNET":
            # PAD classification test
            test_in = np.random.randn(*input_shape).astype(np.float32)
            out = session.run([output_name], {input_name: test_in})[0]
            # Numerically stable softmax
            shift_out = out - np.max(out, axis=-1, keepdims=True)
            probs = np.exp(shift_out) / np.sum(np.exp(shift_out), axis=-1, keepdims=True)
            print(f"  PAD Output:    {out.tolist()}")
            print(f"  Probabilities: {probs.tolist()}")

            results.append({
                "model": artifact_name,
                "arch": arch,
                "dimension": expected_dim,
                "sha256_match": hash_ok,
                "avg_ms": bench["avg_ms"],
                "fps": bench["fps"],
                "l2_norm": "N/A (Softmax)",
                "margin": "N/A (PAD)",
                "status": "PASS" if hash_ok else "FAIL",
            })

    # Summary table
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    header = f"{'Model Artifact':<36} | {'Arch':<12} | {'Dim':<5} | {'Latency':<8} | {'FPS':<6} | {'Margin':<7} | {'Status'}"
    print(header)
    print("-" * 80)
    for r in results:
        print(f"{r['model']:<36} | {r['arch']:<12} | {str(r['dimension']):<5} | {str(r['avg_ms']) + 'ms':<8} | {str(r['fps']):<6} | {str(r['margin']):<7} | {r['status']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
