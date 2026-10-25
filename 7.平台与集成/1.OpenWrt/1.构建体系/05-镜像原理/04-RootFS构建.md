---
id: "openwrt-build-04"
title: RootFS构建
cluster: "openwrt-build"
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "image", "build"]
aliases: ["RootFS构建"]
created: 2026-10-24
updated: 2026-10-24
---
# RootFS构建


### 3.1 target-dir 的准备

**第一步：基础文件系统** (`include/rootfs.mk:71-101` 的 `prepare_rootfs`)：
1. 从 `$(TARGET_DIR_ORIG)` 复制到 `$(TARGET_DIR)`（ORIG = 编译后的原始根文件系统快照）
2. 标记设备节点 `/dev`（`mknod`）
3. 运行所有包 postinst 脚本（`Package/<pkg>/postinst`）
4. 对 opkg 状态文件修正（将 `Status: user` 改为 `ok`）

**第二步：per-device 定制** (`include/image.mk:400-423` 的 `target-dir-%`)：
- 如果 `CONFIG_TARGET_PER_DEVICE_ROOTFS` 开启，每个设备有独立 rootfs（通过不同 DEVICE_PACKAGES 组合产生不同包集合）
- 包通过 `opkg`（或 `apk`）安装到 `$(TARGET_DIR)`

**第三步：$(TOPDIR)/files 覆盖** (`include/image.mk:423`)：
- `$(call prepare_rootfs,$(TARGET_DIR),$(TOPDIR)/files)` — 如果存在 `$(TOPDIR)/files/` 目录，其内容覆盖 target-dir（用于用户自定义配置）

### 3.2 文件系统镜像生成

`target/linux/mediatek/image/Makefile:25` 定义 `FILESYSTEMS := squashfs erofs`（filogic 不默认构建 jffs2 / ubifs 等）。

**SquashFS 生成** (`include/image.mk:282-303`)：
```makefile
define Image/mkfs/squashfs-common
  $(STAGING_DIR_HOST)/bin/mksquashfs4 \
    $(call mkfs_target_dir,$(1)) $@ \
    -nopad -noappend -root-owned \
    -comp $(SQUASHFSCOMP) $(SQUASHFSOPT)
endef
# SQUASHFSCOMP: gzip (默认); 如果 CONFIG_SQUASHFS_XZ=y 则为 xz
# SQUASHFS_BLOCK_SIZE: 128k (CONFIG_TARGET_SQUASHFS_BLOCK_SIZE)k
# SQUASHFSOPT: -p '/dev d 755 0 0' -p '/dev/console c 600 0 0 5 1'
```

输出：`build_dir/linux-.../root.squashfs`（MD5-based id 后缀）

**EROFS 生成** (`include/image.mk:327-331`)：
```makefile
define Image/mkfs/erofs
  env -u SOURCE_DATE_EPOCH $(STAGING_DIR_HOST)/bin/mkfs.erofs \
    -z$(EROFSCOMP) -C$(EROFS_PCLUSTERSIZE) $(EROFSOPT) \
    $@ $(call mkfs_target_dir,$(1))
endef
# EROFSCOMP: lz4hc,12 (默认); CONFIG_EROFS_FS_ZIP_LZMA 时为 lzma,109
```

### 3.3 UBI/UBIFS：NAND 设备的特殊处理

MT7981 的 NAND 设备不使用纯 squashfs 镜像，而是用 **UBI + UBIFS** 或 **UBI + squashfs**（`KERNEL_IN_UBI := 1`）。相关宏定义在 `target/linux/mediatek/image/filogic.mk:5-9`：

```makefile
define Image/Prepare
  rm -f $(KDIR)/ubi_mark
  echo -ne '\xde\xad\xc0\xde' > $(KDIR)/ubi_mark   # UBI 坏块标记
endef
```

UBI 镜像的生成由 `Build/ubinize-image` 或 `Build/append-ubi` 触发，不是简单的 squashfs。以下是 `scripts/ubinize-image.sh:14-98` 的卷结构逻辑：

```bash
ubivol() {                                    # 输出 ubinize.cfg 卷条目
  echo "[$name]"
  echo "mode=ubi"
  echo "vol_id=$volid"
  echo "vol_type=$voltype"                    # dynamic (可动态调整) 或 static
  echo "vol_name=$name"
  echo "vol_size=${size}"
}
# 最终卷布局 (典型):
# vol_id=0: ubootenv  (1MiB, dynamic)
# vol_id=1: ubootenv2 (1MiB, dynamic)
# vol_id=2: kernel    (kernel in UBI, static, 可选 KERNEL_IN_UBI=1)
# vol_id=3: rootfs    (autoresize for UBIFS; 固定 1k-block-aligned for squashfs)
# vol_id=4: rootfs_data (autoresize for squashfs, JFFS2 兼容层)
```

---
