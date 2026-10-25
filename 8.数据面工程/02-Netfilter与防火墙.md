---
id: "dp-08"
title: "Netfilter与防火墙"
cluster: dp
layer: L2
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["firewall", "netfilter", "lte"]
aliases: ["Netfilter与防火墙"]
created: 2026-10-24
updated: 2026-10-24
---
# Netfilter与防火墙


## 防火墙（Firewall）详解


### 1. 概述：防火墙在网络中的角色

防火墙是位于**可信网络与不可信网络**之间（或主机与网络之间）的安全设备，按预定策略对进出流量进行**过滤、检查和转发控制**。它解决的核心问题：**"哪些流量可以进来，哪些流量必须挡在外面"**。

防火墙的三大基本功能：

- **访问控制**：依据规则决定放行或丢弃报文
- **安全审计**：记录被允许/被拒绝的连接，形成日志供分析
- **网络隔离**：把内部可信区域与外部不可信区域隔开，缩小攻击面

传统防火墙工作在网络的"边界"，而**主机防火墙**则运行在每台终端上，两者结合形成纵深防御。

### 2. 防火墙分类

| 类型 | 工作层次 | 检查内容 | 代表实现 | 特点 |
|------|----------|----------|----------|------|
| 包过滤防火墙（Packet Filter） | 网络层/传输层 | 五元组 | 早期路由器 ACL、iptables | 速度快，无状态，无法识别应用层 |
| 状态检测防火墙（Stateful Inspection） | 网络层/传输层 + 连接状态 | 五元组 + 连接状态表 | iptables conntrack、Check Point | 识别连接方向，规则简单，性能较好 |
| 应用层网关（Application Gateway / 代理） | 应用层 | 应用协议内容 | Squid、HTTP/FTP 代理 | 深度检查，性能开销大，可缓存 |
| 下一代防火墙（NGFW） | 网络层~应用层 | 用户、应用、内容、威胁情报 | 各厂商 NGFW | 应用识别 + IPS + 防病毒等一体化 |

> 演进主线：**无状态包过滤 → 有状态检测 → 应用层深度检查**。越往后越"懂业务"，但性能成本也越高。NGFW 是当前企业边界的主流形态。

#### 2.1 包过滤防火墙（无状态）

逐个检查经过的报文头字段，与规则表逐条比对，匹配则执行 ACCEPT/DROP。只关注"这个包本身"，**不关心它是否属于某个已建立的连接**。典型问题：无法区分"主动连接外网"和"外部先发起的连接"，因为两者可能就是相同的五元组。

#### 2.2 状态检测防火墙（有状态）

在包过滤基础上增加**连接状态表（conntrack table）**，首次放行后记录连接，后续属于同一连接的报文直接比对状态表放行，无需重新匹配全部规则。这是当前主流技术的基石。

#### 2.3 应用层网关（代理防火墙）

客户端先与代理建立连接，由代理代发请求到目标服务器。代理能看到完整的应用层内容，可以做内容过滤、病毒扫描，还能隐藏内网拓扑。代价是**性能开销大**，且需要为每种协议单独实现代理。

### 3. 包过滤防火墙：五元组规则

包过滤规则基于报文的五个基本字段，称为**五元组（5-tuple）**：

| 字段 | 说明 |
|------|------|
| 源 IP 地址（Source IP） | 报文从哪里来 |
| 目的 IP 地址（Destination IP） | 报文要去哪里 |
| 源端口（Source Port） | 发送方的端口 |
| 目的端口（Destination Port） | 接收方端口，常对应服务，如 80=HTTP、443=HTTPS |
| 协议（Protocol） | TCP / UDP / ICMP 等 |

规则形式为"**匹配条件 → 动作**"：

```
允许 协议=TCP  源IP=内网网段  源端口=任意  目的IP=任意  目的端口=80 → 通过
允许 协议=TCP  源IP=任意      源端口=任意  目的IP=内网    目的端口=1024~65535 → 通过
默认：其余全部丢弃
```

