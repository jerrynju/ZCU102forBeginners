---
id: TC-OTA-001
title: OTA 升级及回滚
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-009]
  down: [MOD-C-OTA]
tags: [test, ota, update]
---

# TC-OTA-001: OTA 升级及回滚

## 目的
验证 OTA 升级的正常升级和失败回滚。

## 入口
- 测试脚本：[`06_INTEGRATION/ci-cd/run_ota_test.py`](../../06_INTEGRATION/ci-cd/run_ota_test.py)

## 步骤

### 子用例 A：正常升级
1. 准备 swu 包
2. 推送到设备
3. 设备下载 + 验签 + 切换
4. 重启
5. 验证新版本

### 子用例 B：升级失败
1. 注入签名错误 swu
2. 推送到设备
3. 设备应拒绝升级
4. 业务不中断

### 子用例 C：升级中断
1. 升级中拔电
2. 重启
3. 应启动到旧版本

## 通过条件
- A：升级完成，业务 < 1s 中断
- B：拒绝升级，无业务中断
- C：自动回滚，业务不中断

## 失败处理
1. 升级后启动失败：检查 U-Boot 切换
2. 验签失败：检查证书
3. 回滚失败：检查 boot_count
