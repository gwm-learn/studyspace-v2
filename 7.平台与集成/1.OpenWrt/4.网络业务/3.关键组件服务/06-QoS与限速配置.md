---
id: "openwrt-net-06"
title: "QoS与限速配置"
cluster: "openwrt-net"
layer: L3
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "qos"]
aliases: ["QoS与限速配置"]
created: 2026-10-24
updated: 2026-10-24
---
# QoS与限速配置


## OpenWrt QoS（服务质量）


### 一、QoS 模型概述

#### 1.1 什么是 QoS
QoS（Quality of Service，服务质量）指网络设备对流量进行分类、标记、排队和调度的一系列机制，目标是保障关键业务的带宽、时延和丢包率。OpenWrt 中的 QoS 实现分两层：**数据面**（内核 tc 队列调度）与**控制面**（UCI 配置 + LuCI 界面）。

#### 1.2 IntServ（集成服务）
- **模型**：端到端预留，先通过 RSVP 信令为每个流申请带宽，路径上所有节点确认后才能通信。
- **特点**：粒度细、能提供硬性保证，但状态维护开销大，可扩展性差。
- **现状**：在 CPE/家用路由器中基本不使用，主要出现在企业核心网的学术研究中。

#### 1.3 DiffServ（区分服务）
- **模型**：在数据包头部打标记（IPv4 的 ToS 字段 / IPv6 的 TC 字段），每个路由器只根据标记做转发处理，无信令、无每流状态。
- **特点**：可扩展性好，是当前实际部署的主流模型，OpenWrt 的 QoS/SQM 都是 DiffServ 思路。
- **PHB（逐跳行为）**：EF（加速转发，低时延）、AF1x~AF4x（确保转发，分级）、BE（尽力而为，默认）。

### 二、OpenWrt 的 tc 与 qdisc

#### 2.1 tc 基本概念
OpenWrt 的内核流量控制基于 Linux `tc`（traffic control），层次为 `qdisc（队列）→ class（类别）→ filter（过滤器）`：
- **qdisc**：挂在接口上的队列调度器，决定数据包排队与发送顺序。
- **class**：qdisc 内部的子类别，可分配带宽比例。
- **filter**：根据分类规则（如 IP、端口、DSCP）把流量导入对应 class。

#### 2.2 常用 qdisc 对比
| qdisc | 类型 | 特点 | 适用场景 |
|-------|------|------|----------|
| **HTB** | 分类(classful) | 按层级分配带宽，支持借用(borrow)与突发，配置直观 | 经典多级限速、传统 QoS |
| **HFSC** | 分类(classful) | 曲线式带宽控制，Linux 上唯一能精确控制时延的 qdisc | 对时延敏感的场景 |
| **fq_codel** | 无分类(classless) | 公平队列 + CoDel 主动队列管理，自动对抗缓冲膨胀(bufferbloat) | 现代默认 AQM |
| **cake** | 无分类(classless) | fq_codel 的集大成者，内置整形、ECN、DSCP 处理 | SQM 默认 qdisc |

#### 2.3 手工配置示例
SQM 底层实际就是生成这样的 tc 命令：
```
tc qdisc add dev eth0.2 root handle 1: htb default 30
tc class add dev eth0.2 parent 1: classid 1:1 htb rate 100mbit
tc class add dev eth0.2 parent 1:1 classid 1:30 htb rate 80mbit ceil 100mbit
tc qdisc add dev eth0.2 parent 1:30 fq_codel
tc filter add dev eth0.2 parent 1: protocol ip prio 1 u32 match ip dport 80 0xffff flowid 1:30
```

### 三、SQM（Smart Queue Management）

#### 3.1 SQM 是什么
SQM（智能队列管理）= 流量整形（shaping）+ 主动队列管理（AQM）。它把上行/下行限速到略低于实际带宽，让队列始终有空余，配合 fq_codel/cake 消除 bufferbloat（缓冲膨胀导致的高时延）。

#### 3.2 软件构成
- **sqm-scripts**：核心脚本，通过 UCI 读取配置并生成 tc 规则，配合 hotplug 在接口 up 时生效。
- **sqm-scripts-extra**：SQM 检测与调优辅助脚本。
- **luci-app-sqm**：LuCI 图形界面。
- 可选 qdisc：`cake`（默认推荐）、`fq_codel`、`pie`。

#### 3.3 UCI 配置（/etc/config/sqm）
```
config queue 'eth0'
	option interface 'eth0'
	option enabled '1'
	option download '98000'        # 下行限速 kbit/s，建议为实测带宽的 85%~95%
	option upload '48000'          # 上行限速 kbit/s
	option qdisc 'cake'            # 可选 fq_codel / pie
	option script 'simple.qos'
	option linklayer 'ethernet'    # 或 atm，取决于接入方式
	option overhead '44'           # 每包额外开销字节数
	option squash_dscp '1'
	option squash_ingress '1'
```
改动后执行 `/etc/init.d/sqm restart` 生效。

