#!/usr/bin/env python3
"""
K²-UFIN — Comprehensive Smoke Test Script.
Validates the complete model architecture, loss functions, margin warmup,
ONNX export, and ONNX Runtime inference in a single self-contained run.
"""

import os
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from research.k2_ufin.k2_ufin_stage_b import (
    K2UFINStageB,
    relational_distillation_loss,
    count_parameters,
)
from research.k2_ufin.train_stage_b_scratch import ArcFaceLoss


def run_smoke_test():
    print("=" * 70)
    print("K²-UFIN Stage B — Automated Verification & Smoke Test")
    print("=" * 70)

    # 1. Architecture & Parameter Count
    model = K2UFINStageB(embedding_dim=128)
    model.eval()
    num_params = count_parameters(model)
    print(f"[Check 1] Model parameter count: {num_params:,} ({num_params / 1e6:.2f}M)")
    assert 4_000_000 <= num_params <= 5_500_000, f"Unexpected param count: {num_params}"

    # 2. Forward Pass and Tensor Shapes
    batch_size = 4
    dummy_input = torch.randn(batch_size, 3, 112, 112)
    with torch.no_grad():
        emb, qual, pad = model(dummy_input)

    print(f"[Check 2] Forward pass successful:")
    print(f"  - Embeddings shape: {tuple(emb.shape)} (Expected: ({batch_size}, 128))")
    print(f"  - Quality shape:    {tuple(qual.shape)} (Expected: ({batch_size}, 1))")
    print(f"  - PAD logits shape: {tuple(pad.shape)} (Expected: ({batch_size}, 2))")

    assert emb.shape == (batch_size, 128)
    assert qual.shape == (batch_size, 1)
    assert pad.shape == (batch_size, 2)

    # 3. L2 Norm Unit Hypersphere Verification
    norms = torch.norm(emb, p=2, dim=1).numpy()
    print(f"[Check 3] Embedding L2 norms: {norms}")
    assert np.allclose(norms, 1.0, atol=1e-4), "Embeddings not properly normalized to unit sphere"

    # 4. ArcFace Loss with Dynamic Margin Warmup
    num_classes = 20
    arcface_head = ArcFaceLoss(
        num_classes=num_classes,
        embedding_dim=128,
        scale=32.0,
        initial_margin=0.20,
    )
    labels = torch.randint(0, num_classes, (batch_size,))

    loss_epoch_0 = arcface_head(emb, labels)
    arcface_head.set_margin(0.50)
    loss_epoch_10 = arcface_head(emb, labels)
    print(f"[Check 4] ArcFace loss computed:")
    print(f"  - Margin at start (0.20): Loss = {loss_epoch_0.item():.4f}")
    print(f"  - Margin at target (0.50): Loss = {loss_epoch_10.item():.4f}")
    assert loss_epoch_0.item() > 0.0 and loss_epoch_10.item() > 0.0

    # 5. Relational Distillation Loss
    teacher_512d = torch.randn(batch_size, 512)
    distill_loss = relational_distillation_loss(emb, teacher_512d)
    print(f"[Check 5] Relational distillation loss: {distill_loss.item():.6f}")
    assert distill_loss.item() >= 0.0

    # 6. ONNX Export and ONNX Runtime Verification
    export_dir = Path(__file__).resolve().parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    onnx_file = export_dir / "k2_ufin_stage_b_smoke.onnx"

    print(f"[Check 6] Exporting to ONNX: {onnx_file.name}...")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_file),
        input_names=["crops"],
        output_names=["embeddings", "quality", "pad_logits"],
        dynamic_axes={
            "crops": {0: "batch_size"},
            "embeddings": {0: "batch_size"},
            "quality": {0: "batch_size"},
            "pad_logits": {0: "batch_size"},
        },
        opset_version=14,
        dynamo=False,
    )
    print(f"  - Export size: {onnx_file.stat().st_size:,} bytes")
    assert onnx_file.exists() and onnx_file.stat().st_size > 1_000_000

    # 7. ONNX Runtime Inference
    import onnxruntime as ort

    session = ort.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
    test_batch = np.random.randn(6, 3, 112, 112).astype(np.float32)
    ort_outputs = session.run(None, {"crops": test_batch})

    ort_emb, ort_qual, ort_pad = ort_outputs
    print(f"[Check 7] ONNX Runtime batch-6 execution passed:")
    print(f"  - ORT embeddings: {ort_emb.shape} | L2 norm: {np.linalg.norm(ort_emb[0]):.4f}")
    print(f"  - ORT quality:    {ort_qual.shape}")
    print(f"  - ORT pad_logits: {ort_pad.shape}")
    assert ort_emb.shape == (6, 128)
    assert np.allclose(np.linalg.norm(ort_emb, axis=1), 1.0, atol=1e-4)

    print("=" * 70)
    print("ALL 7 K²-UFIN SMOKE CHECKS PASSED SUCCESSFULLY.")
    print("=" * 70)


if __name__ == "__main__":
    run_smoke_test()
