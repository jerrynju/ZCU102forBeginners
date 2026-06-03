"""
模拟检测器（Mock Detector）
在没有真实 DPU 和 xmodel 时，基于场景生成器的 Ground Truth 返回"伪检测结果"
模拟现实中的检测误差：漏检、误检、定位偏差

同时支持 ONNX Runtime 模式（若提供模型文件则使用真实推理）
"""

import time
import random
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    class_id:   int
    class_name: str
    confidence: float
    x1: int; y1: int; x2: int; y2: int
    track_id:   int = -1
    plate:      str = ''


class_names = ['car', 'truck', 'bus', 'motorbike', 'person']


class MockDetector:
    """
    基于 GT 的模拟检测器
    用于在无 DPU 环境下验证下游逻辑（跟踪、事件检测、MQTT上报）

    模拟参数：
      recall:    检出率（默认 0.92）
      precision: 精确率（默认 0.90，误检率=1-precision）
      pos_noise: 定位噪声标准差（像素）
    """
    def __init__(self, recall: float = 0.92, precision: float = 0.90,
                 pos_noise: float = 3.0, seed: int = 0):
        self.recall    = recall
        self.precision = precision
        self.pos_noise = pos_noise
        random.seed(seed)
        np.random.seed(seed)
        self._latency_ms = 5.0  # 模拟推理延迟

    def detect(self, frame_bgr: np.ndarray,
               gt_boxes: list) -> Tuple[List[Detection], float]:
        """
        Args:
            frame_bgr: H×W×3 BGR 图像（本模拟不实际使用）
            gt_boxes:  场景生成器输出的 GroundTruth 列表

        Returns:
            detections: Detection 列表
            latency_ms: 模拟推理延迟
        """
        t0 = time.monotonic()
        detections = []

        for gt in gt_boxes:
            # 模拟漏检
            if random.random() > self.recall:
                continue
            # 定位噪声
            noise = np.random.normal(0, self.pos_noise, 4)
            x1 = max(0, int(gt.x1 + noise[0]))
            y1 = max(0, int(gt.y1 + noise[1]))
            x2 = max(x1 + 5, int(gt.x2 + noise[2]))
            y2 = max(y1 + 5, int(gt.y2 + noise[3]))
            conf = random.uniform(0.72, 0.97)
            detections.append(Detection(
                class_id   = class_names.index(gt.cls) if gt.cls in class_names else 0,
                class_name = gt.cls,
                confidence = conf,
                x1=x1, y1=y1, x2=x2, y2=y2,
            ))

        # 模拟误检（随机添加假目标）
        fp_count = np.random.poisson(len(gt_boxes) * (1 - self.precision) * 0.5)
        H, W = frame_bgr.shape[:2]
        for _ in range(int(fp_count)):
            cls = random.choice(class_names)
            x1  = random.randint(0, W - 30)
            y1  = random.randint(0, H - 30)
            w   = random.randint(15, 50)
            h   = random.randint(20, 70)
            detections.append(Detection(
                class_id   = class_names.index(cls),
                class_name = cls,
                confidence = random.uniform(0.35, 0.55),  # 误检通常置信度较低
                x1=x1, y1=y1, x2=min(W-1, x1+w), y2=min(H-1, y1+h),
            ))

        # 模拟延迟
        elapsed = (time.monotonic() - t0) * 1000
        target  = self._latency_ms + random.gauss(0, 0.5)
        if target > elapsed:
            time.sleep((target - elapsed) / 1000.0)

        return detections, target


