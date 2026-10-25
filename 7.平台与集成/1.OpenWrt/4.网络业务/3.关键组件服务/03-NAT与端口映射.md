---
id: "openwrt-net-03"
title: "NAT与端口映射"
cluster: "openwrt-net"
layer: L1
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "nat"]
aliases: ["NAT与端口映射"]
created: 2026-10-24
updated: 2026-10-24
---
# NAT与端口映射


## NAT源地址转换（SNAT/MASQUERADE）


## 概述
源地址转换（Source NAT，SNAT）是指数据包**从内网发往外网**时，把源IP（和源端口）改写为公网出口IP的过程。它是家用路由器、OpenWrt 设备上网的核心机制：局域网设备只有私网地址，公网无法回包，必须经过 SNAT 改写后才能实现双向通信。

SNAT 是**出向转换**，与端口映射（DNAT，入向转换）相对，两者配合构成完整的 NAT 转发。

## SNAT 与 MASQUERADE 的区别

### 相同点
两者都完成源地址改写，属于 netfilter 的 nat 表中的 **postrouting 链**（数据包路由完成后、真正发出前挂钩）。

### 区别
| 对比项 | SNAT | MASQUERADE |
|--------|------|------------|
| 出口地址 | 必须显式指定，如 `--to-source 1.2.3.4` | 自动取网卡当前 IP，无需指定 |
| 出口IP变化 | 不感知，需要手动改规则 | 自动跟随网卡 IP 变化 |
| 性能 | 略高（地址固定，无需每包查询） | 略低（每个新连接都要查询出口地址） |
| 适用场景 | 固定公网 IP | 动态 IP / PPPoE / DHCP 拨号 |

### 适用场景
- **固定公网 IP**：专线、企业宽带，出口地址长期不变，用 SNAT 指定公网 IP，性能更好，规则清晰。
- **动态 IP / PPPoE**：家庭宽带多采用 PPPoE 拨号，运营商每次重拨都会下发不同的公网 IP。若用 SNAT 固定地址，重拨后规则立即失效。此时用 MASQUERADE，内核每次建连自动读取 pppoe-wan 接口的当前 IP。
- **DHCP 上联**：光猫桥接、二级路由级联等场景出口地址随 DHCP 租约变化，同样适合 MASQUERADE。

## OpenWrt 中的配置

### 配置文件位置
OpenWrt 防火墙配置集中在 `/etc/config/firewall`，由 fw3（iptables 后端）或 fw4（nftables 后端）解析。MASQUERADE 由 **zone 区域**的 `masq` 选项开启，不单独写规则。

```
config zone
    option name 'wan'
    option input 'REJECT'
    option output 'ACCEPT'
    option forward 'REJECT'
    option masq '1'                    # 开启源地址转换
    option mtu_fix '1'
    list network 'wan'
    list network 'wan6'
```

### 选项说明
- `masq '1'`：对从该 zone 发出的流量做 MASQUERADE，即内网访问外网时改写源地址。
- `masq_src`：限定只对哪些源地址做转换，例如 `list masq_src '192.168.1.0/24'`。
- `masq_dest`：限定只对发往哪些目的地址做转换，例如只对去往公网的流量做 NAT。
- `mtu_fix '1'`：修正 PPPoE 链路的 MSS，避免大包被丢弃，PPPoE 场景建议开启。

### 生效方式
修改后执行 `/etc/init.d/firewall restart` 使配置生效。fw3 会把 `masq` 选项翻译为 `iptables -t nat -A zone_wan_postrouting -j MASQUERADE`，fw4 则翻译为 nftables 的 `masquerade` 语句。

## 多WAN场景下的SNAT策略

单出口时一条 MASQUERADE 就够，但多 WAN（如双宽带叠加、4G/5G 拨号备份）时，内核只能根据路由表选择出口，NAT 必须与路由保持一致，否则会出现"从 A 出口发出、回包却走 B 出口地址"的错误。

