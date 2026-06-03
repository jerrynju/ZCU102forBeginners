# 阶段 7 参考资源链接

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG576 | UltraScale Architecture GTH Transceivers User Guide | GTH 收发器完整手册（SerDes 原理/时钟/均衡）|
| PG203 | 100G Ethernet Subsystem Product Guide | CMAC 10/25/100G IP |
| PG232 | MIPI CSI-2 RX Subsystem Product Guide | MIPI 摄像头接收 IP |
| PG023 | AXI CAN Product Guide | AXI CAN IP（PS 内置）|
| PG213 | UltraScale+ PCIe Product Guide | PCIe Gen3×4 端点 |
| UG1085 Chap.29 | TRM: PCIe Controller | PS PCIe 配置 |
| UG585 Chap.16 | Zynq-7000 GEM (PS-GEM 原理类似) | PS-GEM 参考 |

## GTH 参考时钟（ZCU102）

```
ZCU102 GTH 参考时钟来源（见 UG1182 Table 2-8）：
- Y1: 300 MHz (GTH Bank 226, 用于 DDR4)
- Y2: 27 MHz  (GTH Bank 225)
- U13: 156.25 MHz (GTH Bank 230, 用于 10GbE SFP+)
- J15: 100 MHz (GTH Bank 228, 用于 PCIe)
```

## MIPI 摄像头模块

ZCU102 FMC HPC 接口（J5）支持连接 MIPI 摄像头扩展板：
- **Digilent PCAM 5C** (5MP OV5647, MIPI CSI-2 2-lane): https://digilent.com/reference/add-ons/pcam-5c/start
- **Leopard Imaging LI-IMX274MIPI-FMC** (4K, 4-lane): https://leopardimaging.com/
- 参考设计: https://github.com/Xilinx/MIPI_FMC

## 关键 IP 和教程

### 10GbE SFP+（CMAC）
- SFP+ 接口: J28（Single Lane）
- GTH Lane: X0Y8（Bank 230）
- 参考时钟: 156.25 MHz（U13）
- 参考设计: https://www.xilinx.com/products/intellectual-property/cmac_usplus.html

### AXI CAN
- ZCU102 PS 内置 2×CAN（CAN0: MIO 38/39, CAN1: MIO 40/41）
- 连接器: J16/J17（通过 SN65HVD230 CAN 收发器）
- SocketCAN 文档: https://www.kernel.org/doc/html/latest/networking/can.html
- canutils: `sudo apt install can-utils`

### PCIe
- 连接器: J2（PCIe Gen3×4 边缘连接器）
- GTH: Bank 228（X0Y4-7）
- 参考时钟: 100 MHz（J15）

## 实用工具

```bash
# CAN 工具安装
sudo apt install can-utils

# 常用 CAN 命令
ip link set can0 type can bitrate 500000 loopback on  # 自环测试
cansend can0 101#DEADBEEF00000000
candump -l any                                         # 记录所有帧到文件
canplayer -I candump.log                               # 回放日志

# 网络接口测试
iperf3 -s                   # 服务器端
iperf3 -c 192.168.1.100 -t 30 -P 4  # 客户端，4并发，30秒
```
