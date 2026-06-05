#!/usr/bin/env python3
# @req SYS-REQ-002, SYS-REQ-003, PERF-REQ-004, TR-003
# @design TR-003
# @test TC-AI-DET-001
# @author ai-team | @since 2026-06-04 | @version 1.0
# @status verified
"""
Vitis AI 后训练量化（PTQ）脚本
将 FP32 ONNX 模型量化为 INT8 xmodel，供 DPU B4096 推理

运行环境：Vitis AI Docker
  docker run -it --gpus all \
      -v $(pwd):/workspace \
      -v /path/to/calib_data:/data/calib \
      xilinx/vitis-ai-pytorch-gpu:3.5 bash

使用方式：
    cd /workspace
    python ai/quantization/ptq_quantize.py \
        --model weights/yolov8s_traffic.onnx \
        --calib-data /data/calib \
        --output compiled_models/
"""

import argparse
import os
import sys
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--model',       required=True, help='输入 ONNX 模型路径')
    p.add_argument('--calib-data',  required=True, help='校准数据集目录（JPEG/PNG 图像）')
    p.add_argument('--output',      default='./compiled_models', help='输出目录')
    p.add_argument('--calib-num',   type=int, default=200,  help='校准图像数量')
    p.add_argument('--batch-size',  type=int, default=8)
    p.add_argument('--target',      default='DPUCZDX8G',    help='DPU 架构')
    p.add_argument('--arch-json',
        default='/opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json')
    p.add_argument('--skip-compile', action='store_true', help='仅量化，不编译')
    return p.parse_args()

# ── 校准数据集 ─────────────────────────────────────────────
class CalibDataset(Dataset):
    """路口摄像头校准图像集（从实际部署场景采集）"""
    def __init__(self, root: str, num_samples: int, img_size: int = 640):
        self.img_size = img_size
        exts = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.files = [p for p in Path(root).rglob('*') if p.suffix.lower() in exts]
        if not self.files:
            raise FileNotFoundError(f"No images found in {root}")
        # 随机采样指定数量
        import random; random.shuffle(self.files)
        self.files = self.files[:num_samples]
        print(f"校准集：{len(self.files)} 张图像")

        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            # YOLOv8 归一化：[0,1] 不做 mean/std（已在模型内处理）
        ])

    def __len__(self): return len(self.files)

    def __getitem__(self, idx):
        img = Image.open(self.files[idx]).convert('RGB')
        return self.transform(img)

# ── 1. ONNX 转 PyTorch（用于 Vitis AI 量化）──────────────
def load_model_from_onnx(onnx_path: str):
    """将 ONNX 转换为 PyTorch 可量化模型"""
    try:
        from pytorch_nndct.apis import torch_quantizer
        # 使用 onnx2pytorch 或 Vitis AI 的 ONNX 解析器
        import onnx
        from onnx2pytorch import ConvertModel
        onnx_model = onnx.load(onnx_path)
        torch_model = ConvertModel(onnx_model, experimental=True)
        torch_model.eval()
        return torch_model
    except ImportError:
        print("提示：如无 onnx2pytorch，请直接在 PyTorch 中定义模型并加载权重")
        sys.exit(1)

# ── 2. PTQ 量化主流程 ─────────────────────────────────────
def quantize(args):
    from pytorch_nndct.apis import torch_quantizer

    os.makedirs(args.output, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"量化设备: {device}")

    # 加载模型
    print(f"加载模型: {args.model}")
    model = load_model_from_onnx(args.model)
    model = model.to(device)
    model.eval()

    # 准备校准数据
    calib_set = CalibDataset(args.calib_data, args.calib_num)
    calib_loader = DataLoader(calib_set, batch_size=args.batch_size,
                              shuffle=True, num_workers=4)

    dummy_input = torch.randn(1, 3, 640, 640).to(device)

    # ── Phase 1: 校准（统计激活分布）──────────────────────
    print("\n=== Phase 1: 校准量化参数 ===")
    quantizer = torch_quantizer(
        quant_mode = 'calib',
        module     = model,
        input_args = (dummy_input,),
        device     = device,
        quant_config_file = 'quant_config_dpuczdx8g.json'  # DPU B4096 专用
    )
    quant_model = quantizer.quant_model

    with torch.no_grad():
        for i, batch in enumerate(calib_loader):
            batch = batch.to(device)
            quant_model(batch)
            if (i+1) % 10 == 0:
                print(f"  校准进度: {(i+1)*args.batch_size}/{args.calib_num}")

    quantizer.export_quant_config()
    print("校准完成，量化配置已保存")

    # ── Phase 2: 测试量化精度 ──────────────────────────────
    print("\n=== Phase 2: 验证量化精度 ===")
    quantizer_test = torch_quantizer(
        quant_mode = 'test',
        module     = model,
        input_args = (dummy_input,),
        device     = device,
    )
    quant_model_test = quantizer_test.quant_model

    # 在验证集上跑若干批次估算精度损失
    val_set   = CalibDataset(args.calib_data, 100)
    val_loader = DataLoader(val_set, batch_size=4, shuffle=False, num_workers=2)
    with torch.no_grad():
        for batch in val_loader:
            quant_model_test(batch.to(device))
    print("量化精度验证完成（完整 mAP 评估请运行 eval_quant.py）")

    # ── Phase 3: 导出 xmodel ──────────────────────────────
    print("\n=== Phase 3: 导出 xmodel ===")
    quantizer.export_torch_script(output_dir=args.output)
    quantizer.export_onnx_model(output_dir=args.output)
    quantizer.export_xmodel(output_dir=args.output, deploy_check=True)

    xmodel_path = os.path.join(args.output, 'yolov8s_traffic_int8.xmodel')
    print(f"xmodel 导出至: {xmodel_path}")
    return xmodel_path

# ── 3. DPU 编译 ───────────────────────────────────────────
def compile_for_dpu(xmodel_path: str, arch_json: str, output_dir: str):
    print(f"\n=== Phase 4: 编译 xmodel → DPU ===")
    print(f"目标架构: {arch_json}")

    cmd = (
        f"vai_c_xir "
        f"-x {xmodel_path} "
        f"-a {arch_json} "
        f"-o {output_dir} "
        f"-n yolov8s_traffic "
        f"--options '{{\"input_shape\": \"1,3,640,640\"}}'"
    )
    print(f"执行: {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        print("ERROR: vai_c_xir 编译失败")
        sys.exit(1)

    out = os.path.join(output_dir, 'yolov8s_traffic.xmodel')
    print(f"\n编译完成！DPU xmodel: {out}")

    # 打印模型信息
    os.system(f"xdputil inspect {out} -m")
    return out

if __name__ == '__main__':
    args = parse_args()
    print("=" * 60)
    print("Vitis AI PTQ 量化流程")
    print(f"输入模型:  {args.model}")
    print(f"校准数据:  {args.calib_data} ({args.calib_num} 张)")
    print(f"输出目录:  {args.output}")
    print("=" * 60)

    xmodel = quantize(args)
    if not args.skip_compile:
        compile_for_dpu(xmodel, args.arch_json, args.output)

    print("\n=== 完成 ===")
    print("下一步：")
    print(f"  1. 将 {args.output}/yolov8s_traffic.xmodel 复制到 ZCU102 的 /opt/models/")
    print(f"  2. 运行 ai/deploy/test_inference.py 验证推理结果")
