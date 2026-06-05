---
id: VP-003
title: 工厂量产测试
type: verification-policy
status: approved
owner: qa-team
version: 1.0
traces: { up: [], down: [] }
tags: [verification, factory, mass-production]
---

# VP-003: 工厂量产测试（FCT）

## 目标
量产阶段每台设备出厂前的功能测试。

## 工具与位置
- 工厂测试脚本：`core/06_INTEGRATION/ci-cd/factory_test.py`
- 测试设备：MES 系统对接

## 流程

1. 上电检测（< 5s）
2. JTAG 边界扫描（< 30s）
3. 固件烧录（< 3min）
4. 功能测试（< 5min）：DPU / 10GbE / CAN / PPS / 温度
5. 老化测试（8h，可并行多台）
6. 最终验收

## 验收准则
- 100% 测试项通过
- 测试结果自动上传 MES
- 不良品打标隔离

## 自动化
`sw-htf verify factory <device_ip> <device_id>`