### 核心思路：策略路由 + 多出口 NAT
1. **策略路由**：用 ip rule + ip route 把不同来源或不同目的地址的流量分发到不同的路由表，每个 WAN 一个独立路由表。
2. **多出口 NAT**：每个 WAN 接口分别做一次 MASQUERADE，且规则限定对应的源/目的，保证流量走哪个出口，就被哪个出口的地址转换。

OpenWrt 用 mwan3 管理多 WAN。它自动为每个 WAN 创建独立路由表，并在 firewall 中生成对应的 masq 规则。手工配置示意：

```
config zone
    option name 'wan1'
    option masq '1'
    list network 'wan1'

config zone
    option name 'wan2'
    option masq '1'
    list network 'wan2'
```

配合 mwan3 的成员与策略：

```
config member 'wan1'
    option interface 'wan1'
    option metric '10'

config policy 'balanced'
    list use_member 'wan1'
    list use_member 'wan2'

config rule 'video'
    option dest_ip '0.0.0.0/0'
    option use_policy 'balanced'
```

### 关键点
- **NAT 与路由必须一一对应**：哪个路由表选中的出口，就用哪个出口做 MASQUERADE，否则回包无法送达。
- **连接跟踪属于单 WAN**：conntrack 记录连接和转换信息，策略路由变化（如 WAN 切换）后，已有连接需要重建。
- **对称性检查**：用 `conntrack -L` 确认每个连接的 orig 方向出口 IP 与 reply 方向的 NAT IP 属于同一个 WAN。

## iptables / nftables 实现

### iptables（fw3，iptables-nft 或 iptables-legacy 后端）
固定公网 IP 用 SNAT：

```
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth1 -j SNAT --to-source 1.2.3.4
```

动态 IP 用 MASQUERADE：

```
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o pppoe-wan -j MASQUERADE
```

### nftables（fw4 后端）
```
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        ip saddr 192.168.1.0/24 oifname "pppoe-wan" masquerade
    }
}
```

固定地址写法改为：

```
ip saddr 192.168.1.0/24 oifname "eth1" snat to 1.2.3.4
```

## NAT会话表查看

NAT 转换结果记录在连接跟踪表（conntrack）中，由 `nf_conntrack` 模块维护。查看命令：

```
conntrack -L                      # 查看全部连接
conntrack -L -p tcp -d 8.8.8.8    # 过滤特定目的地址
conntrack -L --status ASSURED     # 只看已确认的双向连接
conntrack -D -p udp               # 删除 UDP 连接（测试时清表）
```

输出示例：

```
tcp      6 431982 ESTABLISHED src=192.168.1.100 dst=8.8.8.8 sport=34567 dport=443
src=8.8.8.8 dst=1.2.3.4 sport=443 dport=34567 [ASSURED] mark=0 use=1
```

### 字段解读
- **第一行（orig 方向）**：内网主机 `192.168.1.100` 访问 `8.8.8.8:443`。
- **第二行（reply 方向）**：`1.2.3.4:443` 回包给 `192.168.1.100:34567`，其中 `1.2.3.4` 就是 MASQUERADE 改写后的公网源地址。
- `ESTABLISHED` 表示双向均见过包，`ASSURED` 表示连接已确认稳定，不会被轻易回收。

常用排障思路：内网无法上网时，先看路由是否正确，再看 conntrack 表中 reply 方向的源地址是否为当前出口公网 IP。若 NAT 改写地址与出口 IP 不一致，多半是策略路由与 NAT 规则没对齐。

## 小结
- 固定 IP 用 SNAT，动态 IP（PPPoE/DHCP）用 MASQUERADE。
- OpenWrt 里开 zone 的 `masq` 即可，无需手工写规则。
- 多 WAN 必须让 NAT 跟随策略路由，每个出口独立 masq。
- conntrack 是排查 NAT 问题的第一现场。

## OpenWRT 端口映射（DNAT / Port Forwarding）


