---
id: DES-ARCH-010
title: 离线缓存与重传
type: design-architecture
status: approved
owner: backend-team
version: 1.0
traces: { up: [SYS-REQ-007, SYS-REQ-009, SYS-REQ-010, SAF-REQ-004, SAF-REQ-005], down: [MOD-C-OFFLINE, MOD-C-OTA] }
tags: [architecture, offline, ota]
---

# DES-ARCH-010: 离线缓存与重传

## 离线缓存

### 存储
- SQLite 数据库（`/data/offline_cache.db`）
- 表结构：`pending_msgs (id, topic, payload, qos, created_at)`
- 容量限制：4GB（自动滚动删除最旧数据）

### 写策略
- 网络可用时：直发 MQTT，失败时落 SQLite
- 网络不可用：直写 SQLite

### 读策略（重连后）
1. 启动 `flush_to_mqtt` 线程
2. 批量读取 50 条/批
3. 每条间隔 10ms（限速 1MB/s）
4. 发送成功 → 删除记录

## 重连策略

- 指数退避：1s, 2s, 4s, 8s, 16s, 30s（封顶）
- 心跳超时 60s → 触发重连
- 链路切换：10GbE → 4G（健康检查 30s）

## 4G 备份

- 主链路（10GbE）metric 100
- 备用链路（4G）metric 200
- 主链路连续 3 次 ping 失败 → 切到 4G
- 通知应用层发布 `system/link_failover`

## OTA 升级

### A/B 分区方案

| 分区 | 大小 | 用途 |
|------|------|------|
| Boot0 | 4MB | BOOT_A.BIN |
| Boot1 | 4MB | BOOT_B.BIN |
| p1 | 512MB | /boot_a |
| p2 | 512MB | /boot_b |
| p3 | 8GB | /rootfs_a |
| p4 | 8GB | /rootfs_b |
| p5 | 4GB | /data |
| p6 | 剩余 | /tmp_ota |

### 升级流程
1. 下载 swu 包到 /tmp_ota
2. 验签（RSA-2048）
3. 写入非活跃分区
4. post_install.sh 切换 U-Boot env
5. 重启
6. 启动计数 +1（3 次失败自动回滚）

## 验证
- TC-CLOUD-002: 断网 1h 重连补传
- TC-OTA-001: 正常升级
- TC-OTA-002: 升级失败回滚
