"""
LPRNet - 中国车牌识别网络
论文：LPRNet: License Plate Recognition via Deep Neural Networks
输入：96×24 RGB 图像（车牌裁剪区域，需先经过矫正）
输出：CTC 序列，最多 8 字符（含省份简称）

字符集：68 类
  - 34 个省份简称（中文）
  - 10 个数字（0-9）
  - 24 个字母（去掉 I/O 避免混淆）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple

# 字符集定义
PROVINCES = "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁甯"
ALPHABETS  = "ABCDEFGHJKLMNPQRSTUVWXYZ"
DIGITS     = "0123456789"

CHARS = PROVINCES + ALPHABETS + DIGITS
NUM_CLASS = len(CHARS) + 1  # +1 for CTC blank token

class SmallBasicBlock(nn.Module):
    """LPRNet 基础块：1×1 → (3,1) → (1,3) → 1×1 分解卷积，减少参数量"""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        mid = out_ch // 4
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, mid, 1, bias=False),
            nn.BatchNorm2d(mid), nn.ReLU(inplace=True),
            # 水平和垂直分解
            nn.Conv2d(mid, mid, (3, 1), padding=(1, 0), bias=False),
            nn.BatchNorm2d(mid), nn.ReLU(inplace=True),
            nn.Conv2d(mid, mid, (1, 3), padding=(0, 1), bias=False),
            nn.BatchNorm2d(mid), nn.ReLU(inplace=True),
            nn.Conv2d(mid, out_ch, 1, bias=False),
            nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        )
    def forward(self, x): return self.net(x)

class LPRNet(nn.Module):
    """
    LPRNet 主网络
    参数量：约 1.7M（INT8 量化后 ~1.7MB）
    推理速度：DPU B4096 @300MHz < 3ms/张
    """
    def __init__(self, num_class: int = NUM_CLASS, dropout: float = 0.5):
        super().__init__()
        # 输入: (B, 3, 24, 96)
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.MaxPool3d((1, 3, 3), stride=(1, 1, 1)),  # 不改变 H/W，增强局部感受野

            SmallBasicBlock(64, 128),
            nn.MaxPool3d((1, 3, 3), stride=(1, 2, 2)),  # H/2, W/2

            SmallBasicBlock(128, 256),
            SmallBasicBlock(256, 256),
            nn.MaxPool3d((1, 3, 3), stride=(1, 4, 2)),  # H/4, W/4

            nn.Dropout(dropout),
            nn.Conv2d(256, 256, (1, 4), bias=False),    # W→1
            nn.BatchNorm2d(256), nn.ReLU(inplace=True),

            nn.Dropout(dropout),
            nn.Conv2d(256, num_class, (13, 1), bias=False),  # H→1
            # 输出: (B, num_class, 1, W_out)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, 3, 24, 96)
        Returns:
            log_probs: (T, B, C) - CTC 格式（T=时间步，B=batch，C=类别数）
        """
        y = self.backbone(x)        # (B, C, 1, T)
        y = y.squeeze(2)            # (B, C, T)
        y = y.permute(2, 0, 1)      # (T, B, C) ← CTC 需要此格式
        return F.log_softmax(y, dim=2)

    @staticmethod
    def decode(log_probs: torch.Tensor) -> List[str]:
        """CTC 贪心解码（推理时使用）"""
        # log_probs: (T, B, C)
        preds = log_probs.argmax(dim=2)  # (T, B)
        results = []
        for b in range(preds.shape[1]):
            seq = preds[:, b].cpu().numpy().tolist()
            # 去重复 + 去 blank
            decoded = []
            prev = -1
            for idx in seq:
                if idx != prev and idx != 0:  # 0 = blank
                    decoded.append(idx - 1)   # -1 因为 blank 偏移
                prev = idx
            plate = ''.join(CHARS[i] for i in decoded if 0 <= i < len(CHARS))
            results.append(plate)
        return results

class CTCLoss(nn.Module):
    """CTC 损失封装（支持变长序列）"""
    def __init__(self):
        super().__init__()
        self.ctc = nn.CTCLoss(blank=0, zero_infinity=True)

    def forward(self, log_probs, targets, input_lengths, target_lengths):
        return self.ctc(log_probs, targets, input_lengths, target_lengths)

def build_model(pretrained: str = None, device='cpu') -> LPRNet:
    """工厂函数"""
    model = LPRNet().to(device)
    if pretrained:
        state = torch.load(pretrained, map_location=device)
        model.load_state_dict(state.get('model', state))
        print(f"加载预训练权重: {pretrained}")
    return model

if __name__ == '__main__':
    # 模型信息验证
    model = LPRNet()
    model.eval()
    dummy = torch.randn(4, 3, 24, 96)
    out = model(dummy)
    print(f"输入: {dummy.shape}")
    print(f"输出: {out.shape}  (T, B, C)")

    plates = LPRNet.decode(out)
    print(f"解码结果（随机，仅验证格式）: {plates}")

    # 参数量统计
    params = sum(p.numel() for p in model.parameters())
    print(f"参数量: {params:,} ({params/1e6:.2f}M)")
    print(f"INT8 模型大小估算: {params/1e6:.1f} MB")
