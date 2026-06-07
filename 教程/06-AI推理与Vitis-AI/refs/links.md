# 阶段 6 参考资源链接

## 核心官方教程

### 1. ZCU102 快速入门（预制 SD 卡镜像）
- **URL**: https://xilinx.github.io/Vitis-AI/3.0/html/docs/quickstart/mpsoc.html
- **内容**: 烧录 ZCU102 SD 镜像，SSH 登录，运行预制 ResNet50 推理
- **SD 镜像**: `xilinx-zcu102-dpu-v2022.2-v3.0.0.img.gz`
- **工具版本**: Vitis AI 3.0 / PetaLinux 2022.2

### 2. ResNet18 全流程（量化→编译→部署，Vitis AI 3.5）
- **仓库**: https://github.com/Xilinx/Vitis-AI-Tutorials (branch: 3.5)
- **路径**: `Tutorials/RESNET18/`
- **内容**: 检查浮点模型 → INT8 PTQ 量化 → DPUCZDX8G_ISA1_B4096 编译 → ZCU102 部署
- **目标板**: ZCU102

### 3. PyTorch ResNet18 + VART C++ API
- **仓库**: https://github.com/Xilinx/Vitis-AI-Tutorials (branch: 3.5)
- **路径**: `Tutorials/PyTorch-ResNet18/`
- **内容**: Model Zoo 下载、车辆颜色数据集微调、量化、VART C++ 推理 API
- **目标板**: ZCU102

### 4. PL 预/后处理加速器（HLS + DPU 协同）
- **仓库**: https://github.com/Xilinx/Vitis-AI-Tutorials (branch: 3.0)
- **路径**: `Tutorials/18-mpsocdpu-pre-post-pl-acc/`
- **内容**: HLS 图像归一化（预处理, ~5K LUT）+ Softmax/Argmax（后处理, ~10K LUT）与 DPU 并行
- **目标板**: ZCU102（明确指定）
- **工具版本**: Vitis AI 3.0 / Vitis HLS 2022.2

### 5. Keras CNN 系列（LeNet/VGG/GoogleNet/ResNet）
- **仓库**: https://github.com/Xilinx/Vitis-AI-Tutorials (branch: 3.0)
- **路径**: `Tutorials/Keras_GoogleNet_ResNet/`
- **内容**: Fashion-MNIST 和 CIFAR-10 训练、量化、C++ 推理应用
- **目标板**: ZCU102

### 6. 语义分割（FCN8 和 UNet）
- **仓库**: https://github.com/Xilinx/Vitis-AI-Tutorials (branch: 3.0)
- **路径**: `Tutorials/Keras_FCN8_UNET_segmentation/`
- **内容**: 分割模型量化和部署
- **目标板**: ZCU102

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| PG338 | DPU for Zynq UltraScale+ MPSoC Product Guide | DPU B4096 IP 配置手册 |
| UG1414 | Vitis AI User Guide | 量化/编译完整手册 |
| UG1431 | Vitis AI Library User Guide | 高级视觉 API（YOLOv3/ResNet/SSD）|

## 关键工具命令

```bash
# 查看 DPU 架构配置
cat /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json

# 编译 xmodel（板卡侧）
vai_c_xir \
    --xmodel float.xmodel \
    --arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \
    --net_name my_model \
    --output_dir ./compiled/

# 测试推理性能
/usr/bin/benchmark -t 1 -s 1000 -m my_model.xmodel

# 查看模型信息
xir subgraph my_model.xmodel
```

## Vitis AI Model Zoo（预训练模型）
- **URL**: https://github.com/Xilinx/Vitis-AI/tree/master/model_zoo
- 包含：YOLOv3/v4/v8, ResNet, EfficientDet, SSD, BERT 等
- ZCU102 DPU 对应 benchmark 名称: `DPUCZDX8G_ISA1_B4096`
