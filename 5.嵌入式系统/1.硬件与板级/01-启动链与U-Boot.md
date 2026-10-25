---
id: "hw-01"
title: "启动链与 U-Boot"
cluster: hw
layer: L2
status: draft
confidence: medium
platform: ["MediaTek MT7981", "OpenWrt 23.05"]
source:
  - type: doc
    ref: "MediaTek MT7981 BootROM / ARM Trusted Firmware 流程（待确认具体文档号）"
verified_on: null
tags: ["uboot", "boot", "mt7981"]
aliases: ["U-Boot", "启动链"]
created: 2026-10-24
updated: 2026-10-24
---

# 启动链与 U-Boot

> 解决什么问题：设备上电后为什么能启动、卡在哪一步、怎么救。
> 不解决：内核初始化细节（见 [内核基础与启动](../../6.%E7%B3%BB%E7%BB%9F%E8%BD%AF%E4%BB%B6/1.Linux%E5%86%85%E6%A0%B8%E4%B8%8E%E9%A9%B1%E5%8A%A8/01-%E5%86%85%E6%A0%B8%E5%9F%BA%E7%A1%80%E4%B8%8E%E5%90%AF%E5%8A%A8.md)）。

## 1. 典型启动链

```text
上电
  │
  ▼
BootROM（芯片内固化，不可改）
  │  按 strap/熔丝选择启动介质：SPI-NOR / SPI-NAND / eMMC / SD
  ▼
BL2（Trusted Firmware-A 第二阶段，初始化 DRAM/时钟/安全环境）
  │
  ▼
FIP（含 BL31 / BL33=U-Boot proper）
  │
  ▼
U-Boot proper
  │  读环境变量、加载 kernel/DTB/rootfs
  ▼
Linux kernel → initramfs 或 rootfs → procd
```

不同平台的分段名称可能不同（MTK 常见 `BL2 + FIP`，高通常见 `XBL/SBL/ABL`），但**职责划分一致**：ROM → DRAM 初始化 → 安全监控 → 引导加载器 → 内核。

## 2. U-Boot 的关键对象

| 对象 | 作用 | 查看/修改 |
|---|---|---|
| 环境变量 | `bootcmd`、`bootargs`、`ipaddr`、`serverip` | `printenv` / `setenv` / `saveenv` |
| 启动介质 | NOR/NAND/eMMC/网络 | `mmc list`、`mtd list`、`sf probe` |
| 镜像 | kernel、DTB、rootfs、FIT | `bootm`、`booti`、`sysboot` |
| 网络 | TFTP 救砖、NFS 启动 | `dhcp`、`tftpboot` |
| 分区 | 环境、factory、kernel、rootfs | `mtdparts`、`mtd` |

### 2.1 常见命令

```text
# 查看
printenv
version
bdinfo
mmc list
mtd list
fdt print /

# 修改（临时）
setenv bootargs 'console=ttyS0,115200 root=/dev/mmcblk0p5 rootwait'
setenv bootcmd 'mmc read 0x40000000 0x0 0x1000; bootm 0x40000000'
saveenv

# 网络加载
setenv ipaddr 192.168.1.10
setenv serverip 192.168.1.2
tftpboot 0x40000000 openwrt.bin
bootm 0x40000000
```

> 地址、设备号、分区名必须按实际板子替换；不要照抄。

### 2.2 环境变量存在哪

- 通常在 Flash 的 `uboot-env` 分区，可能有主备两份。
- `saveenv` 写坏会导致默认环境回退或无法启动；改之前先 `printenv` 备份。
- OpenWrt 的 `fw_printenv/fw_setenv` 可在系统内读写（需 `/etc/fw_env.config` 正确）。

## 3. OpenWrt 的衔接

| 阶段 | OpenWrt 相关点 |
|---|---|
| U-Boot → kernel | `bootargs` 里的 `root=`、`console=`、`mtdparts=` |
| kernel → rootfs | FIT image 中的 kernel/DTB/rootfs，或独立分区 |
| rootfs → procd | `/sbin/init` → procd → `/etc/init.d/*` |
| 升级 | `sysupgrade` 写 kernel/rootfs，保留 `uboot-env` 与 factory |

## 4. 定位"卡在哪"

| 现象 | 可能阶段 | 首查 |
|---|---|---|
| 串口无任何输出 | 供电/晶振/BootROM/串口 | 电压、复位、TX/RX 交叉、波特率 |
| 有 ROM 输出但停住 | DRAM/BL2 | DDR 参数、供电、启动介质 strap |
| 进 U-Boot 但自动重启 | 看门狗/环境变量/电源 | `bootcmd`、WDT、负载时电压 |
| 内核解压后无输出 | `bootargs`/DTB/rootfs | `console=`、`root=`、分区名 |
| 挂 rootfs 失败 | 分区/文件系统/驱动 | `mtdparts`、`ubi`、`rootwait` |
| 升级后变砖 | 分区布局/镜像不匹配 | 回滚分区、TFTP 救砖 |

## 5. 救砖路径（按可用性排序）

1. **U-Boot 还在**：串口 + TFTP/USB 重新加载镜像。
2. **U-Boot 坏了，BootROM 可进**：按厂商方式进入下载模式（USB/串口/UART 引导）。
3. **BootROM 也进不去**：JTAG/拆 Flash 离线烧录（最后手段）。

> 具体按键/引脚/工具因板而异，必须查板级文档；不要凭记忆操作。

## 6. 最小检查清单

- [ ] 串口参数：波特率、数据位、停止位、流控。
- [ ] 供电：空载/满载电压，纹波，限流。
- [ ] 启动介质 strap 与实际介质一致。
- [ ] `bootargs` 的 `console` 与物理串口一致。
- [ ] `root=` 与分区表一致。
- [ ] 环境变量有备份，知道怎么恢复默认。

## 7. 待实测/待项目参数
- [ ] 目标板的实际启动介质、分区表、串口引脚。
- [ ] MT7981 BL2/FIP 的具体打包命令与签名流程。
- [ ] 厂商下载模式进入方法。
- [ ] 一次真实的救砖记录（现象/命令/结果）。

## 8. 相关

- [设备树与 DTS](02-%E8%AE%BE%E5%A4%87%E6%A0%91%E4%B8%8EDTS.md)
- [存储与分区](03-%E5%AD%98%E5%82%A8%E4%B8%8E%E5%88%86%E5%8C%BA.md)
- [构建体系/镜像原理](../../7.%E5%B9%B3%E5%8F%B0%E4%B8%8E%E9%9B%86%E6%88%90/1.OpenWrt/1.%E6%9E%84%E5%BB%BA%E4%BD%93%E7%B3%BB/05-%E9%95%9C%E5%83%8F%E5%8E%9F%E7%90%86/00-%E6%80%BB%E8%A7%88.md)
- [升级与恢复](../../7.%E5%B9%B3%E5%8F%B0%E4%B8%8E%E9%9B%86%E6%88%90/1.OpenWrt/5.%E5%8D%87%E7%BA%A7%E4%B8%8E%E6%81%A2%E5%A4%8D/00-%E6%80%BB%E8%A7%88.md)
