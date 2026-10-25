---
id: "hw-02"
title: "设备树与 DTS"
cluster: hw
layer: L2
status: draft
confidence: medium
platform: ["Linux 5.15", "OpenWrt 23.05"]
source:
  - type: doc
    ref: "Devicetree Specification v0.4"
verified_on: null
tags: ["dts", "device-tree", "board"]
aliases: ["DTS", "设备树"]
created: 2026-10-24
updated: 2026-10-24
---

# 设备树与 DTS

> 解决什么问题：内核如何知道板子上有什么硬件、地址是多少、用哪个驱动。
> 不解决：驱动内部实现（见 [驱动模型](../../6.%E7%B3%BB%E7%BB%9F%E8%BD%AF%E4%BB%B6/1.Linux%E5%86%85%E6%A0%B8%E4%B8%8E%E9%A9%B1%E5%8A%A8/04-%E9%A9%B1%E5%8A%A8%E6%A8%A1%E5%9E%8B.md)）。

## 1. 设备树在启动链中的位置

```text
U-Boot 加载 kernel + DTB
        │
        ▼
kernel 解析 DTB → 生成 device_node/device → 匹配 driver 的 compatible
        │
        ▼
probe() → 注册 netdev / gpio / led / mtd ...
```

DTB 是**硬件描述**，不是驱动。驱动通过 `compatible` 匹配，通过 `reg`/`interrupts`/`gpios` 等拿到资源。

## 2. 基本语法

```dts
/dts-v1/;

/ {
    model = "My Router";
    compatible = "vendor,my-router", "mediatek,mt7981";

    chosen {
        bootargs = "console=ttyS0,115200";
    };

    memory@40000000 {
        device_type = "memory";
        reg = <0x40000000 0x10000000>;   /* 256 MiB */
    };

    leds {
        compatible = "gpio-leds";

        led_status: led-status {
            label = "status";
            gpios = <&pio 12 GPIO_ACTIVE_HIGH>;
            linux,default-trigger = "heartbeat";
        };
    };

    keys {
        compatible = "gpio-keys";

        reset {
            label = "reset";
            gpios = <&pio 1 GPIO_ACTIVE_LOW>;
            linux,code = <KEY_RESTART>;
        };
    };
};
```

### 2.1 常用属性

| 属性 | 作用 |
|---|---|
| `compatible` | 驱动匹配字符串，从具体到通用 |
| `reg` | 地址 + 长度（`<addr len>`） |
| `interrupts` | 中断号与触发类型 |
| `gpios` / `gpio` | GPIO 句柄与有效电平 |
| `pinctrl-names` / `pinctrl-0` | 引脚复用状态 |
| `status = "okay"/"disabled"` | 是否启用 |
| `phandle` | 被其他节点引用的句柄 |
| `aliases` | 固定设备名（如 `ethernet0`） |
| `chosen` | 启动参数、stdout 路径 |

### 2.2 路由板常见节点

| 硬件 | 节点/子系统 | 关键点 |
|---|---|---|
| 以太网 MAC | `ethernet@...` | `phy-handle`、`phy-mode`、`mac-address` |
| 交换机 | `switch@...` / DSA | 端口、CPU 口、PHY 地址 |
| Flash | `spi-nor` / `spi-nand` | `reg`、分区子节点 |
| LED | `gpio-leds` | GPIO、默认 trigger |
| 按键 | `gpio-keys` | GPIO、`linux,code` |
| 复位 | `gpio-keys` 或 `restart` | 长按时间由用户态处理 |
| Wi-Fi | `wifi@...` / PCIe | 中断、电源、校准数据 |
| USB | `usb@...` | `dr_mode`、`vbus-supply` |
| 风扇/温控 | `hwmon` / `thermal` | 传感器、PWM |

## 3. OpenWrt 中 DTS 在哪

| 位置 | 说明 |
|---|---|
| `target/linux/<target>/dts/` | 板级 DTS |
| `target/linux/<target>/<subtarget>/` | 平台补丁、设备定义 |
| `target/linux/<target>/image/` | 镜像与设备 profile |
| `build_dir/.../linux-*/arch/.../dts/` | 编译后的 DTS/DTB |
| `/sys/firmware/devicetree/base/` | 运行时设备树 |

编译与反编译：

```bash
# 反编译运行时 DTB（需要 dtc）
dtc -I fs -O dts /sys/firmware/devicetree/base > running.dts

# 从源码编译（在内核构建目录）
make ARCH=arm64 dtbs
```

## 4. 改 DTS 的安全流程

1. 备份原 DTS/DTB 与分区。
2. 只改必要节点，保留 `status = "disabled"` 的节点不动。
3. 编译出 DTB 后先校验：`dtc -I dtb -O dts` 能正常反编译。
4. 通过 TFTP/救砖路径先试启动，不要直接写死。
5. 确认 `dmesg` 中驱动 probe 成功、`/sys/firmware/devicetree` 可见。
6. 记录改动到项目 ADR。

## 5. 常见错误

| 现象 | 常见原因 |
|---|---|
| 驱动不 probe | `compatible` 拼错、`status` 为 disabled |
| 地址/长度错 | `reg` 的地址或长度写错、单位地址不匹配 |
| GPIO 无效 | 引脚被 pinctrl 占用、有效电平反了 |
| 网口不通 | `phy-mode`/`phy-handle` 错、MDIO 地址错 |
| 分区找不到 | `mtd` 分区与 U-Boot `mtdparts` 不一致 |
| 启动卡住 | `chosen/bootargs` 的 console 错、memory 节点错 |
| 编译报错 | phandle 未定义、include 路径错、节点重名 |

## 6. 调试命令

```bash
# 查看模型与兼容性
tr '\0' '\n' < /proc/device-tree/model
tr '\0' '\n' < /proc/device-tree/compatible

# 查看某个节点
ls /proc/device-tree/
find /proc/device-tree -name compatible | xargs -I{} sh -c 'echo {}; tr "\0" "\n" < {}'

# 查看 GPIO
gpioinfo
cat /sys/kernel/debug/gpio

# 查看分区
cat /proc/mtd
```

## 7. 待实测/待项目参数
- [ ] 目标板的完整 DTS 与关键节点注释。
- [ ] 交换机/DSA 端口的实际布局。
- [ ] Wi-Fi 校准数据分区与 DTS 的对应关系。
- [ ] 一次"改 LED/按键"的完整实验记录。

## 8. 相关

- [启动链与 U-Boot](01-%E5%90%AF%E5%8A%A8%E9%93%BE%E4%B8%8EU-Boot.md)
- [存储与分区](03-%E5%AD%98%E5%82%A8%E4%B8%8E%E5%88%86%E5%8C%BA.md)
- [接口与外设](04-%E6%8E%A5%E5%8F%A3%E4%B8%8E%E5%A4%96%E8%AE%BE.md)
- [驱动模型](../../6.%E7%B3%BB%E7%BB%9F%E8%BD%AF%E4%BB%B6/1.Linux%E5%86%85%E6%A0%B8%E4%B8%8E%E9%A9%B1%E5%8A%A8/04-%E9%A9%B1%E5%8A%A8%E6%A8%A1%E5%9E%8B.md)
