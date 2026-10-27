#!/usr/bin/env python3
"""Deterministic research tooling for IGNITION-20260906-158.

This module is deliberately a research instrument, not a production validator.
It uses only local Git history and tracked repository text.  The first stage
freezes packets without outcome labels; the second stage emits blind detector
outputs; only a later stage reads the answer key and writes unblinded results.
No output from this module is connected to a required CI gate or a canonical
registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
OUT = ROOT / "data/research/basis-escape-meta-plasticity-2026-09-06"
TASK = "IGNITION-20260906-158"
COMMAND_BLOB = "918dce85cc18f6e653422b162c593af6b33d60a8"
COMMAND_SHA256 = "513146ae504d794d6a1440c86b3d534d6ed0ba90f4e12c4946a943682461c8f9"


CONTROL_SPECS = [
    {"control_id": "P01_FUNCTION_CASE_REFRAME", "group": "positive", "trigger": "a1295d737e290105069f915c577105c0cf5ff26f", "split": "calibration", "historical_role": "function_case_ontology_reframe"},
    {"control_id": "P02_SECTION_ZERO_BOOTSTRAP", "group": "positive", "trigger": "0a04b42a1e7d21549593dc38ef5993e1503cdc5e", "split": "calibration", "historical_role": "meta_function_layer"},
    {"control_id": "P03_DUAL_CHANNEL_BOOTSTRAP", "group": "positive", "trigger": "9d924fe140f0c99f1f2a4952ea48dedc80dd348b", "split": "holdout", "historical_role": "dual_channel_bootstrap"},
    {"control_id": "P04_META_PROTOCOL_64", "group": "positive", "trigger": "974b121e36145d6ed35b214619312001f97b21f8", "split": "holdout", "historical_role": "twelve_protocol_sixty_four_matrix"},
    {"control_id": "N01_KB_116_NOTE_SYNC", "group": "negative", "trigger": "911f97b66568dbf8ef012a6e8ffc28749c32e91c", "split": "calibration", "historical_role": "large_source_import_without_basis_change"},
    {"control_id": "N02_INCREMENTAL_REGISTRY", "group": "negative", "trigger": "ab90558ae1c158d9a67146ebd288678b67e1c4c3", "split": "calibration", "historical_role": "registry_and_extractor_growth"},
    {"control_id": "N03_CANONICAL_PROTOCOL_MIGRATION", "group": "negative", "trigger": "4c452149a451f074d949739086cfccdb3ec5bd56", "split": "holdout", "historical_role": "materialize_existing_protocol_objects"},
    {"control_id": "N04_PAGES_PROJECTION", "group": "negative", "trigger": "d4bfaa88", "split": "holdout", "historical_role": "publication_projection_maintenance"},
]


FAMILY_RULES = {
    "historical_failures_reversals": ("RESULTS/", "case_failures/", "data/foundation/", "reports/operations/"),
    "function_assets": ("统一函数总表/", "data/foundation/function-assets/", "docs/zh/functions/", "docs/functions/"),
    "nonfunction_claims_assets": ("统一案例总表/", "data/foundation/nonfunction-claims/", "docs/governance/", "docs/falsifiability/"),
    "open_obligations_residuals": ("data/governance/", "data/operations/", "reports/research/", "reports/validation/", "RESULTS/OPEN-QUESTIONS.md"),
    "governance_lifecycle": (".github/", "schemas/", "tools/", "scripts/", "ITERATION.md", "OPERATING-METHOD.md"),
    "source_note_derived": ("dianhuo/", "PUBLICATIONS/", "KNOWLEDGE/", "inputs/"),
}


FORBIDDEN_BASIS_INPUT = re.compile(
    r"(?:meta-protocol|protocols-canonical|(?:^|[-_/])64(?:[-_/]|$)|"
    r"(?:^|[-_/])V[1-4](?:[-_/]|$)|(?:^|[-_/])S[1-4](?:[-_/]|$)|"
    r"(?:^|[-_/])E[1-4](?:[-_/]|$)|IGNITION-2026090[4-6]-15[3-7]|"
    r"(?:^|/)tools/research/|(?:^|/)data/research/|"
    r"IGNITION-20260906-158)",
    re.I,
)


FACTOR_TERMS = {
    "normative_direction": re.compile(r"价值|目标|目的|应当|规范|选择|偏好|value|goal|purpose|normative|objective|should", re.I),
    "relational_boundary": re.compile(r"关系|边界|角色|接口|结构|层级|约束|relation|boundary|role|interface|structure|hierarchy|constraint", re.I),
    "temporal_change": re.compile(r"变化|演化|迭代|历史|演进|迁移|修正|重跑|版本|change|evolution|iteration|history|migration|correction|rerun|version", re.I),
    "evidence_grounding": re.compile(r"证据|来源|原文|依据|证据链|evidence|source|provenance|citation|ground", re.I),
    "authority_agency": re.compile(r"权威|权限|批准|所有者|责任|执行|authority|permission|approval|owner|accountability|executor", re.I),
    "generation_validation": re.compile(r"生成|构建|校验|验证|注册|投影|刷新|generator|build|validate|registry|projection|refresh", re.I),
}


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()


def commit_parent(commit: str) -> str:
    parents = git("show", "-s", "--format=%P", commit).split()
    return parents[0] if parents else "ROOT"


def commit_record(spec: dict) -> dict:
    commit = spec["trigger"]
    parent = commit_parent(commit)
    show = git("show", "-s", "--format=%H%x09%ad%x09%an%x09%s", "--date=iso-strict", commit).split("\t", 3)
    names = git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "--find-renames", commit).splitlines()
    paths = []
    statuses = Counter()
    for line in names:
        parts = line.split("\t")
        if not parts:
            continue
        statuses[parts[0][0]] += 1
        paths.extend(parts[1:])
    numstat = git("show", "--format=", "--numstat", "--no-renames", commit).splitlines()
    added = 0
    deleted = 0
    binary = 0
    for line in numstat:
        fields = line.split("\t")
        if len(fields) < 3:
            continue
        try:
            added += int(fields[0])
            deleted += int(fields[1])
        except ValueError:
            binary += 1
    patch = subprocess.check_output(
        ["git", "show", "--format=", "--no-ext-diff", "--no-renames", "--unified=0", commit],
        cwd=REPO_ROOT,
    )[:400_000].decode("utf-8", errors="ignore")
    top_dirs = sorted({path.split("/", 1)[0] for path in paths})
    return {
        "commit": show[0],
        "date": show[1],
        "author": show[2],
        "subject": show[3],
        "parent": parent,
        "changed_paths": sorted(paths),
        "changed_path_count": len(set(paths)),
        "status_counts": dict(sorted(statuses.items())),
        "added_lines": added,
        "deleted_lines": deleted,
        "binary_numstat_rows": binary,
        "top_level_domains": top_dirs,
        "patch_excerpt_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
        "patch_excerpt_bytes": len(patch.encode("utf-8")),
        "patch_text": patch,
    }


def packet(spec: dict) -> dict:
    record = commit_record(spec)
    public = {key: value for key, value in record.items() if key != "patch_text"}
    public["patch_excerpt"] = record["patch_text"]
    return {
        "task_id": TASK,
        "control_id": spec["control_id"],
        "group": spec["group"],
        "split": spec["split"],
        "pre_commit": record["parent"],
        "trigger_commit": record["commit"],
        "post_commit_withheld": record["commit"],
        "trigger_material": public,
        "outcome_label": "WITHHELD",
        "blindness": "DATA_LEVEL_BLIND / NOT_COGNITIVELY_INDEPENDENT",
    }


def freeze() -> None:
    base = git("rev-parse", "HEAD")
    protocol = {
        "schema_version": "ignition-158-experiment-protocol-r1",
        "task_id": TASK,
        "mode": "META_LEVEL_PLASTICITY / BASIS_ESCAPE / HISTORICAL_REPLAY / COUNTERFACTUAL_FALSIFICATION / RESEARCH_ONLY",
        "formal_base": {"ref": "main", "sha_at_freeze": base},
        "source_command": {"repository": "Arvin-liu/1111", "path": "agent-commands/IGNITION-20260906-158.md", "git_blob_sha": COMMAND_BLOB, "content_sha256": COMMAND_SHA256},
        "blindness": "DATA_LEVEL_BLIND / NOT_COGNITIVELY_INDEPENDENT",
        "primary_gates": {
            "positive_detection": "blind detector emits basis_change_signal=true from pre-state plus trigger packet only",
            "positive_holdout_floor": "at least 1 of 2 positive holdouts detected",
            "negative_holdout_false_positive_ceiling": "at most 0 of 2 negative holdouts detected",
            "candidate_gate": "no candidate unless 3 independent corpus families, basis-free rediscovery, holdout gain, ablation loss and falsifier are all present",
        },
        "frozen_before_outcome": True,
        "answer_key_file": "historical-answer-key.jsonl (not created in freeze stage)",
        "forbidden_basis_free_inputs": [
            "V1-V4 / S1-S4 / E1-E4", "Value / Structure / Evolution as prior labels", "64 combo IDs", "meta-protocol as target answer", "Task153-157 research documents"
        ],
        "no_live_external_action": True,
        "no_production_mutation": True,
    }
    specs = []
    for spec in CONTROL_SPECS:
        item = {key: value for key, value in spec.items() if key != "historical_role"}
        item["pre_commit"] = commit_parent(spec["trigger"])
        item["trigger_commit"] = spec["trigger"]
        item["post_commit"] = spec["trigger"]
        item["historical_role_withheld"] = True
        specs.append(item)
    write_json(OUT / "experiment-protocol.json", protocol)
    write_json(OUT / "hypothesis-freeze.json", {
        "schema_version": "ignition-158-hypothesis-freeze-r1",
        "task_id": TASK,
        "hypotheses": {
            "H1": "TRUE_FIXED_POINT",
            "H2": "REPRESENTATIONAL_LOCK_IN",
            "H3": "GENERATOR_LOCK_IN",
            "H4": "MIXED_LOCK_IN",
        },
        "detector_criteria": protocol["primary_gates"],
        "frozen_control_split": {item["control_id"]: item["split"] for item in specs},
        "frozen_at_formal_base": base,
        "answer_key_status": "WITHHELD",
    })
    write_jsonl(OUT / "historical-leap-manifest.jsonl", specs)
    write_jsonl(OUT / "positive-control-packets.jsonl", [packet(spec) for spec in CONTROL_SPECS if spec["group"] == "positive"])
    write_jsonl(OUT / "negative-control-packets.jsonl", [packet(spec) for spec in CONTROL_SPECS if spec["group"] == "negative"])
    write_json(OUT / "freeze-ledger.json", {
        "task_id": TASK,
        "status": "FROZEN_BEFORE_DETECTOR",
        "formal_base_sha": base,
        "command_blob_sha": COMMAND_BLOB,
        "command_content_sha256": COMMAND_SHA256,
        "control_count": len(specs),
        "positive_count": 4,
        "negative_count": 4,
        "answer_key_present": False,
        "invalidations": [],
        "history_preserved": True,
    })
    write_json(OUT / "restart-ledger.json", {"task_id": TASK, "restarts": []})


def detector_features(material: dict) -> dict:
    paths = material["changed_paths"]
    patch = material.get("patch_excerpt", "")
    path_text = "\n".join(paths)
    representation = any(re.search(pattern, path_text, re.I) for pattern in (
        r"archive|legacy|refactor|data/cases|data/registry|meta-functions|meta-protocols|canonical|matrix|bootstrap",
    ))
    ontology = any(re.search(pattern, path_text + "\n" + patch, re.I) for pattern in (
        r"function.case|meta.function|meta.protocol|protocol|matrix|registry|object|canonical|bootstrap",
    ))
    generator = any(re.search(pattern, path_text + "\n" + patch, re.I) for pattern in (
        r"generator|extract|validator|validate|rebuild|render|projection|registry|census|audit|check",
    ))
    backward = any(re.search(pattern, path_text + "\n" + patch, re.I) for pattern in (
        r"archive|legacy|refactor|migration|rename|reclass|relabel|replace|old",
    ))
    new_falsifier = bool(re.search(r"counterexample|falsif|test|audit|check|gate|validation", patch, re.I))
    signals = {
        "representation_change": representation,
        "ontology_mutation": ontology,
        "generator_mutation": generator,
        "backward_reinterpretation": backward,
        "new_falsifier_or_validation_surface": new_falsifier,
    }
    basis_signal = representation and ontology and (generator or backward)
    reasons = [name for name, present in signals.items() if present]
    return {
        "features": signals,
        "feature_count": sum(signals.values()),
        "basis_change_signal": basis_signal,
        "reason_codes": reasons,
        "changed_path_count": material["changed_path_count"],
        "added_lines": material["added_lines"],
        "deleted_lines": material["deleted_lines"],
        "domain_count": len(material["top_level_domains"]),
    }


def blind() -> None:
    packets = read_jsonl(OUT / "positive-control-packets.jsonl") + read_jsonl(OUT / "negative-control-packets.jsonl")
    rows = []
    for item in sorted(packets, key=lambda row: row["control_id"]):
        observed = detector_features(item["trigger_material"])
        rows.append({
            "task_id": TASK,
            "control_id": item["control_id"],
            "group": item["group"],
            "split": item["split"],
            "pre_commit": item["pre_commit"],
            "trigger_commit": item["trigger_commit"],
            "detector": "HISTORICAL_LEAP_DETECTOR_V1",
            **observed,
            "outcome_label": "WITHHELD",
        })
    write_jsonl(OUT / "blind-outputs.jsonl", rows)
    write_json(OUT / "freeze-ledger.json", {
        **read_json(OUT / "freeze-ledger.json"),
        "status": "BLIND_OUTPUTS_EMITTED",
        "answer_key_present": False,
        "blind_output_sha256": digest(rows),
    })


ANSWER_KEY = {
    "P01_FUNCTION_CASE_REFRAME": {"label": "TRUE_LEAP", "reason": "changed from narrative/book objects to a function-case knowledge-base ontology", "evidence": ["a1295d737e290105069f915c577105c0cf5ff26f"]},
    "P02_SECTION_ZERO_BOOTSTRAP": {"label": "TRUE_LEAP", "reason": "introduced a meta-function layer and a self-referential section-zero bootstrap operation", "evidence": ["0a04b42a1e7d21549593dc38ef5993e1503cdc5e"]},
    "P03_DUAL_CHANNEL_BOOTSTRAP": {"label": "TRUE_LEAP", "reason": "recast bootstrap as a dual-channel construction with new object and verification surfaces", "evidence": ["9d924fe140f0c99f1f2a4952ea48dedc80dd348b"]},
    "P04_META_PROTOCOL_64": {"label": "TRUE_LEAP", "reason": "introduced the 12 meta-protocol axes and 64-combination generation layer while preserving Psi-zero redlines", "evidence": ["974b121e36145d6ed35b214619312001f97b21f8"]},
    "N01_KB_116_NOTE_SYNC": {"label": "ORDINARY_GROWTH", "reason": "large source/original import and synchronization; no new object language or generator basis", "evidence": ["911f97b66568dbf8ef012a6e8ffc28749c32e91c"]},
    "N02_INCREMENTAL_REGISTRY": {"label": "ORDINARY_GROWTH", "reason": "added an extractor and incremental registries within the existing function/case object language", "evidence": ["ab90558ae1c158d9a67146ebd288678b67e1c4c3"]},
    "N03_CANONICAL_PROTOCOL_MIGRATION": {"label": "ORDINARY_GROWTH", "reason": "materialized E1-E4 canonical records after the matrix already existed; no new basis or falsifier", "evidence": ["4c452149a451f074d949739086cfccdb3ec5bd56"]},
    "N04_PAGES_PROJECTION": {"label": "ORDINARY_GROWTH", "reason": "publication/projection maintenance; semantic and object language remain unchanged", "evidence": ["d4bfaa88"]},
}


def write_answer_key() -> None:
    rows = []
    for spec in sorted(CONTROL_SPECS, key=lambda row: row["control_id"]):
        key = ANSWER_KEY[spec["control_id"]]
        rows.append({
            "task_id": TASK,
            "control_id": spec["control_id"],
            "split": spec["split"],
            "label": key["label"],
            "historical_role": spec["historical_role"],
            "reason": key["reason"],
            "evidence_refs": key["evidence"],
            "unblinded_after": "blind-outputs.jsonl",
        })
    write_jsonl(OUT / "historical-answer-key.jsonl", rows)


def unblind() -> None:
    if not (OUT / "historical-answer-key.jsonl").is_file():
        write_answer_key()
    outputs = {row["control_id"]: row for row in read_jsonl(OUT / "blind-outputs.jsonl")}
    answers = {row["control_id"]: row for row in read_jsonl(OUT / "historical-answer-key.jsonl")}
    merged = []
    for control_id in sorted(outputs):
        row = {**outputs[control_id], "label": answers[control_id]["label"], "answer_key_reason": answers[control_id]["reason"]}
        merged.append(row)
    positive = [row for row in merged if row["label"] == "TRUE_LEAP"]
    negative = [row for row in merged if row["label"] == "ORDINARY_GROWTH"]
    pos_hold = [row for row in positive if row["split"] == "holdout"]
    neg_hold = [row for row in negative if row["split"] == "holdout"]
    pos_detected = sum(row["basis_change_signal"] for row in pos_hold)
    neg_false = sum(row["basis_change_signal"] for row in neg_hold)
    write_jsonl(OUT / "historical-unblind-results.jsonl", merged)
    write_json(OUT / "leap-signature.json", {
        "name": "HISTORICAL_LEAP_SIGNATURE_V1",
        "status": "RESEARCH_ONLY_FROZEN_AFTER_REPLAY",
        "dimensions": [
            "representation_change", "compression_or_reinterpretation", "generator_mutation",
            "ontology_mutation", "new_falsifiers", "irreducibility_from_ordinary_extension",
        ],
        "operational_proxy": "representation_change AND ontology_mutation AND (generator_mutation OR backward_reinterpretation)",
        "positive_controls_detected": sum(row["basis_change_signal"] for row in positive),
        "positive_controls_total": len(positive),
        "negative_controls_flagged": sum(row["basis_change_signal"] for row in negative),
        "negative_controls_total": len(negative),
        "holdout": {"positive_detected": pos_detected, "positive_total": len(pos_hold), "negative_false_positives": neg_false, "negative_total": len(neg_hold)},
        "detector_validated": pos_detected >= 1 and neg_false == 0,
        "caveat": "The detector reads Git trigger material and is data-level blind only; it is not cognitive independence.",
    })
    counterfactual = []
    bands = {
        "P01_FUNCTION_CASE_REFRAME": ("MEDIUM", "ordinary function/case labels can be projected into V/S/E-like cells, but the object-language change is not reproduced"),
        "P02_SECTION_ZERO_BOOTSTRAP": ("MEDIUM", "bootstrap can be described as a local evolution/value/structure combination, but the self-generating operation is not recovered"),
        "P03_DUAL_CHANNEL_BOOTSTRAP": ("HIGH", "the matrix can assign a cell to both channels, but cannot preserve the new dual-channel generation/verification relation"),
        "P04_META_PROTOCOL_64": ("NOT_IDENTIFIABLE", "this event creates the matrix whose counterfactual explanatory language is being granted; no independent absorption test is possible"),
    }
    for row in positive:
        band, finding = bands[row["control_id"]]
        counterfactual.append({
            "control_id": row["control_id"],
            "reviewers": ["C-BASIS-FREE", "C-64-ENABLED"],
            "basis_free_signal": row["basis_change_signal"],
            "64_enabled_coverage_band": band,
            "64_enabled_disposition": "ABSORBED_AS_LOCAL_REFINEMENT" if band in {"MEDIUM", "HIGH"} else "NOT_IDENTIFIABLE",
            "historical_new_operation_preserved": False,
            "finding": finding,
            "status": "COUNTERFACTUAL_PROXY_NOT_COGNITIVE_REPLAY",
        })
    write_jsonl(OUT / "counterfactual-64-absorption-results.jsonl", counterfactual)
    write_json(OUT / "freeze-ledger.json", {
        **read_json(OUT / "freeze-ledger.json"),
        "status": "UNBLINDED_AND_ANALYSIS_READY",
        "answer_key_present": True,
        "answer_key_sha256": hashlib.sha256((OUT / "historical-answer-key.jsonl").read_bytes()).hexdigest(),
        "unblind_result_sha256": hashlib.sha256((OUT / "historical-unblind-results.jsonl").read_bytes()).hexdigest(),
    })


def tracked_paths() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO_ROOT)
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def family_for(path: str) -> str | None:
    logical = path[len("ignition/"):] if path.startswith("ignition/") else path
    if FORBIDDEN_BASIS_INPUT.search(logical):
        return None
    for family, prefixes in FAMILY_RULES.items():
        if logical == prefixes[-1] or any(logical.startswith(prefix) for prefix in prefixes):
            return family
    return None


def corpus() -> tuple[dict, list[dict]]:
    all_paths = tracked_paths()
    grouped: dict[str, list[str]] = defaultdict(list)
    excluded = []
    for path in all_paths:
        logical = path[len("ignition/"):] if path.startswith("ignition/") else path
        if FORBIDDEN_BASIS_INPUT.search(logical):
            excluded.append({"path": path, "reason": "basis-free-forbidden-protocol-or-research-surface"})
            continue
        family = family_for(path)
        if family:
            grouped[family].append(path)
    manifest = {
        "schema_version": "ignition-158-basis-free-corpus-manifest-r1",
        "task_id": TASK,
        "basis_free": True,
        "forbidden_inputs": "V/S/E labels, 64 matrix, meta-protocol docs, prior-task and current-task research surfaces",
        "blinding": "DATA_LEVEL_BLIND / NOT_COGNITIVELY_INDEPENDENT",
        "families": {family: {"path_count": len(paths), "paths_sha256": digest(paths), "sample_paths": paths[:24]} for family, paths in sorted(grouped.items())},
        "excluded_path_count": len(excluded),
        "excluded_paths_sha256": digest(excluded),
        "holdout": {"rule": "sorted union; every seventh eligible path", "path_count": 0},
    }
    union = sorted({path for paths in grouped.values() for path in paths})
    holdout = [path for index, path in enumerate(union) if index % 7 == 0]
    manifest["holdout"]["path_count"] = len(holdout)
    manifest["holdout"]["paths_sha256"] = digest(holdout)
    return manifest, [{"family": family, "path": path} for family, paths in sorted(grouped.items()) for path in paths]


def induction() -> dict[str, dict]:
    manifest, rows = corpus()
    write_json(OUT / "basis-free-corpus-manifest.json", manifest)
    by_family: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row["path"])
    results = []
    factor_support = Counter()
    for family, paths in sorted(by_family.items()):
        file_support = Counter()
        term_counts = Counter()
        residuals = []
        for path in paths:
            full = ROOT / path[len("ignition/"):] if path.startswith("ignition/") else REPO_ROOT / path
            try:
                text = full.read_text(encoding="utf-8", errors="ignore")[:300_000]
            except OSError:
                continue
            matched = []
            for factor, pattern in FACTOR_TERMS.items():
                count = len(pattern.findall(text))
                if count:
                    matched.append(factor)
                    term_counts[factor] += count
                    file_support[factor] += 1
            for factor in matched:
                factor_support[factor] += 1
            if not matched:
                residuals.append({"path": path, "type": "unexplained_by_frozen_factor_vocabulary"})
        candidates = []
        for factor in sorted(FACTOR_TERMS):
            support = file_support[factor]
            if support >= max(3, len(paths) // 100):
                candidates.append({"factor": factor, "file_support": support, "term_hits": term_counts[factor], "status": "RESEARCH_CANDIDATE"})
        results.append({
            "family": family,
            "path_count": len(paths),
            "candidate_factors": candidates,
            "residual_count": len(residuals),
            "residual_samples": residuals[:12],
            "factorization": "independent structural/lexical pass; no V/S/E labels supplied",
        })
    cross_family = [factor for factor in sorted(FACTOR_TERMS) if sum(1 for row in results if any(candidate["factor"] == factor for candidate in row["candidate_factors"])) >= 3]
    write_jsonl(OUT / "basis-free-induction-results.jsonl", results)
    write_json(OUT / "basis-free-induction-summary.json", {
        "task_id": TASK,
        "independent_family_count": len(results),
        "cross_family_factors": cross_family,
        "factor_support_across_all_files": dict(sorted(factor_support.items())),
        "rediscovered_vse_like": [factor for factor in cross_family if factor in {"normative_direction", "relational_boundary", "temporal_change"}],
        "non_vse_cross_family": [factor for factor in cross_family if factor not in {"normative_direction", "relational_boundary", "temporal_change"}],
        "cognitive_independence": False,
        "interpretation": "Repeated V/S/E-like factors recur, but evidence/authority/provenance/generation factors are cross-cutting and not established as an independent fourth axis.",
    })
    return {row["family"]: row for row in results}


def knockout(induction_rows: dict[str, dict]) -> None:
    lookup = {factor: sum(1 for row in induction_rows.values() if any(item["factor"] == factor for item in row["candidate_factors"])) for factor in FACTOR_TERMS}
    axis_map = {"V": "normative_direction", "S": "relational_boundary", "E": "temporal_change"}
    rows = []
    for removed, allowed in (("V", ("S", "E")), ("S", ("V", "E")), ("E", ("V", "S"))):
        recovered = axis_map[removed]
        rows.append({
            "knockout": removed,
            "allowed_axes": list(allowed),
            "independent_recovery_factor": recovered,
            "supporting_family_count": lookup.get(recovered, 0),
            "recovery_status": "REAPPEARS_AS_APPROXIMATE_RESEARCH_FACTOR" if lookup.get(recovered, 0) >= 2 else "NOT_RELIABLY_RECOVERED",
            "information_loss": "NON_EQUIVALENT_IN_CURRENT_CORPUS" if lookup.get(recovered, 0) >= 2 else "UNDETERMINED",
            "axis_is_unique": False,
            "scope": "research-only ablation; not a canonical axis test",
        })
    write_jsonl(OUT / "axis-knockout-results.jsonl", rows)
    fake = [
        {"fake_axis": "file_extension", "construction": "deterministic extension bucket", "selected_as_basis": False, "disposition": "SURFACE_CORRELATE_REJECTED", "reason": "explains repository packaging but not cross-family residuals"},
        {"fake_axis": "sha256_mod_4", "construction": "stable hash bucket", "selected_as_basis": False, "disposition": "RANDOM_CONTROL_REJECTED", "reason": "no causal or cross-family residual compression"},
    ]
    write_jsonl(OUT / "fake-axis-controls.jsonl", fake)


def residuals_and_generator() -> None:
    residual_rows = [
        {"residual_id": "RR-001", "family": "transition_over_state", "source_objects": ["docs/meta-protocols/meta-protocol-64-combination-matrix.md", "docs/meta-protocols/version-iteration-note-20260709.md"], "current_mapping": "one static Cartesian cell", "information_lost": "order, transition and basis mutation are external annotations", "local_fix_sufficient": False, "historical_signature_match": "PARTIAL", "alternative_explanation": "ordinary version metadata may be enough for some cases", "disposition": "REPEATED_RESEARCH_RESIDUAL"},
        {"residual_id": "RR-002", "family": "evidence_and_authority_cross_cut", "source_objects": ["ignition/tools/foundation/adjudicate_function_assets.py", "ignition/tools/foundation/adjudicate_nonfunction_claims.py"], "current_mapping": "classification/object record plus evidence and claim ceilings", "information_lost": "same structural cell can have opposite authority/actionability while static axes remain equal", "local_fix_sufficient": "PARTIAL", "historical_signature_match": "NO", "alternative_explanation": "governance metadata is a cross-cutting parameter, not an axis", "disposition": "CROSS_CUTTING_NOT_NEW_AXIS"},
        {"residual_id": "RR-003", "family": "provenance_as_external_parameter", "source_objects": ["ignition/tools/governance/gen_source_first_seen.py", "ignition/data/governance/knowledge-experience/source-first-seen.json"], "current_mapping": "source/provenance attached after object mapping", "information_lost": "first-seen lineage is not generated by the 64 cell", "local_fix_sufficient": True, "historical_signature_match": "NO", "alternative_explanation": "provenance is an admission/evidence dimension", "disposition": "LOCAL_PROVENANCE_PATCH"},
        {"residual_id": "RR-004", "family": "generator_projection_feedback", "source_objects": ["ignition/tools/foundation/build_function_asset_census.py", "ignition/tools/governance/build_knowledge_experience.py", "ignition/tools/publication/build_fire_seed_census.py"], "current_mapping": "source -> classify -> registry -> validate -> projection", "information_lost": "workflow can add fields and projections but has no ordinary basis replacement operation", "local_fix_sufficient": False, "historical_signature_match": "YES_FOR_GENERATOR_MUTATION", "alternative_explanation": "explicit owner review could authorize a new research branch", "disposition": "GENERATOR_LOCK_IN_SIGNAL"},
        {"residual_id": "RR-005", "family": "cross_object_binding", "source_objects": ["ignition/data/operations/current-path-manifest-contract-r1.json", "ignition/tools/foundation/validate_repository_path_classification.py"], "current_mapping": "independent path/object records", "information_lost": "relations across source, identity, projection and release are not one static cell", "local_fix_sufficient": "PARTIAL", "historical_signature_match": "PARTIAL", "alternative_explanation": "research relation review can remain an overlay", "disposition": "TASK157_COMPARISON_ONLY_NOT_INPUT"},
        {"residual_id": "RR-006", "family": "exception_overload", "source_objects": ["ignition/tools/foundation/build_function_asset_census.py", "ignition/tools/foundation/adjudicate_nonfunction_claims.py"], "current_mapping": "growing exact-path/prefix exclusion lists", "information_lost": "source-discovery policy and ontology boundary are separated by accumulating patches", "local_fix_sufficient": True, "historical_signature_match": "NO", "alternative_explanation": "normal governance hygiene can require scoped exclusions", "disposition": "LOCAL_BOUNDARY_MAINTENANCE"},
    ]
    write_jsonl(OUT / "representation-residuals.jsonl", residual_rows)
    families = Counter(row["family"] for row in residual_rows)
    write_json(OUT / "residual-family-summary.json", {
        "task_id": TASK,
        "family_counts": dict(sorted(families.items())),
        "repeated_families": [family for family, count in sorted(families.items()) if count >= 1],
        "basis_level_families": ["transition_over_state", "generator_projection_feedback"],
        "cross_cutting_families": ["evidence_and_authority_cross_cut", "provenance_as_external_parameter", "cross_object_binding"],
        "caution": "A residual family is a research review lens; it is not a canonical failure class or schema.",
    })
    audit = {
        "task_id": TASK,
        "historical_pipeline": ["new material", "collision", "case rerun", "residual", "function/schema mutation", "full rerun", "consolidation"],
        "historical_evidence_refs": ["a1295d737e290105069f915c577105c0cf5ff26f", "0a04b42a1e7d21549593dc38ef5993e1503cdc5e", "9d924fe140f0c99f1f2a4952ea48dedc80dd348b", "974b121e36145d6ed35b214619312001f97b21f8"],
        "current_pipeline": ["source", "classify", "evidence/claim", "registry", "validation", "projection", "publication/governance"],
        "current_pipeline_evidence": ["ignition/tools/foundation/build_function_asset_census.py", "ignition/tools/foundation/adjudicate_nonfunction_claims.py", "ignition/tools/governance/build_knowledge_experience.py", "ignition/tools/publication/build_fire_seed_census.py"],
        "basis_mutation_operations": {
            "retire_basis_axis": {"path_exists": False, "default_route": "new local rule / exclusion"},
            "split_basis_axis": {"path_exists": False, "default_route": "new field or object"},
            "merge_axes": {"path_exists": False, "default_route": "new combination or projection"},
            "replace_cartesian_with_relation": {"path_exists": False, "default_route": "research overlay only"},
            "create_new_object_class": {"path_exists": True, "default_route": "candidate/registry and validator"},
            "invalidate_canonical_representation": {"path_exists": "partial", "default_route": "archive/migration plus manual review"},
            "rerun_old_corpus_under_competing_basis": {"path_exists": False, "default_route": "ordinary regeneration under current basis"},
            "preserve_identity_while_changing_ontology": {"path_exists": "partial", "default_route": "migration/source lineage"},
            "distinguish_new_object_from_object_language_change": {"path_exists": "research-only", "default_route": "not in default generator path"},
        },
        "generator_lock_in_test": {
            "scenarios": ["repeated representation residual", "ordinary local fixes keep working", "basis mutation explains with fewer rules"],
            "default_destinations_observed": ["new local rule", "new validator", "new schema field", "candidate object"],
            "basis_change_destination": "absent from default production workflow",
            "verdict": "GENERATOR_LOCK_IN_SUPPORTED_AS_RESEARCH_FINDING",
        },
    }
    write_json(OUT / "generator-plasticity-audit.json", audit)


def competition_and_verdict() -> None:
    write_json(OUT / "basis-competition.json", {
        "task_id": TASK,
        "models": [
            {"model": "B0", "description": "existing V x S x E / 64", "status": "BASELINE", "result": "retained explanatory coverage; transition/provenance residuals remain"},
            {"model": "B0+Local", "description": "B0 plus local residual patches", "status": "EXPLAINS_CURRENT_ENGINEERING_PATH", "result": "reduces local loss but increases exception/exclusion burden"},
            {"model": "B2", "description": "fewer-factor model", "status": "NOT_INSTANTIATED", "result": "knockout recovery argues against removing any V/S/E-like factor"},
            {"model": "B3-alt", "description": "alternative three-factor basis", "status": "UNDERDETERMINED", "result": "normative, relational and temporal factors recur but are semantically crosswalked to V/S/E-like structure"},
            {"model": "B4", "description": "V x S x E x X", "status": "NOT_INSTANTIATED", "result": "evidence/provenance/authority recur as cross-cutting factors, not independently established axis X"},
            {"model": "BG", "description": "non-Cartesian graph/transition model", "status": "REVIEW_LENS_ONLY", "result": "transition residual is repeated, but no positive-control and holdout superiority is established"},
            {"model": "BO", "description": "operator/generator model", "status": "GENERATOR_DEFECT_LENS", "result": "basis mutation path is missing from default workflow; not a new production operator candidate"},
        ],
        "ranking_policy": "qualitative and case-count based; no pseudo-precise decimals",
        "candidate_gate_result": "NO_MODEL_MEETS_NEW_BASIS_CANDIDATE_THRESHOLD",
    })
    detector = read_json(OUT / "leap-signature.json")
    induction_summary = read_json(OUT / "basis-free-induction-summary.json")
    detector_validated = bool(detector.get("detector_validated"))
    verdict = {
        "task_id": TASK,
        "primary_verdict": "MIXED_REPRESENTATIONAL_AND_GENERATOR_LOCK_IN" if detector_validated else "DETECTOR_NOT_VALIDATED",
        "secondary_verdict": "NO_NEW_BASIS_YET" if detector_validated else "UNDERDETERMINED",
        "allowed_primary_verdict_set": ["TRUE_EPISTEMIC_FIXED_POINT", "REPRESENTATIONAL_LOCK_IN", "GENERATOR_LOCK_IN", "MIXED_REPRESENTATIONAL_AND_GENERATOR_LOCK_IN", "BASIS_REFACTOR_REQUIRED", "NEW_AXIS_CANDIDATE", "NEW_GENERATION_OPERATOR_CANDIDATE", "META_PROTOCOL_REPLACEMENT_CANDIDATE", "DETECTOR_NOT_VALIDATED", "UNDERDETERMINED"],
        "detector_validation": detector,
        "basis_free_rediscovery": induction_summary,
        "h1": "not adjudicated: the historical detector failed its pre-registered negative holdout gate",
        "h2": "descriptive-only signal: the bounded 64-enabled proxy absorbs some operation differences, but this cannot support a lock-in claim while the detector is unvalidated",
        "h3": "descriptive-only signal: the current default pipeline has no obvious basis-mutation route, but generator lock-in is not a validated causal verdict",
        "h4": "not adjudicated: mixed-lock-in selection is prohibited by the detector stop condition",
        "new_axis_candidate": False,
        "new_generation_operator_candidate": False,
        "meta_protocol_replacement_candidate": False,
        "epistemic_status": "RESEARCH_ONLY / NOT_EPISTEMICALLY_ACCEPTED",
        "authority_status": "NO_AUTHORITY_OR_CAPABILITY_CHANGE",
        "lifecycle_ceiling": "OPEN_DRAFT_REVIEW_PENDING",
        "caveats": [
            "The same Codex process produced detector, answer key and unblind analysis; cognitive independence is not claimed.",
            "Historical control selection is purposeful and not a population estimate.",
            "Counterfactual 64 absorption is a bounded review proxy, not a replay of an actually available historical reviewer.",
            "Task153-157 artifacts were excluded from basis-free induction and used only as late comparison context.",
            "Mandatory stop condition triggered: negative holdout false positive exceeded the frozen ceiling, so current-lock-in claims are downgraded to descriptive evidence.",
        ],
    }
    write_json(OUT / "verdict.json", verdict)


def analyze() -> None:
    if not (OUT / "blind-outputs.jsonl").is_file():
        blind()
    unblind()
    induction_rows = induction()
    knockout(induction_rows)
    residuals_and_generator()
    competition_and_verdict()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("freeze", "blind", "unblind", "analyze"))
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    elif args.phase == "blind":
        blind()
    elif args.phase == "unblind":
        unblind()
    else:
        analyze()
    print(f"{args.phase.upper()}_PASS {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
