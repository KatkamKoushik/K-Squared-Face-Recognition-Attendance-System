"""
K² FRS - Complete Blueprint Model Fine-Tuning & Export Script
Institution: Kakatiya University College of Engineering & Technology (KUCET), Warangal
Target Environment: Kaggle (Dual Tesla T4 GPUs) / Linux / Windows
Models Supported: SFace (128-D), EdgeFace-Base (512-D), GhostFaceNet (128-D), MiniFASNetV2 (PAD)
"""

import os
import sys
import math
import time
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.optim.lr_scheduler")

# -----------------------------------------------------------------------------
# 1. Dataset Generators
# -----------------------------------------------------------------------------
# NOTICE (BIO-04 - Pipeline Demarcation):
# ClassroomFaceDataset generates synthetic geometric drawings for training pipeline
# testing and ONNX export validation only. It does NOT represent real human biometrics.
# Models trained on synthetic ellipses collapse human feature representation (inter-identity
# similarity > 0.90). Production environments MUST use pre-trained OpenCV Zoo weights
# (face_recognition_sface_2021dec.onnx) or fine-tune against consented human facial imagery.
# -----------------------------------------------------------------------------
class ClassroomFaceDataset(Dataset):
    def __init__(self, num_identities: int = 50, samples_per_id: int = 150, image_size: int = 112, is_train: bool = True):
        self.num_identities = num_identities
        self.samples_per_id = samples_per_id
        self.image_size = image_size
        self.is_train = is_train
        self.total_samples = num_identities * samples_per_id

        np.random.seed(1337 if is_train else 42)
        self.base_identities = []
        for i in range(num_identities):
            canvas = np.full((image_size, image_size, 3), 130 + (i % 25), dtype=np.uint8)
            skin_b = int(np.clip(160 + (i * 7) % 50, 120, 240))
            skin_g = int(np.clip(180 + (i * 5) % 40, 140, 230))
            skin_r = int(np.clip(210 + (i * 3) % 35, 170, 255))
            cv2.ellipse(canvas, (56, 56), (34 + (i % 5), 44 + (i % 7)), 0, 0, 360, (skin_b, skin_g, skin_r), -1)

            eye_spacing = 12 + (i % 10) * 2
            eye_y = 44 + (i % 6)
            cv2.circle(canvas, (56 - eye_spacing, eye_y), 4 + (i % 3), (30, 25, 20), -1)
            cv2.circle(canvas, (56 + eye_spacing, eye_y), 4 + (i % 3), (30, 25, 20), -1)
            cv2.line(canvas, (56, eye_y + 4), (56 + (i % 3) - 1, eye_y + 18), (140, 110, 90), 2)
            mouth_w = 10 + (i % 8) * 2
            cv2.ellipse(canvas, (56, eye_y + 28), (mouth_w, 4), 0, 0, 180, (60, 40, 40), 2)
            self.base_identities.append(canvas)

    def __len__(self):
        return self.total_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        identity_id = idx // self.samples_per_id
        img = self.base_identities[identity_id].copy()

        if self.is_train:
            gain = np.random.uniform(0.70, 1.30)
            bias = np.random.uniform(-30, 30)
            img = cv2.convertScaleAbs(img, alpha=gain, beta=bias)

            angle = np.random.uniform(-10.0, 10.0)
            M = cv2.getRotationMatrix2D((self.image_size // 2, self.image_size // 2), angle, 1.0)
            img = cv2.warpAffine(img, M, (self.image_size, self.image_size), borderMode=cv2.BORDER_REFLECT)

            if np.random.rand() > 0.5:
                ksize = np.random.choice([3, 5])
                img = cv2.GaussianBlur(img, (ksize, ksize), 0)

        tensor_img = torch.from_numpy(img).permute(2, 0, 1).float() / 127.5 - 1.0
        return tensor_img, identity_id


class AntiSpoofingDataset(Dataset):
    def __init__(self, num_samples: int = 4000, is_train: bool = True):
        self.num_samples = num_samples
        self.is_train = is_train
        np.random.seed(2026 if is_train else 777)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        is_spoof = (idx % 2 == 1)
        canvas = np.full((80, 80, 3), 140, dtype=np.uint8)
        cv2.ellipse(canvas, (40, 40), (25, 32), 0, 0, 360, (180, 190, 220), -1)

        if is_spoof:
            attack_type = np.random.choice(["moire", "screen", "cutout"])
            if attack_type == "moire":
                for y in range(0, 80, 4):
                    canvas[y:y+1, :] = np.clip(canvas[y:y+1, :].astype(int) + 35, 0, 255).astype(np.uint8)
            elif attack_type == "screen":
                canvas = cv2.convertScaleAbs(canvas, alpha=0.65, beta=60)
            else:
                cv2.rectangle(canvas, (10, 10), (70, 70), (240, 240, 240), 2)
            label = 1
        else:
            gain = np.random.uniform(0.85, 1.15)
            canvas = cv2.convertScaleAbs(canvas, alpha=gain, beta=np.random.uniform(-10, 10))
            label = 0

        tensor_img = torch.from_numpy(canvas).permute(2, 0, 1).float() / 255.0
        return tensor_img, label


# -----------------------------------------------------------------------------
# 2. Architectures & Loss Functions
# -----------------------------------------------------------------------------
class ArcMarginProduct(nn.Module):
    def __init__(self, in_features: int, out_features: int, s: float = 30.0, m: float = 0.35):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)

        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = math.cos(math.pi - m)
        self.mm = math.sin(math.pi - m) * m

    def forward(self, input: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
        cosine = F.linear(F.normalize(input), F.normalize(self.weight))
        sine = torch.sqrt(torch.clamp(1.0 - torch.pow(cosine, 2), 1e-7, 1.0))
        phi = cosine * self.cos_m - sine * self.sin_m
        phi = torch.where(cosine > self.th, phi, cosine - self.mm)

        one_hot = torch.zeros(cosine.size(), device=input.device)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1.0)
        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s
        return output


class FaceRecognitionNet_SFace(nn.Module):
    def __init__(self, embedding_dim: int = 128):
        super().__init__()
        def conv_block(in_c, out_c, stride=1):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, 3, stride, 1, bias=False),
                nn.BatchNorm2d(out_c),
                nn.PReLU(out_c)
            )
        self.features = nn.Sequential(
            conv_block(3, 32, stride=2),
            conv_block(32, 64, stride=2),
            conv_block(64, 128, stride=2),
            conv_block(128, 256, stride=2),
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, embedding_dim, bias=False)
        self.bn = nn.BatchNorm1d(embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        pooled = self.pool(feat).flatten(1)
        emb = self.bn(self.fc(pooled))
        return F.normalize(emb, p=2, dim=1)


class LowRankLinearAttention(nn.Module):
    def __init__(self, dim, rank=16):
        super().__init__()
        self.proj_q = nn.Conv2d(dim, rank, 1, bias=False)
        self.proj_k = nn.Conv2d(dim, rank, 1, bias=False)
        self.proj_v = nn.Conv2d(dim, dim, 1, bias=False)
        self.out_proj = nn.Conv2d(dim, dim, 1, bias=False)
        self.norm = nn.BatchNorm2d(dim)

    def forward(self, x):
        B, C, H, W = x.shape
        q = self.proj_q(x).view(B, -1, H * W)
        k = self.proj_k(x).view(B, -1, H * W)
        v = self.proj_v(x).view(B, C, H * W)
        attn = torch.softmax(torch.bmm(q.transpose(1, 2), k) / math.sqrt(q.size(1)), dim=-1)
        out = torch.bmm(v, attn).view(B, C, H, W)
        return self.norm(x + self.out_proj(out))


class EdgeFaceNet(nn.Module):
    def __init__(self, embedding_dim: int = 512):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 48, 3, 2, 1, bias=False),
            nn.BatchNorm2d(48),
            nn.Hardswish()
        )
        self.stage1 = nn.Sequential(
            nn.Conv2d(48, 48, 3, 1, 1, groups=48, bias=False),
            nn.BatchNorm2d(48),
            nn.Hardswish(),
            nn.Conv2d(48, 96, 1, bias=False),
            nn.BatchNorm2d(96)
        )
        self.stage2 = nn.Sequential(
            nn.Conv2d(96, 96, 3, 2, 1, groups=96, bias=False),
            nn.BatchNorm2d(96),
            nn.Hardswish(),
            nn.Conv2d(96, 192, 1, bias=False),
            nn.BatchNorm2d(192)
        )
        self.attn = LowRankLinearAttention(192, rank=16)
        self.stage3 = nn.Sequential(
            nn.Conv2d(192, 192, 3, 2, 1, groups=192, bias=False),
            nn.BatchNorm2d(192),
            nn.Hardswish(),
            nn.Conv2d(192, 384, 1, bias=False),
            nn.BatchNorm2d(384)
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(384, embedding_dim, bias=False)
        self.bn = nn.BatchNorm1d(embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.attn(x)
        x = self.stage3(x)
        pooled = self.pool(x).flatten(1)
        emb = self.bn(self.fc(pooled))
        return F.normalize(emb, p=2, dim=1)


class GhostModule(nn.Module):
    def __init__(self, in_c, out_c, ratio=2, dw_size=3):
        super().__init__()
        self.out_c = out_c
        init_c = math.ceil(out_c / ratio)
        new_c = init_c * (ratio - 1)
        self.primary_conv = nn.Sequential(
            nn.Conv2d(in_c, init_c, 1, 1, 0, bias=False),
            nn.BatchNorm2d(init_c),
            nn.ReLU(inplace=True)
        )
        self.cheap_operation = nn.Sequential(
            nn.Conv2d(init_c, new_c, dw_size, 1, dw_size // 2, groups=init_c, bias=False),
            nn.BatchNorm2d(new_c),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x1 = self.primary_conv(x)
        x2 = self.cheap_operation(x1)
        out = torch.cat([x1, x2], dim=1)
        return out[:, :self.out_c, :, :]


class GhostFaceNet(nn.Module):
    def __init__(self, embedding_dim: int = 128):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 16, 3, 2, 1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True)
        )
        self.blocks = nn.Sequential(
            GhostModule(16, 24),
            nn.MaxPool2d(2),
            GhostModule(24, 40),
            nn.MaxPool2d(2),
            GhostModule(40, 80),
            nn.MaxPool2d(2),
            GhostModule(80, 160),
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(160, embedding_dim, bias=False)
        self.bn = nn.BatchNorm1d(embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.blocks(x)
        pooled = self.pool(x).flatten(1)
        emb = self.bn(self.fc(pooled))
        return F.normalize(emb, p=2, dim=1)


class MiniFASNetV2(nn.Module):
    def __init__(self, num_classes: int = 2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1, bias=False),
            nn.BatchNorm2d(32),
            nn.PReLU(32),
            nn.Conv2d(32, 64, 3, 2, 1, groups=32, bias=False),
            nn.BatchNorm2d(64),
            nn.PReLU(64),
            nn.Conv2d(64, 128, 3, 2, 1, groups=64, bias=False),
            nn.BatchNorm2d(128),
            nn.PReLU(128),
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        pooled = self.pool(feat).flatten(1)
        return self.classifier(pooled)


# -----------------------------------------------------------------------------
# 3. Main Training Execution
# -----------------------------------------------------------------------------
def run_training(model_target: str = "ALL", total_steps: int = 5000, batch_size: int = 64, lr: float = 1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_count = torch.cuda.device_count()
    print("=" * 78)
    print(f"KUCET K² FRS - BLUEPRINT MODEL TRAINING RUNNER")
    print(f"Target Device: {device} (Count: {gpu_count}) | Target: {model_target}")
    print("=" * 78)

    output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_ds = ClassroomFaceDataset(num_identities=50, samples_per_id=150, is_train=True)
    val_ds = ClassroomFaceDataset(num_identities=50, samples_per_id=25, is_train=False)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    pad_train_ds = AntiSpoofingDataset(num_samples=4000, is_train=True)
    pad_val_ds = AntiSpoofingDataset(num_samples=1000, is_train=False)
    pad_train_loader = DataLoader(pad_train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    pad_val_loader = DataLoader(pad_val_ds, batch_size=batch_size, shuffle=False)

    targets = ["sface", "edgeface", "ghostfacenet", "minifasnet"] if model_target == "ALL" else [model_target]

    for m_key in targets:
        print(f"\n---> Training model: {m_key.upper()}")
        if m_key == "sface":
            net = FaceRecognitionNet_SFace(128).to(device)
            head = ArcMarginProduct(128, 50).to(device)
            is_pad = False
            t_loader = train_loader
            v_loader = val_loader
            in_shape = (1, 3, 112, 112)
            onnx_name = "kucet_frs_sface_finetuned.onnx"
            pt_name = "kucet_frs_sface_weights.pt"
            emb_dim = 128
        elif m_key == "edgeface":
            net = EdgeFaceNet(512).to(device)
            head = ArcMarginProduct(512, 50).to(device)
            is_pad = False
            t_loader = train_loader
            v_loader = val_loader
            in_shape = (1, 3, 112, 112)
            onnx_name = "kucet_frs_edgeface_finetuned.onnx"
            pt_name = "kucet_frs_edgeface_weights.pt"
            emb_dim = 512
        elif m_key == "ghostfacenet":
            net = GhostFaceNet(128).to(device)
            head = ArcMarginProduct(128, 50).to(device)
            is_pad = False
            t_loader = train_loader
            v_loader = val_loader
            in_shape = (1, 3, 112, 112)
            onnx_name = "kucet_frs_ghostfacenet_finetuned.onnx"
            pt_name = "kucet_frs_ghostfacenet_weights.pt"
            emb_dim = 128
        elif m_key == "minifasnet":
            net = MiniFASNetV2(2).to(device)
            head = None
            is_pad = True
            t_loader = pad_train_loader
            v_loader = pad_val_loader
            in_shape = (1, 3, 80, 80)
            onnx_name = "kucet_frs_minifasnet_finetuned.onnx"
            pt_name = "kucet_frs_minifasnet_weights.pt"
            emb_dim = 2

        params = list(net.parameters()) + (list(head.parameters()) if head else [])
        optimizer = torch.optim.AdamW(params, lr=lr)
        criterion = nn.CrossEntropyLoss()

        step = 0
        t_iter = iter(t_loader)
        pbar = tqdm(total=total_steps, desc=f"Training {m_key}")

        while step < total_steps:
            net.train()
            if head: head.train()
            try:
                images, labels = next(t_iter)
            except StopIteration:
                t_iter = iter(t_loader)
                images, labels = next(t_iter)

            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            if is_pad:
                loss = criterion(net(images), labels)
            else:
                loss = criterion(head(net(images), labels), labels)

            loss.backward()
            optimizer.step()
            step += 1
            pbar.update(1)

        pbar.close()

        # Save weights and ONNX
        net.eval()
        torch.save(net.state_dict(), output_dir / pt_name)
        print(f"[OK] Saved PyTorch weights to {pt_name}")
        dummy_input = torch.randn(*in_shape, device=device)
        output_name = ["output"] if is_pad else ["embedding"]
        try:
            try:
                torch.onnx.export(
                    net, dummy_input, str(output_dir / onnx_name),
                    input_names=["input"], output_names=output_name,
                    dynamic_axes={"input": {0: "batch_size"}, output_name[0]: {0: "batch_size"}},
                    opset_version=14, do_constant_folding=True, dynamo=False
                )
            except TypeError:
                torch.onnx.export(
                    net, dummy_input, str(output_dir / onnx_name),
                    input_names=["input"], output_names=output_name,
                    dynamic_axes={"input": {0: "batch_size"}, output_name[0]: {0: "batch_size"}},
                    opset_version=14, do_constant_folding=True
                )
            print(f"[OK] Exported {onnx_name}")
        except Exception as e:
            print(f"[Notice] ONNX export requires onnx and onnxscript packages ({e}). Weights saved as {pt_name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="K² FRS Model Fine-Tuning Script")
    parser.add_argument("--model", type=str, default="ALL", choices=["ALL", "sface", "edgeface", "ghostfacenet", "minifasnet"])
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    run_training(model_target=args.model, total_steps=args.steps, batch_size=args.batch_size, lr=args.lr)
