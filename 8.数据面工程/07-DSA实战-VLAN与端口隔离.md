---
id: "dp-dsa-07"
title: "DSA 实战：VLAN 与端口隔离"
cluster: dp
layer: L3
status: draft
confidence: medium
platform: ["OpenWrt 23.05", "Linux 5.15"]
source:
  - type: doc
    ref: "Linux kernel Documentation/networking/dsa/"
verified_on: null
tags: ["dsa", "vlan", "isolation", "bridge"]
aliases: ["DSA实战", "端口隔离"]
created: 2026-10-24
updated: 2026-10-24
---

# DSA 实战：VLAN 与端口隔离

> 解决什么问题：多网口 VLAN、Trunk、端口隔离、交换机硬件转发，不依赖 UCI 也能配通。
> 不解决：具体交换芯片寄存器（按厂商驱动）。

## 1. DSA 模型

```text
CPU port (eth0) ── DSA switch ── lan1/lan2/lan3/wan
```

- 每个交换端口是一个独立 netdev。
- 端口可加入 bridge/VLAN。
- 硬件转发在交换机内部完成，CPU 只处理需要上送/路由的包。
- 与 swconfig 的区别：端口独立、标准 ip/bridge 工具。

## 2. 拓扑示例

```text
lan1: access VLAN 10
lan2: access VLAN 10
lan3: trunk VLAN 10,20
wan : access VLAN 20
```

目标：lan1/lan2 同 VLAN 互通；lan3 可带 VLAN 10/20；wan 独立。

## 3. 配置

### 3.1 建 bridge/VLAN

```bash
ip link add br-lan type bridge
ip link set lan1 master br-lan
ip link set lan2 master br-lan

bridge vlan add dev lan1 vid 10 pvid untagged
bridge vlan add dev lan2 vid 10 pvid untagged
bridge vlan add dev lan3 vid 10
bridge vlan add dev lan3 vid 20
bridge vlan add dev br-lan vid 10 self
```

### 3.2 Trunk

```bash
bridge vlan add dev lan3 vid 10
bridge vlan add dev lan3 vid 20
```

对端交换机对应端口也要允许 10/20。

### 3.3 端口隔离

```bash
bridge link set dev lan1 isolated on
bridge link set dev lan2 isolated on
```

注意：`isolated` 只隔离二层转发；三层仍可能通过网关互通。要完全隔离用 VLAN/防火墙。

### 3.4 PVID/untagged

- `pvid`：入口无标签时打哪个 VLAN。
- `untagged`：出口是否去标签。
- Trunk 口通常 `tagged`，接入口 `pvid untagged`。

## 4. 验证

```bash
bridge vlan show
bridge link show
bridge fdb show
ip -d link show lan1
tcpdump -ni lan1 -e
```

预期：

- `bridge vlan show` 显示端口与 VLAN。
- 同 VLAN 能通，不同 VLAN 不通。
- Trunk 口抓包能看到 802.1Q 标签。

## 5. 硬件转发

- DSA 可把已知单播/广播交给交换机硬件。
- 端口镜像/ACL/风暴抑制按芯片能力。
- 硬件转发可能绕过 CPU 统计/抓包。
- 关闭/开启 offload 对比吞吐/CPU。

## 6. 常见故障

| 现象 | 原因 |
|---|---|
| VLAN 不通 | PVID/untagged/tagged 配错 |
| 同 VLAN 不通 | 端口未加入 bridge/VLAN |
| 广播风暴 | 环路/STP 未开 |
| 隔离无效 | isolated 只二层 |
| CPU 高 | 未走硬件转发/流量上送 |
| Trunk 不通 | 对端未放行 VLAN |

## 7. 与 OpenWrt 的关系

- UCI 的 `config device`/`config interface` 最终生成类似配置。
- 调试时先用 `bridge vlan` 验证，再回到 UCI。
- 不要同时手改和 UCI 管理，避免重启被覆盖。

## 8. 实验

1. 两个 access 口同 VLAN，验证互通。
2. 一个 trunk 口接对端交换机，验证多 VLAN。
3. 开/关 `isolated`，验证二层隔离。
4. 抓包看 tagged/untagged。
5. 对比硬件转发/软件转发吞吐。

## 9. 相关

- [DSA 与交换机](01-DSA与交换机.md)
- [VLAN](../3.网络科学/4.二层协议/01-VLAN.md)
- [网桥与桥接](06-网桥与桥接.md)
- [硬件加速兼容性](08-硬件加速兼容性矩阵.md)
