---
id: TC-CAM-001
title: 4 路 4K 摄像头长稳测试
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-001]
  down: [MOD-HLS-ISP, MOD-C-FRAME-MGR]
tags: [test, video, hardware]
---

# TC-CAM-001: 4 路 4K 摄像头长稳测试

## 目的
验证 4 路 4K@30fps 摄像头在 24 小时连续运行下无丢帧。

## 入口
- 自动化：[`06_INTEGRATION/ci-cd/run_cam_test.sh`](../../06_INTEGRATION/ci-cd/run_cam_test.sh)
- 手动：在 ZCU102 设备上执行 `v4l2_test --device /dev/video0 --count 864000`

## 前置条件
- 4× IMX415 摄像头已连接
- FPGA 比特流已加载
- 内核模块 `xilinx_vdma` 已加载

## 步骤

1. 启动采集
2. 抓取 4 路帧
3. 统计丢帧数、帧间隔
4. 持续 24h
5. 拉取统计

## 通过条件
- 4 路均无丢帧（0 帧丢）
- 帧间隔 P95 偏差 < 5ms
- 帧率 ≥ 28fps
- ISP 输出 NV12 格式正确
- 4 路过曝/欠曝场景切换无 crash

## 失败处理
1. 检查 MIPI 物理连接
2. 拉偏 ISP 时钟
3. 查看内核日志 OOPS
4. 抓取 VDMA 寄存器状态
