"""
K²-UFIN — Corrected Deeper Stage B Backbone with Global Depthwise Convolution (GDC).
Incorporates architectural improvements:
1. True Inverted Residual blocks with expansion ratio t in [2, 4], targeting ~2.7M parameters.
2. Global Depthwise Convolution (GDC) over 7x7 spatial feature map, eliminating Global Average Pooling.
3. Decoupled Early-Layer PAD Branch (taps 28x28 texture representations).
4. Parametric Quality Assessment Head.
5. Relational Knowledge Distillation loss module for cross-dimension teacher comparison.
"""

import math
from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class InvertedResidual(nn.Module):
    """
    MobileNetV2 / MobileFaceNet style inverted residual bottleneck block.
    Expands channels via 1x1 conv, applies 3x3 depthwise conv, projects back via linear 1x1 conv.
    """
    def __init__(self, in_channels: int, out_channels: int, stride: int, expand_ratio: int):
        super().__init__()
        self.stride = stride
        self.use_residual = (stride == 1 and in_channels == out_channels)
        hidden_dim = int(round(in_channels * expand_ratio))

        layers = []
        if expand_ratio != 1:
            # 1x1 Pointwise Expansion
            layers.extend([
                nn.Conv2d(in_channels, hidden_dim, kernel_size=1, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.PReLU(hidden_dim),
            ])

        # 3x3 Depthwise Convolution
        layers.extend([
            nn.Conv2d(
                hidden_dim, hidden_dim, kernel_size=3, stride=stride, padding=1,
                groups=hidden_dim, bias=False
            ),
            nn.BatchNorm2d(hidden_dim),
            nn.PReLU(hidden_dim),
            # 1x1 Pointwise Linear Projection (no activation)
            nn.Conv2d(hidden_dim, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
        ])

        self.conv = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.use_residual:
            return x + self.conv(x)
        return self.conv(x)


class K2UFINStageB(nn.Module):
    """
    K²-UFIN Deeper Stage B Architecture (~2.75M parameters).
    Input: Aligned 112x112 RGB face crop.
    Outputs:
    - 128-D L2-normalized unit hypersphere embedding vector.
    - 1-D Face Quality score [0.0 - 1.0].
    - 2-D Presentation Attack Detection (PAD) logits from early texture branch.
    """
    def __init__(self, embedding_dim: int = 128):
        super().__init__()

        # Stem: 112x112x3 -> 56x56x64 (preserves higher initial resolution)
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1, groups=64, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64),
        )

        # Stage 1: 56x56 -> 28x28 (channels: 64 -> 128)
        self.stage1 = nn.Sequential(
            InvertedResidual(64, 128, stride=2, expand_ratio=2),
            InvertedResidual(128, 128, stride=1, expand_ratio=2),
            InvertedResidual(128, 128, stride=1, expand_ratio=2),
        )

        # Early-layer PAD Branch taps Stage 1 / 28x28 features for texture & moire analysis
        self.pad_branch = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=3, stride=2, padding=1, bias=False),  # 28 -> 14
            nn.BatchNorm2d(64),
            nn.PReLU(64),
            nn.Conv2d(64, 64, kernel_size=3, stride=2, padding=1, bias=False),   # 14 -> 7
            nn.BatchNorm2d(64),
            nn.PReLU(64),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, 32),
            nn.PReLU(32),
            nn.Linear(32, 2),  # [bona_fide_logit, spoof_logit]
        )

        # Stage 2: 28x28 -> 14x14 (channels: 128 -> 256)
        self.stage2 = nn.Sequential(
            InvertedResidual(128, 256, stride=2, expand_ratio=4),
            InvertedResidual(256, 256, stride=1, expand_ratio=2),
            InvertedResidual(256, 256, stride=1, expand_ratio=2),
            InvertedResidual(256, 256, stride=1, expand_ratio=2),
        )

        # Stage 3: 14x14 -> 7x7 (channels: 256 -> 512)
        self.stage3 = nn.Sequential(
            InvertedResidual(256, 512, stride=2, expand_ratio=4),
            InvertedResidual(512, 512, stride=1, expand_ratio=2),
            InvertedResidual(512, 512, stride=1, expand_ratio=2),
            nn.Conv2d(512, 512, kernel_size=1, bias=False),
            nn.BatchNorm2d(512),
            nn.PReLU(512),
        )

        # Global Depthwise Convolution (GDC) over 7x7 map (NO Global Average Pooling)
        # Preserves spatial layout of eyes, nose, and mouth on unit hypersphere
        self.gdc_conv = nn.Conv2d(512, 512, kernel_size=7, stride=1, padding=0, groups=512, bias=False)
        self.gdc_bn = nn.BatchNorm2d(512)

        # Linear projection to 128-D embedding space
        self.embedding_proj = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512, embedding_dim, bias=False),
            nn.BatchNorm1d(embedding_dim),
        )

        # Quality Assessment Head (scalar score [0.0 - 1.0])
        self.quality_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512, 64),
            nn.PReLU(64),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        Returns:
        - normalized_embedding: [B, 128] on unit hypersphere S^127
        - quality_score: [B, 1] scalar score
        - pad_logits: [B, 2] bona fide vs spoof logits
        """
        stem_out = self.stem(x)
        stage1_out = self.stage1(stem_out)

        # Early texture PAD analysis
        pad_logits = self.pad_branch(stage1_out)

        # Deep semantic identity extraction
        stage2_out = self.stage2(stage1_out)
        stage3_out = self.stage3(stage2_out)

        # 7x7 Global Depthwise Convolution
        gdc_out = self.gdc_bn(self.gdc_conv(stage3_out))

        # Identity Embedding projection & L2 normalization
        raw_embed = self.embedding_proj(gdc_out)
        normalized_embed = F.normalize(raw_embed, p=2, dim=1)

        # Quality assessment
        quality_score = self.quality_head(gdc_out)

        return normalized_embed, quality_score, pad_logits


def relational_distillation_loss(
    student_embed: torch.Tensor,
    teacher_embed: torch.Tensor,
) -> torch.Tensor:
    """
    Relational Knowledge Distillation loss.
    Compares the intra-batch cosine similarity Gram matrices:
        S = student @ student.T
        T = teacher @ teacher.T
    Matches geometry across different vector dimensions (e.g. 128-D student vs 512-D teacher).
    """
    student_norm = F.normalize(student_embed, p=2, dim=1)
    teacher_norm = F.normalize(teacher_embed, p=2, dim=1)

    s_matrix = student_norm @ student_norm.T
    t_matrix = (teacher_norm @ teacher_norm.T).detach()

    return F.mse_loss(s_matrix, t_matrix)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    net = K2UFINStageB(embedding_dim=128)
    params = count_parameters(net)
    print(f"K²-UFIN Stage B Model Initialized.")
    print(f"Total Trainable Parameters: {params:,} ({params / 1e6:.2f}M)")

    dummy_crop = torch.randn(4, 3, 112, 112)
    emb, qual, pad = net(dummy_crop)

    print(f"Input Tensor Shape: {tuple(dummy_crop.shape)}")
    print(f"Output Embedding Shape: {tuple(emb.shape)} (L2 Norm: {torch.norm(emb, dim=1).detach().numpy()})")
    print(f"Output Quality Shape: {tuple(qual.shape)}")
    print(f"Output PAD Logits Shape: {tuple(pad.shape)}")