包过滤的优点：实现简单、速度快、对网络性能影响小。缺点：**没有连接状态概念**，无法识别基于连接的攻击（如 SYN 洪泛的后续流程），也无法检查应用层内容。

### 4. 状态检测防火墙（Stateful Inspection）

状态检测防火墙维护一张**连接状态表**，记录每个活动的连接及其状态：

| 状态 | 含义 |
|------|------|
| NEW | 新建的连接，通常是第一个报文（如 TCP SYN） |
| ESTABLISHED | 已建立的连接，双向报文已见（如完成三次握手后） |
| RELATED | 与已有连接**相关**的新连接，如 FTP 数据连接、ICMP 差错报文 |

Linux 内核 conntrack 实际维护的状态还包括 `INVALID`（无法识别的畸形报文）、`UNREPLIED`、`ASSURED` 等，但规则书写中最常用的是 NEW / ESTABLISHED / RELATED 三者。

典型规则写法（只放行"由内向外发起的连接"的回程流量）：

```bash
iptables -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT  -m conntrack --ctstate NEW -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate NEW,ESTABLISHED  -j ACCEPT
```

> 状态检测的优势：**内网主机主动访问外网后，外网的回应无需为每条回程单独开规则**。管理员只需放行"入站的 NEW 连接"，大大简化了策略。

### 5. Netfilter 框架（Linux 内核）

Linux 内核的包过滤/网络地址转换能力由 **Netfilter** 框架提供，iptables 只是其用户态配置工具。报文在内核协议栈的**五个关键挂钩点（hook）**被截获，对应五条链：

```
                   ┌──── 应用层进程 ────┐
                   │                    │
    数据包入       ▼                    │
  ──► PREROUTING ──► 路由判定 ──► INPUT ┤
        │            │                 │ 数据包出
        │            ▼ FORWARD          │
        └───────► （转发路径） ──────► POSTROUTING ──► 出口
                                    ▲
                    OUTPUT（本机发出的包从这儿进）──────┘
```

| 链（Chain） | 挂钩点 | 处理对象 |
|-------------|--------|----------|
| PREROUTING | 报文刚进入协议栈，路由判定**之前** | 入站包，常用于 DNAT（目的地址转换） |
| INPUT | 路由判定后，发给**本机**的包 | 本机入站 |
| FORWARD | 路由判定后，需要**转发**的包 | 路由器/网关转发路径 |
| OUTPUT | 本机**进程发出**的包 | 本机出站 |
| POSTROUTING | 报文即将离开本机 | 出站/转发包，常用于 SNAT（源地址转换） |

#### 5.1 四张表（Tables）

Netfilter 有四种内置表，决定规则的**功能类型**：

| 表 | 主要用途 | 可用链 |
|----|----------|--------|
| **filter** | 包过滤（ACCEPT/DROP/REJECT） | INPUT、FORWARD、OUTPUT |
| **nat** | 地址转换（SNAT/DNAT/MASQUERADE） | PREROUTING、INPUT、OUTPUT、POSTROUTING |
| **mangle** | 修改报文字段（TOS、TTL、标记 MARK） | 全部五条链 |
| **raw** | 跳过连接追踪（NOTRACK） | PREROUTING、OUTPUT |

表的**优先级**为 `raw → mangle → nat → filter`，同一链上先经过优先级高的表。

#### 5.2 规则匹配顺序

报文进入一条链后，**按规则在链中的先后顺序逐条匹配**，一旦匹配就执行该规则的动作并结束（除非动作是 RETURN 或目标跳转）。因此**规则顺序非常重要**：先放行常用流量、后拒绝其余流量，是常见优化手段。

### 6. iptables 基础命令

iptables 命令结构：`iptables -t 表 操作 链 匹配条件 -j 动作`。

常用操作：