端口映射把公网 IP 的某个端口「转发」到内网某台主机的某个端口，让外网用户能访问内网服务。OpenWRT 里端口映射的本质是 **DNAT（目的地址转换）**，在防火墙 nat 表的 PREROUTING 链上改写目的地址和目的端口。

## 一、DNAT / 端口映射原理

外网客户端访问 `公网IP:公网端口`，报文到达路由器 WAN 口后：

1. 报文进入 PREROUTING 链，命中 DNAT 规则。
2. 目的地址改写为内网主机 IP，目的端口改写为内网端口。
3. 报文按新目的地址查路由表，从 LAN 口转发出去。
4. 内网主机应答，回包回到路由器，命中 conntrack 里记录的映射关系，反向转换后回给外网客户端。

与 SNAT 的区别：**DNAT（端口映射）** 改的是**目的**地址和端口，方向「外 → 内」；**SNAT（源地址转换，见 2.NAT源地址转换.md）** 改的是**源**地址，方向「内 → 外」。两者常配合使用：DNAT 决定数据去谁家，SNAT 决定数据以谁的身份出门。内网主机回包能正确回到路由器，靠的就是 conntrack 的双向映射表。

## 二、LuCI 页面配置（网络 → 防火墙 → 端口转发）

入口：`网络 → 防火墙 → 端口转发 → 添加`。页面字段与 UCI 配置项的对应：

| LuCI 字段 | 对应 UCI option | 说明 |
|-----------|-----------------|------|
| 名称 | name | 规则名字，仅用于标识 |
| 协议 | proto | tcp / udp / tcpudp |
| 外部端口 | src_dport | WAN 侧端口，即公网端口 |
| 内部 IP 地址 | dest_ip | 内网目标主机 IP |
| 内部端口 | dest_port | 内网目标端口 |
| 目标区域 | dest | 默认 lan |

添加后点「保存并应用」生效。LuCI 底层仍是写 `/etc/config/firewall`，然后触发 `/etc/init.d/firewall reload`。

## 三、/etc/config/firewall 的 redirect 配置

端口映射在 UCI 里对应 **redirect 配置节**，语法：

```ini
config redirect
	option name 'Web服务器映射'
	option src 'wan'            # 源区域，一般是 wan
	option proto 'tcp'          # 协议：tcp / udp / tcpudp
	option src_dport '80'       # 公网端口（外部端口）
	option dest_ip '192.168.1.100'   # 内网目标主机 IP
	option dest_port '80'       # 内网目标端口
	option target 'DNAT'        # 转发类型：DNAT（默认）
```

常用 option 说明：

- **src / dest**：源/目标区域，dest 默认 `lan` 一般可省略；多 WAN 场景 src 要指定实际进流量的区域。
- **family**：地址族，`ipv4` / `ipv6` / `any`，IPv6 映射需单独处理。
- **reflection**：NAT 回流开关（见第六节），`1` 开启（默认），`0` 关闭。
- **target**：`DNAT` 表示端口映射；`SNAT` 用于把内网访问重定向到指定出口。
- **src_ip**：限制来源 IP，实现「白名单」端口映射。

修改后生效：`uci commit firewall` 然后 `/etc/init.d/firewall reload`。

## 四、常见场景

场景只是 `src_dport`、`dest_ip`、`dest_port` 三个值不同，套用第一节的模板即可。

| 场景 | src_dport | dest_ip | dest_port |
|------|-----------|---------|-----------|
| Web 服务 | 80 / 443 | 192.168.1.100 | 80 / 443 |
| 远程桌面 | 3389 | 192.168.1.50 | 3389 |
| SSH | 22 | 192.168.1.10 | 22 |

例如 Web 服务器映射：

```ini
config redirect
	option name 'Web服务'
	option src 'wan'
	option proto 'tcp'
	option src_dport '80'
	option dest_ip '192.168.1.100'
	option dest_port '80'
	option target 'DNAT'
```

> 安全提示：3389 长期暴露公网极易被暴力破解，建议修改公网端口，如外部 `13389`，内部仍 `3389`。

