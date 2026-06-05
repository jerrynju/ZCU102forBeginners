---
id: SAF-REQ-001
title: 安全启动链 RSA-4096
type: requirement-safety
status: verified
owner: security-team
version: 1.0
traces: { up: [STK-REQ-002], down: [SYS-REQ-008, DES-ARCH-001] }
tags: [safety, security, boot]
verification_method: inspection
---

# SAF-REQ-001: 安全启动链 RSA-4096

## 描述
完整可信启动链，每一级都验证下一级。

## 信任链
1. BootROM（芯片内置 ROM，验证 FSBL）
2. FSBL（验证 PL bitstream + ATF + U-Boot）
3. U-Boot（验证 Linux kernel）
4. Linux（IMA + dm-verity 保护 rootfs）

## 密钥管理
- RSA-4096 密钥对：私钥离线 HSM 保存
- 公钥哈希烧入 eFUSE
- 比特流 AES-256 密钥：烧入 eFUSE/BBRAM

## 验收准则
1. 篡改任何环节 → 锁死
2. 量产关闭 JTAG
3. 密钥全生命周期 HSM 保护

## 验证
- TC-SEC-001: 篡改 bitstream → 拒绝启动
