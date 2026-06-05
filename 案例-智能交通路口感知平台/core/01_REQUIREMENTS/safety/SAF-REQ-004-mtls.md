---
id: SAF-REQ-004
title: mTLS 双向认证
type: requirement-safety
status: approved
owner: security-team
version: 1.0
traces: { up: [STK-REQ-004], down: [DES-ARCH-010, MOD-C-CLOUD] }
tags: [safety, security, tls]
verification_method: inspection
---

# SAF-REQ-004: mTLS 双向认证

## 描述
设备与云端的 MQTT/gRPC 连接均使用 mTLS（双向 TLS 认证）。

## 证书层次
- Root CA（HSM 离线保存）
  - Intermediate CA（在线自动签发）
    - Device Cert（绑定 device_id，有效期 2 年）

## 验收准则
1. 客户端证书校验：CA 链 + CN
2. 服务端证书校验：CA 链 + 域名
3. 证书到期前 30 天主动告警

## 验证
- TC-SAF-004: 错误证书 → 拒绝连接
