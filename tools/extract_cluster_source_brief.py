#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract a faithful source brief for selected article clusters.

Reproducible (stdlib only, no network). Reads the governed card corpus via the
same parser used by build_corpus_relation_graph.py, then for each requested
cluster prints the key fields of every member card so editorial articles can be
written without fabricating claims.

Usage:
    python3 tools/extract_cluster_source_brief.py [CIDs...]
Defaults to the 5 task-104 pilot clusters: C000 C001 C004 C005 C006.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location(
    "bcrg", os.path.join(ROOT, "tools", "build_corpus_relation_graph.py"))
BCRG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BCRG)

PILOT_DEFAULT = ["C000", "C001", "C004", "C005", "C006"]
FIELDS = [
    ("asset_type", "身份/来源·类型"),
    ("status", "当前状态"),
    ("topics", "主题"),
    ("current_result", "当前结果"),
    ("ceiling", "假设与表述上限"),
    ("not_established", "未建立"),
    ("dependencies", "依赖"),
    ("reverse_dependencies", "反向依赖/被引用"),
    ("related", "相关文章/资产"),
    ("evidence_sources", "来源与证据"),
    ("primary_source", "首要来源"),
    ("maturity_m", "数学成熟度"),
    ("maturity_e", "外部证据成熟度"),
    ("last_adjudicated", "最近裁决"),
    ("next_step", "下一步"),
    ("why", "为什么产生"),
]


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "—"
    return str(v)


def main():
    cids = sys.argv[1:] or PILOT_DEFAULT
    nodes, by_lower = BCRG.load_cards(ROOT)
    card_by_id = {n["id"]: n for n in nodes}
    cl = json.load(open(os.path.join(
        ROOT, "analysis", "corpus-relation", "article_cluster_candidates.json"),
        encoding="utf-8"))
    clusters = {c["id"]: c for c in cl["clusters"]}
    out_dir = os.path.join(ROOT, "analysis", "corpus-relation",
                           "cluster_source_briefs")
    os.makedirs(out_dir, exist_ok=True)

    for cid in cids:
        c = clusters.get(cid)
        if not c:
            print("WARN: no cluster %s" % cid, file=sys.stderr)
            continue
        lines = []
        lines.append("# 源资产简报 %s（%s）" % (cid, c["disposition"]))
        lines.append("")
        lines.append("> 中心问题候选：%s" % c.get("proposed_central_question", ""))
        lines.append("> 主导主题：%s（比例 %.2f）｜域数 %d｜规模 %d"
                     % (c.get("dominant_topic"), c.get("dominant_ratio", 0),
                        c.get("distinct_domains", 0), c.get("size", 0)))
        edge_types = c.get("edge_types") or []
        if edge_types:
            lines.append("> 簇内边类型：%s" % ", ".join(edge_types))
        lines.append("")
        members = sorted(c["members"], key=lambda m: m["id"])
        for m in members:
            mid = m["id"]
            node = card_by_id.get(mid) or by_lower.get(mid.lower())
            lines.append("## %s — %s" % (mid, m.get("title", "")))
            if node is None:
                lines.append("（未在主卡语料中匹配，仅簇元数据：asset_type=%s, status=%s, topics=%s）"
                             % (m.get("asset_type"), m.get("status"),
                                ", ".join(m.get("topics", []))))
                lines.append("")
                continue
            for key, label in FIELDS:
                lines.append("- **%s**：%s" % (label, fmt(node.get(key))))
            lines.append("")
        out_path = os.path.join(out_dir, "%s.md" % cid)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("wrote %s (%d cards)" % (out_path, len(members)))

    # also write a compact index of all requested clusters
    idx = os.path.join(out_dir, "INDEX.md")
    with open(idx, "w", encoding="utf-8") as fh:
        fh.write("# 试点簇源资产简报索引\n\n")
        for cid in cids:
            c = clusters.get(cid)
            if not c:
                continue
            fh.write("- [%s](./%s.md) — %s（n=%d, %s）\n"
                     % (cid, cid, c.get("proposed_central_question", ""),
                        c.get("size", 0), c.get("dominant_topic")))
    print("wrote %s" % idx)


if __name__ == "__main__":
    main()
