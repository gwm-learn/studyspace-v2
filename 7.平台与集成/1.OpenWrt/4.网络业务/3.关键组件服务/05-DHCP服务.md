---
id: "openwrt-net-05"
title: OpenWrt DHCP/DNS 综合：dnsmasq 双角色
cluster: "openwrt-net"
layer: L1
status: draft
confidence: medium
platform: []
source: []
verified_on: null
tags: ["openwrt", "dhcp", "dns"]
aliases: ["DHCP服务"]
created: 2026-10-24
updated: 2026-10-24
---
# OpenWrt DHCP/DNS 综合：dnsmasq 双角色

## 一、概述
OpenWrt 中 DHCP 与 DNS 由同一个进程 **dnsmasq** 承载，一个监听 `*:53`（DNS）和一个监听 `*:67`（DHCP）的服务实例，这是嵌入式设备节省资源的经典设计。配置统一放在 `/etc/config/dhcp`，运行时代码则读取它生成 `/var/etc/dnsmasq.conf`。协议细节见 [DHCP 协议](../../../../3.%E7%BD%91%E7%BB%9C%E7%A7%91%E5%AD%A6/3.%E5%9C%B0%E5%9D%80%E4%B8%8E%E6%9C%8D%E5%8A%A1/01-DHCP%E5%8D%8F%E8%AE%AE.md)。

## 二、双角色架构
### 2.1 一个进程两个角色
- **DNS 角色**：缓存、转发、过滤，读取 WAN 侧下发的上游 DNS（`/tmp/resolv.conf.auto`）
- **DHCP 角色**：为 LAN 设备分配地址，租约写入 `/tmp/dhcp.leases`

### 2.2 双角色的联动
这是 dnsmasq 的核心价值：**DHCP 分配的地址自动进入 DNS**。

- 设备通过 DHCP 拿到地址后，dnsmasq 用 `expandhosts` 把设备名注册到本地 DNS
- LAN 设备可用主机名互相访问，无需配置静态 DNS 记录
- 静态绑定（`config host`）中的 `name` 同样自动生效为 DNS 名称

## 三、配置文件结构
### 3.1 UCI 层（/etc/config/dhcp）
```uci
config dnsmasq
        option domainneeded '1'
        option boguspriv '1'
        option filterwin2k '0'
        option localise_queries '1'
        option rebind_protection '1'
        option local '/lan/'
        option domain 'lan'
        option expandhosts '1'
        option authoritative '1'
        option leasefile '/tmp/dhcp.leases'
        option resolvfile '/tmp/resolv.conf.auto'

config dhcp 'lan'
        option interface 'lan'
        option start '100'
        option limit '150'
        option leasetime '12h'

config host
        option name 'printer'
        option mac 'aa:bb:cc:dd:ee:ff'
        option ip '192.168.1.200'
```

### 3.2 运行时层（/var/etc/dnsmasq.conf）
`/etc/init.d/dnsmasq` 启动时把 UCI 配置转换为 dnsmasq 原生配置格式：
```conf
resolv-file=/tmp/resolv.conf.auto
dhcp-range=192.168.1.100,192.168.1.249,255.255.255.0,12h
dhcp-host=aa:bb:cc:dd:ee:ff,printer,192.168.1.200
expand-hosts
local=/lan/
```
- 转换由 `/usr/share/dnsmasq/dnsmasq.uci` 脚本完成
- 直接改 `/var/etc/dnsmasq.conf` 不持久，重启即被覆盖；改 `/etc/config/dhcp` 才是正途
- 高级选项可通过 UCI 的 `option confdir` 追加 `/etc/dnsmasq.d/*.conf` 片段

## 四、工作流程
### 4.1 DHCP 分配
```
Discover -> Offer -> Request -> Ack（四步握手）
租约 50%（T1）单播续约，87.5%（T2）广播续约
```

### 4.2 DNS 解析优先级
```
dnsmasq 缓存 -> /etc/hosts -> 本地 DHCP 主机名 -> 自定义规则 -> 上游 DNS
```

### 4.3 热插拔联动
接口状态变化时，`/etc/hotplug.d/iface/25-dnsmasq` 触发服务重启或动态调整，保证 DHCP 池与 DNS 上游始终跟随网络拓扑。

## 五、常见配置场景
| 场景 | 配置 |
|------|------|
| 按域名分流 | `/etc/dnsmasq.d/gfw.conf` 中 `server=/google.com/8.8.8.8` |
| 广告屏蔽 | `address=/ad.com/0.0.0.0`，加载 `addn-hosts` 列表 |
| 静态绑定 | `config host` 段，MAC 对应固定 IP 和主机名 |
| 自定义 DHCP option | `option dhcp_option '42,192.168.1.1'` 下发 NTP |

## 六、调试与排查
```bash
dnsmasq --test                      # 校验配置语法
logread -f | grep dnsmasq           # 实时日志
cat /tmp/dhcp.leases                # 查看租约
/etc/init.d/dnsmasq restart         # 强制重载
```
常见问题：时间同步导致租约异常触发 del 事件；`dhcp.@dnsmasq[0].dhcpscript` 可挂脚本实时观察 DHCP 事件。

## 七、参考
- [dnsmasq 协议与功能架构](04-DNS%E4%B8%8Ednsmasq.md)
- [DNS 子系统笔记](04-DNS%E4%B8%8Ednsmasq.md)
- [OpenWrt DHCP 服务器（LAN 视角）](../2.LAN/01-DHCP-Server.md)
- [UCI 配置体系](../../3.%E7%AE%A1%E7%90%86%E5%B9%B3%E9%9D%A2/07-uci.md)
