#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复相对链接/图片：按 basename、规范化名、路径后缀匹配重写。"""
import os
import re
import sys
from urllib.parse import unquote, quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", "assets", "99-归档", "__pycache__"}

def norm(s):
    s = unquote(s).lower()
    s = re.sub(r"\.md$", "", s)
    s = re.sub(r"^[\d\.\-\s_]+", "", s)
    s = re.sub(r"[\s_\-\.&（）()\[\]]+", "", s)
    return s


def main():
    all_files = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in fs:
            all_files.append(os.path.relpath(os.path.join(root, f), ROOT).replace(os.sep, "/"))

    by_base, by_norm = {}, {}
    for p in all_files:
        b = os.path.basename(p)
        by_base.setdefault(b, []).append(p)
        by_norm.setdefault(norm(b), []).append(p)

    changed = 0
    unresolved = []

    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in sorted(fs):
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            text = open(p, encoding="utf-8").read()
            orig = text

            def resolve(raw):
                full = unquote(raw)
                # 先试完整路径（处理含 # 的文件名）
                for cand in (full, full.split("#")[0]):
                    tp = os.path.normpath(os.path.join(root, cand))
                    if os.path.exists(tp):
                        return os.path.relpath(tp, root).replace(os.sep, "/"), ""
                base = os.path.basename(full)
                key = norm(base)
                # 别名
                # 精确 basename
                cands = by_base.get(base, [])
                if len(cands) == 1:
                    return os.path.relpath(os.path.join(ROOT, cands[0]), root).replace(os.sep, "/"), ""
                # 规范化 basename
                cands = by_norm.get(key, [])
                if len(cands) == 1:
                    return os.path.relpath(os.path.join(ROOT, cands[0]), root).replace(os.sep, "/"), ""
                # 唯一包含匹配（用于 (未完) 之类）
                cands = [x for k, v in by_norm.items() if key and (key in k or k in key) for x in v]
                if len(cands) == 1:
                    return os.path.relpath(os.path.join(ROOT, cands[0]), root).replace(os.sep, "/"), ""
                # 路径后缀匹配
                tail = "/".join(full.split("/")[-2:])
                cands = [x for x in all_files if x.endswith(tail)]
                if len(cands) == 1:
                    return os.path.relpath(os.path.join(ROOT, cands[0]), root).replace(os.sep, "/"), ""
                return None, full

            def repl(m):
                nonlocal changed
                bang, label, raw = m.group(1), m.group(2), m.group(3).strip()
                if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
                    return m.group(0)
                new, miss = resolve(raw)
                if new is None:
                    unresolved.append((rel, raw))
                    return m.group(0)
                # 保留 anchor（仅当原始用 # 且不是文件名的一部分）
                anchor = ""
                if "#" in raw and not os.path.exists(os.path.join(root, unquote(raw))):
                    anchor = "#" + raw.split("#", 1)[1]
                if new != raw.split("#")[0]:
                    changed += 1
                return f"{bang}[{label}]({quote(new, safe='/')}{anchor})"

            text = re.sub(r"(!?)\[([^\]]*)\]\(([^)]+)\)", repl, text)
            if text != orig:
                open(p, "w", encoding="utf-8").write(text)

    print(f"changed refs={changed} unresolved={len(unresolved)}")
    for rel, raw in unresolved[:40]:
        print("  UNRESOLVED", rel, "->", raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
