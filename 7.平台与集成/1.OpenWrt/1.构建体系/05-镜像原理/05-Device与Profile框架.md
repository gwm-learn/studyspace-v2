---
id: "openwrt-build-05"
title: Device与Profile框架
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build"]
aliases: ["Device与Profile框架"]
created: 2026-10-24
updated: 2026-10-24
---
# Device与Profile框架


### 4.1 Device 框架工作原理

`include/image.mk:428-963` 定义了 OpenWrt 的设备抽象框架，是理解镜像构建的核心：

```
Device/InitProfile    → 初始化 PROFILES, DEVICE_TITLE, DEVICE_PACKAGES (空)
Device/Init          → 初始化所有变量默认值 (KERNEL, IMAGES, IMAGE_SIZE, ARTIFACTS...)
Device/Default       → 从 target/linux/<board>/image/Makefile 的 Device/Default 继承
Device/<name>        → 用户定义的设备实际参数 (DTS, 分区, 镜像命令...)
Device/Check         → 检查 .config 中该设备是否启用
Device/Build         → 展开为具体 make 规则 (Device/Build/kernel, Device/Build/image, Device/Build/artifact)
```

**`Device/Init` 默认变量** (`include/image.mk:467-552`)：
```makefile
DEVICE_NAME := $(1)           # 设备名，如 "openwrt_one"
KERNEL :=                     # 内核镜像管线命令（默认来自 Device/Default）
IMAGES :=                     # 要生成的镜像文件列表
ARTIFACTS :=                  # 附属产物（preloader.bin, bl31-uboot.fip...）
IMAGE_SIZE :=                 # 最大镜像大小（分区大小）
NAND_SIZE :=                  # NAND Flash 总大小
KERNEL_IN_UBI :=              # 是否将 kernel 打包进 UBI 卷
UBOOTENV_IN_UBI :=             # 是否将 ubootenv 打包进 UBI
DEVICE_DTS :=                  # 要编译的 DTS 文件名（无后缀）
DEVICE_PACKAGES :=             # 额外安装的包列表
UBOOT_PATH := $(STAGING_DIR_IMAGE)/uboot-$(1)  # 不适用于 filogic
```

### 4.2 filogic.mk 的 Build 命令扩展

`target/linux/mediatek/image/filogic.mk:1-140` 在 include/image-commands.mk 之外定义了 MT7981 专用 Build 命令：

```makefile
define Build/mt7981-bl2
  # cat STAGING_DIR_IMAGE/mt7981-<arg1>-bl2.img >> $@
  # arg1 = TFA 变体名，如 "spim-nand-ddr3"
  cat $(STAGING_DIR_IMAGE)/mt7981-$1-bl2.img >> $@
endef

define Build/mt7981-bl31-uboot
  # cat STAGING_DIR_IMAGE/mt7981_<arg1>-u-boot.fip >> $@
  # arg1 = U-Boot 变体名，如 "openwrt_one-snand"
  cat $(STAGING_DIR_IMAGE)/mt7981_$1-u-boot.fip >> $@
endef
```

**命名不对称性**：
- BL2 使用 **连字符** 风格（来自 TFA 包：`mt7981-spim-nand-ddr3-bl2.img`）
- FIP 使用 **下划线 + mt7981_ 前缀** 风格（来自 U-Boot 包：`mt7981_openwrt_one-snand-u-boot.fip`）

### 4.3 设备定义范例：openwrt_one（旗舰参考设计）

