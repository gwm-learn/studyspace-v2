---
id: "wan-01"
title: "PPPoE 协议"
cluster: wan
layer: L1
status: draft
confidence: medium
platform: ["OpenWrt 23.05", "Linux 5.15"]
source:
  - type: rfc
    ref: "RFC 2516 (PPPoE), RFC 1661 (PPP)"
verified_on: null
tags: ["pppoe", "ppp", "wan", "dial"]
aliases: ["PPPoE", "拨号"]
created: 2026-10-24
updated: 2026-10-24
---

# PPPoE 协议

> 解决什么问题：宽带拨号的完整过程、报文、认证、MTU、抓包与失败定位。
> 不解决：运营商 BRAS 配置/账号开通。

## 1. 协议栈

```text
IP → PPP → PPPoE → Ethernet
```

- PPPoE 把 PPP 帧封装进以太网。
- 两个阶段：**Discovery（发现）** 与 **Session（会话）**。
- 会话通过 PADT 终止（常被口语化称为 Terminate 阶段）。

## 2. 报文

| 报文 | 方向 | 作用 |
|---|---|---|
| PADI | Client → 广播 | 寻找 BRAS |
| PADO | BRAS → Client | 提供 Service-Name/AC |
| PADR | Client → BRAS | 选择 BRAS/请求会话 |
| PADS | BRAS → Client | 分配 Session ID |
| PADT | 双向 | 终止会话 |

PPPoE 头：

| 字段 | 长度 | 说明 |
|---|---:|---|
| Version/Type | 1 | 0x11 |
| Code | 1 | 0x09 PADI/0x07 PADO/0x19 PADR/0x65 PADS/0xa7 PADT |
| Session ID | 2 | Discovery 为 0；会话为分配值 |
| Length | 2 | 载荷长度 |

## 3. Discovery

```text
Client ── PADI(广播) ──► BRAS(s)
Client ◄─ PADO(单播) ─── BRAS
Client ── PADR(单播) ──► 选中的 BRAS
Client ◄─ PADS(单播) ─── 分配 Session ID
```

- PADI 可带 Service-Name/TAG。
- 多个 PADO 时客户端选一个（按策略）。
- PADS 后进入 Session，后续帧带 Session ID。

## 4. Session：PPP 三阶段

```text
LCP → 认证（PAP/CHAP）→ NCP（IPCP/IPv6CP）
```

### 4.1 LCP

- 协商 MRU、认证协议、魔术字、LCP echo。
- 失败：LCP 超时/配置不匹配。

### 4.2 认证

| 方式 | 特点 |
|---|---|
| PAP | 明文口令，弱 |
| CHAP | 挑战/响应，常见 |
| MS-CHAP | 微软扩展 |

失败：账号/密码/绑定/MAC。

### 4.3 NCP/IPCP

- 协商 IP 地址、DNS。
- IPv6 用 IPv6CP + DHCPv6/RA。
- 失败：地址池/策略。

## 5. MTU/MRU

- PPPoE 头 8 字节 + PPP 2 字节 → 有效 MTU 通常 1492。
- 不调会导致大包黑洞（能 ping 不能网页）。
- MSS clamp：`TCP MSS = MTU - 40`（IPv4）/`-60`（IPv6）。

```bash
# OpenWrt 常见
option mtu '1492'
# 防火墙 MSS clamp
```

## 6. 会话保持/断开

- LCP echo 保活；超时重拨。
- PADT 终止；一端发 PADT 后会话失效。
- 运营商可能因空闲/策略断开。

## 7. OpenWrt 配置（示意）

```uci
config interface 'wan'
    option proto 'pppoe'
    option device 'wan'
    option username 'user'
    option password 'pass'
    option ipv6 '1'
    option mtu '1492'
    option keepalive '5 3'
```

> 具体选项随版本；VLAN 在 `device`/`network` 配。

## 8. 抓包

```bash
tcpdump -ni wan -s0 -w pppoe.pcap 'pppoe or pppoes'
```

看：

- 有没有 PADO/PADS。
- LCP 是否完成。
- 认证失败码。
- IPCP 是否拿到地址/DNS。
- 是否有 PADT/重复 PADI。

## 9. 故障定位

| 阶段 | 现象 | 首查 |
|---|---|---|
| Discovery | 无 PADO | 线路/光猫桥接/VLAN |
| LCP | 超时 | MRU/认证/上游 |
| 认证 | 失败 | 账号/密码/绑定 |
| IPCP | 无地址 | 地址池/策略 |
| 数据 | 能拨不通 | 路由/NAT/MTU |
| 稳定 | 频繁断 | 保活/线路/负载 |

## 10. 设计/运维建议

- 失败重试 + 退避，避免风暴。
- 记录失败阶段/错误码。
- MTU/MSS 默认处理。
- 监控在线率/时延。
- 现场记录 VLAN/账号/光功率。

## 11. 相关

- [PPP 协议栈](../4.二层协议/05-PPP.md)
- [OpenWrt PPPoE 配置](../../7.平台与集成/1.OpenWrt/4.网络业务/1.WAN/01-PPPoE配置.md)
- [PPPoE 失败案例](../../11.应用与案例/5.运维与故障案例/02-PPPoE拨号失败.md)
- [抓包方法](../../10.工程方法/5.测试与实验/02-抓包方法.md)