class OnnxDetector:
    """
    真实 ONNX Runtime 检测器（在有 onnxruntime 和模型文件时使用）
    接口与 MockDetector 一致，可无缝替换
    """
    def __init__(self, model_path: str, conf_thresh: float = 0.4,
                 input_size: Tuple[int, int] = (640, 640)):
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError("请安装 onnxruntime: pip install onnxruntime")

        self.conf_thresh = conf_thresh
        self.input_size  = input_size

        providers = ['CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name  = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        logger.info(f"ONNX模型加载成功: {model_path}")

    def _preprocess(self, img_bgr: np.ndarray) -> np.ndarray:
        """Letterbox 缩放 + 归一化"""
        iH, iW = img_bgr.shape[:2]
        tH, tW = self.input_size
        scale = min(tW / iW, tH / iH)
        nW, nH = int(iW * scale), int(iH * scale)
        import cv2
        resized = cv2.resize(img_bgr, (nW, nH))
        padded  = np.full((tH, tW, 3), 114, dtype=np.uint8)
        padded[:nH, :nW] = resized
        tensor  = padded[:, :, ::-1].astype(np.float32) / 255.0  # BGR→RGB, /255
        tensor  = tensor.transpose(2, 0, 1)[np.newaxis]            # HWC→NCHW
        return tensor, scale, (iW, iH)

    def _postprocess(self, output: np.ndarray, scale: float,
                     orig_size: Tuple[int, int]) -> List[Detection]:
        """YOLOv8 输出解码（[1, 84, 8400] 格式）"""
        preds = output[0].T  # [8400, 84]
        detections = []
        orig_W, orig_H = orig_size
        tH, tW = self.input_size

        for pred in preds:
            confs = pred[4:]
            class_id = int(np.argmax(confs))
            conf = float(confs[class_id])
            if conf < self.conf_thresh:
                continue
            # xywh → xyxy（相对 input_size 的坐标）
            cx, cy, w, h = pred[:4]
            x1 = (cx - w / 2) / tW * orig_W / scale
            y1 = (cy - h / 2) / tH * orig_H / scale
            x2 = (cx + w / 2) / tW * orig_W / scale
            y2 = (cy + h / 2) / tH * orig_H / scale
            cls = class_names[class_id] if class_id < len(class_names) else 'unknown'
            detections.append(Detection(
                class_id=class_id, class_name=cls, confidence=conf,
                x1=max(0, int(x1)), y1=max(0, int(y1)),
                x2=min(orig_W - 1, int(x2)), y2=min(orig_H - 1, int(y2)),
            ))
        return detections

    def detect(self, frame_bgr: np.ndarray,
               gt_boxes: list = None) -> Tuple[List[Detection], float]:
        t0 = time.monotonic()
        tensor, scale, orig_size = self._preprocess(frame_bgr)
        outputs = self.session.run([self.output_name], {self.input_name: tensor})
        detections = self._postprocess(outputs[0], scale, orig_size)
        latency = (time.monotonic() - t0) * 1000
        return detections, latency


def create_detector(model_path: Optional[str] = None, **kwargs):
    """工厂函数：有模型文件用 ONNX，否则用 Mock"""
    if model_path:
        try:
            return OnnxDetector(model_path, **kwargs)
        except Exception as e:
            logger.warning(f"ONNX 加载失败 ({e})，回退到 MockDetector")
    return MockDetector(**kwargs)


if __name__ == '__main__':
    from scene_generator import SceneGenerator
    gen      = SceneGenerator(seed=42)
    detector = MockDetector()

    total_gt = 0; total_det = 0; tp = 0
    for _ in range(100):
        frame, gt = gen.next_frame()
        dets, lat = detector.detect(frame, gt)
        total_gt  += len(gt)
        total_det += len(dets)
        tp        += min(len(gt), len(dets))  # 简化估算

    recall_est = tp / max(total_gt, 1)
    prec_est   = tp / max(total_det, 1)
    print(f"MockDetector 统计（100帧）:")
    print(f"  总GT目标: {total_gt}, 总检测: {total_det}")
    print(f"  估算召回率: {recall_est:.2%} （目标≥{MockDetector().recall:.0%}）")
    print(f"  估算精确率: {prec_est:.2%}")
    print("✓ MockDetector 正常")
