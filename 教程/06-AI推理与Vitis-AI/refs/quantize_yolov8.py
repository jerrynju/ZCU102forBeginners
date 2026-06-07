"""
YOLOv8s PTQ INT8 量化脚本
参考：Vitis-AI-Tutorials/Tutorials/RESNET18/ (branch 3.5)
      Vitis-AI-Tutorials/Tutorials/PyTorch-ResNet18/ (branch 3.5)
工具版本：Vitis AI 3.5 / PyTorch 1.13.1

使用方法（在 Vitis AI Docker 中运行）：
  docker run -it --gpus all -v $(pwd):/workspace xilinx/vitis-ai-gpu:latest
  conda activate vitis-ai-pytorch
  python3 quantize_yolov8.py --model yolov8s.pt --data coco.yaml --calib 200
"""

import os
import sys
import argparse
import torch
import torch.nn as nn
from pathlib import Path

# ── 参数解析 ──────────────────────────────────────────────
parser = argparse.ArgumentParser(description='YOLOv8 Vitis AI PTQ 量化')
parser.add_argument('--model',  type=str, default='yolov8s.pt', help='PyTorch 模型路径')
parser.add_argument('--data',   type=str, default='coco.yaml',   help='数据集配置')
parser.add_argument('--calib',  type=int, default=200,            help='校准图像数量')
parser.add_argument('--output', type=str, default='./quantized',  help='输出目录')
parser.add_argument('--device', type=str, default='cuda',         help='cuda 或 cpu')
args = parser.parse_args()

device = torch.device(args.device if torch.cuda.is_available() else 'cpu')

# ── 步骤 1：替换不支持的激活函数（SiLU → ReLU6）────────────
print("[1/4] 替换 SiLU 激活函数为 ReLU6（DPU 不支持 SiLU）...")

def replace_activation(module: nn.Module, src_type, dst_fn):
    """递归替换激活函数"""
    for name, child in module.named_children():
        if isinstance(child, src_type):
            setattr(module, name, dst_fn())
        else:
            replace_activation(child, src_type, dst_fn)

try:
    from ultralytics import YOLO
    yolo = YOLO(args.model)
    model = yolo.model
    replace_activation(model, nn.SiLU, lambda: nn.ReLU6(inplace=True))
    model = model.to(device).eval()
    print(f"   ✓ 模型加载成功，SiLU 已替换为 ReLU6")
except ImportError:
    print("   ! 需要安装 ultralytics: pip install ultralytics")
    sys.exit(1)

# ── 步骤 2：创建量化器 ────────────────────────────────────
print("[2/4] 初始化 pytorch_nndct 量化器（校准模式）...")
try:
    from pytorch_nndct.apis import torch_quantizer

    dummy_input = torch.randn(1, 3, 640, 640).to(device)
    quantizer = torch_quantizer(
        quant_mode='calib',
        module=model,
        input_args=dummy_input,
        device=device,
        quant_config_file=None,
    )
    quant_model = quantizer.quant_model
    print("   ✓ 量化器创建成功")
except ImportError:
    print("   ! 需要在 Vitis AI Docker 中运行（conda activate vitis-ai-pytorch）")
    sys.exit(1)

# ── 步骤 3：校准（前向传播校准数据集）────────────────────
print(f"[3/4] 校准（{args.calib} 张图像）...")
import cv2
import numpy as np
from torch.utils.data import DataLoader, Dataset

class CalibDataset(Dataset):
    def __init__(self, img_dir, n_images=200, img_size=640):
        self.files = sorted(Path(img_dir).glob('*.jpg'))[:n_images]
        self.img_size = img_size

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        img = cv2.imread(str(self.files[idx]))
        img = cv2.resize(img, (self.img_size, self.img_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        # 标准化（COCO 均值/方差）
        mean = np.array([0.485, 0.456, 0.406])
        std  = np.array([0.229, 0.224, 0.225])
        img  = (img - mean) / std
        return torch.from_numpy(img.transpose(2, 0, 1)).float()

# 从环境变量或默认路径读取校准数据集
calib_dir = os.environ.get('CALIB_DATA', '/workspace/calib_data')
if not os.path.exists(calib_dir):
    print(f"   ! 校准数据集目录不存在: {calib_dir}")
    print(f"     设置环境变量 CALIB_DATA=<路径> 或创建 {calib_dir}")
    print(f"     跳过校准，直接导出（量化精度可能降低）")
else:
    calib_ds     = CalibDataset(calib_dir, n_images=args.calib)
    calib_loader = DataLoader(calib_ds, batch_size=8, num_workers=4, pin_memory=True)

    quant_model.eval()
    with torch.no_grad():
        for i, imgs in enumerate(calib_loader):
            imgs = imgs.to(device)
            _ = quant_model(imgs)
            if (i + 1) % 5 == 0:
                print(f"   校准进度: {(i+1)*8}/{args.calib}")

    print("   ✓ 校准完成")

# 导出量化配置
os.makedirs(args.output, exist_ok=True)
quantizer.export_quant_config()

# ── 步骤 4：导出 xmodel ───────────────────────────────────
print("[4/4] 导出 xmodel（测试模式）...")
quantizer_test = torch_quantizer(
    quant_mode='test',
    module=model,
    input_args=dummy_input,
    device=device,
    quant_config_file='quant_info.json',
    output_dir=args.output,
)
quant_model_test = quantizer_test.quant_model

# 运行一次前向，触发 xmodel 生成
with torch.no_grad():
    _ = quant_model_test(dummy_input)

quantizer_test.export_xmodel(
    output_dir=args.output,
    deploy_check=True,
)

print(f"\n✓ 量化完成！输出文件:")
print(f"  {args.output}/YoloV8s_int.xmodel  (float xmodel)")
print(f"  {args.output}/quant_info.json      (量化配置)")
print(f"\n下一步：使用 vai_c_xir 编译为 DPU 指令：")
print(f"  vai_c_xir \\")
print(f"    --xmodel {args.output}/YoloV8s_int.xmodel \\")
print(f"    --arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \\")
print(f"    --net_name yolov8s_traffic \\")
print(f"    --output_dir ./compiled/")
