# 发布产物清单

> 各版本的发布产物、签名、Checksum 记录。

## 命名规范

- `edgevision-t1-{version}.swu`：OTA 升级包
- `edgevision-t1-{version}.bin`：完整镜像（SD 卡烧录）
- `edgevision-t1-{version}.tar.gz`：源码 + 文档 打包
- `edgevision-t1-{version}-manifest.json`：产物清单（文件名/大小/SHA256）

## 目录

- `v1.0.0/`：GA Release
- `v1.1.0-beta.1/`：内测
- `internal/`：内部测试版本
