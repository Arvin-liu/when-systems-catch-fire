#!/usr/bin/env python3
"""Fail-closed validation and deterministic projection for stage snapshots."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/operations/stage-snapshots.json"
SCHEMA = ROOT / "schemas/operations/stage-snapshot-registry.schema.json"
REQUEST_SCHEMA = ROOT / "schemas/operations/stage-snapshot-request.schema.json"
README = ROOT / "README.md"
PROJECTION = ROOT / "docs/generated/recent-stage-results.md"
START = "<!-- STAGE-SNAPSHOTS:START -->"
END = "<!-- STAGE-SNAPSHOTS:END -->"
INVARIANTS = {
    "PUBLISHED_SNAPSHOT != ACCEPTED",
    "PUBLISHED_SNAPSHOT != CURRENT",
    "PUBLISHED_SNAPSHOT != ACTIVATED",
    "SNAPSHOT_MERGED_TO_MAIN != CANDIDATE_PAYLOAD_MERGED_TO_MAIN",
    "HOMEPAGE_VISIBLE != CAPABILITY_AVAILABLE",
}
VISIBLE_STATUSES = {
    "PR_VISIBLE", "PUBLISHED_SNAPSHOT", "SUPERSEDED_SNAPSHOT",
    "WITHDRAWN_SNAPSHOT", "HISTORICAL_SNAPSHOT",
}
TERMINAL_FAILURE_OUTCOMES = {"REJECTED", "FAILURE", "WITHDRAWN"}
SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)authorization\s*:\s*(?:bearer|basic)\s+\S+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class ContractError(AssertionError):
    """A stage snapshot contract violation."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda e: [str(p) for p in e.path])
    return [f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _remote_key(repository: str, pr: int) -> str:
    return f"{repository}#{pr}"


def fetch_remote_fact(repository: str, pr: int) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/pulls/{pr}"],
        cwd=ROOT, text=True, capture_output=True, timeout=60,
    )
    require(result.returncode == 0, f"remote PR cannot be resolved: {repository}#{pr}: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    state = "MERGED" if payload.get("merged_at") else str(payload.get("state", "")).upper()
    return {
        "repository": repository,
        "pull_request": pr,
        "state": state,
        "draft": bool(payload.get("draft")),
        "head": payload["head"]["sha"],
        "branch": payload["head"]["ref"],
    }


def fetch_remote_facts(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for snapshot in registry["snapshots"]:
        source = snapshot["source"]
        evidence = snapshot["evidence"]
        facts[_remote_key(source["repository"], source["pull_request"])] = fetch_remote_fact(source["repository"], source["pull_request"])
        facts[_remote_key(evidence["relay_repository"], evidence["relay_pull_request"])] = fetch_remote_fact(evidence["relay_repository"], evidence["relay_pull_request"])
    return facts


def validate_request(request: dict[str, Any]) -> None:
    errors = schema_errors(request, load(REQUEST_SCHEMA))
    require(not errors, "stage snapshot request schema failure: " + errors[0] if errors else "")


def validate_registry(registry: dict[str, Any], remote_facts: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    errors = schema_errors(registry, load(SCHEMA))
    require(not errors, "stage snapshot registry schema failure: " + errors[0] if errors else "")
    require(set(registry["axis_invariants"]) == INVARIANTS, "stage/publication orthogonality invariants are incomplete")
    registry_state = registry["registry_state"]
    require(not registry_state["current"] or registry_state["accepted"], "Current method registry is not Accepted")
    require(not registry_state["merged_to_main"] or registry_state["accepted"], "unaccepted method registry claims Main merge")
    require(not registry_state["candidate"] or not registry_state["current"], "method registry cannot be Candidate and Current")

    snapshots = registry["snapshots"]
    ids = [item["snapshot_id"] for item in snapshots]
    require(len(ids) == len(set(ids)), "duplicate snapshot ID")
    by_id = {item["snapshot_id"]: item for item in snapshots}

    for item in snapshots:
        sid = item["snapshot_id"]
        source = item["source"]
        evidence = item["evidence"]
        att = item["remote_attestation"]

        require(source["pull_request_url"] == f"https://github.com/{source['repository']}/pull/{source['pull_request']}", f"{sid}: source PR URL/repository mismatch")
        require(evidence["relay_pull_request_url"] == f"https://github.com/{evidence['relay_repository']}/pull/{evidence['relay_pull_request']}", f"{sid}: relay PR URL/repository mismatch")
        require(source["exact_head"] == att["source_head"], f"{sid}: source HEAD drift from attestation")
        require(source["branch"] == att["source_branch"], f"{sid}: source branch drift from attestation")
        require(evidence["relay_exact_head"] == att["relay_head"], f"{sid}: 1111 receipt HEAD drift from attestation")
        require(evidence["relay_pull_request_url"] in evidence["entries"], f"{sid}: 1111 receipt entry missing")

        preaccepted_states = {"CANDIDATE", "READY", "IMPLEMENTED_PENDING_REVIEW", "REPAIR_ACCEPTED_IN_SOURCE_BRANCH", "REJECTED", "WITHDRAWN"}
        if item["lifecycle_state"] in preaccepted_states:
            require(not item["accepted"] and not item["current"] and not item["activated"], f"{sid}: pre-acceptance lifecycle has inflated boolean state")
        if item["lifecycle_state"] in {"ACCEPTED", "MERGED_CAPABILITY", "CURRENT", "CLOSED"}:
            require(item["accepted"], f"{sid}: post-acceptance lifecycle omits Accepted")
        if item["lifecycle_state"] == "CURRENT":
            require(item["current"], f"{sid}: CURRENT lifecycle omits Current boolean")

        require(not item["activated"] or item["accepted"], f"{sid}: Activated cannot be true without Accepted")
        require(not item["current"] or item["accepted"], f"{sid}: Current cannot be true without Accepted")
        require(not item["affects_formal_capability"] or item["accepted"], f"{sid}: candidate was registered as formal capability")
        require(not item["practical_application_allowed"] or item["activated"], f"{sid}: practical application requires explicit activation")
        require(not source["candidate_payload_merged_to_main"] or item["accepted"], f"{sid}: unaccepted candidate payload claims Main merge")
        main_snapshot_states = {"PUBLISHED_SNAPSHOT", "SUPERSEDED_SNAPSHOT", "WITHDRAWN_SNAPSHOT", "HISTORICAL_SNAPSHOT"}
        require(source["snapshot_record_merged_to_main"] == (item["publication_status"] in main_snapshot_states), f"{sid}: Main snapshot flag conflicts with publication state")
        require(not item["homepage"]["visible"] or item["publication_status"] in VISIBLE_STATUSES, f"{sid}: homepage exposes UNPUBLISHED snapshot")
        require(not item["homepage"]["visible"] or not item["affects_formal_capability"], f"{sid}: homepage visibility was used as capability registration")

        if item["lifecycle_state"] == "REJECTED":
            require(item["outcome"] in {"REJECTED", "FAILURE"}, f"{sid}: rejected lifecycle is disguised as success")
        if item["lifecycle_state"] == "WITHDRAWN":
            require(item["outcome"] == "WITHDRAWN", f"{sid}: withdrawn lifecycle is disguised as success")
        if item["publication_status"] == "SUPERSEDED_SNAPSHOT":
            require(item["relationships"]["superseded_by"], f"{sid}: superseded snapshot lacks successor relation")
        if item["publication_status"] == "WITHDRAWN_SNAPSHOT":
            require(item["outcome"] == "WITHDRAWN", f"{sid}: withdrawn snapshot is disguised as success")
        if item["outcome"] in TERMINAL_FAILURE_OUTCOMES:
            require(item["outcome"].lower() in item["homepage"]["summary"].lower() or any(term in item["homepage"]["summary"] for term in ("拒绝", "失败", "撤回")), f"{sid}: rejected/withdrawn result is disguised as success")
        homepage_summary = item["homepage"]["summary"]
        false_claims = {
            "accepted": (r"(?i)\baccepted\s*=\s*true\b", r"(?i)\bis\s+accepted\b", r"已(?:经)?(?:成为|通过).*Accepted"),
            "current": (r"(?i)\bcurrent\s*=\s*true\b", r"(?i)\bis\s+current\b", r"已(?:经)?(?:成为|进入).*Current"),
            "activated": (r"(?i)\bactivated\s*=\s*true\b", r"(?i)\bis\s+activated\b", r"已(?:经)?激活"),
        }
        for flag, patterns in false_claims.items():
            if not item[flag]:
                require(not any(re.search(pattern, homepage_summary) for pattern in patterns), f"{sid}: homepage falsely claims {flag}")

        for relation_name, relation_ids in item["relationships"].items():
            for related in relation_ids:
                require(related in by_id, f"{sid}: unknown {relation_name} snapshot {related}")
                require(related != sid, f"{sid}: self relation is forbidden")
        for successor in item["relationships"]["successors"]:
            require(sid in by_id[successor]["relationships"]["predecessors"], f"{sid}: successor relation is not reciprocal")
        for target in item["relationships"]["supersedes"]:
            require(sid in by_id[target]["relationships"]["superseded_by"], f"{sid}: supersedes relation is not reciprocal")

        public_blob = "\n".join(_strings(item))
        require("/Users/" not in public_blob and "file://" not in public_blob, f"{sid}: local/private path leaked")
        for pattern in SECRET_PATTERNS:
            require(not pattern.search(public_blob), f"{sid}: secret-like material detected")

        if remote_facts is not None:
            source_fact = remote_facts.get(_remote_key(source["repository"], source["pull_request"]))
            relay_fact = remote_facts.get(_remote_key(evidence["relay_repository"], evidence["relay_pull_request"]))
            require(source_fact is not None, f"{sid}: source PR does not exist in remote facts")
            require(relay_fact is not None, f"{sid}: 1111 receipt PR does not exist in remote facts")
            require(source_fact["head"] == source["exact_head"], f"{sid}: live source HEAD drift")
            require(source_fact["branch"] == source["branch"], f"{sid}: live source branch mismatch")
            require(source_fact["state"] == att["source_pr_state"] and source_fact["draft"] == att["source_pr_draft"], f"{sid}: live source PR state mismatch")
            require(relay_fact["head"] == evidence["relay_exact_head"], f"{sid}: live 1111 receipt HEAD drift")
            require(relay_fact["state"] == att["relay_pr_state"] and relay_fact["draft"] == att["relay_pr_draft"], f"{sid}: live 1111 receipt PR state mismatch")

    return {"status": "PASS", "snapshot_count": len(snapshots), "remote_verified": remote_facts is not None}


def _status_label(item: dict[str, Any]) -> str:
    labels = {
        "UNPUBLISHED": "未发布", "PR_VISIBLE": "PR 可见候选",
        "PUBLISHED_SNAPSHOT": "阶段快照", "SUPERSEDED_SNAPSHOT": "已被替代",
        "WITHDRAWN_SNAPSHOT": "已撤回", "HISTORICAL_SNAPSHOT": "历史快照",
    }
    return labels[item["publication_status"]]


def render_projection(registry: dict[str, Any]) -> str:
    visible = [item for item in registry["snapshots"] if item["homepage"]["visible"]]
    visible.sort(key=lambda item: (item["homepage"]["priority"], item["homepage"]["sort_time"], item["snapshot_id"]), reverse=True)
    visible = visible[: registry["projection_limit"]]
    lines = [
        "## 正在炼化 / Recent Stage Results",
        "",
        "> 这里展示的是可审计的阶段快照，不是能力接受公告。`PUBLISHED_SNAPSHOT != ACCEPTED`；`PUBLISHED_SNAPSHOT != CURRENT`；`PUBLISHED_SNAPSHOT != ACTIVATED`；`SNAPSHOT_MERGED_TO_MAIN != CANDIDATE_PAYLOAD_MERGED_TO_MAIN`；`HOMEPAGE_VISIBLE != CAPABILITY_AVAILABLE`。Current 正式能力仍以“项目现状”和正式 capability registry 为准。",
        "",
    ]
    for item in visible:
        source, evidence = item["source"], item["evidence"]
        flags = f"Accepted=`{str(item['accepted']).lower()}` · Current=`{str(item['current']).lower()}` · Activated=`{str(item['activated']).lower()}` · 正式能力影响=`{str(item['affects_formal_capability']).lower()}`"
        blockers = "；".join(item["known_limitations_and_blockers"])
        lines.extend([
            f"### {item['title']}", "",
            f"**类别：** {_status_label(item)} / `{item['lifecycle_state']}` / `{item['outcome']}`",
            "",
            f"**版本：** [{source['repository']} PR #{source['pull_request']}]({source['pull_request_url']}) @ `{source['exact_head'][:12]}`；分支 `{source['branch']}`",
            "",
            f"**状态边界：** {flags}",
            "",
            f"**最近成果：** {item['homepage']['summary']}",
            "",
            f"**仍有阻断：** {blockers}",
            "",
            f"**证据：** [正式 PR]({source['pull_request_url']}) / [1111 回执 PR #{evidence['relay_pull_request']}]({evidence['relay_pull_request_url']}) / [机器 registry](./data/operations/stage-snapshots.json)",
            "",
            f"**Claim ceiling：** {item['claim_ceiling']}", "",
        ])
    lines.extend([
        "阶段记录可被后继快照修订、替代或撤回；历史仍保留。Agent 只能提交 `stage snapshot request`，不能自行声称已进入 Main。",
        "",
        "[查看制度、状态图与发布门](./docs/operations/stage-snapshot-publication.md) / [查看全部机器记录](./data/operations/stage-snapshots.json)",
        "",
    ])
    return "\n".join(lines)


def readme_with_projection(readme: str, projection: str) -> str:
    block = f"{START}\n{projection.rstrip()}\n{END}"
    if START in readme or END in readme:
        require(readme.count(START) == 1 and readme.count(END) == 1, "README stage snapshot markers are malformed")
        return readme.split(START, 1)[0] + block + readme.split(END, 1)[1]
    anchor = "\n## 之元写作法成果\n"
    require(anchor in readme, "README stage snapshot insertion anchor missing")
    return readme.replace(anchor, f"\n{block}\n\n## 之元写作法成果\n", 1)


def materialize(registry: dict[str, Any], check: bool) -> None:
    projection = render_projection(registry)
    expected_readme = readme_with_projection(README.read_text(encoding="utf-8"), projection)
    expected_projection = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]
    if check:
        validate_materialized_projection(
            registry,
            README.read_text(encoding="utf-8"),
            PROJECTION.read_text(encoding="utf-8") if PROJECTION.is_file() else "",
        )
    else:
        README.write_text(expected_readme, encoding="utf-8")
        PROJECTION.parent.mkdir(parents=True, exist_ok=True)
        PROJECTION.write_text(expected_projection, encoding="utf-8")


def validate_materialized_projection(registry: dict[str, Any], readme: str, projection_doc: str) -> None:
    projection = render_projection(registry)
    expected_readme = readme_with_projection(readme, projection)
    expected_projection = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]
    require(readme == expected_readme, "README stage snapshot projection is stale")
    require(projection_doc == expected_projection, "generated stage snapshot projection is stale")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify-remotes", action="store_true")
    args = parser.parse_args()
    registry = load(REGISTRY)
    facts = fetch_remote_facts(registry) if args.verify_remotes else None
    result = validate_registry(registry, facts)
    materialize(registry, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
