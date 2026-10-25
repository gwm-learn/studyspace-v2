---
id: "wifi-05"
title: "hostapd 与无线安全"
cluster: wifi
layer: L2
status: draft
confidence: medium
platform: ["OpenWrt 23.05", "hostapd 2.10"]
source:
  - type: code
    ref: "hostapd/hostapd.conf（上游）"
verified_on: null
tags: ["hostapd", "wpa2", "wpa3", "wifi"]
aliases: ["hostapd", "WPA3"]
created: 2026-10-24
updated: 2026-10-24
---

# hostapd 与无线安全

> 解决什么问题：AP 怎么起来、加密怎么配、WPA3/PMF 怎么开、常见认证失败怎么查。
> 不解决：驱动与 cfg80211/nl80211（→ [cfg80211](02-cfg80211.md)、[nl80211](03-nl80211.md)）。

## 1. 在无线栈中的位置

```text
LuCI/UCI → netifd/wifi-scripts → hostapd
                                  │  nl80211
                                  ▼
                             cfg80211 → mac80211 → 驱动（mt76）
                                  │
                                  ▼
                              硬件/射频
```

hostapd 负责：认证、关联、密钥协商、802.11k/v/r 相关管理、ACL、计费（可选）。

## 2. 最小配置

```conf
interface=wlan0
driver=nl80211
ssid=MyAP
hw_mode=g
channel=6
country_code=CN
ieee80211n=1
ieee80211ac=1

wpa=2
wpa_key_mgmt=WPA-PSK SAE
wpa_passphrase=change-me
rsn_pairwise=CCMP
ieee80211w=2
sae_require_mfp=1
```

| 配置 | 含义 |
|---|---|
| `wpa=2` | WPA2/WPA3（RSN） |
| `wpa_key_mgmt` | `WPA-PSK`（WPA2）、`SAE`（WPA3） |
| `ieee80211w` | 0 关闭 / 1 可选 / 2 必须（PMF） |
| `sae_require_mfp` | WPA3 要求管理帧保护 |
| `country_code` | 法规域，影响信道/功率 |

> OpenWrt 通常不直接手写 hostapd.conf，而是由 `/etc/config/wireless` + `wifi` 脚本生成；调试时可临时手写验证。

## 3. WPA2 / WPA3 / 混合模式

| 模式 | 密钥协商 | 兼容性 | 建议 |
|---|---|---|---|
| WPA2-PSK | 4 次握手 | 最好 | 兼容旧设备 |
| WPA3-SAE | SAE | 较新设备 | 新设备默认 |
| 混合 | PSK + SAE | 较好 | 过渡期 |
| WPA3-Enterprise | 802.1X/EAP | 企业 | 需 RADIUS |
| OWE | 无口令加密 | 开放网络 | 替代开放 SSID |

注意：WPA3 开启 PMF 后，部分老设备无法连接；过渡期用混合模式并观察。

## 4. 常用调试

```bash
# 前台跑 hostapd，直接看日志
hostapd -dd /etc/hostapd.conf

# 查看关联终端
iw dev wlan0 station dump
hostapd_cli all_sta
hostapd_cli status

# 查看当前配置
uci show wireless
iw list | grep -A5 "Supported Ciphers"
```

## 5. 常见失败

| 现象 | 可能原因 | 定位 |
|---|---|---|
| AP 起不来 | 驱动/接口名/信道/法规 | `hostapd -dd`、`dmesg` |
| 终端连不上 | 加密不匹配、PMF、MAC 过滤 | `hostapd_cli`、抓 4 次握手 |
| 连上但无 IP | DHCP/网桥/VLAN | `brctl show`、`udhcpd` 日志 |
| 频繁掉线 | 干扰、省电、漫游阈值 | `station dump` 重传/信号 |
| WPA3 失败 | 终端不支持、时间不同步 | 换 WPA2 对比 |
| 速率低 | 频宽/空间流/干扰/协商速率 | `iw dev wlan0 link` |

## 6. 安全基线

- [ ] 禁用 WEP/TKIP；只用 CCMP/GCMP。
- [ ] 关闭 WPS（或仅 PBC 且限时）。
- [ ] 管理帧保护（PMF）开启。
- [ ] 强口令，禁用默认 SSID/口令。
- [ ] 访客网络隔离（AP isolation + 防火墙）。
- [ ] 关闭不用的 SSID/射频。
- [ ] 法规域与功率正确，避免干扰。

## 7. 待实测/待项目参数
- [ ] 目标平台的 hostapd 版本与 mt76 支持矩阵。
- [ ] 一次 WPA3 连接失败的抓包分析。
- [ ] 访客网络隔离的完整配置。

## 8. 相关

- [802.11 原理](01-802.11%E5%8E%9F%E7%90%86.md)
- [cfg80211](02-cfg80211.md)
- [nl80211](03-nl80211.md)
- [WiFi 排障与性能](07-WiFi%E6%8E%92%E9%9A%9C%E4%B8%8E%E6%80%A7%E8%83%BD.md)
- [无线网络与移动通信](08-%E6%97%A0%E7%BA%BF%E7%BD%91%E7%BB%9C%E4%B8%8E%E7%A7%BB%E5%8A%A8%E9%80%9A%E4%BF%A1.md)
