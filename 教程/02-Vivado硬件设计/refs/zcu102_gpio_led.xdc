# ============================================================
# ZCU102 用户 LED 引脚约束
# 参考：UG1182 ZCU102 Board User Guide, Table 2-3
# GPIO_LED[0:7] - DS26..DS33 (LVCMOS33, MIO 0-7 或 PL 扩展)
#
# 注意：若使用 PL GPIO（非 PS MIO），使用以下约束
# 若使用 PS MIO，直接在 PS Block 中配置，无需 XDC
# ============================================================

# ZCU102 DS26-DS33（8个用户LED，来自 Schematic Rev1.0）
set_property PACKAGE_PIN AG14 [get_ports {gpio_led_tri_o[0]}]
set_property PACKAGE_PIN AF13 [get_ports {gpio_led_tri_o[1]}]
set_property PACKAGE_PIN AE13 [get_ports {gpio_led_tri_o[2]}]
set_property PACKAGE_PIN AJ14 [get_ports {gpio_led_tri_o[3]}]
set_property PACKAGE_PIN AJ15 [get_ports {gpio_led_tri_o[4]}]
set_property PACKAGE_PIN AH13 [get_ports {gpio_led_tri_o[5]}]
set_property PACKAGE_PIN AH14 [get_ports {gpio_led_tri_o[6]}]
set_property PACKAGE_PIN AL12 [get_ports {gpio_led_tri_o[7]}]

set_property IOSTANDARD LVCMOS33 [get_ports {gpio_led_tri_o[*]}]

# ZCU102 用户拨码开关 SW19（4-bit）
# set_property PACKAGE_PIN A17 [get_ports {gpio_sw_tri_i[0]}]
# set_property PACKAGE_PIN A16 [get_ports {gpio_sw_tri_i[1]}]
# set_property PACKAGE_PIN B16 [get_ports {gpio_sw_tri_i[2]}]
# set_property PACKAGE_PIN B15 [get_ports {gpio_sw_tri_i[3]}]
# set_property IOSTANDARD LVCMOS18 [get_ports {gpio_sw_tri_i[*]}]

# ZCU102 用户按键 SW4-SW7（4个）
# set_property PACKAGE_PIN B13 [get_ports {gpio_btn_tri_i[0]}]
# set_property PACKAGE_PIN C13 [get_ports {gpio_btn_tri_i[1]}]
# set_property PACKAGE_PIN D14 [get_ports {gpio_btn_tri_i[2]}]
# set_property PACKAGE_PIN D13 [get_ports {gpio_btn_tri_i[3]}]
# set_property IOSTANDARD LVCMOS18 [get_ports {gpio_btn_tri_i[*]}]
