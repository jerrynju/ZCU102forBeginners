# 问题跟踪（ISS）

> 每条问题一份文本文件，便于 git 追溯、链接到代码/需求、状态机驱动。

## 模板

```markdown
---
id: ISS-XXX
title: 一句话标题
type: issue
status: open              # open | triaged | in-progress | resolved | closed
severity: S2               # S1 (阻断) | S2 (严重) | S3 (一般) | S4 (低)
owner: zhang.san
created: 2026-MM-DD
updated: 2026-MM-DD
traces:
  up: [SYS-REQ-XXX, DES-ARCH-XXX]
  down: [MOD-C-XXX]
tags: [bug, performance]
---

# ISS-XXX: 标题

## 现象
（可复现步骤、影响范围）

## 根因
（定位结论）

## 修复
（PR 链接、commit hash）

## 验证
- [ ] TC-XXX-001 重新通过
- [ ] regression 无新问题
```

## 列表

| ID | 标题 | 严重度 | 状态 |
|----|------|--------|------|
| _（暂无开放问题）_ | | | |
