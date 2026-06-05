# 开发视图

> 4+1 视图中的开发视图，关注 **代码组织、构建、测试、发布**。

## 仓库结构

```
案例-智能交通路口感知平台/                 # 本仓库
├── ARCHITECTURE.md                       # 架构宪法
├── README.md                             # 项目入口
├── .gitignore
├── .gitattributes
│
├── core/                                 # 核心部分（纯文本）
│   ├── 00_MANIFEST/                      # 入口与元数据
│   ├── 01_REQUIREMENTS/                  # 需求（35+ 文档）
│   ├── 02_ARCHITECTURE/                  # 架构（4+1 视图、分解、ICD）
│   ├── 03_ALGORITHM/                     # 算法（理论、仿真、黄金参考）
│   ├── 04_IMPLEMENTATION/                # 实现（C/C++/HLS/Verilog/RTOS/AI/Proto/Web）
│   ├── 05_VERIFICATION/                  # 验证（测试计划、用例、报告、集成）
│   ├── 06_INTEGRATION/                   # 集成（CI/CD、部署、Release）
│   ├── 07_FEEDBACK/                      # 反馈（问题、ADR、复盘）
│   └── 99_REFERENCES/                    # 参考资料 + 历史
│
├── tools/                                # 工具流（可迁移，submodule）
│   ├── sw_hw_toolflow/                   # Python 库
│   ├── hooks/                            # Git hooks
│   ├── make/                             # Makefile 片段
│   ├── schemas/                          # JSON Schema
│   ├── ci-templates/                     # CI 平台模板
│   └── agents/                           # LLM Agent 模板
│
└── configs/                              # 项目配置
    ├── toolchain.yml                     # 工具链映射
    ├── project.yml                       # 项目元信息
    ├── ci.yml                            # CI 平台选择
    ├── release.yml                       # Release 流程
    └── secret.example.yml                # 敏感配置模板
```

## 模块归属（core/04_IMPLEMENTATION/）

| 模块 | 路径 | 语言 | 负责人 |
|------|------|------|--------|
| C 应用主控 | `c/src/main.cpp` | C++17 | sw-team |
| C 推理引擎 | `c/src/inference_engine.cpp` | C++17 | sw-team |
| C 跟踪 | `c/src/bytetrack.cpp` | C++17 | sw-team |
| C 事件检测 | `c/src/event_detector.cpp` | C++17 | sw-team |
| C 帧管理 | `c/src/frame_manager.cpp` | C++17 | sw-team |
| C 云端上报 | `c/src/cloud_reporter.cpp` | C++17 | sw-team |
| C gRPC | `c/src/grpc_server.cpp` | C++17 | sw-team |
| C REST/WS | `c/src/rest_server.cpp` | C++17 | sw-team |
| C OSD 写 | `c/src/osd_writer.cpp` | C++17 | sw-team |
| C 离线缓存 | `c/src/offline_cache.cpp` | C++17 | sw-team |
| C OTA | `c/src/ota_client.cpp` | C++17 | sw-team |
| C 视频驱动 | `c/drivers/traffic_video.c` | C | kernel-team |
| HLS ISP | `hls/isp_pipeline/` | C++ | fpga-team |
| HLS OSD | `hls/osd_overlay/` | C++ | fpga-team |
| Vivado 工程 | `verilog/vivado_project/` | Tcl | fpga-team |
| XDC 约束 | `verilog/constraints/` | Tcl | fpga-team |
| YOLOv8 训练 | `ai/train/` | Python | ai-team |
| LPRNet 模型 | `ai/models/` | Python | ai-team |
| 量化 | `ai/quantization/` | Python | ai-team |
| 部署 | `ai/deploy/` | Python | ai-team |
| FreeRTOS R5 | `rtos/src/` | C | rtos-team |
| Proto | `proto/traffic_edge.proto` | Protobuf | backend-team |
| Web UI | `bindings/web/` | Vue/HTML/JS | web-team |
| 算法仿真 | `../../03_ALGORITHM/simulation/src/` | Python | sim-team |

## 构建依赖

```
ai/models/  →  ai/train/  →  ai/quantization/  →  ai/deploy/
                                                       │
hls/isp_pipeline/  ─────────────────────────────────────┤
                                                       │
hls/osd_overlay/  ─────────────────────────────────────┤
                                                       ▼
verilog/vivado_project/  →  bitstream (BOOT.BIN)  →  petalinux
                                                       │
                                                       ▼
rtos/src/  ─────────────────────────────────────────→  petalinux
                                                       │
                                                       ▼
c/src/ + c/include/  →  cross-compile  →  rootfs
                                                       │
                                                       ▼
proto/  →  protoc  →  c/src/
                                                       ▼
bindings/web/  →  npm build  →  rootfs
                                                       │
                                                       ▼
04_IMPLEMENTATION  →  Release (06_INTEGRATION/releases/)
```

## 测试分层

| 层级 | 位置 | 工具 |
|------|------|------|
| 单元 | `04_IMPLEMENTATION/c/test/` | gtest |
| 单元 | `04_IMPLEMENTATION/ai/quantization/` | pytest |
| 模块 | `05_VERIFICATION/test-cases/` | 手工 + 脚本 |
| 集成 | `05_VERIFICATION/integration/` | pytest |
| 回归 | `05_VERIFICATION/regressions/` | pytest |
| 系统 | `05_VERIFICATION/integration/e2e_integration.py` | pytest |
| 工厂 | `06_INTEGRATION/ci-cd/factory_test.py` | Python paramiko |

## CI/CD 流水线

参见 [06_INTEGRATION/ci-cd/](../../06_INTEGRATION/ci-cd/)：
- pre-commit：lint、ID 校验、链接校验
- pre-push：追溯校验
- CI (PR)：full_verify
- CI (push to main)：build + test
- tag → release：自动 OTA 包构建与签名

## Release 流程

1. 开发者发起 PR
2. CI 跑全量验证
3. 合并到 main
4. 自动构建 Release 候选
5. 手动审批 → tag
6. tag 触发 OTA 包构建
7. 签名 + 上传 OSS
8. 通知云端下发
