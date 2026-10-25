---
id: "net-route-03"
title: "策略路由与多 WAN"
cluster: net
layer: L2
status: draft
confidence: medium
platform: ["Linux 5.15", "OpenWrt 23.05"]
source:
  - type: doc
    ref: "ip-rule(8), ip-route(8), mwan3"
verified_on: null
tags: ["policy-routing", "multi-wan", "mwan3", "failover"]
aliases: ["策略路由", "多WAN"]
created: 2026-10-24
updated: 2026-10-24
---

# 策略路由与多 WAN

> 解决什么问题：不同来源/业务走不同出口；主链路故障自动切换；避免“路由有但流量不走”。
> 不解决：具体运营商选路策略/业务分流规则。

## 1. 路由决策的三层

```text
目的地址 → 路由表 → 出接口/下一跳
   ↑
策略规则（源/目的/mark/入接口）决定用哪张表
```

Linux 默认三张表：

| 表 | 用途 |
|---|---|
| local | 本机地址/广播 |
| main | 默认路由 |
| default | 兜底 |

自定义表（如 `100`）用于策略路由。

## 2. 基本命令

```bash
ip rule show
ip route show table main
ip route show table 100

ip rule add from 192.168.2.0/24 table 100
ip route add default via 192.0.2.1 dev wan2 table 100

ip rule add fwmark 0x1 table 100
ip route add default via 192.0.2.1 dev wan2 table 100
```

规则优先级：`ip rule` 的 `pref` 越小越先匹配；默认 `32766` main、`32767` default。

## 3. 三种常见做法

### 3.1 按源地址

```bash
ip rule add from 192.168.10.0/24 table 10
ip route add default via 10.0.0.1 table 10
```

适合：不同 LAN/访客网络走不同出口。

### 3.2 按 fwmark

```bash
# nftables/iptables 打标
nft add rule inet fw4 mangle_prerouting ip daddr 203.0.113.0/24 meta mark set 0x1
# 或 iptables -t mangle -A PREROUTING ... -j MARK --set-mark 0x1

ip rule add fwmark 0x1 table 10
```

适合：按应用/目的/策略分流。

### 3.3 按入接口

```bash
ip rule add iif br-lan table 10
```

适合：多 LAN/多租户。

## 4. 多 WAN 故障切换

### 4.1 组成

```text
健康检查（ping/DNS/HTTP） → 选路 → 写默认路由/规则 → 清理会话
```

| 方案 | 特点 |
|---|---|
| 静态双默认 + 权重 | 简单，无故障检测 |
| mwan3 | 健康检查、权重、故障切换、策略 |
| 自研脚本 | 灵活，维护成本高 |

### 4.2 mwan3 关键

- `config interface` 定义成员与权重。
- `config member` 绑定接口/ metric。
- `config policy` 组合成员（主备/负载均衡）。
- `config rule` 按源/目的/端口选策略。
- 健康检查失败 → 标记 down → 切换。

### 4.3 切换时要做什么

1. 更新默认路由/规则。
2. 清理 conntrack（旧会话绑定旧出口）。
3. 更新 NAT/masq 接口。
4. 更新 DNS/策略路由。
5. 记录切换原因/时间。

## 5. 常见坑

| 现象 | 原因 |
|---|---|
| 加了 rule 仍走 main | 规则优先级/表为空/没默认路由 |
| 回程不对称 | 只配去程，未配回程/NAT |
| 切换后旧连接卡死 | conntrack 未清理 |
| 双 WAN 都断 | 健康检查误判/上游 DNS |
| 策略路由影响本机 | local 表/输出链未考虑 |
| IPv6 不生效 | 只配了 v4 规则/表 |

## 6. 排查命令

```bash
ip rule show
ip route get 8.8.8.8
ip route get 8.8.8.8 from 192.168.2.10
conntrack -L | head
nft list ruleset | grep -i mark
logread | grep -i mwan
```

`ip route get` 是最直接的验证：它按真实规则返回出口/源地址。

## 7. 设计建议

- 规则少而清晰；优先级文档化。
- 源地址策略优先于目的策略（按业务）。
- 故障切换要有迟滞，避免抖动。
- 切换后清理 conntrack。
- 监控每条链路的时延/丢包，不只看 up/down。

## 8. 实验

1. 两个 WAN，按 LAN 分流。
2. 拔掉主 WAN，观察切换时间与丢包。
3. 用 `ip route get` 验证每条规则。
4. 用 `conntrack -L` 看旧会话是否清理。

## 9. 相关

- [路由与策略](01-路由与策略.md)
- [NAT 与 conntrack](../../8.数据面工程/03-NAT与conntrack.md)
- [OpenWrt 路由表管理](../../7.平台与集成/1.OpenWrt/4.网络业务/3.关键组件服务/01-路由表管理.md)
