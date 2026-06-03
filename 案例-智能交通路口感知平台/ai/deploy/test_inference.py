#!/usr/bin/env python3
"""
ZCU102 DPU 推理验证脚本（在 ARM Linux 上运行）
验证量化模型在 DPU 上的推理结果是否正确

用法（在 ZCU102 Linux 上）：
    python3 test_inference.py --image test.jpg [--model /opt/models/yolov8s_traffic.xmodel]
    python3 test_inference.py --benchmark      # 性能基准测试
    python3 test_inference.py --camera 0       # 实时摄像头测试
"""

import argparse
import time
import os
import sys
import json
import numpy as np

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--model',  default='/opt/models/yolov8s_traffic.xmodel')
    p.add_argument('--image',  default=None, help='测试图像路径')
    p.add_argument('--camera', type=int, default=None, help='摄像头通道号')
    p.add_argument('--benchmark', action='store_true', help='运行性能基准测试')
    p.add_argument('--num-frames', type=int, default=100, help='基准测试帧数')
    p.add_argument('--save-result', action='store_true')
    return p.parse_args()

CLASS_NAMES = ['car', 'truck', 'bus', 'person', 'motorcycle', 'bicycle']
CLASS_COLORS_BGR = [
    (0, 0, 255),    # car:        红
    (0, 255, 0),    # truck:      绿
    (255, 0, 0),    # bus:        蓝
    (0, 255, 255),  # person:     黄
    (255, 0, 255),  # motorcycle: 紫
    (255, 255, 0),  # bicycle:    青
]

def load_model(model_path: str):
    """加载 Vitis AI VART 模型"""
    try:
        import vart
        import xir
        g = xir.Graph.deserialize(model_path)
        subgraph = g.get_root_subgraph()
        dpu_subgraphs = [s for s in subgraph.toposort_child_subgraph()
                         if s.has_attr('device') and s.get_attr('device') == 'DPU']
        if not dpu_subgraphs:
            raise RuntimeError("No DPU subgraph found in xmodel")
        runner = vart.Runner.create_runner(dpu_subgraphs[0], 'run')
        print(f"DPU runner 创建成功")
        print(f"  输入张量: {[t.name for t in runner.get_input_tensors()]}")
        print(f"  输出张量: {[t.name for t in runner.get_output_tensors()]}")
        return runner
    except ImportError:
        print("警告：vart/xir 不可用，使用 CPU 模拟模式")
        return None

def preprocess(img_bgr, input_size=(640, 640)):
    """图像预处理：resize + normalize（与训练时一致）"""
    import cv2
    h, w = img_bgr.shape[:2]
    # letterbox padding
    scale = min(input_size[0] / h, input_size[1] / w)
    new_h, new_w = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img_bgr, (new_w, new_h))
    img_padded = np.zeros((input_size[0], input_size[1], 3), dtype=np.uint8)
    pad_h, pad_w = (input_size[0]-new_h)//2, (input_size[1]-new_w)//2
    img_padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = img_resized
    # BGR→RGB, HWC→CHW, /255
    img_rgb = img_padded[:, :, ::-1].astype(np.float32) / 255.0
    return img_rgb[np.newaxis], scale, pad_h, pad_w

def postprocess(output, conf_thresh=0.4, nms_thresh=0.5,
                scale=1.0, pad_h=0, pad_w=0, orig_hw=(1080,1920)):
    """YOLOv8 输出解析：[B, num_boxes, 4+num_classes]"""
    import cv2
    # output shape: (1, 8400, 4+6)
    pred = output[0]  # (8400, 10)
    boxes, scores, class_ids = [], [], []
    for det in pred:
        conf = det[4:].max()
        if conf < conf_thresh: continue
        cls = int(det[4:].argmax())
        cx, cy, bw, bh = det[:4]
        # 去掉 letterbox padding，恢复原始坐标
        x1 = (cx - bw/2 - pad_w) / scale
        y1 = (cy - bh/2 - pad_h) / scale
        x2 = (cx + bw/2 - pad_w) / scale
        y2 = (cy + bh/2 - pad_h) / scale
        x1 = max(0, min(x1, orig_hw[1]))
        y1 = max(0, min(y1, orig_hw[0]))
        boxes.append([x1, y1, x2, y2])
        scores.append(float(conf))
        class_ids.append(cls)

    if not boxes: return []
    indices = cv2.dnn.NMSBoxes(
        [[b[0], b[1], b[2]-b[0], b[3]-b[1]] for b in boxes],
        scores, conf_thresh, nms_thresh)
    return [(boxes[i], scores[i], class_ids[i])
            for i in (indices.flatten() if len(indices) > 0 else [])]

