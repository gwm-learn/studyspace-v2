---
id: "openwrt-build-09"
title: fitblk引导rootfs
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build"]
aliases: ["fitblk引导rootfs"]
created: 2026-10-24
updated: 2026-10-24
---
# fitblk引导rootfs


### 8.1 设计背景

传统的 OpenWrt 镜像中，kernel 和 rootfs 是独立的文件/分区。但 Filogic 平台引入了一个巧妙的设计：**将 rootfs 嵌入到 FIT 镜像内部**，通过 `fitblk` 机制在运行时暴露为块设备。

### 8.2 内核配置

`target/linux/mediatek/filogic/config-6.12`：
```
CONFIG_MTD_UBI=y                    # UBI 子系统
CONFIG_MTD_UBI_BLOCK=y              # UBI 块设备（将 UBI 卷转为块设备）
CONFIG_UIMAGE_FIT_BLK=y             # FIT 块设备驱动（关键！）
```

`drivers/block/fitblk.c`（内核补丁 `target/linux/generic/pending-6.12/510-block-add-uImage.FIT-subimage-block-driver.patch`）：该驱动解析 U-Boot FIT 镜像中的子镜像（`"rootfs"` 节点），将其内容作为块设备暴露。

### 8.3 FIT 镜像中的 rootfs 节点

`Build/fit-its` 中的 `rootfs` 节点 (`scripts/mkits.sh:143-161`)：
```dts
rootfs@1 {
  description = "ARM64 OpenWrt rootfs";
  data = /incbin/("rootfs.squashfs.pagesync");  # 带 pagesync 头
  type = "filesystem";
  arch = "arm64";
  compression = "none";
};
```

**为什么需要 `.pagesync`**：`mkfs.squashfs` 输出 `rootfs.squashfs`，但 UBI 块设备需要 4KB 对齐。`scripts/mkits.sh:85-88` 检测：如果 rootfs 不是 4KB 对齐，追加 `.pagesync` blob（4096 字节的 0x00 填充）使总长度对齐。

### 8.4 运行时引导流程

```
U-Boot:
  ubi part ubi 0
  ubifsload virt 0:fit 0x48000000 openwrt_one-sysupgrade.itb
  bootm 0x48000000                    # 启动 FIT 镜像

Linux (boot params from FDT):
  /chosen/rootdisk = <&ubi_fit_volume> # phandle 指向 UBI 卷
  MTD UBI:ubi 块设备被 mtdblock 驱动创建
  fitblk 驱动:
    - 解析 FIT 中的 rootfs@1 子镜像
    - 将其内容作为 /dev/fit0 (块设备) 暴露
  mount /dev/fit0 /                  # squashfs 根文件系统
```

`package/utils/fitblk` 的用户态工具 (`fitblk` 可执行文件) 和 `/lib/upgrade/fit.sh` 负责在引导时正确释放块设备、处理镜像布局。

---
