# Vitis HLS 综合脚本 - OSD Overlay IP
open_project osd_overlay_prj
set_top osd_overlay
open_solution "solution1" -flow_target vivado

set_part {xczu9eg-ffvb1156-2-e}
create_clock -period 4 -name default   ;# 250 MHz

add_files osd_overlay.cpp -cflags "-I. -std=c++14"

csim_design -clean
csynth_design

export_design -format ip_catalog \
    -description "Real-time OSD bounding-box and text overlay for 1080p video" \
    -display_name "Traffic OSD Overlay v1.0" \
    -vendor "traffic_edge" \
    -version "1.0" \
    -output ../../ip_repo/osd_overlay_v1.0

puts "=== OSD Overlay HLS Build Complete ==="
# 预期资源 @250MHz：LUT ~9,000  FF ~7,000  BRAM ~0  DSP ~0