| 操作 | 含义 |
|------|------|
| `-A`（--append） | 在链末尾追加规则 |
| `-I`（--insert） | 在链开头插入规则 |
| `-D`（--delete） | 删除指定规则 |
| `-F`（--flush） | 清空链上所有规则 |
| `-L`（--list） | 列出规则 |
| `-P`（--policy） | 设置链的默认策略 |

常用动作（-j 目标）：

| 动作 | 含义 |
|------|------|
| ACCEPT | 放行 |
| DROP | 静默丢弃（不回包） |
| REJECT | 拒绝并回 ICMP 错误包 |
| LOG | 记日志，继续下一条规则 |
| SNAT / DNAT / MASQUERADE | 地址转换（nat 表） |

示例：允许外部访问本机 80 端口（Web 服务）：

```bash
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
#         链   协议  目的端口   动作
```

示例：允许来自内网网段 192.168.1.0/24 的 SSH，其余入站默认拒绝：

```bash
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 -j ACCEPT
iptables -P INPUT DROP
```

> 注意：`iptables` 规则**重启即失效**（不持久），需要用 `iptables-save`/`iptables-restore` 或发行版自带的保存机制固化。现代系统中 `nftables` 是 iptables 的替代者，但规则模型一脉相承。

### 7. 典型部署位置

| 部署位置 | 形态 | 保护对象 | 特点 |
|----------|------|----------|------|
| **边界防火墙** | 独立硬件设备，串接在内外网之间 | 整个内部网络 | 性能强、吞吐高，企业入口的"大门" |
| **主机防火墙** | 软件，运行在每台主机内 | 单台主机 | 粒度细，可针对进程/端口精确控制，Linux 的 iptables/firewalld、Windows 的 Windows Defender 防火墙 |
| **DMZ（非军事区）** | 边界上隔离出的半可信区域 | 对外提供服务的服务器 | 对外服务器放 DMZ，即使被攻破也不能直通内网 |

#### 7.1 DMZ 架构

```
                    互联网
                      │
                 ┌────┴────┐
                 │  边界防火墙 │
                 └────┬────┘
              ┌───────┼────────┐
              │       │        │
        ┌─────┴───┐  ┌┴──────┐
        │  内网     │  │  DMZ   │
        │ 服务器/PC │  │ Web/Mail│
        └─────────┘  └───────┘
```

DMZ 中的服务器需要同时被**外网访问**（开放部分端口）和**访问内网数据库**（按需最小开放）。边界防火墙用两条不同策略分别约束"外网 → DMZ"和"DMZ → 内网"两个方向的流量。

### 8. 常见防火墙策略设计

#### 8.1 白名单 vs 黑名单

| 策略 | 原理 | 默认状态 | 安全性 | 维护成本 |
|------|------|----------|--------|----------|
| **白名单**（默认拒绝） | 只放行明确允许的流量 | 默认 DROP | 高，未知流量一律进不来 | 高，需要不断补充放行规则 |
| **黑名单**（默认允许） | 只阻挡明确禁止的流量 | 默认 ACCEPT | 低，新攻击靠规则补丁 | 低，日常干扰少 |

企业边界通常采用**白名单**（默认拒绝），因为网络环境相对固定；个人主机常用黑名单，因为需要灵活访问互联网。**默认拒绝、按需放行**是安全审计中被广泛接受的最佳实践。

#### 8.2 策略设计原则

- **最小权限**：只开放业务必需的端口，如 Web 服务器仅开放 80/443
- **方向性控制**：入站只放行 NEW 连接的目标服务，回程统一放行 ESTABLISHED,RELATED
- **纵深防御**：边界防火墙 + 主机防火墙 + 应用层过滤配合，单一设备失效不意味着网络失守
- **日志与告警**：DROP 的流量要留日志，异常访问模式是入侵信号的重要来源

### 9. 小结

