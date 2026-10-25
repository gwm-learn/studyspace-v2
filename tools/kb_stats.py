#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 0.框架/仪表盘.md：规模、分层、状态、链接、重复、孤儿笔记。"""
import hashlib
import os
import re
from collections import Counter, defaultdict
from datetime import date
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", "assets", "99-归档", "__pycache__", "项目实践", "4.源码快照"}


def walk_md():
    out = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in fs:
            if f.endswith(".md") and f != "AGENTS.md":
                out.append(os.path.join(root, f))
    return sorted(out)


def fm(p):
    t = open(p, encoding="utf-8", errors="ignore").read()
    d = {}
    if t.startswith("---\n"):
        e = t.find("\n---\n", 4)
        if e != -1:
            for line in t[4:e].splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    d[k.strip()] = v.strip().strip('"')
            t = t[e + 5 :]
    return d, t


def main():
    ps = walk_md()
    sizes = [os.path.getsize(p) for p in ps]
    clusters, layers, status, conf = Counter(), Counter(), Counter(), Counter()
    inbound = Counter()
    links = 0
    titles = {}
    for p in ps:
        d, t = fm(p)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        clusters[d.get("cluster", "?")] += 1
        layers[d.get("layer", "?")] += 1
        status[d.get("status", "?")] += 1
        conf[d.get("confidence", "?")] += 1
        titles[rel] = d.get("title", os.path.splitext(os.path.basename(p))[0])
        for m in re.finditer(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", t):
            raw = unquote(m.group(2).strip())
            if raw.startswith(("http", "mailto:", "#")):
                continue
            links += 1
            target = os.path.normpath(os.path.join(os.path.dirname(p), raw.split("#")[0]))
            inbound[os.path.relpath(target, ROOT).replace(os.sep, "/")] += 1

    # 完全重复
    hashes = defaultdict(list)
    for p in ps:
        hashes[hashlib.md5(open(p, "rb").read()).hexdigest()].append(p)
    dups = [v for v in hashes.values() if len(v) > 1]

    # 孤儿：没有入链、不是 Hub/README/导航/模板
    orphans = []
    for p in ps:
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if rel.startswith("0.框架/") or rel.endswith("00-总览.md") or rel in ("README.md", "AGENTS.md"):
            continue
        if inbound[rel] == 0:
            orphans.append(rel)

    # 路线图待补
    roadmap = os.path.join(ROOT, "0.框架", "知识框架图.md")
    pending = 0
    ready = 0
    if os.path.exists(roadmap):
        rt = open(roadmap, encoding="utf-8").read()
        pending = rt.count("⬜ 待补")
        ready = rt.count("| ✅ |")

    total = sum(sizes)
    lines = [
        "---",
        'id: "framework-dashboard"',
        'title: "仪表盘"',
        "cluster: framework",
        "layer: L1",
        "status: review",
        "confidence: high",
        "platform: []",
        "source: []",
        f"verified_on: {date.today().isoformat()}",
        'tags: ["metrics"]',
        "---",
        "",
        "# 仪表盘",
        "",
        f"> 自动生成：`python3 tools/kb_stats.py`（{date.today().isoformat()}）",
        "",
        "## 规模",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 笔记数 | {len(ps)} |",
        f"| 总字节 | {total:,} |",
        f"| 中位体量 | {sorted(sizes)[len(sizes)//2]:,} B |",
        f"| 平均体量 | {total//max(1,len(ps)):,} B |",
        f"| 相对链接 | {links} |",
        f"| 完全重复组 | {len(dups)} |",
        f"| 孤儿笔记（无入链） | {len(orphans)} |",
        "",
        "## 分层",
        "",
        "| 层 | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(layers.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 状态", "", "| 状态 | 数量 |", "|---|---:|"]
    for k, v in sorted(status.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 置信度", "", "| 置信度 | 数量 |", "|---|---:|"]
    for k, v in sorted(conf.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 主题簇", "", "| 簇 | 笔记数 |", "|---|---:|"]
    for k, v in clusters.most_common():
        lines.append(f"| {k} | {v} |")

    if dups:
        lines += ["", "## 完全重复", ""]
        for g in dups:
            lines.append("- " + " / ".join(f"`{os.path.relpath(x, ROOT)}`" for x in g))
    if orphans:
        lines += ["", "## 孤儿笔记（需挂到 Hub 或被引用）", ""]
        for o in orphans[:80]:
            lines.append(f"- `{o}`")
        if len(orphans) > 80:
            lines.append(f"- … 共 {len(orphans)} 条")
    lines += ["", "## 说明", "", "- 孤儿笔记不一定是错误（可能是新写未挂链），但应尽快处理。", "- 完全重复应为 0；近重复用 `tools/kb_dup.py` 检查。", ""]
    out = os.path.join(ROOT, "0.框架", "仪表盘.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print(f"dashboard: notes={len(ps)} dups={len(dups)} orphans={len(orphans)} ready={ready} pending={pending}")


if __name__ == "__main__":
    main()
