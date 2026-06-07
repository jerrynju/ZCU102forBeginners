# 阶段 6：AI 推理与 Vitis AI

## 学习目标

- 理解 DPU B4096 架构与配置选项
- 使用 Vitis AI 3.5 Docker 对 YOLOv8s 进行 PTQ INT8 量化
- 生成 `.xmodel` 文件并部署到 ZCU102 DPU
- 使用 VART C++ API 进行高性能推理
- 分析推理性能（吞吐量/延迟/精度损失）

---

## 6.1 DPU B4096 架构

```
┌──────────────────────────────────────────────────────┐
│  DPU B4096 (Batch Size=1 per core)                   │
│                                                      │
│  计算能力: 2.5 TOPS (INT8, 2×B2048 = B4096)          │
│  权重 DDR: 通过 AXI HP 接口（高带宽，512-bit）         │
│  指令缓存: L1 64KB on-chip                            │
│                                                      │
│  支持算子: Conv2D, DWConv, MaxPool, AvgPool,          │
│            Concat, ReLU, LeakyReLU, BatchNorm         │
│  不支持: SiLU（需要量化前替换为近似激活）               │
└──────────────────────────────────────────────────────┘
```

### DPU IP 配置（Vivado IPI）

```tcl
# 推荐 ZCU102 DPU 配置
set_property -dict [list \
    CONFIG.DPU_NUM      {2}        \
    CONFIG.DPU_CLK_MHz  {300}      \
    CONFIG.DPU_ARCH     {B4096}    \
    CONFIG.RAM_USAGE    {Low}      \
    CONFIG.DSP48_USAGE  {High}     \
    CONFIG.URAM_ENABLE  {Disable}  \
] [get_bd_cells dpu_0]
```

---

## 6.2 Vitis AI Docker 环境

```bash
# 拉取 Vitis AI 3.5 CPU Docker
docker pull xilinx/vitis-ai-cpu:latest

# 启动（挂载项目目录）
docker run -it --rm \
    -v $(pwd):/workspace \
    -w /workspace \
    xilinx/vitis-ai-cpu:latest /bin/bash

# 在容器内激活 PyTorch 环境
conda activate vitis-ai-pytorch
```

---

## 6.3 实验 6-1：YOLOv8s PTQ INT8 量化

### 6.3.1 模型准备（SiLU → ReLU6 替换）

```python
# convert_yolov8.py - 替换不支持的激活函数
import torch
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

# 替换 SiLU 为 ReLU6（DPU 不支持 SiLU）
def replace_silu(module):
    for name, child in module.named_children():
        if isinstance(child, torch.nn.SiLU):
            setattr(module, name, torch.nn.ReLU6(inplace=True))
        else:
            replace_silu(child)

replace_silu(model.model)
torch.save(model.model.state_dict(), 'yolov8s_relu6.pth')
```

### 6.3.2 导出 ONNX 并量化

```python
# quantize_yolov8.py
import torch
from pytorch_nndct.apis import torch_quantizer
from yolov8_model import YOLOv8s

# 加载模型
model = YOLOv8s(nc=80).cuda()
model.load_state_dict(torch.load('yolov8s_relu6.pth'))
model.eval()

# 创建量化器（校准数据集 200 张图）
input_shape = torch.randn(1, 3, 640, 640).cuda()
quantizer = torch_quantizer('calib', model, input_shape,
                            device=torch.device('cuda'))
quant_model = quantizer.quant_model

# 校准（前向传播校准数据）
from calibration_dataset import CalibDataset
calib_loader = CalibDataset('/datasets/coco/calib200/')
with torch.no_grad():
    for img, _ in calib_loader:
        quant_model(img.cuda())

# 导出量化配置
quantizer.export_quant_config()

# 测试量化精度
quantizer_test = torch_quantizer('test', model, input_shape,
    quant_config_file='quant_info.json',
    device=torch.device('cuda'))
# ... 运行验证集评估 mAP

# 导出 xmodel
quantizer_test.export_xmodel(deploy_check=True)
```

