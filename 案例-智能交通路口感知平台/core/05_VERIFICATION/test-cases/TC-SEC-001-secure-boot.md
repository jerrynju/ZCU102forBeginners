---
id: TC-SEC-001
title: 安全启动链验证
type: test-case
status: approved
owner: security-team
version: 1.0
traces:
  up: [SYS-REQ-008, SAF-REQ-001]
  down: []
tags: [test, security, boot]
---

# TC-SEC-001: 安全启动链验证

## 目的
验证安全启动链在任意环节篡改时均能拒绝启动。

## 入口
- 工厂脚本：[`06_INTEGRATION/ci-cd/factory_test.py`](../../06_INTEGRATION/ci-cd/factory_test.py) --test sec

## 步骤

1. 启动设备到工作状态
2. 注入篡改（任意环节）：FSBL / bitstream / U-Boot / kernel / rootfs
3. 重启设备
4. 观察：应锁定、不进入业务

## 通过条件
- 篡改 FSBL → 锁定
- 篡改 bitstream → 锁定
- 篡改 U-Boot → 锁定
- 篡改 kernel → dm-verity I/O 错误
- 篡改 rootfs → dm-verity I/O 错误
- 篡改设备树 → 锁定

## 失败处理
1. 启动通过：检查签名链
2. 异常崩溃：检查 WDT
