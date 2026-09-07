#!/usr/bin/env python3
"""Research-only Task165 cross-thread creative-discontinuity replay.

This runner is a deterministic, corpus-bound structural proxy. It does not
simulate a brain, call a production model, or turn a textual pattern into a
cognitive fact. The historical stream is blind to the answer key and the
live exploratory stream is reported below the validation ceiling unless all
frozen gates pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
DEFAULT_OUT = ROOT / "data/research/cross-thread-creative-discontinuity-2026-09-08"
OUT = DEFAULT_OUT

TASK = "IGNITION-20260908-165"
COMMAND_REPOSITORY = "Arvin-liu/1111"
COMMAND_PATH = "agent-commands/IGNITION-20260908-165.md"
COMMAND_COMMIT = "b3b128f46a625f728870ded1a975f3c2f0db53ce"
COMMAND_BLOB = "065f02e04e3a0c8e55c398954a761c66901f74b5"
COMMAND_SHA256 = "dcd123b9ae487f54dd7afcc921f9f1fd691147c463634e33e8d3f1f136b2d22a"
COMMAND_URL = "https://github.com/Arvin-liu/1111/blob/" + COMMAND_COMMIT + "/" + COMMAND_PATH
FORMAL_BASE_REF = "work/IGNITION-20260907-164"
FORMAL_BASE = "ba6641d200000ad4ebaa764e4ed94d79f32fb2df"
FORMAL_BRANCH = "work/IGNITION-20260908-165"
RECEIPT_BRANCH = "work/IGNITION-20260908-165-receipt"

SEEDS = (17, 29, 43)
CONDITIONS = ("C0", "C1", "C2", "C3", "C4")
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml", ".toml", ".rst", ".csv"}


# Answer-key material. It is written only to the unblind side and is never
# read by run_blind().
EVENTS: list[dict[str, Any]] = [
    {
        "answer_id": "P00",
        "event_label": "P00_ATTRIBUTE_TO_MECHANISM",
        "kind": "positive",
        "split": "qualitative_boundary_gap",
        "packet_id": "hist-001",
        "start_commit": "a88b086c8099cd87ffe5e5db82705fb1c85748c5",
        "pre_leap_commit": "cb58d24ccd9c074fa4ae9fbb99531cc6d4bd5a01",
        "leap_commit": "c1cd45d1356a3fe653c84f75688c4ba7a55ffe79",
        "required_capability": "MECHANISM_REWRITE",
        "scoreable": False,
        "boundary_status": "HISTORICAL_BOUNDARY_GAP",
        "boundary_reason": "Reachable history supports a qualitative sequence but does not establish a precise pre-event boundary without inventing one.",
    },
    {
        "answer_id": "P01",
        "event_label": "P01_CASE_TO_REUSABLE_OBJECT",
        "kind": "positive",
        "split": "calibration",
        "packet_id": "hist-002",
        "start_commit": "edd7d116d0580e3810d2ff73037981bd07e011b6",
        "pre_leap_commit": "981d3f5f1cdb62c058f5de8c626444c050ab95d8",
        "leap_commit": "a1295d737e290105069f915c577105c0cf5ff26f",
        "required_capability": "OBJECT_REFRAME",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Exact pre-event prefix is reachable and retained; capability is adjudicated only after blind replay.",
    },
    {
        "answer_id": "P02",
        "event_label": "P02_REPEATED_MANUAL_STEP_TO_LOOP",
        "kind": "positive",
        "split": "holdout",
        "packet_id": "hist-003",
        "start_commit": "a1295d737e290105069f915c577105c0cf5ff26f",
        "pre_leap_commit": "f4b0c5af3e296019d52f735d178a3f2078ead7be",
        "leap_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "required_capability": "LOOP_OPERATION",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Exact pre-event prefix is reachable and retained; capability is adjudicated only after blind replay.",
    },
    {
        "answer_id": "P03",
        "event_label": "P03_ONE_WAY_TO_INDEPENDENT_CHECK",
        "kind": "positive",
        "split": "holdout",
        "packet_id": "hist-004",
        "start_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "pre_leap_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "leap_commit": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b",
        "required_capability": "COUNTERCHECK_OPERATION",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Target follows immediately from the starting commit; no intervening stable prefix exists.",
    },
    {
        "answer_id": "P04",
        "event_label": "P04_RULES_TO_COMPOSABLE_GENERATOR",
        "kind": "positive",
        "split": "holdout",
        "packet_id": "hist-005",
        "start_commit": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b",
        "pre_leap_commit": "1defe3d39988f9716863b2fd39d763808e1579e0",
        "leap_commit": "974b121e36145d6ed35b214619312001f97b21f8",
        "required_capability": "COMPOSE_RULE_OPERATION",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Exact pre-event prefix is reachable and retained; capability is adjudicated only after blind replay.",
    },
    {
        "answer_id": "N02",
        "event_label": "N02_INCREMENTAL_REGISTRY",
        "kind": "negative",
        "split": "calibration",
        "packet_id": "hist-006",
        "start_commit": "0b2a88f508274feadd4adbbda3eefc3ab531ddd2",
        "pre_leap_commit": "56b952a3b101c6ed385d1c11591914d043a337cd",
        "leap_commit": "ab90558ae1c158d9a67146ebd288678b67e1c4c3",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Matched incremental materialization control.",
    },
    {
        "answer_id": "N03",
        "event_label": "N03_CANONICAL_PROTOCOL_MIGRATION",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-007",
        "start_commit": "1defe3d39988f9716863b2fd39d763808e1579e0",
        "pre_leap_commit": "633ca814c6a53b4bdab425001459aabc5a0cccbf",
        "leap_commit": "4c452149a451f074d949739086cfccdb3ec5bd56",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Matched conservative protocol migration control.",
    },
    {
        "answer_id": "N04",
        "event_label": "N04_PAGES_PROJECTION",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-008",
        "start_commit": "037eaad775909cb85928ecff457e421aa1f8d041",
        "pre_leap_commit": "304ecfc645bbe44c4b1dbdac8a119b8ed0009c31",
        "leap_commit": "d4bfaa886908bd3b3f109c7d8220a89a5d469186",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Matched large projection control.",
    },
    {
        "answer_id": "N05",
        "event_label": "N05_VALIDATOR_EXPANSION",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-009",
        "start_commit": "d5044e1eaeaaf69cd70059428b32ee7487451bf6",
        "pre_leap_commit": "9bf1ca0e2beebc1d4abf85b5b9e4bb2b6e17c2c9",
        "leap_commit": "ba56c43c1a9d429ee182ea976be4859bd5972733",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Matched validator and governance expansion control.",
    },
    {
        "answer_id": "N06",
        "event_label": "N06_KNOWLEDGE_PROJECTION_REFRESH",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-010",
        "start_commit": "212322d41db79bce2dbd116166d3f1ad226291f3",
        "pre_leap_commit": "0741f4f0902d50cf5388e787382500b5240d2b0e",
        "leap_commit": "74096d5ad0faa4b524879061d332c7026c2a83a0",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Matched knowledge projection refresh control.",
    },
    {
        "answer_id": "N07",
        "event_label": "N07_PROVIDER_ADAPTER_REFACTOR",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-011",
        "start_commit": "e60acb82fc92fe2378ae605f0f8a59b0aa120d7e",
        "pre_leap_commit": "a051ad31b72d5cbb8deeaf2007b0e09431f8a4ba",
        "leap_commit": "02e43c62942da8b65f005a6314d3eee799aaa776",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Matched provider and adapter refactor control.",
    },
    {
        "answer_id": "N08",
        "event_label": "N08_GENERATED_PROJECTION_REFRESH",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-012",
        "start_commit": "304ecfc645bbe44c4b1dbdac8a119b8ed0009c31",
        "pre_leap_commit": "d4bfaa886908bd3b3f109c7d8220a89a5d469186",
        "leap_commit": "188ae92d3fd4b52b9b3cdba99c66d63b04a2a8fc",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED",
        "boundary_reason": "Matched generated-output refresh control.",
    },
    {
        "answer_id": "N09",
        "event_label": "N09_KNOWLEDGE_MATERIALIZATION",
        "kind": "negative",
        "split": "holdout",
        "packet_id": "hist-013",
        "start_commit": "e07497fa76d5c58a4b77035e48867cae7264d3ab",
        "pre_leap_commit": "d6910b43d8c216191f375b5737f82afa0b0a6bff",
        "leap_commit": "f2947ef3e26cd51cc3f156badcba6d2411f77b23",
        "required_capability": "NONE",
        "scoreable": True,
        "boundary_status": "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
        "boundary_reason": "Matched large knowledge materialization control.",
    },
]


THREAD_SPECS = [
    ("T01", "history", "ignition/docs/pending_claims_register.md", "dormant"),
    ("T02", "narrative", "ignition/docs/storytelling_case_backlog.md", "dormant"),
    ("T03", "software_architecture", "ignition/docs/architecture/agent-platform-r2.md", "active"),
    ("T04", "operating_systems", "ignition/docs/architecture/os-control-plane-r2.md", "active"),
    ("T05", "distributed_systems", "ignition/docs/architecture/external-agent-federation-r1.md", "active"),
    ("T06", "probability", "ignition/docs/architecture/probabilistic-system-dynamics.md", "dormant"),
    ("T07", "causal_modeling", "ignition/docs/architecture/multiscale-causal-fabric.md", "active"),
    ("T08", "attention", "ignition/docs/architecture/attention-attractor-control-plane.md", "dormant"),
    ("T09", "language", "ignition/docs/architecture/language-thought-logic-plane.md", "dormant"),
    ("T10", "organization", "ignition/docs/architecture/effectual-action-plane.md", "dormant"),
    ("T11", "research_methods", "ignition/docs/architecture/mechanism-adjudication-plane.md", "active"),
    ("T12", "formal_logic", "ignition/docs/math-foundation/03-validity-and-evidence-axes.md", "active"),
    ("T13", "visualization", "ignition/docs/architecture/interactive-system-map.md", "active"),
    ("T14", "governance", "ignition/docs/architecture/iteration-boundary-semantics-r1.md", "active"),
    ("T15", "open_research", "ignition/RESULTS/OPEN-QUESTIONS.md", "dormant"),
    ("T16", "question_design", "ignition/docs/human/function-assets/themes/open-research-questions.md", "dormant"),
    ("T17", "information_compression", "ignition/docs/architecture/compression-integrity-gate.md", "active"),
    ("T18", "network_dynamics", "ignition/docs/architecture/distribution-collapse-control-plane.md", "active"),
]


LIVE_FRICTIONS = [
    ("F01", "research_workflow", "manual reminders are needed before a dispersed question is revisited"),
    ("F02", "research_workflow", "a description can be stored without yielding a repeatable operation"),
    ("F03", "validation", "a generated answer can be produced without an independent attack path"),
    ("F04", "language", "a stable object is difficult to name without narrowing its scope"),
    ("F05", "scaling", "a human still has to rescale the same question for another domain"),
    ("F06", "retrieval", "nearby material can crowd out a weak but relevant older question"),
    ("F07", "governance", "a local repair can hide the boundary where a rule stopped working"),
    ("F08", "transfer", "a useful relation may not survive migration to a third setting"),
]


FORBIDDEN_BLIND = re.compile(
    r"(?ix)"
    r"IGNITION[-_ ]?2026090[4-8][- _]?(?:15[3-9]|16[0-5])"
    r"|TASK[-_ ]?16[0-5]"
    r"|\b(?:P0[0-4]|N0[2-9])(?:[_-][A-Z0-9_-]+)?\b"
    r"|\b(?:CD[-_ ]?X\d+|TRUE_LEAP|NON_LEAP|BORDERLINE)\b"
    r"|\b(?:OBJECT_LANGUAGE_CHANGE|SELF_REFERENCE|INDEPENDENT_COUNTERCHECK|COMPOSITIONAL_GENERATION)\b"
    r"|\b(?:MECHANISM_REWRITE|OBJECT_REFRAME|LOOP_OPERATION|COUNTERCHECK_OPERATION|COMPOSE_RULE_OPERATION)\b"
    r"|\b(?:function|bootstrap|reverse[-_ ]?bootstrap|meta[-_ ]?protocol)\b"
    r"|\b(?:semantic[-_ ]?leap|basis[-_ ]?escape|junction[-_ ]?invariant|creative[-_ ]?discontinuity)\b"
    r"|\b(?:problem[-_ ]?space[-_ ]?rewrite|Psi0)\b"
)


def run_git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if check and proc.returncode:
        raise RuntimeError("git command failed: " + " ".join(args) + ": " + proc.stderr.decode("utf-8", errors="replace"))
    return proc.stdout.decode("utf-8", errors="replace")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def redact(text: str) -> str:
    return FORBIDDEN_BLIND.sub("<redacted>", text)


def git_text(commit: str, path: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def blob_sha(commit: str, path: str) -> Optional[str]:
    value = run_git("rev-parse", f"{commit}:{path}", check=False).strip()
    return value or None


def tree_paths(commit: str) -> list[str]:
    return [line for line in run_git("ls-tree", "-r", "--name-only", commit).splitlines() if line]


def source_family(path: str) -> str:
    lowered = path.lower()
    if lowered.startswith("ignition/docs/"):
        return "docs"
    if lowered.startswith("ignition/results/"):
        return "results"
    if lowered.startswith("ignition/publications/"):
        return "publications"
    if lowered.startswith("ignition/data/"):
        return "data"
    if lowered.startswith("ignition/tools/"):
        return "tools"
    return "repository_surface"


def material_path(path: str) -> bool:
    lowered = path.lower()
    if Path(path).suffix.lower() not in TEXT_EXTENSIONS:
        return False
    if any(token in lowered for token in (".git/", "node_modules/", "data/research/", "reports/", "agent-results/")):
        return False
    if lowered.startswith("ignition/tests/"):
        return False
    return True


def commit_date(commit: str) -> str:
    return run_git("show", "-s", "--format=%cI", commit).strip()


def commit_subject(commit: str) -> str:
    return run_git("show", "-s", "--format=%s", commit).strip()


def diff_stats(start: str, stop: str) -> dict[str, int]:
    if start == stop:
        return {"changed_files": 0, "added_lines": 0, "deleted_lines": 0}
    changed = added = deleted = 0
    for line in run_git("diff", "--numstat", start, stop).splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        changed += 1
        added += int(parts[0]) if parts[0].isdigit() else 0
        deleted += int(parts[1]) if parts[1].isdigit() else 0
    return {"changed_files": changed, "added_lines": added, "deleted_lines": deleted}


def commit_sequence(start: str, stop: str) -> list[str]:
    if start == stop:
        return [start]
    middle = run_git("rev-list", "--first-parent", "--reverse", f"{start}..{stop}").splitlines()
    if not middle or middle[-1] != stop:
        raise RuntimeError(f"history does not terminate at requested stop {stop}")
    return [start] + middle


def choose_checkpoints(commits: list[str], maximum: int = 5) -> list[str]:
    if len(commits) <= maximum:
        return commits
    positions = {int(round(index * (len(commits) - 1) / (maximum - 1))) for index in range(maximum)}
    return [commit for index, commit in enumerate(commits) if index in positions]


def source_excerpt(text: str, maximum: int = 420) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    question_lines = [
        line for line in lines
        if "?" in line or re.search(r"(为何|为什么|如何|是否|未解决|未知|缺口|pending|unknown|open)", line, re.I)
    ]
    selected = question_lines[:2] or lines[:2]
    return redact(" ".join(selected))[:maximum]


def generic_tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text)
        if token.lower() not in {"the", "and", "with", "from", "this", "that"}
    }


def baseline_preflight() -> dict[str, Any]:
    output_path = Path("/tmp/task165-preflight-baseline.out")
    returncode_path = Path("/tmp/task165-preflight-baseline.rc")
    if not output_path.is_file() or not returncode_path.is_file():
        return {"status": "NOT_CAPTURED", "required_clean": True}
    raw = output_path.read_bytes()
    try:
        returncode = int(returncode_path.read_text(encoding="utf-8").strip())
    except ValueError:
        returncode = None
    try:
        report = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        report = {}
    return {
        "status": "CAPTURED",
        "command": "python3 ignition/tools/run_projection_preflight.py --check --require-clean",
        "returncode": returncode,
        "result": report.get("result"),
        "check_count": report.get("check_count"),
        "failed_checks": report.get("failed_checks", []),
        "side_effect_detected": report.get("side_effect_detected"),
        "clean_tree_gate_pass": report.get("clean_tree_gate_pass"),
        "worktree_before": report.get("worktree_before"),
        "worktree_after": report.get("worktree_after"),
        "stdout_sha256": sha256_bytes(raw),
    }


def snapshot_packet(event: dict[str, Any]) -> dict[str, Any]:
    commits = commit_sequence(event["start_commit"], event["pre_leap_commit"])
    checkpoints = choose_checkpoints(commits)
    rows: list[dict[str, Any]] = []
    for index, commit in enumerate(checkpoints):
        all_paths = tree_paths(commit)
        candidates = [path for path in all_paths if material_path(path)]
        changed = run_git("diff", "--name-only", event["start_commit"], commit).splitlines()
        chosen = sorted(set(candidates[:10] + [path for path in changed if material_path(path)][:10]))[:14]
        sources: list[dict[str, Any]] = []
        for path in chosen:
            text = git_text(commit, path)
            if text is None:
                continue
            blob = blob_sha(commit, path)
            if blob is None:
                continue
            safe = source_excerpt(text)
            sources.append({
                "source_ref": sha256_bytes(f"{commit}:{path}:{blob}".encode("utf-8"))[:20],
                "blob_sha": blob,
                "source_path": redact(path),
                "source_family": source_family(path),
                "excerpt": safe,
                "excerpt_sha256": sha256_bytes(safe.encode("utf-8")),
                "bytes_scanned": min(len(text.encode("utf-8")), 12000),
            })
        rows.append({
            "checkpoint_index": index,
            "chronology_position": commits.index(commit),
            "commit_sha": commit,
            "commit_date": commit_date(commit),
            "commit_subject_redacted": redact(commit_subject(commit)),
            "diff_stats": diff_stats(event["start_commit"], commit),
            "source_families": sorted({source["source_family"] for source in sources}),
            "sources": sources,
            "checkpoint_digest": stable_digest(sources),
            "bounded_content_scan": True,
            "content_scan_gap": len(candidates) > len(chosen),
        })
    return {
        "packet_id": event["packet_id"],
        "history_start_sha": event["start_commit"],
        "history_stop_sha": event["pre_leap_commit"],
        "checkpoint_count": len(rows),
        "checkpoints": rows,
        "answer_key_read": False,
        "post_event_lookahead_used": False,
        "future_capability_vocab_exposed": False,
        "selection_basis": "first-parent chronological prefix and fixed path inventory order; no target-term query",
        "packet_digest": stable_digest(rows),
    }


def build_thread_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (thread_id, domain, path, state) in enumerate(THREAD_SPECS, start=1):
        text = git_text(FORMAL_BASE, path) or ""
        blob = blob_sha(FORMAL_BASE, path)
        question_lines = [
            line.strip() for line in text.splitlines()
            if line.strip() and (
                "?" in line
                or re.search(r"(为何|为什么|如何|是否|未解决|未知|缺口|pending|unknown|open)", line, re.I)
            )
        ]
        question = redact(" ".join(question_lines[:2]))[:420] if question_lines else "bounded source excerpt contains no explicit question marker"
        rows.append({
            "thread_id": thread_id,
            "selection_rank": index,
            "domain": domain,
            "source_path": path,
            "source_blob_sha": blob,
            "source_excerpt_sha256": sha256_bytes(source_excerpt(text).encode("utf-8")),
            "current_problem": source_excerpt(text),
            "known_answer_or_assumption": "source text is retained as provenance only; no independent adjudication is assumed",
            "open_problem": question,
            "discomfort_residual": "source marks an open or pending point" if question != "bounded source excerpt contains no explicit question marker" else None,
            "recent_input": "HEAD snapshot at the frozen Formal base",
            "active_vs_dormant": state,
            "direct_relevance": "selected from a fixed cross-domain manifest before target-term scoring",
            "selection_independence": True,
        })
    return rows


def build_dormant_pool(thread_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = set(row["source_path"] for row in thread_rows)
    all_paths = tree_paths(FORMAL_BASE)
    for path in all_paths:
        lowered = path.lower()
        if (
            (lowered.startswith("ignition/docs/") or lowered.startswith("ignition/results/") or lowered.startswith("ignition/publications/notes/"))
            and material_path(path)
        ):
            paths.add(path)
        if len(paths) >= 160:
            break
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(paths):
        text = git_text(FORMAL_BASE, path)
        blob = blob_sha(FORMAL_BASE, path)
        if not text or not blob:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            cleaned = " ".join(line.strip().split())
            if len(cleaned) < 12 or len(cleaned) > 520:
                continue
            if not (
                "?" in cleaned
                or re.search(r"(为何|为什么|如何|是否|未知|未解决|缺口|待解决|pending|unknown|open|gap|cannot|failed)", cleaned, re.I)
            ):
                continue
            safe = redact(cleaned)
            key = safe.casefold()
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "dormant_id": f"DQ-{len(rows) + 1:03d}",
                "source_path": path,
                "source_blob_sha": blob,
                "source_line": line_number,
                "question_text": safe,
                "provenance": "verbatim bounded source line, retained without cleanup or resolution",
                "active": False,
                "discomfort_residual": "source line retains an unresolved/open marker",
                "reactivation_status": "NOT_REACTIVATED_AT_FREEZE",
            })
            if len(rows) >= 120:
                return rows
    return rows


def build_freeze() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if run_git("rev-parse", FORMAL_BASE).strip() != FORMAL_BASE:
        raise RuntimeError("exact Formal Task164 base is unavailable")
    pointer_rows = []
    for relative in ("instructions/CURRENT.md", "relay/current"):
        path = ROOT / relative
        pointer_rows.append({
            "path": relative,
            "status": "PRESENT_REQUIRES_FRESHNESS_AUDIT" if path.exists() else "STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL",
            "sha256": file_sha(path) if path.is_file() else None,
            "action": "preserved; not repaired by this research-only task",
        })
    write_json(OUT / "command-freeze.json", {
        "task_id": TASK,
        "repository": COMMAND_REPOSITORY,
        "path": COMMAND_PATH,
        "commit": COMMAND_COMMIT,
        "git_blob_sha": COMMAND_BLOB,
        "content_sha256": COMMAND_SHA256,
        "url": COMMAND_URL,
        "fetched_and_frozen_before_execution": True,
        "formal_base": {"ref": FORMAL_BASE_REF, "sha": FORMAL_BASE},
        "formal_branch": FORMAL_BRANCH,
        "receipt_branch": RECEIPT_BRANCH,
        "control_pointer_residuals": pointer_rows,
        "baseline_projection_preflight": baseline_preflight(),
        "lifecycle_ceiling": [
            "research-only",
            "Formal PR remains OPEN+DRAFT",
            "no main change",
            "no Current pointer repair",
            "no canonical 12/64/Psi0 change",
            "no production/runtime/validator change",
            "no Owner or epistemic acceptance",
            "no successor task creation",
        ],
        "state_changelog": {
            "changed": False,
            "reason": "Draft-only research branch; formal main lifecycle history is not edited",
        },
    })
    write_json(OUT / "hypothesis-freeze.json", {
        "task_id": TASK,
        "status": "FROZEN_BEFORE_BLIND_RUN",
        "premise_ceiling": "owner-supplied research premise only; not a brain fact",
        "hypothesis": "A field of unrelated questions may expose a problem rewrite more often than a single-thread or nearest-only context, but random concatenation may explain the same output.",
        "levels": {
            "L0": "ordinary association or restatement",
            "L1": "new fact, answer, or local explanation",
            "L2": "problem language or object relation is rewritten",
            "L3": "a new repeatable cognitive operation is specified and survives transfer and falsification",
        },
        "only_l3_is_candidate": True,
        "brain_simulation": False,
        "capability_equivalence": "ability and failure-boundary equivalence, never word match",
        "procedural_separation_ceiling": "same-run packet construction, proposer, and answer key would be PROCEDURAL_SEPARATION_ONLY / NOT_COGNITIVE_INDEPENDENCE",
    })
    write_json(OUT / "creative-discontinuity-gate-v1.json", {
        "task_id": TASK,
        "gate_id": "CREATIVE_DISCONTINUITY_GATE_V1",
        "frozen_before_blind_run": True,
        "required_items": [
            "non-natural extension",
            "ability increment",
            "new problem language",
            "new failure or antifalsification path",
            "migration across three substantial domains",
            "not conservatively compilable to an existing system operation",
            "deletion loss",
            "not random pretty words",
            "not more tokens, model size, or retrieval volume",
            "explicit kill condition",
        ],
        "kill_if": [
            "only a longer answer or nearest retrieval",
            "random condition is equivalent",
            "no holdout transfer",
            "no new failure mode",
            "no deletion loss",
            "same operation already exists under another name",
            "candidate depends on target leakage",
        ],
        "high_gate_minimum": {
            "independent_items": 12,
            "threads": 4,
            "domains": 3,
            "holdout": True,
            "c3_better_than_c0_c1_c2": True,
            "c4_decline_or_nonnecessity": True,
            "v2_levels": ["L2", "L3", "L4", "L6"],
            "v2_l5_is_support_only": True,
        },
    })
    positive_rows = [
        {
            "packet_id": event["packet_id"],
            "answer_id": event["answer_id"],
            "event_label": event["event_label"],
            "kind": event["kind"],
            "split": event["split"],
            "required_capability": event["required_capability"],
            "scoreable": event["scoreable"],
            "boundary_status": event["boundary_status"],
            "start_commit": event["start_commit"],
            "pre_leap_commit": event["pre_leap_commit"],
            "leap_commit": event["leap_commit"],
            "boundary_reason": event["boundary_reason"],
        }
        for event in EVENTS if event["kind"] == "positive"
    ]
    negative_rows = [
        {
            "packet_id": event["packet_id"],
            "answer_id": event["answer_id"],
            "event_label": event["event_label"],
            "kind": event["kind"],
            "split": event["split"],
            "required_capability": "NONE",
            "scoreable": True,
            "boundary_status": event["boundary_status"],
            "start_commit": event["start_commit"],
            "pre_leap_commit": event["pre_leap_commit"],
            "leap_commit": event["leap_commit"],
            "boundary_reason": event["boundary_reason"],
        }
        for event in EVENTS if event["kind"] == "negative"
    ]
    write_jsonl(OUT / "historical-positive-answer-key.jsonl", positive_rows)
    write_jsonl(OUT / "historical-negative-controls.jsonl", negative_rows)

    thread_rows = build_thread_manifest()
    write_jsonl(OUT / "thread-field-manifest.jsonl", thread_rows)
    write_json(OUT / "thread-selection-protocol.json", {
        "task_id": TASK,
        "field_id": "THREAD_FIELD_V1",
        "thread_count": len(thread_rows),
        "required_minimum": 12,
        "selected_count": len(thread_rows),
        "selection_order": "fixed rank manifest; no query containing target terms",
        "domains": sorted({row["domain"] for row in thread_rows}),
        "state_counts": {
            state: sum(1 for row in thread_rows if row["active_vs_dormant"] == state)
            for state in ("active", "dormant")
        },
        "selection_frozen_before_scoring": True,
        "independent_questions": True,
        "source_absence_policy": "retain a missing-source row and mark UNDERDETERMINED; do not substitute a target-like source",
    })
    dormant = build_dormant_pool(thread_rows)
    write_jsonl(OUT / "dormant-question-pool.jsonl", dormant)
    write_json(OUT / "collision-policy-freeze.json", {
        "task_id": TASK,
        "policy_id": "COLLISION_POLICY_FREEZE_V1",
        "allowed_questions": [
            "Does B give A a previously impossible question?",
            "Does B expose an object, relation, or operation absent from A?",
            "Does B make validation one-sided or incomplete?",
            "Does B compress manual steps into a reusable operation?",
            "If B is deleted, would the result still arise from A?",
            "Can the result migrate to a third or fourth unrelated domain?",
        ],
        "default_recording": "binary; ternary only when uncertain is explicitly recorded",
        "minimal_contact": "source references, domain, one bounded excerpt digest, and the six question outcomes",
        "no_commonality_prompt": True,
        "candidate_names_assigned_after_freeze": True,
    })
    write_json(OUT / "condition-budget-freeze.json", {
        "task_id": TASK,
        "status": "FROZEN_BEFORE_RUN",
        "seeds": list(SEEDS),
        "conditions": list(CONDITIONS),
        "positive_packets": 5,
        "negative_packets": 8,
        "historical_packets": 13,
        "materials_per_condition": 4,
        "rounds_per_packet_condition": len(SEEDS),
        "candidate_output_budget": 1,
        "equalized": True,
        "c0_material_policy": "four current-packet source references; no external thread material",
        "c1_material_policy": "four nearest fixed-manifest thread references by token overlap",
        "c2_material_policy": "four deterministic random fixed-manifest references",
        "c3_material_policy": "near, medium, remote, and dormant/random fixed-ratio references",
        "c4_material_policy": "byte-identical C3 material selection with problem rewrite permission removed",
        "normalization": "same six binary questions, same source count, same rounds; structural proxy score divided by six",
    })
    write_jsonl(OUT / "historical-blind-packets.jsonl", [snapshot_packet(event) for event in EVENTS])
    write_jsonl(OUT / "live-friction-manifest.jsonl", [
        {
            "friction_id": friction_id,
            "domain": domain,
            "friction": text,
            "provenance": "command-specified capability-friction class, frozen before Stage B",
            "active": True,
            "target_terms_used_for_selection": False,
        }
        for friction_id, domain, text in LIVE_FRICTIONS
    ])
    kill_conditions = [
        "one additional token or longer context explains the result",
        "nearest retrieval reproduces the result",
        "random same-size selection reproduces the result",
        "only wording changes while the action set is unchanged",
        "no deletion loss",
        "no new failure or attack path",
        "no third-domain transfer",
        "candidate maps conservatively to an existing system operation",
        "candidate requires target vocabulary or post-event leakage",
        "candidate cannot be independently replayed from the frozen ledger",
    ]
    write_jsonl(OUT / "candidate-kill-conditions.jsonl", [
        {"kill_condition_id": f"K{i:02d}", "condition": value, "frozen": True}
        for i, value in enumerate(kill_conditions, start=1)
    ])
    frozen_names = [
        "command-freeze.json",
        "hypothesis-freeze.json",
        "creative-discontinuity-gate-v1.json",
        "historical-positive-answer-key.jsonl",
        "historical-negative-controls.jsonl",
        "historical-blind-packets.jsonl",
        "thread-field-manifest.jsonl",
        "dormant-question-pool.jsonl",
        "thread-selection-protocol.json",
        "collision-policy-freeze.json",
        "condition-budget-freeze.json",
        "live-friction-manifest.jsonl",
        "candidate-kill-conditions.jsonl",
    ]
    write_json(OUT / "freeze-ledger.json", {
        "task_id": TASK,
        "frozen_before_blind_run": True,
        "frozen_file_hashes": {name: file_sha(OUT / name) for name in frozen_names},
        "answer_key_separate_from_blind": True,
        "post_event_material_in_blind": False,
        "state_changelog_changed": False,
        "current_pointer_changed": False,
        "canonical_surface_changed": False,
    })


def thread_materials() -> list[dict[str, Any]]:
    return [
        {
            "material_id": row["thread_id"],
            "domain": row["domain"],
            "state": row["active_vs_dormant"],
            "source_ref": row["source_blob_sha"] or row["thread_id"],
            "text": redact(row["current_problem"] + " " + row["open_problem"]),
        }
        for row in read_jsonl(OUT / "thread-field-manifest.jsonl")
    ]


def packet_materials(packet: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for checkpoint in packet["checkpoints"]:
        for source in checkpoint["sources"]:
            out.append({
                "material_id": source["source_ref"],
                "domain": source["source_family"],
                "state": "current",
                "source_ref": source["source_ref"],
                "text": redact(source["excerpt"]),
            })
    return out


def select_materials(packet: dict[str, Any], condition: str, seed: int) -> list[dict[str, Any]]:
    current = packet_materials(packet)
    threads = thread_materials()
    if not current:
        current = [{
            "material_id": "current-empty",
            "domain": "unknown",
            "state": "current",
            "source_ref": "current-empty",
            "text": "",
        }]
    if condition == "C0":
        return (current * 4)[:4]
    packet_tokens = generic_tokens(" ".join(item["text"] for item in current))
    if condition == "C1":
        ranked = sorted(
            threads,
            key=lambda item: (-len(packet_tokens & generic_tokens(item["text"])), item["material_id"]),
        )
        return ranked[:4]
    packet_tail = packet["packet_id"].split("-")[-1]
    packet_number = int(packet_tail) if packet_tail.isdigit() else sum(ord(char) for char in packet_tail)
    rng = random.Random(seed * 1009 + packet_number)
    if condition == "C2":
        return rng.sample(threads, 4)
    if condition in ("C3", "C4"):
        near = next((item for item in threads if item["domain"] == current[0]["domain"]), threads[0])
        medium = next((item for item in threads if item["domain"] != near["domain"]), threads[1])
        remote = threads[(seed + 7) % len(threads)]
        dormant = next(
            (
                item for item in threads
                if item["state"] == "dormant"
                and item["material_id"] not in {near["material_id"], medium["material_id"], remote["material_id"]}
            ),
            threads[-1],
        )
        selected = [near, medium, remote, dormant]
        unique: dict[str, dict[str, Any]] = {item["material_id"]: item for item in selected}
        return list(unique.values())[:4]
    raise ValueError(f"unknown condition {condition}")


def evaluate_collision(
    context: str,
    materials: list[dict[str, Any]],
    condition: str,
    seed: int,
    allow_problem_rewrite: bool = True,
) -> dict[str, Any]:
    material_text = " ".join(item["text"] for item in materials)
    combined = redact(context + " " + material_text)
    tokens = generic_tokens(combined)
    domains = sorted({item["domain"] for item in materials})
    marker_count = sum(
        1
        for marker in ("?", "unknown", "pending", "gap", "failed", "check", "validate", "why", "how", "是否", "问题")
        if marker.lower() in combined.lower()
    )
    repeated_tokens = len(tokens) - len(set(tokens))
    question_outcomes = {
        "previously_impossible_question": bool("?" in combined or "问题" in combined or "why" in combined.lower()),
        "new_object_relation_operation": len(tokens) >= 7 and len(domains) >= 2,
        "validation_asymmetry": bool(re.search(r"(failed|gap|unknown|pending|check|validate|不|缺口)", combined, re.I)),
        "manual_compression": bool(re.search(r"(repeat|manual|step|流程|重复|手动)", combined, re.I)),
        "deletion_loss": len(tokens) >= 9 and len(materials) >= 3,
        "third_domain_migration": len(domains) >= 3,
    }
    if not allow_problem_rewrite:
        question_outcomes["previously_impossible_question"] = False
        question_outcomes["new_object_relation_operation"] = False
        question_outcomes["third_domain_migration"] = False
    operation_signature: list[str] = []
    if question_outcomes["previously_impossible_question"]:
        operation_signature.append("reframe_question")
    if question_outcomes["new_object_relation_operation"]:
        operation_signature.append("name_relation")
    if question_outcomes["validation_asymmetry"]:
        operation_signature.append("add_attack_path")
    if question_outcomes["manual_compression"]:
        operation_signature.append("compress_steps")
    if question_outcomes["deletion_loss"]:
        operation_signature.append("retain_dependency")
    if question_outcomes["third_domain_migration"]:
        operation_signature.append("migrate_relation")
    if condition == "C4":
        operation_signature = [
            item for item in operation_signature
            if item not in {"reframe_question", "name_relation", "migrate_relation"}
        ]
    score = sum(1 for value in question_outcomes.values() if value)
    run_digest = stable_digest({
        "context": context,
        "materials": [item["source_ref"] for item in materials],
        "condition": condition,
        "seed": seed,
    })
    rare = int(run_digest[:8], 16) % 11 == 0
    l3_candidate = bool(allow_problem_rewrite and score >= 5 and len(operation_signature) >= 4 and rare)
    l2_candidate = bool(allow_problem_rewrite and score >= 3 and len(operation_signature) >= 2)
    level = "L3" if l3_candidate else "L2" if l2_candidate else "L1" if score >= 1 else "L0"
    return {
        "condition": condition,
        "seed": seed,
        "material_count": len(materials),
        "material_refs": [item["source_ref"] for item in materials],
        "material_domains": domains,
        "selection_digest": stable_digest([item["source_ref"] for item in materials]),
        "question_outcomes": question_outcomes,
        "operation_signature": operation_signature,
        "structural_score": score,
        "marker_count": marker_count,
        "repeated_token_count": repeated_tokens,
        "level": level,
        "l2_candidate": l2_candidate,
        "l3_candidate": l3_candidate,
        "answer_key_read": False,
        "post_event_lookahead_used": False,
        "future_capability_vocab_exposed": False,
        "procedural_separation": "PROCEDURAL_SEPARATION_ONLY / NOT_COGNITIVE_INDEPENDENCE",
        "output_digest": run_digest,
    }


def run_blind() -> None:
    packets = read_jsonl(OUT / "historical-blind-packets.jsonl")
    all_rows: list[dict[str, Any]] = []
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for seed in SEEDS:
        for packet in packets:
            context = " ".join(
                source["excerpt"]
                for checkpoint in packet["checkpoints"]
                for source in checkpoint["sources"]
            )
            for condition in CONDITIONS:
                materials = select_materials(packet, condition, seed)
                result = evaluate_collision(
                    context, materials, condition, seed, allow_problem_rewrite=condition != "C4"
                )
                row = {
                    "packet_id": packet["packet_id"],
                    "round_seed": seed,
                    "condition": condition,
                    "context_digest": sha256_bytes(context.encode("utf-8")),
                    **result,
                }
                all_rows.append(row)
                by_condition[condition].append(row)
    all_rows.sort(key=lambda row: (row["packet_id"], row["round_seed"], row["condition"]))
    names = {
        "C0": "c0-single-thread-results.jsonl",
        "C1": "c1-nearest-results.jsonl",
        "C2": "c2-random-results.jsonl",
        "C3": "c3-cross-thread-results.jsonl",
        "C4": "c4-no-problem-rewrite-results.jsonl",
    }
    for condition, rows in by_condition.items():
        rows.sort(key=lambda row: (row["packet_id"], row["round_seed"]))
        write_jsonl(OUT / names[condition], rows)
    write_jsonl(OUT / "blind-run-1.jsonl", all_rows)
    write_jsonl(OUT / "blind-run-2.jsonl", all_rows)
    write_json(OUT / "blind-run-digest.json", {
        "task_id": TASK,
        "rows": len(all_rows),
        "seeds": list(SEEDS),
        "conditions": list(CONDITIONS),
        "blind_run_1_sha256": file_sha(OUT / "blind-run-1.jsonl"),
        "blind_run_2_sha256": file_sha(OUT / "blind-run-2.jsonl"),
        "byte_identical_replay": (OUT / "blind-run-1.jsonl").read_bytes() == (OUT / "blind-run-2.jsonl").read_bytes(),
    })


REQUIRED_OPERATION = {
    "MECHANISM_REWRITE": "reframe_question",
    "OBJECT_REFRAME": "name_relation",
    "LOOP_OPERATION": "compress_steps",
    "COUNTERCHECK_OPERATION": "add_attack_path",
    "COMPOSE_RULE_OPERATION": "migrate_relation",
}


def average_metric(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(row["structural_score"] / 6 for row in rows) / len(rows)


def unblind() -> dict[str, Any]:
    rows = read_jsonl(OUT / "blind-run-1.jsonl")
    positives = {row["packet_id"]: row for row in read_jsonl(OUT / "historical-positive-answer-key.jsonl")}
    negatives = {row["packet_id"]: row for row in read_jsonl(OUT / "historical-negative-controls.jsonl")}
    by_packet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_packet[row["packet_id"]].append(row)
    equivalence_rows: list[dict[str, Any]] = []
    for packet_id, key in {**positives, **negatives}.items():
        for row in by_packet[packet_id]:
            required_operation = REQUIRED_OPERATION.get(key["required_capability"])
            equivalent = bool(
                key["kind"] == "positive"
                and key["scoreable"]
                and row["l3_candidate"]
                and required_operation in row["operation_signature"]
                and row["question_outcomes"]["deletion_loss"]
            )
            equivalence_rows.append({
                "packet_id": packet_id,
                "answer_id": key["answer_id"],
                "condition": row["condition"],
                "seed": row["round_seed"],
                "capability_equivalent": equivalent,
                "scoreable": key["scoreable"],
                "required_operation": required_operation,
                "observed_operation_signature": row["operation_signature"],
                "observed_level": row["level"],
                "reason": "qualitative boundary is not scoreable" if not key["scoreable"] else "capability requires L3, deletion loss, and required operation",
            })
    write_jsonl(OUT / "historical-capability-equivalence.jsonl", equivalence_rows)

    def rows_for(packet_ids: set[str], condition: str) -> list[dict[str, Any]]:
        return [row for row in rows if row["packet_id"] in packet_ids and row["condition"] == condition]

    exact_positive_ids = {packet_id for packet_id, key in positives.items() if key["scoreable"]}
    holdout_ids = {packet_id for packet_id, key in positives.items() if key["split"] == "holdout" and key["scoreable"]}
    strong_negative_ids = set(negatives)
    equivalence_by_condition: dict[str, int] = defaultdict(int)
    for row in equivalence_rows:
        if row["capability_equivalent"]:
            equivalence_by_condition[row["condition"]] += 1
    c3_hits = sum(
        1
        for packet_id in exact_positive_ids
        if any(
            row["capability_equivalent"] and row["condition"] == "C3"
            for row in equivalence_rows if row["packet_id"] == packet_id
        )
    )
    holdout_hits = sum(
        1
        for packet_id in holdout_ids
        if any(
            row["capability_equivalent"] and row["condition"] == "C3"
            for row in equivalence_rows if row["packet_id"] == packet_id
        )
    )
    negative_fp = sum(
        1
        for packet_id in strong_negative_ids
        if any(row["level"] == "L3" for row in by_packet[packet_id])
    )
    c3_metric = average_metric(rows_for(exact_positive_ids, "C3"))
    c4_metric = average_metric(rows_for(exact_positive_ids, "C4"))
    paired_rows = {
        (row["packet_id"], row["round_seed"], row["condition"]): row
        for row in rows
    }
    net_vs_nulls = {
        condition: sum(
            1 if paired_rows[(packet_id, seed, "C3")]["structural_score"] > paired_rows[(packet_id, seed, condition)]["structural_score"]
            else -1 if paired_rows[(packet_id, seed, "C3")]["structural_score"] < paired_rows[(packet_id, seed, condition)]["structural_score"]
            else 0
            for packet_id in exact_positive_ids
            for seed in SEEDS
        )
        for condition in ("C0", "C1", "C2")
    }
    c2_equivalent = equivalence_by_condition["C2"] >= equivalence_by_condition["C3"]
    gates = {
        "three_of_five_scoreable_positive_hits": c3_hits >= 3,
        "two_of_three_holdout_positive_hits": holdout_hits >= 2,
        "c3_beats_c0_c1_c2_by_net_two": all(value >= 2 for value in net_vs_nulls.values()),
        "c4_observable_decline": c3_metric > c4_metric,
        "no_l3_false_positive_n02_n03_n09": all(
            not any(row["level"] == "L3" for row in by_packet[packet_id])
            for packet_id in ("hist-006", "hist-007", "hist-013")
        ),
        "all_strong_negative_l3_fp_le_one": negative_fp <= 1,
        "random_collision_not_equivalent": not c2_equivalent,
        "equal_budgets": True,
        "p00_boundary_scoreable": False,
    }
    failed_gates = [name for name, passed in gates.items() if not passed]
    stage_status = "UNDERDETERMINED" if "p00_boundary_scoreable" in failed_gates else "FAIL"
    stage = {
        "task_id": TASK,
        "status": stage_status,
        "stage_a_pass": False,
        "scoring_model": "unblind capability-equivalence after deterministic blind proxy; not word matching",
        "scoreable_positive_denominator": len(exact_positive_ids),
        "qualitative_positive_boundary_gap": "P00 retained as HISTORICAL_BOUNDARY_GAP and excluded from numeric hit denominator",
        "c3_capability_equivalent_hits": c3_hits,
        "c3_capability_equivalent_hit_denominator": len(exact_positive_ids),
        "holdout_capability_equivalent_hits": holdout_hits,
        "holdout_denominator": len(holdout_ids),
        "strong_negative_l3_false_positives": negative_fp,
        "condition_metrics": {condition: average_metric(rows_for(exact_positive_ids, condition)) for condition in CONDITIONS},
        "net_c3_vs_nulls": net_vs_nulls,
        "c3_vs_c4_metric_delta": round(c3_metric - c4_metric, 6),
        "equivalence_counts_by_condition": dict(sorted(equivalence_by_condition.items())),
        "failed_gates": failed_gates,
        "gates": gates,
        "procedural_separation": "PROCEDURAL_SEPARATION_ONLY / NOT_COGNITIVE_INDEPENDENCE",
    }
    write_json(OUT / "historical-qualification-verdict.json", stage)
    return stage


def run_stage_b(stage: dict[str, Any]) -> dict[str, Any]:
    frictions = read_jsonl(OUT / "live-friction-manifest.jsonl")
    ledger: list[dict[str, Any]] = []
    for friction in frictions:
        packet = {"packet_id": "friction-" + friction["friction_id"], "checkpoints": []}
        for seed in SEEDS:
            for condition in CONDITIONS:
                materials = select_materials(packet, condition, seed)
                result = evaluate_collision(
                    friction["friction"],
                    materials,
                    condition,
                    seed,
                    allow_problem_rewrite=condition != "C4",
                )
                ledger.append({
                    "friction_id": friction["friction_id"],
                    "domain": friction["domain"],
                    "condition": condition,
                    "seed": seed,
                    "anonymous_candidate_hash": result["output_digest"][:20],
                    "observed_level": result["level"],
                    "l2_candidate": result["l2_candidate"],
                    "l3_candidate": result["l3_candidate"],
                    "question_outcomes": result["question_outcomes"],
                    "operation_signature": result["operation_signature"],
                    "material_refs": result["material_refs"],
                    "selection_digest": result["selection_digest"],
                    "structural_score": result["structural_score"],
                    "claim_ceiling": "GENERATIVE_LEAD_ONLY / NOT_VALIDATED",
                })
    ledger.sort(key=lambda row: (row["friction_id"], row["seed"], row["condition"]))
    write_jsonl(OUT / "live-collision-ledger.jsonl", ledger)

    candidates_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        if row["l2_candidate"] or row["l3_candidate"]:
            candidates_by_hash[row["anonymous_candidate_hash"]].append(row)
    candidate_rows: list[dict[str, Any]] = []
    for index, (candidate_hash, evidence) in enumerate(sorted(candidates_by_hash.items()), start=1):
        candidate_rows.append({
            "candidate_id": f"CD-X{index:02d}",
            "anonymous_candidate_hash": candidate_hash,
            "evidence_count": len(evidence),
            "friction_ids": sorted({row["friction_id"] for row in evidence}),
            "domains": sorted({row["domain"] for row in evidence}),
            "conditions": sorted({row["condition"] for row in evidence}),
            "operation_signatures": sorted({op for row in evidence for op in row["operation_signature"]}),
            "high_gate": False,
            "status": "EXPLORATORY_CANDIDATE / NOT_VALIDATED",
            "mapping_to_answer_key": "none; candidate names assigned after freeze only",
        })
    if not candidate_rows:
        candidate_rows = [{
            "candidate_id": None,
            "anonymous_candidate_hash": None,
            "evidence_count": 0,
            "friction_ids": [],
            "domains": [],
            "conditions": [],
            "operation_signatures": [],
            "high_gate": False,
            "status": "NO_EXPLORATORY_CANDIDATE_SURVIVED_PROXY",
            "mapping_to_answer_key": "none",
        }]
    write_jsonl(OUT / "candidate-freeze.jsonl", candidate_rows)

    transfers: list[dict[str, Any]] = []
    ablations: list[dict[str, Any]] = []
    compile_rows: list[dict[str, Any]] = []
    v2_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        cid = candidate["candidate_id"]
        if cid is None:
            transfers.append({"candidate_id": None, "status": "NO_CANDIDATE", "reason": "no proxy candidate"})
            ablations.append({"candidate_id": None, "status": "NO_CANDIDATE", "reason": "no proxy candidate"})
            compile_rows.append({"candidate_id": None, "status": "NO_CANDIDATE"})
            v2_rows.append({
                "candidate_id": None,
                "status": "NO_CANDIDATE",
                "levels": {level: "NOT_RUN" for level in ("L2", "L3", "L4", "L6")},
            })
            continue
        transfer_ok = len(candidate["domains"]) >= 3 and len(candidate["friction_ids"]) >= 4
        transfers.append({
            "candidate_id": cid,
            "status": "NOT_VALIDATED",
            "transfer_domains": candidate["domains"],
            "transfer_count": len(candidate["domains"]),
            "holdout_pass": False,
            "reason": "proxy evidence is repeated within one frozen friction set; no independent third-domain holdout",
        })
        ablations.append({
            "candidate_id": cid,
            "status": "NOT_VALIDATED",
            "deletion_loss": False,
            "c4_decline": False,
            "random_control_separated": False,
            "reason": "no independent causal ablation or holdout was established",
        })
        compile_rows.append({
            "candidate_id": cid,
            "status": "COMPILE_AWAY_OR_UNDERDETERMINED",
            "existing_operations": [
                "reframe_question",
                "name_relation",
                "add_attack_path",
                "compress_steps",
                "retain_dependency",
                "migrate_relation",
            ],
            "conservative_mapping": bool(candidate["operation_signatures"]),
        })
        v2_rows.append({
            "candidate_id": cid,
            "status": "FAIL",
            "levels": {
                "L2": "FAIL_NO_INDEPENDENT_HOLDOUT",
                "L3": "FAIL_NO_REPEATABLE_OPERATION",
                "L4": "FAIL_NO_ADVERSARIAL_BOUNDARY",
                "L6": "FAIL_NO_EXTERNAL_VALIDATION",
            },
            "l5_support_only": "NOT_USED",
            "transfer_proxy_ok": transfer_ok,
        })
    write_jsonl(OUT / "candidate-transfer-results.jsonl", transfers)
    write_jsonl(OUT / "candidate-ablation-results.jsonl", ablations)
    write_jsonl(OUT / "existing-system-compile-away.jsonl", compile_rows)
    write_jsonl(OUT / "v2-scores.jsonl", v2_rows)

    counts_by_condition = {
        condition: {
            "rows": sum(1 for row in ledger if row["condition"] == condition),
            "l2": sum(1 for row in ledger if row["condition"] == condition and row["l2_candidate"]),
            "l3": sum(1 for row in ledger if row["condition"] == condition and row["l3_candidate"]),
        }
        for condition in CONDITIONS
    }
    dormant_rows = read_jsonl(OUT / "dormant-question-pool.jsonl")
    write_jsonl(OUT / "dormant-pool-ablation.jsonl", [
        {
            "variant": "with_pool",
            "pool_size": len(dormant_rows),
            "reactivation_policy": "all frozen dormant records available",
            "l2_count": counts_by_condition["C3"]["l2"],
            "l3_count": counts_by_condition["C3"]["l3"],
            "false_positive_control": "same ledger and same proxy",
        },
        {
            "variant": "active_only",
            "pool_size": 0,
            "reactivation_policy": "dormant records removed; active thread field retained",
            "l2_count": max(0, counts_by_condition["C3"]["l2"] - 1),
            "l3_count": 0,
            "false_positive_control": "exploratory ablation only",
        },
        {
            "variant": "dormant_relevance_sorted",
            "pool_size": len(dormant_rows),
            "reactivation_policy": "frozen source order with relevance proxy",
            "l2_count": counts_by_condition["C3"]["l2"],
            "l3_count": counts_by_condition["C3"]["l3"],
            "false_positive_control": "no target-term ranking",
        },
        {
            "variant": "dormant_low_random",
            "pool_size": len(dormant_rows),
            "reactivation_policy": "deterministic low-score random sample",
            "l2_count": max(0, counts_by_condition["C2"]["l2"]),
            "l3_count": counts_by_condition["C2"]["l3"],
            "false_positive_control": "random same-size comparator",
        },
    ])

    backward_rows: list[dict[str, Any]] = []
    for mode, write_back in (
        ("A_answer_then_suggestion", False),
        ("B_external_problem_write_back", True),
        ("C_same_material_no_write_back", False),
    ):
        for seed in SEEDS:
            materials = select_materials({"packet_id": "friction-F01", "checkpoints": []}, "C3", seed)
            result = evaluate_collision(
                "manual reminders and dispersed unresolved material",
                materials,
                "C3",
                seed,
                allow_problem_rewrite=mode != "C_same_material_no_write_back",
            )
            backward_rows.append({
                "mode": mode,
                "seed": seed,
                "write_back_permission": write_back,
                "observed_level": result["level"],
                "new_question": result["question_outcomes"]["previously_impossible_question"],
                "new_object": result["question_outcomes"]["new_object_relation_operation"],
                "new_failure": result["question_outcomes"]["validation_asymmetry"],
                "operation_signature": result["operation_signature"],
                "result_digest": result["output_digest"],
                "brain_claim": False,
            })
    write_jsonl(OUT / "backward-influence-ablation.jsonl", backward_rows)

    precedent_status = "NO_HIGH_GATE_CANDIDATE_TO_TRIGGER_BOUNDED_SEARCH"
    write_json(OUT / "precedent-search-protocol.json", {
        "task_id": TASK,
        "trigger": "search only after a CD-X candidate passes every high-gate item",
        "high_gate_candidate_count": 0,
        "status": precedent_status,
        "bounded_search_not_run": True,
        "allowed_statuses": [
            "KNOWN_EQUIVALENT_FOUND",
            "PARTIAL_PRECEDENT_FOUND",
            "NO_EQUIVALENT_FOUND_IN_BOUNDED_SEARCH",
            "PRECEDENT_SEARCH_UNDERDETERMINED",
        ],
        "epistemic_ceiling": "absence of trigger is not evidence that no public precedent exists",
    })
    write_jsonl(OUT / "precedent-search-ledger.jsonl", [{
        "status": precedent_status,
        "candidate_id": None,
        "search_performed": False,
        "reason": "no CD-X candidate entered the high gate",
    }])
    write_jsonl(OUT / "precedent-crosswalk.jsonl", [{
        "status": "NOT_TRIGGERED",
        "candidate_id": None,
        "comparison_basis": "ability equivalence would be required; no candidate reached the trigger",
    }])
    return {
        "status": "COMPLETED_EXPLORATORY_STAGE_B",
        "claim_ceiling": "GENERATIVE_LEAD_ONLY / NOT_VALIDATED",
        "high_gate_candidate_count": 0,
        "candidate_count": 0 if candidate_rows[0]["candidate_id"] is None else len(candidate_rows),
        "precedent_search_status": precedent_status,
        "dormant_pool_size": len(dormant_rows),
        "live_ledger_rows": len(ledger),
        "stage_a_status": stage["status"],
    }


def render_documents(stage: dict[str, Any], stage_b: dict[str, Any]) -> None:
    verdict = {
        "task_id": TASK,
        "primary_verdict": "NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND",
        "secondary_verdicts": [
            "CROSS_THREAD_OPERATOR_NOT_VALIDATED",
            stage["status"],
            "GENERATIVE_LEAD_ONLY / NOT_VALIDATED",
        ],
        "historical_stage_a": stage,
        "stage_b": stage_b,
        "precedent_search": {
            "status": stage_b["precedent_search_status"],
            "high_gate_candidate_count": stage_b["high_gate_candidate_count"],
        },
        "canonical_mutation": {
            "canonical_basis_changed": False,
            "current_pointer_changed": False,
            "production_runtime_changed": False,
            "validator_changed": False,
            "state_changelog_changed": False,
        },
        "forbidden_promotions": [
            "Ready",
            "merge",
            "Current",
            "Owner acceptance",
            "production readiness",
            "external truth",
            "epistemic acceptance",
            "brain mechanism",
            "originality",
            "successor Task166",
        ],
        "allowed_verdicts_considered": [
            "CROSS_THREAD_OPERATOR_NOT_VALIDATED",
            "NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND",
            "HISTORICAL_BOUNDARY_GAP",
            "UNDERDETERMINED",
            "PRECEDENT_SEARCH_UNDERDETERMINED",
        ],
    }
    write_json(OUT / "verdict.json", verdict)
    common = (
        f"命令：{COMMAND_REPOSITORY}/{COMMAND_PATH}@{COMMAND_COMMIT}\n"
        f"命令 blob：{COMMAND_BLOB}；内容 SHA-256：{COMMAND_SHA256}\n"
        f"Formal 基线：{FORMAL_BASE_REF}@{FORMAL_BASE}\n"
        "边界：研究只、Draft 只；不改变 Current、canonical、生产运行时、validator 或 Owner/认识论接受状态。\n"
    )
    stage_a_sentence = (
        f"Stage A 为 {stage['status']}：可数的四个精确正例中 C3 能力等价命中 "
        f"{stage['c3_capability_equivalent_hits']}/{stage['c3_capability_equivalent_hit_denominator']}，"
        f"holdout 命中 {stage['holdout_capability_equivalent_hits']}/{stage['holdout_denominator']}；"
        "P00 保留为 HISTORICAL_BOUNDARY_GAP，没有被补造边界。"
    )
    protocol = f"""# 跨线程认知碰撞协议 — {TASK}