防火墙的演进本质上是**从"看包"到"看连接"，再到"看应用"**的过程：包过滤基于五元组做静态匹配，状态检测引入连接状态表解决回程放行难题，代理/NGFW 深入到应用层识别真正的业务内容。理解 Linux 的 Netfilter 五链四表与 iptables 规则模型，就掌握了绝大多数开源防火墙的实现内核。无论设备形态如何变化，**"默认拒绝、按需放行、方向控制、留足日志"**始终是策略设计的核心。

## 选择一个数据包过滤策略


防火墙是一个实现访问控制策略的设备，实现一个默认的防火墙策略又两种方法   
1. 默认拒绝所有消息，明确地允许特定地数据包通过防火墙   
2. 默认接受所有消息，明确地拒绝选定地数据包通过防火墙   

## 对一个数据包地驳回Reject VS 拒绝Deny
当一个数据包被驳回时，该数据包被丢弃，同时一个ICMP错误消息被返回到发送方。   
当一个数据包被丢弃时，它仅仅是被简单地丢弃而已，不会向发送者进行通知。   

## 过滤传入地数据包
1. 远程源地址过滤   
2. 本地目的地址过滤   
3. 远程端口过滤   
4. 本地目的端口过滤   
5. 传入TCP地连接状态过滤   
6. 探测和扫描   
7. 拒绝服务攻击   
8. 源路由数据包   

## 过滤传出数据包
1. 本地源地址过滤   
2. 远程目的地址过滤   
3. 本地源端口过滤   
4. 远程目的端口过滤   
5. 传出TCP连接状态过滤   

## Netfilter 框架概述

Netfilter 是 Linux 内核中的**数据包处理框架**，在协议栈的固定位置提供钩子（hook），让用户空间工具（iptables/nftables）挂载规则对数据包进行检查和修改。

### 五大钩子点

数据包在内核中的通行路径上有五个钩子，规则链与钩子一一对应：

| 钩子 | 触发时机 | 对应链 |
|------|----------|--------|
| NF_INET_PRE_ROUTING | 包刚进入协议栈，路由决策之前 | PREROUTING |
| NF_INET_LOCAL_IN | 路由判定发往本机 | INPUT |
| NF_INET_FORWARD | 路由判定需要转发 | FORWARD |
| NF_INET_LOCAL_OUT | 本机进程产生报文发出 | OUTPUT |
| NF_INET_POST_ROUTING | 报文发出前最后一步 | POSTROUTING |

### 数据包流向

```
             ┌─ PREROUTING ─ 路由 ─┬─ 本机 → INPUT → 本地进程
入口 ──────▶│                      └─ 转发 → FORWARD → POSTROUTING → 出口
                                  OUTPUT（本机发出）───────┘
```

三种流向覆盖三个链条组合：
- 入站（发给本机）：PREROUTING → INPUT
- 转发（路由穿越）：PREROUTING → FORWARD → POSTROUTING
- 出站（本机发出）：OUTPUT → POSTROUTING

### 表与链的关系

Netfilter 提供多张**表**，每张表可在不同链上挂规则，同一条链上按 **raw → mangle → nat → filter** 的表顺序依次执行：

| 表 | 主要用途 | 挂载的链 |
|----|----------|----------|
| raw | 连接跟踪豁免（NOTRACK） | PREROUTING、OUTPUT |
| mangle | 修改报文（TOS、TTL、标记） | 全部五条链 |
| nat | 地址转换（SNAT/DNAT/MASQUERADE） | PREROUTING、OUTPUT、POSTROUTING |
| filter | 数据包过滤（放行/拒绝） | INPUT、FORWARD、OUTPUT |

## iptables 与 nftables 对比

| 对比项 | iptables | nftables |
|--------|----------|----------|
| 内核框架 | Netfilter 钩子 + 独立表结构 | Netfilter 钩子 + 新式 nf_tables 框架 |
| 配置工具 | iptables/ip6tables/arptables/ebtables 多套 | 统一为 `nft` 一个工具 |
| 语法 | 命令行逐条操作，可读性差 | 类脚本语法，支持变量、集合、映射 |
| 内置表/链 | 有内置表链结构 | 无内置内容，需自行创建 |
| 规则集管理 | 逐条添加/删除 | 支持整体原子替换（`nft -f`） |
| 地址族 | 每工具一个地址族 | 一套语法覆盖 ip/ip6/inet/bridge/arp |
| 性能 | 传统匹配，链式遍历 | 用集合/映射和并发哈希优化，规则多时更快 |

