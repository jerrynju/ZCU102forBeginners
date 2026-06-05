---
id: SYS-REQ-009
title: OTA 远程升级
type: requirement-system
status: approved
owner: ota-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P1
traces:
  up: [STK-REQ-002]
  down: [DES-ARCH-010, MOD-C-OTA, TC-OTA-001]
tags: [system, ota, update]
verification_method: integration_test
---

# SYS-REQ-009: OTA 远程升级

## 描述
支持远程升级以下组件，**不影响业务**：
- Linux 内核 + 设备树
- 根文件系统（应用层）
- FPGA bitstream
- R5 firmware

## 验收准则
1. A/B 分区升级
2. 升级失败自动回滚（3 次启动失败触发）
3. 断点续传
4. 升级包签名验证（RSA-2048）
5. 升级过程不断业务（视频流可断 < 1s）

## 验证
- TC-OTA-001: 正常升级 + 启动
- TC-OTA-002: 升级中掉电 → 启动旧版本
- TC-OTA-003: 升级包签名错误 → 拒绝升级

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | li.si | 初始 |