### 6.3.3 编译为 DPU 指令

```bash
# 在 Vitis AI Docker 中编译 xmodel
vai_c_xir \
    --xmodel float.xmodel \
    --arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \
    --net_name yolov8s_traffic \
    --output_dir ./compiled/

# 输出文件
ls compiled/
# yolov8s_traffic.xmodel  ← 部署到板卡
# meta.json
```

---

## 6.4 实验 6-2：VART C++ 推理

```cpp
// infer.cpp - VART 推理框架
#include <vitis/ai/nnpp/yolov3.hpp>
#include "vart/runner.hpp"
#include "vart/tensor_buffer.hpp"

int main(int argc, char* argv[]) {
    // 加载 xmodel
    auto graph = xir::Graph::deserialize(argv[1]);
    auto root  = graph->get_root_subgraph();

    // 找到 DPU 子图
    xir::Subgraph* dpu_subgraph = nullptr;
    for (auto* s : root->get_children()) {
        if (s->get_attr<std::string>("device") == "DPU")
            dpu_subgraph = s;
    }

    // 创建 DPU Runner
    auto runner = vart::Runner::create_runner(dpu_subgraph, "run");

    // 获取输入/输出张量
    auto inputs  = runner->get_inputs();
    auto outputs = runner->get_outputs();

    // 准备输入（640×640 NV12 → RGB 预处理）
    auto* in_buf = dynamic_cast<vart::CpuFlatTensorBuffer*>(inputs[0]);
    preprocess_nv12_to_rgb(frame_nv12, in_buf->data().first, 640, 640);

    // 运行推理
    auto job_id = runner->execute_async(inputs, outputs);
    runner->wait(job_id.first, -1);  // 等待完成

    // 解析输出（YOLOv8 头部解码）
    std::vector<BBox> detections = decode_yolov8_output(outputs, 0.5f, 0.45f);

    return 0;
}
```

---

## 6.5 量化精度验证

```bash
# 在 ZCU102 上运行基准测试
./benchmark -m yolov8s_traffic.xmodel \
            -i /mnt/test_images/ \
            -t 2  # 2个线程

# 期望结果（ZCU102 DPU B4096）
# Throughput: ~8 FPS (640×640 单帧)
# Latency:    ~125ms
# mAP50:      FP32=52.1% → INT8=50.8% (降低<2%)
```

---

## 6.6 实验 6-3：多模型流水线

```
视频帧 (NV12)
    │
    ▼ (预处理: resize + normalize)
YOLOv8s 检测
    │  BBox列表
    ▼
目标裁剪 + 仿射变换
    │  96×32 裁剪
    ▼
LPRNet 车牌识别
    │  字符序列 (CTC)
    ▼
字符解码 + 后处理
    │  "京A12345"
    ▼
结果输出 (MQTT / OSD)
```

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| Vitis AI 教程 | [github.com/Xilinx/Vitis-AI/tree/master/examples](https://github.com/Xilinx/Vitis-AI/tree/master/examples) | 官方部署示例 |
| DPU B4096 产品指南 | PG338 | DPU IP 配置与接口手册 |
| Vitis AI 用户指南 | UG1414 | 量化/编译完整流程 |
| YOLOv8 on ZCU102 | [Vitis-AI/examples/vai_runtime/yolov3](https://github.com/Xilinx/Vitis-AI/tree/master/examples/vai_runtime/yolov3) | YOLO 推理示例 |
| VART API 文档 | [Vitis AI VART](https://xilinx.github.io/Vitis-AI/3.5/html/index.html) | VART C++/Python API |
| ZCU102 DPU overlay | [DPU-PYNQ](https://github.com/Xilinx/DPU-PYNQ) | 预制 DPU Overlay |

详见 [`refs/`](refs/) 目录。