### 迁移要点

- nftables 语法更直观：`nft add rule ip filter input tcp dport 22 accept`。
- 规则集整体加载采用**事务式**，出错可回滚，比 iptables 逐条执行更安全。
- 现有 iptables 规则可用 `iptables-translate` 辅助转换为 nftables 语法，再手工核对。

## Netfilter数据包传输


Netfilter(iptables)使用了三个内置的过滤器链：INPUT、OUTPUT、FORWARD。   
![Netfilter数据包传输](assets/Netfilter%E6%95%B0%E6%8D%AE%E5%8C%85%E4%BC%A0%E8%BE%93.png)   

Netfilter防火墙有三个独立的表：filter、nat、mangle。   
filter表是实现基本的防火墙的默认表。   
nat表用来提供NAT和相关的功能。   
mangle在数据包被防火墙修改时使用。   

规则表的先后顺序:raw→mangle→nat→filter   

规则链的先后顺序:   
入站顺序:PREROUTING→INPUT   
出站顺序:OUTPUT→POSTROUTING   
转发顺序:PREROUTING→FORWARD→POSTROUTING   
![iptables表与链](assets/iptables%E8%A1%A8%E4%B8%8E%E9%93%BE.png)   

## iptables 基本语法

iptables的命令从前往后执行，因此当一条允许特定数据包的指令后若跟着一条拒绝同样数据包的命令，将会导致数据最终被防火墙丢弃。   
iptables < option > < chain > < matching criteria > < target >   
iptables命令的基础语法以iptables命令本身开始，然后是一个或多个选项，一个规则链，一个匹配标准集以及一个目标或处置。   

```SHELL
参数 作用

-P 设置默认策略:iptables -P INPUT (DROP|ACCEPT)

-F 清空规则链

-L 查看规则链

-A 在规则链的末尾加入新规则

-I num 在规则链的头部加入新规则

-D num 删除某一条规则

-s 匹配来源地址IP/MASK，加叹号"!"表示除这个IP外。

-d 匹配目标地址

-i 网卡名称 匹配从这块网卡流入的数据

-o 网卡名称 匹配从这块网卡流出的数据

-p 匹配协议,如tcp,udp,icmp

--dport num 匹配目标端口号

--sport num 匹配来源端口号
```

### filter表
filter表包含了实际的防火墙过滤规则，内建的规则链包括   
INPUT   
OUTPUT   
FORWARD   

### nat表
nat表包含了源地址和目的地址转换以及端口转换的规则，内建的规则链包括   
PREROUTING--DNAT/REDIRECT   
OUTPUT--DNAT/REDIRECT   
POSTROUTING--SNAT/MASQUERADE   

### mangle表
mangle表包含了设置特殊数据包路由标志的规则，这些规则将在filter表中进行检查，内建的规则链包括   
PREROUTING--被路由的数据包   
INPUT--到达防火墙并通过PREROUTING规则链的数据包   
FORWARD--修改通过防火墙路由的数据包   
POSTROUTING--在数据包通过OUTPUT规则链之后但在离开防火墙之前修改的数据包   
OUTPUT--本地生成的数据包   

## NAT
局域网内封包的传送   
1. 先经过 NAT table 的 PREROUTING 链   
2. 经由路由判断确定这个封包是要进入本机与否，若不进入本机，则下一步   
3. 再经过 Filter table 的 FORWARD 链   
4. 通过 NAT table 的 POSTROUTING 链，最后传送出去   