**公网端口与内网端口可以不同**，这是端口映射的灵活之处：外网 2222 → 内网 22，外网就少一个被扫描的目标端口。

## 五、端口范围映射 vs 单个端口映射

- **单个端口**：`src_dport` 和 `dest_port` 各填一个端口，一对一映射，适合固定服务（Web、SSH、RDP）。
- **端口范围**：适合游戏、P2P、视频监控等多端口应用。范围两端用 `-` 连接，`dest_port` 可填相同范围整体平移，也可收拢到单个端口：

```ini
# 整体平移：外部 10000-20000 → 内部 10000-20000
config redirect
	option name '游戏端口段'
	option src 'wan'
	option proto 'tcpudp'
	option src_dport '10000-20000'
	option dest_ip '192.168.1.88'
	option dest_port '10000-20000'
	option target 'DNAT'
# 收拢到单端口：外部 50000-50100 → 内部 80
config redirect
	option name '范围收拢'
	option src 'wan'
	option proto 'tcp'
	option src_dport '50000-50100'
	option dest_ip '192.168.1.100'
	option dest_port '80'
	option target 'DNAT'
```

## 六、注意事项：NAT 回流（NAT Loopback / Hairpin）

端口映射配好后，**外网访问正常，但内网设备用「公网 IP + 端口」访问映射的服务却不通**，这就是经典的 NAT 回流问题。

原因是内网设备访问公网 IP 时，报文从 LAN 口进来，目标是「公网 IP」。若只做了 PREROUTING 的 DNAT，回包的路由方向不对（数据从 LAN 出，目标却是 WAN 上的公网地址），连接建立失败。

OpenWRT 的 redirect 规则默认带 **reflection（回流）** 支持：额外生成一条规则，内网访问公网 IP:端口 时同样做 DNAT 并强制走内网出口。

```ini
option reflection '1'    # 开启 NAT 回流（默认开启）
```

排查建议：

- 内网访问不通，先确认 `reflection` 是否为 `0`。
- 仍不通时，检查内网主机的**本机防火墙**，或服务是否绑定在特定网卡/回环地址。
- 部分场景用「DNS 重定向或 hosts 指向内网 IP」可绕开，但 reflection 才是标准做法。
- 部分厂商定制固件默认不开启回流，需手动补 `reflection '1'`。

## 七、小结

端口映射 = DNAT，是 OpenWRT 防火墙的核心能力。配一条映射只需三步：确定协议、定公网端口（src_dport）、定内网目标（dest_ip + dest_port）。reflection 默认开启保证内网也能访问，公网端口与内网端口可不同以增强安全性，范围映射适用于多端口应用。排查时先 `iptables -t nat -L -n`（或 nft）确认规则已下发，再结合 `tcpdump` 抓包定位。

## DMZ（非军事区）


### 一、概述

#### 1.1 什么是 DMZ
DMZ（Demilitarized Zone，非军事区）在 CPE/家庭网关中通常指**暴露主机（Exposed Host）**功能：把所有未被端口映射规则匹配的外网入站流量，全部转发到指定的内网主机。

该功能在 OpenWrt 中通过防火墙的 DNAT 规则实现，本质是一条"全端口、全协议"的目的地址转换规则。

#### 1.2 DMZ 的作用
- **全端口暴露**：将 WAN 侧入站流量无差别转发给指定内网主机
- **免逐个配置**：无需为每个端口单独建立映射规则
- **透明转发**：保留原始目的端口，不做端口改写
- **规则优先级最低**：只处理未被端口映射匹配的流量

#### 1.3 与防火墙的关系
DMZ 主机收到的流量仍要经过防火墙 NAT 阶段，只是放行策略更宽松。防火墙 zone 的 forward 规则仍需允许 wan 到 lan 的转发，否则 DNAT 之后的流量会被转发策略拦下。

---

### 二、实现原理

#### 2.1 iptables 层面的实现
DMZ 在 iptables 的 nat 表 PREROUTING 链（OpenWrt 中为 `zone_wan_prerouting`）添加一条全端口的 DNAT 规则，把入站流量统一指向 DMZ 主机：

