# ═══════════════════════════════════════════════════════════════
# @req IF-REQ-001, IF-REQ-002, IF-REQ-003, IF-REQ-005, IF-REQ-006
# @design DES-ARCH-001
# @test TC-IF-MIPI-001, TC-IF-10G-001, TC-IF-CAN-001
# @author fpga-team | @since 2026-06-04 | @version 1.0
# @status verified
#
# ZCU102 引脚分配约束
# 项目：智能交通路口感知平台
# 目标器件：xczu9eg-ffvb1156-2-e
# ═══════════════════════════════════════════════════════════════

# ── MIPI CSI-2 摄像头接口（通过 FMC HPC J55）──────────────────
# 摄像头 0：4-lane MIPI，最高 2.5 Gbps/lane
# LVDS 差分对，VCCO = 1.2V（Bank 65/66）

# CAM0 差分时钟
set_property PACKAGE_PIN AF8  [get_ports {cam0_clk_p}]
set_property PACKAGE_PIN AF7  [get_ports {cam0_clk_n}]
set_property IOSTANDARD LVDS_25 [get_ports {cam0_clk_*}]

# CAM0 数据 Lane 0-3
set_property PACKAGE_PIN AH8  [get_ports {cam0_data_p[0]}]
set_property PACKAGE_PIN AH7  [get_ports {cam0_data_n[0]}]
set_property PACKAGE_PIN AJ8  [get_ports {cam0_data_p[1]}]
set_property PACKAGE_PIN AJ7  [get_ports {cam0_data_n[1]}]
set_property PACKAGE_PIN AG10 [get_ports {cam0_data_p[2]}]
set_property PACKAGE_PIN AH10 [get_ports {cam0_data_n[2]}]
set_property PACKAGE_PIN AJ10 [get_ports {cam0_data_p[3]}]
set_property PACKAGE_PIN AJ9  [get_ports {cam0_data_n[3]}]
set_property IOSTANDARD LVDS_25 [get_ports {cam0_data_*}]

# 摄像头 1（2-lane，适配 1080p 备用摄像头）
set_property PACKAGE_PIN AK8  [get_ports {cam1_clk_p}]
set_property PACKAGE_PIN AK7  [get_ports {cam1_clk_n}]
set_property PACKAGE_PIN AL8  [get_ports {cam1_data_p[0]}]
set_property PACKAGE_PIN AL7  [get_ports {cam1_data_n[0]}]
set_property PACKAGE_PIN AM8  [get_ports {cam1_data_p[1]}]
set_property PACKAGE_PIN AM7  [get_ports {cam1_data_n[1]}]
set_property IOSTANDARD LVDS_25 [get_ports {cam1_clk_* cam1_data_*}]

# I2C：摄像头寄存器配置（PS MIO，由 PS 直接控制，无需 PL 约束）

# ── CAN 总线（通过 FMC LPC J87，外接 SN65HVD230 PHY）──────────
# PL 侧 CAN TX/RX → 外部 CAN PHY
set_property PACKAGE_PIN D22  [get_ports {can_tx}]
set_property PACKAGE_PIN C22  [get_ports {can_rx}]
set_property IOSTANDARD LVCMOS33 [get_ports {can_tx can_rx}]

# ── GPS PPS 输入（1 PPS 秒脉冲，接 AXI GPIO）──────────────────
set_property PACKAGE_PIN E22  [get_ports {gps_pps}]
set_property IOSTANDARD LVCMOS33 [get_ports {gps_pps}]
# PPS 上升沿触发，配置为输入
set_property PULLDOWN true [get_ports {gps_pps}]

# ── 调试 LED（ZCU102 板载 8个 LED）───────────────────────────
# LED[0]: 系统运行心跳（1Hz 闪烁）
# LED[1]: DPU 推理激活
# LED[2]: 10GbE 链路
# LED[3-7]: 各通道状态
set_property PACKAGE_PIN AG14 [get_ports {led[0]}]
set_property PACKAGE_PIN AF13 [get_ports {led[1]}]
set_property PACKAGE_PIN AE13 [get_ports {led[2]}]
set_property PACKAGE_PIN AJ14 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[*]}]

# ── 系统复位按钮（ZCU102 板载 SW19）──────────────────────────
set_property PACKAGE_PIN B8   [get_ports {sys_rst_n}]
set_property IOSTANDARD LVCMOS33 [get_ports {sys_rst_n}]
set_property PULLUP true [get_ports {sys_rst_n}]

# ── 10GbE GTH 参考时钟（156.25 MHz，来自板载 Si570）────────────
# GTH Bank 226（SFP+ 光口）
# 注意：GTH 引脚由 Vivado 自动管理，此处仅约束参考时钟
set_property PACKAGE_PIN P6  [get_ports {gt_ref_clk_p}]
set_property PACKAGE_PIN P5  [get_ports {gt_ref_clk_n}]
# GT TX/RX：Bank 226，由 XXV Ethernet IP 的 BD 连接自动约束

# ── DisplayPort（PS 侧，MIO 引脚，由 PS 配置，PL 无需约束）──────
# DP_TX_HPD: MIO 27
# DP_AUX_IN: MIO 28
# DP_AUX_OUT: MIO 29
# （设备树和 PS 配置已处理）

# ── 主时钟（PL 逻辑时钟，来自 PS FCLK）──────────────────────
# FCLK_CLK0: 250 MHz  → ISP / OSD 逻辑
# FCLK_CLK1: 200 MHz  → DPU
# FCLK_CLK2: 100 MHz  → AXI Interconnect
# FCLK_CLK3: 25 MHz   → 低速外设
# （均由 Zynq PS IP 内部生成，无需额外约束）

# ── VCCO 电压约束 ──────────────────────────────────────────
set_property INTERNAL_VREF 0.84 [get_iobanks 64]  ;# DDR4
set_property INTERNAL_VREF 0.84 [get_iobanks 65]