NAT 主机的重点就在于上面流程的第 1,4 步骤，也就是 NAT table 的两条重要的链：PREROUTING 与POSTROUTING。 那这两条链重要功能在于修改IP，而这两条链修改的IP又是不一样的，POSTROUTING在修改来源IP，PREROUTING则在修改目标IP 。由于修改的 IP 不一样，所以就称为来源NAT (Source NAT, SNAT) 及目标 NAT (Destination NAT, DNAT)。   

### SNAT
SNAT即源地址转换，能够让多个内网用户通过一个外网地址上网，解决了IP资源匮乏的问题。一个无线路由器也就使用此技术。
![SNAT封包传送](assets/SNAT%E5%B0%81%E5%8C%85%E4%BC%A0%E9%80%81.png)   

由上图可知，需要将192.168.10.10转换为111.196.211.212，iptables命令如下：   
iptables -t nat -A POSTROUTING -s 192.168.10.10 -o eth1 -j SNAT --to-source 111.196.221.212   
外网IP地址不稳定的情况即可使用MASQUERADE(动态伪装),能够自动的寻找外网地址并改为当前正确的外网IP地址   
iptables -t nat -A POSTROUTING -s 192.168.10.0/24 -j MASQUERADE   

### DNAT
DNAT即目地地址转换，则能够让外网用户访问局域网内不同的服务器。（相当于SNAT的反向代理）   
![DNAT封包传送](assets/DNAT%E5%B0%81%E5%8C%85%E4%BC%A0%E9%80%81.png)   

由上图可知，目标地址192.168.10.6在路由前就转换成61.240.149.149，需在网关上运行iptables命令如下：   
iptables -t nat -A PREROUTING -d 192.168.100.159 -p tcp -m tcp -dport 80 -j DNAT --to-destination 192.168.70.136:80   
eth1网口传入，且想要使用 port 80 的服务时，将该封包重新传导到 192.168.1.210:80 的 IP 及 port 上面,可以同时修改 IP 与 port。此为地址映射与端口转换。   

还可以使用REDIRECT单独进行端口转换   
例：将 80 端口的封包转递到 8080端口   
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080   
使用 8080 这个 port 来启动 WWW ，但是别人都以80来联机

## nftables和iptables的差别


nftables不仅替代了iptables的功能，还替代了ip6tables、arptables、etables。   
nftables拥有使用额外脚本的能力。   
nftables不包含任何内置表。   

## nftables基本语法
```SHELL
nft <command> <subcommand> <chain> <rule definition>
```
command:add、list、insert、delete、flush   
subcommand:table、chain、rule   

## nftables特性
地址族：   
1. ip：IPv4地址   
2. ip6：IPv6地址   
3. inet：ARP   
4. bridge：处理桥接数据包   

钩子：   
1. prerouting：刚到达并未被nftables的其他部分所路由或处理的数据包   
2. input：以及被接收并且已经经过prerouting钩子的传入数据包   
3. forward：如果数据包将被发送到另一个设备，它将会通过forward钩子   
4. output：从本地系统传出的数据包   
5. postrouting：仅仅在离开系统之前，postrouting钩子使得可以对数据包进行进一步的处理   

## nft 命令实用指南

### 表与链的创建

nftables 没有内置表和链，一切从创建开始：

```shell
# 创建 inet 地址族（同时处理 IPv4/IPv6）的 filter 表
nft add table inet filter
# 在表中创建 input 链，绑定 input 钩子
nft add chain inet filter input { type filter hook input priority 0 \; }
```

`inet` 地址族一套规则同时覆盖 IPv4 和 IPv6，避免忘记配置 v6 规则导致的漏防。常用链优先级：raw(-300) → mangle(-150) → nat(-100) → filter(0)。

### 基础规则增删改查

```shell
nft list ruleset                      # 列出全部规则集
nft add rule inet filter input tcp dport 22 accept    # 放行 ssh
nft insert rule inet filter input ip saddr 192.168.1.0/24 accept  # 链首插入
nft -a list chain inet filter input   # -a 显示每条规则的 handle
nft delete rule inet filter input handle 3            # 按 handle 删除
nft delete table inet filter          # 删除整张表
```

