# 阶段 5 参考资源链接

## 核心官方教程

### 1. Vitis HLS Getting Started（官方入门）
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Getting_Started/Vitis_HLS/`
- **内容**: Vitis HLS 工程创建、C综合、II优化、数据流

### 2. HLS Code Optimization for ZCU102（直接针对 ZCU102）
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Developer_Contributed/03-HLS_Code_Optimization/`
- **工具版本**: Vitis 2024.1（明确验证）
- **目标板**: ZCU102 和 VCK190
- **内容**: HLS 优化技术，硬件加速完整流程

### 3. HLS Performance Pragma
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Vitis_HLS/Feature_Tutorials/01-performance-pragma/`
- **内容**: 顶层 Performance Pragma，系统级吞吐率目标

### 4. HLS Beamformer Design
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Vitis_HLS/Design_Tutorials/02-Beamformer/`
- **内容**: 复杂 DSP 算法 HLS 实现（浮点 QRD+WBS）

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG1399 | Vitis HLS User Guide | HLS 完整手册（指令/接口/优化报告）|
| UG902 | Vivado Design Suite: High-Level Synthesis | 旧版参考，指令兼容性好 |
| UG1270 | Vitis HLS Pragma Reference Guide | 所有 pragma 速查 |

## 关键 HLS Pragma 速查

```cpp
// 数据流并行
#pragma HLS DATAFLOW

// 流水线（目标 II=1）
#pragma HLS PIPELINE II=1

// 展开循环
#pragma HLS UNROLL factor=4

// 数组分割（提高并行访问）
#pragma HLS ARRAY_PARTITION variable=A cyclic factor=4 dim=2

// AXI-Lite 控制接口
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL

// AXI4-Stream 数据接口
#pragma HLS INTERFACE axis port=in_stream depth=1024

// AXI4 主接口（DDR 访问）
#pragma HLS INTERFACE m_axi port=data offset=slave bundle=MAXI depth=1024

// 内联函数（消除函数调用开销）
#pragma HLS INLINE

// 资源绑定（强制使用 DSP）
#pragma HLS RESOURCE variable=sum core=FAddSub_nodsp
```

## Vitis Libraries（可直接调用的 HLS 库）
- **仓库**: https://github.com/Xilinx/Vitis_Libraries
- **教程**: https://github.com/Xilinx/Vitis-Tutorials/tree/master/Getting_Started/Vitis_Libraries
- 包含: 线性代数/图像处理/DSP/数据压缩/数据库等预优化 HLS 库
