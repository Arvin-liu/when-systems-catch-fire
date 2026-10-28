from __future__ import annotations

import json


def normalized_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def render_summary(network: dict) -> str:
    spec = network["network_spec"]
    return f"{spec['network_id']}: {len(network['nodes'])} nodes, {len(network['relations'])} relations, claim ceiling: {spec['claim_ceiling']}"


def render_markdown(network: dict, layer: str | None = None, time_window: tuple[float, float] | None = None, relation_class: str | None = None) -> str:
    relations = network.get("relations", [])
    if layer:
        relations = [r for r in relations if r["layer"] == layer]
    if relation_class:
        relations = [r for r in relations if r["relation_class"] == relation_class]
    if time_window:
        start, end = time_window
        relations = [r for r in relations if r["temporal_bounds"]["start"] >= start and r["temporal_bounds"]["end"] <= end]
    lines = [
        f"# {network['network_spec']['network_id']}",
        "",
        f"- Claim ceiling: {network['network_spec']['claim_ceiling']}",
        f"- Nodes: {len(network.get('nodes', []))}",
        f"- Relations in view: {len(relations)}",
        "",
        "## Relations"
    ]
    for rel in sorted(relations, key=lambda r: r["relation_id"]):
        lines.append(f"- `{rel['relation_id']}`: `{rel['source']}` -> `{rel['target']}` / `{rel['relation_class']}` / t={rel['temporal_bounds']['start']}..{rel['temporal_bounds']['end']}")
    if network.get("hyper_relations"):
        lines.extend(["", "## HyperRelations"])
        for hyper in sorted(network["hyper_relations"], key=lambda h: h["hyper_id"]):
            lines.append(f"- `{hyper['hyper_id']}` preserves {len(hyper['members'])} members; residue if projected: {hyper['residue_if_projected']}")
    lines.extend(["", "This rendering is a projection, not canonical evidence, truth, value or causality."])
    return "\n".join(lines) + "\n"


def render_timeline(network: dict) -> str:
    lines = [f"# Timeline: {network['network_spec']['network_id']}", ""]
    for episode in sorted(network.get("reconfiguration_episodes", []), key=lambda e: e["episode_id"]):
        lines.append(f"- `{episode['episode_id']}`: {episode['baseline_state']} -> {episode['post_state']}; delay={episode['delay']}; oscillation={episode['oscillation']}; claim={episode['claim_ceiling']}")
    return "\n".join(lines) + "\n"

