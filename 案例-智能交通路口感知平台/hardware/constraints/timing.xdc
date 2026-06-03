# ═══════════════════════════════════════════════════════════════
# ZCU102 时序约束文件
# 项目：智能交通路口感知平台
# ═══════════════════════════════════════════════════════════════

# ── PS 生成的 PL 时钟（Zynq PS IP 自动创建，此处设置期望频率）──
# FCLK_CLK0: 250 MHz → ISP HLS / OSD / AXI Interconnect 主时钟
create_generated_clock -name clk_250m \
    -source [get_pins -hierarchical -filter {NAME =~ */PS8_i/PLCLK[0]}] \
    -divide_by 1 \
    [get_nets -hierarchical -filter {NAME =~ */FCLK_CLK0}]

# FCLK_CLK1: 300 MHz → DPU 推理时钟
create_generated_clock -name clk_300m \
    -source [get_pins -hierarchical -filter {NAME =~ */PS8_i/PLCLK[1]}] \
    -divide_by 1 \
    [get_nets -hierarchical -filter {NAME =~ */FCLK_CLK1}]

# FCLK_CLK2: 150 MHz → AXI HP 总线（PS↔PL DMA）
create_generated_clock -name clk_150m \
    -source [get_pins -hierarchical -filter {NAME =~ */PS8_i/PLCLK[2]}] \
    -divide_by 1 \
    [get_nets -hierarchical -filter {NAME =~ */FCLK_CLK2}]

# ── GTH 参考时钟（10GbE，156.25 MHz）──────────────────────────
create_clock -name gt_ref_clk -period 6.400 \
    [get_ports gt_ref_clk_p]

# ── MIPI 字节时钟（由 MIPI CSI-2 RX IP 内部生成）─────────────
# 典型值：摄像头 RAW10 @4K30 → 750Mbps/lane → 75 MHz 字节时钟
# Vivado 会自动推断，此处设置 jitter 预算
set_input_jitter [get_clocks -of_objects \
    [get_nets -hierarchical -filter {NAME =~ *mipi*rxbyteclk*}]] 0.050

# ── 跨时钟域约束（CDC）────────────────────────────────────────
# ISP @ 250MHz → AXI HP @ 150MHz（VDMA 写入 DDR）
# 使用 set_max_delay 配合 CDC FIFO，约束最大传播时间
set_max_delay -datapath_only \
    -from [get_clocks clk_250m] \
    -to   [get_clocks clk_150m] \
    6.667   ;# 1/150MHz

set_max_delay -datapath_only \
    -from [get_clocks clk_150m] \
    -to   [get_clocks clk_250m] \
    4.000   ;# 1/250MHz

# DPU @ 300MHz → AXI HP @ 150MHz
set_max_delay -datapath_only \
    -from [get_clocks clk_300m] \
    -to   [get_clocks clk_150m] \
    6.667

set_max_delay -datapath_only \
    -from [get_clocks clk_150m] \
    -to   [get_clocks clk_300m] \
    3.333   ;# 1/300MHz

# GTH 用户时钟 → 250MHz（10GbE AXIS 接口）
set_max_delay -datapath_only \
    -from [get_clocks -of_objects \
           [get_nets -hierarchical -filter {NAME =~ *xxv_ethernet*}]] \
    -to   [get_clocks clk_250m] \
    4.000

# ── 假路径（不需要时序分析）────────────────────────────────────
# 系统复位信号（异步复位，不需要时序约束）
set_false_path -from [get_ports sys_rst_n]

# LED 输出（无时序要求）
set_false_path -to [get_ports {led[*]}]

# GPS PPS 输入（已有专用同步逻辑处理亚稳态）
set_false_path -from [get_ports gps_pps]

# CAN TX/RX（外部 PHY 处理，无 FPGA 内时序要求）
set_false_path -from [get_ports can_rx]
set_false_path -to   [get_ports can_tx]

# ── I/O 时序约束（MIPI 输入）────────────────────────────────
# MIPI 差分输入建立/保持时间（参考 Xilinx MIPI AN）
set_input_delay -clock [get_clocks -of_objects \
    [get_nets -hierarchical -filter {NAME =~ *mipi*rxbyteclk*}]] \
    -max 0.35 [get_ports {cam0_data_p[*] cam0_data_n[*]}]
set_input_delay -clock [get_clocks -of_objects \
    [get_nets -hierarchical -filter {NAME =~ *mipi*rxbyteclk*}]] \
    -min 0.10 [get_ports {cam0_data_p[*] cam0_data_n[*]}]

# ── Pblock 约束（固定 DPU 布局区域，减少长线互联）─────────────
# DPU 放置在 FPGA 中间区域（远离 GT 和 IO）
create_pblock pb_dpu
add_cells_to_pblock [get_pblocks pb_dpu] \
    [get_cells -hierarchical -filter {NAME =~ *dpu_0*}]
resize_pblock [get_pblocks pb_dpu] \
    -add {CLOCKREGION_X0Y3:CLOCKREGION_X3Y4}

# ISP 管线放置在左侧，靠近 GT
create_pblock pb_isp
add_cells_to_pblock [get_pblocks pb_isp] \
    [get_cells -hierarchical -filter {NAME =~ *isp_pipeline*}]
resize_pblock [get_pblocks pb_isp] \
    -add {CLOCKREGION_X0Y0:CLOCKREGION_X1Y2}

# ── 综合策略提示（在 Vivado Tcl Console 中执行）──────────────
# set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]
# set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
