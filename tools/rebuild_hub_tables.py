#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 Hub 的“子主题/笔记”两张表，修复重复与遗漏。"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", "assets", "99-归档", "__pycache__", "项目实践", "4.源码快照"}
MANUAL = {
    "1.基础科学", "2.计算机科学", "3.网络科学", "4.通信科学",
    "5.嵌入式系统", "7.平台与集成", "9.管理与安全",
    "10.工程方法", "11.应用与案例",
}
DESC = {
    "1.构建体系": "从环境准备到镜像生成的完整构建链",
    "2.启动与板级": "启动链、U-Boot、DTS、分区",
    "3.管理平面": "procd/ubus/uci/netifd",
    "4.网络业务": "WAN/LAN/防火墙/DNS/QoS 配置",
    "5.升级与恢复": "sysupgrade/恢复出厂",
    "6.包管理与生态": "opkg/feed/版本",
}

def fm(p):
    t = open(p, encoding="utf-8").read(); d = {}
    if t.startswith("---\n"):
        e = t.find("\n---\n", 4)
        if e != -1:
            for line in t[4:e].splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1); d[k.strip()] = v.strip().strip('"')
            t = t[e+5:]
    return d, t

def one_line(t):
    for line in t.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ">", "|", "-", "*", "```", "!", "[")):
            continue
        s = re.sub(r"[`*_\[\]()]", "", s)
        return s[:60] + ("…" if len(s) > 60 else "")
    return ""

def sub_rows(root):
    rows = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "00-总览.md")
        if os.path.isdir(os.path.join(root, d)) and os.path.exists(p):
            rows.append(f"| [{d}]({d}/00-总览.md) | {DESC.get(d,'')} |")
    return rows

def note_rows(root):
    rows = []
    for f in sorted(os.listdir(root)):
        if not f.endswith(".md") or f == "00-总览.md":
            continue
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        d, t = fm(p)
        rows.append(f"| [{d.get('title', f[:-3])}]({f}) | {d.get('layer','')} | {d.get('status','')} | {one_line(t)} |")
    return rows

def main():
    changed = 0
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        hub = os.path.join(root, "00-总览.md")
        if not os.path.exists(hub):
            continue
        rel = os.path.relpath(root, ROOT).replace(os.sep, "/")
        lines = open(hub, encoding="utf-8").read().splitlines()
        idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
        if not idx:
            continue
        pre = lines[:idx[0]]
        secs = []
        for k, i in enumerate(idx):
            end = idx[k+1] if k+1 < len(idx) else len(lines)
            secs.append((lines[i], lines[i+1:end]))
        new = []
        for name, body in secs:
            if name == "## 子主题":
                if rel in MANUAL:
                    continue
                rows = sub_rows(root)
                new.append((name, ["", "| 子主题 | 说明 |", "|---|---|"] + rows + [""]))
            elif name == "## 笔记":
                rows = note_rows(root)
                new.append((name, ["", "| 笔记 | 层 | 状态 | 一句话 |", "|---|---|---|---|"] + rows + [""]))
            else:
                new.append((name, body))
        out = pre[:]
        for name, body in new:
            out.append(name); out.extend(body)
        text = "\n".join(out).rstrip() + "\n"
        if text != open(hub, encoding="utf-8").read():
            open(hub, "w", encoding="utf-8").write(text); changed += 1
    print("hubs rebuilt:", changed)

if __name__ == "__main__":
    main()
