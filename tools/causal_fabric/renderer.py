from __future__ import annotations

from .projector import project_summary


def render_markdown(fabric: dict) -> str:
    summary = project_summary(fabric)
    lines = [
        f"# {summary['fabric_id']}",
        "",
        f"- Events: {summary['events']}",
        f"- States: {summary['states']}",
        f"- Relations: {summary['relations']}",
        f"- Relation classes: {', '.join(summary['relation_classes'])}",
        f"- Scale domains: {', '.join(summary['scale_domains'])}",
        f"- Residue count: {summary['residue_count']}",
        f"- Claim ceiling: {summary['claim_ceiling']}",
        "",
        "This rendering is a derived view. It is not causal proof and does not replace Foundation.",
    ]
    return "\n".join(lines) + "\n"

