---
id: "ops-case-02"
title: "案例：PPPoE 拨号失败"
cluster: ops
layer: L4
status: draft
confidence: low
platform: []
source: []
verified_on: null
tags: ["pppoe", "case", "troubleshooting", "wan"]
aliases: ["PPPoE失败"]
created: 2026-10-24
updated: 2026-10-24
---

# 案例：PPPoE 拨号失败

> 说明：这是“定位框架 + 常见根因”，具体日志/现象需按现场替换。

## 1. 现象

- WAN 无 IPv4 地址；`pppd` 反复重连。
- 日志出现 PADI/PADO 超时、LCP 超时、认证失败、IPCP 失败。
- 有时能拨上但很快断。

## 2. 分层定位

```text
物理/链路 → PPPoE Discovery → LCP → 认证 → IPCP → 路由/NAT → 业务
```

| 层 | 证据 | 命令 |
|---|---|---|
| 物理 | 光猫/线路/灯 | 查看光功率/网口 |
| Discovery | 有无 PADO/PADS | `tcpdump -ni wan 'pppoe'` |
| LCP | 协商是否完成 | `logread | grep pppd` |
| 认证 | CHAP/PAP 失败 | 日志/账号 |
| IPCP | 是否拿到地址/DNS | `ifstatus wan` |
| 路由/NAT | 有地址不通 | `ip route`/`nft` |
| 业务 | DNS/MTU | `ping`/`curl` |

## 3. 关键命令

```bash
logread | grep -i -E 'ppp|pppoe'
ps | grep pppd
ifstatus wan
ip addr show
ip route
tcpdump -ni wan -s0 'pppoe or pppoes'
cat /etc/config/network
```

## 4. 常见根因

### 4.1 Discovery 失败

| 原因 | 验证 |
|---|---|
| 线路/光猫未桥接 | 光猫状态/直连 PC 拨号 |
| VLAN 错 | 运营商 VLAN 配置 |
| PPPoE 中继缺失 | 上游交换机 |
| 网口/驱动 | `ethtool`/`dmesg` |

### 4.2 认证失败

- 账号/密码错。
- 服务名（Service-Name）不匹配。
- 绑定 MAC/端口。
- 账号被限速/停机。

### 4.3 IPCP/路由

- 拿到地址但无默认路由。
- DNS 未下发。
- MTU/MSS 不对（能 ping 不能网页）。
- NAT/防火墙未放行。

### 4.4 频繁断

- LCP echo 超时。
- 线路质量/光衰。
- 上游会话老化。
- 设备负载/内存。

## 5. 修复

| 场景 | 动作 |
|---|---|
| 账号错 | 核对/重置 |
| VLAN 错 | 改 WAN VLAN |
| MTU | 调 MTU/MSS/ clamp |
| 路由 | 加默认路由/策略 |
| 频繁断 | 开重拨/保活/查线路 |
| 光衰 | 清洁/换线/报修 |

## 6. 预防

- 拨号失败自动重试 + 退避。
- 记录失败阶段/错误码。
- 监控 WAN 在线率/时延。
- 现场记录光功率/VLAN/账号来源。

## 7. 复盘问题

1. 失败发生在哪一层？
2. 证据是什么（抓包/日志）？
3. 是配置、线路还是上游？
4. 下次如何更早发现？

## 8. 相关

- [PPPoE 协议](../../3.网络科学/2.接入协议/01-PPPoE协议.md)
- [通用网络排查](01-通用网络排查.md)
- [抓包方法](../../10.工程方法/5.测试与实验/02-抓包方法.md)
- [现场记录模板](06-现场记录模板.md)
