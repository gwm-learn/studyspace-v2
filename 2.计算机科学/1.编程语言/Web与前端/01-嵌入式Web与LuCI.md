---
id: "cs-web-01"
title: "嵌入式 Web 与 LuCI"
cluster: cs
layer: L2
status: draft
confidence: medium
platform: ["OpenWrt 23.05"]
source: []
verified_on: null
tags: ["web", "cgi", "luci", "ubus", "uci"]
aliases: ["LuCI", "嵌入式Web"]
created: 2026-10-24
updated: 2026-10-24
---

# 嵌入式 Web 与 LuCI

> 解决什么问题：管理页面打不开、配置不生效、登录/权限异常、前后端数据不通。
> 不解决：具体前端框架/UI 设计。

## 1. 架构

```text
浏览器
  │ HTTP/HTTPS
  ▼
uhttpd / lighttpd / nginx
  │ CGI / Lua / ucode
  ▼
LuCI 控制器/视图
  │ ubus / uci / shell
  ▼
系统服务（netifd、dnsmasq、hostapd…）
```

## 2. 组件

| 组件 | 作用 |
|---|---|
| uhttpd | OpenWrt 默认 Web 服务器 |
| LuCI | Web 管理框架（MVC） |
| ubus | 运行时 RPC |
| uci | 持久化配置 |
| rpcd | 权限/对象访问 |
| ucode/Lua | 后端脚本 |

## 3. 请求链路

1. 浏览器请求 `/cgi-bin/luci/...`。
2. uhttpd 交给 LuCI。
3. 控制器解析参数、鉴权。
4. 通过 ubus/uci 读写状态/配置。
5. 渲染视图或返回 JSON。

## 4. 鉴权与会话

- 登录后发 session token/cookie。
- 会话有超时；并发登录策略。
- 权限分级（只读/管理）。
- 敏感操作二次确认/审计日志。

## 5. 安全

| 风险 | 防护 |
|---|---|
| CSRF | Token、SameSite、来源校验 |
| XSS | 输出编码、CSP |
| 命令注入 | 参数白名单、避免拼 shell |
| 路径穿越 | 规范化、根目录限制 |
| 弱口令 | 强口令、锁定、默认改密 |
| 明文传输 | HTTPS + 证书 |

## 6. 前后端数据

- 后端返回 JSON；前端 fetch/XHR。
- 大列表分页；避免一次拉全量。
- 错误统一格式（code/message）。
- 长操作异步 + 进度。

## 7. 调试

```bash
ps | grep -E 'uhttpd|lighttpd'
logread | tail -50
ubus list
ubus call network.interface.wan status
uci show network
curl -v http://192.168.1.1/cgi-bin/luci/
```

| 现象 | 首查 |
|---|---|
| 404 | 路由/根目录/权限 |
| 500 | 后端脚本错误/权限 |
| 配置不生效 | `uci commit` + reload |
| 登录失败 | 会话存储/时间/密码 |
| 页面空白 | JS 错误/接口 401 |
| 卡顿 | 同步阻塞/大查询 |

## 8. 性能

- 静态资源缓存/压缩。
- 减少 ubus 往返；批量查询。
- 避免在请求里做长耗时操作。
- 嵌入式内存小，注意并发连接数。

## 9. 设计建议

- 配置写入走 uci，运行时状态走 ubus。
- 不要在前端直接拼命令。
- 所有写操作校验参数/权限。
- 关键操作记录审计日志。

## 10. 相关

- [uci](../../../7.平台与集成/1.OpenWrt/3.管理平面/07-uci.md)
- [ubus](../../../7.平台与集成/1.OpenWrt/3.管理平面/06-ubus.md)
- [安全与认证](../../../9.管理与安全/3.安全与认证/00-总览.md)
- [代码质量与测试](../../5.软件工程/01-代码质量与测试.md)
