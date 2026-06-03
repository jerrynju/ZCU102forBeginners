# 02 - FPGA / PL 硬件逻辑开发

## 1. Vivado 工程结构

```
hardware/vivado_project/
├── traffic_edge.xpr              # 顶层工程文件
├── ip_repo/                      # 自定义 IP 库
│   ├── mipi_csi2_rx_v1.0/        # MIPI CSI-2 接收 IP
│   ├── isp_pipeline_v1.0/        # HLS ISP 管线 IP
│   └── osd_overlay_v1.0/         # HLS OSD 叠加 IP
├── constraints/
│   ├── timing.xdc                # 时序约束
│   └── pinout.xdc                # 引脚分配
└── bd/
    └── traffic_edge_bd.tcl       # Block Design Tcl 重建脚本
```

## 2. Block Design 模块清单

```
ZCU102 Block Design: traffic_edge_bd
│
├── zynq_ultra_ps_e_0              (Zynq UltraScale+ MPSoC)
│   ├── HP0_LPD_AXI: ← video_dma_s2mm (摄像头写入)
│   ├── HP1_FPD_AXI: ← dpu_0 input    (DPU 读帧)
│   ├── HP2_FPD_AXI: ← dpu_0 output   (DPU 写结果)
│   ├── HP3_FPD_AXI: ← osd_vdma       (显示读取)
│   ├── HPC0_FPD_AXI: ← (保留)
│   └── M_AXI_HPM0/1: → AXI Interconnect → 所有从设备
│
├── mipi_csi2_rx_subsystem_[0..3]  (Xilinx MIPI CSI-2 RX IP)
│   └── video_out: AXI-Stream (RAW10) → isp_pipeline
│
├── isp_pipeline_[0..3]            (自研 HLS IP)
│   ├── s_axis_video: ← MIPI RAW10
│   └── m_axis_video: NV12 @ 1080p → video_dma
│
├── axi_vdma_0                     (Video DMA, 4 channel write)
│   └── 将 4 路 NV12 帧写入 DDR4 帧缓冲
│
├── dpu_0                          (Xilinx DPU B4096)
│   ├── s_axi_control: ← AXI-Lite (PS 控制)
│   ├── m_axi_data0: ↔ HP1 (权重/输入)
│   └── m_axi_data1: ↔ HP2 (输出)
│
├── xxv_ethernet_0                 (25G/10G Ethernet IP, 配置为 10GbE)
│   └── gt_ref_clk: 156.25MHz
│
├── axi_can_0                      (AXI CAN 2.0B)
│
├── v_dp_txss1_0                   (DisplayPort TX Subsystem)
│   └── dp_tx: → 板载 DP 连接器
│
├── osd_overlay_0                  (自研 HLS IP)
│   └── 从 DDR 读取帧 + 叠加检测框/字幕
│
├── axi_gpio_0                     (GPS PPS 信号接入)
│
└── axi_intc_0                     (中断控制器)
```

## 3. HLS ISP 管线实现

### 3.1 功能概述
将 MIPI 输出的 RAW10 Bayer 格式转换为 NV12（YUV420），并完成：
- 黑电平校正（Black Level Correction）
- 去马赛克（Demosaicing，RGGB → RGB）
- 白平衡（Auto White Balance）
- 伽马校正
- 色彩空间转换（RGB → YUV）
- 缩放（4K → 1080p，供 DPU 使用）