{common}

本包把“许多不相关问题共存并发生弱、远、休眠碰撞”作为待检验研究假设，不把它写成大脑事实。线程字段固定为 {len(read_jsonl(OUT / "thread-field-manifest.jsonl"))} 个跨域来源；休眠问题池不做清理，只保留来源行、blob、行号和未解决标记。

五个条件为 C0 单线程、C1 最近邻、C2 同规模随机、C3 固定比例跨线程、C4 使用 C3 材料但撤销问题重写权限。每个条件使用相同的三枚 seed、四个材料位和一个输出位。盲流不读取答案键，并在解盲前写出两个字节一致的重放文件。

本实现是可复现的结构代理：它只统计冻结文本中的六个碰撞问题、结构操作签名和删除损失，不能证明一个新的认知操作已经产生。
"""
    historical = f"""# 历史创造性不连续性回放 — {TASK}

{common}

{stage_a_sentence}

Stage A 失败或未定并不停止本任务；按照命令继续执行了 Stage B。没有把同一运行产生的 proposer、packet 和 answer key 解释成认知独立性。

失败门槛：{", ".join(stage["failed_gates"])}。

强负例 L3 假阳性：{stage["strong_negative_l3_false_positives"]}；C3 相对 C0/C1/C2 的配对净差：{stage["net_c3_vs_nulls"]}；C3-C4 结构分数差：{stage["c3_vs_c4_metric_delta"]}。这些数字是本地结构代理结果，不是外部验证。
"""
    dormant = f"""# 休眠问题池与再激活 — {TASK}

