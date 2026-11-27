"""
K² FRS — Option 1 (SCRFD-500M-KPS + ArcFace MobileFaceNet 512-D) Adapters.
Encapsulates high-speed ONNX inference for SCRFD-500M-KPS face detection
and ArcFace MobileFaceNet 512-D embedding extraction with 5-landmark affine alignment.
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import onnxruntime as ort

REFERENCE_5_PTS = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def nms(boxes: np.ndarray, scores: np.ndarray, iou_thresh: float = 0.45) -> List[int]:
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]
    return keep


class SCRFD500MDetector:
    MODEL_HASH = "010375cf3981881ff1f8857fe05d15ba40989c049924559286eb7ebaf5309395"
    DEFAULT_FILENAME = "scrfd_500m_kps.onnx"

    def __init__(self, model_path: Optional[str] = None, num_threads: int = 2):
        self.model_path = self._resolve_path(model_path)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(str(self.model_path), opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]
        self.strides = [8, 16, 32]

        if len(self.output_names) != 9:
            raise ValueError(f"SCRFD model {self.model_path} does not have 9 outputs! Got {len(self.output_names)}")

    def _resolve_path(self, explicit_path: Optional[str]) -> Path:
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.is_file():
                return p
        candidates = [
            Path("backend/models") / self.DEFAULT_FILENAME,
            Path("models") / self.DEFAULT_FILENAME,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / self.DEFAULT_FILENAME,
            Path("D:/K2-local-model-lab/weights") / self.DEFAULT_FILENAME,
        ]
        for c in candidates:
            r = c.resolve()
            if r.is_file():
                return r
        return Path("backend/models") / self.DEFAULT_FILENAME

    def _generate_anchors(self, height: int, width: int) -> List[np.ndarray]:
        anchors = []
        for s in self.strides:
            fh = height // s
            fw = width // s
            sx = np.arange(0, fw) * s
            sy = np.arange(0, fh) * s
            sxx, syy = np.meshgrid(sx, sy)
            grid = np.stack([sxx.reshape(-1), syy.reshape(-1)], axis=-1)
            grid = np.repeat(grid, 2, axis=0)
            anchors.append(grid)
        return anchors

    def detect(
        self, img_bgr: np.ndarray, target_size: int = 640, score_thresh: float = 0.35, iou_thresh: float = 0.45
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        t0 = time.perf_counter()
        orig_h, orig_w = img_bgr.shape[:2]
        ratio = target_size / max(orig_h, orig_w)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)

        resized = cv2.resize(img_bgr, (new_w, new_h))
        pad_img = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        pad_img[:new_h, :new_w, :] = resized

        blob = cv2.dnn.blobFromImage(pad_img, 1.0 / 128.0, (target_size, target_size), (127.5, 127.5, 127.5), swapRB=True)
        t_onnx_start = time.perf_counter()
        outs = self.session.run(self.output_names, {self.input_name: blob})
        t_onnx = (time.perf_counter() - t_onnx_start) * 1000.0

        scores_list = outs[0:3]
        boxes_list = outs[3:6]
        kps_list = outs[6:9]

        anchors_list = self._generate_anchors(target_size, target_size)

        all_boxes = []
        all_scores = []
        all_kps = []

        for stride, scores, bboxes, kpss, anchors in zip(self.strides, scores_list, boxes_list, kps_list, anchors_list):
            scores = scores.reshape(-1)
            valid = scores >= score_thresh
            if not np.any(valid):
                continue
            v_scores = scores[valid]
            v_bboxes = bboxes[valid]
            v_kpss = kpss[valid]
            v_anchors = anchors[valid]

            x1 = v_anchors[:, 0] - v_bboxes[:, 0] * stride
            y1 = v_anchors[:, 1] - v_bboxes[:, 1] * stride
            x2 = v_anchors[:, 0] + v_bboxes[:, 2] * stride
            y2 = v_anchors[:, 1] + v_bboxes[:, 3] * stride
            boxes = np.stack([x1, y1, x2, y2], axis=-1)

            kps = v_kpss.reshape(-1, 5, 2) * stride + v_anchors[:, None, :]

            boxes[:, 0] /= ratio
            boxes[:, 1] /= ratio
            boxes[:, 2] /= ratio
            boxes[:, 3] /= ratio
            kps[:, :, 0] /= ratio
            kps[:, :, 1] /= ratio

            all_boxes.append(boxes)
            all_scores.append(v_scores)
            all_kps.append(kps)

        if not all_boxes:
            return np.empty((0, 4)), np.empty((0,)), np.empty((0, 5, 2)), t_onnx

        all_boxes = np.concatenate(all_boxes, axis=0)
        all_scores = np.concatenate(all_scores, axis=0)
        all_kps = np.concatenate(all_kps, axis=0)

        keep = nms(all_boxes, all_scores, iou_thresh=iou_thresh)
        return all_boxes[keep], all_scores[keep], all_kps[keep], t_onnx


class ArcFaceMobileNetRecognizer:
    MODEL_HASH = "9cc6e4a75f0e2bf0b1aed94578f144d15175f357bdc05e815e5c4a02b319eb4f"
    DEFAULT_FILENAME = "mobilefacenet_w600k.onnx"
    DIMENSION = 512

    def __init__(self, model_path: Optional[str] = None, num_threads: int = 2):
        self.model_path = self._resolve_path(model_path)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(str(self.model_path), opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def _resolve_path(self, explicit_path: Optional[str]) -> Path:
        if explicit_path:
            p = Path(explicit_path).resolve()
            if p.is_file():
                return p
        candidates = [
            Path("backend/models") / self.DEFAULT_FILENAME,
            Path("models") / self.DEFAULT_FILENAME,
            Path(__file__).resolve().parent.parent.parent.parent / "models" / self.DEFAULT_FILENAME,
            Path("D:/K2-local-model-lab/weights") / self.DEFAULT_FILENAME,
        ]
        for c in candidates:
            r = c.resolve()
            if r.is_file():
                return r
        return Path("backend/models") / self.DEFAULT_FILENAME

    def align_and_extract(
        self, img_bgr: np.ndarray, kps_5: np.ndarray, bbox: Optional[np.ndarray] = None, score: float = 1.0
    ) -> np.ndarray:
        M, _ = cv2.estimateAffinePartial2D(kps_5, REFERENCE_5_PTS, method=cv2.LMEDS)
        if M is None:
            x1 = max(0, int(np.min(kps_5[:, 0])))
            y1 = max(0, int(np.min(kps_5[:, 1])))
            x2 = min(img_bgr.shape[1], int(np.max(kps_5[:, 0])))
            y2 = min(img_bgr.shape[0], int(np.max(kps_5[:, 1])))
            crop = img_bgr[y1:y2, x1:x2]
            aligned = cv2.resize(crop, (112, 112))
        else:
            aligned = cv2.warpAffine(img_bgr, M, (112, 112), borderValue=0.0)

        blob = cv2.dnn.blobFromImage(aligned, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        feat = self.session.run([self.output_name], {self.input_name: blob})[0].reshape(-1)
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm
        return feat
