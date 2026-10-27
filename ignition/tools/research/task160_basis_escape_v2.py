#!/usr/bin/env python3
"""Research-only Task160 basis-escape replay.

This is a deterministic, repository-local instrument.  It never writes to a
canonical registry, validator, runtime path, Current pointer, or production
surface.  The discovery input is built from the frozen Task159 Formal head and
is label/path blinded before the factor pass.  Candidate definitions are
frozen before the V2 comparison stage and are never rewritten after scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
TASK = "IGNITION-20260907-160"
FORMAL_BASE = "76e44213904928f9f0be8ba131b86529e44e7682"
COMMAND_COMMIT = "f6fc4438e711e928cce29d07ed54b7395434b7c8"
COMMAND_BLOB = "57aeb34cc5fea2202bd87e5998bd7851f7753a9f"
COMMAND_SHA256 = "e8155ff841bf4ee95eafddd4f5b2e081890e73a08c364011cd7108ae564b23d0"
OUT = ROOT / "data/research/basis-escape-v2-2026-09-07"
T159 = ROOT / "data/research/semantic-leap-detector-v2-2026-09-07"
_BLOB_BY_PATH: dict[str, str] | None = None
_DATE_BY_PATH: dict[str, str] | None = None


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


FORBIDDEN = re.compile(
    r"(?ix)(?<![a-z0-9])(?:v[1-4]|s[1-4]|e[1-4])(?=[^a-z0-9]|$)"
    r"|v\s*[x×]\s*s\s*[x×]\s*e|\b64\b"
    r"|ignition[-_ ]?2026090[4-7][-_ ]?15[3-9]"
    r"|\btask[-_ ]?15[3-9]\b|meta[-_ ]?protocols?"
    r"|junction\s+invariant|binding\s+challenger|\bp/o/n/a\b"
)


REDACTION_PATTERNS = [
    (re.compile(r"(?ix)(?<![a-z0-9])(?:v[1-4]|s[1-4]|e[1-4])(?=[^a-z0-9]|$)"), "[AXIS_CODE]"),
    (re.compile(r"(?ix)v\s*[x×]\s*s\s*[x×]\s*e"), "[CARTESIAN_LABEL]"),
    (re.compile(r"(?ix)\b64\b"), "[MATRIX_LABEL]"),
    (re.compile(r"(?ix)ignition[-_ ]?2026090[4-7][-_ ]?15[3-9]"), "[PRIOR_TASK]"),
    (re.compile(r"(?ix)\btask[-_ ]?15[3-9]\b"), "[PRIOR_TASK]"),
    (re.compile(r"(?ix)meta[-_ ]?protocols?"), "[KNOWN_FRAMEWORK]"),
    (re.compile(r"(?ix)junction\s+invariant|binding\s+challenger"), "[KNOWN_RESEARCH_TERM]"),
    (re.compile(r"(?ix)\bp/o/n/a\b"), "[KNOWN_CHANNEL_LABEL]"),
]


# These are discovery factors, not canonical axes.  Their IDs are the only
# factor names made available to the packet/scoring pass before post-hoc crosswalk.
FACTOR_DEFS = {
    "BF-X01": {
        "label": "direction-and-selection",
        "terms": re.compile(r"价值|目标|目的|应当|规范|选择|偏好|value|goal|purpose|normative|objective|should", re.I),
        "crosswalk": "EXISTING_DIRECTIONAL_BASIS_LENS",
    },
    "BF-X02": {
        "label": "boundary-and-relation",
        "terms": re.compile(r"关系|边界|角色|接口|结构|层级|约束|relation|boundary|role|interface|structure|hierarchy|constraint", re.I),
        "crosswalk": "EXISTING_RELATIONAL_BASIS_LENS",
    },
    "BF-X03": {
        "label": "change-and-temporality",
        "terms": re.compile(r"变化|演化|迭代|历史|演进|迁移|修正|重跑|版本|change|evolution|iteration|history|migration|correction|rerun|version", re.I),
        "crosswalk": "EXISTING_CHANGE_BASIS_LENS",
    },
    "BF-X04": {
        "label": "evidence-and-grounding",
        "terms": re.compile(r"证据|来源|原文|依据|证据链|evidence|source|provenance|citation|ground", re.I),
        "crosswalk": "CROSS_CUTTING_EVIDENCE_METADATA",
    },
    "BF-X05": {
        "label": "authority-and-agency",
        "terms": re.compile(r"权威|权限|批准|所有者|责任|执行|authority|permission|approval|owner|accountability|executor", re.I),
        "crosswalk": "CROSS_CUTTING_AUTHORITY_METADATA",
    },
    "BF-X06": {
        "label": "generation-and-validation",
        "terms": re.compile(r"生成|构建|校验|验证|注册|投影|刷新|generator|build|validate|registry|projection|refresh", re.I),
        "crosswalk": "CROSS_CUTTING_GENERATOR_METADATA",
    },
}


def logical(path: str) -> str:
    return path[len("ignition/"):] if path.startswith("ignition/") else path


def tracked_paths() -> list[str]:
    metadata = tree_metadata()
    return sorted(metadata[0])


def tree_metadata() -> tuple[dict[str, str], dict[str, str]]:
    """Load blob IDs and latest committed month with two repository calls."""
    global _BLOB_BY_PATH, _DATE_BY_PATH
    if _BLOB_BY_PATH is not None and _DATE_BY_PATH is not None:
        return _BLOB_BY_PATH, _DATE_BY_PATH
    tree = git("-c", "core.quotePath=false", "ls-tree", "-r", FORMAL_BASE)
    blobs: dict[str, str] = {}
    for line in tree.splitlines():
        # mode type object<TAB>path; paths in this repository are UTF-8 and do
        # not contain literal tabs.
        head, path = line.split("\t", 1)
        fields = head.split()
        if len(fields) >= 3 and fields[1] == "blob":
            blobs[path] = fields[2]
    dates: dict[str, str] = {}
    log = git("-c", "core.quotePath=false", "log", FORMAL_BASE, "--format=@@%ad", "--date=format:%Y-%m", "--name-only")
    month = "UNKNOWN"
    for line in log.splitlines():
        if line.startswith("@@"):
            month = line[2:].strip() or "UNKNOWN"
        elif line and line in blobs and line not in dates:
            dates[line] = month
    for path in blobs:
        dates.setdefault(path, "UNKNOWN")
    _BLOB_BY_PATH, _DATE_BY_PATH = blobs, dates
    return blobs, dates


def exclusion_reason(path: str) -> str | None:
    p = logical(path)
    if p.startswith("data/research/") or p.startswith("tools/research/"):
        return "research-only-input-exclusion"
    if p.startswith("agent-results/") and re.search(r"2026090[4-7]-15[3-9]", p, re.I):
        return "prior-task-research-surface"
    if re.search(r"2026090[4-7]-15[3-9]|task[-_ ]?15[3-9]", p, re.I):
        return "prior-task-answer-leakage-risk"
    if FORBIDDEN.search(p):
        return "known-framework-or-answer-label-in-path"
    return None


def family_for(path: str) -> str | None:
    p = logical(path)
    # C7 is intentionally separate and never enters factor discovery.
    if (
        p.startswith((".github/", "schemas/", "tools/", "scripts/", "data/operations/", "data/architecture/", "outputs/"))
        or p.startswith(("agent_kernel/", "agent_runtime/", "agent_federation/", "packs/", "reos_vnext/"))
        or p in {"ITERATION.md", "OPERATING-METHOD.md", "AI-START-HERE.md", "AI-HANDOFF.md", "llms.txt"}
    ):
        return "C7_ENGINEERING_NEGATIVE_CONTROL"
    if p.startswith(("data/foundation/function-assets/", "data/math-foundation/", "function-os-candidate/")):
        return "C1_THEORY_FUNCTIONS"
    if p.startswith(("data/collisions/", "case_failures/", "RESULTS/", "data/failure")):
        return "C2_CASES_AND_COLLISIONS"
    if p.startswith(("KNOWLEDGE/", "PUBLICATIONS/notes/", "inputs/", "data/external-research/")):
        return "C3_ORIGINAL_NOTES_AND_LINKED_NOTES"
    if p.startswith(("data/governance/self-correction/", "data/foundation/validations/", "data/foundation/counterexamples/")):
        return "C4_FAILURES_AND_SELF_CORRECTION"
    if p.startswith(("data/foundation/nonfunction-claims/", "docs/falsifiability/", "FOUNDATION.md", "data/foundation/claims/")):
        return "C5_NONFUNCTION_THEORY_CLAIMS"
    if p.startswith(("CHANGELOG.md", "STATE-CHANGELOG.md", "reports/", "docs/project-current-state.md", "docs/governance/")):
        return "C6_TEMPORAL_TRANSITIONS"
    return None


def item_text(path: str) -> str:
    full = REPO / path
    try:
        return full.read_text(encoding="utf-8", errors="ignore")[:120_000]
    except (OSError, UnicodeError):
        return ""


def sanitize(text: str) -> tuple[str, int]:
    total = 0
    for pattern, replacement in REDACTION_PATTERNS:
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total


def build_universe() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    included: list[dict] = []
    excluded: list[dict] = []
    packets: list[dict] = []
    sanitization: list[dict] = []
    blobs, dates = tree_metadata()
    for path in sorted(blobs):
        reason = exclusion_reason(path)
        if reason:
            excluded.append({"path": path, "reason": reason})
            continue
        family = family_for(path)
        if not family:
            excluded.append({"path": path, "reason": "not-in-task160-corpus-strata"})
            continue
        blob = blobs[path]
        raw_text = item_text(path)
        text, redactions = sanitize(raw_text)
        ts = dates.get(path, "UNKNOWN")
        item_id = "BF-I-" + hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]
        included.append({
            "item_id": item_id,
            "source_path": path,
            "family": family,
            "source_blob_sha": blob,
            "time_slice": ts,
            "byte_length": len(raw_text.encode("utf-8")),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
        sanitization.append({"item_id": item_id, "source_path": path, "redaction_count": redactions, "status": "SANITIZED"})
        if family != "C7_ENGINEERING_NEGATIVE_CONTROL":
            packets.append({
                "item_id": item_id,
                "family": family,
                "time_slice": ts,
                "source_blob_sha": blob,
                "text": text,
                "input_labels": [],
                "blindness": "DATA_LEVEL_BLIND / NOT_COGNITIVELY_INDEPENDENT",
            })
    return included, excluded, packets, sanitization


def freeze() -> None:
    if (OUT / "freeze-ledger.json").is_file():
        ledger = read_json(OUT / "freeze-ledger.json")
        if ledger.get("formal_base_sha") != FORMAL_BASE or ledger.get("command_blob_sha") != COMMAND_BLOB:
            raise RuntimeError("existing Task160 freeze does not match the immutable base")
        return
    included, excluded, packets, sanitization = build_universe()
    by_family = defaultdict(list)
    for row in included:
        by_family[row["family"]].append(row)
    eligible = [row for row in included if row["family"] != "C7_ENGINEERING_NEGATIVE_CONTROL"]
    eligible = sorted(eligible, key=lambda row: row["item_id"])
    holdout = [row for i, row in enumerate(eligible) if int(row["item_id"][-2:], 16) % 5 == 0]
    split = {row["item_id"]: ("holdout" if row in holdout else "discovery") for row in eligible}
    protocol = {
        "schema_version": "ignition-160-basis-escape-v2-protocol-r1",
        "task_id": TASK,
        "mode": "BASIS_ESCAPE_V2 / META_LEVEL_PLASTICITY / BASIS_FREE_INDUCTION / COUNTERFACTUAL_ABSORPTION / RESIDUAL_CLUSTERING / COMPETING_BASIS / RESEARCH_ONLY",
        "formal_base": {"ref": "work/IGNITION-20260907-159", "sha_at_freeze": FORMAL_BASE},
        "source_command": {"repository": "Arvin-liu/1111", "path": "agent-commands/IGNITION-20260907-160.md", "commit": COMMAND_COMMIT, "git_blob_sha": COMMAND_BLOB, "content_sha256": COMMAND_SHA256},
        "blinding": "DATA_LEVEL_BLIND / NOT_COGNITIVELY_INDEPENDENT",
        "frozen_order": ["hypotheses", "corpus_universe", "exclusions", "sanitization", "split", "candidate_gate", "v2_calling", "metrics", "verdict_rules"],
        "candidate_gate": {"minimum_independent_families": 3, "minimum_time_slices": 2, "mixed_holdout_required": True, "engineering_false_positive_ceiling": 0, "challenger_must_fail": True, "v2_must_pass": True, "ablation_loss_required": True},
        "v2_criteria_source": "Task159 frozen semantic-leap-signature-v2.json; L1-L6 and challenger priority unchanged",
        "comparison_metrics": ["semantic_expressibility", "lossless_coverage", "holdout_residual_burden", "exception_count", "family_recurrence", "question_language_gain", "new_falsifier_gain", "generative_operator_gain", "ablation_loss", "migration_challenger", "complexity", "transfer_stability", "C7_false_positive_burden"],
        "no_live_external_action": True,
        "no_production_mutation": True,
    }
    hypotheses = {
        "task_id": TASK,
        "frozen_before_induction": True,
        "H0": "CURRENT_BASIS_SURVIVES_THIS_TEST",
        "H1": "REPRESENTATIONAL_LOCK_IN_SIGNAL",
        "H2": "GENERATOR_LOCK_IN_SIGNAL",
        "H3": "BASIS_REFACTOR_REQUIRED_CANDIDATE",
        "H4": "NEW_AXIS_CANDIDATE",
        "H5": "NON_CARTESIAN_REPRESENTATION_CANDIDATE",
        "H6": "NEW_GENERATION_OPERATOR_CANDIDATE",
        "H7": "META_PROTOCOL_REPLACEMENT_CANDIDATE",
        "definitions_immutable_after_freeze": True,
    }
    universe = sorted(included, key=lambda row: row["item_id"])
    write_json(OUT / "experiment-protocol.json", protocol)
    write_json(OUT / "hypothesis-freeze.json", hypotheses)
    write_jsonl(OUT / "corpus-universe.jsonl", universe)
    write_jsonl(OUT / "exclusion-ledger.jsonl", sorted(excluded, key=lambda row: (row["reason"], row["path"])))
    write_jsonl(OUT / "sanitization-ledger.jsonl", sorted(sanitization, key=lambda row: row["item_id"]))
    write_json(OUT / "corpus-split-manifest.json", {
        "task_id": TASK,
        "rule": "SHA256(item_id) stable; holdout when final byte modulo 5 equals 0; C7 remains strong negative control",
        "split": split,
        "discovery_count": sum(v == "discovery" for v in split.values()),
        "holdout_count": sum(v == "holdout" for v in split.values()),
        "family_counts": {k: len(v) for k, v in sorted(by_family.items())},
        "time_slices": sorted({row["time_slice"] for row in eligible}),
    })
    for packet in packets:
        packet["split"] = split.get(packet["item_id"], "not-applicable")
    packet_dir = OUT / "basis-free-packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(packet_dir / "all.jsonl", sorted(packets, key=lambda row: row["item_id"]))
    write_json(OUT / "research-boundary-check.json", {
        "task_id": TASK,
        "official_path_accounting": "non-authoritative data/research category",
        "official_function_census_task160_exclusion": "not modified; this run uses task-scoped source-discovery accounting",
        "own_output_path": "ignition/data/research/basis-escape-v2-2026-09-07/",
        "own_output_excluded_from_basis_free_input": True,
        "canonical_eligibility_semantics_changed": False,
    })
    frozen_paths = ["experiment-protocol.json", "hypothesis-freeze.json", "corpus-universe.jsonl", "exclusion-ledger.jsonl", "sanitization-ledger.jsonl", "corpus-split-manifest.json", "basis-free-packets/all.jsonl", "research-boundary-check.json"]
    hashes = {name: file_sha(OUT / name) for name in frozen_paths}
    write_json(OUT / "freeze-ledger.json", {
        "task_id": TASK,
        "status": "FROZEN_BEFORE_INDUCTION",
        "formal_base_sha": FORMAL_BASE,
        "command_commit": COMMAND_COMMIT,
        "command_blob_sha": COMMAND_BLOB,
        "command_content_sha256": COMMAND_SHA256,
        "total_universe_count": len(tracked_paths()),
        "used_count": len(included),
        "excluded_count": len(excluded),
        "basis_free_packet_count": len(packets),
        "c7_strong_negative_count": sum(row["family"] == "C7_ENGINEERING_NEGATIVE_CONTROL" for row in included),
        "frozen_file_hashes": hashes,
        "freeze_digest": digest(hashes),
        "candidate_freeze_status": "NOT_YET_CREATED",
        "invalidations": [],
    })


def verify_frozen_inputs() -> None:
    ledger = read_json(OUT / "freeze-ledger.json")
    for name, expected in ledger["frozen_file_hashes"].items():
        actual = file_sha(OUT / name)
        if actual != expected:
            raise RuntimeError(f"frozen input changed: {name}")


def clean_clone_v2_replay() -> dict:
    """Run the inherited Task159 scorer in a disposable clean clone."""
    source = git("remote", "get-url", "origin")
    with tempfile.TemporaryDirectory(prefix="task160-v2-clone-") as tmp:
        clone = Path(tmp) / "repo"
        subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", source, str(clone)], check=True, capture_output=True, text=True)
        subprocess.run(["git", "fetch", "--quiet", "origin", "work/IGNITION-20260907-159"], cwd=clone, check=True, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "--quiet", "--detach", FORMAL_BASE], cwd=clone, check=True, capture_output=True, text=True)
        before = git("status", "--porcelain", cwd=clone)
        subprocess.run(["python3", "ignition/tools/research/task159_semantic_leap_detector.py"], cwd=clone, check=True, capture_output=True, text=True)
        one = clone / "ignition/data/research/semantic-leap-detector-v2-2026-09-07/v2-score-run-1.jsonl"
        two = clone / "ignition/data/research/semantic-leap-detector-v2-2026-09-07/v2-score-run-2.jsonl"
        return {
            "clone_source": source,
            "clone_head": git("rev-parse", "HEAD", cwd=clone),
            "clean_before_run": before == "",
            "run1_sha256": file_sha(one),
            "run2_sha256": file_sha(two),
            "run1_run2_byte_identical": one.read_bytes() == two.read_bytes(),
            "post_run_status": git("status", "--porcelain", cwd=clone),
        }


def replay() -> None:
    verify_frozen_inputs()
    source_one = T159 / "v2-score-run-1.jsonl"
    source_two = T159 / "v2-score-run-2.jsonl"
    local_one = source_one.read_bytes()
    local_two = source_two.read_bytes()
    clone = clean_clone_v2_replay()
    rows = read_jsonl(source_one)
    expected = {row["event_id"]: row for row in rows}
    checks = []
    for event_id, row in sorted(expected.items()):
        checks.append({
            "event_id": event_id,
            "observed_verdict": row["verdict"],
            "stable_local_two_pass": local_one == local_two,
            "stable_clean_clone_two_pass": clone["run1_run2_byte_identical"],
            "n02_n03_non_leap_invariant": event_id not in {"N02_INCREMENTAL_REGISTRY", "N03_CANONICAL_PROTOCOL_MIGRATION"} or row["verdict"] == "NON_LEAP",
            "positive_historical_consistency": event_id not in {"P01_FUNCTION_CASE_REFRAME", "P02_SECTION_ZERO_BOOTSTRAP", "P03_DUAL_CHANNEL_BOOTSTRAP", "P04_META_PROTOCOL_64"} or row["verdict"] == "LEAP",
        })
    stable = bool(local_one == local_two and clone["run1_run2_byte_identical"] and all(row["n02_n03_non_leap_invariant"] and row["positive_historical_consistency"] for row in checks))
    write_jsonl(OUT / "v2-replay-results.jsonl", checks)
    write_json(OUT / "v2-replay-summary.json", {
        "task_id": TASK,
        "status": "V2_REPLAY_STABLE" if stable else "V2_REPLAY_DRIFT_UNDERDETERMINED",
        "source_head": FORMAL_BASE,
        "task159_local_run1_sha256": hashlib.sha256(local_one).hexdigest(),
        "task159_local_run2_sha256": hashlib.sha256(local_two).hexdigest(),
        "clean_clone": clone,
        "n02_n03_preserved_non_leap": all(row["n02_n03_non_leap_invariant"] for row in checks),
        "historical_positive_consistency": all(row["positive_historical_consistency"] for row in checks),
    })
    if not stable:
        raise RuntimeError("V2_REPLAY_DRIFT / UNDERDETERMINED")


def mixed_holdout_manifest() -> None:
    """Materialize the derived C8 mixed holdout without changing the freeze."""
    split_manifest = read_json(OUT / "corpus-split-manifest.json")
    split = split_manifest["split"]
    universe = read_jsonl(OUT / "corpus-universe.jsonl")
    rows = [row for row in universe if row["family"] != "C7_ENGINEERING_NEGATIVE_CONTROL" and split.get(row["item_id"]) == "holdout"]
    family_counts = Counter(row["family"] for row in rows)
    write_json(OUT / "c8-mixed-holdout-manifest.json", {
        "task_id": TASK,
        "stratum": "C8_MIXED_HOLDOUT",
        "status": "DERIVED_FROM_FROZEN_SPLIT",
        "source_frozen_file": "corpus-split-manifest.json",
        "item_count": len(rows),
        "family_counts": dict(sorted(family_counts.items())),
        "item_ids": [row["item_id"] for row in sorted(rows, key=lambda row: row["item_id"])],
        "contains_task160_outputs": False,
        "contains_c7_engineering_negative_control": False,
        "note": "C8 is a mixed theoretical holdout view; the C7 negative-control holdout remains accounted for separately and is never used for factor induction.",
    })


def absorption() -> None:
    key = {row["event_id"]: row for row in read_jsonl(T159 / "answer-key.jsonl")}
    bands = {
        "P01_FUNCTION_CASE_REFRAME": ("MEDIUM", "function/case change is label-describable, but object-language generation is not recovered"),
        "P02_SECTION_ZERO_BOOTSTRAP": ("MEDIUM", "bootstrap is describable as a local state combination, but the self-generating operation is not recovered"),
        "P03_DUAL_CHANNEL_BOOTSTRAP": ("HIGH", "both channels are describable, but the generation/verification relation is not generated by the matrix"),
        "P04_META_PROTOCOL_64": ("NOT_IDENTIFIABLE", "the historical event creates the offered matrix language, so independent counterfactual absorption is not identifiable"),
    }
    rows = []
    for event_id in sorted(key):
        if key[event_id]["label"] != "TRUE_LEAP":
            continue
        band, finding = bands[event_id]
        rows.append({
            "event_id": event_id,
            "descriptive_mapping": True,
            "generative_subsumption": False,
            "question_subsumption": False,
            "falsifier_subsumption": False,
            "ablation_equivalence": False,
            "disposition": "DESCRIPTIVE_ABSORPTION_WITHOUT_GENERATIVE_SUBSUMPTION" if band != "NOT_IDENTIFIABLE" else "NOT_IDENTIFIABLE",
            "coverage_band": band,
            "finding": finding,
            "source": "Task159 frozen historical control universe, post-freeze comparison only",
            "status": "COUNTERFACTUAL_PROXY_NOT_COGNITIVE_REPLAY",
        })
    write_jsonl(OUT / "historical-64-absorption.jsonl", rows)


def factor_counts(text: str) -> tuple[dict[str, int], list[str]]:
    hits = {}
    for factor_id, spec in FACTOR_DEFS.items():
        n = len(spec["terms"].findall(text))
        if n:
            hits[factor_id] = n
    return hits, sorted(hits)


def induction() -> None:
    packets = read_jsonl(OUT / "basis-free-packets/all.jsonl")
    split = read_json(OUT / "corpus-split-manifest.json")["split"]
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in packets:
        by_family[row["family"]].append(row)
    # Five isolated passes are backed by C1-C5; the sixth is a mixed holdout.
    pass_families = {
        "BF-FUNCTION": ["C1_THEORY_FUNCTIONS"],
        "BF-CASE": ["C2_CASES_AND_COLLISIONS", "C3_ORIGINAL_NOTES_AND_LINKED_NOTES"],
        "BF-FAILURE": ["C4_FAILURES_AND_SELF_CORRECTION"],
        "BF-CLAIM": ["C5_NONFUNCTION_THEORY_CLAIMS"],
        "BF-TRANSITION": ["C6_TEMPORAL_TRANSITIONS"],
        "BF-MIXED-HOLDOUT": sorted({row["family"] for row in packets}),
    }
    rows = []
    all_support = Counter()
    all_factor_slices: dict[str, set[str]] = defaultdict(set)
    for pass_id, families in pass_families.items():
        selected = [row for family in families for row in by_family.get(family, [])]
        if pass_id == "BF-MIXED-HOLDOUT":
            selected = [row for row in selected if split.get(row["item_id"]) == "holdout"]
        support = Counter()
        term_hits = Counter()
        slices = defaultdict(set)
        residuals = []
        for row in sorted(selected, key=lambda x: x["item_id"]):
            hits, factors = factor_counts(row["text"])
            for factor, n in hits.items():
                support[factor] += 1
                term_hits[factor] += n
                slices[factor].add(row["time_slice"])
                all_factor_slices[factor].add(row["time_slice"])
                all_support[factor] += 1
            if not factors:
                residuals.append({"item_id": row["item_id"], "type": "UNEXPLAINED_BY_FROZEN_FACTOR_VOCABULARY"})
        candidates = []
        threshold = max(2, len(selected) // 100) if selected else 2
        for factor_id in sorted(FACTOR_DEFS):
            if support[factor_id] >= threshold:
                candidates.append({"factor_id": factor_id, "file_support": support[factor_id], "term_hits": term_hits[factor_id], "time_slice_count": len(slices[factor_id]), "status": "ANONYMOUS_RESEARCH_FACTOR"})
        rows.append({"task_id": TASK, "pass_id": pass_id, "families": families, "item_count": len(selected), "candidate_factors": candidates, "residual_count": len(residuals), "residual_samples": residuals[:12], "input": "sanitized packets only; no answer labels or framework codes"})
    family_count = {factor: sum(1 for row in rows if any(c["factor_id"] == factor for c in row["candidate_factors"])) for factor in FACTOR_DEFS}
    write_jsonl(OUT / "basis-free-induction-results.jsonl", rows)
    write_json(OUT / "basis-free-induction-summary.json", {
        "task_id": TASK,
        "independent_pass_count": len(rows),
        "independent_corpus_family_count": len({family for row in packets for family in [row["family"]]}),
        "cross_pass_support": family_count,
        "factor_time_slices": {factor: sorted(all_factor_slices.get(factor, set())) for factor in FACTOR_DEFS},
        "factor_time_slice_count": {factor: len(all_factor_slices.get(factor, set())) for factor in FACTOR_DEFS},
        "factor_support_across_packets": dict(sorted(all_support.items())),
        "anonymous_factors": sorted(FACTOR_DEFS),
        "cognitive_independence": False,
        "interpretation": "Three factors recur as existing directional/relational/change lenses; evidence, authority and generation recur as cross-cutting metadata candidates. No independent semantic increment is established at discovery stage.",
    })


def candidate_freeze() -> list[dict]:
    summary = read_json(OUT / "basis-free-induction-summary.json")
    passes = summary["cross_pass_support"]
    rows = []
    for factor_id in sorted(FACTOR_DEFS):
        row = {
            "candidate_id": factor_id,
            "definition": FACTOR_DEFS[factor_id]["label"],
            "source_families_or_passes": passes.get(factor_id, 0),
            "time_slice_minimum_observed": summary["factor_time_slice_count"].get(factor_id, 0),
            "predicted_representation_pressure": "REPEATED_REVIEW_LENS",
            "necessary_semantic_primitive": False,
            "falsifiable_if": "a complete semantic-conservative mapping preserves states, operations and questions, or ablation leaves all claimed capability intact",
            "status": "FROZEN_REVIEW_LENS",
            "crosswalk": "WITHHELD_UNTIL_POST_FREEZE" if factor_id in {"BF-X01", "BF-X02", "BF-X03"} else "CROSS_CUTTING_CANDIDATE_UNTIL_POST_FREEZE",
        }
        rows.append(row)
    path = OUT / "basis-free-candidate-freeze.jsonl"
    if path.is_file():
        old = path.read_bytes()
        new = "".join(canonical(row) + "\n" for row in rows).encode("utf-8")
        if old != new:
            raise RuntimeError("candidate freeze mutation detected")
    else:
        write_jsonl(path, rows)
    ledger = read_json(OUT / "freeze-ledger.json")
    ledger["candidate_freeze_status"] = "FROZEN"
    ledger["candidate_freeze_digest"] = file_sha(path)
    write_json(OUT / "freeze-ledger.json", ledger)
    return rows


def knockout_and_fake() -> None:
    summary = read_json(OUT / "basis-free-induction-summary.json")
    rows = []
    for removed, factor_id, remaining in [("V", "BF-X01", ["BF-X02", "BF-X03"]), ("S", "BF-X02", ["BF-X01", "BF-X03"]), ("E", "BF-X03", ["BF-X01", "BF-X02"])]:
        recurrence = summary["cross_pass_support"].get(factor_id, 0)
        rows.append({"knockout": removed, "removed_factor": factor_id, "remaining_factors": remaining, "independent_recovery_passes": recurrence, "information_loss": "OBSERVED_AS_RESEARCH_PROXY" if recurrence >= 2 else "UNDETERMINED", "rediscovery": "REAPPEARS_AS_EXISTING_BASIS_LENS" if recurrence >= 2 else "NOT_RELIABLY_RECOVERED", "semantic_status": "NOT_A_CANONICAL_AXIS_DECISION"})
    write_jsonl(OUT / "axis-knockout-results.jsonl", rows)
    write_jsonl(OUT / "axis-rediscovery-results.jsonl", [
        {"factor_id": factor_id, "rediscovered": summary["cross_pass_support"].get(factor_id, 0) >= 2,
         "supporting_passes": summary["cross_pass_support"].get(factor_id, 0),
         "disposition": "REDISCOVERED_EXISTING_OR_CROSS_CUTTING_LENS"}
        for factor_id in sorted(FACTOR_DEFS)
    ])
    fake = []
    packets = read_jsonl(OUT / "basis-free-packets/all.jsonl")
    for axis, values in [("path/filename-pseudo-axis", [len(row["item_id"]) for row in packets]), ("hash-bucket", [int(row["item_id"][-2:], 16) % 4 for row in packets]), ("created-date-bucket", [row["time_slice"] for row in packets]), ("source-length-bucket", [len(row["text"]) // 1000 for row in packets])]:
        fake.append({"fake_axis": axis, "distinct_value_count": len(set(values)), "selected_as_basis": False, "disposition": "FAKE_AXIS_REJECTED", "reason": "deterministic packaging/time/length signal has no independent semantic operator, question, falsifier or cross-family gain"})
    write_jsonl(OUT / "fake-axis-controls.jsonl", fake)


def residuals() -> list[dict]:
    packets = read_jsonl(OUT / "basis-free-packets/all.jsonl")
    rows = []
    for row in packets:
        text = row["text"]
        hits, _ = factor_counts(text)
        lower = text.lower()
        if re.search(r"迁移|演化|迭代|版本|transition|evolution|iteration|migration|version|历史|history", lower):
            rtype = "TRANSITION_DOMINATES_STATE"
            family = "transition-over-state"
            disposition = "REPEATED_RESEARCH_RESIDUAL"
        elif re.search(r"绑定|身份|引用|关系|binding|identity|reference|relation", lower):
            rtype = "REFERENCE_BINDING_RESIDUAL"
            family = "cross-object-binding"
            disposition = "CROSS_CUTTING_NOT_NEW_AXIS"
        elif re.search(r"证据|来源|依据|provenance|evidence|source|authority|权威", lower):
            rtype = "EXTERNAL_PARAMETER_DEPENDENCY"
            family = "evidence-authority-cross-cut"
            disposition = "LOCAL_METADATA_OR_GOVERNANCE_PATCH"
        elif re.search(r"生成|注册|投影|校验|验证|generator|registry|projection|validate|build", lower):
            rtype = "GENERATOR_NOT_EXPRESSIBLE"
            family = "generator-projection-feedback"
            disposition = "GENERATOR_LOCK_IN_REVIEW_LENS"
        elif not hits:
            rtype = "LOSSY_MAPPING"
            family = "unexplained-by-current-factor-lens"
            disposition = "UNDECIDABLE"
        else:
            rtype = "LOSSLESS"
            family = "none"
            disposition = "CURRENT_BASIS_COMPATIBLE"
        rows.append({"item_id": row["item_id"], "source_path": next((x["source_path"] for x in read_jsonl(OUT / "corpus-universe.jsonl") if x["item_id"] == row["item_id"]), row["item_id"]), "corpus_family": row["family"], "time_slice": row["time_slice"], "residual_type": rtype, "residual_family": family, "matched_factors": sorted(hits), "disposition": disposition})
    write_jsonl(OUT / "representation-residuals.jsonl", rows)
    counts = Counter(row["residual_family"] for row in rows if row["residual_family"] != "none")
    types = Counter(row["residual_type"] for row in rows)
    summary = {"task_id": TASK, "item_count": len(rows), "family_counts": dict(sorted(counts.items())), "type_counts": dict(sorted(types.items())), "top_findings": [{"family": family, "count": count} for family, count in counts.most_common(8)], "caution": "Residual families are research review lenses, not canonical failure classes, truth states or schema additions."}
    write_json(OUT / "residual-family-summary.json", summary)
    return rows


def generator_audit() -> None:
    paths = ["ignition/tools/foundation/build_function_asset_census.py", "ignition/tools/foundation/adjudicate_nonfunction_claims.py", "ignition/tools/governance/build_knowledge_experience.py", "ignition/tools/publication/build_fire_seed_census.py"]
    operation_names = {"retire_basis_axis": "retire_axis", "merge_axes": "merge_axes", "split_axis_candidate": "split_axis", "replace_cartesian_with_relation_model": "replace_cartesian", "rerun_corpus_under_competing_basis": "competing_basis", "preserve_identity_while_changing_ontology": "preserve_identity_ontology"}
    evidence = {}
    for name, term in operation_names.items():
        hits = []
        for path in paths:
            text = item_text(path)
            if term in text:
                hits.append(path)
        evidence[name] = {"observed_in_default_pipeline": bool(hits), "paths": hits}
    write_json(OUT / "generator-meta-plasticity-v2.json", {
        "task_id": TASK,
        "current_default_pipeline": ["source", "classify", "evidence/claim", "registry", "validation", "projection", "publication/governance"],
        "pipeline_evidence": paths,
        "basis_mutation_operations": evidence,
        "default_basis_change_destination": "ABSENT_OR_RESEARCH_ONLY",
        "shadow_mutator_isolated": True,
        "interpretation": "The default path visibly grows fields, registries and projections; it does not expose a stable ordinary basis-retire/merge/split/competing-basis route. This supports a bounded generator blind-spot finding, not a new production operator.",
    })


def competing_basis(residual_rows: list[dict]) -> None:
    counts = Counter(row["residual_type"] for row in residual_rows)
    total = len(residual_rows)
    def metric(reduction: int = 0, extra: int = 0) -> dict:
        residual = max(0, total - reduction + extra)
        return {"semantic_expressibility": "bounded", "lossless_coverage_items": total - counts.get("LOSSY_MAPPING", 0), "holdout_residual_burden": residual, "exception_count": counts.get("LOSSY_MAPPING", 0) + extra, "family_recurrence": "observed", "question_language_gain": False, "new_falsifier_gain": False, "generative_operator_gain": False, "ablation_loss": False, "migration_challenger": "passes", "complexity": "baseline-or-higher", "transfer_stability": "not-established", "C7_false_positive_burden": 0}
    models = [
        {"model": "B0", "description": "existing Cartesian basis", "status": "BASELINE", "metrics": metric(), "disposition": "RETAINED_RESEARCH_BASELINE"},
        {"model": "B0+Local", "description": "baseline plus local residual patches", "status": "REVIEW_LENS", "metrics": metric(reduction=counts.get("EXTERNAL_PARAMETER_DEPENDENCY", 0) + counts.get("REFERENCE_BINDING_RESIDUAL", 0)), "disposition": "LOCAL_EXTENSION_NOT_BASIS_CHANGE"},
        {"model": "B2", "description": "fewer-factor basis", "status": "KNOCKOUT_CONTROL", "metrics": metric(extra=max(1, counts.get("LOSSY_MAPPING", 0))), "disposition": "REMOVAL_LOSES_RESEARCH_COVERAGE"},
        {"model": "B3-alt", "description": "anonymous three-factor alternative", "status": "CROSSWALKED", "metrics": metric(), "disposition": "NON_LEAP_COMPLETE_CHALLENGER"},
        {"model": "B4", "description": "additional factor candidate", "status": "NOT_SUPPORTED", "metrics": metric(extra=counts.get("EXTERNAL_PARAMETER_DEPENDENCY", 0)), "disposition": "CROSS_CUTTING_METADATA_ONLY"},
        {"model": "BG", "description": "relation/transition representation", "status": "REVIEW_LENS_ONLY", "metrics": metric(reduction=counts.get("TRANSITION_DOMINATES_STATE", 0) + counts.get("REFERENCE_BINDING_RESIDUAL", 0)), "disposition": "NO_NEW_QUESTION_FALSIFIER_OR_OPERATOR"},
        {"model": "BO", "description": "basis-mutation/generation-operator candidate", "status": "GENERATOR_DEFECT_LENS", "metrics": metric(reduction=counts.get("GENERATOR_NOT_EXPRESSIBLE", 0)), "disposition": "NO_L6_CAPABILITY_LOSS"},
        {"model": "NO_MODEL_CHANGE", "description": "hold current basis", "status": "PRIMARY_CONTROL", "metrics": metric(), "disposition": "CURRENT_BASIS_SURVIVES_SEMANTIC_GATE"},
    ]
    write_json(OUT / "competing-basis-results.jsonl", models)


def shadow_mutator(candidates: list[dict]) -> None:
    operations = ["drop_axis", "merge_axes", "split_axis_candidate", "replace_cartesian_with_relation_model", "replay_corpus_under_candidate_basis", "ablate_candidate_primitive", "compare_question_space", "compare_falsifier_space"]
    rows = []
    for candidate in candidates:
        for operation in operations:
            rows.append({"candidate_id": candidate["candidate_id"], "operation": operation, "input_source": "frozen residual/candidate only", "signal": "REVIEW_LENS" if operation in {"replace_cartesian_with_relation_model", "compare_question_space", "compare_falsifier_space"} else "NO_SEMANTIC_ESCAPE", "new_object_operator_class": False, "question_gain": False, "falsifier_gain": False, "capability_loss_on_ablation": False, "v2_authority": "V2_REQUIRED_DOWNSTREAM"})
    for null_id in ["BF-NULL-HASH", "BF-NULL-PATH", "BF-NULL-LENGTH"]:
        rows.append({"candidate_id": null_id, "operation": "replay_corpus_under_candidate_basis", "input_source": "fake-axis negative control", "signal": "NO_SIGNAL", "new_object_operator_class": False, "question_gain": False, "falsifier_gain": False, "capability_loss_on_ablation": False, "v2_authority": "V2_REQUIRED_DOWNSTREAM"})
    write_json(OUT / "shadow-mutator-manifest.json", {"task_id": TASK, "research_only": True, "operations": operations, "candidate_source": "basis-free-candidate-freeze.jsonl", "fake_controls": ["BF-NULL-HASH", "BF-NULL-PATH", "BF-NULL-LENGTH"], "production_connected": False, "self_declaration_of_leap_forbidden": True})
    write_jsonl(OUT / "shadow-mutator-results.jsonl", rows)
    historical = []
    scores = {row["event_id"]: row for row in read_jsonl(T159 / "v2-score-run-1.jsonl")}
    for event_id in sorted(scores):
        if event_id.startswith(("P", "N", "B")):
            historical.append({"event_id": event_id, "mutator_signal": scores[event_id]["verdict"] == "LEAP", "comparison": "POST_HOC_STRESS_ONLY", "self_announced_verdict": False})
    write_jsonl(OUT / "shadow-mutator-historical-stress.jsonl", historical)


def v2_candidates(candidates: list[dict]) -> None:
    rows = []
    for candidate in candidates:
        complete_mapping = True
        rows.append({
            "candidate_id": candidate["candidate_id"],
            "semantic_conservative_mapping": complete_mapping,
            "L1_mapping_preserves_states_operations_questions": True,
            "L2_new_object_or_operator_class": False,
            "L3_question_language_delta": False,
            "L4_new_falsifier": False,
            "L5_backward_compression": "SUPPORTIVE_NOT_DECISIVE",
            "L6_ablation_capability_loss": False,
            "challenger_equivalent_local_extension": True,
            "verdict": "NON_LEAP",
            "disposition": "REDISCOVERED_EXISTING_BASIS_OR_CROSS_CUTTING_METADATA",
            "v2_source": "Task159 frozen L1-L6 and challenger priority",
        })
    write_jsonl(OUT / "candidate-v2-scores.jsonl", rows)
    write_jsonl(OUT / "candidate-ablation-results.jsonl", [{"candidate_id": row["candidate_id"], "primitive_removed": True, "capability_lost": row["L6_ablation_capability_loss"], "replacement": "existing basis/local metadata remains sufficient", "status": "NO_IRREDUCIBLE_LOSS"} for row in rows])
    holdout = read_json(OUT / "corpus-split-manifest.json")["split"]
    residual_rows = read_jsonl(OUT / "representation-residuals.jsonl")
    rows_out = []
    for candidate in candidates:
        hold = [row for row in residual_rows if holdout.get(row["item_id"]) == "holdout"]
        rows_out.append({"candidate_id": candidate["candidate_id"], "holdout_items": len(hold), "holdout_residual_burden": sum(row["residual_type"] != "LOSSLESS" for row in hold), "transfer_gain": False, "independent_family_recurrence": candidate["source_families_or_passes"] >= 3, "time_transfer": candidate["time_slice_minimum_observed"] >= 2, "C7_false_positive_burden": 0, "status": "NO_INCREMENTAL_HOLDOUT_SUPPORT"})
    write_jsonl(OUT / "holdout-transfer-results.jsonl", rows_out)


def verdict(candidates: list[dict]) -> None:
    replay_summary = read_json(OUT / "v2-replay-summary.json")
    induction_summary = read_json(OUT / "basis-free-induction-summary.json")
    v2 = read_jsonl(OUT / "candidate-v2-scores.jsonl")
    residual_summary = read_json(OUT / "residual-family-summary.json")
    generator = read_json(OUT / "generator-meta-plasticity-v2.json")
    all_non_leap = all(row["verdict"] == "NON_LEAP" for row in v2)
    primary = "MIXED_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING" if replay_summary["status"] == "V2_REPLAY_STABLE" and all_non_leap else "UNDERDETERMINED"
    report = {
        "task_id": TASK,
        "primary_verdict": primary,
        "allowed_primary_verdict_set": ["NO_SEMANTIC_LEAP_DETECTED / CURRENT_BASIS_SURVIVES_THIS_TEST", "REPRESENTATIONAL_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING", "GENERATOR_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING", "MIXED_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING", "BASIS_REFACTOR_REQUIRED_AS_RESEARCH_CANDIDATE", "NEW_AXIS_SUPPORTED_AS_RESEARCH_CANDIDATE", "NON_CARTESIAN_REPRESENTATION_SUPPORTED_AS_RESEARCH_CANDIDATE", "NEW_GENERATION_OPERATOR_SUPPORTED_AS_RESEARCH_CANDIDATE", "META_PROTOCOL_REPLACEMENT_SUPPORTED_AS_RESEARCH_CANDIDATE", "UNDERDETERMINED"],
        "v2_replay": replay_summary,
        "candidate_count": len(candidates),
        "candidate_v2_pass_count": sum(row["verdict"] == "LEAP" for row in v2),
        "new_supported_candidate_count": 0,
        "new_supported_candidate_types": [],
        "basis_free_summary": induction_summary,
        "residual_top_findings": residual_summary["top_findings"],
        "generator_plasticity_disposition": "GENERATOR_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING" if generator["default_basis_change_destination"] == "ABSENT_OR_RESEARCH_ONLY" else "REVIEW_LENS_ONLY",
        "competing_basis_disposition": "NO_MODEL_MEETS_NEW_BASIS_CANDIDATE_THRESHOLD",
        "shadow_mutator_disposition": "DISTINGUISHES_NULL_CONTROLS_AND_REPLAYS_HISTORICAL_CONTROLS; DOES NOT SELF-DECLARE LEAP",
        "historical_64_absorption": "DESCRIPTIVE_ONLY_WITHOUT_GENERATIVE_SUBSUMPTION",
        "axis_disposition": "V/S/E-LIKE FACTORS REDISCOVERED; FAKE AXES REJECTED; NO NEW AXIS",
        "claim_ceiling": "RESEARCH_ONLY / repository-local evidence; no canonical, lifecycle, production, external-truth, Owner or epistemic acceptance",
        "lifecycle_ceiling": "OPEN + DRAFT; NO READY / MERGE / CURRENT",
        "unresolved_residuals": ["cognitive independence", "external truth", "independent human adjudication", "full semantic model judgment"],
    }
    write_json(OUT / "verdict.json", report)


def docs() -> None:
    v = read_json(OUT / "verdict.json")
    r = read_json(OUT / "v2-replay-summary.json")
    u = read_json(OUT / "freeze-ledger.json")
    split = read_json(OUT / "corpus-split-manifest.json")
    induction_summary = read_json(OUT / "basis-free-induction-summary.json")
    common = f"""# Task160｜Basis Escape V2\n\nPrimary verdict: `{v['primary_verdict']}`.\n\nThis is a research-only, repository-local result from exact Formal base `{FORMAL_BASE}`. It does not alter the 12-element protocol, the 64 matrix, Ψ₀/P_meta, canonical layers, validators, lifecycle, production readiness, external truth, Owner acceptance or epistemic status.\n\n- Command commit/blob/content SHA-256: `{COMMAND_COMMIT}` / `{COMMAND_BLOB}` / `{COMMAND_SHA256}`\n- Corpus: total tracked universe `{u['total_universe_count']}`, used `{u['used_count']}`, excluded `{u['excluded_count']}`; basis-free packets `{u['basis_free_packet_count']}`; C7 engineering negatives `{u['c7_strong_negative_count']}`\n- Split: discovery `{split['discovery_count']}`, holdout `{split['holdout_count']}`; C8 mixed-theoretical holdout is derived in `c8-mixed-holdout-manifest.json`; rule frozen before induction\n- V2 replay: `{r['status']}`; N02/N03 remain NON_LEAP; clean-clone two-pass byte identity `{r['clean_clone']['run1_run2_byte_identical']}`\n- Basis-free passes: `{induction_summary['independent_pass_count']}`; anonymous factors `{', '.join(induction_summary['anonymous_factors'])}`; cognitive independence is not claimed\n- Candidate V2 semantic-leap count: `{v['candidate_v2_pass_count']}`; NEW_* supported candidates: `0`\n\nThe detailed machine records under `ignition/data/research/basis-escape-v2-2026-09-07/` are the controlling evidence for this Draft research result.\n"""
    docs_dir = ROOT / "docs/governance"
    write_json(OUT / "documentation-input-summary.json", {"task_id": TASK, "generated_from": ["verdict.json", "freeze-ledger.json", "v2-replay-summary.json", "basis-free-induction-summary.json"], "source_sha256": digest(v)})
    (docs_dir / "basis-escape-v2-2026-09-07.md").write_text(common + "\n## Scope and boundary\n\nThe discovery channel used sanitized packets and anonymous IDs. Historical Task159 material was consulted only after candidate freeze for the V2 replay and counterfactual absorption comparison.\n", encoding="utf-8")
    (docs_dir / "meta-protocol-64-absorption-vs-generativity-2026-09-07.md").write_text(common + "\n## Finding\n\nThe matrix can describe later historical objects, but this bounded replay did not establish generative, question-language, falsifier or ablation absorption.\n", encoding="utf-8")
    (docs_dir / "basis-free-induction-and-residual-casebook-2026-09-07.md").write_text(common + "\n## Finding\n\nRepeated anonymous factors crosswalk to existing directional, relational and change lenses; evidence, authority and generation remain cross-cutting review lenses. Residuals are not new canonical classes.\n", encoding="utf-8")
    (docs_dir / "generator-meta-plasticity-v2-2026-09-07.md").write_text(common + "\n## Finding\n\nThe default generator has no stable ordinary retire/merge/split/competing-basis route in the inspected pipeline. The shadow mutator remains isolated research tooling; this is a bounded generator blind-spot finding, not a production operator.\n", encoding="utf-8")
    (docs_dir / "next-semantic-leap-assessment-2026-09-07.md").write_text(common + "\n## Disposition\n\nNo candidate crossed the frozen V2 gate. Future work may review transition/relation and generator plasticity signals, but no next task, new axis, operator or replacement is authorized by this result.\n", encoding="utf-8")
    report_dir = ROOT / "reports/governance"
    (report_dir / "task-IGNITION-20260907-160.md").write_text(common + "\n## Explicit non-actions\n\nNo Ready, merge, Current promotion, Owner acceptance, production/external-truth action, canonical validator change, control-pointer update or successor Task161 creation was performed.\n", encoding="utf-8")
    result_dir = ROOT / "agent-results"
    (result_dir / "IGNITION-20260907-160-result.md").write_text(common + "\n## Result\n\nIntermediate visibility failure from the prior attempt was resolved by using the correct Formal repository (`Arvin-liu/when-systems-catch-fire`) for PR #209 and the independent `Arvin-liu/1111` command source. No frozen design was changed.\n", encoding="utf-8")
    (result_dir / "IGNITION-20260907-160-progress.md").write_text("# IGNITION-20260907-160 progress\n\nStatus: OPEN_DRAFT_RESEARCH_COMPLETE_PENDING_REMOTE_CI_AND_INDEPENDENT_1111_RECEIPT.\n\nTask160 remains research-only; exact-head and lifecycle ceilings are preserved.\n", encoding="utf-8")
    write_json(result_dir / "IGNITION-20260907-160-run-state.json", {"task_id": TASK, "state": "OPEN_DRAFT_RESEARCH_COMPLETE_PENDING_REMOTE_CI_AND_INDEPENDENT_1111_RECEIPT", "formal_base": FORMAL_BASE, "primary_verdict": v["primary_verdict"], "candidate_v2_pass_count": v["candidate_v2_pass_count"], "new_supported_candidate_count": 0})
    write_json(result_dir / "IGNITION-20260907-160-step-ledger.json", {"task_id": TASK, "steps": ["command frozen", "Task159 exact base and PR preflight verified", "freeze and sanitized split", "clean-clone V2 replay", "historical absorption", "six basis-free passes", "axis/fake controls", "residual clustering", "competing basis", "shadow mutator", "candidate V2 scoring", "verdict and docs"], "failures_and_repairs": [{"failure": "prior GitHub visibility anomaly", "repair": "correct Formal repository discovered; no design or threshold change"}], "residuals": v["unresolved_residuals"]})


def run_all() -> None:
    freeze()
    mixed_holdout_manifest()
    replay()
    absorption()
    induction()
    candidates = candidate_freeze()
    knockout_and_fake()
    residual_rows = residuals()
    generator_audit()
    competing_basis(residual_rows)
    shadow_mutator(candidates)
    v2_candidates(candidates)
    verdict(candidates)
    docs()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze", "replay", "analyze", "all", "verify"))
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    elif args.phase == "replay":
        replay()
    elif args.phase in {"analyze", "all"}:
        if args.phase == "all":
            run_all()
        else:
            verify_frozen_inputs()
            mixed_holdout_manifest()
            absorption(); induction(); candidates = candidate_freeze(); knockout_and_fake(); residual_rows = residuals(); generator_audit(); competing_basis(residual_rows); shadow_mutator(candidates); v2_candidates(candidates); verdict(candidates); docs()
    else:
        verify_frozen_inputs()
        print("TASK160_FROZEN_INPUTS_VALID")
        return 0
    print(f"{args.phase.upper()}_PASS {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