```cpp
// hardware/hls/isp_pipeline/isp_pipeline.cpp
#include "hls_video.h"
#include "ap_int.h"

#define SRC_WIDTH  3840
#define SRC_HEIGHT 2160
#define DST_WIDTH  1920
#define DST_HEIGHT 1080

typedef hls::stream<ap_axiu<16,1,1,1>> AXI_STREAM_IN;
typedef hls::stream<ap_axiu<24,1,1,1>> AXI_STREAM_OUT;
typedef hls::Mat<SRC_HEIGHT, SRC_WIDTH, HLS_16UC1> MAT_SRC;
typedef hls::Mat<DST_HEIGHT, DST_WIDTH, HLS_8UC3>  MAT_RGB;
typedef hls::Mat<DST_HEIGHT, DST_WIDTH, HLS_8UC2>  MAT_NV12;

void isp_pipeline(
    AXI_STREAM_IN& src,
    AXI_STREAM_OUT& dst,
    uint16_t black_level,
    uint16_t wb_r, uint16_t wb_g, uint16_t wb_b
) {
#pragma HLS INTERFACE axis port=src
#pragma HLS INTERFACE axis port=dst
#pragma HLS INTERFACE s_axilite port=black_level bundle=CTRL
#pragma HLS INTERFACE s_axilite port=wb_r        bundle=CTRL
#pragma HLS INTERFACE s_axilite port=wb_g        bundle=CTRL
#pragma HLS INTERFACE s_axilite port=wb_b        bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return      bundle=CTRL
#pragma HLS DATAFLOW  // 关键：使各阶段流水线并行

    MAT_SRC mat_raw(SRC_HEIGHT, SRC_WIDTH);
    MAT_SRC mat_blc(SRC_HEIGHT, SRC_WIDTH);
    MAT_RGB mat_rgb(DST_HEIGHT, DST_WIDTH);
    MAT_RGB mat_wb (DST_HEIGHT, DST_WIDTH);
    MAT_NV12 mat_nv12(DST_HEIGHT, DST_WIDTH);

    // Stage 1: AXI-Stream → Mat
    hls::AXIvideo2Mat(src, mat_raw);

    // Stage 2: 黑电平校正
    black_level_correction(mat_raw, mat_blc, black_level);

    // Stage 3: 去马赛克 + 缩放（合并减少 BRAM 开销）
    hls::Resize(mat_blc, mat_rgb);  // 内部含 demosaic

    // Stage 4: 白平衡
    white_balance(mat_rgb, mat_wb, wb_r, wb_g, wb_b);

    // Stage 5: RGB → NV12 + AXI-Stream 输出
    hls::CvtColor<HLS_RGB2YUV_I420>(mat_wb, mat_nv12);
    hls::Mat2AXIvideo(mat_nv12, dst);
}

// 黑电平校正（减去暗电流偏置）
void black_level_correction(MAT_SRC& src, MAT_SRC& dst, uint16_t level) {
#pragma HLS INLINE
    for (int r = 0; r < SRC_HEIGHT; r++) {
        for (int c = 0; c < SRC_WIDTH; c++) {
#pragma HLS PIPELINE II=1
            hls::Scalar<1, uint16_t> px;
            src >> px;
            px.val[0] = (px.val[0] > level) ? (px.val[0] - level) : 0;
            dst << px;
        }
    }
}
```

### 3.2 HLS 综合指令要点

```cpp
// 关键优化点说明：

// 1. DATAFLOW 使各处理阶段形成流水线，帧级并行
#pragma HLS DATAFLOW

// 2. PIPELINE II=1 使像素级循环每时钟处理一像素
#pragma HLS PIPELINE II=1

// 3. ARRAY_PARTITION 避免 BRAM 端口冲突（行缓冲区）
#pragma HLS ARRAY_PARTITION variable=line_buffer cyclic factor=4 dim=2

// 4. 4路 ISP 并行：在 Block Design 中例化 4 份，共享同一 IP
```

### 3.3 综合目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 时钟频率 | 250 MHz | 足以处理 4K@30fps（像素率 248.8 MHz） |
| 延迟 | < 2 帧 | ~66ms |
| LUT 使用 | < 15K / 路 | 4 路共 < 60K，占总资源 ~10% |
| DSP | < 50 / 路 | 用于插值和颜色矩阵运算 |
| BRAM | < 20 / 路 | 行缓冲区 |

## 4. OSD 字幕叠加 IP

```cpp
// hardware/hls/osd_overlay/osd_overlay.cpp
// 功能：从 DDR 读取检测结果，在视频流上叠加矩形框 + 文字

#define MAX_OBJECTS 64
#define BOX_THICKNESS 2

struct DetBox {
    uint16_t x, y, w, h;
    uint8_t  class_id;
    uint8_t  confidence;  // 0-100
};

// 颜色表：不同类别用不同颜色
static const uint32_t CLASS_COLORS[8] = {
    0xFF0000,  // 0: car    红
    0x00FF00,  // 1: truck  绿
    0x0000FF,  // 2: bus    蓝
    0xFFFF00,  // 3: person 黄
    0xFF00FF,  // 4: plate  紫
};

void osd_overlay(
    hls::stream<ap_axiu<24,1,1,1>>& s_video,
    hls::stream<ap_axiu<24,1,1,1>>& m_video,
    DetBox* boxes,
    uint8_t box_count,
    uint16_t frame_width,
    uint16_t frame_height
) {
#pragma HLS INTERFACE axis      port=s_video
#pragma HLS INTERFACE axis      port=m_video
#pragma HLS INTERFACE m_axi     port=boxes   depth=64 bundle=GMEM
#pragma HLS INTERFACE s_axilite port=box_count   bundle=CTRL
#pragma HLS INTERFACE s_axilite port=frame_width  bundle=CTRL
#pragma HLS INTERFACE s_axilite port=frame_height bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return       bundle=CTRL

    // 预加载检测框到本地缓存（避免逐像素访问 DDR）
    DetBox local_boxes[MAX_OBJECTS];
#pragma HLS ARRAY_PARTITION variable=local_boxes complete
    for (int i = 0; i < box_count; i++) local_boxes[i] = boxes[i];

    for (int row = 0; row < frame_height; row++) {
        for (int col = 0; col < frame_width; col++) {
#pragma HLS PIPELINE II=1
            ap_axiu<24,1,1,1> pixel;
            s_video >> pixel;

            // 判断当前像素是否在任意检测框的边界上
            bool on_border = false;
            uint32_t border_color = 0;
            for (int b = 0; b < MAX_OBJECTS; b++) {
#pragma HLS UNROLL
                if (b >= box_count) continue;
                bool in_x = (col >= local_boxes[b].x) &&
                            (col <  local_boxes[b].x + local_boxes[b].w);
                bool in_y = (row >= local_boxes[b].y) &&
                            (row <  local_boxes[b].y + local_boxes[b].h);
                bool on_x_edge = (col - local_boxes[b].x < BOX_THICKNESS) ||
                                 (local_boxes[b].x + local_boxes[b].w - col <= BOX_THICKNESS);
                bool on_y_edge = (row - local_boxes[b].y < BOX_THICKNESS) ||
                                 (local_boxes[b].y + local_boxes[b].h - row <= BOX_THICKNESS);
                if (in_x && in_y && (on_x_edge || on_y_edge)) {
                    on_border = true;
                    border_color = CLASS_COLORS[local_boxes[b].class_id & 0x7];
                }
            }

            if (on_border) {
                pixel.data = border_color;
            }
            m_video << pixel;
        }
    }
}
```

