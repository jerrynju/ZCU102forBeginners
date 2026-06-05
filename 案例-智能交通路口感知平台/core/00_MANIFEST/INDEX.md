# 文档全索引（自动生成）

> 由 `tools/sw_hw_toolflow/core/build_index.py` 扫描 `core/` 自动生成  
> 末次生成：2026-06-04

---

## 0. 入口

- [README.md](README.md) — 项目入口
- [ARCHITECTURE.md](../../ARCHITECTURE.md) — 架构宪法
- [CHANGELOG.md](CHANGELOG.md) — 变更日志
- [glossary.md](glossary.md) — 术语表
- [stakeholders.md](stakeholders.md) — 干系人列表
- [requirements.yml](requirements.yml) — 需求库
- [traceability.yml](traceability.yml) — 追溯矩阵
- [metrics.yml](metrics.yml) — 项目度量
- [decisions.log](decisions.log) — 决策日志

---

## 1. 需求（`01_REQUIREMENTS/`）

### 1.1 干系人需求（`stakeholder/`）

| ID | 标题 | 状态 |
|----|------|------|
| STK-REQ-001 | 城市路口违章检测全覆盖 | approved |
| STK-REQ-002 | 24 小时无人值守运行 | approved |
| STK-REQ-003 | 与现有信号灯系统兼容 | approved |
| STK-REQ-004 | 数据上报云平台做大数据分析 | approved |

### 1.2 系统需求（`system/`）

| ID | 标题 | 优先级 | 状态 |
|----|------|--------|------|
| SYS-REQ-001 | 4 路 4K@30fps 视频同步接入 | P0 | verified |
| SYS-REQ-002 | 车辆/行人检测 mAP50 > 85% | P0 | verified |
| SYS-REQ-003 | 车牌识别准确率 > 95% | P0 | verified |
| SYS-REQ-004 | 多目标跟踪 MOTA > 75% | P0 | verified |
| SYS-REQ-005 | 流量统计精度 > 95% | P0 | approved |
| SYS-REQ-006 | 信号灯联动控制 < 10ms | P1 | approved |
| SYS-REQ-007 | 云端上报 < 500ms | P0 | verified |
| SYS-REQ-008 | 安全启动链 | P0 | verified |
| SYS-REQ-009 | OTA 远程升级 | P1 | approved |
| SYS-REQ-010 | 离线工作 24h | P1 | approved |

### 1.3 接口需求（`interface/`）

| ID | 标题 | 状态 |
|----|------|------|
| IF-REQ-001 | MIPI CSI-2 4 lane 接收 | approved |
| IF-REQ-002 | 10GbE SFP+ 光口 | approved |
| IF-REQ-003 | CAN 2.0B 总线 | approved |
| IF-REQ-004 | USB3.0 摄像头热插拔 | approved |
| IF-REQ-005 | DisplayPort 1.2 输出 | approved |
| IF-REQ-006 | GPS PPS 时间同步 | approved |

### 1.4 性能需求（`performance/`）

| ID | 标题 | 状态 |
|----|------|------|
| PERF-REQ-001 | 端到端检测延迟 < 30ms/帧 | approved |
| PERF-REQ-002 | 整机功耗 < 35W | approved |
| PERF-REQ-003 | 启动时间 < 15s | approved |
| PERF-REQ-004 | DPU 推理 ≥ 2.5 TOPS | approved |
| PERF-REQ-005 | DDR4 带宽 ≥ 30 GB/s 实际 | approved |

### 1.5 安全/可靠性需求（`safety/`）

| ID | 标题 | 状态 |
|----|------|------|
| SAF-REQ-001 | 安全启动链 RSA-4096 | verified |
| SAF-REQ-002 | 看门狗 A53→R5 心跳 | approved |
| SAF-REQ-003 | 信号灯安全模式（全红） | approved |
| SAF-REQ-004 | mTLS 双向认证 | approved |
| SAF-REQ-005 | 掉电数据不丢失 | approved |
| SAF-REQ-006 | 工作温度 -20°C ~ +70°C | approved |
| SAF-REQ-007 | MTBF > 50,000 小时 | approved |

### 1.6 验证策略（`verification/`）

| ID | 标题 | 状态 |
|----|------|------|
| VP-001 | 闭环仿真验证 | approved |
| VP-002 | DPU 实机验证 | approved |
| VP-003 | 工厂量产测试 | approved |

---

## 2. 架构（`02_ARCHITECTURE/`）

### 2.1 4+1 视图（`views/`）

| 视图 | 内容 |
|------|------|
| logical | [logical/README.md](logical/README.md) |
| process | [process/README.md](process/README.md) |
| physical | [physical/README.md](physical/README.md) |
| development | [development/README.md](development/README.md) |

### 2.2 模块分解（`decomposition/`）

