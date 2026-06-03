# ============================================================
# ZCU102 AXI GPIO 实验 - Vivado Tcl 脚本
# 参考：Vivado-Design-Tutorials/General/IP_Integrator/Designing_in_IPI/
# 工具版本：Vivado 2023.1
# ============================================================

set project_name "lab2_gpio"
set project_dir  "./${project_name}"
set bd_name      "system"
set part         "xczu9eg-ffvb1156-2-e"
set board_part   "xilinx.com:zcu102:part0:3.4"

# ── 创建工程 ──────────────────────────────────────────────
create_project $project_name $project_dir -part $part -force
set_property board_part $board_part [current_project]

# ── Block Design ──────────────────────────────────────────
create_bd_design $bd_name
update_compile_order -fileset sources_1

# ── Zynq UltraScale+ PS ──────────────────────────────────
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} [get_bd_cells zynq_ultra_ps_e_0]

# 确保 M_AXI_HPM0_FPD 高性能 AXI 主端口已启用（用于连接 PL IP）
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
] [get_bd_cells zynq_ultra_ps_e_0]

# ── AXI GPIO ──────────────────────────────────────────────
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_0
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH  {8} \
    CONFIG.C_ALL_OUTPUTS {1} \
    CONFIG.C_GPIO_DEFAULT_TRI_MASK {0x00000000} \
] [get_bd_cells axi_gpio_0]

# ── 自动连接 AXI ──────────────────────────────────────────
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config {Master "/zynq_ultra_ps_e_0/M_AXI_HPM0_FPD" \
             Slave  "/axi_gpio_0/S_AXI" \
             intc_ip "New AXI Interconnect" \
             Clk_xbar "Auto" Clk_master "Auto" Clk_slave "Auto"} \
    [get_bd_intf_pins axi_gpio_0/S_AXI]

# ── 创建外部 LED 端口 ──────────────────────────────────────
make_bd_intf_pins_external [get_bd_intf_pins axi_gpio_0/GPIO]
set_property name {gpio_led} [get_bd_intf_ports GPIO_0]

# ── 验证与生成输出 ─────────────────────────────────────────
validate_bd_design
save_bd_design

generate_target all [get_files ${project_dir}/${project_name}.srcs/sources_1/bd/${bd_name}/${bd_name}.bd]

make_wrapper -files [get_files ${project_dir}/${project_name}.srcs/sources_1/bd/${bd_name}/${bd_name}.bd] -top
add_files -norecurse \
    ${project_dir}/${project_name}.gen/sources_1/bd/${bd_name}/hdl/${bd_name}_wrapper.v

# ── 综合与实现 ─────────────────────────────────────────────
launch_runs synth_1 -jobs 8
wait_on_run synth_1

# 在实现前添加约束
add_files -fileset constrs_1 -norecurse [file normalize "./refs/zcu102_gpio_led.xdc"]
set_property PROCESSING_ORDER LATE [get_files ./refs/zcu102_gpio_led.xdc]

launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

# ── 导出 XSA ──────────────────────────────────────────────
write_hw_platform -fixed -force -include_bit \
    -file ${project_dir}/zcu102_gpio.xsa
puts "✓ XSA 导出完成：${project_dir}/zcu102_gpio.xsa"
