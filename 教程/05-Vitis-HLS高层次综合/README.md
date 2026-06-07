# 阶段 5：Vitis HLS 高层次综合

## 学习目标

- 理解 HLS C/C++ → RTL 的综合流程
- 掌握 `#pragma HLS` 指令（PIPELINE、UNROLL、DATAFLOW、ARRAY_PARTITION）
- 生成 AXI4-Lite 控制接口和 AXI4-Stream 数据接口
- 进行 C 仿真、RTL 仿真和 Co-Sim 验证
- 将 HLS IP 集成到 Vivado IPI Block Design

---

## 5.1 HLS 综合流程

```
C/C++ 源码
    │ petalinux-build
    ▼
C 仿真 (csim)         ← 纯软件仿真，验证算法正确性
    │
    ▼
综合 (synthesis)      ← 生成 RTL + 资源/延迟报告
    │
    ▼
RTL 仿真 (cosim)      ← 用 C testbench 驱动 RTL 仿真
    │
    ▼
导出 IP (export RTL)  ← 生成可在 Vivado IPI 中使用的 IP
    │
    ▼
Vivado 集成           ← 在 Block Design 中使用 HLS IP
```

---

## 5.2 实验 5-1：矩阵乘法（PIPELINE + UNROLL）

### 5.2.1 基础实现

```cpp
// matmul.cpp - 16×16 矩阵乘法
void matmul(
    float A[16][16],
    float B[16][16],
    float C[16][16]
) {
#pragma HLS INTERFACE s_axilite port=return
#pragma HLS INTERFACE bram port=A
#pragma HLS INTERFACE bram port=B
#pragma HLS INTERFACE bram port=C

    for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
#pragma HLS PIPELINE II=1
            float sum = 0;
            for (int k = 0; k < 16; k++) {
#pragma HLS UNROLL factor=4
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}
```

### 5.2.2 优化版（DATAFLOW + ARRAY_PARTITION）

```cpp
// 使用 DATAFLOW 实现流水线并行
void matmul_opt(
    float A[16][16],
    float B[16][16],
    float C[16][16]
) {
#pragma HLS INTERFACE s_axilite port=return
#pragma HLS ARRAY_PARTITION variable=A cyclic factor=4 dim=2
#pragma HLS ARRAY_PARTITION variable=B cyclic factor=4 dim=1
#pragma HLS DATAFLOW

    float tmp[16][16];
#pragma HLS ARRAY_PARTITION variable=tmp complete dim=0

    compute: for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
#pragma HLS PIPELINE II=1
            float sum = 0;
            for (int k = 0; k < 16; k++) {
                sum += A[i][k] * B[k][j];
            }
            tmp[i][j] = sum;
        }
    }

    store: for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
#pragma HLS PIPELINE II=1
            C[i][j] = tmp[i][j];
        }
    }
}
```

### 5.2.3 综合结果对比

| 版本 | Latency (cycles) | II | LUT | DSP |
|------|------------------|----|-----|-----|
| 基础（无指令）| 4352 | 4352 | 120 | 4 |
| PIPELINE II=1 | 276 | 1 | 350 | 16 |
| DATAFLOW+PARTITION | 68 | 1 | 1200 | 64 |

---

## 5.3 实验 5-2：AXI4-Stream 图像滤波

