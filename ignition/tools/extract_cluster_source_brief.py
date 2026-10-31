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
import argparse
import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def assert_local_source_paths(root):
    """Reject symlinked input paths so a read-only tool stays inside its checkout."""
    root = os.fspath(root)
    if os.path.islink(root):
        raise ValueError("checkout root must not be a symlink")
    root = os.path.realpath(root)
    relative_paths = [
        "KNOWLEDGE/cards",
        "analysis/corpus-relation/article_cluster_candidates.json",
        "tools/build_corpus_relation_graph.py",
    ]
    for relative in relative_paths:
        current = root
        for part in relative.split(os.sep):
            current = os.path.join(current, part)
            if os.path.islink(current):
                raise ValueError("source path contains a symlink: " + relative)
        if os.path.commonpath([root, os.path.realpath(current)]) != root:
            raise ValueError("source path escapes the checkout: " + relative)
    cards_dir = os.path.join(root, "KNOWLEDGE", "cards")
    for filename in os.listdir(cards_dir):
        if filename.startswith("part-") and filename.endswith(".md"):
            path = os.path.join(cards_dir, filename)
            if os.path.islink(path) or os.path.commonpath([root, os.path.realpath(path)]) != root:
                raise ValueError("asset-card source escapes the checkout: " + filename)


def load_card_parser(root):
    """Load the source-pinned parser only after validating its path boundary."""
    parser_path = os.path.join(os.fspath(root), "tools", "build_corpus_relation_graph.py")
    spec = importlib.util.spec_from_file_location("bcrg", parser_path)
    if spec is None or spec.loader is None:
        raise ValueError("asset-card parser cannot be loaded")
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    return parser


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "—"
    return str(v)


def load_source_brief_inputs(root=ROOT):
    """Read the governed card corpus and cluster snapshot without writing."""
    assert_local_source_paths(root)
    parser = load_card_parser(root)
    nodes, by_lower = parser.load_cards(root)
    card_by_id = {node["id"]: node for node in nodes}
    cluster_path = os.path.join(root, "analysis", "corpus-relation", "article_cluster_candidates.json")
    with open(cluster_path, encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict) or not isinstance(document.get("clusters"), list):
        raise ValueError("cluster candidate source must contain a clusters array")
    clusters = {cluster["id"]: cluster for cluster in document["clusters"] if isinstance(cluster, dict) and isinstance(cluster.get("id"), str)}
    return card_by_id, by_lower, clusters


def build_brief_text(cid, cluster, card_by_id, by_lower):
    """Render one cluster as a deterministic, read-only Markdown brief."""
    lines = []
    lines.append("# 源资产简报 %s（%s）" % (cid, cluster["disposition"]))
    lines.append("")
    lines.append("> 中心问题候选：%s" % cluster.get("proposed_central_question", ""))
    lines.append("> 主导主题：%s（比例 %.2f）｜域数 %d｜规模 %d"
                 % (cluster.get("dominant_topic"), cluster.get("dominant_ratio", 0),
                    cluster.get("distinct_domains", 0), cluster.get("size", 0)))
    edge_types = cluster.get("edge_types") or []
    if edge_types:
        lines.append("> 簇内边类型：%s" % ", ".join(edge_types))
    lines.append("")
    members = sorted(cluster["members"], key=lambda member: member["id"])
    for member in members:
        member_id = member["id"]
        node = card_by_id.get(member_id) or by_lower.get(member_id.lower())
        lines.append("## %s — %s" % (member_id, member.get("title", "")))
        if node is None:
            lines.append("（未在主卡语料中匹配，仅簇元数据：asset_type=%s, status=%s, topics=%s）"
                         % (member.get("asset_type"), member.get("status"),
                            ", ".join(member.get("topics", []))))
            lines.append("")
            continue
        for key, label in FIELDS:
            lines.append("- **%s**：%s" % (label, fmt(node.get(key))))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_briefs(cids, root=ROOT):
    """Return briefs for known cluster IDs, rejecting the whole request on a gap."""
    if not isinstance(cids, (list, tuple)) or not cids or any(not isinstance(cid, str) or not cid for cid in cids):
        raise ValueError("at least one nonblank cluster ID is required")
    if len(cids) != len(set(cids)):
        raise ValueError("cluster IDs must be unique")
    card_by_id, by_lower, clusters = load_source_brief_inputs(root)
    unknown = sorted(set(cids) - set(clusters))
    if unknown:
        raise ValueError("unknown cluster ID(s): " + ", ".join(unknown))
    return "\n---\n\n".join(build_brief_text(cid, clusters[cid], card_by_id, by_lower) for cid in cids)


