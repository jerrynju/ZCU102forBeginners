---
id: TC-SIM-001
title: 闭环仿真 (基础)
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [VP-001]
  down: [ALG-TRACK-001, MOD-C-EVENT, MOD-C-SIG-FSM]
tags: [test, simulation, regression]
---

# TC-SIM-001: 闭环仿真（基础）

## 目的
在无硬件依赖的 PC 上，验证业务逻辑闭环。

## 入口
```bash
python3 core/03_ALGORITHM/simulation/src/traffic_sim.py --frames 600 --seed 42
```

## 步骤

1. 启动仿真
2. 运行 600 帧
3. 检查事件检测率
4. 检查信号灯相位切换

## 通过条件
- 仿真 FPS ≥ 30
- 闯红灯事件 100% 检出
- 信号灯 6 步相位顺序正确
- 跟踪 ID 稳定

## 回归基线
- `core/03_ALGORITHM/golden-ref/sim_baseline.json`
