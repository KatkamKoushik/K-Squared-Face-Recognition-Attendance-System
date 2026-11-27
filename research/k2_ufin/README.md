# K²-UFIN — Unified Face Intelligence Network (Research Lab)

This directory contains the independent research implementation of **K²-UFIN**, a custom deep convolutional neural network designed specifically for KUCET classroom attendance.

---

## Architecture Overview (Stage B)

- **Backbone**: Inverted Residual Bottlenecks with channel expansion factors $t \in [2, 4]$.
- **Parameters**: ~4.62M trainable parameters across 16 convolutional layers.
- **Global Depthwise Convolution (GDC)**: Replaces Global Average Pooling (GAP) with a $7\times 7$ depthwise convolution (`Conv2d(512, 512, kernel_size=7, groups=512)`), preserving critical spatial landmark geometry on the unit hypersphere $\mathbb{S}^{127}$.
- **Decoupled Early-Layer PAD Branch**: Taps Stage 1 / Stage 2 ($28\times 28$) features to evaluate high-frequency skin textures, moiré, and print patterns before identity abstraction.
- **Quality Head**: Evaluates per-face crop usability (sharpness, resolution, exposure).

---

## Workflow & Step-by-Step Usage

### Step 1: Benchmark the Baseline Scoreboard
Measure the current production baseline (YuNet + SFace) on the held-out classroom test set:
```bash
python scripts/benchmark_baseline_scoreboard.py --dataset research/kaggle_model_lab/data/heldout_kucet --output reports/evidence/baseline_scoreboard.json
```

This outputs:
- Equal Error Rate (EER) and optimal threshold $\tau^*$.
- True Accept Rate at False Accept Rates $\text{TAR} @ \text{FAR}=10^{-3}$ and $\text{TAR} @ \text{FAR}=10^{-2}$.
- Detection and embedding latency profiles ($p50, p95, p99$).

### Step 2: Train Stage B from Scratch (ArcFace + Margin Warmup)
Train the custom Stage B model from pure random initialization:
```bash
python research/k2_ufin/train_stage_b_scratch.py --epochs 25 --batch-size 32 --warmup-epochs 10
```

- **Margin Warmup**: Starts with $m = 0.20$ and linearly ramps to $m = 0.50$ over the warmup epochs to stabilize initial angular convergence.
- **Distillation Mode (Optional Experiment)**:
  ```bash
  python research/k2_ufin/train_stage_b_scratch.py --epochs 25 --distill
  ```
  Applies relational distillation loss comparing batch Gram matrices ($S S^\top \approx T T^\top$) to experimentally test whether teacher guidance improves or degrades accuracy.

### Step 3: Promotion Gate Rule
Per Blueprint §11 and §14.3, K²-UFIN will only be promoted to replace the baseline SFace weights if and only if:
1. $\text{TAR} @ \text{FAR}=10^{-3}$ on the held-out set is $\ge$ the baseline recorded in [baseline_scoreboard.json](../../reports/evidence/baseline_scoreboard.json).
2. End-to-end multi-face batch latency is $\le 15\text{ ms}$ on standard server CPU.
