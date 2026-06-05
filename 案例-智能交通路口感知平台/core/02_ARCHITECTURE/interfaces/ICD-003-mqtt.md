---
id: ICD-003
title: MQTT 主题与数据 schema
type: interface-control
status: approved
owner: backend-team
version: 1.0
traces: { up: [SYS-REQ-007, STK-REQ-004, SAF-REQ-004], down: [MOD-C-CLOUD] }
tags: [interface, mqtt, cloud]
---

# ICD-003: MQTT 主题与数据 schema

## 主题命名规范

```
traffic/edge/{city}/{district}/{device_id}/{data_type}
```

## 主题清单

| Topic | 方向 | QoS | 频率 |
|-------|------|-----|------|
| `traffic/edge/{city}/{district}/{device_id}/stats` | →云 | 1 | 1/min |
| `traffic/edge/{city}/{district}/{device_id}/events` | →云 | 1 | 实时 |
| `traffic/edge/{city}/{district}/{device_id}/status` | →云 | 1 | 1/10s |
| `traffic/edge/{city}/{district}/{device_id}/signal` | →云 | 1 | 事件触发 |
| `traffic/cloud/{device_id}/cmd` | 云→端 | 1 | 实时 |
| `traffic/cloud/{device_id}/config` | 云→端 | 1 | 事件触发 |

## 流量统计 stats 格式

```json
{
  "v": 2,
  "device_id": "edge001",
  "ts": 1700000000000,
  "period_s": 60,
  "channels": [
    {
      "ch": 0,
      "direction": "north_south_thru",
      "counts": {
        "car": 42, "truck": 5, "bus": 2, "person": 18,
        "motorcycle": 7, "bicycle": 3
      },
      "speed_avg_kmh": 38.5,
      "speed_p85_kmh": 52.0,
      "queue_max_m": 45.0,
      "occupancy_pct": 23.4
    }
  ]
}
```

## 事件 events 格式

```json
{
  "v": 2,
  "event_id": "evt_edge001_1700000123_0042",
  "device_id": "edge001",
  "ts": 1700000123456,
  "type": "RED_LIGHT_VIOLATION",
  "channel": 2,
  "plate": "京A12345",
  "plate_conf": 0.97,
  "vehicle_class": "car",
  "speed_kmh": 45.2,
  "evidence": {
    "image_url": "https://oss.example.com/evidence/2024/...",
    "video_url": "https://oss.example.com/clips/2024/..."
  },
  "location": {
    "lat": 39.9042, "lon": 116.4074,
    "intersection_id": "bj_cy_001"
  },
  "signal_state": "RED",
  "track_id": 157
}
```

## TLS / mTLS

- TLS 1.3 强制
- 客户端证书绑定 device_id
- 服务端证书 CN 校验
