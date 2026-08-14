#!/usr/bin/env python3
"""Generate the single transparent clickable conceptual architecture SVG."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data/architecture/overall-architecture.json"
OUT = ROOT / "docs/generated/ignition-overall-architecture.svg"
WIDTH = 2200
HEIGHT = 1320
GROUP_W = 510
GROUP_H = 500
COL_GAP = 35
ROW_GAP = 45
LEFT = 35
TOP = 115
NODE_H = 82
NODE_GAP = 24


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def validate_spec(spec: dict) -> None:
    groups = spec.get("groups", [])
    nodes = spec.get("nodes", [])
    if not 6 <= len(groups) <= 10:
        raise ValueError(f"first-level group count outside 6-10: {len(groups)}")
    if not 20 <= len(nodes) <= 30:
        raise ValueError(f"node count outside 20-30: {len(nodes)}")
    group_ids = {group["id"] for group in groups}
    node_ids = {node["id"] for node in nodes}
    if len(node_ids) != len(nodes):
        raise ValueError("duplicate node IDs")
    if any(node.get("group") not in group_ids for node in nodes):
        raise ValueError("node references an unknown group")
    def target_exists(node: dict) -> bool:
        path = node["target"].split("#", 1)[0]
        return path == "docs/generated/ignition-overall-architecture.svg" or (ROOT / path).exists()
    if any(not node.get("target") or not target_exists(node) for node in nodes):
        missing = [node["target"] for node in nodes if not target_exists(node)]
        raise ValueError(f"missing canonical target(s): {missing[:5]}")
    if any(edge.get("source") not in node_ids or edge.get("target") not in node_ids for edge in spec.get("edges", [])):
        raise ValueError("edge references an unknown node")


def target_url(base: str, target: str) -> str:
    path, _, anchor = target.partition("#")
    encoded = "/".join(quote(part, safe="-._~") for part in ("ignition" + "/" + path).split("/"))
    suffix = f"#{anchor}" if anchor else ""
    return f"{base}/blob/main/{encoded}{suffix}"


def generate(spec: dict) -> str:
    validate_spec(spec)
    groups = {group["id"]: group for group in spec["groups"]}
    nodes_by_group = {group_id: [] for group_id in groups}
    for node in spec["nodes"]:
        nodes_by_group[node["group"]].append(node)
    positions: dict[str, tuple[int, int, int, int]] = {}
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{esc(spec['title'])}</title>",
        f"<desc id=\"desc\">{esc(spec['description'])}</desc>",
        "<style>",
        ".title{font:700 34px system-ui,-apple-system,sans-serif;fill:#0f172a}.subtitle{font:400 16px system-ui,-apple-system,sans-serif;fill:#475569}.note{font:600 13px system-ui,-apple-system,sans-serif;fill:#334155}.group-label{font:700 22px system-ui,-apple-system,sans-serif}.group-desc{font:400 14px system-ui,-apple-system,sans-serif;fill:#64748b}.node{fill:none;stroke:#94a3b8;stroke-width:2}.node-label{font:600 15px system-ui,-apple-system,sans-serif;fill:#0f172a}.edge{fill:none;stroke:#94a3b8;stroke-width:1.7;stroke-opacity:.6;marker-end:url(#arrow)}.node-link:hover .node,.node-link:focus .node{stroke:#0f172a;stroke-width:3}.node-link:focus{outline:none}",
        "</style>",
        "<defs><marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"5\" markerHeight=\"5\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#64748b\"/></marker></defs>",
        f'<text class="title" x="{LEFT}" y="48">{esc(spec["title"])}</text>',
        f'<text class="subtitle" x="{LEFT}" y="77">{esc(spec["description"])}</text>',
        f'<text class="note" x="{LEFT}" y="100">点击节点进入 canonical 资产；连线只表示仓库内导航、同步或约束关系。</text>',
    ]
    for group in spec["groups"]:
        x = LEFT + group["column"] * (GROUP_W + COL_GAP)
        y = TOP + group["row"] * (GROUP_H + ROW_GAP)
        chunks.append(f'<g aria-label="{esc(group["label"])}">')
        chunks.append(f'<rect x="{x}" y="{y}" width="{GROUP_W}" height="{GROUP_H}" rx="18" fill="none" stroke="{esc(group["color"])}" stroke-width="2.5" stroke-opacity=".8"/>')
        chunks.append(f'<text class="group-label" x="{x + 24}" y="{y + 38}" fill="{esc(group["color"])}">{esc(group["label"])}</text>')
        chunks.append(f'<text class="group-desc" x="{x + 24}" y="{y + 66}">{esc(group["description"])}</text>')
        for index, node in enumerate(nodes_by_group[group["id"]]):
            nx = x + 24
            ny = y + 95 + index * (NODE_H + NODE_GAP)
            positions[node["id"]] = (nx, ny, GROUP_W - 48, NODE_H)
            chunks.append(f'<a class="node-link" href="{esc(target_url(spec["repository_url"], node["target"]))}" xlink:href="{esc(target_url(spec["repository_url"], node["target"]))}" target="_top" aria-label="{esc(node["label"])}">')
            chunks.append(f'<rect class="node" x="{nx}" y="{ny}" width="{GROUP_W - 48}" height="{NODE_H}" rx="12"/>')
            chunks.append(f'<text class="node-label" x="{nx + 18}" y="{ny + 48}">{esc(node["label"])}</text>')
            chunks.append("</a>")
        chunks.append("</g>")
    for edge in spec["edges"]:
        sx, sy, sw, sh = positions[edge["source"]]
        tx, ty, tw, th = positions[edge["target"]]
        start_x, start_y = sx + sw / 2, sy + sh / 2
        end_x, end_y = tx + tw / 2, ty + th / 2
        mid_x = (start_x + end_x) / 2
        d = f"M {start_x:.1f} {start_y:.1f} C {mid_x:.1f} {start_y:.1f}, {mid_x:.1f} {end_y:.1f}, {end_x:.1f} {end_y:.1f}"
        chunks.append(f'<path class="edge" d="{d}" data-source="{esc(edge["source"])}" data-target="{esc(edge["target"])}"><title>{esc(edge["label"])} [{esc(edge["relation"])}]</title></path>')
    chunks.append("</svg>\n")
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    content = generate(spec)
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if args.check:
        if current != content:
            print("OVERALL_ARCHITECTURE_STALE")
            return 1
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(content, encoding="utf-8")
    print(f"OVERALL_ARCHITECTURE_OK groups={len(spec['groups'])} nodes={len(spec['nodes'])} edges={len(spec['edges'])} transparent=1 clickable=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