def draw_results(img, detections):
    import cv2
    for (x1,y1,x2,y2), conf, cls in detections:
        color = CLASS_COLORS_BGR[cls % len(CLASS_COLORS_BGR)]
        cv2.rectangle(img, (int(x1),int(y1)), (int(x2),int(y2)), color, 2)
        label = f"{CLASS_NAMES[cls]} {conf:.2f}"
        cv2.putText(img, label, (int(x1), int(y1)-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return img

def run_inference(runner, img_bgr):
    """在 DPU 上执行一次推理，返回检测结果"""
    if runner is None:
        # CPU 模拟（开发调试用）
        time.sleep(0.020)  # 模拟 20ms 推理延迟
        return []

    input_tensors  = runner.get_input_tensors()
    output_tensors = runner.get_output_tensors()

    inp, scale, pad_h, pad_w = preprocess(img_bgr)
    h, w = img_bgr.shape[:2]

    input_data  = {t.name: np.zeros(tuple(t.dims), dtype=np.int8)
                   for t in input_tensors}
    output_data = {t.name: np.zeros(tuple(t.dims), dtype=np.int8)
                   for t in output_tensors}

    # 量化输入（FP32 → INT8，scale factor 来自 xmodel）
    scale_factor = 1.0 / 128.0
    input_data[input_tensors[0].name] = (inp / scale_factor).astype(np.int8)

    job_id = runner.execute_async(input_data, output_data)
    runner.wait(job_id)

    # 反量化输出
    out_fp32 = output_data[output_tensors[0].name].astype(np.float32) * scale_factor
    return postprocess(out_fp32, scale=scale, pad_h=pad_h, pad_w=pad_w, orig_hw=(h, w))

def benchmark(runner, num_frames=100):
    import cv2
    print(f"\n=== 性能基准测试（{num_frames} 帧）===")
    # 随机生成测试帧
    test_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    # 预热
    for _ in range(5): run_inference(runner, test_img)

    latencies = []
    for i in range(num_frames):
        t0 = time.perf_counter()
        run_inference(runner, test_img)
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies.sort()
    print(f"  平均延迟:  {np.mean(latencies):.2f} ms")
    print(f"  P50 延迟:  {latencies[len(latencies)//2]:.2f} ms")
    print(f"  P95 延迟:  {latencies[int(len(latencies)*0.95)]:.2f} ms")
    print(f"  P99 延迟:  {latencies[int(len(latencies)*0.99)]:.2f} ms")
    print(f"  最大延迟:  {max(latencies):.2f} ms")
    print(f"  吞吐量:    {1000/np.mean(latencies):.1f} FPS")
    print(f"  4路合计:   {4000/np.mean(latencies):.1f} FPS (if 4ch parallel)")

def main():
    args = parse_args()
    import cv2

    runner = load_model(args.model)

    if args.benchmark:
        benchmark(runner, args.num_frames)
        return

    if args.image:
        img = cv2.imread(args.image)
        if img is None:
            print(f"无法读取图像: {args.image}")
            sys.exit(1)

        t0 = time.perf_counter()
        detections = run_inference(runner, img)
        lat = (time.perf_counter() - t0) * 1000

        print(f"\n推理结果（延迟: {lat:.1f} ms）：")
        for (x1,y1,x2,y2), conf, cls in detections:
            print(f"  {CLASS_NAMES[cls]:<12} conf={conf:.3f}  "
                  f"bbox=[{int(x1)},{int(y1)},{int(x2)},{int(y2)}]")

        if args.save_result:
            out = draw_results(img.copy(), detections)
            out_path = 'inference_result.jpg'
            cv2.imwrite(out_path, out)
            print(f"结果图像保存至: {out_path}")

    elif args.camera is not None:
        cap = cv2.VideoCapture(f'/dev/video{args.camera}')
        if not cap.isOpened():
            print(f"无法打开 /dev/video{args.camera}")
            sys.exit(1)
        print(f"实时推理 /dev/video{args.camera}，按 Ctrl+C 退出")
        fps_counter, t_start = 0, time.time()
        try:
            while True:
                ret, frame = cap.read()
                if not ret: break
                dets = run_inference(runner, frame)
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps = fps_counter / (time.time() - t_start)
                    print(f"FPS: {fps:.1f}  Detections: {len(dets)}")
        except KeyboardInterrupt:
            pass
        cap.release()

if __name__ == '__main__':
    main()
