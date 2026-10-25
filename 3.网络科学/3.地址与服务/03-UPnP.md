---
id: "svc-upnp-03"
title: "UPnP 与 IGD"
cluster: svc
layer: L1
status: draft
confidence: medium
platform: ["OpenWrt 23.05"]
source:
  - type: standard
    ref: "UPnP Device Architecture 1.0/1.1; UPnP IGD:1/2"
verified_on: null
tags: ["upnp", "igd", "ssdp", "soap", "port-mapping"]
aliases: ["UPnP", "IGD", "NAT-PMP"]
created: 2026-10-24
updated: 2026-10-24
---

# UPnP 与 IGD

> 解决什么问题：应用如何自动开端口；为什么 UPnP 有安全风险；OpenWrt 上怎么配/排障。
> 不解决：具体应用（游戏/下载）的兼容性。

## 1. 角色

| 角色 | 说明 |
|---|---|
| Control Point | 发起发现/控制的客户端（PC/手机） |
| Device | 提供服务的设备（路由器 IGD） |
| Service | 设备上的服务（WANIPConnection 等） |

IGD = Internet Gateway Device，提供端口映射/外部 IP/连接状态。

## 2. 协议栈

```text
SSDP（发现，UDP 1900 组播）
  → HTTP（描述 XML）
    → SOAP（控制）
      → GENA（事件）
```

### 2.1 SSDP

- `M-SEARCH` 组播搜索；设备 `NOTIFY` 通告。
- 返回 `LOCATION`（描述 URL）。
- 设备类型：`InternetGatewayDevice:1`。

### 2.2 描述

- 获取 `device.xml`/`service.xml`。
- 包含服务类型、控制 URL、事件 URL。

### 2.3 SOAP 控制

```xml
<u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
  <NewRemoteHost></NewRemoteHost>
  <NewExternalPort>8080</NewExternalPort>
  <NewProtocol>TCP</NewProtocol>
  <NewInternalPort>80</NewInternalPort>
  <NewInternalClient>192.168.1.10</NewInternalClient>
  <NewEnabled>1</NewEnabled>
  <NewPortMappingDescription>demo</NewPortMappingDescription>
  <NewLeaseDuration>0</NewLeaseDuration>
</u:AddPortMapping>
```

常用动作：`AddPortMapping`、`DeletePortMapping`、`GetExternalIPAddress`、`GetGenericPortMappingEntry`。

### 2.4 GENA

- 订阅事件（外部 IP 变化/连接状态）。
- 设备通过 `NOTIFY` 推送。

## 3. IGD 服务

| 服务 | 用途 |
|---|---|
| WANIPConnection:1/2 | IP 接入口的端口映射 |
| WANPPPConnection:1 | PPPoE 接入口 |
| Layer3Forwarding | 默认路由 |
| DeviceInfo | 厂商/型号 |

## 4. 与 NAT-PMP/PCP

| 协议 | 特点 |
|---|---|
| UPnP IGD | XML/SOAP，生态广 |
| NAT-PMP | 简单 UDP，Apple |
| PCP | NAT-PMP 后继，支持 IPv6 |

## 5. 安全风险

| 风险 | 说明 |
|---|---|
| 应用私自开端口 | 绕过管理员 |
| 暴露内网服务 | 摄像头/NAS |
| 恶意软件 | 持久映射 |
| 无认证 | 局域网内可调用 |

对策：

- 默认关闭或按需开启。
- 限制 LAN 来源/白名单。
- 映射租约/审计日志。
- 定期清理。

## 6. OpenWrt

```bash
uci show upnpd
/etc/init.d/miniupnpd status
logread | grep -i upnp
```

配置要点：

- `enabled`、`internal_iface`/`external_iface`。
- `secure_mode`、`upnp_forward_chain`。
- 防火墙放行/隔离。

## 7. 排障

```bash
# 发现
tcpdump -ni br-lan 'udp port 1900'
# 控制
tcpdump -ni br-lan 'tcp port 5000'   # 端口随实现
# 查看映射
uci show upnpd
nft list ruleset | grep -i upnp
```

| 现象 | 首查 |
|---|---|
| 应用找不到网关 | SSDP/组播/防火墙 |
| 映射失败 | 权限/端口冲突/地址 |
| 外网访问不了 | 防火墙/运营商 NAT |
| 映射自动消失 | 租约/重启 |
| 安全告警 | 关闭/白名单 |

## 8. 设计建议

- 默认关闭，提供明确开关。
- 只允许内网可信网段。
- 记录映射来源/时间。
- 与防火墙/NAT 规则联动，避免绕过。

## 9. 相关

- [NAT 与 conntrack](../../8.数据面工程/03-NAT与conntrack.md)
- [防火墙](../../8.数据面工程/02-Netfilter与防火墙.md)
- [OpenWrt 防火墙配置](../../7.平台与集成/1.OpenWrt/4.网络业务/3.关键组件服务/02-防火墙配置.md)
- [网络安全原理](../1.网络原理/08-网络安全原理.md)
