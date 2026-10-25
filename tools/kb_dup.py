#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重复检测：md5 完全重复 + 字符 3-gram Jaccard 近重复。"""
import hashlib
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {".git", "assets", "99-归档", "__pycache__", "项目实践", "4.源码快照"}


def files():
    out = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in fs:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return out


def body(p):
    t = open(p, encoding="utf-8", errors="ignore").read()
    if t.startswith("---\n"):
        e = t.find("\n---\n", 4)
        if e != -1:
            t = t[e + 5 :]
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"[#>*`|\-\[\]()]", "", t)
    return re.sub(r"\s+", "", t)


def shingles(s, n=3):
    return {s[i : i + n] for i in range(0, max(0, len(s) - n + 1))}


def main():
    ps = files()
    exact = defaultdict(list)
    for p in ps:
        exact[hashlib.md5(open(p, "rb").read()).hexdigest()].append(p)
    dups = {k: v for k, v in exact.items() if len(v) > 1}

    near = []
    bodies = {p: body(p) for p in ps}
    sh = {p: shingles(b) for p, b in bodies.items() if len(b) > 1500}
    keys = sorted(sh)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            sa, sb = sh[a], sh[b]
            if not sa or not sb:
                continue
            inter = len(sa & sb)
            j = inter / len(sa | sb)
            if j >= 0.75:
                near.append((j, a, b))

    print(f"files={len(ps)} exact_groups={len(dups)} near_pairs={len(near)}")
    for k, v in dups.items():
        print("  EXACT", [os.path.relpath(x, ROOT) for x in v])
    for j, a, b in sorted(near, reverse=True)[:20]:
        print(f"  NEAR {j:.2f} {os.path.relpath(a, ROOT)} <-> {os.path.relpath(b, ROOT)}")
    return 1 if dups or near else 0


if __name__ == "__main__":
    sys.exit(main())
