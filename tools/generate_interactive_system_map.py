#!/usr/bin/env python3
"""Generate the repository-native interactive system map from its JSON spec."""

from __future__ import annotations

import argparse
import io
import json
import re
import textwrap
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "data/architecture/interactive-system-map.json"
DEFAULT_OUTPUT = ROOT / "docs/generated/ignition-system-map.svg"
COMPONENT_REGISTRY = ROOT / "data/operations/project-components.json"
PROPAGATION_TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
LAYOUT_OVERLAY = ROOT / "data/architecture/interactive-system-map-layout.json"
SVG_NS = "http://www.w3.org/2000/svg"

ET.register_namespace("", SVG_NS)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_spec(path: Path = DEFAULT_SPEC) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_projection(
    components_doc: dict | None = None,
    topology_doc: dict | None = None,
    layout_doc: dict | None = None,
) -> dict:
    """Derive the map projection; no node identity or relation is authored here."""
    components_doc = components_doc or load_json(COMPONENT_REGISTRY)
    topology_doc = topology_doc or load_json(PROPAGATION_TOPOLOGY)
    layout_doc = layout_doc or load_json(LAYOUT_OVERLAY)
    components = {item["component_id"]: item for item in components_doc["components"]}
    visible = {key for key, item in components.items() if item["map_projection"]["visible"]}
    ordered_ids: list[str] = []
    for group in layout_doc["groups"]:
        group_id = group["id"]
        for component_id in layout_doc["node_order"].get(group_id, []):
            require(component_id in components, f"layout references unknown component: {component_id}")
            require(component_id in visible, f"layout includes hidden component: {component_id}")
            require(components[component_id]["map_projection"]["group"] == group_id, f"layout group disagrees with registry for {component_id}")
            ordered_ids.append(component_id)
    require(len(ordered_ids) == len(set(ordered_ids)), "layout repeats a component")
    require(set(ordered_ids) == visible, f"layout visibility mismatch: missing={sorted(visible-set(ordered_ids))} extra={sorted(set(ordered_ids)-visible)}")
    for component_id, component in components.items():
        projection = component["map_projection"]
        if not projection["visible"]:
            require(projection.get("represented_by") in visible, f"hidden component {component_id} lacks a visible representative")
            require(projection.get("no_change_reason", "").strip(), f"hidden component {component_id} lacks NO_CHANGE reason")

    nodes = [
        {
            "id": component_id,
            "label": components[component_id]["label"],
            "group": components[component_id]["map_projection"]["group"],
            "target": components[component_id]["canonical_target"],
            "description": components[component_id]["description"],
            "lifecycle_status": components[component_id]["lifecycle"]["status"],
        }
        for component_id in ordered_ids
    ]
    edges = [
        {
            "id": relation["relation_id"],
            "source": relation["source"],
            "target": relation["target"],
            "label": relation["label"],
            "relation_class": relation["relation_class"],
            "relation_domain": relation["relation_domain"],
        }
        for relation in topology_doc["relations"]
        if relation["map_visible"]
    ]
    require(all(edge["source"] in visible and edge["target"] in visible for edge in edges), "visible map relation references hidden component")
    return {
        "schema_version": "2.0.0",
        "map_version": layout_doc["current_map_version"],
        "historical_map_version": layout_doc["historical_map_version"],
        "projection_status": "CURRENT_DERIVED_PROJECTION",
        "title": layout_doc["title"],
        "subtitle": layout_doc["subtitle"],
        "repository_url": layout_doc["repository_url"],
        "projection_authority": {
            "component_registry": "data/operations/project-components.json",
            "propagation_topology": "data/operations/change-propagation-topology.json",
            "layout_overlay": "data/architecture/interactive-system-map-layout.json",
            "component_registry_version": components_doc["registry_version"],
            "topology_version": topology_doc["topology_version"],
            "layout_version": layout_doc["layout_version"],
        },
        "layout": layout_doc["geometry"],
        "groups": layout_doc["groups"],
        "nodes": nodes,
        "edges": edges,
    }


