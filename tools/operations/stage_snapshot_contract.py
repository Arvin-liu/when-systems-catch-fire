#!/usr/bin/env python3
"""Fail-closed validation and deterministic projection for stage snapshots."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/operations/stage-snapshots.json"
SCHEMA = ROOT / "schemas/operations/stage-snapshot-registry.schema.json"
REQUEST_SCHEMA = ROOT / "schemas/operations/stage-snapshot-request.schema.json"
ACTOR_REGISTRY = ROOT / "data/operations/responsibility-actors.json"
ACTOR_SCHEMA = ROOT / "schemas/operations/responsibility-actor-registry.schema.json"
PROJECTION = ROOT / "docs/generated/recent-stage-results.md"
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
NON_ACCOUNTABLE_TOKENS = {
    "ai", "agent", "agents", "algorithm", "algorithms", "automated", "automation",
    "bot", "bots", "ci", "codex", "model", "models", "pipeline", "pipelines",
    "platform", "platforms", "robot", "robots", "script", "scripts", "software",
    "workflow", "workflows",
}
STRICT_TECHNICAL_IDENTITY_TOKENS = {
    "ai", "agent", "agents", "algorithm", "algorithms", "bot", "bots", "ci",
    "codex", "model", "models", "pipeline", "pipelines", "platform", "platforms",
    "robot", "robots", "script", "scripts", "software", "workflow", "workflows",
}
TECHNICAL_WRAPPER_TOKENS = NON_ACCOUNTABLE_TOKENS | {
    "action", "actions", "automatic", "autonomous", "github", "organization",
    "organisation", "process", "processes", "publication", "publishing", "service",
    "services", "system", "systems", "team", "the",
}
NON_ACCOUNTABLE_PHRASES = {
    "github actions", "ignition founder", "the founder", "upstream project", "upstream organization",
    "the algorithm", "the system", "the systems", "a i", "c i",
    "人工智能", "智能体", "模型", "机器人", "算法", "工作流", "自动流程", "自动化流程",
    "持续集成", "脚本", "软件", "平台", "系统自动", "由系统", "无人负责",
}
PLACEHOLDER_NAMES = {
    "admin", "administrator", "anyone", "company", "governance", "human", "maintainer",
    "maintainers", "founder", "n a", "na", "nobody", "no one", "none", "null", "organization",
    "organisation", "owner", "project", "relevant people", "relevant personnel", "someone",
    "staff", "team", "tbd", "unknown", "unassigned",
}


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


def _normalized_actor_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[_\-/]+", " ", value)
    value = re.sub(r"[^a-z0-9\u3400-\u9fff]+", " ", value)
    return " ".join(value.split())


def _actor_identity(actor_ref: dict[str, Any]) -> str:
    return actor_ref["actor_ref"]


def _validate_registry_actor(actor: dict[str, Any], context: str) -> None:
    """Keep technical systems and placeholders out of the controlled actor registry."""
    actor_type = actor["type"]
    normalized_name = _normalized_actor_text(actor["official_name"])
    normalized_role = _normalized_actor_text(actor["role"])
    tokens = set(normalized_name.split())
    has_gpt_alias = any(token == "gpt" or re.fullmatch(r"gpt\d+", token) for token in tokens)
    is_synthetic = (
        bool(tokens & STRICT_TECHNICAL_IDENTITY_TOKENS)
        or has_gpt_alias
        or any(phrase in normalized_name for phrase in NON_ACCOUNTABLE_PHRASES)
        or bool(tokens) and tokens <= TECHNICAL_WRAPPER_TOKENS
    )
    require(not is_synthetic, f"{context}: non-accountable automated actor cannot be final responsibility")
    require(normalized_name not in PLACEHOLDER_NAMES, f"{context}: accountable actor name is generic or placeholder")
    require(normalized_role not in {"", "unknown", "tbd", "n a", "none"}, f"{context}: accountable actor role is missing or placeholder")
    expected_prefix = "person:" if actor_type == "PERSON" else "org:"
    require(actor["actor_id"].startswith(expected_prefix), f"{context}: stable ID does not match actor type")
    require(actor["accountability_reference"].startswith("https://"), f"{context}: accountability reference is not traceable")
    require(actor["human_or_governance_contact"].startswith("https://"), f"{context}: human/governance contact is not traceable")


def validate_actor_registry(actor_registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    actor_registry = load(ACTOR_REGISTRY) if actor_registry is None else actor_registry
    errors = schema_errors(actor_registry, load(ACTOR_SCHEMA))
    require(not errors, "responsibility actor registry schema failure: " + errors[0] if errors else "")
    actors = actor_registry["actors"]
    actor_ids = [actor["actor_id"] for actor in actors]
    require(len(actor_ids) == len(set(actor_ids)), "duplicate responsibility actor ID")
    history_ids: list[str] = []
    for actor in actors:
        _validate_registry_actor(actor, actor["actor_id"])
        actor_history_ids = [record["record_id"] for record in actor["history"]]
        require(len(actor_history_ids) == len(set(actor_history_ids)), f"{actor['actor_id']}: duplicate actor history record ID")
        for index, record in enumerate(actor["history"]):
            if index == 0:
                require(record["supersedes_record_id"] is None, f"{actor['actor_id']}: first actor history record cannot supersede another record")
            else:
                require(record["supersedes_record_id"] == actor["history"][index - 1]["record_id"], f"{actor['actor_id']}: actor history chain is broken")
        latest_change = actor["history"][-1]["change_type"]
        if actor["status"] == "ACTIVE":
            require(latest_change in {"REGISTERED", "REVISED"}, f"{actor['actor_id']}: active actor history status mismatch")
        else:
            require(latest_change == actor["status"], f"{actor['actor_id']}: inactive actor history status mismatch")
        history_ids.extend(actor_history_ids)
    require(len(history_ids) == len(set(history_ids)), "duplicate actor history record ID across registry")
    return {actor["actor_id"]: actor for actor in actors}


def active_actor_ids(actor_registry: dict[str, Any] | None = None) -> list[str]:
    actors = validate_actor_registry(actor_registry)
    return sorted(actor_id for actor_id, actor in actors.items() if actor["status"] == "ACTIVE")


def _schema_actor_ref_ids(schema: dict[str, Any]) -> list[str]:
    try:
        values = schema["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"]
    except (KeyError, TypeError) as exc:
        raise ContractError("schema accountable actor_ref enum is missing") from exc
    require(isinstance(values, list) and all(isinstance(value, str) for value in values), "schema accountable actor_ref enum is invalid")
    return sorted(values)


def validate_actor_contract_sources(
    actor_registry: dict[str, Any] | None = None,
    registry_schema: dict[str, Any] | None = None,
    request_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_ids = active_actor_ids(actor_registry)
    registry_schema_ids = _schema_actor_ref_ids(load(SCHEMA) if registry_schema is None else registry_schema)
    request_schema_ids = _schema_actor_ref_ids(load(REQUEST_SCHEMA) if request_schema is None else request_schema)
    require(registry_schema_ids == active_ids, "stage snapshot registry schema actor_ref set drift")
    require(request_schema_ids == active_ids, "stage snapshot request schema actor_ref set drift")
    require(registry_schema_ids == request_schema_ids, "stage snapshot schemas use different actor_ref sets")
    return {"status": "PASS", "active_actor_ids": active_ids}


def materialize_actor_schema_refs(*, check: bool) -> dict[str, Any]:
    active_ids = active_actor_ids()
    changed: list[str] = []
    for path in (SCHEMA, REQUEST_SCHEMA):
        schema = load(path)
        current_ids = _schema_actor_ref_ids(schema)
        if current_ids != active_ids:
            require(not check, f"{path.relative_to(ROOT)} actor_ref enum is stale")
            schema["$defs"]["accountableActorRef"]["properties"]["actor_ref"]["enum"] = active_ids
            path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    return {"status": "PASS", "active_actor_ids": active_ids, "changed": changed}


def resolve_actor(actor_ref: dict[str, Any], context: str, actor_registry: dict[str, Any] | None = None) -> dict[str, Any]:
    require(isinstance(actor_ref, dict) and set(actor_ref) == {"actor_ref"}, f"{context}: final responsibility must use only actor_ref")
    actors = validate_actor_registry(actor_registry)
    actor_id = actor_ref.get("actor_ref")
    require(actor_id in actors, f"{context}: actor_ref does not resolve")
    actor = actors[actor_id]
    require(actor["status"] == "ACTIVE", f"{context}: retired or withdrawn actor_ref cannot be used")
    return actor


def _validate_responsibility(
    responsibility: dict[str, Any], context: str, *, request: bool = False,
    actor_registry: dict[str, Any] | None = None,
) -> None:
    resolve_actor(responsibility["responsible_actor"], f"{context} responsible_actor", actor_registry)
    publisher_key = "proposed_publisher_actor" if request else "publisher_actor"
    resolve_actor(responsibility[publisher_key], f"{context} {publisher_key}", actor_registry)


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


def validate_request(request: dict[str, Any], actor_registry: dict[str, Any] | None = None) -> None:
    validate_actor_contract_sources(actor_registry)
    errors = schema_errors(request, load(REQUEST_SCHEMA))
    require(not errors, "stage snapshot request schema failure: " + errors[0] if errors else "")
    _validate_responsibility(request["responsibility"], "stage snapshot request", request=True, actor_registry=actor_registry)


def validate_registry(
    registry: dict[str, Any], remote_facts: dict[str, dict[str, Any]] | None = None,
    actor_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_actor_contract_sources(actor_registry)
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
    responsibility_record_ids = [item["responsibility"]["responsibility_record"]["record_id"] for item in snapshots]
    require(len(responsibility_record_ids) == len(set(responsibility_record_ids)), "duplicate responsibility record ID")

    for item in snapshots:
        sid = item["snapshot_id"]
        source = item["source"]
        evidence = item["evidence"]
        att = item["remote_attestation"]
        responsibility = item["responsibility"]
        responsibility_record = responsibility["responsibility_record"]

        _validate_responsibility(responsibility, sid, actor_registry=actor_registry)

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

        predecessor_records = {
            by_id[predecessor]["responsibility"]["responsibility_record"]["record_id"]
            for predecessor in item["relationships"]["predecessors"]
        }
        if responsibility_record["supersedes_record_id"] is not None:
            require(
                responsibility_record["supersedes_record_id"] in predecessor_records,
                f"{sid}: responsibility record does not supersede a declared predecessor",
            )
        for predecessor in item["relationships"]["predecessors"]:
            predecessor_responsibility = by_id[predecessor]["responsibility"]
            actor_changed = any(
                _actor_identity(responsibility[field]) != _actor_identity(predecessor_responsibility[field])
                for field in ("responsible_actor", "publisher_actor")
            )
            if actor_changed:
                require(
                    responsibility_record["supersedes_record_id"] == predecessor_responsibility["responsibility_record"]["record_id"],
                    f"{sid}: accountable actor changed without a new superseding responsibility record",
                )

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


def render_projection(registry: dict[str, Any], actor_registry: dict[str, Any] | None = None) -> str:
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
        responsibility = item["responsibility"]
        accountable = resolve_actor(responsibility["responsible_actor"], f"{item['snapshot_id']} responsible_actor", actor_registry)
        publisher = resolve_actor(responsibility["publisher_actor"], f"{item['snapshot_id']} publisher_actor", actor_registry)
        execution_agents = "、".join(actor["name"] for actor in responsibility["execution_agents"]) or "无"
        workflows = "、".join(workflow["name"] for workflow in responsibility["automation_workflows"]) or "无"
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
            f"**最终责任主体：** `{accountable['type']}` {accountable['official_name']}（`{accountable['actor_id']}`；{accountable['role']}；[责任依据]({accountable['accountability_reference']})；[负责人／治理入口]({accountable['human_or_governance_contact']})）",
            "",
            f"**发布责任主体：** `{publisher['type']}` {publisher['official_name']}（`{publisher['actor_id']}`；{publisher['role']}）",
            "",
            f"**技术执行记录（非最终责任）：** Agent／模型：{execution_agents}；自动化／工作流：{workflows}",
            "",
            f"**最近成果：** {item['homepage']['summary']}",
            "",
            f"**仍有阻断：** {blockers}",
            "",
            f"**证据：** [正式 PR]({source['pull_request_url']}) / [1111 回执 PR #{evidence['relay_pull_request']}]({evidence['relay_pull_request_url']}) / [快照 registry](./data/operations/stage-snapshots.json) / [责任主体 registry](./data/operations/responsibility-actors.json)",
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


def materialize(registry: dict[str, Any], check: bool) -> None:
    """Deterministically generate and validate the stage-snapshot dedicated page.

    The stage snapshot ONLY projects to docs/generated/recent-stage-results.md.
    It no longer inserts a 正在炼化 module or STAGE-SNAPSHOTS marker into README;
    the homepage front door is validated separately by validate_human_front_door.py.
    """
    projection = render_projection(registry)
    expected_projection = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]
    if check:
        validate_materialized_projection(
            registry,
            PROJECTION.read_text(encoding="utf-8") if PROJECTION.is_file() else "",
        )
    else:
        PROJECTION.parent.mkdir(parents=True, exist_ok=True)
        PROJECTION.write_text(expected_projection, encoding="utf-8")


def validate_materialized_projection(registry: dict[str, Any], projection_doc: str) -> None:
    projection = render_projection(registry)
    expected_projection = "# Recent Stage Results / 正在炼化\n\n" + projection.split("\n", 2)[2]
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