#### 3.4 限速值怎么定
- 用 speedtest 或路由器自带 SQM 检测测得实际带宽。
- 限速取实测带宽的 85%~95%，留出余量，否则队列会满、AQM 失效。
- 上行不限制的话，TCP ACK 会被下行队列拖累，所以上下行都要开。

### 四、LuCI 中 SQM QoS 插件使用

- 安装：`opkg update && opkg install luci-app-sqm sqm-scripts`。
- 入口：LuCI「网络 → SQM QoS」。
- 页面主要项：
  - **启用队列管理**：勾选后启用。
  - **接口**：选要限速的接口（通常为 `eth0.2`/`wan` 与 `br-lan`/`lan` 两个方向）。
  - **下载/上传速率**：填 kbit/s，即上面的 download/upload。
  - **qdisc**：建议选 `cake`；链路类型选 ethernet/atm。
  - **每包额外开销**：默认 44 字节，PPPoE 场景建议 40~44。
- 保存并应用后，可立即用 `tc -s qdisc show dev eth0` 确认队列是否生效。
- 效果验证：开一个满速下载的同时 ping 网关，时延应基本稳定，不再出现数百毫秒的抖动。

### 五、CPE 场景中的优先级标记（DSCP / 802.1p）

#### 5.1 三层标记 DSCP
- DSCP 位于 IPv4 ToS 字段的高 6 位，取值 0~63，经典值：EF=46、AF41=34、AF31=26、CS6=48、CS7=56。
- CPE 内常用 **iptables/nftables mangle 表**打标，例如 VoIP 流量：
```
iptables -t mangle -A POSTROUTING -o eth0.2 -p udp --dport 5060 -j DSCP --set-dscp 46
iptables -t mangle -A POSTROUTING -o eth0.2 -p udp --dport 10000:20000 -j DSCP --set-dscp 46
```
- OpenWrt 22.03+ 用 nftables 语法：
```
nft add rule ip mangle postrouting oifname "eth0.2" udp dport 5060 ip dscp set ef
```

#### 5.2 二层标记 802.1p
- 802.1p 优先级（PCP）位于 802.1Q 标签的 3 bit 字段，取值 0~7。
- CPE 上 VLAN 接口出方向可用 tc 的 vlan action 打标，将三层 DSCP 映射到二层 PCP。
- 典型映射：DSCP EF → PCP 5（语音）、AF41 → PCP 4（视频）、AF31 → PCP 3（关键业务）、BE → PCP 0。

#### 5.3 典型 CPE 场景落地流程
1. **分类**：识别语音、视频、管理、上网等业务流（按端口/IP/协议）。
2. **标记**：三层打 DSCP，二层打 802.1p，保证端到端优先级一致。
3. **调度**：WAN 侧挂 cake/fq_codel，将标记映射到不同优先级队列。
4. **验证**：用 tcpdump 抓包确认 DSCP 标记正确，用 iperf3 多流并发验证优先级生效。

### 六、小结
DiffServ 是主流 QoS 模型，OpenWrt 全部 QoS 功能都围绕它展开；手动 tc/HTB 适合固定分级限速，现代场景优先用 SQM（cake）解决 bufferbloat。CPE 上做 QoS 的关键是"分类 → 标记 → 调度"三步：DSCP 负责跨三层网络传递优先级，802.1p 负责二层链路内传递。

## OpenWrt 流量控制：tc 与 HTB


### 一、限速策略概述

Linux 的流量控制（Traffic Control）由内核的 `tc` 子系统实现，OpenWrt 只是把它封装成 UCI 配置和 LuCI 页面。限速的目的不是简单把带宽压小，而是**分配**：保证关键业务有带宽、防止单个终端吃光整条链路。

限速分三个层次：
- **链路层**：ethtool / 交换芯片，作用于整个物理端口，固定协商速率。
- **网络层**：tc（qdisc/class/filter），按 IP、端口、接口分类，平滑整形、带宽分配。
- **应用层**：应用自身限速，作用于单个会话/连接（如 P2P 客户端）。

OpenWrt 常用的是中间那层。上层封装有两个：老的 `qos-scripts`（luci-app-qos）和新的 `sqm-scripts`（luci-app-sqm，基于 fq_codel/cake），两者最终都调用 tc 下发规则。

### 二、tc 层级令牌桶（HTB）

#### 2.1 基本概念

