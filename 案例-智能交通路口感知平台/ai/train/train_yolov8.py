#!/usr/bin/env python3
"""
YOLOv8 交通目标检测模型训练脚本
目标：在路口监控数据集上微调 YOLOv8s，优化小目标检测

用法：
    python train_yolov8.py [--resume] [--epochs N] [--batch B]
    python train_yolov8.py --mode export   # 仅导出 ONNX
"""

import argparse
import os
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--mode',    default='train', choices=['train', 'val', 'export'])
    p.add_argument('--model',   default='yolov8s.pt',  help='预训练权重或已训练模型')
    p.add_argument('--data',    default='traffic_intersection.yaml')
    p.add_argument('--epochs',  type=int, default=300)
    p.add_argument('--batch',   type=int, default=16)
    p.add_argument('--imgsz',   type=int, default=640)
    p.add_argument('--device',  default='0',    help='GPU: "0" or "0,1" or "cpu"')
    p.add_argument('--project', default='runs/traffic')
    p.add_argument('--name',    default='yolov8s_traffic_v1')
    p.add_argument('--resume',  action='store_true', help='从上次中断处恢复')
    return p.parse_args()

def train(args):
    from ultralytics import YOLO

    model = YOLO(args.model)

    # ── 训练超参数（针对路口场景优化）────────────────────────
    results = model.train(
        data    = args.data,
        epochs  = args.epochs,
        batch   = args.batch,
        imgsz   = args.imgsz,
        device  = args.device,
        project = args.project,
        name    = args.name,
        resume  = args.resume,
        workers = 8,

        # 优化器
        optimizer = 'AdamW',
        lr0       = 0.001,
        lrf       = 0.01,      # 最终学习率 = lr0 * lrf
        momentum  = 0.937,
        weight_decay = 0.0005,
        warmup_epochs = 3,

        # 数据增强（路口场景特化）
        hsv_h = 0.015,         # 色相扰动（模拟不同时间/天气）
        hsv_s = 0.7,
        hsv_v = 0.4,
        flipud = 0.0,          # 不垂直翻转（路口有方向性）
        fliplr = 0.5,          # 水平翻转可以（对称路口）
        mosaic = 1.0,          # Mosaic 增强（提升小目标检测）
        mixup  = 0.15,         # Mixup（减少过拟合）
        copy_paste = 0.1,      # Copy-paste（增加密集场景样本）
        close_mosaic = 15,     # 最后 15 epoch 关闭 mosaic 稳定收敛

        # 小目标优化
        multi_scale = True,    # 多尺度训练（0.5x ~ 1.5x）
        overlap_mask = True,

        # 保存策略
        save_period = 20,      # 每 20 epoch 保存一次检查点
        val         = True,
        plots       = True,    # 保存训练曲线

        # 硬件
        amp  = True,           # 自动混合精度（节省显存，加快训练）
        half = False,          # 训练用 FP32
    )

    print(f"\n训练完成！")
    print(f"最佳 mAP50:    {results.results_dict.get('metrics/mAP50(B)', 'N/A'):.3f}")
    print(f"最佳 mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A'):.3f}")
    print(f"最佳模型路径:  {args.project}/{args.name}/weights/best.pt")
    return results

def validate(args):
    from ultralytics import YOLO

    model = YOLO(args.model)
    metrics = model.val(data=args.data, device=args.device, imgsz=args.imgsz)

    print("\n=== 验证结果 ===")
    print(f"mAP50:    {metrics.box.map50:.3f}")
    print(f"mAP50-95: {metrics.box.map:.3f}")
    print("\n各类别 AP50:")
    for cls_name, ap in zip(metrics.names.values(), metrics.box.ap50):
        print(f"  {cls_name:<12}: {ap:.3f}")

def export_onnx(args):
    from ultralytics import YOLO

    model = YOLO(args.model)
    # 导出 ONNX（Vitis AI 量化的标准输入格式）
    out = model.export(
        format    = 'onnx',
        imgsz     = args.imgsz,
        opset     = 13,         # Vitis AI 要求 opset 11~13
        simplify  = True,       # onnx-simplifier 简化图
        dynamic   = False,      # 固定 batch size=1（DPU 推理）
        half      = False,      # FP32 导出（量化工具处理）
    )
    print(f"\nONNX 模型已导出: {out}")
    print("下一步：运行 ai/quantization/ptq_quantize.py 进行量化")

if __name__ == '__main__':
    args = parse_args()
    os.makedirs(args.project, exist_ok=True)

    if args.mode == 'train':
        train(args)
    elif args.mode == 'val':
        validate(args)
    elif args.mode == 'export':
        export_onnx(args)
