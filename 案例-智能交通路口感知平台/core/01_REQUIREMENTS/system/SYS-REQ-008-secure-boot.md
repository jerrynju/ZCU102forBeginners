---
id: SYS-REQ-008
title: 安全启动链
type: requirement-system
status: verified
owner: security-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-002]
  down: [DES-ARCH-001, SAF-REQ-001, TC-SEC-001]
tags: [system, security, boot]
verification_method: inspection
---

# SYS-REQ-008: 安全启动链

## 描述
设备上电后必须建立一条 **不可绕过** 的信任链：
BootROM → FSBL → PL bitstream + ATF → U-Boot → Kernel → rootfs (dm-verity) → app

## 验收准则
1. FSBL RSA-4096 签名验证
2. PL bitstream AES-256 GCM 加密
3. eFUSE 烧写 RSA 公钥哈希
4. 量产关闭 JTAG
5. 任意环节失败 → 锁死

## 验证
- TC-SEC-001: 篡改 bitstream → 拒绝启动
- TC-SEC-002: 篡改 kernel → 拒绝启动
- TC-SEC-003: 篡改 rootfs → dm-verity I/O 错误

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | sun.jing | 初始 |
