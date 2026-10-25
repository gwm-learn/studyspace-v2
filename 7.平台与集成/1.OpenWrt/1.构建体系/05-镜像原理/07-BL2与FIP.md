---
id: "openwrt-build-07"
title: BL2与FIP
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build"]
aliases: ["BL2与FIP"]
created: 2026-10-24
updated: 2026-10-24
---
# BL2与FIP


### 6.1 构件来源总览

| 构件 | 来源包 | 源类型 | 输出文件名 |
|------|-------|--------|-----------|
| BL2 (Preloader) | `package/boot/arm-trusted-firmware-mediatek` | **构建自源码** (mtk-openwrt/arm-trusted-firmware.git) | `mt7981-<bootdev>-<ddrtype>-bl2.img` |
| BL31 | 同上 | **构建自源码** | `mt7981-<bootdev>-<ddrtype>-bl31.bin` |
| U-Boot proper | `package/boot/uboot-mediatek` | **构建自源码** (denx.de/u-boot.git + 133 patches) | 中间产物 `u-boot.bin` |
| FIP | 同上 | 由 `fiptool`（arm-trusted-firmware-tools/host 包）打包 | `mt7981_<device>-u-boot.fip` |

**关键误解澄清**：`package/boot/uboot-mediatek/` 目录下只有 `Makefile` 和 `patches/` 子目录，**没有任何预编译二进制文件**。BL2、BL31、U-Boot 均从源码构建。

### 6.2 ARM Trusted Firmware (ATF) 构建

`package/boot/arm-trusted-firmware-mediatek/Makefile:14-17`：
```makefile
PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/mtk-openwrt/arm-trusted-firmware.git
PKG_SOURCE_DATE:=2025-07-11
PKG_SOURCE_VERSION:=78a0dfd927bb00ce973a1f8eb4079df0f755887a
```

**MT7981 ATF 变体** (`Makefile:691-707` 的 TFA_TARGETS)：
| 变体 | 用途 | BL2 特性 |
|------|------|---------|
| `spim-nand-ddr3` | 大多数商业 NAND 设备 | mkimage 包装，NAND I/O |
| `spim-nand-ddr3-1866` | DDR3 @ 1866MHz 变体 | 同上，频率参数不同 |
| `spim-nand-ubi-ddr4` | UBI + DDR4 设备 | UBI 启动支持 |
| `emmc-ddr3/ddr4` | eMMC 启动设备 | eMMC I/O |
| `nor-ddr3/ddr4` | SPI-NOR 启动设备 | NOR I/O，FIP 启用 |
| `sdmmc-ddr3` | SD 卡启动 | SD/eMMC I/O |
| `snand-ddr3` | SNFI NAND | 串行 NAND I/O |

ATF 安装脚本 (`Makefile:788-792`)：
```makefile
define Package/trusted-firmware-a/install
  $(INSTALL_DIR) $(STAGING_DIR_IMAGE)
  $(INSTALL_DATA) $(PKG_BUILD_DIR)/build/$(PLAT)/release/bl2.img \
    $(STAGING_DIR_IMAGE)/$(BUILD_VARIANT)-bl2.img
  $(INSTALL_DATA) $(PKG_BUILD_DIR)/build/$(PLOT)/release/bl31.bin \
    $(STAGING_DIR_IMAGE)/$(BUILD_VARIANT)-bl31.bin
endef
# 例: BUILD_VARIANT=mt7981-spim-nand-ddr3
# 输出: STAGING_DIR_IMAGE/mt7981-spim-nand-ddr3-bl2.img
#      STAGING_DIR_IMAGE/mt7981-spim-nand-ddr3-bl31.bin
```

**BL2 包装**：`USE_MKIMAGE=1 MKIMAGE=$(STAGING_DIR_HOST)/bin/mkimage` — ATF 构建系统使用 OpenWrt 主机工具链中的 `mkimage` 为 BL2 添加 U-Boot 传统头（MediaTek 专有头由 `mtk_image` 工具添加，部分厂商使用）。

### 6.3 U-Boot 构建与 FIP 合成

`package/boot/uboot-mediatek/Makefile` 定义 47 个 MT7981 变体，例如：
```makefile
define U-Boot/mt7981_xiaomi_mi-router-ax3000t
  NAME:=Xiaomi Router AX3000T
  BUILD_SUBTARGET:=filogic
  BUILD_DEVICES:=xiaomi_mi-router-ax3000t-ubootmod
  UBOOT_CONFIG:=mt7981_xiaomi_mi-router-ax3000t
  UBOOT_IMAGE:=u-boot.fip
  BL2_BOOTDEV:=spim-nand
  BL2_SOC:=mt7981
  BL2_DDRTYPE:=ddr3
  DEPENDS:=+trusted-firmware-a-mt7981-spim-nand-ddr3
endef
```

**FIP 合成** (`Makefile:1398-1407` 的 `Build/fip-image`)：
```makefile
define Build/fip-image
  $(STAGING_DIR_HOST)/bin/fiptool create \
    --soc-fw $(STAGING_DIR_IMAGE)/$(BL2_SOC)-$(BL2_BOOTDEV)-$(BL2_DDRTYPE)-bl31.bin \
    --nt-fw $(PKG_BUILD_DIR)/u-boot.bin \
    $(PKG_BUILD_DIR)/u-boot.fip
endef
```

**FIP 安装** (`Makefile:1438-1441` 的 `Build/InstallDev`)：
```makefile
define Build/InstallDev
  $(INSTALL_DIR) $(STAGING_DIR_IMAGE)
  $(INSTALL_DATA) $(PKG_BUILD_DIR)/$(UBOOT_IMAGE) \
    $(STAGING_DIR_IMAGE)/$(BUILD_VARIANT)-$(UBOOT_IMAGE)
endef
# 例: STAGING_DIR_IMAGE/mt7981_xiaomi_mi-router-ax3000t-u-boot.fip
```

### 6.4 filogic.mk 对引导构件的消费

```makefile
# filogic.mk:20-26 — 读取 STAGING_DIR_IMAGE 中的构件拼入目标镜像
define Build/mt7981-bl2
  cat $(STAGING_DIR_IMAGE)/mt7981-$1-bl2.img >> $@
  # $1 = "spim-nand-ddr3" → mt7981-spim-nand-ddr3-bl2.img
endef

define Build/mt7981-bl31-uboot
  cat $(STAGING_DIR_IMAGE)/mt7981_$1-u-boot.fip >> $@
  # $1 = "xiaomi_mi-router-ax3000t" → mt7981_xiaomi_mi-router-ax3000t-u-boot.fip
endef
```

### 6.5 BL2 类型对照表（按 boot 介质）

| boot 介质 | BL2 变体 | 依赖 TFA 包 | 说明 |
|-----------|---------|------------|------|
| SPI-NAND | `spim-nand-ddr3` | `trusted-firmware-a-mt7981-spim-nand-ddr3` | NAND I/O, DDR3 |
| SPI-NAND + UBI | `spim-nand-ubi-ddr4` | `...-mt7981-spim-nand-ubi-ddr4` | 支持 UBI 启动 |
| eMMC | `emmc-ddr4` | `...-mt7981-emmc-ddr4` | eMMC HS200/HS400 |
| SPI-NOR | `nor-ddr4` | `...-mt7981-nor-ddr4` | 支持 FIP over NOR |
| SD 卡 | `sdmmc-ddr3` | `...-mt7981-sdmmc-ddr3` | SD 卡启动 |
| SNFI NAND | `snand-ddr3` | `...-mt7981-snfi-ddr3` | 串行 NAND I/O |

---
