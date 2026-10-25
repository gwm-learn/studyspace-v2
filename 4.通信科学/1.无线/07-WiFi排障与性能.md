---
id: "wifi-07"
title: "WiFi 排障与性能"
cluster: wifi
layer: L3
status: draft
confidence: medium
platform: ["OpenWrt 23.05"]
source: []
verified_on: null
tags: ["wifi", "troubleshooting", "performance"]
aliases: ["WiFi 排障", "无线性能"]
created: 2026-10-24
updated: 2026-10-24
---

# WiFi 排障与性能

> 解决什么问题：无线"慢/断/连不上"时，如何用数据和日志定位，而不是靠重启。
> 不解决：驱动源码与协议细节。

## 1. 先分层

```text
终端 ── 空口 ── AP（hostapd/mac80211/驱动）── 网桥/VLAN ── 路由/NAT ── 上游
  1        2                3                      4            5
```

| 层 | 关键问题 | 工具 |
|---|---|---|
| 1 终端 | 支持频段/协议、省电、驱动 | 终端侧信息 |
| 2 空口 | 信号、干扰、重传、速率 | `station dump`、扫频 |
| 3 AP | 配置、认证、驱动日志 | `hostapd_cli`、`dmesg` |
| 4 二层 | 网桥/VLAN/隔离 | `bridge`、`ip link` |
| 5 三层 | 地址、路由、NAT、DNS | `ip`、`conntrack`、抓包 |

## 2. 必看指标

```bash
# 关联与速率
iw dev wlan0 link
iw dev wlan0 station dump

# 信道与干扰
iw dev wlan0 survey
iw list | grep -E "Frequencies|Channel"

# 接口统计
ip -s link show wlan0
```

| 指标 | 健康范围（示例） | 异常含义 |
|---|---|---|
| 信号（RSSI） | > -65 dBm 好，< -75 差 | 覆盖不足/遮挡 |
| SNR | > 25 dB | 干扰/距离 |
| 协商速率 | 接近频宽/空间流上限 | 降速 |
| 重传/失败 | 低且稳定 | 干扰/冲突/弱信号 |
| 信道利用率 | < 50% | 拥塞 |
| 终端数 | 不超过设计容量 | 过载 |

## 3. 常见故障与定位

| 现象 | 首查 | 进一步 |
|---|---|---|
| 搜不到 SSID | 射频是否 up、SSID 隐藏、信道/法规 | `iw dev`、`hostapd -dd` |
| 连不上 | 加密/PMF/MAC 过滤/认证 | 抓 4 次握手、hostapd 日志 |
| 连上无 IP | 网桥/VLAN/DHCP | `bridge link`、`udhcpd` 日志 |
| 频繁掉线 | 省电、漫游、干扰、驱动 | `station dump` 时间序列 |
| 速率低 | 频宽/空间流/干扰/回程 | `iw link`、扫频、测回程 |
| 延迟高/抖动 | 空口重传、队列、bufferbloat | `tc -s`、ping 抖动 |
| 只有 2.4G | 终端/信道/DFS | 5G 信道与法规 |
| 大面积不稳定 | 供电/温度/驱动 | `dmesg`、温度、功耗 |

## 4. 干扰与信道

- 2.4G 只用 1/6/11（20 MHz）；40 MHz 在拥挤环境通常更差。
- 5G 优先非 DFS 信道做接入，DFS 信道注意雷达避让。
- 用 `iw survey` 看 busy time，不只看"有没有别的 AP"。
- 高密度场景降低单 AP 功率、增加 AP 密度，而不是一味加大功率。

## 5. 性能测试方法

```bash
# 吞吐（AP 侧或旁路设备）
iperf3 -s
iperf3 -c <server> -t 30 -P 4

# 双向/ UDP
iperf3 -c <server> -t 30 -R
iperf3 -c <server> -u -b 100M

# 时延/抖动
ping -i 0.01 -c 1000 <gateway>
```

测试矩阵：近/中/远点 × 2.4G/5G × 20/40/80 MHz × 单/多终端 × 上/下行。记录环境、终端型号、固件版本。

## 6. 抓包

| 场景 | 抓法 |
|---|---|
| 认证失败 | 空口抓管理帧（需要 monitor 接口） |
| 数据不通 | AP 的网桥/上行口抓包，确认是否转发 |
| 漫游 | 抓 auth/assoc/reassoc 与 FT 帧 |
| 干扰 | 频谱仪/扫频，不是 tcpdump |

```bash
# 创建 monitor 接口（视驱动支持）
iw phy phy0 interface add mon0 type monitor
ip link set mon0 up
tcpdump -ni mon0 -e -s0 'wlan type mgt'
```

## 7. 稳定性测试

- 72 h 连续吞吐 + 周期性漫游。
- 反复上下电 50 次。
- 高温满载 8 h。
- 多终端（如 32/64 台）关联与并发。
- 弱信号边缘（RSSI -75～-85）保持连接能力。

## 8. 待实测/待项目参数
- [ ] 目标平台的实际速率/空间流/频宽能力。
- [ ] 一次"速率只有一半"的完整定位记录。
- [ ] 高密度场景的容量测试数据。

## 9. 相关

- [802.11 原理](01-802.11%E5%8E%9F%E7%90%86.md)
- [hostapd 与安全](05-hostapd%E4%B8%8E%E5%AE%89%E5%85%A8.md)
- [漫游与 Mesh](06-%E6%BC%AB%E6%B8%B8%E4%B8%8EMesh.md)
- [抓包方法](../../10.%E5%B7%A5%E7%A8%8B%E6%96%B9%E6%B3%95/5.%E6%B5%8B%E8%AF%95%E4%B8%8E%E5%AE%9E%E9%AA%8C/02-%E6%8A%93%E5%8C%85%E6%96%B9%E6%B3%95.md)
