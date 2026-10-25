---
id: "vpn-05"
title: "IPsec 与 IKEv2"
cluster: vpn
layer: L1
status: draft
confidence: medium
platform: ["strongSwan 5.x", "OpenWrt 23.05"]
source:
  - type: rfc
    ref: "RFC 7296 (IKEv2), RFC 4301/4303 (IPsec/ESP)"
verified_on: null
tags: ["ipsec", "ikev2", "strongswan"]
aliases: ["IPsec", "IKEv2"]
created: 2026-10-24
updated: 2026-10-24
---

# IPsec 与 IKEv2

> 解决什么问题：站点到站点/远程接入的网络层加密，何时选 IPsec 而不是 WireGuard。
> 不解决：具体运营商 VPN 客户端兼容性（需实测）。

## 1. 组成

```text
IKEv2（UDP 500/4500）  协商密钥与安全联盟
        │
        ▼
IPsec SA
├── ESP：加密 + 完整性（常用）
└── AH：仅完整性（少用）
        │
        ▼
策略：哪些流量走隧道（SPD/路由）
```

| 概念 | 说明 |
|---|---|
| IKE SA | 控制通道，负责认证与协商 |
| Child SA | 数据通道（ESP） |
| Proposal | 加密/完整性/DH 算法组合 |
| PSK / 证书 | 认证方式 |
| Traffic Selector | 哪些源/目的网段走隧道 |
| NAT-T | NAT 场景封装到 UDP 4500 |

## 2. 与 WireGuard 的取舍

| 维度 | IPsec/IKEv2 | WireGuard |
|---|---|---|
| 标准化 | IETF，运营商/企业广泛支持 | 轻量，非 IETF |
| 客户端 | iOS/Android/Windows 原生支持 | 需装客户端 |
| 配置 | 复杂（策略/算法/认证） | 简单（密钥/AllowedIPs） |
| NAT 穿透 | NAT-T | UDP + 保活 |
| 性能 | 成熟，硬件加速多 | 内核实现，性能好 |
| 适用 | 企业/运营商互通 | 自建/站点互联 |

## 3. strongSwan 最小配置（示例）

```conf
# /etc/ipsec.conf
config setup
    charondebug="ike 1, knl 1, cfg 0"

conn %default
    keyexchange=ikev2
    ike=aes256-sha256-modp2048!
    esp=aes256-sha256!
    dpdaction=restart
    dpddelay=30s

conn site-to-site
    left=192.0.2.1
    leftsubnet=10.1.0.0/24
    leftauth=psk
    right=198.51.100.1
    rightsubnet=10.2.0.0/24
    rightauth=psk
    auto=start
```

```conf
# /etc/ipsec.secrets
192.0.2.1 198.51.100.1 : PSK "change-me"
```

> 生产优先证书认证，PSK 仅实验/临时。

## 4. 验证

```bash
ipsec statusall
ipsec trafficstatus
ip xfrm state
ip xfrm policy
tcpdump -ni any 'udp port 500 or udp port 4500 or esp'
```

判定：IKE SA 建立、Child SA 建立、流量计数增长、策略命中。

## 5. 常见失败

| 现象 | 首查 |
|---|---|
| IKE 不建立 | 算法不匹配、PSK/证书、UDP 500 被拦 |
| 一阶段成功二阶段失败 | Traffic Selector、子网、ESP 算法 |
| 能建立但不通 | 路由/策略、NAT、防火墙 forward |
| 一段时间断 | DPD、NAT 老化、重协商 |
| 只有单向通 | 策略方向、路由回程 |
| 多客户端冲突 | 同一 CIDR、连接标记 |

## 6. 安全要点

- 禁用 IKEv1/弱算法（DES/3DES/MD5/SHA1）。
- 证书校验 + 强身份（FQDN/ID）。
- 限制对端 IP；不要用 `%any` 除非必要。
- 定期轮换密钥/证书。
- 日志脱敏。

## 7. 待实测/待项目参数
- [ ] 目标运营商/客户的 IPsec 参数模板。
- [ ] 一次 strongSwan 与商用网关的互通记录。
- [ ] 性能对比（IPsec vs WireGuard）。

## 8. 相关

- [WireGuard](01-WireGuard.md)
- [隧道接入范式](04-%E9%9A%A7%E9%81%93%E6%8E%A5%E5%85%A5%E8%8C%83%E5%BC%8F.md)
- [Netfilter 与防火墙](../../8.%E6%95%B0%E6%8D%AE%E9%9D%A2%E5%B7%A5%E7%A8%8B/02-Netfilter%E4%B8%8E%E9%98%B2%E7%81%AB%E5%A2%99.md)
- [PKI 与证书](../3.%E5%AE%89%E5%85%A8%E4%B8%8E%E8%AE%A4%E8%AF%81/01-PKI%E4%B8%8E%E8%AF%81%E4%B9%A6.md)
