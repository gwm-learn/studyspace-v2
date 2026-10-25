#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 0.框架/知识框架图.md：可视化知识框架 + 可点击索引。

不是学习路线：节点是知识域/概念，边是依赖关系。
"""
import os
import re

def sort_key(d):
    m = re.match(r"(\d+)", d)
    return (int(m.group(1)) if m else 999, d)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "0.框架", "知识框架图.md")
SKIP = {".git", "assets", "99-归档", "__pycache__"}

DOMAINS = [
    ("1.基础科学", "数学、物理与电磁、电子电路、信号与系统"),
    ("2.计算机科学", "编程语言、数据结构与算法、脚本与自动化"),
    ("3.网络科学", "网络原理、接入协议、地址与服务、二层协议、路由与组播"),
    ("4.通信科学", "无线、蜂窝与终端、射频与天线"),
    ("5.嵌入式系统", "硬件与板级：启动、DTS、分区、接口、硬件调试"),
    ("6.系统软件", "Linux 内核、驱动、网络栈、调试观测"),
    ("7.平台与集成", "OpenWrt、构建系统（Yocto/CMake/make）"),
    ("8.数据面工程", "DSA、Netfilter/NAT、QoS、转发加速、网桥"),
    ("9.管理与安全", "终端管理、隧道与 VPN、安全与认证"),
    ("10.工程方法", "调试与性能、诊断与观测、开发环境、Linux 使用、测试与实验"),
    ("11.应用与案例", "项目、ADR、认证、产线、运维、合规（应用层）"),
]


def fm(p):
    t = open(p, encoding="utf-8").read()
    d = {}
    if t.startswith("---\n"):
        e = t.find("\n---\n", 4)
        if e != -1:
            for line in t[4:e].splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    d[k.strip()] = v.strip().strip('"')
            t = t[e + 5:]
    return d, t


def rel(target):
    return os.path.relpath(os.path.join(ROOT, target), os.path.join(ROOT, "0.框架")).replace(os.sep, "/")


def link(label, target):
    if os.path.exists(os.path.join(ROOT, target)):
        return f"[{label}]({rel(target)})"
    return f"{label}（待补）"


def main():
    lines = [
        "---",
        'id: "framework-map"',
        'title: "知识框架图"',
        "cluster: framework",
        "layer: L1",
        "status: review",
        "confidence: high",
        "platform: []",
        "source: []",
        'tags: ["framework", "map", "moc"]',
        'aliases: ["框架图", "知识地图"]',
        "created: 2026-10-24",
        "updated: 2026-10-24",
        "---",
        "",
        "# 知识框架图",
        "",
        "> 这张图把**知识域、概念、实现、应用**串起来；它不是课程表，也不是项目排期。",
        "> 先看域间关系，再按“包的一生 / 一次入网 / 一次升级”三条主线跳转。",
        "",
        "## 1. 域间关系",
        "",
        "```mermaid",
        "flowchart TD",
        '  FND["1.基础科学"] --> COM["4.通信科学"]',
        '  FND --> EMB["5.嵌入式系统"]',
        '  FND --> NET["3.网络科学"]',
        '  CS["2.计算机科学"] --> OS["6.系统软件"]',
        '  CS --> NET',
        '  NET --> DP["8.数据面工程"]',
        '  OS --> DP',
        '  EMB --> OS',
        '  COM --> NET',
        '  PLT["7.平台与集成"] --> DP',
        '  OS --> PLT',
        '  DP --> SEC["9.管理与安全"]',
        '  NET --> SEC',
        '  ENG["10.工程方法"] -.-> NET',
        '  ENG -.-> OS',
        '  ENG -.-> DP',
        '  APP["11.应用与案例"] -.-> PLT',
        '  APP -.-> SEC',
        "```",
        "",
        "> 实线：概念/实现依赖；虚线：方法/验证反哺。",
        "",
        "## 2. 三条主线",
        "",
        "### 2.1 一个包的一生（数据面）",
        "",
        "```mermaid",
        "flowchart LR",
        '  RF["射频/空口"] --> PHY["PHY/MAC"]',
        '  PHY --> DRV["网卡/驱动"]',
        '  DRV --> KNET["内核网络栈"]',
        '  KNET --> NF["Netfilter/NAT"]',
        '  KNET --> FWD["转发/DSA"]',
        '  NF --> APP["应用/服务"]',
        '  FWD --> APP',
        "```",
        "",
        "| 步 | 概念 | 去哪里 |",
        "|---:|---|---|",
        f"| 1 | 射频/空口 | {link('通信科学', '4.通信科学/00-总览.md')} |",
        f"| 2 | PHY/MAC | {link('802.11 原理', '4.通信科学/1.无线/01-802.11原理.md')} |",
        f"| 3 | 网卡/驱动 | {link('驱动模型', '6.系统软件/1.Linux内核与驱动/04-驱动模型.md')} |",
        f"| 4 | 内核网络栈 | {link('网络栈', '6.系统软件/1.Linux内核与驱动/03-网络栈.md')} |",
        f"| 5 | Netfilter/NAT | {link('Netfilter与防火墙', '8.数据面工程/02-Netfilter与防火墙.md')} |",
        f"| 6 | 转发/DSA | {link('DSA与交换机', '8.数据面工程/01-DSA与交换机.md')} |",
        f"| 7 | 应用/服务 | {link('应用层协议', '3.网络科学/1.网络原理/06-应用层协议.md')} |",
        "",
        "### 2.2 一次入网（蜂窝/ODU）",
        "",
        "```mermaid",
        "flowchart LR",
        '  SIM["SIM/eSIM"] --> MOD["Modem"]',
        '  MOD --> QMI["QMI/MBIM"]',
        '  QMI --> NET["rmnet/IPA"]',
        '  NET --> NAT["NAT/路由"]',
        '  NAT --> APP["业务"]',
        "```",
        "",
        "| 步 | 概念 | 去哪里 |",
        "|---:|---|---|",
        f"| 1 | SIM/UIM | {link('QMI UIM', '4.通信科学/2.蜂窝与终端/09-QMI-UIM.md')} |",
        f"| 2 | 入网信令 | {link('终端入网流程', '4.通信科学/2.蜂窝与终端/06-终端入网流程.md')} |",
        f"| 3 | QMI/MBIM | {link('QMI NAS', '4.通信科学/2.蜂窝与终端/07-QMI-NAS.md')} |",
        f"| 4 | 数据通路 | {link('Modem IPA', '4.通信科学/2.蜂窝与终端/11-Modem-IPA.md')} |",
        f"| 5 | 拨号配置 | {link('5G 拨号', '7.平台与集成/1.OpenWrt/4.网络业务/1.WAN/03-5G拨号配置.md')} |",
        f"| 6 | ODU 整机 | {link('ODU 与 IDU', '4.通信科学/2.蜂窝与终端/13-ODU与IDU.md')} |",
        "",
        "### 2.3 一次升级（平台/集成）",
        "",
        "```mermaid",
        "flowchart LR",
        '  IMG["镜像"] --> BOOT["U-Boot"]',
        '  BOOT --> KER["Kernel/DTB"]',
        '  KER --> ROOT["RootFS"]',
        '  ROOT --> CFG["配置/overlay"]',
        '  CFG --> RB["回滚/恢复"]',
        "```",
        "",
        "| 步 | 概念 | 去哪里 |",
        "|---:|---|---|",
        f"| 1 | 镜像生成 | {link('镜像原理', '7.平台与集成/1.OpenWrt/1.构建体系/05-镜像原理/00-总览.md')} |",
        f"| 2 | 启动链 | {link('启动链与 U-Boot', '5.嵌入式系统/1.硬件与板级/01-启动链与U-Boot.md')} |",
        f"| 3 | 设备树 | {link('设备树与 DTS', '5.嵌入式系统/1.硬件与板级/02-设备树与DTS.md')} |",
        f"| 4 | 分区/存储 | {link('存储与分区', '5.嵌入式系统/1.硬件与板级/03-存储与分区.md')} |",
        f"| 5 | 升级 | {link('sysupgrade', '7.平台与集成/1.OpenWrt/5.升级与恢复/01-sysupgrade.md')} |",
        f"| 6 | 恢复 | {link('恢复出厂', '7.平台与集成/1.OpenWrt/5.升级与恢复/02-恢复出厂.md')} |",
        "",
        "## 3. 知识域索引",
        "",
    ]

    for name, desc in DOMAINS:
        root = os.path.join(ROOT, name)
        if not os.path.isdir(root):
            continue
        lines += [f"### {name}", "", desc, "", "| 子域/笔记 | 层 | 状态 |", "|---|---|---|"]
        # 子目录
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            hub = os.path.join(p, "00-总览.md")
            if os.path.isdir(p) and os.path.exists(hub):
                d_fm, _ = fm(hub)
                lines.append(f"| {link(d, f'{name}/{d}/00-总览.md')} | {d_fm.get('layer','')} | {d_fm.get('status','')} |")
        # 本域直属笔记
        for f in sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if f.endswith(".md") and f != "00-总览.md" and os.path.isfile(p):
                d_fm, _ = fm(p)
                lines.append(f"| {link(d_fm.get('title', f[:-3]), f'{name}/{f}')} | {d_fm.get('layer','')} | {d_fm.get('status','')} |")
        lines.append("")

    # 全量索引
    lines += ["## 4. 全量索引（按目录）", "", "> 保证每个文件都能从框架图到达。", ""]
    cur = None
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = sorted((d for d in dirs if d not in SKIP), key=sort_key)
        rel_dir = os.path.relpath(root, ROOT).replace(os.sep, "/")
        if rel_dir == ".":
            continue
        for f in sorted(fs):
            if not f.endswith(".md"):
                continue
            if rel_dir != cur:
                cur = rel_dir
                lines += ["", f"#### {rel_dir}", ""]
            p = os.path.join(root, f)
            d_fm, _ = fm(p)
            lines.append(f"- {link(d_fm.get('title', f[:-3]), f'{rel_dir}/{f}')}")

    lines += ["", "## 5. 维护", "", "- 本文件由 `tools/gen_framework_map.py` 生成；新增/移动文件后重跑。", "- 框架原则见 [知识框架.md](知识框架.md)；学习顺序见 [视图/学习路径.md](视图/学习路径.md)（可选）。", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print("framework map:", len(lines), "lines")


if __name__ == "__main__":
    main()
