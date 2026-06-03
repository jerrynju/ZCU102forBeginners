# Vivado Block Design 构建脚本
# 用途：在干净环境重建完整工程
# 运行方式：vivado -mode batch -source build.tcl -tclargs /path/to/build_dir

set build_dir [lindex $argv 0]
if {$build_dir eq ""} { set build_dir "./build_output" }
file mkdir $build_dir

# ── 1. 创建工程 ───────────────────────────────────────────
create_project traffic_edge $build_dir/vivado -part xczu9eg-ffvb1156-2-e -force
set_property board_part xilinx.com:zcu102:part0:3.4 [current_project]
set_property target_language Verilog [current_project]

# 添加自定义 IP 仓库路径
set ip_repo_path [file normalize "[file dirname [info script]]/../../ip_repo"]
set_property ip_repo_paths $ip_repo_path [current_project]
update_ip_catalog -rebuild

# ── 2. 创建 Block Design ─────────────────────────────────
create_bd_design "traffic_edge_bd"
update_compile_order -fileset sources_1

# ── 3. 添加 Zynq UltraScale+ MPSoC IP ────────────────────
set zynq [create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0]

# 应用 ZCU102 板级预设
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} $zynq

# PS 高级配置
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP1 {0} \
    CONFIG.PSU__USE__S_AXI_HP0 {1} \
    CONFIG.PSU__USE__S_AXI_HP1 {1} \
    CONFIG.PSU__USE__S_AXI_HP2 {1} \
    CONFIG.PSU__USE__S_AXI_HP3 {1} \
    CONFIG.PSU__USE__S_AXI_HPC0_FPD {1} \
    CONFIG.PSU__FPGA_PL0_ENABLE {1} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {250} \
    CONFIG.PSU__FPGA_PL1_ENABLE {1} \
    CONFIG.PSU__CRL_APB__PL1_REF_CTRL__FREQMHZ {300} \
    CONFIG.PSU__FPGA_PL2_ENABLE {1} \
    CONFIG.PSU__CRL_APB__PL2_REF_CTRL__FREQMHZ {150} \
    CONFIG.PSU__FPGA_PL3_ENABLE {1} \
    CONFIG.PSU__CRL_APB__PL3_REF_CTRL__FREQMHZ {25}  \
    CONFIG.PSU__USE__IRQ0 {1} \
    CONFIG.PSU__GPIO_EMIO__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__GPIO_EMIO__PERIPHERAL__IO {32} \
    CONFIG.PSU__UART0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__UART0__PERIPHERAL__IO {MIO 42 .. 43} \
    CONFIG.PSU__I2C0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__I2C0__PERIPHERAL__IO {MIO 14 .. 15} \
    CONFIG.PSU__SD1__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__SD1__PERIPHERAL__IO {MIO 46 .. 51} \
    CONFIG.PSU__USB0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__USB0__PERIPHERAL__IO {MIO 52 .. 63} \
    CONFIG.PSU__DP__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__DP__REF_CLK_SEL {Ref Clk1} \
] $zynq

# ── 4. 添加 AXI SmartConnect（主互联）────────────────────
set sc_m [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_sc_master]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {8}] $sc_m

set sc_s [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_sc_slave]
set_property -dict [list CONFIG.NUM_SI {6} CONFIG.NUM_MI {4}] $sc_s

# ── 5. 添加 MIPI CSI-2 RX 子系统（4 路）─────────────────
for {set i 0} {$i < 4} {incr i} {
    set mipi [create_bd_cell -type ip \
        -vlnv xilinx.com:ip:mipi_csi2_rx_subsystem:5.1 \
        mipi_csi2_rx_${i}]
    set lanes [expr {$i < 2 ? 4 : 2}]  ;# CAM0/1 用4lane，CAM2/3用2lane
    set_property -dict [list \
        CONFIG.C_CSI_LANES       $lanes \
        CONFIG.C_PIXEL_FORMAT    "RAW10" \
        CONFIG.C_AXIS_TDATA_WIDTH 32 \
        CONFIG.C_MAX_PIXELS_PER_CLOCK 2 \
    ] $mipi
}

# ── 6. 添加 ISP Pipeline IP（4路）───────────────────────
for {set i 0} {$i < 4} {incr i} {
    create_bd_cell -type ip \
        -vlnv traffic_edge:hls:isp_pipeline:1.0 \
        isp_pipeline_$i
}

