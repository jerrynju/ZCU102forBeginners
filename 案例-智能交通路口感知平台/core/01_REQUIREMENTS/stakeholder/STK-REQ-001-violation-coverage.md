---
id: STK-REQ-001
title: 城市路口违章检测全覆盖
type: requirement-stakeholder
status: approved
owner: customer-success
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: []
  down: [SYS-REQ-002, SYS-REQ-003, SYS-REQ-005, SYS-REQ-006]
tags: [stakeholder, violation-detection, core-business]
---

# STK-REQ-001: 城市路口违章检测全覆盖

## 来源
城市交通管理局/智慧城市集成商招标文件、多次客户访谈

## 描述
在城市路口部署后，EdgeVision-T1 应能 **100% 检测** 路口监控画面内的以下违章行为：
- 闯红灯
- 逆行
- 违规停车
- 占用公交车道
- 行人闯红灯

违章检出后应在 **< 1s** 内将证据（含车牌、违章时间、违章类型）上报云平台。

## 验收准则
1. 4 路摄像头覆盖路口 4 个方向，**画面重叠区不出现重复上报**
2. 闯红灯检出率 ≥ 95%（白天）/ ≥ 85%（夜晚）
3. 违章证据包含：高分辨率图片、车牌识别结果、时间戳、信号灯状态
4. 云端 ACK 延迟 < 1s

## 干系人
- 决策：城市交通管理局采购
- 验收：交通局信息中心
- 使用：交警执法系统

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | zhang.san | 初始 |
