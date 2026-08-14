#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anysearch 学术检索客户端（免 key，CORS 开放）。
用法：
  python3 anysearch_client.py "query" [limit]
输出 JSON 数组：[{title,url,snippet,content}, ...]
合规：本工具只返回检索线索；任何用于 088 产物的 DOI 必须再用 Crossref 验真。
"""
import sys, json, urllib.request, urllib.parse

API="https://api.anysearch.com/v1/search"
def search(query, limit=5):
    body=json.dumps({"query":query,"limit":limit}).encode()
    req=urllib.request.Request(API, data=body, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        o=json.load(r)
    if o.get("code")!=0:
        raise RuntimeError(o.get("message"))
    return o["data"]["results"]

if __name__=="__main__":
    q=" ".join(sys.argv[1:])
    if q.lower().startswith("limit="):
        # 允许 python3 anysearch_client.py "q" 5
        pass
    lim=5
    parts=q.split()
    if parts and parts[-1].isdigit():
        lim=int(parts[-1]); q=" ".join(parts[:-1])
    res=search(q, lim)
    print(json.dumps(res, ensure_ascii=False, indent=2))
