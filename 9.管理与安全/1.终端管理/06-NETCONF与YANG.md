---
id: "mgt-06"
title: "NETCONF 与 YANG"
cluster: mgt
layer: L1
status: draft
confidence: medium
platform: []
source:
  - type: rfc
    ref: "RFC 6241 (NETCONF), RFC 6242 (SSH), RFC 7950 (YANG 1.1)"
verified_on: null
tags: ["netconf", "yang", "model", "automation"]
aliases: ["NETCONF", "YANG"]
created: 2026-10-24
updated: 2026-10-24
---

# NETCONF 与 YANG

> 解决什么问题：模型驱动配置、事务/回滚、自动化；与 TR-069 的差异与选型。
> 不解决：具体厂商 YANG 模型。

## 1. 协议栈

```text
NETCONF (RPC/XML)
  └─ SSH (830) / TLS
      └─ YANG 模型
          └─ Datastore (running/candidate/startup)
```

| 层 | 作用 |
|---|---|
| 传输 | SSH/TLS |
| 消息 | `<rpc>`, `<rpc-reply>`, `<notification>` |
| 操作 | get/get-config/edit-config/commit/lock |
| 模型 | YANG 定义数据结构/约束 |

## 2. 会话

```text
<hello> 交换 capabilities/session-id
  ↓
<lock> → <edit-config> → <commit> → <unlock>
  ↓
<close-session>
```

能力（capabilities）决定支持哪些操作/模型；先 `hello` 再发 RPC。

## 3. Datastore

| 存储 | 说明 |
|---|---|
| running | 当前生效 |
| candidate | 候选，可编辑后 commit |
| startup | 启动配置 |
| intended | 厂商扩展 |

`candidate` + `confirmed-commit` 支持“提交后超时自动回滚”。

## 4. 常用 RPC

```xml
<rpc message-id="1" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>
    <source><running/></source>
    <filter type="subtree">
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>
    </filter>
  </get-config>
</rpc>
```

```xml
<rpc message-id="2" ...>
  <edit-config>
    <target><candidate/></target>
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>eth0</name>
          <enabled>true</enabled>
        </interface>
      </interfaces>
    </config>
  </edit-config>
</rpc>
```

## 5. YANG

```yang
module demo {
  namespace "urn:demo";
  prefix d;
  container system {
    leaf hostname { type string; }
    leaf mtu { type uint16; default 1500; }
    list interface {
      key "name";
      leaf name { type string; }
      leaf enabled { type boolean; default true; }
    }
  }
}
```

| 语句 | 作用 |
|---|---|
| container | 容器 |
| leaf | 叶子 |
| list/key | 列表/主键 |
| leaf-list | 多值 |
| choice/case | 分支 |
| must/unique | 约束 |
| rpc/notification | 操作/事件 |

## 6. 工具

| 工具 | 用途 |
|---|---|
| `netopeer2` | 开源 NETCONF 服务端 |
| `sysrepo` | 数据存储 |
| `libyang` | YANG 解析 |
| `ncclient` | Python 客户端 |
| `yanglint` | 模型校验 |

最小实验：

```bash
# 服务端
netopeer2-server -d
# 客户端
netconf-console --host 127.0.0.1 --port 830 --get-config
```

## 7. 与 TR-069 的差异

| 项 | TR-069 | NETCONF/YANG |
|---|---|---|
| 传输 | HTTP/SOAP | SSH/XML |
| 模型 | TR-098/181 | YANG |
| 事务 | 弱 | candidate/commit/rollback |
| 通知 | Inform | notification |
| 适用 | 运营商 CPE | 网络设备/自动化 |

## 8. 常见问题

| 现象 | 原因 |
|---|---|
| 连接失败 | SSH/端口/密钥 |
| RPC 不支持 | capability/模型 |
| 配置不生效 | 未 commit/目标 datastore |
| 模型报错 | 命名空间/版本/约束 |
| 回滚失败 | 未用 candidate/confirmed-commit |

## 9. 设计建议

- 先定义 YANG，再写实现。
- 变更走 candidate + confirmed-commit。
- 权限/审计与 SSH 密钥管理。
- 模型版本兼容/废弃策略。

## 10. 相关

- [TR-069](01-TR-069.md)
- [TR-369](02-TR-369.md)
- [PKI 与证书](../3.安全与认证/01-PKI与证书.md)
- [自动化测试](../../10.工程方法/5.测试与实验/03-自动化测试.md)