```cpp
// sobel.cpp - AXI-Stream Sobel 边缘检测
#include "hls_stream.h"
#include "ap_int.h"
#include "ap_fixed.h"
#include "hls_video.h"

typedef ap_uint<8>  pixel_t;
typedef hls::stream<ap_axiu<8,1,1,1>> AXI_STREAM;

void sobel_filter(
    AXI_STREAM &in_stream,
    AXI_STREAM &out_stream,
    int rows,
    int cols
) {
#pragma HLS INTERFACE axis port=in_stream
#pragma HLS INTERFACE axis port=out_stream
#pragma HLS INTERFACE s_axilite port=rows
#pragma HLS INTERFACE s_axilite port=cols
#pragma HLS INTERFACE s_axilite port=return

    // 行缓冲（2 行 1080 宽）
    static pixel_t line_buf[2][1920];
#pragma HLS ARRAY_PARTITION variable=line_buf complete dim=1

    pixel_t win[3][3];
#pragma HLS ARRAY_PARTITION variable=win complete dim=0

    row_loop: for (int r = 0; r < rows; r++) {
        col_loop: for (int c = 0; c < cols; c++) {
#pragma HLS PIPELINE II=1
            ap_axiu<8,1,1,1> px = in_stream.read();
            pixel_t val = px.data;

            // 更新行缓冲与滑动窗口
            // ... (完整实现见 refs/sobel.cpp)

            // Sobel 核
            int16_t gx = win[0][0] - win[0][2]
                        + 2*win[1][0] - 2*win[1][2]
                        + win[2][0] - win[2][2];
            int16_t gy = win[0][0] + 2*win[0][1] + win[0][2]
                        - win[2][0] - 2*win[2][1] - win[2][2];
            uint16_t mag = hls::abs(gx) + hls::abs(gy);
            ap_axiu<8,1,1,1> out_px;
            out_px.data = (mag > 255) ? 255 : mag;
            out_px.last = px.last;
            out_stream.write(out_px);
        }
    }
}
```

---

## 5.4 实验 5-3：AXI4-Lite 控制接口

```cpp
// pwm.cpp - 可编程 PWM（AXI-Lite 配置）
void pwm_ctrl(
    volatile ap_uint<32> *config,   // [31:16]=period, [15:0]=duty
    ap_uint<1> &pwm_out
) {
#pragma HLS INTERFACE s_axilite port=config bundle=CTRL
#pragma HLS INTERFACE ap_none   port=pwm_out
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL

    static ap_uint<32> counter = 0;
    ap_uint<16> period = (*config >> 16) & 0xFFFF;
    ap_uint<16> duty   = *config & 0xFFFF;

    counter++;
    if (counter >= period) counter = 0;
    pwm_out = (counter < duty) ? 1 : 0;
}
```

生成的 AXI-Lite 寄存器映射（VivadoIPI 中可见）：
```
0x00 CTRL      ap_start/done/idle
0x10 CONFIG    period[31:16] | duty[15:0]
```

---

## 5.5 Vitis HLS Tcl 自动化

```tcl
# run_hls.tcl - 非交互式综合脚本
open_project matmul_proj
set_top matmul
add_files matmul.cpp
add_files -tb matmul_tb.cpp

open_solution "solution1" -flow_target vivado
set_part xczu9eg-ffvb1156-2-e
create_clock -period 4 -name default    ;# 250 MHz

# 运行 C 仿真
csim_design

# 综合
csynth_design

# RTL 协同仿真
cosim_design

# 导出 IP
export_design -rtl verilog -format ip_catalog

exit
```

```bash
vitis_hls -f run_hls.tcl
```

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| Vitis HLS 教程 | [github.com/Xilinx/Vitis-Tutorials/tree/master/Hardware_Accelerators](https://github.com/Xilinx/Vitis-Tutorials/tree/master/Hardware_Accelerators) | 官方 HLS 加速器教程 |
| UG1399 | Vitis HLS 用户指南 | HLS 完整手册（指令/接口/优化）|
| UG902 | Vivado HLS 用户指南（旧版参考）| 指令兼容参考 |
| Vitis HLS Introductory | [github.com/Xilinx/Vitis-Tutorials/tree/master/Hardware_Accelerators/Design_Tutorials](https://github.com/Xilinx/Vitis-Tutorials/tree/master/Hardware_Accelerators/Design_Tutorials) | 设计教程 |
| HLS pragma 速查 | UG1399 附录 A | 所有 pragma 列表 |

详见 [`refs/`](refs/) 目录。
