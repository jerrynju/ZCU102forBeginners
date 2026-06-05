---
id: SYS-REQ-007
title: 云端上报 < 500ms
type: requirement-system
status: verified
owner: backend-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-004]
  down: [DES-ARCH-010, ICD-003, IF-REQ-002, MOD-C-CLOUD, MOD-C-OFFLINE, TC-CLOUD-001]
tags: [system, cloud, network]
verification_method: integration_test
---

# SYS-REQ-007: 云端上报 < 500ms

## 描述
违章事件从设备检出到云端 ACK 的端到端延迟 < 500ms。

## 链路
事件检出 (PS) → JSON 序列化 → MQTT publish (QoS 1) → TLS 加密 → 10GbE → 云端 Broker → 业务 ACK

## 验收准则
1. P95 延迟 < 500ms
2. P99 延迟 < 1s
3. 掉线自动重连（指数退避）
4. 离线 24h 重连后能补传所有数据

## 验证
- TC-CLOUD-001: 1000 次事件延迟分布
- TC-CLOUD-002: 断网 1h 重连补传测试
- TC-CLOUD-003: 4G 备份链路切换测试

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | li.si | 初始 |
