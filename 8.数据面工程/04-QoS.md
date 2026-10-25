---
id: "dp-10"
title: "QoS 原理"
cluster: dp
layer: L2
status: draft
confidence: medium
platform: ["Linux 5.15", "OpenWrt 23.05"]
source:
  - type: doc
    ref: "tc(8), tc-htb(8), tc-cake(8)"
verified_on: null
tags: ["qos", "tc", "htb", "cake", "sqm"]
aliases: ["QoS", "流量控制", "SQM"]
created: 2026-10-24
updated: 2026-10-24
---

# QoS 原理

> 解决什么问题：带宽有限时，如何保证关键业务（语音/游戏/办公）不被下载/上传挤死。
> 不解决：OpenWrt 具体配置（→ [QoS 与限速配置](../7.%E5%B9%B3%E5%8F%B0%E4%B8%8E%E9%9B%86%E6%88%90/1.OpenWrt/4.%E7%BD%91%E7%BB%9C%E4%B8%9A%E5%8A%A1/3.%E5%85%B3%E9%94%AE%E7%BB%84%E4%BB%B6%E6%9C%8D%E5%8A%A1/06-QoS%E4%B8%8E%E9%99%90%E9%80%9F%E9%85%8D%E7%BD%AE.md)）。

## 1. 为什么需要 QoS

```text
无 QoS：先到先服务 → 大流量占满队列 → 语音/游戏排队 → 延迟/抖动爆炸
有 QoS：分类 → 排队 → 调度 → 限速 → 关键业务优先
```

核心不是"限速"，而是**管理排队**。带宽再大，队列满了也会 bufferbloat。

## 2. Linux 流量控制模型

| 概念 | 说明 |
|---|---|
| qdisc | 队列规则（pfifo_fast、fq_codel、cake、htb） |
| class | 分类（HTB 的层级） |
| filter | 分类规则（按 IP/端口/DSCP/fwmark） |
| root qdisc | 挂在接口上的根队列 |

```text
网卡 → root qdisc
        ├─ class 1:1  (总带宽)
        │   ├─ class 1:10 (语音，优先)
        │   ├─ class 1:20 (办公)
        │   └─ class 1:30 (下载，低优先)
        └─ 默认类
```

## 3. 常见 qdisc

| qdisc | 特点 | 适用 |
|---|---|---|
| pfifo_fast | 简单三优先级 | 默认、低负载 |
| fq_codel | 公平队列 + CoDel，抗 bufferbloat | 通用 |
| cake | 内置分类、整形、去抖 | OpenWrt SQM 首选 |
| HTB | 分层令牌桶，可精确分配 | 需要保证/限制带宽 |
| TBF | 单桶限速 | 简单限速 |
| SFB | 流公平 | 备选 |

## 4. 分类与标记

| 方式 | 说明 |
|---|---|
| DSCP | IP 头 6 位，端到端标记 |
| fwmark | iptables/nftables 打标，tc 按 mark 分类 |
| 五元组 | 直接按地址/端口分类 |
| 应用识别 | 需要 DPI，成本高 |

推荐：边缘信任终端 DSCP 要谨慎（可被伪造）；运营商/企业网可用 DSCP，家庭网关更常用五元组 + fwmark。

## 5. 关键指标

| 指标 | 说明 | 目标（示例） |
|---|---|---|
| 时延 | 单程/往返 | 语音 <150 ms |
| 抖动 | 时延变化 | <30 ms |
| 丢包 | 队列溢出 | <1% |
| 吞吐 | 有效带宽 | 达到套餐 80%+ |
| bufferbloat | 满载时延上升 | <50 ms |

## 6. OpenWrt 的 SQM

SQM 用 cake/fq_codel 做"整形 + 队列管理"，重点解决上行 bufferbloat：

```text
LAN → 路由 → WAN
              │
              └─ SQM（下行/上行整形）→ 队列 → 驱动
```

配置要点：
- 上行带宽按实测的 85–95% 设置（留余量）。
- 下行若运营商侧已整形，可只做上行。
- 关闭硬件加速（flow offload）以免绕过 QoS。
- 用 `tc -s qdisc` 看丢包/队列。

## 7. 验证

```bash
tc qdisc show dev eth0
tc class show dev eth0
tc -s qdisc show dev eth0

# 满载 + 测时延
iperf3 -c server -t 60 &
ping -i 0.05 -c 600 gateway
```

判定：满载时 ping 时延不显著上升；关键业务不丢包；吞吐没有断崖。

## 8. 常见误区

| 误区 | 纠正 |
|---|---|
| 只限速不做队列 | 限速本身也会排队，需 AQM |
| 下行限速越大越好 | 超过链路能力反而更差 |
| 开了 QoS 就一定不卡 | 无线空口/上游拥塞仍会卡 |
| 忽略硬件加速 | offload 会绕过 tc |
| 用 DSCP 但不信任边界 | 终端可伪造优先级 |

## 9. 待实测/待项目参数
- [ ] 目标产品的 QoS 需求（语音/游戏/IPTV）。
- [ ] 一次 bufferbloat 前后对比数据。
- [ ] 硬件加速与 QoS 共存的配置。

## 10. 相关

- [QoS 与限速配置](../7.%E5%B9%B3%E5%8F%B0%E4%B8%8E%E9%9B%86%E6%88%90/1.OpenWrt/4.%E7%BD%91%E7%BB%9C%E4%B8%9A%E5%8A%A1/3.%E5%85%B3%E9%94%AE%E7%BB%84%E4%BB%B6%E6%9C%8D%E5%8A%A1/06-QoS%E4%B8%8E%E9%99%90%E9%80%9F%E9%85%8D%E7%BD%AE.md)
- [转发加速](05-%E8%BD%AC%E5%8F%91%E5%8A%A0%E9%80%9F.md)
- [Netfilter 与防火墙](02-Netfilter%E4%B8%8E%E9%98%B2%E7%81%AB%E5%A2%99.md)
- [测试方法](../10.%E5%B7%A5%E7%A8%8B%E6%96%B9%E6%B3%95/5.%E6%B5%8B%E8%AF%95%E4%B8%8E%E5%AE%9E%E9%AA%8C/01-%E6%B5%8B%E8%AF%95%E6%96%B9%E6%B3%95.md)
