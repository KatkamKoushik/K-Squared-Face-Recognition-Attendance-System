# ADR 0003: On-Premise ONNX Vision Pipeline for Student Privacy

## Status
Accepted

## Context
Commercial cloud computer vision services (such as AWS Rekognition, Azure Face, or Google Cloud Vision) require transmitting high-resolution classroom photographs containing hundreds of identifiable student faces across public networks to third-party cloud infrastructure. This model introduces substantial student privacy risks, violates the Digital Personal Data Protection (DPDP) Act of India, and incurs recurring cloud egress and per-image inference costs.

## Decision
1. All face detection, landmark alignment, and embedding extraction runs exclusively on-premise on university-controlled infrastructure using ONNX Runtime.
2. The vision pipeline utilizes:
   * **Face Detector:** SCRFD (Sample and Computation Redistribution for Efficient Face Detection), 2.5M parameters (`scrfd_2.5g_k2_v7.onnx`).
   * **Feature Embedder:** ArcFace (Additive Angular Margin Loss, ResNet-50 backbone), 512-dimensional output embeddings (`arcface_w600k_r50_v7.onnx`).
3. Query embeddings are normalized ($\|\mathbf{v}\|_2 = 1.0$), enabling cosine similarity computation via vector dot product against enrolled gallery templates.

## Consequences
### Positive
* Absolute data sovereignty: student biometric data never leaves university campus boundaries.
* Zero external API subscription or egress costs ($0.00$ marginal cost per session).
* Deterministic inference latency ($\le 85\text{ms}$ per candidate face).

### Negative
* Requires local CPU/GPU compute provisioning for background vision worker processes.