### 常用匹配与动作

| 匹配/动作 | 示例 | 说明 |
|-----------|------|------|
| 端口匹配 | `tcp dport 80` / `udp dport 53` | 可写端口范围 `1024-65535` |
| 地址匹配 | `ip saddr 10.0.0.0/8` / `ip6 daddr ::1` | 支持 CIDR |
| 接口匹配 | `iifname "wan0"` / `oifname "lan"` | 入/出接口，可用通配符 |
| 状态匹配 | `ct state established,related` | 连接跟踪状态匹配 |
| 计数器 | `counter` | 统计命中次数，配合 `nft list` 查看 |
| 日志 | `log prefix "DROP: "` | 打印内核日志，便于排查 |
| 跳转 | `jump my_chain` / `goto my_chain` | 调用自定义链 |
| 动作 | `accept / drop / reject / queue` | 放行、丢弃、拒绝（回 ICMP）、入队 |

### 规则集文件与原子加载

nftables 支持把整个规则集写入脚本文件，一次性原子加载，出错整体回滚，比 iptables 逐条执行更安全：

```shell
# /etc/nftables.conf 示例片段
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iifname "lo" accept
        tcp dport 22 accept
    }
}
```

```shell
nft -f /etc/nftables.conf   # 加载整个规则集
nft list ruleset > /etc/nftables.conf   # 导出当前规则集用于备份
```

### 与 OpenWrt 的关系

OpenWrt 使用 nftables 后端（fw4），规则通过 `/etc/config/firewall` 的 UCI 配置描述，由 fw4 翻译生成 nftables 规则集，普通用户不直接编辑 nftables 脚本。调试时可用 `nft list ruleset` 查看 fw4 生成的实际规则。复杂匹配（如多端口、多网段）可用集合合并，减少链遍历次数，提升规则集性能。

## Netfilter 框架


## 概述

Netfilter 是 Linux 内核中的**报文处理框架**，在内核协议栈的固定位置（钩子点）挂接回调函数，让内核模块可以对经过的包做修改、过滤、跟踪等操作。iptables、nftables、conntrack、ebtables 都是构建在 Netfilter 之上的子系统。

在 OpenWrt 中，防火墙（firewall4 + nftables）最终都翻译成 Netfilter 规则下发到内核。理解 Netfilter 的钩子点和表链结构，是理解整个 OpenWrt 流量路径的基础。

## 钩子点（Hook）

内核在协议栈的关键路径上定义了 5 个 IPv4/IPv6 钩子点，每个钩子点有一个回调链表，模块通过 `nf_register_hook()` 挂接自己的回调：

| 钩子 | 宏定义 | 触发位置 | 典型用途 |
|------|--------|----------|----------|
| 1 | `NF_INET_PRE_ROUTING` | 包进入本机，路由决策之前 | DNAT、原始包过滤 |
| 2 | `NF_INET_LOCAL_IN` | 路由后，包发往本机进程 | 入站过滤 |
| 3 | `NF_INET_FORWARD` | 路由后，包被转发 | 转发过滤 |
| 4 | `NF_INET_LOCAL_OUT` | 本机进程发出，路由决策前 | SNAT、出站过滤 |
| 5 | `NF_INET_POST_ROUTING` | 包离开本机前 | SNAT、MASQUERADE |

调用顺序由 `NF_HOOK` 宏完成：先 `nf_hook_slow()` 遍历该钩子点的回调链表，返回 `NF_ACCEPT` 继续走协议栈，`NF_DROP` 丢弃，`NF_STOLEN` 表示包被接管。

## 五链四表

iptables 的**表（table）**对应规则的功能分类，**链（chain）**对应钩子点。五张内置链就是上面 5 个钩子点，四张表按优先级依次在每条链上执行。

四表的优先级（数字小者先执行）：