| ID | 标题 | 状态 |
|----|------|------|
| DES-ARCH-001 | PS/PL 功能划分 | approved |
| DES-ARCH-002 | 存储器分区方案 | approved |
| DES-ARCH-003 | 总线带宽规划 | approved |
| DES-ARCH-004 | 主控线程模型 | approved |
| DES-ARCH-005 | R5 FreeRTOS 任务划分 | approved |
| DES-ARCH-006 | OpenAMP 通信协议 | approved |
| DES-ARCH-007 | ISP 流水线 | approved |
| DES-ARCH-008 | 多目标跟踪管线 | approved |
| DES-ARCH-009 | 事件检测状态机 | approved |
| DES-ARCH-010 | 离线缓存与重传 | approved |

### 2.3 接口控制文档（`interfaces/`）

| ID | 标题 | 状态 |
|----|------|------|
| ICD-001 | PS↔PL 共享内存 (DetectionResult) | approved |
| ICD-002 | R5↔A53 RPMsg 协议 | approved |
| ICD-003 | MQTT 主题与数据 schema | approved |
| ICD-004 | gRPC 管理接口 | approved |
| ICD-005 | CAN 总线帧定义 | approved |
| ICD-006 | OSD 寄存器接口 | approved |

### 2.4 权衡研究（`trade-studies/`）

| ID | 标题 | 状态 |
|----|------|------|
| TR-001 | PS/PL 划分（ISP、AI 推理、跟踪、信号灯） | approved |
| TR-002 | 国产 FPGA 替代 | draft |
| TR-003 | YOLO 模型选型（n/s/m） | approved |

---

## 3. 算法（`03_ALGORITHM/`）

| 子目录 | 内容 |
|--------|------|
| [theory/](theory/) | 数学推导与论文笔记 |
| [simulation/src/](simulation/src/) | 算法仿真代码（Python） |
| [golden-ref/](golden-ref/) | 黄金参考输出 |
| [metrics/](metrics/) | 精度/性能/资源度量 |

---

## 4. 实现（`04_IMPLEMENTATION/`）

| 子目录 | 关键文件 |
|--------|---------|
| [c/src/](c/src/) | `main.cpp`、`inference_engine.cpp`、`bytetrack.cpp`、`event_detector.cpp` |
| [c/include/](c/include/) | 头文件 |
| [c/test/](c/test/) | C 单元测试 |
| [hls/isp_pipeline/](hls/isp_pipeline/) | Vitis HLS ISP IP |
| [hls/osd_overlay/](hls/osd_overlay/) | Vitis HLS OSD IP |
| [verilog/rtl/](verilog/rtl/) | 自研 RTL（保留目录） |
| [verilog/constraints/](verilog/constraints/) | XDC 时序/引脚约束 |
| [verilog/vivado_project/](verilog/vivado_project/) | Vivado 工程脚本 |
| [ai/train/](ai/train/) | YOLOv8/LPRNet 训练脚本 |
| [ai/quantization/](ai/quantization/) | Vitis AI PTQ 量化 |
| [ai/models/](ai/models/) | 模型定义 |
| [ai/deploy/](ai/deploy/) | 部署/测试 |
| [rtos/src/](rtos/src/) | FreeRTOS R5 源码 |
| [proto/](proto/) | `traffic_edge.proto` |
| [bindings/web/](bindings/web/) | Vue Web UI |

---

## 5. 验证（`05_VERIFICATION/`）

| 子目录 | 内容 |
|--------|------|
| [test-plans/](test-plans/) | 测试计划 TP-XXX |
| [test-cases/](test-cases/) | 测试用例 TC-XXX-XXX |
| [test-vectors/](test-vectors/) | 测试向量 |
| [testbenches/](testbenches/) | HDL 测试平台 |
| [reports/](reports/) | 测试报告 |
| [coverage/](coverage/) | 覆盖率分析 |
| [regressions/](regressions/) | 回归测试集 |
| [integration/](integration/) | 端到端集成测试 |

---

## 6. 集成（`06_INTEGRATION/`）

| 子目录 | 内容 |
|--------|------|
| [ci-cd/](ci-cd/) | CI/CD 流水线 |
| [environments/](environments/) | dev/sim/staging/prod |
| [releases/](releases/) | 发布产物清单 |
| [deployment/](deployment/) | 部署脚本 |

---

## 7. 反馈（`07_FEEDBACK/`）

| 子目录 | 内容 |
|--------|------|
| [issues/](issues/) | 问题跟踪（ISS-XXX） |
| [adr/](adr/) | 架构决策记录（ADR-XXX） |
| [reviews/](reviews/) | 评审记录 |
| [metrics/](metrics/) | 反馈度量 |
| [retrospectives/](retrospectives/) | 复盘 |

---

## 9. 参考（`99_REFERENCES/`）

| 子目录 | 内容 |
|--------|------|
| [papers/](papers/) | 论文 |
| [standards/](standards/) | 标准 |
| [datasheets/](datasheets/) | 芯片手册 |
| [legacy-docs/](legacy-docs/) | 旧版 docs/（已结构化抽取） |