`target/linux/mediatek/image/filogic.mk:2861-2905`：
```makefile
define Device/openwrt_one
  DEVICE_VENDOR := OpenWrt
  DEVICE_MODEL := One
  DEVICE_DTS := mt7981b-openwrt-one
  DEVICE_DTS_DIR := ../dts
  DEVICE_DTC_FLAGS := --pad 4096          # DTB 4KB 对齐
  DEVICE_DTS_LOADADDR := 0x43f00000       # DTB 加载地址

  KERNEL_LOADADDR := 0x44000000            # 比默认值 0x48000000 低（openwrt_one 设计）
  KERNEL := kernel-bin | gzip             # 注意：不是 lzma，是 gzip
  KERNEL_INITRAMFS := kernel-bin | lzma | \
    fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb with-initrd | pad-to 64k
  KERNEL_INITRAMFS_SUFFIX := .itb

  KERNEL_IN_UBI := 1                     # kernel 打入 UBI 卷
  UBOOTENV_IN_UBI := 1                   # ubootenv 打入 UBI 卷

  IMAGES := sysupgrade.itb
  IMAGE/sysupgrade.itb := append-kernel | \
    fit gzip $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb \
    external-with-rootfs | pad-rootfs | append-metadata
  # external-with-rootfs: FIT 中 rootfs 作为独立子镜像，通过 fitblk 暴露为块设备

  UBINIZE_OPTS := -E 5                   # UBI 擦除对齐
  BLOCKSIZE := 128k
  PAGESIZE := 2048

  # 引导加载程序产物
  ARTIFACTS := nor-preloader.bin nor-bl31-uboot.fip \
    snand-preloader.bin snand-bl31-uboot.fip \
    factory.ubi snand-factory.bin nor-factory.bin

  # SPI-NOR 介质 (bl2 连字符 + FIP 下划线)
  ARTIFACT/nor-preloader.bin    := mt7981-bl2 nor-ddr4
  ARTIFACT/nor-bl31-uboot.fip  := mt7981-bl31-uboot openwrt_one-nor

  # SPI-NAND 介质
  ARTIFACT/snand-preloader.bin  := mt7981-bl2 spim-nand-ubi-ddr4
  ARTIFACT/snand-bl31-uboot.fip:= mt7981-bl31-uboot openwrt_one-snand

  # UBI factory 镜像（kernel+rootfs 一起打包）
  ARTIFACT/factory.ubi         := ubinize-image fit squashfs-sysupgrade.itb

  # snand-factory.bin: 重复 bl2 (256k/512k/768k/1M) + ubinize-image
  ARTIFACT/snand-factory.bin   := mt7981-bl2 spim-nand-ubi-ddr4 | pad-to 256k | \
    mt7981-bl2 spim-nand-ubi-ddr4 | pad-to 512k | \
    mt7981-bl2 spim-nand-ubi-ddr4 | pad-to 768k | \
    mt7981-bl2 spim-nand-ubi-ddr4 | pad-to 1024k | \
    ubinize-image fit squashfs-sysupgrade.itb

  # nor-factory.bin: nor-bl2 + eeprom + nor-bl31-uboot.fip + initramfs
  ARTIFACT/nor-factory.bin     := mt7981-bl2 nor-ddr4 | pad-to 256k | \
    append-openwrt-one-eeprom | pad-to 1024k | \
    mt7981-bl31-uboot openwrt_one-nor | pad-to 512k | \
    append-image-stage initramfs.itb

  # UBI 卷定义（FIP 从外部分区加载）
  UBINIZE_PARTS := fip=:$(STAGING_DIR_IMAGE)/mt7981_openwrt_one-snand-u-boot.fip \
    recovery=:$(KDIR)/tmp/$$(KERNEL_INITRAMFS_IMAGE) \
    calibration=:$(TOPDIR)/openwrt-mediatek-filogic-openwrt_one-calibration.itb
endef
```

**关键理解**：
- `sysupgrade.itb` 是 **不含 rootfs 的 FIT**（`external-with-rootfs`），rootfs 从 UBI:fit 卷加载
- `factory.ubi` 是 **UBI 镜像**，包含 kernel FIT + rootfs（完整可启动镜像）
- `snand-factory.bin` 包含 **多个 BL2 拷贝**（不同偏移，用于兼容性或备份）
- `KERNEL_IN_UBI=1` 使 `Build/append-ubi` 将 kernel FIT 打入 UBI 的 kernel 卷

### 4.4 SPI-NAND UBI 设备：abt_asr3000

`target/linux/mediatek/image/filogic.mk:142-164`：
```makefile
define Device/abt_asr3000
  DEVICE_DTS := mt7981b-abt-asr3000
  DEVICE_PACKAGES := kmod-mt7915e kmod-mt7981-firmware mt7981-wo-firmware
  UBINIZE_OPTS := -E 5
  BLOCKSIZE := 128k
  PAGESIZE := 2048
  KERNEL_IN_UBI := 1
  UBOOTENV_IN_UBI := 1
  IMAGES := sysupgrade.itb
  KERNEL_INITRAMFS_SUFFIX := -recovery.itb
  KERNEL := kernel-bin | gzip
  KERNEL_INITRAMFS := kernel-bin | lzma | \
    fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb with-initrd | pad-to 64k
  IMAGE/sysupgrade.itb := append-kernel | \
    fit gzip $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb \
    external-static-with-rootfs | append-metadata
  # external-static-with-rootfs: rootfs 作为 static 卷（固定大小）嵌入 UBI

  ARTIFACTS := preloader.bin bl31-uboot.fip
  ARTIFACT/preloader.bin  := mt7981-bl2 spim-nand-ddr3
  ARTIFACT/bl31-uboot.fip := mt7981-bl31-uboot abt_asr3000
endef
```

### 4.5 MT7981 参考设计（全部启动介质）：mediatek_mt7981-rfb

`target/linux/mediatek/image/filogic.mk:2251-2303` — 展示了一块支持 **所有启动介质** 的参考板：

| 启动介质 | BL2 产物 | FIP 产物 |
|---------|---------|---------|
| eMMC | `emmc-preloader.bin` | `emmc-bl31-uboot.fip` |
| SPI-NOR | `nor-preloader.bin` | `nor-bl31-uboot.fip` |
| SNFI NAND | `snfi-nand-preloader.bin` | `snfi-nand-bl31-uboot.fip` |
| SPI-NAND | `spim-nand-preloader.bin` | `spim-nand-bl31-uboot.fip` |
| SD 卡 (GPT) | GPT 分区表 + bl2 @ 17k + fip @ 6656k | |

SD 卡镜像 (`ARTIFACT/sdcard.img.gz`) 的 GPT 分区由 `Build/mt798x-gpt` (`filogic.mk:60-80`) 生成：
```bash
ptgen -g -o $@.tmp -a 1 -l 1024 \
  -t 0x83 -N ubootenv -r -p 512k@4M \
  -t 0x83 -N factory -r -p 2M@4608k \
  -t 0xef -N fip -r -p 4M@6656k \
  -t 0x2e -N production -p <ROOTFS_PARTSIZE>M@64M
```

---