```bash
iptables -t nat -A zone_wan_prerouting -j DNAT --to-destination 192.168.1.100
```

#### 2.2 与端口映射的区别
| 特性 | 端口映射 | DMZ |
|------|----------|-----|
| 匹配范围 | 指定端口/端口段 | 全部端口 |
| 协议 | 可指定 tcp/udp | 全部协议 |
| 端口改写 | 可改写目的端口 | 保留原端口 |
| 规则优先级 | 高 | 低 |
| 暴露面 | 受控 | 全暴露 |

DNAT 匹配顺序：更具体的端口映射规则优先命中，未匹配的流量才落到 DMZ 规则上。

---

### 三、OpenWrt 中配置 DMZ

#### 3.1 通过 LuCI 配置
OpenWrt 官方 LuCI 没有独立的"DMZ"页面，通用做法是在 **Network > Firewall > Port Forwards** 新建一条端口转发，外部端口留空或填 `1-65535`，目标 IP 填 DMZ 主机地址。部分厂商基于 OpenWrt 定制的固件才有独立 DMZ 配置页。

#### 3.2 通过命令行配置（UCI）
编辑 `/etc/config/firewall`，添加一条 `config redirect`（不设置 `dest_port`，保留原始端口）：

```
config redirect
	option name 'DMZ'
	option src 'wan'
	option dest 'lan'
	option dest_ip '192.168.1.100'
	option proto 'all'
	option target 'DNAT'
	option family 'ipv4'
```

等价 uci 命令：`uci add firewall redirect`，随后用 `uci set firewall.@redirect[-1].xxx=...` 逐项赋值，最后 `uci commit firewall` 并 `/etc/init.d/firewall reload` 生效。

注意：DMZ 主机需要固定的内网 IP，建议通过 DHCP 静态租约绑定，避免地址变化后 DMZ 失效。

---

### 四、安全风险与使用建议

#### 4.1 安全风险
- **完全暴露**：DMZ 主机的所有端口都暴露在公网，等于绕过了防火墙保护
- **横向渗透**：DMZ 主机一旦被入侵，攻击者可以借它攻击内网其他设备
- **弱口令与漏洞**：暴露的设备若存在默认口令、未打补丁的漏洞，极易被扫描利用
- **扫描流量消耗**：公网扫描器会持续向 DMZ 主机发送探测流量，占用带宽和资源

#### 4.2 使用建议
- **能不用就不用**：只开放少数服务时，优先使用端口映射
- **只放专用设备**：DMZ 主机只放游戏主机、摄像头、服务器等专用设备，不要放日常办公电脑
- **及时加固**：关闭无关服务，修改默认口令，及时更新固件和补丁
- **配合其他措施**：必要时开启主机自带防火墙、IP 白名单、带宽限速
- **短期使用**：调试完成后及时关闭 DMZ，改用精准的端口映射

---

### 五、在 CPE/家庭网关中的典型应用场景

1. **游戏主机**：Xbox/PlayStation 等对 NAT 类型敏感，开启 DMZ 可解决 Strict NAT、P2P 联机失败问题
2. **网络摄像头/NVR**：需要借助厂商 App 远程访问，逐个端口映射成本高，直接开 DMZ 更省事
3. **不支持 UPnP 的老设备**：老式设备无法自动映射端口，只能通过 DMZ 全端口暴露
4. **家庭实验室**：临时搭建 Web/测试服务器，图省事直接 DMZ 到内网某台主机
5. **VoIP/SIP 终端**：部分话机需要大量动态端口，逐个映射维护成本高

DMZ 是"快而糙"的解决方案，适合对安全性要求不高的设备；生产环境务必用端口映射加精准放行替代。

补充：企业网络中的"DMZ"指防火墙与内网之间的隔离区（放置对外提供服务的 Web/Mail 服务器），而 CPE 网关的 DMZ 是"暴露主机"，两个概念不同，注意区分。
