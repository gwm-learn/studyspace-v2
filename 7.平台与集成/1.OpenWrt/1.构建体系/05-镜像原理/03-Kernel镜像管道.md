---
id: "openwrt-build-03"
title: Kernel镜像管道
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build"]
aliases: ["Kernel镜像管道"]
created: 2026-10-24
updated: 2026-10-24
---
# Kernel镜像管道


### 2.1 管线概述

MT7981 Filogic 默认的内核镜像管线定义在 `target/linux/mediatek/image/Makefile:17-34`：

```makefile
define Device/Default
  KERNEL_NAME := Image                          # aarch64 Linux Image (非 vmlinux)
  KERNEL = kernel-bin | lzma | \
    fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb
  KERNEL_INITRAMFS = kernel-bin | lzma | \
    fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb with-initrd
  KERNEL_LOADADDR = 0x48000000                  # Filogic 默认加载地址
  FILESYSTEMS := squashfs erofs
  IMAGES := sysupgrade.bin
  IMAGE/sysupgrade.bin := append-kernel | pad-to 128k | append-rootfs | \
    pad-rootfs | append-metadata
endef
```

**管线语法**：`|` 分隔的每一段对应一个 `Build/<命令>` 或 `Image/Build/<命令>`，按顺序执行，上一段的输出作为下一段的输入（`$@`）。

### 2.2 管线拆解

#### 第一段：`kernel-bin`

`include/image-commands.mk:539-542`：
```makefile
define Build/kernel-bin
  rm -f $@
  cp $< $@                     # 从 $(KDIR)/vmlinux 或 Image 复制到 $@
endef
```

`$<` 是 `Device/Build/kernel` 规则的第一个依赖：`$(KDIR)/$(KERNEL_NAME):: image_prepare` → `$(call Kernel/Compile)` → Linux 源码的 `arch/arm64/boot/Image`（aarch64 输出文件恰好就叫 `Image`，不是 `vmlinux`）。

#### 第二段：`lzma`

`include/image-commands.mk:591-598`：
```makefile
define Build/lzma
  $(call Build/lzma-no-dict,-lc1 -lp2 -pb2 $(1))
endef
define Build/lzma-no-dict
  $(STAGING_DIR_HOST)/bin/lzma e $@ $(1) $@.new
  @mv $@.new $@
endef
```

使用 `$(STAGING_DIR_HOST)/bin/lzma`（主机工具，不是目标工具）对 Image 压缩。`STAGING_DIR_HOST` 是交叉编译工具链的安装目录（`build_dir/host`）。

#### 第三段：`fit lzma $(KDIR)/image-$(DTS).dtb`

`include/image-commands.mk:464-467`：
```makefile
define Build/fit
  $(call Build/fit-its,$(1))
  $(call Build/fit-image,$(1))
endef
```

两步：
1. `fit-its` → 调用 `scripts/mkits.sh` 生成 `.its` (Image Tree Source) 文件
2. `fit-image` → 调用 `mkimage -f $@.its $@.new` 生成 `.itb` (FIT Image Blob)

`Device/Default` 中传参 `lzma` 和 `$(KDIR)/image-$(firstword $(DEVICE_DTS)).dtb`，对应 `Build/fit-its` 的参数解析：

`include/image-commands.mk:433-455`：
```makefile
define Build/fit-its
  # $(1) = "lzma", $(2) = dtb path (optional), $(3) = with-rootfs/with-initrd
  $(TOPDIR)/scripts/mkits.sh \
    -D $(DEVICE_NAME) -o $@.its \
    -C $(word 1,$(1)) \         # 压缩类型: lzma / gzip / none
    $(if $(word 2,$(1)),-d $(KERNEL_BUILD_DIR)/image-$$(basename $(word 2,$(1))),) \
    -a $(KERNEL_LOADADDR) -e $(if $(KERNEL_ENTRY),$(KERNEL_ENTRY),$(KERNEL_LOADADDR)) \
    -c $(if $(DEVICE_DTS_CONFIG),$(DEVICE_DTS_CONFIG),"config-1") \
    -A $(LINUX_KARCH) -v $(LINUX_VERSION) \
    ...
endef
```

`mkits.sh` (`scripts/mkits.sh:1-244`) 生成 DTS 格式的 `.its` 文件，其中关键节点：

```dts
/dts-v1/;
/ {
  images {
    kernel@1 {
      description = "ARM64 OpenWrt Linux-6.12";
      data = /incbin/("Image.lzma");          # 内核压缩镜像
      type = "kernel";
      arch = "arm64";
      os = "linux";
      compression = "lzma";
      load = <0x48000000>;                   # KERNEL_LOADADDR
      entry = <0x48000000>;
    };
    fdt@1 {
      description = ...;
      data = /incbin/("mt7981b-xxx.dtb");    # 编译后的 DTB
      type = "flat_dt";
    };
    // with-rootfs 时还有 rootfs@1 节点
  };
  configurations {
    default = "config-1";
    config-1 {
      kernel = "kernel@1";
      fdt = "fdt@1";
      // with-rootfs 时: loadables = "rootfs@1"
    };
  };
};
```

`mkimage -f $@.its $@.new` 将 `.its` 编译为 `.itb`（U-Boot FIT 格式），它是一个环形结构：kernel + DTB（还可以内嵌 rootfs）打包在一起。

### 2.3 DTB 编译：Image/BuildDTB

`include/image.mk:228-246`：
```makefile
define Image/BuildDTB/sub
  $(TARGET_CROSS)cpp -nostdinc -x assembler-with-cpp \
    -I$(DTS_DIR) -I$(DTS_DIR)/include \
    -I$(LINUX_DIR)/include/ \
    -I$(LINUX_DIR)/scripts/dtc/include-prefixes \
    -undef -D__DTS__ \
    -o $(2).tmp $(1)
  $(LINUX_DIR)/scripts/dtc/dtc -O dtb \
    -i$(dir $(1)) \
    -o $(2) $(2).tmp
  $(RM) $(2).tmp
endef
```

DTS 源文件在 `target/linux/mediatek/dts/mt7981b-*.dts`，编译输出到 `build_dir/linux-aarch64_cortex-a53_musl/linux-6.12/arch/arm64/boot/dts/mediatek/mt7981b-*.dtb`，然后在 Device/Build/kernel 阶段通过 `Build/append-dtb` 拼入 FIT。

### 2.4 最终内核输出

`Device/Default` 中 `KERNEL := kernel-bin | lzma | fit lzma ...dtb`，管线输出文件为：
- `$(KDIR)/image-mt7981b-<device>.itb` — FIT Image，包含压缩内核 + DTB（+ 可选 rootfs）
- 该文件在 `Device/Build/kernel:743` 通过 `cp $^ $@` 复制到 `$(BIN_DIR)/$(KERNEL_IMAGE)` = `$(BIN_DIR)/openwrt-mediatek-filogic-<device>-kernel.bin`

---
