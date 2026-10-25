---
id: "net-09"
title: "IPv6 过渡与 CPE 部署"
cluster: net
layer: L2
status: draft
confidence: medium
platform: ["OpenWrt 23.05", "Linux 5.15"]
source:
  - type: rfc
    ref: "RFC 6333 (DS-Lite), RFC 6877 (464XLAT), RFC 6146 (NAT64), RFC 8415 (DHCPv6)"
verified_on: null
tags: ["ipv6", "ds-lite", "464xlat", "nat64", "cpe", "pd"]
aliases: ["IPv6过渡", "DS-Lite", "464XLAT"]
created: 2026-10-24
updated: 2026-10-24
---

# IPv6 过渡与 CPE 部署

> 解决什么问题：运营商只给 IPv6 时，如何让 IPv4 业务可用；CPE 的 WAN/LAN 前缀怎么分、怎么放行、怎么排障。
> 不解决：IPv6 报文/ND 基础（见 [IPv6 体系](07-IPv6体系.md)）。

## 1. 过渡技术全景

| 技术 |  encapsulation | 谁做翻译 | 适用 |
|---|---|---|---|
| 双栈 | 无 | 无 | 最常见 |
| DS-Lite | IPv4-in-IPv6 隧道 | AFTR（运营商） | 只有 v6 接入，终端仍 v4 |
| 464XLAT | CLAT（终端/CPE）+ NAT64 | CLAT + NAT64 | 终端应用只支持 v4 |
| NAT64/DNS64 | 无隧道 | 运营商 NAT64 | 纯 v6 网络访问 v4 |
| MAP-E/MAP-T | 无/隧道 | 运营商 | 地址+端口映射 |
| 6rd | IPv6-in-IPv4 | 运营商 | 早期过渡 |

### 1.1 DS-Lite

```text
CPE( B4 ) ── IPv6 隧道 ── AFTR ── IPv4 Internet
```

- CPE 把内网 IPv4 包封装进 IPv6，送到 AFTR。
- AFTR 做 NAT44；CPE 不做 NAT（或做少量）。
- 关键：隧道 MTU、AFTR 地址发现（DHCPv6 option 64）、IPv6 防火墙。

### 1.2 464XLAT

```text
App(v4) → CLAT(v4→v6) → NAT64(v6→v4) → v4 服务
```

- CLAT 在 CPE/终端内，把 v4 包转成 v6。
- NAT64 在运营商侧，把 v6 转回 v4。
- DNS64 合成 AAAA，让终端以为服务是 v6。
- 关键：CLAT 前缀（通常 `64:ff9b::/96`）、DNS64、MTU、应用兼容性。

## 2. CPE 的 WAN 侧

### 2.1 常见组合

| 运营商 | WAN 地址 | LAN 前缀 | 备注 |
|---|---|---|---|
| DHCPv6-PD | IA_NA 或 SLAAC | IA_PD | 最常见 |
| SLAAC + RDNSS | SLAAC | 静态/ULA/PD | 无 DHCPv6 |
| 静态 | 手工 | 手工 | 专线 |
| DS-Lite | IPv6 + 隧道 | PD | v4 业务走 AFTR |

### 2.2 前缀委派（PD）

```text
WAN: 2001:db8:abcd::/56
  ├─ LAN1: 2001:db8:abcd:1::/64
  ├─ LAN2: 2001:db8:abcd:2::/64
  └─ Guest: 2001:db8:abcd:3::/64
```

- 每个 LAN 一个 /64（SLAAC 要求）。
- 从 PD 中按顺序/哈希分配，避免冲突。
- 前缀续期失败时保留旧前缀一段（preferred/valid lifetime），避免 LAN 立刻断。
- 前缀变化要更新 RA、DHCPv6、防火墙、DNS。

## 3. LAN 侧

- RA：`A=1` 允许 SLAAC；`M/O` 按是否用 DHCPv6。
- DHCPv6：有状态（IA_NA）/无状态（DNS 等）。
- RDNSS/DNSSL：RA 携带 DNS。
- 防火墙：默认拒绝入站，放行必要 ICMPv6。

## 4. 防火墙要点

| 规则 | 原因 |
|---|---|
| 允许 ICMPv6 NS/NA/RS/RA | ND 依赖 |
| 允许 DAD | 地址冲突检测 |
| 允许 Packet Too Big | PMTU |
| 允许 DHCPv6 客户端 | UDP 546→547 |
| 默认拒绝入站 | IPv6 无 NAT，暴露 |
| 限制链路本地 | 防上游探测 |

> 为了“安全”封掉全部 ICMPv6 是最常见的错误：会导致地址不可用/PMTU 黑洞。

## 5. MTU 与 PMTU

- 隧道（DS-Lite/464XLAT）有封装开销，MTU 要减。
- 典型：以太网 1500 → 隧道 1452/1480（按封装）。
- 依赖 ICMPv6 Packet Too Big；被封会导致大包黑洞（能 ping 不能网页）。

## 6. 配置片段（OpenWrt 思路）

```uci
config interface 'wan6'
    option proto 'dhcpv6'
    option reqaddress 'try'
    option reqprefix 'auto'

config interface 'lan'
    option proto 'static'
    list ip6addr '2001:db8:abcd:1::1/64'
    option ip6assign '64'
```

> 具体选项随版本；以 `odhcp6c`/`odhcpd` 文档为准。

## 7. 验证与排障

```bash
ip -6 addr
ip -6 route
ip -6 neigh
cat /proc/sys/net/ipv6/conf/all/forwarding
tcpdump -ni any 'icmp6 or udp port 546 or udp port 547'
rdisc6 wan0
ping6 -c3 2001:4860:4860::8888
tracepath6 2001:4860:4860::8888
```

| 现象 | 首查 |
|---|---|
| WAN 只有 fe80 | RA 未到/M/O/DHCPv6 |
| 有地址不通 | 默认路由/防火墙 ICMPv6/上游 |
| LAN 无 v6 | RA 未开/前缀无效/A/M/O |
| 能 ping 不能网页 | PMTU/DNS |
| 一段时间断 | 租约/前缀续期 |
| v4 应用在纯 v6 失败 | 464XLAT/NAT64/DNS64 |

## 8. 设计取舍

| 选择 | 优点 | 代价 |
|---|---|---|
| 双栈 | 兼容最好 | 地址/运维复杂 |
| DS-Lite | 运营商侧集中 NAT | CPE 隧道/MTU |
| 464XLAT | 终端透明 | CLAT/DNS64 复杂 |
| NAT64 | 纯 v6 简洁 | v4 字面地址应用不兼容 |

## 9. 检查表

- [ ] WAN 能拿到 IA_NA/IA_PD。
- [ ] 每个 LAN 有 /64，无冲突。
- [ ] RA/DHCPv6 配置一致。
- [ ] ICMPv6 必要类型放行。
- [ ] 隧道 MTU/MSS 正确。
- [ ] 前缀续期/变化有处理。
- [ ] DNS（RDNSS/DHCPv6/DNS64）可用。

## 10. 相关

- [IPv6 体系](07-IPv6体系.md)
- [防火墙](../../8.数据面工程/02-Netfilter与防火墙.md)
- [接入协议](../2.接入协议/00-总览.md)
- [运营商认证](../../4.通信科学/2.蜂窝与终端/14-运营商认证.md)
