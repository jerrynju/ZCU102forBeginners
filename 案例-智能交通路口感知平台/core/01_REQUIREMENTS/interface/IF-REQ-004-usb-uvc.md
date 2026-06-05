---
id: IF-REQ-004
title: USB3.0 UVC 摄像头
type: requirement-interface
status: approved
owner: backend-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, MOD-C-UVC-DRV] }
tags: [interface, usb, video]
---

# IF-REQ-004: USB3.0 UVC 摄像头（备用）

## 描述
1 路 USB3.0 UVC 接口，可热插拔作为备用摄像头。

## 规格
- 协议：USB Video Class (UVC) 1.5
- 速率：USB 3.0 SuperSpeed (5 Gbps)
- 格式：MJPEG / YUY2
- 分辨率：1080p@30fps

## 验收准则
1. 热插拔不重启
2. /dev/video4 设备节点自动创建

## 验证
- TC-IF-USB-001: 拔插测试