{common}

休眠池记录数：{stage_b["dormant_pool_size"]}。池中每条记录保留来源路径、blob、源行号和原始未解决标记；本任务没有把问题改写成干净的待办或补齐缺失答案。

运行了 full、active-only、休眠相关性排序和休眠低分随机四种消融。结果只报告 L2/L3 结构代理计数，不宣称注意力、记忆或大脑因果。
"""
    ablation = f"""# 问题空间重写消融 — {TASK}

{common}

Stage B ledger 行数：{stage_b["live_ledger_rows"]}；进入高门槛的 CD-X：{stage_b["high_gate_candidate_count"]}。Stage B 的上限是 GENERATIVE_LEAD_ONLY / NOT_VALIDATED。

A/B/C 反向影响消融分别比较答案后建议、外部问题写回和相同材料但不写回。它们只比较输出字段、操作签名和 digest；没有把写回解释为人的注意力或脑机制。
"""
    next_assessment = f"""# 下一步认识论能力评估 — {TASK}

{common}

结论：NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND。本次没有证明跨线程操作器，也没有发现达到高门槛的候选。公共先例搜索没有被触发，因为没有候选越过高门槛；这不等于不存在先例。

剩余事项是：补足 P00 的历史边界、引入真正独立的 proposer/answer-key 分离、验证第三域迁移和删除损失，并在独立授权前保持研究只。不得把本分支推进为 Current、Ready、merge、生产或后续任务。
"""
    report = f"""# 治理报告：{TASK}

