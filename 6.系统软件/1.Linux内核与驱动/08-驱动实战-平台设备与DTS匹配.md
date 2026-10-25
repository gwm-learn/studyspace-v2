---
id: "os-drv-08"
title: "驱动实战：平台设备与 DTS 匹配"
cluster: os
layer: L2
status: draft
confidence: medium
platform: ["Linux 5.15"]
source:
  - type: doc
    ref: "Linux kernel Documentation/driver-api/driver-model/platform.rst"
verified_on: null
tags: ["driver", "platform", "dts", "probe"]
aliases: ["平台驱动", "probe"]
created: 2026-10-24
updated: 2026-10-24
---

# 驱动实战：平台设备与 DTS 匹配

> 解决什么问题：驱动为什么不 probe、资源怎么拿、`-EPROBE_DEFER` 怎么处理。
> 不解决：总线协议细节（I2C/SPI/PCIe 按各自框架）。

## 1. 匹配链路

```text
DTS node (compatible) → platform_device → platform_driver.of_match_table → probe()
```

- `compatible` 从具体到通用：`vendor,board-xxx`、`vendor,soc-xxx`。
- 内核用 `of_match_table` 匹配。
- 匹配成功后调用 `probe`。

## 2. 驱动骨架

```c
static int demo_probe(struct platform_device *pdev) {
    struct resource *res;
    void __iomem *base;
    int irq;

    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    base = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(base)) return PTR_ERR(base);

    irq = platform_get_irq(pdev, 0);
    if (irq < 0) return irq;

    /* 初始化硬件/注册子系统 */
    return 0;
}

static int demo_remove(struct platform_device *pdev) { return 0; }

static const struct of_device_id demo_of_match[] = {
    { .compatible = "vendor,demo" },
    { }
};
MODULE_DEVICE_TABLE(of, demo_of_match);

static struct platform_driver demo_driver = {
    .probe = demo_probe,
    .remove = demo_remove,
    .driver = {
        .name = "demo",
        .of_match_table = demo_of_match,
    },
};
module_platform_driver(demo_driver);
```

## 3. 资源获取

| 资源 | API |
|---|---|
| 寄存器 | `platform_get_resource` + `devm_ioremap_resource` |
| 中断 | `platform_get_irq` |
| GPIO | `devm_gpiod_get` |
| 时钟 | `devm_clk_get` |
| 复位 | `devm_reset_control_get` |
|  regulator | `devm_regulator_get` |
| DMA | `dma_request_chan` |

用 `devm_*` 自动释放，减少错误路径泄漏。

## 4. DTS 对应

```dts
demo@10000000 {
    compatible = "vendor,demo";
    reg = <0x10000000 0x1000>;
    interrupts = <0 42 4>;
    clocks = <&clk 1>;
    reset-gpios = <&pio 5 GPIO_ACTIVE_LOW>;
    status = "okay";
};
```

## 5. 常见返回值

| 返回值 | 含义 |
|---|---|
| `-ENODEV` | 不匹配/硬件不存在 |
| `-ENOMEM` | 内存不足 |
| `-EBUSY` | 资源被占用 |
| `-EPROBE_DEFER` | 依赖未就绪，稍后重试 |
| `-EINVAL` | 参数/DTS 错 |

`-EPROBE_DEFER` 不是错误；确保依赖（时钟/ regulator/GPIO）先注册。

## 6. 调试

```bash
ls /sys/bus/platform/drivers/demo/
cat /sys/bus/platform/devices/*/driver
dmesg | grep -i demo
cat /proc/device-tree/.../compatible
```

- 看 `driver` 链接是否存在。
- 看 `dmesg` 的 probe 日志/错误码。
- 用 `dev_info/dev_err` 打印资源。

## 7. 常见坑

| 现象 | 原因 |
|---|---|
| 不 probe | compatible 不匹配/status disabled |
| probe 失败 | 资源名/索引错 |
| 一直 defer | 依赖驱动未加载 |
| 卸载崩溃 | 未注销/未释放 |
| 寄存器读写错 | 地址/位宽/字节序 |
| 中断不进 | 触发类型/中断号 |

## 8. 相关

- [设备树与 DTS](../../5.嵌入式系统/1.硬件与板级/02-设备树与DTS.md)
- [驱动模型](04-驱动模型.md)
- [字符设备](07-驱动实战-字符设备.md)
- [内存管理与调试](09-内存管理与调试.md)
