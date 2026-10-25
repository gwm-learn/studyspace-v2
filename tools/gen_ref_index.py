#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 90.参考资料/00-索引.md（只基于当前目录，不引用任何外部路径）。"""
import os, re
from urllib.parse import quote
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF=os.path.join(ROOT,'90.参考资料')
rows=[]
for root,dirs,fs in os.walk(REF):
    dirs[:]=[d for d in dirs if d not in ('assets','__pycache__','4.源码快照')]
    for f in fs:
        if f in ('00-索引.md','00-总览.md') or f.endswith('.md'): continue
        if os.path.splitext(f)[1].lower() not in ('.pdf','.doc','.docx','.ppt','.pptx','.xls','.xlsx'): continue
        p=os.path.join(root,f)
        rel=os.path.relpath(p,REF).replace(os.sep,'/')
        cat=rel.split('/')[0] if '/' in rel else '其他'
        size=os.path.getsize(p)
        rows.append((cat,rel,size))
rows.sort(key=lambda x:(x[0],x[1]))
lines=['---','id: "ref-index"','title: "参考资料索引"','cluster: ref','layer: L1','status: review','confidence: high','platform: []','source: []','tags: ["reference"]','---','','# 参考资料索引','',f'> 共 {len(rows)} 份，按分类归档。点击文件名打开。','', '| 分类 | 文件 | 大小 |','|---|---|---:|']
for cat,rel,size in rows:
    s=f"{size/1024/1024:.1f} MB" if size>1024*1024 else f"{size/1024:.0f} KB"
    lines.append(f"| {cat} | [{os.path.basename(rel)}]({quote(rel,safe='/')}) | {s} |")
open(os.path.join(REF,'00-索引.md'),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('refs',len(rows))