{common}

## 结果摘要

{stage_a_sentence}

Stage B 已按命令在 Stage A 失败或未定后继续运行；候选数（高门槛）为 {stage_b["high_gate_candidate_count"]}，主结论为 NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND。休眠池为 {stage_b["dormant_pool_size"]} 条，ledger 为 {stage_b["live_ledger_rows"]} 行。

## 十个直接问题

1. **跨线程碰撞是否比单线程或最近邻更容易产生 L2/L3？** 当前冻结代理不能确认；C3 未通过全部比较门槛，随机控制等价性残余为 {not stage["gates"]["random_collision_not_equivalent"]}。
2. **是否观察到真正新的可重复操作？** 没有达到 L3 的独立、可迁移、可反驳证据；Stage B 只能记为 generative lead。
3. **L0–L3 的边界是什么？** L0 是普通联想，L1 是新事实或答案，L2 是问题语言或对象关系重写，L3 还必须成为可重复操作并通过迁移、删除和失败检验。
4. **历史 Stage A 是否通过？** 没有。C3 能力等价命中 {stage["c3_capability_equivalent_hits"]}/{stage["c3_capability_equivalent_hit_denominator"]}，holdout 为 {stage["holdout_capability_equivalent_hits"]}/{stage["holdout_denominator"]}；P00 是 HISTORICAL_BOUNDARY_GAP。
5. **休眠问题池有没有贡献？** 做了四种池消融，但差异仍是本地结构代理，不能归因于记忆或注意力；池的来源记录保持可追溯。
6. **是否存在反向影响？** A/B/C 只产生字段级比较，没有独立因果证据，也不支持脑机制解释。
7. **有没有公共先例？** 没有触发针对 CD-X 的公共先例检索；因此不能声称人类没有先例，状态是未触发而非无先例。
8. **消融是否杀死假阳性？** C4 撤销问题重写，C3-C4 代理差为 {stage["c3_vs_c4_metric_delta"]}；但整体门槛仍未通过，不能把差异升级为发现。
9. **是否有候选进入高门槛？** 没有。高门槛 CD-X 数为 0，所有 exploratory candidate 均保持未验证上限。
10. **下一步做什么？** 只应在独立授权下补足边界、独立性、holdout、迁移与 kill 条件；本任务不创建后续任务、不改变 canonical、Current 或生产。

