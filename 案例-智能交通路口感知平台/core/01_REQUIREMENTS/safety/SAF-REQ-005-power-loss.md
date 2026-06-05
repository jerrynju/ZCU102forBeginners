---
id: SAF-REQ-005
title: 掉电数据不丢失
type: requirement-safety
status: approved
owner: backend-team
version: 1.0
traces: { up: [STK-REQ-002], down: [DES-ARCH-010, MOD-C-OFFLINE] }
tags: [safety, persistence, power-loss]
verification_method: fault_injection
---

# SAF-REQ-005: 掉电数据不丢失

## 描述
异常掉电后，设备恢复后应能：
1. 启动到工作状态
2. 离线缓存数据不丢失
3. 配置文件不损坏

## 措施
- eMMC 启用 ext4 同步写（data=journal）
- 关键数据 WAL 模式
- 掉电检测 + 紧急 flush（< 50ms）

## 验收准则
1. 拔电源 1s 后恢复 → 数据完整
2. 拔电源 24h 后恢复 → 离线缓存可上传

## 验证
- TC-SAF-005: 拔电 → 重启 → 数据完整性
