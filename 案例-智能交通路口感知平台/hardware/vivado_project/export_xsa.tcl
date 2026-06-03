# 导出 XSA 硬件描述文件（供 PetaLinux 使用）
# 运行方式：vivado -mode batch -source export_xsa.tcl -tclargs /path/to/build_dir

set build_dir [lindex $argv 0]
if {$build_dir eq ""} { set build_dir "./build_output" }

open_project $build_dir/vivado/traffic_edge.xpr

open_run impl_1

write_hw_platform -fixed -include_bit -force \
    -file $build_dir/traffic_edge.xsa

puts "XSA exported to: $build_dir/traffic_edge.xsa"
close_project