def render_receipt(cids, root=ROOT):
    """Return deterministic source hashes and brief hashes for a read-only run."""
    if not isinstance(cids, (list, tuple)) or not cids or any(not isinstance(cid, str) or not cid for cid in cids):
        raise ValueError("at least one nonblank cluster ID is required")
    if len(cids) != len(set(cids)):
        raise ValueError("cluster IDs must be unique")
    root = os.fspath(root)
    card_by_id, by_lower, clusters = load_source_brief_inputs(root)
    unknown = sorted(set(cids) - set(clusters))
    if unknown:
        raise ValueError("unknown cluster ID(s): " + ", ".join(unknown))
    cluster_path = os.path.join(root, "analysis", "corpus-relation", "article_cluster_candidates.json")
    with open(cluster_path, "rb") as handle:
        cluster_sha256 = hashlib.sha256(handle.read()).hexdigest()
    cards_dir = os.path.join(root, "KNOWLEDGE", "cards")
    card_hashes = []
    for filename in sorted(os.listdir(cards_dir)) if os.path.isdir(cards_dir) else []:
        if filename.startswith("part-") and filename.endswith(".md"):
            path = os.path.join(cards_dir, filename)
            with open(path, "rb") as handle:
                card_hashes.append({"path": "KNOWLEDGE/cards/" + filename, "sha256": hashlib.sha256(handle.read()).hexdigest()})
    corpus_payload = json.dumps(card_hashes, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    parser_path = os.path.join(root, "tools", "build_corpus_relation_graph.py")
    with open(parser_path, "rb") as handle:
        parser_bytes = handle.read()
    parser_blob_sha1 = hashlib.sha1(b"blob " + str(len(parser_bytes)).encode("ascii") + b"\0" + parser_bytes).hexdigest()
    briefs = []
    for cid in cids:
        markdown = build_brief_text(cid, clusters[cid], card_by_id, by_lower)
        briefs.append({
            "cluster_id": cid,
            "disposition": clusters[cid]["disposition"],
            "member_count": len(clusters[cid]["members"]),
            "markdown": markdown,
            "output_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        })
    document = {
        "schema_version": "cluster-source-brief-output-r0",
        "status": "REPOSITORY_SNAPSHOT_PROJECTION",
        "source_refs": {
            "cluster_snapshot": {"path": "ignition/analysis/corpus-relation/article_cluster_candidates.json", "sha256": cluster_sha256},
            "knowledge_cards": {"path": "ignition/KNOWLEDGE/cards/", "tree_sha256": hashlib.sha256(corpus_payload).hexdigest(), "file_count": len(card_hashes)},
            "parser": {"path": "ignition/tools/build_corpus_relation_graph.py", "git_blob_sha1": parser_blob_sha1},
        },
        "briefs": briefs,
        "claim_ceiling": "Snapshot-derived source-card projection only; no scientific truth, proof, external evidence, or publication acceptance is inferred.",
    }
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    document["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract source-backed briefs from declared article clusters.")
    parser.add_argument("cids", nargs="*", help="cluster IDs; defaults to the five Task104 pilot IDs")
    parser.add_argument("--stdout", action="store_true", help="print only; do not create or overwrite any file")
    parser.add_argument("--json", action="store_true", help="emit briefs with source and output digests; requires --stdout")
    args = parser.parse_args(argv)
    cids = args.cids or PILOT_DEFAULT
    if args.json and not args.stdout:
        parser.error("--json requires --stdout")
    if args.stdout:
        try:
            if args.json:
                sys.stdout.write(json.dumps(render_receipt(cids), ensure_ascii=False, indent=2) + "\n")
            else:
                sys.stdout.write(render_briefs(cids))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print("SOURCE_BRIEF_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
            return 2
        return 0

    # Preserve the historical file-writing mode for existing callers. The new
    # toolbox entrypoint uses --stdout and never reaches this branch.
    card_by_id, by_lower, clusters = load_source_brief_inputs(ROOT)
    unknown = sorted(set(cids) - set(clusters))
    if unknown:
        print("SOURCE_BRIEF_NOT_AVAILABLE: unknown cluster ID(s): %s" % ", ".join(unknown), file=sys.stderr)
        return 2
    out_dir = os.path.join(ROOT, "analysis", "corpus-relation",
                           "cluster_source_briefs")
    os.makedirs(out_dir, exist_ok=True)

    for cid in cids:
        c = clusters.get(cid)
        members = sorted(c["members"], key=lambda m: m["id"])
        out_path = os.path.join(out_dir, "%s.md" % cid)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(build_brief_text(cid, c, card_by_id, by_lower))
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
    raise SystemExit(main())
