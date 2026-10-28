#!/usr/bin/env python3
"""Validate the registry-derived machine projection's geometry and compactness.

The stable homepage SVG is a separate Task150-derived public projection; its
provenance and bytes are checked by validate_homepage_architecture_projection.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from generate_interactive_system_map import build_projection, render_svg, validate_spec


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
SVG_NS = "http://www.w3.org/2000/svg"
QUALITY_PATH = ROOT / "data/architecture/system-map-geometry-quality-r1.json"
SCHEMA_PATH = ROOT / "schemas/architecture/system-map-geometry-quality.schema.json"
BASELINE_PATH = ROOT / "data/architecture/system-map-geometry-baseline-r1.json"
FIXTURE_PATH = ROOT / "data/operations/iterations/123/fixtures/system-map-geometry-fixtures-r1.json"
SVG_PATH = ROOT / "docs/generated/ignition-system-architecture.svg"
MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"
TASK_ID = "IGNITION-20260816-123"
EPSILON = 1e-6
MOBILE_VIEWPORTS = [(375, 667), (390, 844)]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def box_overlap(left: dict[str, float], right: dict[str, float]) -> bool:
    overlap_width = min(left["x"] + left["width"], right["x"] + right["width"]) - max(left["x"], right["x"])
    overlap_height = min(left["y"] + left["height"], right["y"] + right["height"]) - max(left["y"], right["y"])
    return overlap_width > EPSILON and overlap_height > EPSILON


def box_contains(outer: dict[str, float], inner: dict[str, float]) -> bool:
    return (
        inner["x"] >= outer["x"] - EPSILON
        and inner["y"] >= outer["y"] - EPSILON
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + EPSILON
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"] + EPSILON
    )


def orient(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def proper_segment_crossing(
    first_start: tuple[float, float],
    first_end: tuple[float, float],
    second_start: tuple[float, float],
    second_end: tuple[float, float],
) -> bool:
    if {first_start, first_end, second_start, second_end}.__len__() < 4:
        return False
    first_a = orient(first_start, first_end, second_start)
    first_b = orient(first_start, first_end, second_end)
    second_a = orient(second_start, second_end, first_start)
    second_b = orient(second_start, second_end, first_end)
    return ((first_a > 0 and first_b < 0) or (first_a < 0 and first_b > 0)) and ((second_a > 0 and second_b < 0) or (second_a < 0 and second_b > 0))


def baseline_blank_area(baseline: dict[str, Any]) -> float:
    groups = baseline.get("groups", [])
    group_width = float(groups[0]["width"]) if groups else 0.0
    return sum(sum(float(gap) for gap in data.get("internal_gaps", [])) * group_width for data in baseline["vertical_blank_corridor"]["by_column"].values())


def parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    values = [float(value) for value in root.attrib.get("viewBox", "").split()]
    require(len(values) == 4, "SVG viewBox must contain four numeric values")
    require(values[2] > 0 and values[3] > 0, "SVG viewBox must have positive width and height")
    return values[0], values[1], values[2], values[3]


def text_last_baseline(text_element: ET.Element) -> float:
    baseline = float(text_element.attrib.get("y", "nan"))
    tspans = text_element.findall(f"{{{SVG_NS}}}tspan")
    return baseline + 18 * max(0, len(tspans) - 1)


def approximate_text_width(value: str, default_width: float = 8.0) -> float:
    return sum(14.0 if ord(char) >= 0x3000 else default_width for char in value)


def parse_current_geometry(spec: dict[str, Any]) -> dict[str, Any]:
    rendered = render_svg(spec, ROOT)
    root = ET.fromstring(rendered)
    _, _, width, height = parse_viewbox(root)
    layout = spec["layout"]
    group_elements = root.findall(f".//{{{SVG_NS}}}rect[@class='cluster']")
    groups: list[dict[str, Any]] = []
    group_by_id: dict[str, dict[str, Any]] = {}
    spec_groups = {group["id"]: group for group in spec["groups"]}
    for element in group_elements:
        group_id = element.attrib.get("data-group", "")
        require(group_id in spec_groups, f"SVG cluster lacks a known data-group: {group_id}")
        box = {key: float(element.attrib[key]) for key in ("x", "y", "width", "height")}
        record = {"id": group_id, "column": int(spec_groups[group_id]["column"]), "node_count": 0, "degree": 0, **box}
        groups.append(record)
        group_by_id[group_id] = record
    require(set(group_by_id) == set(spec_groups), "SVG cluster set differs from map groups")

    anchors = root.findall(f".//{{{SVG_NS}}}a[@class='node-link']")
    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    label_clip_count = 0
    node_group_by_id = {node["id"]: node["group"] for node in spec["nodes"]}
    for anchor in anchors:
        node_id = anchor.attrib.get("data-node-id", "")
        rect = anchor.find(f"{{{SVG_NS}}}rect[@class='node']")
        require(rect is not None, f"clickable node {node_id} lacks a node rect")
        group_id = anchor.attrib.get("data-group", "")
        require(node_id in node_group_by_id and group_id == node_group_by_id[node_id], f"SVG node/group mismatch for {node_id}")
        box = {key: float(rect.attrib[key]) for key in ("x", "y", "width", "height")}
        nodes.append({"id": node_id, "group": group_id, **box})
        node_ids.add(node_id)
        group_by_id[group_id]["node_count"] += 1
        text_element = anchor.find(f"{{{SVG_NS}}}text[@class='node-label']")
        if text_element is None:
            label_clip_count += 1
            continue
        last_baseline = text_last_baseline(text_element)
        text_x = float(text_element.attrib.get("x", "nan"))
        line_widths = [approximate_text_width(tspan.text or "") for tspan in text_element.findall(f"{{{SVG_NS}}}tspan")]
        if last_baseline > box["y"] + box["height"] - 5 or text_x < box["x"] or max([text_x + width_value for width_value in line_widths] or [text_x]) > box["x"] + box["width"] - 8:
            label_clip_count += 1

    expected_node_ids = set(node_group_by_id)
    clickable_target_coverage = node_ids == expected_node_ids and all(anchor.attrib.get("href", "").startswith("https://github.com/") for anchor in anchors)
    for group in groups:
        cluster_title = next((element for element in root.findall(f".//{{{SVG_NS}}}text[@class='cluster-title']") if abs(float(element.attrib.get("x", "nan")) - group["x"] - 22) < EPSILON and abs(float(element.attrib.get("y", "nan")) - group["y"] - 32) < EPSILON), None)
        cluster_desc = next((element for element in root.findall(f".//{{{SVG_NS}}}text[@class='cluster-desc']") if abs(float(element.attrib.get("x", "nan")) - group["x"] - 22) < EPSILON and abs(float(element.attrib.get("y", "nan")) - group["y"] - 58) < EPSILON), None)
        for element in (cluster_title, cluster_desc):
            if element is None or text_last_baseline(element) > group["y"] + float(layout["group_header_height"]) - 8:
                label_clip_count += 1
            elif any(float(element.attrib.get("x", "nan")) + approximate_text_width(tspan.text or "") > group["x"] + group["width"] - 8 for tspan in element.findall(f"{{{SVG_NS}}}tspan")):
                label_clip_count += 1

    edges = [{"id": edge["id"], "source": edge["source"], "target": edge["target"]} for edge in spec["edges"]]
    node_by_id = {node["id"]: node for node in nodes}
    for edge in edges:
        require(edge["source"] in node_by_id and edge["target"] in node_by_id, f"edge endpoint missing from SVG: {edge['id']}")
        if node_by_id[edge["source"]]["group"] != node_by_id[edge["target"]]["group"]:
            group_by_id[node_by_id[edge["source"]]["group"]]["degree"] += 1
            group_by_id[node_by_id[edge["target"]]["group"]]["degree"] += 1

    group_overlap_count = sum(1 for index, first in enumerate(groups) for second in groups[index + 1 :] if box_overlap(first, second))
    node_overlap_count = sum(1 for index, first in enumerate(nodes) for second in nodes[index + 1 :] if box_overlap(first, second))
    nodes_outside_group_count = sum(1 for node in nodes if not box_contains(group_by_id[node["group"]], node))
    by_column: dict[int, list[dict[str, Any]]] = {}
    for group in groups:
        by_column.setdefault(group["column"], []).append(group)
    internal_gaps: list[float] = []
    gap_by_column: dict[str, dict[str, Any]] = {}
    for column, column_groups in sorted(by_column.items()):
        ordered = sorted(column_groups, key=lambda group: group["y"])
        gaps = [round(ordered[index + 1]["y"] - (ordered[index]["y"] + ordered[index]["height"]), 6) for index in range(len(ordered) - 1)]
        internal_gaps.extend(gaps)
        gap_by_column[str(column)] = {"groups": [group["id"] for group in ordered], "internal_gaps": gaps, "max_internal_gap": max(gaps or [0.0])}
    max_internal_gap = max(internal_gaps or [0.0])
    bottom_only_groups: list[str] = []
    bottom_only_isolated_groups: list[str] = []
    for column_groups in by_column.values():
        bottom = max(group["y"] + group["height"] for group in column_groups)
        for group in column_groups:
            if abs(group["y"] + group["height"] - bottom) < EPSILON:
                bottom_only_groups.append(group["id"])
                if group["degree"] == 0:
                    bottom_only_isolated_groups.append(group["id"])

    segments = [(edge["id"], (node_by_id[edge["source"]]["x"] + node_by_id[edge["source"]]["width"] / 2, node_by_id[edge["source"]]["y"] + node_by_id[edge["source"]]["height"] / 2), (node_by_id[edge["target"]]["x"] + node_by_id[edge["target"]]["width"] / 2, node_by_id[edge["target"]]["y"] + node_by_id[edge["target"]]["height"] / 2), edge["source"], edge["target"]) for edge in edges]
    edge_crossing_proxy = 0
    for index, first in enumerate(segments):
        for second in segments[index + 1 :]:
            if set(first[3:]) & set(second[3:]):
                continue
            if proper_segment_crossing(first[1], first[2], second[1], second[2]):
                edge_crossing_proxy += 1

    min_x = min(group["x"] for group in groups)
    min_y = min(group["y"] for group in groups)
    max_x = max(group["x"] + group["width"] for group in groups)
    max_y = max(group["y"] + group["height"] for group in groups)
    padding = {"left": min_x, "top": min_y, "right": width - max_x, "bottom": height - max_y}
    mobile_viewports = []
    for viewport_width, viewport_height in MOBILE_VIEWPORTS:
        scale = min(viewport_width / width, viewport_height / height)
        mobile_viewports.append({"width": viewport_width, "height": viewport_height, "fit_scale": round(scale, 8), "fit_without_horizontal_scroll": height * viewport_width / width <= viewport_height + EPSILON})

    return {
        "canvas": {"width": width, "height": height, "view_box": root.attrib["viewBox"], "preserve_aspect_ratio": root.attrib.get("preserveAspectRatio", "")},
        "groups": sorted(groups, key=lambda group: group["id"]),
        "nodes": sorted(nodes, key=lambda node: node["id"]),
        "edges": edges,
        "expected_node_count": len(expected_node_ids),
        "clickable_target_count": len(anchors),
        "clickable_target_coverage": clickable_target_coverage,
        "solid_background_rect_count": len(root.findall(f".//{{{SVG_NS}}}rect[@class='map-bg']")),
        "label_clip_count": label_clip_count,
        "group_box_overlap_count": group_overlap_count,
        "node_box_overlap_count": node_overlap_count,
        "nodes_outside_group_count": nodes_outside_group_count,
        "internal_blank_area": round(sum(internal_gaps) * float(layout["group_width"]), 6),
        "gap_by_column": gap_by_column,
        "max_internal_gap": max_internal_gap,
        "bottom_only_groups": sorted(bottom_only_groups),
        "bottom_only_isolated_groups": sorted(bottom_only_isolated_groups),
        "edge_crossing_proxy": edge_crossing_proxy,
        "padding": padding,
        "outer_padding": float(layout["outer_padding"]),
        "top_offset": float(layout["top_offset"]),
        "mobile_viewports": mobile_viewports,
    }


def assess(raw: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_height = float(baseline["canvas"]["height"])
    baseline_crossings = float(baseline["edge_crossing_proxy"]["count"])
    baseline_blank = baseline_blank_area(baseline)
    blank_reduction = 1.0 - (float(raw["internal_blank_area"]) / baseline_blank if baseline_blank else 0.0)
    height_reduction = 1.0 - float(raw["canvas"]["height"]) / baseline_height
    crossing_ratio = float(raw["edge_crossing_proxy"]) / baseline_crossings if baseline_crossings else 0.0
    thresholds = {
        "minimum_blank_area_reduction_vs_baseline": 0.30,
        "minimum_canvas_height_reduction_vs_baseline": 0.20,
        "maximum_edge_crossing_ratio_vs_baseline": 1.10,
        "maximum_internal_gap": 200.0,
        "required_outer_padding": raw["outer_padding"],
        "required_mobile_viewports_without_horizontal_scroll": len(MOBILE_VIEWPORTS),
    }
    failures: list[str] = []
    if raw["group_box_overlap_count"]:
        failures.append("group_box_overlap")
    if raw["node_box_overlap_count"]:
        failures.append("node_box_overlap")
    if raw["nodes_outside_group_count"]:
        failures.append("node_box_outside_group")
    if raw["clickable_target_count"] != raw["expected_node_count"] or not raw["clickable_target_coverage"]:
        failures.append("clickable_target_coverage")
    if raw["solid_background_rect_count"] != 1:
        failures.append("solid_background")
    if raw["label_clip_count"]:
        failures.append("label_clip")
    if abs(raw["padding"]["left"] - raw["outer_padding"]) > 1 or abs(raw["padding"]["right"] - raw["outer_padding"]) > 1 or abs(raw["padding"]["bottom"] - raw["outer_padding"]) > 1 or raw["padding"]["top"] > raw["top_offset"] + 1:
        failures.append("canvas_envelope_padding")
    if raw["max_internal_gap"] > thresholds["maximum_internal_gap"]:
        failures.append("max_internal_gap")
    if blank_reduction < thresholds["minimum_blank_area_reduction_vs_baseline"]:
        failures.append("blank_area_reduction")
    if height_reduction < thresholds["minimum_canvas_height_reduction_vs_baseline"]:
        failures.append("canvas_height_reduction")
    if crossing_ratio > thresholds["maximum_edge_crossing_ratio_vs_baseline"]:
        failures.append("edge_crossing_regression")
    if raw["bottom_only_isolated_groups"]:
        failures.append("isolated_bottom_group")
    if len(raw["nodes"]) != raw["expected_node_count"]:
        failures.append("node_geometry_missing")
    if raw["canvas"]["preserve_aspect_ratio"] != "xMidYMin meet":
        failures.append("mobile_zoomable")
    if sum(1 for viewport in raw["mobile_viewports"] if viewport["fit_without_horizontal_scroll"]) < thresholds["required_mobile_viewports_without_horizontal_scroll"]:
        failures.append("mobile_viewport_fit")
    return {
        "checks": {
            "group_box_overlap_count": raw["group_box_overlap_count"],
            "node_box_overlap_count": raw["node_box_overlap_count"],
            "nodes_outside_group_count": raw["nodes_outside_group_count"],
            "clickable_target_count": raw["clickable_target_count"],
            "expected_node_count": raw["expected_node_count"],
            "clickable_target_coverage": raw["clickable_target_coverage"],
            "solid_background_rect_count": raw["solid_background_rect_count"],
            "label_clip_count": raw["label_clip_count"],
            "bottom_only_isolated_groups": raw["bottom_only_isolated_groups"],
            "node_geometry_count": len(raw["nodes"]),
        },
        "metrics": {
            "canvas_height": raw["canvas"]["height"],
            "canvas_width": raw["canvas"]["width"],
            "internal_blank_area": raw["internal_blank_area"],
            "baseline_internal_blank_area": baseline_blank,
            "blank_area_reduction_vs_baseline": round(blank_reduction, 10),
            "baseline_canvas_height": baseline_height,
            "canvas_height_reduction_vs_baseline": round(height_reduction, 10),
            "edge_crossing_proxy": raw["edge_crossing_proxy"],
            "baseline_edge_crossing_proxy": baseline_crossings,
            "edge_crossing_ratio_vs_baseline": round(crossing_ratio, 10),
            "max_internal_gap": raw["max_internal_gap"],
            "group_occupancy_ratio": round(sum(group["width"] * group["height"] for group in raw["groups"]) / (raw["canvas"]["width"] * raw["canvas"]["height"]), 10),
            "mobile_viewports_fit": sum(1 for viewport in raw["mobile_viewports"] if viewport["fit_without_horizontal_scroll"]),
        },
        "thresholds": thresholds,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }


def build_report() -> dict[str, Any]:
    spec = build_projection()
    validate_spec(spec, ROOT)
    baseline = load_json(BASELINE_PATH)
    raw = parse_current_geometry(spec)
    assessment = assess(raw, baseline)
    return {
        "schema_version": "system-map-geometry-quality-r1",
        "task_id": TASK_ID,
        "map_version": spec["map_version"],
        "layout_version": spec["projection_authority"]["layout_version"],
        "packing_algorithm": spec["layout"]["packing_algorithm"],
        "canvas": raw.pop("canvas"),
        "groups": raw.pop("groups"),
        "nodes": raw.pop("nodes"),
        "edges": raw.pop("edges"),
        "padding": raw.pop("padding"),
        "outer_padding": raw.pop("outer_padding"),
        "top_offset": raw.pop("top_offset"),
        "mobile_viewports": raw.pop("mobile_viewports"),
        **raw,
        **assessment,
    }


def fixture_baseline_candidate(baseline: dict[str, Any]) -> dict[str, Any]:
    groups = [
        {"id": group["id"], "column": int(group["column"]), "node_count": int(group["node_count"]), "degree": int(group["group_degree"]), "x": float(group["x"]), "y": float(group["y"]), "width": float(group["width"]), "height": float(group["height"])}
        for group in baseline["groups"]
    ]
    return {
        "canvas": {"width": float(baseline["canvas"]["width"]), "height": float(baseline["canvas"]["height"]), "preserve_aspect_ratio": "xMidYMin meet"},
        "groups": groups,
        "nodes": [],
        "edges": [],
        "expected_node_count": int(baseline["clickability_and_isolation"]["visible_nodes"]),
        "clickable_target_count": int(baseline["clickability_and_isolation"]["svg_clickable_targets"]),
        "clickable_target_coverage": True,
        "solid_background_rect_count": 1,
        "label_clip_count": 0,
        "padding": {"left": 32.0, "top": 122.0, "right": 32.0, "bottom": 32.0},
        "outer_padding": 32.0,
        "top_offset": 122.0,
        "mobile_viewports": [{"width": width, "height": height, "fit_without_horizontal_scroll": False} for width, height in MOBILE_VIEWPORTS],
        "group_box_overlap_count": 0,
        "node_box_overlap_count": 0,
        "nodes_outside_group_count": 0,
        "internal_blank_area": baseline_blank_area(baseline),
        "max_internal_gap": float(baseline["vertical_blank_corridor"]["max_internal_gap"]),
        "bottom_only_isolated_groups": [],
        "edge_crossing_proxy": float(baseline["edge_crossing_proxy"]["count"]),
    }


def check_fixtures(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    fixture_doc = load_json(FIXTURE_PATH)
    errors: list[str] = []
    for fixture in fixture_doc.get("fixtures", []):
        if fixture.get("mutation") == "old_row_max_baseline":
            candidate = fixture_baseline_candidate(baseline)
        elif fixture.get("mutation") == "overlap_first_two_groups":
            candidate = copy.deepcopy(current)
            candidate["groups"][1]["x"] = candidate["groups"][0]["x"]
            candidate["groups"][1]["y"] = candidate["groups"][0]["y"]
            candidate["group_box_overlap_count"] = 1
        else:
            errors.append(f"unknown geometry fixture mutation: {fixture.get('mutation')}")
            continue
        result = assess(candidate, baseline)
        expected = set(fixture.get("expected_failure_codes", []))
        actual = set(result["failures"])
        if result["status"] != fixture.get("expected_status"):
            errors.append(f"fixture {fixture['id']} expected {fixture.get('expected_status')} but got {result['status']}")
        if not expected.issubset(actual):
            errors.append(f"fixture {fixture['id']} missing failures: {sorted(expected - actual)}")
    return errors


def schema_errors(document: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator

        schema = load_json(SCHEMA_PATH)
        return [error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(document)]
    except ImportError:
        return []


def check() -> tuple[list[str], dict[str, Any]]:
    expected = build_report()
    errors = schema_errors(expected)
    if QUALITY_PATH.read_bytes() != (json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"):
        errors.append("system-map-geometry-quality-r1.json is stale; run --write")
    if expected["status"] != "PASS":
        errors.append("current system-map geometry quality status is FAIL: " + ", ".join(expected["failures"]))
    errors.extend(check_fixtures(expected, load_json(BASELINE_PATH)))
    return errors, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-fixtures", action="store_true")
    args = parser.parse_args()
    if sum(bool(value) for value in (args.write, args.check, args.check_fixtures)) != 1:
        parser.error("choose exactly one of --write, --check or --check-fixtures")
    if args.write:
        report = build_report()
        QUALITY_PATH.write_bytes((json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print(f"SYSTEM_MAP_GEOMETRY_WRITTEN status={report['status']} blank_reduction={report['metrics']['blank_area_reduction_vs_baseline']}")
        return 0 if report["status"] == "PASS" else 1
    if args.check_fixtures:
        errors = check_fixtures(build_report(), load_json(BASELINE_PATH))
        if errors:
            print("SYSTEM_MAP_GEOMETRY_FIXTURES_INVALID", file=sys.stderr)
            for error in errors:
                print("- " + error, file=sys.stderr)
            return 1
        print("SYSTEM_MAP_GEOMETRY_FIXTURES_OK")
        return 0
    errors, report = check()
    if errors:
        print("SYSTEM_MAP_GEOMETRY_INVALID", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1
    print(f"SYSTEM_MAP_GEOMETRY_OK height={report['canvas']['height']} blank_reduction={report['metrics']['blank_area_reduction_vs_baseline']} crossing={report['metrics']['edge_crossing_proxy']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