## 5. 时序约束（XDC 关键部分）

```tcl
# constraints/timing.xdc

# ─── 主时钟 ───────────────────────────────────────────────
create_clock -period 4.000 -name clk_250m [get_ports clk_250m_p]
create_clock -period 6.400 -name clk_156m [get_ports gt_ref_clk_p]  ;# 10GbE

# ─── MIPI 时钟（由 CSI-2 PHY 产生，标称 750MHz 每 lane）────
# Vivado 通常自动推断，手动 set_input_jitter
set_input_jitter [get_clocks clk_mipi_rxbyteclk] 0.05

# ─── 跨时钟域约束 ────────────────────────────────────────
# ISP_250MHz → PS_AXI_150MHz（VDMA 接口）
set_max_delay -datapath_only -from [get_clocks clk_250m] \
              -to [get_clocks clkout1_primitive] 4.0

# ─── 假路径（无需时序分析的路径）───────────────────────────
set_false_path -from [get_ports rst_n]

# ─── I/O 延迟约束（MIPI LVDS）──────────────────────────────
set_input_delay -clock clk_mipi_rxbyteclk -max 0.3 [get_ports {mipi_data_p[*]}]
set_input_delay -clock clk_mipi_rxbyteclk -min 0.1 [get_ports {mipi_data_p[*]}]
```

## 6. 综合与实现配置

```tcl
# 推荐 Strategy：性能优先
set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]

# DPU 推荐使用 Pblock 固定位置，避免影响其他逻辑布局
create_pblock pblock_dpu
add_cells_to_pblock [get_pblocks pblock_dpu] [get_cells -hierarchical -filter {NAME =~ *dpu_0*}]
resize_pblock [get_pblocks pblock_dpu] -add {CLOCKREGION_X0Y3:CLOCKREGION_X3Y4}
```

## 7. 资源使用预算

| 模块 | LUT | FF | BRAM | DSP | 占总资源% |
|------|-----|----|------|-----|----------|
| DPU B4096 | 80K | 60K | 200 | 900 | 32% |
| 4× ISP HLS | 60K | 50K | 80  | 200 | 24% |
| 4× MIPI RX | 8K  | 6K  | 20  | 0   | 3% |
| VDMA × 2 | 5K  | 4K  | 16  | 0   | 2% |
| 10GbE MAC | 12K | 10K | 30  | 0   | 5% |
| OSD HLS | 10K | 8K  | 10  | 20  | 4% |
| DisplayPort | 5K  | 4K  | 8   | 0   | 2% |
| AXI Infra | 8K  | 6K  | 0   | 0   | 3% |
| **合计** | **188K** | **148K** | **364** | **1120** | **~75%** |

> ZCU102 总资源：274K LUT / 548K FF / 912 BRAM / 2520 DSP  
> 保留 25% 余量用于时序收敛

## 8. 常见问题与调试

### 时序违例处理流程

```
1. 运行 report_timing_summary 找到违例路径
2. 分析关键路径：
   - 跨模块长线？→ 添加寄存器打拍
   - 组合逻辑过深？→ HLS 中增加 PIPELINE 或手动 register
   - 跨时钟域？→ 检查 CDC 约束是否正确
3. HLS 层面优化：
   - 减小 PIPELINE II（增加流水线级数）
   - 使用 ap_fixed 代替 float
4. Vivado 层面：
   - 调整 Pblock，减少跨区域走线
   - 使用 phys_opt_design -directive AggressiveExplore
```

### MIPI 接收不稳定

```
检查项目：
□ Lane 对齐：mipi_csi2_rx 的 lane_link_state 寄存器是否全部 ALIGNED
□ 时钟：参考时钟频率与摄像头 D-PHY 配置是否匹配
□ 端接：MIPI 差分对 100Ω 差分端接是否在 PCB 上正确实现
□ 电压：VCCO_MIPI 是否为 1.2V（LVDS 标准）
□ 日志：dmesg | grep mipi 查看驱动初始化状态
```