def serialized_projection(spec: dict) -> bytes:
    return (json.dumps(spec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def target_file(target: str) -> str:
    return target.split("#", 1)[0]


def target_url(repository_url: str, target: str) -> str:
    path, marker, fragment = target.partition("#")
    encoded_path = urllib.parse.quote(path, safe="/-._~")
    url = f"{repository_url}/blob/main/{encoded_path}"
    if marker:
        url += "#" + urllib.parse.quote(fragment, safe="-_")
    return url


def validate_spec(spec: dict, root: Path = ROOT) -> None:
    require(spec.get("schema_version") in {"1.0.0", "2.0.0"}, "unsupported system-map schema_version")
    if spec.get("schema_version") == "2.0.0":
        require(spec.get("projection_status") == "CURRENT_DERIVED_PROJECTION", "derived map lacks Current projection status")
        authority = spec.get("projection_authority", {})
        require(authority.get("component_registry") == "data/operations/project-components.json", "map projection has wrong component authority")
        require(authority.get("propagation_topology") == "data/operations/change-propagation-topology.json", "map projection has wrong topology authority")
        require(authority.get("layout_overlay") == "data/architecture/interactive-system-map-layout.json", "map projection has wrong layout authority")
    repository_url = spec.get("repository_url", "")
    require(repository_url.startswith("https://github.com/"), "repository_url must be a GitHub HTTPS URL")
    forbidden = ("/Users/", "/tmp/", "file://")
    raw = json.dumps(spec, ensure_ascii=False)
    require(not any(item in raw for item in forbidden), "system-map spec leaks a local or temporary path")

    groups = spec.get("groups")
    nodes = spec.get("nodes")
    edges = spec.get("edges")
    require(isinstance(groups, list) and groups, "system-map spec requires groups")
    require(isinstance(nodes, list) and nodes, "system-map spec requires nodes")
    require(isinstance(edges, list), "system-map spec requires edges")

    group_ids = [group.get("id") for group in groups]
    require(len(group_ids) == len(set(group_ids)), "duplicate system-map group id")
    require(all(group_ids), "every system-map group requires an id")
    node_ids = [node.get("id") for node in nodes]
    require(len(node_ids) == len(set(node_ids)), "duplicate system-map node id")
    require(all(node_ids), "every system-map node requires an id")

    for node in nodes:
        for field in ("id", "label", "group", "target", "description"):
            require(isinstance(node.get(field), str) and node[field].strip(), f"node {node.get('id')} lacks {field}")
        require(node["group"] in group_ids, f"node {node['id']} references unknown group {node['group']}")
        path = root / target_file(node["target"])
        require(path.is_file(), f"node {node['id']} target does not exist: {node['target']}")
        if "#" in node["target"]:
            fragment = node["target"].split("#", 1)[1]
            heading_pattern = rf"^#+\s+{re.escape(fragment)}\s*$"
            require(re.search(heading_pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE) is not None, f"node {node['id']} target anchor does not exist: {node['target']}")

    layer_nodes = [node["id"] for node in nodes if node["group"] == "layers"]
    require(layer_nodes == [f"l{index}" for index in range(7)], "layer group must contain exactly ordered L0-L6")
    require(not any(node["id"] == "l7" for node in nodes), "system map must not add L7")

    node_id_set = set(node_ids)
    for edge in edges:
        require(edge.get("source") in node_id_set, f"edge has unknown source: {edge}")
        require(edge.get("target") in node_id_set, f"edge has unknown target: {edge}")
        require(isinstance(edge.get("label"), str) and edge["label"], f"edge lacks label: {edge}")
        if spec.get("schema_version") == "2.0.0":
            require(edge.get("relation_domain") in {"substantive_causal_candidate", "repository_dependency", "synchronization_obligation"}, f"edge lacks typed relation domain: {edge}")


def wrap_label(label: str, width: int = 24) -> list[str]:
    if " / " in label:
        left, right = label.split(" / ", 1)
        return [left + " /", right]
    lines = textwrap.wrap(label, width=width, break_long_words=False, break_on_hyphens=False)
    return lines[:2] or [label]


def svg_element(tag: str, attributes: dict[str, str] | None = None, text: str | None = None) -> ET.Element:
    element = ET.Element(f"{{{SVG_NS}}}{tag}", attributes or {})
    if text is not None:
        element.text = text
    return element


def render_svg(spec: dict, root_path: Path = ROOT) -> bytes:
    validate_spec(spec, root_path)
    layout = spec["layout"]
    columns = int(layout["columns"])
    group_width = int(layout["group_width"])
    outer = int(layout["outer_padding"])
    gap = int(layout["group_gap"])
    header_height = int(layout["group_header_height"])
    node_height = int(layout["node_height"])
    node_gap = int(layout["node_gap"])
    top_offset = 122

    nodes_by_group: dict[str, list[dict]] = {group["id"]: [] for group in spec["groups"]}
    for node in spec["nodes"]:
        nodes_by_group[node["group"]].append(node)

    group_heights = {
        group_id: header_height + len(items) * (node_height + node_gap) + outer
        for group_id, items in nodes_by_group.items()
    }
    rows = max(int(group["row"]) for group in spec["groups"]) + 1
    row_heights = [
        max(group_heights[group["id"]] for group in spec["groups"] if int(group["row"]) == row)
        for row in range(rows)
    ]
    row_y: list[int] = []
    cursor = top_offset
    for height in row_heights:
        row_y.append(cursor)
        cursor += height + gap

    width = outer * 2 + columns * group_width + (columns - 1) * gap
    height = cursor - gap + outer
    root = svg_element(
        "svg",
        {
            "viewBox": f"0 0 {width} {height}",
            "width": str(width),
            "height": str(height),
            "role": "img",
            "aria-labelledby": "map-title map-description",
        },
    )
    root.append(svg_element("title", {"id": "map-title"}, spec["title"]))
    root.append(svg_element("desc", {"id": "map-description"}, spec["subtitle"]))

    style = svg_element("style")
    style.text = """
      .map-bg{fill:#f8fafc}.map-title{font:700 30px system-ui,sans-serif;fill:#0f172a}
      .map-subtitle{font:400 15px system-ui,sans-serif;fill:#475569}
      .cluster{fill:#fff;stroke-width:2}.cluster-title{font:700 20px system-ui,sans-serif}
      .cluster-desc{font:400 13px system-ui,sans-serif;fill:#64748b}
      .node{fill:#fff;stroke:#cbd5e1;stroke-width:1.5;filter:url(#shadow)}
      .node-label{font:600 14px system-ui,sans-serif;fill:#0f172a;pointer-events:none}
      .node-link:hover .node,.node-link:focus .node{stroke-width:3;stroke:#0f172a}
      .edge{fill:none;stroke:#64748b;stroke-width:1.5;stroke-opacity:.34;marker-end:url(#arrow)}
      .boundary-note{font:600 12px system-ui,sans-serif;fill:#334155}
    """
    root.append(style)
    defs = svg_element("defs")
    marker = svg_element("marker", {"id": "arrow", "viewBox": "0 0 10 10", "refX": "9", "refY": "5", "markerWidth": "5", "markerHeight": "5", "orient": "auto-start-reverse"})
    marker.append(svg_element("path", {"d": "M 0 0 L 10 5 L 0 10 z", "fill": "#64748b", "fill-opacity": ".55"}))
    defs.append(marker)
    shadow = svg_element("filter", {"id": "shadow", "x": "-10%", "y": "-20%", "width": "120%", "height": "150%"})
    shadow.append(svg_element("feDropShadow", {"dx": "0", "dy": "2", "stdDeviation": "2", "flood-color": "#0f172a", "flood-opacity": ".10"}))
    defs.append(shadow)
    root.append(defs)
    root.append(svg_element("rect", {"class": "map-bg", "x": "0", "y": "0", "width": str(width), "height": str(height)}))
    root.append(svg_element("text", {"class": "map-title", "x": str(outer), "y": "42"}, spec["title"]))
    root.append(svg_element("text", {"class": "map-subtitle", "x": str(outer), "y": "72"}, spec["subtitle"]))
    root.append(svg_element("text", {"class": "boundary-note", "x": str(outer), "y": "98"}, "点击任一构件打开 canonical 目标；视觉邻近与连线不自动表示因果、严格同构或理论完备。"))

    group_positions: dict[str, tuple[int, int, int]] = {}
    node_positions: dict[str, tuple[float, float, float, float, str]] = {}
    group_lookup = {group["id"]: group for group in spec["groups"]}
    for group in spec["groups"]:
        x = outer + int(group["column"]) * (group_width + gap)
        y = row_y[int(group["row"])]
        group_positions[group["id"]] = (x, y, group_heights[group["id"]])
        root.append(svg_element("rect", {"class": "cluster", "x": str(x), "y": str(y), "width": str(group_width), "height": str(group_heights[group["id"]]), "rx": "16", "stroke": group["color"]}))
        root.append(svg_element("text", {"class": "cluster-title", "x": str(x + 22), "y": str(y + 32), "fill": group["color"]}, group["label"]))
        root.append(svg_element("text", {"class": "cluster-desc", "x": str(x + 22), "y": str(y + 58)}, group["description"]))
        for index, node in enumerate(nodes_by_group[group["id"]]):
            node_x = x + 22
            node_y = y + header_height + index * (node_height + node_gap)
            node_positions[node["id"]] = (node_x, node_y, group_width - 44, node_height, group["id"])

    edge_layer = svg_element("g", {"aria-label": "system relations"})
    for edge in spec["edges"]:
        sx, sy, sw, sh, source_group = node_positions[edge["source"]]
        tx, ty, tw, th, target_group = node_positions[edge["target"]]
        if source_group == target_group:
            start_x, start_y = sx + sw / 2, sy + sh
            end_x, end_y = tx + tw / 2, ty
            mid_y = (start_y + end_y) / 2
            d = f"M {start_x:.1f} {start_y:.1f} C {start_x:.1f} {mid_y:.1f}, {end_x:.1f} {mid_y:.1f}, {end_x:.1f} {end_y:.1f}"
        else:
            start_x, start_y = sx + sw / 2, sy + sh / 2
            end_x, end_y = tx + tw / 2, ty + th / 2
            mid_x = (start_x + end_x) / 2
            d = f"M {start_x:.1f} {start_y:.1f} C {mid_x:.1f} {start_y:.1f}, {mid_x:.1f} {end_y:.1f}, {end_x:.1f} {end_y:.1f}"
        attributes = {"class": "edge", "d": d, "data-source": edge["source"], "data-target-node": edge["target"]}
        if "relation_class" in edge:
            attributes["data-relation-class"] = edge["relation_class"]
            attributes["data-relation-domain"] = edge["relation_domain"]
        path = svg_element("path", attributes)
        domain = f" [{edge['relation_domain']}]" if "relation_domain" in edge else ""
        path.append(svg_element("title", text=f"{edge['source']} → {edge['target']}: {edge['label']}{domain}"))
        edge_layer.append(path)
    root.append(edge_layer)

    node_layer = svg_element("g", {"aria-label": "clickable system components"})
    repository_url = spec["repository_url"]
    for node in spec["nodes"]:
        x, y, node_width, node_height_value, _ = node_positions[node["id"]]
        link = svg_element(
            "a",
            {
                "class": "node-link",
                "href": target_url(repository_url, node["target"]),
                "target": "_top",
                "data-node-id": node["id"],
                "data-group": node["group"],
                "data-target": node["target"],
                "aria-label": f"{node['label']}：{node['description']}",
            },
        )
        link.append(svg_element("title", text=f"{node['label']} — {node['description']}"))
        link.append(svg_element("rect", {"class": "node", "x": f"{x:.1f}", "y": f"{y:.1f}", "width": f"{node_width:.1f}", "height": f"{node_height_value:.1f}", "rx": "10"}))
        lines = wrap_label(node["label"])
        text_y = y + (22 if len(lines) == 2 else 33)
        text_element = svg_element("text", {"class": "node-label", "x": f"{x + 16:.1f}", "y": f"{text_y:.1f}"})
        for offset, line in enumerate(lines):
            text_element.append(svg_element("tspan", {"x": f"{x + 16:.1f}", "dy": "0" if offset == 0 else "18"}, line))
        link.append(text_element)
        node_layer.append(link)
    root.append(node_layer)

    ET.indent(root, space="  ")
    buffer = io.BytesIO()
    ET.ElementTree(root).write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue() + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC, help="materialized derived projection path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    derived = build_projection()
    rendered = render_svg(derived, ROOT)
    if args.check:
        require(args.spec.is_file(), f"materialized system-map projection missing: {args.spec}")
        require(args.spec.read_bytes() == serialized_projection(derived), "materialized system-map projection is stale or hand-edited")
        require(args.output.is_file(), f"generated SVG missing: {args.output}")
        require(args.output.read_bytes() == rendered, "generated SVG is stale; run the generator")
        print(f"SYSTEM_MAP_DERIVED_OK nodes={len(derived['nodes'])} edges={len(derived['edges'])}")
        return 0
    args.spec.parent.mkdir(parents=True, exist_ok=True)
    args.spec.write_bytes(serialized_projection(derived))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered)
    print(f"generated {args.spec.relative_to(ROOT)} and {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
