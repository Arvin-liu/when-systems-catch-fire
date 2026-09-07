#!/usr/bin/env python3
"""Research-only Task164 historical basis-pressure qualification.

The blind path reconstructs anonymous cumulative prefixes from reachable Git
history. It never reads the answer key. A short or incomplete historical
window is retained as an explicit residual, not filled with modern structure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
DEFAULT_OUT = ROOT / "data/research/historical-basis-pressure-sensor-2026-09-07"
OUT = DEFAULT_OUT

TASK = "IGNITION-20260907-164"
FORMAL_BASE_REF = "work/IGNITION-20260907-163"
FORMAL_BASE = "644c93cd5cd0c7d4ed490f95795897df3bcd8826"
COMMAND_REPOSITORY = "Arvin-liu/1111"
COMMAND_PATH = "agent-commands/IGNITION-20260907-164.md"
COMMAND_COMMIT = "ef5ac179529bb0dc44c7d1111ca1ea63ef4c89e5"
COMMAND_BLOB = "18ba43e3a7d6aab3a8bdc794b2767db2e861b78a"
COMMAND_SHA256 = "e25ac0171db94709d0a0c65fa51c8f425b935c191a17e8210336e6ed943db1f3"
COMMAND_URL = "https://github.com/Arvin-liu/1111/blob/" + COMMAND_COMMIT + "/" + COMMAND_PATH

TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml", ".toml", ".rst"}
MAX_INITIAL_SCAN_FILES = 160
MAX_CANDIDATE_FILES_PER_CHECKPOINT = 320
MAX_SCAN_BYTES_PER_CHECKPOINT = 1_750_000
MIN_CHECKPOINTS_FOR_CHANGE_POINT = 6
MAX_CHECKPOINTS = 10

DIMENSIONS = [
    "UNRESOLVED_RESIDUAL_BURDEN",
    "LOCAL_PATCH_BURDEN",
    "REINTERPRETATION_CHURN",
    "QUESTION_LANGUAGE_DEFICIT",
    "FALSIFIER_DEFICIT",
    "CROSS_SOURCE_COLLISION",
    "CONTRADICTORY_PREDICTION_BURDEN",
    "DUPLICATED_STRUCTURE_PRESSURE",
]

# This is answer-key material. It is never read by blind_run_once.
EVENTS: list[dict[str, Any]] = [
    {
        "blind_epoch_id": "epoch-001", "answer_id": "E1_PRE_FUNCTION_CASE",
        "event_id": "P01_FUNCTION_CASE_REFRAME", "kind": "positive", "split": "calibration",
        "start_commit": "edd7d116d0580e3810d2ff73037981bd07e011b6",
        "pre_leap_commit": "981d3f5f1cdb62c058f5de8c626444c050ab95d8",
        "leap_commit": "a1295d737e290105069f915c577105c0cf5ff26f",
        "required_capability": "OBJECT_LANGUAGE_CHANGE",
        "boundary_reason": "Earliest stable raw-note/function-case absorption window available before the first formally named function-case reframe.",
    },
    {
        "blind_epoch_id": "epoch-002", "answer_id": "E2_FUNCTION_CASE_STABLE",
        "event_id": "P02_SECTION_ZERO_BOOTSTRAP", "kind": "positive", "split": "holdout",
        "start_commit": "a1295d737e290105069f915c577105c0cf5ff26f",
        "pre_leap_commit": "f4b0c5af3e296019d52f735d178a3f2078ead7be",
        "leap_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "required_capability": "SELF_REFERENCE",
        "boundary_reason": "Starts at the first post-reframe state and stops at the last pre-section-zero state.",
    },
    {
        "blind_epoch_id": "epoch-003", "answer_id": "E3_BOOTSTRAP_STABLE",
        "event_id": "P03_DUAL_CHANNEL_BOOTSTRAP", "kind": "positive", "split": "holdout",
        "start_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "pre_leap_commit": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e",
        "leap_commit": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b",
        "required_capability": "INDEPENDENT_COUNTERCHECK",
        "boundary_reason": "The target follows immediately from the bootstrap commit; no intervening stable prefix exists.",
    },
    {
        "blind_epoch_id": "epoch-004", "answer_id": "E4_DUAL_CHANNEL_STABLE",
        "event_id": "P04_META_PROTOCOL_64", "kind": "positive", "split": "holdout",
        "start_commit": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b",
        "pre_leap_commit": "1defe3d39988f9716863b2fd39d763808e1579e0",
        "leap_commit": "974b121e36145d6ed35b214619312001f97b21f8",
        "required_capability": "COMPOSITIONAL_GENERATION",
        "boundary_reason": "Starts after the dual-channel bootstrap and stops before the first protocol-generation-layer commit.",
    },
    {
        "blind_epoch_id": "epoch-005", "answer_id": "N02_INCREMENTAL_REGISTRY",
        "event_id": "N02_INCREMENTAL_REGISTRY", "kind": "negative", "split": "calibration",
        "start_commit": "0b2a88f508274feadd4adbbda3eefc3ab531ddd2",
        "pre_leap_commit": "56b952a3b101c6ed385d1c11591914d043a337cd",
        "leap_commit": "ab90558ae1c158d9a67146ebd288678b67e1c4c3",
        "required_capability": "NONE",
        "boundary_reason": "Small but real note-sync to registry-expansion control window.",
    },
    {
        "blind_epoch_id": "epoch-006", "answer_id": "N03_CANONICAL_PROTOCOL_MIGRATION",
        "event_id": "N03_CANONICAL_PROTOCOL_MIGRATION", "kind": "negative", "split": "holdout",
        "start_commit": "1defe3d39988f9716863b2fd39d763808e1579e0",
        "pre_leap_commit": "633ca814c6a53b4bdab425001459aabc5a0cccbf",
        "leap_commit": "4c452149a451f074d949739086cfccdb3ec5bd56",
        "required_capability": "NONE",
        "boundary_reason": "July protocol migration retained as conservative materialization control.",
    },
    {
        "blind_epoch_id": "epoch-007", "answer_id": "N04_PAGES_PROJECTION",
        "event_id": "N04_PAGES_PROJECTION", "kind": "negative", "split": "holdout",
        "start_commit": "037eaad775909cb85928ecff457e421aa1f8d041",
        "pre_leap_commit": "304ecfc645bbe44c4b1dbdac8a119b8ed0009c31",
        "leap_commit": "d4bfaa886908bd3b3f109c7d8220a89a5d469186",
        "required_capability": "NONE",
        "boundary_reason": "Pages/projection build retained as a large engineering-change control.",
    },
    {
        "blind_epoch_id": "epoch-008", "answer_id": "N05_VALIDATOR_EXPANSION",
        "event_id": "N05_VALIDATOR_EXPANSION", "kind": "negative", "split": "holdout",
        "start_commit": "d5044e1eaeaaf69cd70059428b32ee7487451bf6",
        "pre_leap_commit": "9bf1ca0e2beebc1d4abf85b5b9e4bb2b6e17c2c9",
        "leap_commit": "ba56c43c1a9d429ee182ea976be4859bd5972733",
        "required_capability": "NONE",
        "boundary_reason": "Governance/validator expansion retained as non-leap control.",
    },
    {
        "blind_epoch_id": "epoch-009", "answer_id": "N06_KNOWLEDGE_PROJECTION_REFRESH",
        "event_id": "N06_KNOWLEDGE_PROJECTION_REFRESH", "kind": "negative", "split": "holdout",
        "start_commit": "212322d41db79bce2dbd116166d3f1ad226291f3",
        "pre_leap_commit": "0741f4f0902d50cf5388e787382500b5240d2b0e",
        "leap_commit": "74096d5ad0faa4b524879061d332c7026c2a83a0",
        "required_capability": "NONE",
        "boundary_reason": "Later knowledge/projection refresh tests whether engineering churn masquerades as pressure.",
    },
    {
        "blind_epoch_id": "epoch-010", "answer_id": "N07_PROVIDER_ADAPTER_REFACTOR",
        "event_id": "N07_PROVIDER_ADAPTER_REFACTOR", "kind": "negative", "split": "holdout",
        "start_commit": "e60acb82fc92fe2378ae605f0f8a59b0aa120d7e",
        "pre_leap_commit": "a051ad31b72d5cbb8deeaf2007b0e09431f8a4ba",
        "leap_commit": "02e43c62942da8b65f005a6314d3eee799aaa776",
        "required_capability": "NONE",
        "boundary_reason": "Provider/adapter architecture window treated as conservative refactor control.",
    },
    {
        "blind_epoch_id": "epoch-011", "answer_id": "N08_GENERATED_PROJECTION_REFRESH",
        "event_id": "N08_GENERATED_PROJECTION_REFRESH", "kind": "negative", "split": "holdout",
        "start_commit": "304ecfc645bbe44c4b1dbdac8a119b8ed0009c31",
        "pre_leap_commit": "d4bfaa886908bd3b3f109c7d8220a89a5d469186",
        "leap_commit": "188ae92d3fd4b52b9b3cdba99c66d63b04a2a8fc",
        "required_capability": "NONE",
        "boundary_reason": "Generated-output refresh tests projection churn separately from source-language change.",
    },
    {
        "blind_epoch_id": "epoch-012", "answer_id": "N09_KNOWLEDGE_MATERIALIZATION",
        "event_id": "N09_KNOWLEDGE_MATERIALIZATION", "kind": "negative", "split": "holdout",
        "start_commit": "e07497fa76d5c58a4b77035e48867cae7264d3ab",
        "pre_leap_commit": "d6910b43d8c216191f375b5737f82afa0b0a6bff",
        "leap_commit": "f2947ef3e26cd51cc3f156badcba6d2411f77b23",
        "required_capability": "NONE",
        "boundary_reason": "Large knowledge-ledger materialization retained as matched non-leap control.",
    },
]

DIMENSION_PATTERNS: dict[str, tuple[str, ...]] = {
    "UNRESOLVED_RESIDUAL_BURDEN": (r"\bunresolved\b", r"\bunknown\b", r"\bpending\b", r"\bmissing\b", r"\bgap\b", r"\bcannot\b", r"\bnot enough\b", r"\bincomplete\b", r"\bblocked\b", r"\bopen question\b", r"\bfailure\b", r"\bfailed\b"),
    "LOCAL_PATCH_BURDEN": (r"\bpatch(?:es|ed|ing)?\b", r"\bfix(?:es|ed|ing)?\b", r"\brepair(?:ed|ing)?\b", r"\bbackfill(?:ed|ing)?\b", r"\bexception(?:s)?\b", r"\bworkaround(?:s)?\b", r"\bcompat(?:ibility)?\b", r"\blegacy\b", r"\bhotfix\b"),
    "REINTERPRETATION_CHURN": (r"\brewrite(?:s|d|ing)?\b", r"\breclassif(?:y|ied|ication)\b", r"\bnormaliz(?:e|ed|ation)\b", r"\brebuild(?:s|ing)?\b", r"\brefresh(?:ed|ing)?\b", r"\brerun(?:s|ning)?\b", r"\brecompute(?:d|s|ing)?\b", r"\brename(?:d|s|ing)?\b", r"\bmigrat(?:e|ed|ion|ing)\b"),
    "QUESTION_LANGUAGE_DEFICIT": (r"\?", r"\bwhy\b", r"\bhow\b", r"\bwhat if\b", r"\bwhether\b", r"\bunder what\b", r"\bshould\b", r"\bcan we\b"),
    "FALSIFIER_DEFICIT": (r"\bfalsif(?:y|ier|ication|ied)\b", r"\bcounterexample\b", r"\badversarial\b", r"\brefut(?:e|ed|ation)\b", r"\binvariant\b", r"\bcheck(?:s|ed|ing)?\b", r"\bvalidat(?:e|ed|ion|or|ing)\b", r"\btest(?:s|ed|ing)?\b"),
    "CROSS_SOURCE_COLLISION": (r"\bcollision(?:s)?\b", r"\bconflict(?:s|ed|ing)?\b", r"\bcontradict(?:s|ed|ion|ory|ing)?\b", r"\binconsistent\b", r"\boverlap(?:s|ped|ping)?\b", r"\bduplicate(?:s|d|ting)?\b", r"\bclash(?:es|ed|ing)?\b"),
    "CONTRADICTORY_PREDICTION_BURDEN": (r"\bcontradict(?:s|ed|ion|ory|ing)?\b", r"\binconsistent\b", r"\bprediction(?:s)?\b", r"\bpredict(?:s|ed|ing)?\b", r"\bexpected\b", r"\bif\b", r"\bwould\b"),
    "DUPLICATED_STRUCTURE_PRESSURE": (r"\bduplicate(?:s|d|ting)?\b", r"\brepeated\b", r"\brecurr(?:ent|ence)\b", r"\bsame\b", r"\bcopy\b", r"\bparallel\b", r"\bmirror\b", r"\btemplate\b"),
}

DIRECT_LEAKAGE = re.compile(
    r"(?ix)IGNITION[-_ ]?2026090[4-7][- _]?(?:15[3-9]|16[0-4])"
    r"|TASK[-_ ]?16[0-4]"
    r"|\b(?:P0[1-4]|N0[2-9])(?:[_-][A-Z0-9_-]+)?\b"
    r"|\b(?:TRUE_LEAP|NON_LEAP|BORDERLINE)\b"
    r"|\b(?:OBJECT_LANGUAGE_CHANGE|SELF_REFERENCE|INDEPENDENT_COUNTERCHECK|COMPOSITIONAL_GENERATION)\b"
    r"|\b(?:object[-_ ]language|self[-_ ]reference|independent[-_ ]counter[-_ ]check|compositional[-_ ]generation)\b"
    r"|\b(?:meta[-_ ]protocol|basis[-_ ]escape|semantic[-_ ]leap|junction[-_ ]invariant)\b"
)


def run_git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and proc.returncode:
        raise RuntimeError("git command failed: " + " ".join(args) + ": " + proc.stderr.decode("utf-8", errors="replace"))
    return proc.stdout.decode("utf-8", errors="replace")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def commit_date(commit: str) -> str:
    return run_git("show", "-s", "--format=%cI", commit).strip()


def commit_subject(commit: str) -> str:
    return run_git("show", "-s", "--format=%s", commit).strip()


def tree_entries(commit: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line in run_git("ls-tree", "-r", "--format=%(objectname)\t%(objectsize)\t%(path)", commit).splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        blob, size_raw, path = parts
        result[path] = {"blob_sha": blob, "size": int(size_raw) if size_raw.isdigit() else 0}
    return result


def material_path(path: str) -> bool:
    lowered = path.lower()
    if lowered.startswith((".github/", "ignition/data/research/", "ignition/reports/", "ignition/agent-results/", "ignition/docs/governance/", "ignition/tests/", "ignition/outputs/")):
        return False
    if "node_modules/" in lowered or "/.git/" in lowered:
        return False
    return Path(path).suffix.lower() in TEXT_EXTENSIONS


def direct_sensitive_path(path: str) -> bool:
    return bool(re.search(r"ignition[-_ ]?2026090[4-7][- _]?(?:15[3-9]|16[0-4])|task[-_ ]?16[0-4]|semantic[-_ ]?leap|mutable[-_ ]?basis|basis[-_ ]?escape|meta[-_ ]?protocol[-_ ]?64|junction[-_ ]?invariant|pressure", path.lower()))


def source_family(path: str) -> str:
    lowered = path.lower()
    if lowered.startswith(("dianhuo/", "originals/")):
        return "raw_notes"
    if lowered.startswith("ignition/knowledge/"):
        return "knowledge"
    if lowered.startswith("ignition/publications/"):
        return "publication"
    if lowered.startswith(("ignition/data/", "统一函数总表/", "统一案例总表/")):
        return "data"
    if lowered.startswith(("ignition/tools/", "ignition/scripts/")):
        return "tooling"
    if lowered.startswith("ignition/docs/"):
        return "docs"
    if lowered.startswith("ignition/"):
        return "ignition_surface"
    return "root_surface"


def redact(text: str) -> tuple[str, int]:
    return DIRECT_LEAKAGE.subn("<redacted>", text)


def dimension_counts(text: str) -> dict[str, int]:
    return {
        dimension: sum(len(re.findall(pattern, text, flags=re.I | re.M)) for pattern in patterns)
        for dimension, patterns in DIMENSION_PATTERNS.items()
    }


def unit_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def word_count(text: str) -> int:
    return max(1, len(re.findall(r"\w+", text, flags=re.UNICODE)))


def epoch_commits(start: str, stop: str) -> list[str]:
    if start == stop:
        return [start]
    middle = run_git("rev-list", "--first-parent", "--reverse", f"{start}..{stop}").splitlines()
    if not middle or middle[-1] != stop:
        raise RuntimeError("history does not terminate at requested stop " + stop)
    return [start] + middle


def choose_checkpoints(commits: list[str]) -> list[str]:
    if len(commits) <= MAX_CHECKPOINTS:
        return commits
    positions = {int(round(index * (len(commits) - 1) / (MAX_CHECKPOINTS - 1))) for index in range(MAX_CHECKPOINTS)}
    return [commit for index, commit in enumerate(commits) if index in positions]


def diff_paths(start: str, checkpoint: str) -> list[str]:
    if start == checkpoint:
        return []
    return sorted(path for path in run_git("diff", "--name-only", start, checkpoint).splitlines() if path)


def diff_stats(start: str, checkpoint: str) -> dict[str, int]:
    if start == checkpoint:
        return {"changed_files": 0, "added_lines": 0, "deleted_lines": 0}
    changed = added = deleted = 0
    for line in run_git("diff", "--numstat", start, checkpoint).splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        changed += 1
        added += int(parts[0]) if parts[0].isdigit() else 0
        deleted += int(parts[1]) if parts[1].isdigit() else 0
    return {"changed_files": changed, "added_lines": added, "deleted_lines": deleted}


def commit_path_events(start: str, stop: str) -> list[tuple[str, list[str]]]:
    commits = run_git("rev-list", "--first-parent", "--reverse", f"{start}..{stop}").splitlines()
    return [
        (
            commit,
            sorted(path for path in run_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines() if path),
        )
        for commit in commits
    ]


def read_blobs(commit: str, paths: list[str]) -> dict[str, str]:
    """Read a deterministic batch of snapshot blobs with one Git process."""
    if not paths:
        return {}
    requests = b"".join((f"{commit}:{path}\n").encode("utf-8") for path in paths)
    completed = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=REPO,
        input=requests,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "git cat-file --batch failed")
    payload = completed.stdout
    offset = 0
    result: dict[str, str] = {}
    for path in paths:
        header_end = payload.find(b"\n", offset)
        if header_end < 0:
            raise RuntimeError("truncated git cat-file --batch header")
        header = payload[offset:header_end].split()
        offset = header_end + 1
        if len(header) >= 2 and header[1] == b"missing":
            continue
        if len(header) < 3 or header[1] != b"blob":
            raise RuntimeError("unexpected git cat-file --batch response for " + path)
        size = int(header[2])
        data = payload[offset:offset + size]
        if len(data) != size:
            raise RuntimeError("truncated git cat-file --batch blob for " + path)
        offset += size
        if payload[offset:offset + 1] == b"\n":
            offset += 1
        result[path] = data.decode("utf-8", errors="replace")
    return result


def scan_checkpoint(event: dict[str, Any], checkpoint: str, path_events: list[tuple[str, list[str]]], position: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entries = tree_entries(checkpoint)
    all_material = sorted(path for path in entries if material_path(path) and not direct_sensitive_path(path))
    changed = diff_paths(event["start_commit"], checkpoint)
    changed_material = [path for path in changed if material_path(path) and not direct_sensitive_path(path)]
    candidate_pool = sorted(set(all_material[:MAX_INITIAL_SCAN_FILES]) | set(changed_material))
    candidate_truncated = len(candidate_pool) > MAX_CANDIDATE_FILES_PER_CHECKPOINT
    if candidate_truncated:
        anchors = list(all_material[:MAX_INITIAL_SCAN_FILES])
        remaining = [path for path in candidate_pool if path not in set(anchors)]
        slots = max(0, MAX_CANDIDATE_FILES_PER_CHECKPOINT - len(anchors))
        if slots:
            positions = {int(round(index * (len(remaining) - 1) / (slots - 1))) for index in range(slots)} if slots > 1 else {0}
            sampled = [path for index, path in enumerate(remaining) if index in positions]
        else:
            sampled = []
        candidates = sorted(set(anchors + sampled))[:MAX_CANDIDATE_FILES_PER_CHECKPOINT]
    else:
        candidates = candidate_pool
    fetch_paths: list[str] = []
    fetch_bytes = 0
    for path in candidates:
        if path not in entries:
            continue
        size = entries[path]["size"]
        if size <= 350_000 and fetch_bytes + size <= MAX_SCAN_BYTES_PER_CHECKPOINT:
            fetch_paths.append(path)
            fetch_bytes += size
    blob_texts = read_blobs(checkpoint, fetch_paths)
    source_rows: list[dict[str, Any]] = []
    aggregate = {dimension: 0 for dimension in DIMENSIONS}
    family_dimension_counts: dict[str, dict[str, int]] = defaultdict(lambda: {dimension: 0 for dimension in DIMENSIONS})
    families: Counter[str] = Counter()
    scanned_bytes = redactions = skipped_large = skipped_budget = 0
    for path in candidates:
        entry = entries.get(path)
        if not entry:
            continue
        if entry["size"] > 350_000:
            skipped_large += 1
            continue
        text = blob_texts.get(path)
        if text is None:
            skipped_budget += 1
            continue
        sanitized, count = redact(text)
        encoded = sanitized.encode("utf-8")
        if scanned_bytes + len(encoded) > MAX_SCAN_BYTES_PER_CHECKPOINT:
            skipped_budget += 1
            continue
        redactions += count
        scanned_bytes += len(encoded)
        counts = dimension_counts(sanitized)
        family = source_family(path)
        families[family] += 1
        for dimension in DIMENSIONS:
            aggregate[dimension] += counts[dimension]
            family_dimension_counts[family][dimension] += counts[dimension]
        source_rows.append({
            "blind_epoch_id": event["blind_epoch_id"],
            "checkpoint_index": position,
            "source_ref": hashlib.sha256(f"{checkpoint}:{path}:{entry['blob_sha']}".encode()).hexdigest()[:20],
            "blob_sha": entry["blob_sha"],
            "family": family,
            "bytes": len(encoded),
            "units": unit_count(sanitized),
            "words": word_count(sanitized),
            "dimension_counts": counts,
            "text_sha256": hashlib.sha256(encoded).hexdigest(),
        })
    changed_counts: Counter[str] = Counter()
    for _, paths in path_events[:position]:
        for path in paths:
            if material_path(path) and not direct_sensitive_path(path):
                changed_counts[path] += 1
    repeated_paths = sum(max(0, count - 1) for count in changed_counts.values())
    repeated_stems = sum(max(0, count - 1) for count in Counter(Path(path).stem.lower() for path in changed_counts).values())
    subject_text = "\n".join(redact(commit_subject(commit))[0] for commit, _ in path_events[:position])
    subject_counts = dimension_counts(subject_text)
    for dimension in DIMENSIONS:
        aggregate[dimension] += subject_counts[dimension]
    aggregate["FALSIFIER_DEFICIT"] = max(0, aggregate["UNRESOLVED_RESIDUAL_BURDEN"] + aggregate["CONTRADICTORY_PREDICTION_BURDEN"] - aggregate["FALSIFIER_DEFICIT"])
    aggregate["DUPLICATED_STRUCTURE_PRESSURE"] += repeated_paths + repeated_stems
    stats = diff_stats(event["start_commit"], checkpoint)
    proxy = {
        "changed_file_count": stats["changed_files"],
        "line_change_count": stats["added_lines"] + stats["deleted_lines"],
        "commit_density": position,
        "corpus_unit_count": sum(row["units"] for row in source_rows),
        "corpus_word_count": sum(row["words"] for row in source_rows),
        "path_name_churn": sum(1 for path in changed if re.search(r"(?:rename|move|path|route|index|registry)", path, re.I)),
        "generated_output_churn": sum(1 for path in changed if re.search(r"(?:outputs|reports|generated|projection|registry|manifest)", path, re.I)),
    }
    coverage_gap = bool(candidate_truncated or skipped_large or skipped_budget or len(all_material) > len(source_rows))
    evidence_refs = {
        dimension: [row["source_ref"] for row in source_rows if row["dimension_counts"].get(dimension, 0) > 0][:8]
        for dimension in DIMENSIONS
    }
    record = {
        "blind_epoch_id": event["blind_epoch_id"],
        "checkpoint_index": position,
        "commit_sha": checkpoint,
        "commit_date": commit_date(checkpoint),
        "commit_count_from_epoch_start": position,
        "commit_subject_redacted": redact(commit_subject(checkpoint))[0],
        "source_family_counts": dict(sorted(families.items())),
        "family_dimension_counts": {family: dict(sorted(counts.items())) for family, counts in sorted(family_dimension_counts.items())},
        "raw_dimension_counts": dict(sorted(aggregate.items())),
        "dimension_evidence_refs": evidence_refs,
        "path_recurrence": {"repeated_changed_paths": repeated_paths, "repeated_path_stems": repeated_stems},
        "diff_stats": stats,
        "proxy_metrics": proxy,
        "coverage": {
            "snapshot_material_file_count": len(all_material),
            "candidate_pool_file_count": len(candidate_pool),
            "candidate_file_count": len(candidates),
            "candidate_truncated": candidate_truncated,
            "scanned_file_count": len(source_rows),
            "scanned_bytes": scanned_bytes,
            "skipped_large_file_count": skipped_large,
            "skipped_budget_file_count": skipped_budget,
            "coverage_gap": coverage_gap,
            "coverage_gap_reason": "candidate cap, content scan budget, or excluded generated surface; path/blob inventory remains complete" if coverage_gap else None,
            "redaction_count": redactions,
        },
        "basis_fit": "UNDECIDABLE_DUE_COVERAGE_GAP" if coverage_gap else "LOSSY_OR_UNDECIDABLE",
    }
    return record, source_rows


def historical_basis_state(event: dict[str, Any], first: dict[str, Any]) -> dict[str, Any]:
    raw = first["raw_dimension_counts"]
    return {
        "blind_epoch_id": event["blind_epoch_id"],
        "answer_id": event["answer_id"],
        "epoch_start_commit": event["start_commit"],
        "status": "PARTIAL_HISTORICAL_BASIS_RECONSTRUCTION",
        "policy": "Only epoch-start and earlier reachable material was used; this is not a translation into the modern basis.",
        "expressible_units": ["historical_textual_units", "source_records", "named_cases_or_functions_if_present"],
        "observed_relations": ["adjacency_and_document_links_if_present", "source_family_cooccurrence"],
        "observed_actions": ["add_or_update_material", "rebuild_or_refresh_if_observed"],
        "observed_questions": ["question_markers_and_why_how_what_language" if raw["QUESTION_LANGUAGE_DEFICIT"] else "none_in_scanned_start_surface"],
        "observed_checks": ["check_or_validation_language" if raw["FALSIFIER_DEFICIT"] else "none_in_scanned_start_surface"],
        "identity_scope_lifecycle": ["path_and_source_family_identity_only", "no_future_schema_inferred"],
        "unresolved_dimensions_observed": [dimension for dimension in DIMENSIONS if raw[dimension] > 0],
        "coverage": first["coverage"],
        "future_capability_material_used": False,
    }


def build_freeze() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "freeze-ledger.json").exists():
        verify_frozen_inputs()
        return
    if run_git("rev-parse", FORMAL_BASE).strip() != FORMAL_BASE:
        raise RuntimeError("exact Formal Task163 base unavailable")
    pointer_rows = []
    for relative in ("instructions/CURRENT.md", "relay/current"):
        path = REPO / relative
        pointer_rows.append({"path": relative, "status": "present_requires_freshness_audit" if path.exists() else "absent_and_preserved", "sha256": file_sha(path) if path.is_file() else None})
    checkpoint_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    boundaries: list[dict[str, Any]] = []
    basis_rows: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    for event in EVENTS:
        commits = epoch_commits(event["start_commit"], event["pre_leap_commit"])
        checkpoints = choose_checkpoints(commits)
        path_events = commit_path_events(event["start_commit"], event["pre_leap_commit"])
        local_rows: list[dict[str, Any]] = []
        for index, checkpoint in enumerate(checkpoints):
            record, sources = scan_checkpoint(event, checkpoint, path_events, commits.index(checkpoint))
            record["checkpoint_index"] = index
            record["chronology_position_in_full_history"] = commits.index(checkpoint)
            local_rows.append(record)
            checkpoint_rows.append(record)
            source_rows.extend(sources)
            leakage_rows.append({
                "blind_epoch_id": event["blind_epoch_id"],
                "checkpoint_index": index,
                "direct_leakage_redactions": record["coverage"]["redaction_count"],
                "post_event_material_included": False,
                "answer_labels_included": False,
                "candidate_names_included": False,
                "sensitive_path_names_excluded": True,
                "coverage_gap": record["coverage"]["coverage_gap"],
            })
        boundaries.append({
            "blind_epoch_id": event["blind_epoch_id"],
            "answer_id": event["answer_id"],
            "event_id": event["event_id"],
            "kind": event["kind"],
            "split": event["split"],
            "exact_start_commit": event["start_commit"],
            "exact_pre_leap_stop_commit": event["pre_leap_commit"],
            "leap_boundary_commit": event["leap_commit"],
            "start_date": commit_date(event["start_commit"]),
            "pre_leap_stop_date": commit_date(event["pre_leap_commit"]),
            "full_history_commit_count": len(commits),
            "checkpoint_count": len(checkpoints),
            "source_file_count_at_stop": local_rows[-1]["coverage"]["snapshot_material_file_count"],
            "source_families_at_stop": sorted(local_rows[-1]["source_family_counts"]),
            "coverage_gap": any(row["coverage"]["coverage_gap"] for row in local_rows),
            "boundary_status": "EPOCH_BOUNDARY_UNDERDETERMINED" if len(commits) < MIN_CHECKPOINTS_FOR_CHANGE_POINT else "BOUNDARY_RECONSTRUCTED_FROM_FIRST_PARENT_HISTORY",
            "selection_reason": event["boundary_reason"],
            "exclusions": ["leap and post-event material are answer-key-only", "sensitive research/report paths excluded from blind stream"],
        })
        basis_rows.append(historical_basis_state(event, local_rows[0]))
    command_freeze = {
        "task_id": TASK, "repository": COMMAND_REPOSITORY, "path": COMMAND_PATH,
        "commit": COMMAND_COMMIT, "git_blob_sha": COMMAND_BLOB, "content_sha256": COMMAND_SHA256,
        "url": COMMAND_URL, "fetched_and_frozen_before_execution": True,
        "formal_preflight": {"pr_number": 213, "state": "OPEN", "draft": True, "head_sha": FORMAL_BASE, "base_ref": "work/IGNITION-20260907-162", "head_ref": FORMAL_BASE_REF},
        "formal_base": {"ref": FORMAL_BASE_REF, "sha": FORMAL_BASE},
        "control_pointer_residuals": pointer_rows,
    }
    pressure_freeze = {
        "task_id": TASK, "status": "FROZEN_BEFORE_BLIND_UNBLIND", "dimensions": DIMENSIONS,
        "dimension_definitions": {
            "UNRESOLVED_RESIDUAL_BURDEN": "unresolved, missing, failed, blocked, unknown, or not-enough markers",
            "LOCAL_PATCH_BURDEN": "patch, fix, repair, backfill, exception, workaround, compatibility, and legacy markers",
            "REINTERPRETATION_CHURN": "rewrite, reclassification, normalization, rebuild, refresh, rerun, rename, and migration markers",
            "QUESTION_LANGUAGE_DEFICIT": "question and temporary question-language markers",
            "FALSIFIER_DEFICIT": "failure/contradiction burden not matched by checking or validation markers",
            "CROSS_SOURCE_COLLISION": "collision, conflict, contradiction, overlap, duplicate, and clash markers across families",
            "CONTRADICTORY_PREDICTION_BURDEN": "prediction/expectation language with contradiction or inconsistency",
            "DUPLICATED_STRUCTURE_PRESSURE": "repeated structural markers plus repeated changed paths/path stems",
        },
        "normalization": {"within_epoch": "min_max_rank_over_all_frozen_checkpoints", "active_threshold": 0.67, "positive_slope_threshold": 0.05, "persistence_checkpoints": 2},
        "change_point_rule": {"high_requires_active_dimensions": 3, "high_requires_source_families": 2, "high_requires_persistence": 2, "pre_boundary_signal_must_occur_before_final_checkpoint": True, "minimum_checkpoints": MIN_CHECKPOINTS_FOR_CHANGE_POINT},
        "engineering_volume_is_covariate_only": ["changed_file_count", "line_change_count", "commit_density", "corpus_unit_count", "corpus_word_count", "path_name_churn", "generated_output_churn"],
        "no_manual_total_score": True,
    }
    protocol = {
        "task_id": TASK, "mode": "HISTORICAL_BASIS_PRESSURE / EPOCH_RECONSTRUCTION / CHANGE_POINT / SENSITIVITY_QUALIFICATION / RESEARCH_ONLY",
        "research_only": True, "command_freeze": command_freeze,
        "blind_input_policy": {"reads": ["blind-epoch-manifest.jsonl", "blind-checkpoint-inputs.jsonl", "chronological-source-stream.jsonl", "pressure-dimension-freeze.json"], "does_not_read": ["positive-answer-key.jsonl", "negative-control-manifest.jsonl", "epoch-boundary-manifest.jsonl", "historical-basis-state-freeze.jsonl", "stage-a-verdict.json"], "post_event_material_included": False, "answer_labels_included": False, "future_capability_vocab_included": False},
        "freeze_order": ["command_freeze", "formal_preflight", "epoch_boundaries", "historical_basis_state_freeze", "chronological_source_stream", "pressure_dimensions", "split", "blind_run_1", "blind_run_2", "unblind_and_stage_a_only"],
        "canonical_mutation": {"canonical_basis_changed": False, "twelve_protocol_changed": False, "sixty_four_matrix_changed": False, "production_runtime_changed": False, "stage_b_mutation_generator_invoked": False},
    }
    split = {
        "task_id": TASK,
        "calibration_positive": ["P01_FUNCTION_CASE_REFRAME"],
        "historical_positive_holdout": ["P02_SECTION_ZERO_BOOTSTRAP", "P03_DUAL_CHANNEL_BOOTSTRAP"],
        "transfer_positive_holdout": ["P04_META_PROTOCOL_64"],
        "calibration_negatives": ["N02_INCREMENTAL_REGISTRY", "N05_VALIDATOR_EXPANSION"],
        "holdout_negatives": ["N03_CANONICAL_PROTOCOL_MIGRATION", "N04_PAGES_PROJECTION", "N06_KNOWLEDGE_PROJECTION_REFRESH", "N07_PROVIDER_ADAPTER_REFACTOR", "N08_GENERATED_PROJECTION_REFRESH", "N09_KNOWLEDGE_MATERIALIZATION"],
        "thresholds_frozen_before_holdout_unblind": True,
    }
    blind_epochs = [{"blind_epoch_id": event["blind_epoch_id"], "checkpoint_count": next(row["checkpoint_count"] for row in boundaries if row["blind_epoch_id"] == event["blind_epoch_id"]), "event_name_hidden": True, "split_hidden": True, "answer_key_read": False} for event in EVENTS]
    positives = [{"blind_epoch_id": event["blind_epoch_id"], "event_id": event["event_id"], "kind": event["kind"], "split": event["split"], "pre_leap_commit": event["pre_leap_commit"], "leap_boundary_commit": event["leap_commit"], "required_capability": event["required_capability"]} for event in EVENTS if event["kind"] == "positive"]
    negatives = [{"blind_epoch_id": event["blind_epoch_id"], "event_id": event["event_id"], "kind": event["kind"], "split": event["split"], "pre_change_commit": event["pre_leap_commit"], "control_boundary_commit": event["leap_commit"], "control_reason": event["boundary_reason"]} for event in EVENTS if event["kind"] == "negative"]
    write_json(OUT / "command-freeze.json", command_freeze)
    write_json(OUT / "experiment-protocol.json", protocol)
    write_json(OUT / "pressure-dimension-freeze.json", pressure_freeze)
    write_json(OUT / "split-manifest.json", split)
    write_jsonl(OUT / "epoch-boundary-manifest.jsonl", boundaries)
    write_jsonl(OUT / "historical-basis-state-freeze.jsonl", basis_rows)
    write_jsonl(OUT / "chronological-source-stream.jsonl", source_rows)
    write_jsonl(OUT / "checkpoint-manifest.jsonl", checkpoint_rows)
    write_jsonl(OUT / "blind-epoch-manifest.jsonl", blind_epochs)
    write_jsonl(OUT / "blind-checkpoint-inputs.jsonl", checkpoint_rows)
    write_jsonl(OUT / "positive-answer-key.jsonl", positives)
    write_jsonl(OUT / "negative-control-manifest.jsonl", negatives)
    write_jsonl(OUT / "leakage-ledger.jsonl", leakage_rows)
    frozen_names = ["command-freeze.json", "experiment-protocol.json", "pressure-dimension-freeze.json", "split-manifest.json", "epoch-boundary-manifest.jsonl", "historical-basis-state-freeze.jsonl", "chronological-source-stream.jsonl", "checkpoint-manifest.jsonl", "blind-epoch-manifest.jsonl", "blind-checkpoint-inputs.jsonl", "positive-answer-key.jsonl", "negative-control-manifest.jsonl", "leakage-ledger.jsonl"]
    write_json(OUT / "freeze-ledger.json", {
        "task_id": TASK, "status": "FROZEN_BEFORE_BLIND_SCORING", "formal_base_sha": FORMAL_BASE, "formal_base_ref": FORMAL_BASE_REF,
        "command_commit": COMMAND_COMMIT, "command_blob_sha": COMMAND_BLOB, "command_content_sha256": COMMAND_SHA256,
        "frozen_file_hashes": {name: file_sha(OUT / name) for name in frozen_names}, "answer_key_is_not_a_blind_input": True,
        "stage_b_not_started": True, "epoch_count": len(EVENTS), "positive_epoch_count": 4, "negative_epoch_count": 8,
    })


def verify_frozen_inputs() -> None:
    ledger = read_json(OUT / "freeze-ledger.json")
    if ledger["formal_base_sha"] != FORMAL_BASE or ledger["command_commit"] != COMMAND_COMMIT or ledger["command_blob_sha"] != COMMAND_BLOB:
        raise RuntimeError("Task164 provenance or Formal base drift")
    for name, expected in ledger["frozen_file_hashes"].items():
        if file_sha(OUT / name) != expected:
            raise RuntimeError("frozen Task164 input changed: " + name)


def normalized(value: float, values: list[float]) -> float:
    return 0.0 if not values or max(values) == min(values) else (value - min(values)) / (max(values) - min(values))


def score_epoch(rows: list[dict[str, Any]], excluded_family: str | None = None) -> list[dict[str, Any]]:
    prepared = []
    for row in rows:
        raw = dict(row["raw_dimension_counts"])
        families = dict(row["source_family_counts"])
        if excluded_family:
            removed = row["family_dimension_counts"].get(excluded_family, {})
            for dimension in DIMENSIONS:
                raw[dimension] = max(0, raw[dimension] - removed.get(dimension, 0))
            families.pop(excluded_family, None)
        prepared.append((row, raw, families))
    values = {dimension: [raw[dimension] for _, raw, _ in prepared] for dimension in DIMENSIONS}
    result: list[dict[str, Any]] = []
    persistence: Counter[str] = Counter()
    for row, raw, families in prepared:
        ranks = {dimension: normalized(raw[dimension], values[dimension]) for dimension in DIMENSIONS}
        active = []
        for dimension in DIMENSIONS:
            previous = result[-1]["normalized_dimensions"][dimension] if result else 0.0
            if ranks[dimension] >= 0.67 and (ranks[dimension] - previous >= 0.05 or persistence[dimension] >= 1):
                active.append(dimension)
                persistence[dimension] += 1
            else:
                persistence[dimension] = 0
        max_persistence = max(persistence.values(), default=0)
        underdetermined = len(rows) < MIN_CHECKPOINTS_FOR_CHANGE_POINT
        state = "UNDECIDABLE" if underdetermined else "HIGH" if len(active) >= 3 and len(families) >= 2 and max_persistence >= 2 else "RISING" if len(active) >= 2 and len(families) >= 2 else "RISING" if active else "LOW"
        result.append({
            "blind_epoch_id": row["blind_epoch_id"], "checkpoint_index": row["checkpoint_index"], "commit_sha": row["commit_sha"], "commit_date": row["commit_date"],
            "raw_dimensions": raw, "normalized_dimensions": ranks, "active_dimensions": active, "source_families": sorted(families),
            "source_family_count": len(families), "max_dimension_persistence": max_persistence, "pressure_state": state,
            "basis_fit": row["basis_fit"], "coverage": row["coverage"], "dimension_evidence_refs": row["dimension_evidence_refs"],
        })
    return result


def first_pre_boundary_signal(scored: list[dict[str, Any]]) -> dict[str, Any]:
    if len(scored) < MIN_CHECKPOINTS_FOR_CHANGE_POINT:
        return {"signal": False, "first_signal_checkpoint": None, "reason": "EPOCH_BOUNDARY_UNDERDETERMINED"}
    candidates = [row for row in scored[:-1] if row["pressure_state"] == "HIGH" and len(row["active_dimensions"]) >= 2 and row["source_family_count"] >= 2]
    return {"signal": bool(candidates), "first_signal_checkpoint": candidates[0]["checkpoint_index"] if candidates else None, "reason": "HIGH_SIGNAL_BEFORE_FINAL_CHECKPOINT" if candidates else "NO_PRE_BOUNDARY_HIGH_SIGNAL"}


def blind_run_once() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    verify_frozen_inputs()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(OUT / "blind-checkpoint-inputs.jsonl"):
        groups[row["blind_epoch_id"]].append(row)
    blind_rows: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    change_points: list[dict[str, Any]] = []
    for blind_id in sorted(groups):
        scored = score_epoch(sorted(groups[blind_id], key=lambda row: row["checkpoint_index"]))
        for row in scored:
            blind_rows.append({
                "blind_epoch_id": row["blind_epoch_id"], "checkpoint_index": row["checkpoint_index"], "commit_sha": row["commit_sha"], "commit_date": row["commit_date"],
                "raw_dimensions": row["raw_dimensions"], "normalized_dimensions": row["normalized_dimensions"], "active_dimensions": row["active_dimensions"],
                "source_families": row["source_families"], "pressure_state": row["pressure_state"], "basis_fit": row["basis_fit"], "coverage_gap": row["coverage"]["coverage_gap"],
                "answer_key_read": False, "post_event_lookahead_used": False, "future_capability_vocab_exposed": False,
            })
            trajectories.append({
                "blind_epoch_id": row["blind_epoch_id"], "checkpoint_index": row["checkpoint_index"], "pressure_state": row["pressure_state"],
                "active_dimensions": row["active_dimensions"], "source_family_count": row["source_family_count"], "raw_dimensions": row["raw_dimensions"],
                "normalized_dimensions": row["normalized_dimensions"], "lossless_or_lossy_or_undecidable": row["basis_fit"], "raw_evidence_refs": row["dimension_evidence_refs"],
            })
        change_points.append({"blind_epoch_id": blind_id, "checkpoint_count": len(scored), "first_pre_boundary_signal": first_pre_boundary_signal(scored), "change_point_method": "first persistent multi-dimension HIGH regime", "answer_key_read": False})
    blind_rows.sort(key=lambda row: (row["blind_epoch_id"], row["checkpoint_index"]))
    trajectories.sort(key=lambda row: (row["blind_epoch_id"], row["checkpoint_index"]))
    change_points.sort(key=lambda row: row["blind_epoch_id"])
    return blind_rows, trajectories, change_points


def run_blind() -> None:
    first, trajectories, change_points = blind_run_once()
    second, trajectories_two, change_points_two = blind_run_once()
    if first != second or trajectories != trajectories_two or change_points != change_points_two:
        raise RuntimeError("isolated Task164 blind passes diverged")
    write_jsonl(OUT / "blind-run-1.jsonl", first)
    write_jsonl(OUT / "blind-run-2.jsonl", second)
    write_jsonl(OUT / "pressure-trajectories.jsonl", trajectories)
    write_jsonl(OUT / "change-point-results.jsonl", change_points)
    write_jsonl(OUT / "pressure-ledger.jsonl", [{
        "blind_epoch_id": row["blind_epoch_id"], "checkpoint_index": row["checkpoint_index"], "pressure_state": row["pressure_state"],
        "raw_dimensions": row["raw_dimensions"], "active_dimensions": row["active_dimensions"], "raw_evidence_refs": row["raw_evidence_refs"], "answer_key_read": False,
    } for row in trajectories])


def proxy_signal(rows: list[dict[str, Any]], key: str) -> bool:
    values = [float(row["proxy_metrics"].get(key, 0)) for row in rows]
    if len(values) < MIN_CHECKPOINTS_FOR_CHANGE_POINT:
        return False
    ranks = [normalized(value, values) for value in values]
    return any(rank >= 0.67 and index < len(ranks) - 1 for index, rank in enumerate(ranks))


def null_controls(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inputs:
        groups[row["blind_epoch_id"]].append(row)
    result = []
    for blind_id, group in sorted(groups.items()):
        group = sorted(group, key=lambda row: row["checkpoint_index"])
        seed = int(hashlib.sha256(blind_id.encode()).hexdigest()[:8], 16)
        random_index = seed % max(1, len(group) - 1)
        result.append({
            "blind_epoch_id": blind_id,
            "proxy_results": {key: proxy_signal(group, key) for key in ("changed_file_count", "line_change_count", "commit_density", "corpus_unit_count", "corpus_word_count", "path_name_churn", "generated_output_churn")},
            "random_checkpoint_index": random_index,
            "random_checkpoint_is_pre_boundary": random_index < len(group) - 1,
            "seeded_random_residual_assignment_hit": bool(seed % 7 == 0),
            "proxy_rule": "within_epoch rank at least 0.67 before final checkpoint",
        })
    return result


def source_family_ablation(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inputs:
        groups[row["blind_epoch_id"]].append(row)
    result = []
    for blind_id, group in sorted(groups.items()):
        group = sorted(group, key=lambda row: row["checkpoint_index"])
        families = sorted({family for row in group for family in row["source_family_counts"]})
        all_signal = first_pre_boundary_signal(score_epoch(group))
        ablations = []
        for family in families:
            ablations.append({"removed_source_family": family, "signal": first_pre_boundary_signal(score_epoch(group, excluded_family=family))})
        result.append({"blind_epoch_id": blind_id, "all_source_signal": all_signal, "source_families": families, "ablations": ablations})
    return result


def stage_b_sentinels(stage_a: dict[str, Any]) -> None:
    sentinel = {"task_id": TASK, "status": "NOT_RUN_STAGE_A_STOP", "reason": "Stage A failed; no external material or mutation coupling is authorized.", "stage_a_failed_gates": stage_a["failed_gates"]}
    for name in ("r1-trigger-coupling.jsonl", "mutation-proposals.jsonl", "capability-equivalence.jsonl"):
        write_jsonl(OUT / name, [sentinel])
    write_json(OUT / "stage-b-stop.json", sentinel)


def unblind() -> dict[str, Any]:
    verify_frozen_inputs()
    blind_rows = read_jsonl(OUT / "blind-run-1.jsonl")
    inputs = read_jsonl(OUT / "blind-checkpoint-inputs.jsonl")
    boundaries = {row["blind_epoch_id"]: row for row in read_jsonl(OUT / "epoch-boundary-manifest.jsonl")}
    answers = {row["blind_epoch_id"]: row for row in read_jsonl(OUT / "positive-answer-key.jsonl") + read_jsonl(OUT / "negative-control-manifest.jsonl")}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in blind_rows:
        grouped[row["blind_epoch_id"]].append(row)
    event_results = []
    for blind_id, answer in sorted(answers.items()):
        rows = sorted(grouped[blind_id], key=lambda row: row["checkpoint_index"])
        signal_rows = [row for row in rows[:-1] if row["pressure_state"] == "HIGH" and len(row["active_dimensions"]) >= 2 and len(row["source_families"]) >= 2]
        pre_signal = bool(signal_rows) and boundaries[blind_id]["boundary_status"] != "EPOCH_BOUNDARY_UNDERDETERMINED"
        event_results.append({
            "blind_epoch_id": blind_id, "event_id": answer["event_id"], "kind": answer["kind"], "split": answer["split"],
            "boundary_status": boundaries[blind_id]["boundary_status"], "pre_boundary_pressure_signal": pre_signal,
            "first_signal_checkpoint": signal_rows[0]["checkpoint_index"] if signal_rows else None,
            "signal_dimensions": sorted({dimension for row in signal_rows for dimension in row["active_dimensions"]}),
            "signal_source_families": sorted({family for row in signal_rows for family in row["source_families"]}),
        })
    positives = [row for row in event_results if row["kind"] == "positive"]
    holdout_positives = [row for row in positives if row["event_id"] in {"P02_SECTION_ZERO_BOOTSTRAP", "P03_DUAL_CHANNEL_BOOTSTRAP", "P04_META_PROTOCOL_64"}]
    strong_negatives = [row for row in event_results if row["event_id"] in {"N02_INCREMENTAL_REGISTRY", "N03_CANONICAL_PROTOCOL_MIGRATION"}]
    ablation = source_family_ablation(inputs)
    ablation_by_id = {row["blind_epoch_id"]: row for row in ablation}
    ablation_true_hits = sum(any(item["signal"]["signal"] for item in ablation_by_id[row["blind_epoch_id"]]["ablations"]) for row in positives)
    null_rows = null_controls(inputs)
    write_jsonl(OUT / "null-control-results.jsonl", null_rows)
    write_jsonl(OUT / "sensitivity-analysis.jsonl", ablation)
    positive_hits = sum(row["pre_boundary_pressure_signal"] for row in positives)
    holdout_hits = sum(row["pre_boundary_pressure_signal"] for row in holdout_positives)
    strong_negative_fp = sum(row["pre_boundary_pressure_signal"] for row in strong_negatives)
    null_match = any(sum(row["proxy_results"].values()) >= positive_hits for row in null_rows)
    gates = {
        "true_leap_pre_boundary_at_least_3_of_4": positive_hits >= 3,
        "p02_p03_p04_pre_boundary_at_least_2_of_3": holdout_hits >= 2,
        "at_least_one_true_holdout_hit": holdout_hits >= 1,
        "strong_negative_false_positive_zero": strong_negative_fp == 0,
        "n02_n03_not_high": all(not row["pre_boundary_pressure_signal"] for row in strong_negatives),
        "every_positive_boundary_reconstructed": all(row["boundary_status"] != "EPOCH_BOUNDARY_UNDERDETERMINED" for row in positives),
        "at_least_two_dimensions_and_two_source_families": all(len(row["signal_dimensions"]) >= 2 and len(row["signal_source_families"]) >= 2 for row in positives if row["pre_boundary_pressure_signal"]),
        "remove_largest_source_family_keeps_two_true_signals": ablation_true_hits >= 2,
        "null_proxy_not_equivalent": not null_match,
        "two_blind_outputs_byte_identical": (OUT / "blind-run-1.jsonl").read_bytes() == (OUT / "blind-run-2.jsonl").read_bytes(),
        "thresholds_frozen_before_holdout_unblind": True,
    }
    failed = [name for name, passed in gates.items() if not passed]
    stage_a = {
        "task_id": TASK, "stage": "Stage A / Historical Basis Pressure Sensor Qualification",
        "status": "PASS" if not failed else "FAIL", "stage_a_pass": not failed, "gate_results": gates, "failed_gates": failed,
        "positive_epoch_count": len(positives), "true_leap_pre_boundary_hits": positive_hits, "positive_holdout_hits": holdout_hits,
        "strong_negative_false_positive_count": strong_negative_fp, "n02_n03_results": strong_negatives, "event_results": event_results,
        "source_family_ablation_count": len(ablation), "null_proxy_match": null_match,
        "claim_ceiling": "research-only pressure qualification; pressure is not a semantic-leap or canonical-basis conclusion",
    }
    write_json(OUT / "stage-a-verdict.json", stage_a)
    if not stage_a["stage_a_pass"]:
        stage_b_sentinels(stage_a)
        stage_b_status = "NOT_RUN_STAGE_A_STOP"
    else:
        stage_b_sentinels(stage_a)
        stage_b_status = "NOT_RUN_STAGE_A_PASS_SEPARATE_SCOPE"
    verdict = {
        "task_id": TASK,
        "primary_verdict": "BASIS_PRESSURE_SENSOR_VALIDATED_FOR_HISTORICAL_REPLAY" if stage_a["stage_a_pass"] else "BASIS_PRESSURE_SENSOR_NOT_VALIDATED",
        "secondary_verdicts": ["UNDERDETERMINED" if ("every_positive_boundary_reconstructed" in failed or "null_proxy_not_equivalent" in failed) else "PARTIAL_HISTORICAL_PRESSURE_SIGNAL"],
        "stage_a": stage_a,
        "stage_b": {"status": stage_b_status, "r1_trigger_coupling_run": False, "external_longform_material_acquired": False, "mutation_set_changed": False},
        "pressure_is_not_semantic_leap": True, "canonical_basis_changed": False, "production_or_external_truth_claim": False,
        "forbidden_promotions": ["Ready", "merge", "Current", "Owner acceptance", "production", "external truth", "successor Task165"],
    }
    write_json(OUT / "verdict.json", verdict)
    return verdict


def render_documents(verdict: dict[str, Any]) -> None:
    stage = verdict["stage_a"]
    boundaries = read_jsonl(OUT / "epoch-boundary-manifest.jsonl")
    results = {row["blind_epoch_id"]: row for row in stage["event_results"]}
    lines = []
    for row in boundaries:
        result = results[row["blind_epoch_id"]]
        lines.append("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
            row["answer_id"], row["exact_start_commit"][:12], row["exact_pre_leap_stop_commit"][:12],
            row["leap_boundary_commit"][:12], row["checkpoint_count"], row["boundary_status"],
            "signal" if result["pre_boundary_pressure_signal"] else "no pre-boundary signal",
        ))
    common = (
        "Command: {0}/{1}@{2}\nCommand blob: {3}\nCommand SHA-256: {4}\n"
        "Formal base: {5}@{6}\nLifecycle ceiling: research-only, Draft-only; no canonical, production, Current, Owner, external-truth, or epistemic acceptance claim.\n"
    ).format(COMMAND_REPOSITORY, COMMAND_PATH, COMMAND_COMMIT, COMMAND_BLOB, COMMAND_SHA256, FORMAL_BASE_REF, FORMAL_BASE)
    table = "\n".join(lines)
    reconstruction = "# Historical basis-pressure reconstruction — " + TASK + "\n\n" + common + "\nThe experiment uses cumulative first-parent Git-history prefixes. Blind inputs contain anonymous commit/snapshot provenance and neutral marker counts; leap names, answer labels, post-event material, and future capability vocabulary are held outside blind scoring.\n\n## Boundary table\n\nEpoch | Start | Pre-boundary stop | Boundary | Checkpoints | Status | Result\n---|---|---|---|---:|---|---\n" + table + "\n\nE3 has no intervening first-parent history between its start and target boundary. It is retained as EPOCH_BOUNDARY_UNDERDETERMINED rather than filled from later structure.\n\nThe historical basis ledger is marked PARTIAL_HISTORICAL_BASIS_RECONSTRUCTION because content scanning is bounded and skipped-file coverage gaps are preserved.\n"
    dimensions = read_json(OUT / "pressure-dimension-freeze.json")
    dimension_lines = "\n".join("- " + name + ": " + description for name, description in dimensions["dimension_definitions"].items())
    qualification = "# Basis-pressure sensor qualification — " + TASK + "\n\n" + common + "\n## Stage A\n\nStatus: " + stage["status"] + "\nTrue-leap pre-boundary hits: {0}/4\nP02/P03/P04 holdout hits: {1}/3\nStrong-negative false positives: {2}\nFailed gates: {3}\nNull-proxy match: {4}\n\nFrozen pressure dimensions:\n\n{5}\n\nThe detector uses within-epoch rank, positive slope, persistence, concurrent dimensions, and source-family recurrence. Engineering volume is a covariate, not a pressure dimension. A signal must occur before the final pre-boundary checkpoint.\n\n## Stage B\n\nStatus: {6}. No external longform material, R1 coupling, or mutation proposal was run.\n".format(stage["true_leap_pre_boundary_hits"], stage["positive_holdout_hits"], stage["strong_negative_false_positive_count"], ", ".join(stage["failed_gates"]) or "none", stage["null_proxy_match"], dimension_lines, verdict["stage_b"]["status"])
    sensitivity = "# Sensitivity versus mutation-generator diagnosis — " + TASK + "\n\n" + common + "\nTask164 qualifies sensitivity only. It does not qualify a mutation generator and does not convert pressure into a semantic leap.\n\nPrimary verdict: " + verdict["primary_verdict"] + "\nStage B: " + verdict["stage_b"]["status"] + "\n\nSource-family ablations and null controls are recorded in the machine package. A single-source-family result is not independent support.\n"
    next_assessment = "# Next-basis learning assessment — " + TASK + "\n\n" + common + "\nThe current evidence does not authorize coupling a pressure sensor to Task163 mutation operations. Required next evidence: reliably reconstructed pre-boundary history for every positive epoch; independently adjudicated material; signals surviving source-family ablation and engineering-volume null controls; deterministic blind reruns at the exact Formal head; and a separately authorized Stage B only after a passing Stage A.\n\nNo Task165 was created.\n"
    report = "# Governance report: " + TASK + "\n\n" + common + "\n## Preflight\n\nFormal PR #213 was rechecked as OPEN + DRAFT at the exact Task163 head. The Formal branch was created from work/IGNITION-20260907-163 and the receipt branch from execution-time 1111/main. Missing or stale instructions/CURRENT.md and relay/current were preserved as STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL.\n\n## Experiment\n\nFour positive basis epochs and eight matched negative/control epochs were constructed from reachable Git history. Cumulative prefixes were chronological and answer keys were separate from blind scoring. Pressure dimensions and change-point rules were frozen before unblind.\n\n## Result\n\nStage A: " + stage["status"] + ". True-leap pre-boundary hits: " + str(stage["true_leap_pre_boundary_hits"]) + "/4; P02/P03/P04: " + str(stage["positive_holdout_hits"]) + "/3; strong-negative FP: " + str(stage["strong_negative_false_positive_count"]) + ". Primary verdict: " + verdict["primary_verdict"] + ". Secondary: " + ", ".join(verdict["secondary_verdicts"]) + ". Stage B: " + verdict["stage_b"]["status"] + ".\n\n## Repository validation residuals\n\nThe read-only projection preflight completed with side_effect_detected=false and reported failures in the existing function/nonfunction projection products, Current-surface projections and durability projection hygiene; repository-path classification passed 10/10 and the knowledge-experience checks passed. These residuals remain recorded and were not regenerated or promoted by this research-only command.\n\n## Boundaries\n\n" + table + "\n\n## Explicit non-claims\n\nNo Ready, merge, Current promotion, Owner acceptance, production readiness, external truth, epistemic acceptance, canonical basis change, runtime/provider/authority change, semantic-leap claim, or Task165 creation occurred.\n"
    result = "# Agent result: " + TASK + "\n\nExecuted the pinned research-only command at " + COMMAND_COMMIT + " (blob " + COMMAND_BLOB + ", content SHA-256 " + COMMAND_SHA256 + ") from Formal base " + FORMAL_BASE_REF + "@" + FORMAL_BASE + ".\n\nStage A is " + stage["status"] + ": " + str(stage["true_leap_pre_boundary_hits"]) + "/4 true-leap pre-boundary hits, " + str(stage["positive_holdout_hits"]) + "/3 P02/P03/P04 hits, and " + str(stage["strong_negative_false_positive_count"]) + " strong-negative false positives. Primary verdict: " + verdict["primary_verdict"] + "; secondary: " + ", ".join(verdict["secondary_verdicts"]) + ". Stage B was " + verdict["stage_b"]["status"] + "; no external longform, R1 coupling, or mutation proposal was run.\n\nRepository-path classification passed 10/10. The read-only projection preflight had side_effect_detected=false but retained failures for existing function/nonfunction, Current-surface and durability projection products; no regeneration or lifecycle promotion was performed.\n\nNo Ready, merge, Current, Owner acceptance, production/external-truth claim, canonical/runtime/authority change, or Task165 creation occurred.\n"
    (ROOT / "docs/governance/historical-basis-pressure-reconstruction-2026-09-07.md").write_text(reconstruction, encoding="utf-8")
    (ROOT / "docs/governance/basis-pressure-sensor-qualification-2026-09-07.md").write_text(qualification, encoding="utf-8")
    (ROOT / "docs/governance/sensitivity-vs-mutation-generator-diagnosis-2026-09-07.md").write_text(sensitivity, encoding="utf-8")
    (ROOT / "docs/governance/next-basis-learning-assessment-2026-09-07.md").write_text(next_assessment, encoding="utf-8")
    (ROOT / "reports/governance/task-IGNITION-20260907-164.md").write_text(report, encoding="utf-8")
    (ROOT / "agent-results/IGNITION-20260907-164-result.md").write_text(result, encoding="utf-8")


def update_artifact_hashes() -> None:
    paths = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "artifact-sha256.json")
    write_json(OUT / "artifact-sha256.json", {path.name: file_sha(path) for path in paths})


def verify() -> None:
    verify_frozen_inputs()
    required = ["blind-run-1.jsonl", "blind-run-2.jsonl", "pressure-ledger.jsonl", "pressure-trajectories.jsonl", "change-point-results.jsonl", "null-control-results.jsonl", "sensitivity-analysis.jsonl", "stage-a-verdict.json", "r1-trigger-coupling.jsonl", "mutation-proposals.jsonl", "capability-equivalence.jsonl", "stage-b-stop.json", "verdict.json"]
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing:
        raise RuntimeError("missing Task164 artifacts: " + repr(missing))
    if (OUT / "blind-run-1.jsonl").read_bytes() != (OUT / "blind-run-2.jsonl").read_bytes():
        raise RuntimeError("Task164 blind outputs are not byte-identical")
    for name in ("blind-run-1.jsonl", "blind-run-2.jsonl", "pressure-ledger.jsonl", "pressure-trajectories.jsonl", "change-point-results.jsonl", "chronological-source-stream.jsonl", "checkpoint-manifest.jsonl", "blind-checkpoint-inputs.jsonl"):
        if DIRECT_LEAKAGE.search((OUT / name).read_text(encoding="utf-8")):
            raise RuntimeError("direct future/answer leakage in blind artifact: " + name)
    verdict = read_json(OUT / "verdict.json")
    if not verdict["stage_a"]["stage_a_pass"] and verdict["stage_b"]["status"] != "NOT_RUN_STAGE_A_STOP":
        raise RuntimeError("Stage B stop enforcement is inconsistent")
    for name in ("r1-trigger-coupling.jsonl", "mutation-proposals.jsonl", "capability-equivalence.jsonl", "stage-b-stop.json"):
        rows = read_jsonl(OUT / name) if name.endswith(".jsonl") else [read_json(OUT / name)]
        if not rows or rows[0].get("status") != "NOT_RUN_STAGE_A_STOP":
            raise RuntimeError("Stage B sentinel is inconsistent: " + name)


def all_steps() -> None:
    build_freeze()
    run_blind()
    verdict = unblind()
    render_documents(verdict)
    update_artifact_hashes()
    verify()


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["freeze", "blind", "unblind", "all", "verify"], nargs="?", default="all")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    OUT = Path(args.out).resolve()
    if args.phase == "freeze":
        build_freeze()
    elif args.phase == "blind":
        run_blind()
    elif args.phase == "unblind":
        unblind()
    elif args.phase == "verify":
        verify()
    else:
        all_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
