---
id: VP-001
title: 闭环仿真验证
type: verification-policy
status: approved
owner: qa-team
version: 1.0
traces: { up: [], down: [] }
tags: [verification, simulation]
---

# VP-001: 闭环仿真验证

## 目标
在无 FPGA 比特流、无真实摄像头、无 CAN 线的情况下，**在 PC 或 ZCU102 A53 上**
完成端到端业务逻辑的闭环验证。

## 工具与位置
- 仿真代码：`core/03_ALGORITHM/simulation/`
- 集成测试：`core/05_VERIFICATION/integration/`
- 入口脚本：`core/06_INTEGRATION/ci-cd/run_full_sim.sh`

## 范围
覆盖：
- 场景生成 → 检测 → 跟踪 → 事件检测
- 信号灯 FSM（Webster 自适应）
- MQTT 数据上报
- vcan0 虚拟 CAN

不覆盖：
- DPU 真实推理（用 mock_detector 替代）
- PL 硬件时序
- 真实摄像头 ISP

## 验收准则
1. 全流程 FPS ≥ 30（fast 模式）
2. 6 个核心测试 100% 通过
3. 可复现性：相同种子输出一致

## 自动化
`sw-htf verify sim` → pre-merge gate
