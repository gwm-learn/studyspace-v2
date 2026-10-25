#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐 Hub 中未登记的笔记/子主题（不覆盖已有内容）。"""
import os, re
from urllib.parse import unquote
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP={'.git','assets','99-归档','__pycache__','项目实践'}

def fm(p):
    t=open(p,encoding='utf-8').read(); d={}
    if t.startswith('---\n'):
        e=t.find('\n---\n',4)
        if e!=-1:
            for line in t[4:e].splitlines():
                if ': ' in line:
                    k,v=line.split(': ',1); d[k.strip()]=v.strip().strip('"')
    return d

def add_section(lines, title, header, rows):
    if not rows: return lines
    try:
        i=next(k for k,l in enumerate(lines) if l.strip()==f'## {title}')
    except StopIteration:
        lines += ['', f'## {title}', '', header, '|'+'---|'*header.count('|'), *rows, '']
        return lines
    j=i+1; last=None
    while j<len(lines) and not lines[j].startswith('## '):
        if lines[j].startswith('|'): last=j
        j+=1
    if last is None:
        lines[i+1:i+1]=['',header,'|'+'---|'*header.count('|'),*rows]
    else:
        lines[last+1:last+1]=rows
    return lines

def main():
    changed=0
    for root,dirs,fs in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in SKIP]
        hub=os.path.join(root,'00-总览.md')
        if not os.path.exists(hub): continue
        text=open(hub,encoding='utf-8').read(); lines=text.splitlines()
        existing=unquote(text)
        note_rows=[]; sub_rows=[]
        for f in sorted(fs):
            if f=='00-总览.md' or not f.endswith('.md'): continue
            if f in existing: continue
            d=fm(os.path.join(root,f))
            note_rows.append(f"| [{d.get('title',f[:-3])}]({f}) | {d.get('layer','')} | {d.get('status','')} |  |")
        for d in sorted(dirs):
            if d in ('assets','99-归档'): continue
            if os.path.exists(os.path.join(root,d,'00-总览.md')):
                if f'{d}/00-总览.md' in existing: continue
                sub_rows.append(f"| [{d}]({d}/00-总览.md) |  |")
        if not note_rows and not sub_rows: continue
        if sub_rows: lines=add_section(lines,'子主题','| 子主题 | 说明 |',sub_rows)
        if note_rows: lines=add_section(lines,'笔记','| 笔记 | 层 | 状态 | 一句话 |',note_rows)
        open(hub,'w',encoding='utf-8').write('\n'.join(lines)+'\n'); changed+=1
    print('hubs updated',changed)
if __name__=='__main__': main()
