---
id: "openwrt-build-08"
title: Flash分区与DTS
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build", "dts"]
aliases: ["Flash分区与DTS"]
created: 2026-10-24
updated: 2026-10-24
---
# Flash分区与DTS


本章以旗舰参考设计 `openwrt_one`（`target/linux/mediatek/dts/mt7981b-openwrt-one.dts`）为核心，描述 MT7981 的 Flash 分区布局。详细的可视化布局见第 13 节。

### 7.1 SPI-NAND Flash 分区布局（以 openwrt_one 为例）

`mt7981b-openwrt-one.dts`（第 322-345 行）：

```
flash@0 (spi-nand, 总容量 256MB):
  partition@0       "bl2"        0x000000 - 0x100000  (1MB, 只读, BootROM 加载 BL2)
  partition@580000   "ubi"        0x100000 - 0x10000000 (255MB, UBI 卷)
                       └─ volumes:
                           ubi-volume-fit (volname="fit") → kernel FIT 镜像
                           ubi-volume-rootfs (squashfs)
                           ubi-volume-ubootenv × 2 (各 1MiB)
```

**布局特点**：openwrt_one 的 SPI-NAND 布局非常精简——仅 `bl2` + `ubi` 两个分区。U-Boot 环境变量与 rootfs 一起打包进 UBI 卷，kernel FIT 存放在 UBI:fit 卷。没有独立的 u-boot-env / factory / fip 分区；U-Boot 可能嵌入 UBI:fit（通过 mkimage "firmware" 子镜像）或由 BootROM 特殊加载路径处理。

> **变体差异**：多数商业 NAND 设备（如 abt_asr3000、MT7981-rfb）的 DTS 布局更复杂——`partition@0 "bl2"` + `partition@100000 "u-boot-env"` + `partition@180000 "art"` + `partition@280000 "factory"` + `partition@380000 "fip"` + `partition@580000 "ubi"`。FIP 是独立的 raw MTD 分区（`partition@380000 "fip"`，128KB），与 UBI 并列。

### 7.2 SPI-NOR Flash 布局（Dual Flash 设备）

`mt7981b-openwrt-one.dts`（第 365-407 行）：

```
flash@1 (spi-nor):
  partition@0        "bl2-nor"   0x00000 - 0x40000    (256KB, BootROM 加载 BL2)
  partition@40000    "factory"   0x40000 - 0xC0000   (512KB, 校准数据 MAC/Board ID)
  partition@100000   "fip-nor"   0x100000 - 0x180000 (512KB, FIP 镜像)
  partition@180000   "recovery"  0x180000 - 0xE00000  (12.5MB, 恢复 kernel)
```

**fip-nor 分区内容**：`mt7981_openwrt_one-nor-u-boot.fip`（xz 压缩: BL31 + U-Boot proper）。

**双 Flash 启动流程**（openwrt_one Dual Flash）：
1. BootROM 加载 SPI-NAND BL2 → 启动主系统
2. 也可切换至 SPI-NOR：BL2_NOR → FIP_NOR → Recovery kernel（用于紧急恢复）
3. NOR 分区主要用于：出厂校准数据存储、Recovery 镜像、FIP 备份

### 7.3 Device Tree chosen 节点（启动参数传递）

`mt7981b-openwrt-one.dts`（第 20-23 行）：

```dts
chosen {
  stdout-path = "serial0:115200n8";
  rootdisk = <&ubi_fit_volume>;   # fitblk 驱动通过此 phandle 找到 FIT 中的 rootfs 子镜像
};
```

`fitblk` 驱动读取 `/chosen/rootdisk` 的 phandle，将对应的 FIT 子镜像（rootfs）暴露为 `/dev/fit0` 等块设备。

> 对于 abt_asr3000 等 NAND 设备，chosen 节点使用 `rootdisk = <&ubi_rootdisk>`（指向 UBI rootfs 卷的 phandle）。

### 7.4 sysupgrade 升级路径

`target/linux/mediatek/filogic/base-files/lib/upgrade/platform.sh:98-159`：

```bash
platform_do_upgrade() {
  local board=$(board_name)
  case "$board" in
  openwrt,one|abt,asr3000|mediatek,mt7981-rfb|...)
    fit_do_upgrade "$1"        # FIT 镜像升级
    ;;
  acer,predator-w6|glinet,gl-mt2500|...)
    emmc_do_upgrade "$1"       # eMMC 设备升级
    ;;
  asus,rt-ax52|asus,rt-ax57m|...)
    CI_UBIPART="UBI_DEV"
    nand_do_upgrade "$1"       # 厂商 UBI NAND 升级
    ;;
  *)
    default_do_upgrade "$1"     # 直接mtd write
    ;;
  esac
}
```

`fit_do_upgrade` (`/lib/upgrade/fit.sh`) 流程：
1. `fwtool -q -i /tmp/sysupgrade.meta "$1"` — 读取镜像元数据验证兼容性
2. `fwtool_check_signature` — 如果签名开启，验证 usign 签名
3. `fit info` — 读取 FIT 信息
4. `fit flash kernel` — 将 FIT 中的 kernel 写入 UBI:fit 卷（或 MTD 分区）
5. `fitblk release` — 释放 FIT rootfs 块设备
6. `fit rootfs layout` — 确定 rootfs 在 UBI 卷中的位置
7. `nand_do_upgrade` 或 `emmc_do_upgrade` — 写入 rootfs
