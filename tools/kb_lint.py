#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库静态检查：frontmatter / H1 / 断链 / 图片 / 空文件 / 命名 / Hub。"""
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "assets", "99-归档", "__pycache__", "项目实践", "4.源码快照"}
REQUIRED = ["id", "title", "cluster", "layer", "status", "confidence", "tags"]
LAYERS = {"L1", "L2", "L3", "L4"}
STATUS = {"draft", "review", "verified", "deprecated", "template"}


def parse_fm(text):
    if not text.startswith("---\n"):
        return {}, text, False
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text, False
    fm = {}
    for line in text[4:end].splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, text[end + 5 :], True


def main():
    errors, warnings = [], []
    files = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(fs):
            if f.endswith(".md"):
                files.append(os.path.join(root, f))

    for p in files:
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if rel.startswith("99-归档/") or rel == "AGENTS.md":
            continue
        text = open(p, encoding="utf-8").read()
        fm, body, has = parse_fm(text)
        is_tpl = "/模板/" in "/" + rel

        # 空文件
        if len(text.strip()) == 0:
            errors.append(f"{rel}: 空文件")

        # frontmatter
        if not has:
            errors.append(f"{rel}: 缺少 frontmatter")
        elif not is_tpl:
            for k in REQUIRED:
                if k not in fm:
                    errors.append(f"{rel}: frontmatter 缺少 {k}")
            if fm.get("layer") not in LAYERS | {"template"}:
                errors.append(f"{rel}: layer 非法: {fm.get('layer')}")
            if fm.get("status") not in STATUS:
                errors.append(f"{rel}: status 非法: {fm.get('status')}")

        # H1
        h1 = re.search(r"(?m)^#\s+(.+)$", body)
        if not h1:
            errors.append(f"{rel}: 缺少 H1")
        elif not is_tpl and fm.get("title") and h1.group(1).strip() != fm["title"]:
            warnings.append(f"{rel}: H1 与 title 不一致: {h1.group(1)} != {fm['title']}")

        # 命名
        name = os.path.basename(p)
        if " " in name:
            errors.append(f"{rel}: 文件名含空格")
        if "&" in rel:
            errors.append(f"{rel}: 路径含 &")

        # 链接与图片
        for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", body):
            raw = m.group(2).strip()
            if raw.startswith(("http://", "https://", "data:")):
                continue
            found = False
            for cand in (unquote(raw), unquote(raw.split("#")[0])):
                if not cand:
                    continue
                tp = os.path.normpath(os.path.join(os.path.dirname(p), cand))
                if os.path.exists(tp):
                    found = True
                    break
            if not found:
                errors.append(f"{rel}: 图片失效 -> {raw}")

        for m in re.finditer(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", body):
            raw = m.group(2).strip()
            if raw.startswith(("http://", "https://", "mailto:", "#")):
                continue
            found = False
            for cand in (unquote(raw), unquote(raw.split("#")[0])):
                if not cand:
                    continue
                tp = os.path.normpath(os.path.join(os.path.dirname(p), cand))
                if os.path.exists(tp):
                    found = True
                    break
            if not found:
                errors.append(f"{rel}: 链接失效 -> {raw}")

    # Hub 覆盖
    dirs_with_md = set()
    dirs_with_hub = set()
    for p in files:
        d = os.path.dirname(p)
        dirs_with_md.add(d)
        if os.path.basename(p) == "00-总览.md":
            dirs_with_hub.add(d)
    for d in sorted(dirs_with_md):
        rel = os.path.relpath(d, ROOT).replace(os.sep, "/")
        if rel == "." or "99-归档" in rel or rel.endswith("模板"):
            continue
        if d not in dirs_with_hub:
            errors.append(f"{rel}: 目录缺少 00-总览.md")

    print(f"files={len(files)} errors={len(errors)} warnings={len(warnings)}")
    for e in errors:
        print("  ERROR", e)
    for w in warnings[:30]:
        print("  WARN ", w)
    if len(warnings) > 30:
        print(f"  ... {len(warnings)-30} more warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