# ── 7. 添加 AXI VDMA（视频 DMA）─────────────────────────
set vdma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_vdma:6.3 axi_vdma_0]
set_property -dict [list \
    CONFIG.c_num_fstores {4} \
    CONFIG.c_s2mm_genlock_mode {0} \
    CONFIG.c_s2mm_linebuffer_depth {2048} \
    CONFIG.c_s2mm_max_burst_length {256} \
    CONFIG.c_use_s2mm_fsync {1} \
] $vdma

# ── 8. 添加 DPU IP ────────────────────────────────────────
# 注意：DPU IP 需要从 Vitis AI 安装目录导入
# 路径：$XILINX_VITIS/data/dpu/dpuv3/rtl/
set dpu [create_bd_cell -type ip -vlnv xilinx.com:ip:dpu:3.4 dpu_0]
set_property -dict [list \
    CONFIG.DPU_NUM    {1} \
    CONFIG.DPU_ARCH   {4096} \
    CONFIG.DPU_CLK_MHz {300} \
] $dpu

# ── 9. 添加 10GbE 以太网 IP ──────────────────────────────
set eth [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:xxv_ethernet:3.1 xxv_ethernet_0]
set_property -dict [list \
    CONFIG.LINE_RATE {10} \
    CONFIG.NUM_OF_CORES {1} \
    CONFIG.GT_REF_CLK_FREQ {156.25} \
] $eth

# ── 10. 添加 AXI CAN ─────────────────────────────────────
set can [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_can:2.1 axi_can_0]
set_property -dict [list \
    CONFIG.C_CAN_MODE {1} \
    CONFIG.C_BASEADDR {0xA0020000} \
    CONFIG.C_HIGHADDR {0xA002FFFF} \
] $can

# ── 11. 添加 OSD Overlay IP ─────────────────────────────
for {set i 0} {$i < 4} {incr i} {
    create_bd_cell -type ip \
        -vlnv traffic_edge:hls:osd_overlay:1.0 \
        osd_overlay_$i
}

# ── 12. 添加 AXI GPIO（GPS PPS + LED）────────────────────
set gpio [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_0]
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH  {8} \
    CONFIG.C_GPIO2_WIDTH {1} \
    CONFIG.C_IS_DUAL {1} \
    CONFIG.C_ALL_OUTPUTS {1} \
    CONFIG.C_ALL_INPUTS2 {1} \
] $gpio

# ── 13. 添加 AXI 中断控制器 ─────────────────────────────
set intc [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_intc:4.1 axi_intc_0]

# ── 14. 连接时钟与复位 ───────────────────────────────────
# 创建时钟复位辅助单元
set clk_rst [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:proc_sys_reset:5.0 proc_sys_reset_0]

connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] \
               [get_bd_pins proc_sys_reset_0/slowest_sync_clk]
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_resetn0] \
               [get_bd_pins proc_sys_reset_0/ext_reset_in]

# ── 15. 验证、生成、综合 ─────────────────────────────────
validate_bd_design
save_bd_design
generate_target all [get_files traffic_edge_bd.bd]

make_wrapper -files [get_files traffic_edge_bd.bd] -top
add_files -norecurse $build_dir/vivado/traffic_edge.gen/sources_1/bd/traffic_edge_bd/hdl/traffic_edge_bd_wrapper.v
set_property top traffic_edge_bd_wrapper [current_fileset]
update_compile_order -fileset sources_1

# 添加约束文件
add_files -fileset constrs_1 \
    [file normalize "[file dirname [info script]]/../constraints/timing.xdc"]
add_files -fileset constrs_1 \
    [file normalize "[file dirname [info script]]/../constraints/pinout.xdc"]

# 启动综合
launch_runs synth_1 -jobs [exec nproc]
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {
    error "Synthesis failed!"
}

# 启动实现
launch_runs impl_1 -to_step write_bitstream -jobs [exec nproc]
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    error "Implementation failed!"
}

# 检查时序
open_run impl_1
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1]]
puts "WNS = $wns ns"
if {$wns < 0} {
    puts "WARNING: Timing NOT met! WNS = $wns ns"
} else {
    puts "Timing met. WNS = $wns ns"
}

# 生成时序报告
report_timing_summary -file $build_dir/timing_summary.rpt -warn_on_violation

puts "=== Vivado Build Complete ==="
puts "Bitstream: $build_dir/vivado/traffic_edge.runs/impl_1/traffic_edge_bd_wrapper.bit"
