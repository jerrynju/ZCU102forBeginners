# Vitis HLS 综合脚本 - ISP Pipeline
# 运行方式：vitis_hls -f run_hls.tcl

# ── 工程设置 ──────────────────────────────────────────────
open_project isp_pipeline_prj
set_top isp_pipeline
open_solution "solution1" -flow_target vivado

# 目标器件：ZCU102 (xczu9eg-ffvb1156-2-e)
set_part {xczu9eg-ffvb1156-2-e}
create_clock -period 4 -name default   ;# 250 MHz

# ── 源文件 ────────────────────────────────────────────────
add_files isp_pipeline.cpp -cflags "-I. -std=c++14"
add_files -tb isp_tb.cpp   -cflags "-I. -std=c++14" -csimflags "-Wno-unknown-pragmas"

# ── C 仿真 ────────────────────────────────────────────────
csim_design -clean

# ── HLS 综合 ──────────────────────────────────────────────
csynth_design

# ── 综合后仿真（与 RTL 对比）────────────────────────────────
cosim_design -rtl verilog -tool xsim -trace_level all

# ── 导出 IP（供 Vivado 使用）────────────────────────────────
export_design -format ip_catalog \
    -description "4K→1080p ISP Pipeline: BLC/Demosaic/WB/Resize/Gamma/NV12" \
    -display_name "Traffic ISP Pipeline v1.0" \
    -vendor "traffic_edge" \
    -version "1.0" \
    -output ../../ip_repo/isp_pipeline_v1.0

puts "=== ISP Pipeline HLS Build Complete ==="
puts "IP exported to: ../../ip_repo/isp_pipeline_v1.0"

# ── 综合报告摘要 ──────────────────────────────────────────
# 预期资源（250 MHz，xczu9eg）：
#   LUT:  ~14,000
#   FF:   ~12,000
#   BRAM: ~18 (行缓冲区)
#   DSP:  ~40 (缩放、颜色矩阵运算)
#   II:   1 (流水线间隔)
#   延迟: 约 4K 帧时间 + 少量流水线延迟