```
raw(1) → mangle(2) → nat(3) → filter(4)
```

各表职责：

- **raw**：跳过连接跟踪的包（`NOTRACK` 目标），优先级最高，先于 conntrack 执行。
- **mangle**：修改包头字段（TTL、TOS、MARK），不参与地址转换。
- **nat**：地址转换，DNAT 只出现在 PREROUTING/OUTPUT 链，SNAT 只出现在 POSTROUTING/INPUT 链，规则由 `nf_nat` 模块实现。
- **filter**：过滤，默认表，`INPUT`/`FORWARD`/`OUTPUT` 三条链。

并非每条链都有全部表，例如 `nat` 表没有 FORWARD 链。实际挂载关系用 `iptables -t <table> -L` 查看。nftables 中表链更自由，但钩子优先级仍沿用这一思想。

## 连接跟踪（conntrack）

连接跟踪由 `nf_conntrack` 模块实现，它为每个连接（TCP/UDP/ICMP）维护一条**连接表项**，记录 5 元组、状态、超时等信息。OpenWrt 中 conntrack 与 fw4 配合实现状态防火墙，常见于 `nf_conntrack` 系统参数。

### 1. 表项结构

`struct nf_conn` 是连接的核心结构，通过哈希表管理，字段包括：

- **tuple 二元组**：`struct nf_conntrack_tuple` 保存原始方向和应答方向的 5 元组。
- **状态标志**：`IPS_*` 标志位，如 `IPS_CONFIRMED`（已确认）、`IPS_ASSURED`（双向流量确认）。
- **超时**：`timeout`，TCP 各状态、UDP、ICMP 各有默认值，可由 `nf_conntrack_timeout` 调整。
- **扩展区**：`nf_conn_ext` 挂 NAT、MARK、LABEL 等扩展数据，NAT 就是挂在扩展上的。

### 2. 连接状态机

用户空间通过 `conntrack -L` 或 `/proc/net/nf_conntrack` 看到的 4 种状态：

- **NEW**：首次见到该方向报文，还未建立双向确认。
- **ESTABLISHED**：已看到两个方向的报文，`IPS_ASSURED` 被置位。
- **RELATED**：与已有连接相关的新连接，如 FTP 数据通道、ICMP 差错报文。
- **INVALID**：无法关联任何已知连接，通常被防火墙直接丢弃。

### 3. 与 NAT 的关系

NAT 依赖 conntrack：`nat` 表规则修改地址后，改动记录在 conntrack 表项里，反向报文通过查找应答方向 tuple 自动还原。因此 NAT 规则只作用于首包（NEW 状态），后续报文靠 conntrack 完成逆变换。这也是 `MASQUERADE` 只需一条规则就能服务整个内网的原因。

## 与协议栈的协同

```
收包: 网卡 → PRE_ROUTING → conntrack/DNAT → 路由 → LOCAL_IN / FORWARD
发包: 本机 → LOCAL_OUT → conntrack/SNAT → POST_ROUTING → 网卡
```

- 协议栈调用顺序：`ip_rcv()` → `NF_INET_PRE_ROUTING` → 路由 → `ip_forward()` / `ip_local_deliver()`。
- 发送路径：`ip_output()` → `NF_INET_POST_ROUTING` 之前还有 `NF_INET_LOCAL_OUT`。
- 每个钩子点都会先做 conntrack 处理，再执行各表规则，保证过滤决策基于已跟踪的连接状态。

## OpenWrt 实践要点

- fw4（firewall4）默认把规则编译为 nftables 脚本，写入 `/tmp/fw4.nft`，加载进内核 Netfilter 框架。
- 调试命令：`nft list ruleset` 查看全量规则，`conntrack -L` 查看连接表，`cat /proc/net/nf_conntrack` 查看原始表项。
- 调大连接跟踪表：`sysctl -w net.netfilter.nf_conntrack_max=65536`，OpenWrt 默认值较小，大并发环境下易丢包。
