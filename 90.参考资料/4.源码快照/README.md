---
id: "ref-source"
title: "源码快照说明"
cluster: ref
layer: L1
status: review
confidence: high
platform: []
source: []
tags: ["source"]
---

# 源码快照说明

> 与笔记直接相关的源码快照，**只读**，不修改。

## 目录

| 目录 | 来源 | 用途 |
|---|---|---|
| `netifd/` | OpenWrt netifd | 阅读接口/调用链/协议处理 |
| `Linux011/` | Linux 0.11 | 早期内核学习 |
| `leds/` | Linux 内核 LED 驱动 | 驱动模型示例 |

## 上游

| 项目 | 地址 |
|---|---|
| netifd | <https://git.openwrt.org/project/netifd.git> |
| Linux 0.11 | <https://www.kernel.org/>（历史版本） |
| Linux LED | <https://git.kernel.org/> |

## 未收录

- **net-snmp 全量源码**：体积大、上游可获取，本库不内置。
  获取：<https://www.net-snmp.org/download.html>

## 使用规则

- 引用源码必须写清“路径 + 版本/commit”。
- 需要实验时复制到临时目录，不在此目录修改。
- 源码快照不参与知识框架索引。
