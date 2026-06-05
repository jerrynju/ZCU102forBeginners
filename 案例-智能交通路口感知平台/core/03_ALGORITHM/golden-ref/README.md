# 黄金参考（Golden Reference）

> 闭环仿真的固定基准；任何漂移必须走 ADR 流程（参见 [07_FEEDBACK/adr/](../07_FEEDBACK/adr/)）。

## sim_baseline.json

由 [03_ALGORITHM/simulation/src/traffic_sim.py](../../03_ALGORITHM/simulation/src/traffic_sim.py) 持续运行 600 帧（seed=42）生成：

```json
{
  "version": "1.0.0",
  "seed": 42,
  "frames": 600,
  "fps": 38.5,
  "events": {
    "RED_LIGHT_VIOLATION": 12,
    "WRONG_WAY": 3,
    "ILLEGAL_PARKING": 5,
    "PEDESTRIAN_JAYWALK": 8
  },
  "tracking": {
    "MOTA": 0.762,
    "IDF1": 0.703,
    "IDS": 14
  },
  "signal_fsm": {
    "phase_transitions": 30,
    "avg_cycle_s": 138,
    "webster_y": 0.42
  },
  "kpi": {
    "detection_mAP50": 0.885,
    "lpr_accuracy": 0.953
  }
}
```

## 使用方法

```bash
# 跑当前仿真
python3 03_ALGORITHM/simulation/src/traffic_sim.py --frames 600 --seed 42 \
    --output /tmp/run.json

# 与黄金参考 diff
python3 tools/sw_hw_toolflow/cli/verify.py sim --golden 03_ALGORITHM/golden-ref/sim_baseline.json
```

## 刷新流程

1. 评审需要：算法变更、场景参数变更
2. 跑 10 次取 P50
3. 写入本目录
4. 更新追溯矩阵 `core/00_MANIFEST/metrics.yml`
