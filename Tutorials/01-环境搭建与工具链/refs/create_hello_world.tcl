# ============================================================
# ZCU102 Hello World - Vivado Tcl 脚本
# 参考：Embedded-Design-Tutorials/docs/Getting_Started/ZynqMPSoC-EDT/
# 工具版本：Vivado 2023.1
# ============================================================

# 创建工程
create_project hello_zcu102 ./hello_zcu102 -part xczu9eg-ffvb1156-2-e -force
set_property board_part xilinx.com:zcu102:part0:3.4 [current_project]

# 创建 Block Design
create_bd_design "system"
update_compile_order -fileset sources_1

# 添加 Zynq UltraScale+ MPSoC PS
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0

# 应用 ZCU102 板卡预设（自动配置 DDR、UART、ETH 等）
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} [get_bd_cells zynq_ultra_ps_e_0]

# 确保 UART0 启用（用于 Hello World 输出）
set_property -dict [list \
    CONFIG.PSU__UART0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__UART0__PERIPHERAL__IO    {MIO 18 .. 19} \
] [get_bd_cells zynq_ultra_ps_e_0]

# 验证 BD
validate_bd_design

# 生成 HDL Wrapper
make_wrapper -files [get_files system.bd] -top
add_files -norecurse \
    ./hello_zcu102/hello_zcu102.gen/sources_1/bd/system/hdl/system_wrapper.v
set_property top system_wrapper [current_fileset]

# 综合、实现、生成比特流
launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

# 导出硬件平台 XSA
write_hw_platform -fixed -force -include_bit \
    -file ./hello_zcu102/zcu102_hello.xsa

puts "✓ XSA 已生成：./hello_zcu102/zcu102_hello.xsa"
puts "  下一步：在 Vitis 中导入 XSA，创建 Hello World 应用"
