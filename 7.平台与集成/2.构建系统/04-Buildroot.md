---
id: "plt-build-04"
title: "Buildroot 要点"
cluster: plt
layer: L2
status: draft
confidence: medium
platform: ["Buildroot 2023.x/2024.x"]
source:
  - type: doc
    ref: "Buildroot User Manual"
verified_on: null
tags: ["buildroot", "build", "rootfs"]
aliases: ["Buildroot"]
created: 2026-10-24
updated: 2026-10-24
---

# Buildroot 要点

> 解决什么问题：用 Buildroot 构建一个可启动、可定制、可维护的嵌入式 Linux；知道它和 OpenWrt/Yocto 的边界。
> 不解决：具体包配方细节（按 package 目录）。

## 1. 定位

| 项 | Buildroot | OpenWrt | Yocto |
|---|---|---|---|
| 目标 | 小型嵌入式根文件系统 | 路由器发行版 | 通用嵌入式发行版 |
| 配置 | menuconfig | menuconfig + feeds | layer/recipe |
| 包管理 | 无（可加） | opkg/apk | rpm/deb/ipk |
| 学习曲线 | 低 | 中 | 高 |
| 适合 | 固定功能 | 网络设备 | 多产品/长维护 |

## 2. 目录结构

```text
buildroot/
├── board/          # 板级配置（DTS、内核 config、post-build）
├── configs/        # defconfig
├── package/        # 软件包配方
├── support/        # 脚本/工具
├── system/         # 根文件系统骨架
├── toolchain/      # 工具链
└── output/         # 构建产物
```

## 3. 最小流程

```bash
make menuconfig
make
ls output/images/
```

输出：`zImage/Image`、`*.dtb`、`rootfs.ext4`、`rootfs.tar`、`sdcard.img` 等。

### 3.1 关键配置

| 配置 | 作用 |
|---|---|
| Target Architecture | ARM/x86/MIPS |
| Toolchain | 内置/外部 |
| Kernel | 版本/defconfig/DTS |
| Bootloader | U-Boot |
| Root FS | ext4/squashfs/ubifs/initramfs |
| System | init（busybox/systemd） |

## 4. 板级定制

```text
board/<vendor>/<board>/
├── linux.config
├── genimage.cfg
├── post-build.sh
├── post-image.sh
└── rootfs_overlay/
```

- `post-build.sh`：改权限/配置/删除文件。
- `post-image.sh`：生成 SD/eMMC 镜像。
- `rootfs_overlay`：覆盖文件。

## 5. 自定义包

```text
package/demo/
├── Config.in
├── demo.mk
└── demo.hash
```

`demo.mk` 关键变量：`DEMO_VERSION`、`DEMO_SITE`、`DEMO_SOURCE`、`DEMO_CONF_OPTS`、`DEMO_INSTALL_TARGET_CMDS`。

## 6. BR2_EXTERNAL

把项目定制放在主树外：

```bash
make BR2_EXTERNAL=/path/to/project demo_defconfig
```

- 避免改主树，便于升级。
- 可放 board/package/configs。

## 7. 常见任务

| 任务 | 命令/方法 |
|---|---|
| 保存配置 | `make savedefconfig` |
| 只编译某包 | `make <pkg>-rebuild` |
| 清理包 | `make <pkg>-dirclean` |
| 全清 | `make clean` / `distclean` |
| 外部工具链 | Toolchain → External |
| 增大 rootfs | 改分区/镜像配置 |

## 8. 常见坑

| 坑 | 说明 |
|---|---|
| 全量重编译慢 | ccache/外部输出目录 |
| 包版本冲突 | 锁版本/补丁 |
| 无包管理 | OTA 需 A/B/自建 |
| 工具链不匹配 | sysroot/ABI |
| 根文件系统只读 | overlay/可写分区 |
| 许可合规 | 收集 license/SBOM |

## 9. 与 OpenWrt/Yocto 的取舍

- 固定功能、小体积、快速启动：Buildroot。
- 网络设备、需要 opkg/LuCI：OpenWrt。
- 多产品/长维护/强定制：Yocto。
- 厂商 SDK 已给：先打通，再评估迁移。

## 10. 检查表

- [ ] 可复现构建（版本/配置/工具链）。
- [ ] 板级文件在 BR2_EXTERNAL。
- [ ] 根文件系统可写/overlay。
- [ ] 升级/回滚方案。
- [ ] license/SBOM。
- [ ] 启动/网络/存储验证。

## 11. 相关

- [构建系统总览](00-总览.md)
- [Yocto](03-Yocto/00-总览.md)
- [OpenWrt 构建体系](../../7.平台与集成/1.OpenWrt/1.构建体系/00-总览.md)
- [构建系统选型](06-构建系统选型.md)