tc 由三部分组成：
- **qdisc（队列规则）**：挂在接口上的调度器，如 `pfifo`、`htb`、`fq_codel`。
- **class（分类）**：qdisc 内部的带宽桶，只存在于 HTB 这类 classful qdisc。
- **filter（过滤器）**：把报文按规则丢进某个 class，常用 `u32`、`flower`、`fw`。

#### 2.2 HTB 原理

HTB（Hierarchical Token Bucket，层级令牌桶）是树形结构：根 qdisc 下挂多个 class，每个 class 有自己的令牌桶，令牌按 `rate` 填充。关键在于**借用**：子类带宽没打满时，可以把父类的富余带宽借过来用，但最多不超过 `ceil`。

| 参数 | 含义 |
|------|------|
| `rate` | 保证速率，令牌按此速度补充 |
| `ceil` | 最大速率，允许借用带宽后的上限 |
| `burst` / `cburst` | 瞬间突发容量，令牌桶深度 |
| `quantum` | 每次借用时分到的字节数，影响公平性 |

HTB 与单层 TBF 的区别：TBF 只有一个桶、不能分类；HTB 支持多层嵌套和带宽借用，适合"总带宽固定、子业务分配"的典型 CPE 场景。

#### 2.3 层级示意

```
1: root (htb)
└── 1:1 总带宽 1000mbit
    ├── 1:10 rate 10mbit ceil 10mbit    ← 某终端/业务
    └── 1:20 rate 990mbit ceil 1000mbit ← 默认类
```

叶子 class 上还能再挂一个 qdisc（如 `sfq`、`fq_codel`）做公平排队，否则多个连接会互相挤占。

### 三、OpenWrt 中 tc 配置示例

示例：限制 192.168.1.100 这台终端的下行速率 10Mbps。查看现状用 `tc qdisc show dev br-lan`，先 `tc qdisc del dev br-lan root` 清掉旧规则再重建：

```bash
# 1. 清掉旧规则
tc qdisc del dev br-lan root
# 2. 根 qdisc，默认流量进 1:20
tc qdisc add dev br-lan root handle 1: htb default 20
# 3. 根类=总带宽，子类：10M 给指定终端，990M 给默认
tc class add dev br-lan parent 1: classid 1:1 htb rate 1000mbit
tc class add dev br-lan parent 1:1 classid 1:10 htb rate 10mbit ceil 10mbit
tc class add dev br-lan parent 1:1 classid 1:20 htb rate 990mbit ceil 1000mbit
# 4. 叶子挂 fq_codel 保证多连接公平
tc qdisc add dev br-lan parent 1:10 handle 20: fq_codel
tc qdisc add dev br-lan parent 1:20 handle 30: fq_codel
# 5. 过滤器：目标 IP 是 192.168.1.100 的报文进 1:10
tc filter add dev br-lan parent 1: protocol ip prio 1 \
    u32 match ip dst 192.168.1.100 flowid 1:10
```

几个要点：
- **方向**：下行限速做在 LAN 侧入口（`br-lan` 的 ingress），但 ingress 侧只能丢包不能整形，通常挂 `ifb` 重定向后再做 HTB。
- **匹配**：filter 按 `prio` 顺序匹配，`match` 命中后进对应 `flowid`。
- **持久化**：tc 规则重启即失效，OpenWrt 里要写进 `/etc/rc.local` 或交给 qos/sqm 服务管理，不要裸跑命令。

### 四、LuCI 流量控制配置

#### 4.1 经典 QoS（luci-app-qos）

LuCI「网络 → QoS」操作的就是 `qos-scripts`，配置文件 `/etc/config/qos`，核心 option 有三个：`interface`（作用接口）、`class`（目标 IP/端口 → 速率）、`default`（未匹配流量的默认带宽）。适合"给某类流量分带宽"的粗粒度控制，实现上同样是生成 tc 规则。

#### 4.2 现代 SQM（luci-app-sqm）

LuCI「网络 → SQM QoS」基于 `sqm-scripts`，推荐使用 `cake` qdisc。相比手写 HTB，SQM 内置了队列长度管理、公平调度和 AQM（主动队列管理），对**上下行同时整形**（DS/US）支持更完整，能明显改善缓冲膨胀（bufferbloat）问题。

```uci
config queue 'eth0'
    option enabled '1'
    option interface 'eth0'
    option download '100000'
    option upload '20000'
    option qdisc 'cake'
```

### 五、总结

