---
id: "net-mcast-04"
title: "组播转发与 IGMP Snooping"
cluster: net
layer: L2
status: draft
confidence: medium
platform: ["Linux 5.15", "OpenWrt 23.05"]
source:
  - type: rfc
    ref: "RFC 1112 (IGMPv1), RFC 2236 (IGMPv2), RFC 3376 (IGMPv3), RFC 3810 (MLDv2)"
verified_on: null
tags: ["multicast", "igmp", "mld", "snooping", "iptv"]
aliases: ["组播", "IGMP Snooping", "IPTV"]
created: 2026-10-24
updated: 2026-10-24
---

# 组播转发与 IGMP Snooping

> 解决什么问题：IPTV/组播业务泛洪、换台慢、只有第一个终端能看、Wi-Fi 组播卡。
> 不解决：具体运营商组播源/IGMP 版本要求。

## 1. 组播模型

```text
源 ──(组播路由)── 路由器 ──(二层)── 交换机/AP ── 接收者
```

- 源只发一份；网络按需复制。
- 接收者通过 IGMP（IPv4）/MLD（IPv6）加入/离开组。
- 组播地址：IPv4 `224.0.0.0/4`；IPv6 `ff00::/8`。
- 组播 MAC：IPv4 `01:00:5e:xx:xx:xx`；IPv6 `33:33:xx:xx:xx:xx`。

## 2. IGMP/MLD

| 版本 | 特点 |
|---|---|
| IGMPv1 | 查询/报告，无 Leave |
| IGMPv2 | 增加 Leave，兼容 v1 |
| IGMPv3 | 源过滤（SSM） |
| MLDv1 | IPv6 版 IGMPv2 |
| MLDv2 | IPv6 版 IGMPv3 |

报文：

- 查询（Query）：路由器/交换机周期性询问。
- 报告（Report）：主机加入。
- 离开（Leave）：主机离开（v2+）。

## 3. 二层：Snooping

交换机默认把组播当广播泛洪。Snooping 偷听 IGMP/MLD，建立“组播 MAC → 端口”表：

```text
收到 Join → 记录端口 → 只向该端口转发
收到 Leave → 查询是否还有其他成员 → 删除
```

关键配置：

- 全局开启 snooping。
- 路由器端口（mrouter）识别：静态配置或动态学习（IGMP Query/PIM Hello）。
- 快速离开（fast leave）用于单终端端口，减少换台延迟。
- 未知组播处理：泛洪 or 丢弃（按业务）。

## 4. 三层：组播路由

| 协议 | 用途 |
|---|---|
| IGMP Proxy | 上游/下游成员聚合，常见于家庭网关 |
| PIM-SM | 稀疏模式，共享树/最短路径树 |
| PIM-DM | 密集模式，泛洪+剪枝 |
| SSM | 指定源组播 |

家庭网关常见：`igmpproxy` 把 WAN 侧组播转到 LAN；或内核 IGMP proxy + 防火墙放行。

## 5. OpenWrt 关注点

```bash
cat /proc/net/igmp
bridge mdb show
ip maddr show
```

- 防火墙放行 IGMP/组播（WAN 入站、LAN 转发）。
- 网桥 `multicast_snooping=1`。
- Wi-Fi 组播转单播（multicast-to-unicast），否则低速率/无重传导致卡顿。
- 组播 VLAN/独立 SSID 隔离 IPTV。

## 6. 常见故障

| 现象 | 原因 |
|---|---|
| 组播泛洪 | snooping 未开/未知组播泛洪 |
| 换台慢 | Leave 处理慢/无 fast leave |
| 只有第一个终端能看 | 未做 proxy/转发/成员管理 |
| Wi-Fi 卡 | 组播速率低/无重传/空口拥塞 |
| 跨 VLAN 不通 | mrouter/三层组播未配 |
| IPv6 组播不通 | MLD 未放行/snooping 不支持 |

## 7. 排查步骤

1. 确认接收者发出 Join（抓包）。
2. 确认交换机/网桥学到组播表。
3. 确认路由器有组播路由/代理。
4. 确认防火墙放行。
5. 确认无线组播转单播。

```bash
tcpdump -ni br-lan 'igmp or icmp6'
bridge mdb show
cat /proc/net/igmp
```

## 8. 设计建议

- IPTV 用独立 VLAN/SSID，避免与上网互相影响。
- 开启 snooping + fast leave。
- 无线组播转单播，或限制组播速率。
- 组播源/组地址规划，避免冲突。
- 监控组播流量与成员数。

## 9. 实验

1. 用 `iperf3`/`mping` 或 VLC 发组播，观察泛洪。
2. 开/关 snooping，对比端口流量。
3. 两个终端加入同一组，验证复制。
4. 抓 IGMP Join/Leave，测换台时延。

## 10. 相关

- [组播原理](02-组播.md)
- [网桥与桥接](../../8.数据面工程/06-网桥与桥接.md)
- [VLAN](../4.二层协议/01-VLAN.md)
