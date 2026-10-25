---
id: "wifi-06"
title: "漫游与 Mesh"
cluster: wifi
layer: L2
status: draft
confidence: medium
platform: ["OpenWrt 23.05"]
source: []
verified_on: null
tags: ["roaming", "mesh", "802.11r", "802.11k", "802.11v"]
aliases: ["漫游", "Mesh", "802.11r"]
created: 2026-10-24
updated: 2026-10-24
---

# 漫游与 Mesh

> 解决什么问题：多 AP 组网时，终端如何在 AP 间平滑切换；Mesh 回程怎么选。
> 不解决：单 AP 配置（→ [hostapd 与安全](05-hostapd%E4%B8%8E%E5%AE%89%E5%85%A8.md)）。

## 1. 三种"漫游"不要混

| 概念 | 说明 |
|---|---|
| 终端自主漫游 | 终端自己决定何时切，AP 只能引导 |
| 802.11k | AP 提供邻居报告，帮助终端发现候选 |
| 802.11v | BSS Transition Management，AP 建议终端切换 |
| 802.11r | 快速 BSS 切换（FT），减少重认证时延 |
| 802.11s | Mesh 组网（AP 之间自组网） |

> 真正决定切换的是终端；AP 侧能做的是"提供信息 + 引导 + 降低切换成本"。

## 2. 快速切换（802.11r）

| 模式 | 说明 | 适用 |
|---|---|---|
| Over-the-Air | FT 认证帧走空口 | 通用 |
| Over-the-DS | 通过 DS 转发 | 有线回程 |
| 混合 | 兼容两种 | 过渡 |

关键配置（hostapd）：

```conf
ieee80211r=1
mobility_domain=1234
ft_over_ds=1
ft_psk_generate_local=1
r0kh=xx:xx:xx:xx:xx:xx * 00112233445566778899aabbccddeeff
r1kh=xx:xx:xx:xx:xx:xx 00112233445566778899aabbccddeeff
```

> 同一 mobility domain 内的 AP 必须共享密钥；配置不一致会导致 FT 失败并回退到完整认证。

## 3. 漫游引导

| 手段 | 说明 | 风险 |
|---|---|---|
| 信号阈值 | 低于阈值踢下线 | 踢太早导致断流 |
| 负载均衡 | 按终端数/信道利用率引导 | 误判 |
| 频段引导 | 优先 5G | 远距离覆盖差 |
| 802.11v BTM | 建议终端切换 | 终端可能不理会 |
| 弱信号剔除 | `hostapd_cli disassociate` | 粗暴，慎用 |

调参原则：先保证"不断"，再追求"快"；阈值要按现场覆盖与终端类型调。

## 4. Mesh

| 项 | 说明 |
|---|---|
| 回程 | 无线回程（5G/6G）或有线回程（Ethernet backhaul） |
| 协议 | 802.11s、厂商私有 Mesh、EasyMesh |
| 选路 | 按链路质量/跳数；环路需避免 |
| 带宽 | 无线回程与接入共享射频，跳数越多越差 |
| 配置 | 同一 Mesh ID/密钥；节点角色（控制器/代理） |

有线回程优先；无线回程要单独规划信道，避免与接入同频。

## 5. 常见问题

| 现象 | 可能原因 | 定位 |
|---|---|---|
| 走动时断流 1–3 s | 未开 802.11r / 终端不支持 | 抓 4 次握手/FT 帧 |
| 粘滞不切 | 终端策略、信号阈值 | 看 `station dump` 信号 |
| 切了但没网 | VLAN/网桥/DHCP 未同步 | 检查二层连通与地址 |
| Mesh 速率低 | 回程跳数/同频干扰 | 测回程吞吐、换信道 |
| 环路/广播风暴 | Mesh 拓扑成环、STP 未开 | 看 CPU/广播、开 STP |

## 6. 验证方法

```bash
# 终端侧持续 ping，记录切换时延/丢包
ping -i 0.2 -c 300 192.168.1.1

# AP 侧看关联与信号
iw dev wlan0 station dump
hostapd_cli all_sta

# 抓 FT 认证帧
tcpdump -ni wlan0 -e -s0 'wlan type mgt subtype auth'
```

判定：切换丢包 ≤ 2–3 个（视业务），时延抖动可接受；语音/游戏要求更高。

## 7. 待实测/待项目参数
- [ ] 目标平台的 802.11r/k/v 支持情况。
- [ ] 一次双 AP 漫游实测（时延/丢包/日志）。
- [ ] Mesh 有线/无线回程对比数据。

## 8. 相关

- [hostapd 与安全](05-hostapd%E4%B8%8E%E5%AE%89%E5%85%A8.md)
- [WiFi 排障与性能](07-WiFi%E6%8E%92%E9%9A%9C%E4%B8%8E%E6%80%A7%E8%83%BD.md)
- [网桥与桥接](../../8.%E6%95%B0%E6%8D%AE%E9%9D%A2%E5%B7%A5%E7%A8%8B/06-%E7%BD%91%E6%A1%A5%E4%B8%8E%E6%A1%A5%E6%8E%A5.md)