- **选型**：手写 tc + HTB 灵活但复杂，适合固定规则；SQM（cake）省心，适合日常 CPE 场景。
- **入口**：LuCI 页面、UCI 配置、`/etc/rc.local` 裸命令三条路，生产环境优先 UCI。
- **排查**：`tc -s qdisc show dev br-lan` 看 drop/backlog，`tc -s class show dev br-lan` 看各 class 实际速率。
- **边界**：tc 管的是转发路径上的队列，物理端口本身的协商速率归 ethtool/交换芯片管，见《端口限速》。

*最后更新：2026-08-12*

## OpenWrt 端口限速


### 一、物理端口速率限制

端口限速直接作用于**物理接口**，设置的是链路层的协商速率，跟"队列里怎么排队"无关。物理对象分两种：直连 CPU 的 PHY（`eth0` 这类）和挂在交换芯片下的 LAN 口（DSA 框架下叫 `lan1`~`lan4`），命令都是 `ethtool`。

#### 1.1 ethtool 命令

```bash
ethtool eth0                          # 查看当前速率、自协商状态
ethtool -s eth0 speed 100 duplex full autoneg off   # 固定 100M 全双工
ethtool -s eth0 speed 10  duplex full autoneg off   # 强制 10M
```

注意：`autoneg off` 关闭自动协商后，对端也必须固定到相同速率，否则会掉链或闪断。固定速率不是平滑限速，是硬性把链路协商到某个档位。

#### 1.2 交换芯片（switch）

CPE 的多个 LAN 口通常共享一颗交换芯片（如 MT7530、RTL8367、IP175G）。DSA 框架下每个端口有独立 netdev（`lan1`、`lan2`...），命令用法一样：

```bash
ethtool -s lan1 speed 10 duplex full autoneg off
```

旧式 `swconfig` 框架下 LAN 口不带独立 netdev，只能操作交换芯片寄存器（`swconfig dev switch0 port 1 set speed 10`）。不是所有交换芯片都允许逐端口固定速率，具体看驱动支持。部分芯片还有限速寄存器，只限转发带宽、不影响协商速率，效果接近 tc 但粒度只到物理端口。

### 二、与流量控制的区别

| 对比项 | 端口限速（ethtool/芯片） | 流量控制（tc/HTB） |
|--------|--------------------------|---------------------|
| 作用层次 | 物理层/链路层 | 网络层队列调度 |
| 粒度 | 整个物理端口 | 可按 IP、端口、接口细分 |
| 效果 | 协商速率，硬性、不缓存 | 平滑整形，可借带宽、可排队 |
| 方向 | 通常双向对称 | 上下行可分别控制 |
| 适用场景 | 链路协商、兼容性、功耗 | 带宽分配、QoS、公平调度 |
| 持久性 | 掉电/重启需重设 | 由 qos/sqm 服务管理 |

一句话：端口限速是"这台口最快就这么多"，流量控制是"这条链路的带宽我来分"。

### 三、常见 CPE 场景

#### 3.1 限制 LAN 口速率

**需求**：给特定客户或测试环境限制某个 LAN 口的速率，比如把 `lan2` 限到 10M。

```bash
ethtool -s lan2 speed 10 duplex full autoneg off
```

要点：
- 只影响**有线协商速率**，无线终端不受影响（WiFi 速率由射频管理）。
- 对端网线质量差时，强制 10M 仍可能闪断，先 `ethtool lan2` 看 link 状态。
- 如果只是想限某个终端的业务带宽，应该用 tc 按 IP 匹配，而不是限整个口。

#### 3.2 限制 WAN 口速率

**需求**：模拟运营商接入带宽，验证路由器在低带宽下的表现（如 PPPoE 300M 压到 100M）。

WAN 口物理限速并不常用：运营商的瓶颈在局端，本端限制反而丢失链路冗余。更贴合实际的是在 WAN 接口上做 tc 整形（上行直接挂 HTB，下行需 ifb 重定向；PPPoE 场景下做在 `pppoe-wan` 而非物理接口上）：

```bash
tc qdisc add dev wan root handle 1: htb default 10
tc class add dev wan parent 1: classid 1:10 htb rate 20mbit ceil 20mbit
```

#### 3.3 小结

- **硬限制**（链路协商/芯片限速）：固定档位、简单粗暴，适合"必须不超 X Mbps"。
- **软整形**（tc）：灵活平滑，适合"带宽怎么分"的日常 QoS。
- 两者互补：物理口限速兜底，tc 做精细分配。

### 四、总结

- 端口限速工具是 `ethtool`，对象是物理接口或交换芯片端口，改的是链路协商速率。
- 与 tc 的本质区别：端口限速无队列、无分类，tc 是软整形。
- 生产环境优先考虑：模拟低带宽用 WAN 口 tc，隔离客户用 LAN 口 tc 按 IP，物理口固定速率只在兼容性/测试场景用。

*最后更新：2026-08-12*