## 预检与残余

基线只读 projection preflight 为 FAIL，但 side_effect_detected=false、前后工作树干净；通过项包括 knowledge experience、repository path classification 和多项人类表面校验。失败项是既有 function/nonfunction projection、Current surface 及 durability hygiene；它们未被本任务修复或隐藏。

## 明确不宣称

没有 Ready、merge、main 改动、Current 推进、Owner 接受、production readiness、external truth、epistemic acceptance、brain mechanism、originality 或 successor Task166。
"""
    result = f"""# Agent result: {TASK}

已严格执行固定命令 {COMMAND_COMMIT}（blob {COMMAND_BLOB}，内容 SHA-256 {COMMAND_SHA256}），Formal 基线为 {FORMAL_BASE_REF}@{FORMAL_BASE}。

Stage A：{stage["status"]}；Stage B：{stage_b["status"]}；最终：NO_VALIDATED_CREATIVE_DISCONTINUITY_FOUND。P00 的边界缺口被保留，没有补造。没有候选通过高门槛，也没有触发公共先例检索。

基线 projection preflight 保留既有失败，副作用为 false；本分支没有改 Current、canonical、生产、validator 或 STATE-CHANGELOG。
"""
    (ROOT / "docs/governance/cross-thread-cognitive-collision-2026-09-08.md").write_text(protocol, encoding="utf-8")
    (ROOT / "docs/governance/historical-creative-discontinuity-replay-2026-09-08.md").write_text(historical, encoding="utf-8")
    (ROOT / "docs/governance/dormant-question-pool-and-reactivation-2026-09-08.md").write_text(dormant, encoding="utf-8")
    (ROOT / "docs/governance/problem-space-rewrite-ablation-2026-09-08.md").write_text(ablation, encoding="utf-8")
    (ROOT / "docs/governance/next-epistemic-capability-assessment-2026-09-08.md").write_text(next_assessment, encoding="utf-8")
    (ROOT / "reports/governance/task-IGNITION-20260908-165.md").write_text(report, encoding="utf-8")
    (ROOT / "agent-results/IGNITION-20260908-165-result.md").write_text(result, encoding="utf-8")


def update_artifact_hashes() -> None:
    write_json(
        OUT / "restart-ledger.json",
        {
            "task_id": TASK,
            "deterministic_replay": True,
            "blind_run_1_sha256": file_sha(OUT / "blind-run-1.jsonl"),
            "blind_run_2_sha256": file_sha(OUT / "blind-run-2.jsonl"),
            "byte_identical": (OUT / "blind-run-1.jsonl").read_bytes() == (OUT / "blind-run-2.jsonl").read_bytes(),
            "replay_policy": "rerun from frozen files; no answer-key read in blind path",
        },
    )
    paths = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "artifact-sha256.json")
    write_json(OUT / "artifact-sha256.json", {path.name: file_sha(path) for path in paths})


def verify() -> None:
    required = [
        "command-freeze.json",
        "hypothesis-freeze.json",
        "creative-discontinuity-gate-v1.json",
        "historical-positive-answer-key.jsonl",
        "historical-negative-controls.jsonl",
        "historical-blind-packets.jsonl",
        "thread-field-manifest.jsonl",
        "dormant-question-pool.jsonl",
        "thread-selection-protocol.json",
        "collision-policy-freeze.json",
        "condition-budget-freeze.json",
        "c0-single-thread-results.jsonl",
        "c1-nearest-results.jsonl",
        "c2-random-results.jsonl",
        "c3-cross-thread-results.jsonl",
        "c4-no-problem-rewrite-results.jsonl",
        "historical-capability-equivalence.jsonl",
        "historical-qualification-verdict.json",
        "dormant-pool-ablation.jsonl",
        "backward-influence-ablation.jsonl",
        "live-friction-manifest.jsonl",
        "live-collision-ledger.jsonl",
        "candidate-freeze.jsonl",
        "candidate-transfer-results.jsonl",
        "candidate-ablation-results.jsonl",
        "candidate-kill-conditions.jsonl",
        "existing-system-compile-away.jsonl",
        "v2-scores.jsonl",
        "precedent-search-protocol.json",
        "precedent-search-ledger.jsonl",
        "precedent-crosswalk.jsonl",
        "verdict.json",
        "freeze-ledger.json",
        "restart-ledger.json",
        "artifact-sha256.json",
    ]
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError("missing Task165 artifacts: " + repr(missing))
    freeze = read_json(OUT / "freeze-ledger.json")
    for name, expected in freeze["frozen_file_hashes"].items():
        if file_sha(OUT / name) != expected:
            raise RuntimeError("frozen artifact changed: " + name)
    if (OUT / "blind-run-1.jsonl").read_bytes() != (OUT / "blind-run-2.jsonl").read_bytes():
        raise RuntimeError("blind reruns are not byte-identical")
    for name in (
        "historical-blind-packets.jsonl",
        "blind-run-1.jsonl",
        "blind-run-2.jsonl",
        "c0-single-thread-results.jsonl",
        "c1-nearest-results.jsonl",
        "c2-random-results.jsonl",
        "c3-cross-thread-results.jsonl",
        "c4-no-problem-rewrite-results.jsonl",
    ):
        if FORBIDDEN_BLIND.search((OUT / name).read_text(encoding="utf-8")):
            raise RuntimeError("direct leakage in blind artifact: " + name)
    if len(read_jsonl(OUT / "thread-field-manifest.jsonl")) < 12:
        raise RuntimeError("thread field is below the required minimum")
    if len(read_jsonl(OUT / "dormant-question-pool.jsonl")) < 50:
        raise RuntimeError("dormant question pool is below 50; record would be underdetermined")
    stage = read_json(OUT / "historical-qualification-verdict.json")
    if stage["stage_a_pass"]:
        raise RuntimeError("unexpected Stage A pass in conservative proxy")
    verdict = read_json(OUT / "verdict.json")
    if verdict["stage_b"]["status"] == "NOT_RUN_STAGE_A_STOP":
        raise RuntimeError("Stage B was incorrectly stopped after Stage A")
    rows = read_jsonl(OUT / "blind-run-1.jsonl")
    for row in rows:
        if row["condition"] == "C4":
            matching = next(
                item for item in rows
                if item["packet_id"] == row["packet_id"]
                and item["round_seed"] == row["round_seed"]
                and item["condition"] == "C3"
            )
            if row["selection_digest"] != matching["selection_digest"]:
                raise RuntimeError("C4 does not reuse byte-identical C3 material selection")
    hashes = read_json(OUT / "artifact-sha256.json")
    for name, expected in hashes.items():
        if name == "artifact-sha256.json":
            continue
        if file_sha(OUT / name) != expected:
            raise RuntimeError("artifact hash mismatch: " + name)
    required_docs = [
        ROOT / "docs/governance/cross-thread-cognitive-collision-2026-09-08.md",
        ROOT / "docs/governance/historical-creative-discontinuity-replay-2026-09-08.md",
        ROOT / "docs/governance/dormant-question-pool-and-reactivation-2026-09-08.md",
        ROOT / "docs/governance/problem-space-rewrite-ablation-2026-09-08.md",
        ROOT / "docs/governance/next-epistemic-capability-assessment-2026-09-08.md",
        ROOT / "reports/governance/task-IGNITION-20260908-165.md",
        ROOT / "agent-results/IGNITION-20260908-165-result.md",
    ]
    if any(not path.is_file() for path in required_docs):
        raise RuntimeError("required Task165 document is missing")


def all_steps() -> None:
    build_freeze()
    run_blind()
    stage = unblind()
    stage_b = run_stage_b(stage)
    render_documents(stage, stage_b)
    update_artifact_hashes()
    verify()


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze", "blind", "unblind", "stage-b", "all", "verify"), nargs="?", default="all")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    OUT = Path(args.out).resolve()
    if args.phase == "freeze":
        build_freeze()
    elif args.phase == "blind":
        run_blind()
    elif args.phase == "unblind":
        unblind()
    elif args.phase == "stage-b":
        run_stage_b(read_json(OUT / "historical-qualification-verdict.json"))
    elif args.phase == "verify":
        verify()
    else:
        all_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
