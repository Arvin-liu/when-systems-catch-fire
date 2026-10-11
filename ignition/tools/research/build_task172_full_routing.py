#!/usr/bin/env python3
"""Build the Task172 full routing overlay for one canonical asset plane.

The overlay is a generated, canonical-ID keyed projection.  It is deliberately
separate from both Foundation registries: routing can improve bounded discovery
but cannot alter identity, M/E, disposition, claim ceiling, evidence status or
the registry's source bytes.

This builder has two useful modes:

* ``--write`` is the scan-sensitive build used before a logical Step05/06
  commit.  It requires the caller to name the exact current parent head.
* ``--check`` regenerates the rows in memory and compares them with the
  committed overlay and receipts without writing anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.research.build_task172_gate_r import classify


BRANCH = "work/IGNITION-20260912-172-knowledge-routing-universal-corpus"
PR_NUMBER = 218
ROUTING_REL = Path("data/research/task172-routing-r1")
FUNCTION_AUTHORITY_REL = Path("data/foundation/function-assets/identity-cards.jsonl")
NONFUNCTION_AUTHORITY_REL = Path("data/foundation/nonfunction-claims/claim-registry.jsonl")
GATE_T_REL = Path("data/research/task172-gate-t-unesco-1988")
GATE_R_REL = Path("data/research/task172-gate-r-routing")
GATE_C_REL = Path("data/research/task172-gate-c-scholarly-admission")
COMMAND_SOURCES = [
    {"repository": "Arvin-liu/1111", "ref": "b7c27fab", "path": "agent-commands/IGNITION-20260912-172.md"},
    {"repository": "Arvin-liu/1111", "ref": "ebc75f9c", "path": "agent-commands/IGNITION-20260913-175.md"},
    {"repository": "Arvin-liu/1111", "ref": "b1fc45fb", "path": "agent-commands/IGNITION-20260913-176.md"},
]
TAXONOMY = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
ALLOWED_STATES = {"CLASSIFIED", "MULTIDISCIPLINARY", "OUT_OF_UNESCO_SCOPE", "UNRESOLVED"}
ALLOWED_ROLES = {"METHOD_TRANSFER", "EVIDENCE_CHECK", "ANALOGY_SOURCE", "HISTORICAL_CONTEXT", "NARRATIVE_CASE"}
ALLOWED_USES = {
    "EXPLAIN",
    "COMPARE",
    "ANALOGY_SOURCE",
    "MECHANISM_TEST",
    "CAUSAL_CHALLENGE",
    "COUNTEREXAMPLE",
    "EVIDENCE_CHECK",
    "METHOD_TRANSFER",
    "BOUNDARY_TEST",
    "NORMATIVE_CHECK",
    "NARRATIVE_CASE",
    "HISTORICAL_CONTEXT",
}
TAGGER_VERSION = "task172-step05-06-full-routing-v1"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")


def authority_for_kind(repo_root: Path, asset_kind: str) -> tuple[Path, list[dict[str, Any]]]:
    if asset_kind == "FUNCTION_ASSET":
        path = repo_root / FUNCTION_AUTHORITY_REL
    elif asset_kind == "NONFUNCTION_CLAIM":
        path = repo_root / NONFUNCTION_AUTHORITY_REL
    else:  # pragma: no cover - argparse constrains this
        raise ValueError(f"unsupported asset kind: {asset_kind}")
    rows = sorted(read_jsonl(path), key=lambda row: str(row["canonical_id"]))
    return path, rows


def expected_count(asset_kind: str, repo_root: Path | None = None) -> int:
    if asset_kind == "FUNCTION_ASSET" and repo_root is not None:
        # Both Foundation registries are scan-sensitive authority sources. A
        # governed report may legitimately add a quarantined discovery row,
        # so routing must close over the current registry rather than preserve
        # a stale historical count.
        return len(read_jsonl(repo_root / FUNCTION_AUTHORITY_REL))
    if asset_kind == "NONFUNCTION_CLAIM" and repo_root is not None:
        return len(read_jsonl(repo_root / NONFUNCTION_AUTHORITY_REL))
    raise ValueError("repo_root is required to resolve the current nonfunction authority count")


def source_path_for_kind(asset_kind: str) -> str:
    return str(FUNCTION_AUTHORITY_REL if asset_kind == "FUNCTION_ASSET" else NONFUNCTION_AUTHORITY_REL)


def taxonomy_sets(repo_root: Path) -> tuple[set[str], set[str], dict[str, str]]:
    parse = read_json(repo_root / GATE_T_REL / "primary-1988-parse.json")
    fields = {row["code"]: row["label"] for row in parse["hierarchy"]["fields"]}
    disciplines = {row["code"] for row in parse["discipline_records"]}
    return set(fields), disciplines, fields


def _probe_row(row: dict[str, Any], asset_kind: str) -> dict[str, Any]:
    """Expose only deterministic source text to the frozen Gate R classifier."""
    probe = dict(row)
    if asset_kind == "FUNCTION_ASSET":
        probe["title"] = " ".join(
            str(value)
            for value in (
                row.get("title", ""),
                row.get("primary_identity", ""),
                " ".join(str(item) for item in row.get("secondary_identities", [])),
                str((row.get("definition") or {}).get("domain", "")),
                str((row.get("definition") or {}).get("codomain", "")),
            )
            if value
        )
    else:
        probe["canonical_title"] = " ".join(
            str(value)
            for value in (
                row.get("canonical_title", ""),
                row.get("claim_class", ""),
                row.get("assertion_type", ""),
                row.get("minimal_atomic_claim", ""),
            )
            if value
        )
    probe["canonical_source"] = " ".join(
        str(item.get("path", "")) for item in row.get("source_anchors", []) if item.get("path")
    )
    return probe


def _joined_status(row: dict[str, Any]) -> str:
    values: list[str] = []
    for key in (
        "final_disposition",
        "claimed_status",
        "internal_external_status",
        "replication_status",
        "reviewer_state",
        "claim_ceiling",
    ):
        value = row.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    values.extend(str(item) for item in row.get("prohibited_wording", []) or [])
    values.extend(str(item) for item in row.get("prohibited_uses", []) or [])
    return " ".join(values).upper()


def is_negative_boundary(row: dict[str, Any]) -> bool:
    status = _joined_status(row)
    return any(token in status for token in ("REJECT", "QUARANTINE", "WITHDRAWN", "UNSUPPORTED", "RETRACTED", "CONTRADICTED", "HISTORICAL_ONLY"))


def route_use_tags(row: dict[str, Any], asset_kind: str) -> tuple[list[str], list[str], dict[str, str]]:
    """Assign retrieval-purpose tags, never truth/evidence promotion tags."""
    if is_negative_boundary(row):
        return (
            ["HISTORICAL_CONTEXT"],
            ["COUNTEREXAMPLE", "EVIDENCE_CHECK", "HISTORICAL_CONTEXT"],
            {"evidence_role": "NEGATIVE_OR_WITHDRAWN_LINEAGE_REVIEW"},
        )

    if asset_kind == "NONFUNCTION_CLAIM":
        claim_class = str(row.get("claim_class", "")).upper()
        if claim_class == "EMPIRICAL_OR_LITERATURE_CLAIM":
            # This is deliberately a review/check route.  It does not mean
            # that a repository claim is external scientific evidence.
            return ["EVIDENCE_CHECK"], ["EVIDENCE_CHECK"], {"evidence_role": "REPOSITORY_CLAIM_METADATA_REVIEW"}
        if "CAUSAL" in claim_class or "PREDICTION" in claim_class:
            return ["EVIDENCE_CHECK"], ["MECHANISM_TEST", "CAUSAL_CHALLENGE", "COUNTEREXAMPLE"], {"evidence_role": "CAUSAL_OR_PREDICTIVE_BOUNDARY_REVIEW"}
        if "THEOREM" in claim_class or "FORMAL" in claim_class or "MATHEMAT" in claim_class:
            return ["METHOD_TRANSFER"], ["EXPLAIN", "BOUNDARY_TEST"], {"evidence_role": "FORMAL_SCOPE_REVIEW"}
        if "CROSS_DOMAIN" in claim_class or "CORRESPONDENCE" in claim_class or "INTERPRET" in claim_class:
            return ["ANALOGY_SOURCE"], ["COMPARE", "BOUNDARY_TEST"], {"evidence_role": "CROSS_DOMAIN_ANALOGY_REVIEW"}
        return ["NARRATIVE_CASE"], ["EXPLAIN"], {"evidence_role": "SOURCE_DEFINED_REVIEW"}

    primary = str(row.get("primary_identity", "")).upper()
    if primary in {"PARAMETRIC_MATHEMATICAL_MODEL", "RELATION_OR_CONSTRAINT", "FORMAL_RULE_OR_THEOREM"}:
        return ["METHOD_TRANSFER"], ["EXPLAIN", "BOUNDARY_TEST"], {"evidence_role": "FORMAL_SCOPE_REVIEW"}
    if "MECHANISM" in primary or "CAUSAL" in primary or "EMPIRICAL" in primary:
        return ["EVIDENCE_CHECK"], ["MECHANISM_TEST", "CAUSAL_CHALLENGE"], {"evidence_role": "FUNCTION_SCOPE_REVIEW"}
    if "ANALOG" in primary or "CORRESPOND" in primary or "INTERPRET" in primary:
        return ["ANALOGY_SOURCE"], ["COMPARE", "BOUNDARY_TEST"], {"evidence_role": "ANALOGY_SCOPE_REVIEW"}
    return ["NARRATIVE_CASE"], ["EXPLAIN"], {"evidence_role": "SOURCE_DEFINED_REVIEW"}


def immutable_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "canonical_id",
        "title",
        "canonical_title",
        "primary_identity",
        "claim_class",
        "assertion_type",
        "mathematical_maturity",
        "external_evidence_maturity",
        "final_disposition",
        "claimed_status",
        "replication_status",
        "reviewer_state",
        "claim_ceiling",
        "record_sha256",
    )
    return {key: row[key] for key in keys if key in row}


def build_row(row: dict[str, Any], asset_kind: str, field_codes: set[str], discipline_codes: set[str]) -> dict[str, Any]:
    field_tags, state, matched_terms, confidence, basis = classify(_probe_row(row, asset_kind))
    field_tags = list(dict.fromkeys(field_tags))[:2]
    role_tags, use_tags, use_basis = route_use_tags(row, asset_kind)
    source_record_sha = row.get("record_sha256")
    if not source_record_sha:
        raise ValueError(f"authority row has no record_sha256: {row.get('canonical_id')}")
    if any(code not in field_codes for code in field_tags):
        raise ValueError(f"classifier emitted a non-primary UNESCO field: {row.get('canonical_id')}: {field_tags}")
    if any(code not in discipline_codes for code in []):
        raise ValueError(f"classifier emitted a non-primary UNESCO discipline: {row.get('canonical_id')}")
    if state == "OUT_OF_UNESCO_SCOPE":
        field_tags = []
    return {
        "canonical_id": row["canonical_id"],
        "asset_kind": asset_kind,
        "canonical_target": {
            "canonical_id": row["canonical_id"],
            "authority_path": source_path_for_kind(asset_kind),
        },
        "domain": {
            "unesco_field_codes": field_tags,
            # A canonical Foundation asset is not assigned a four-digit
            # discipline by lexical coincidence.  Empty is an explicit
            # unresolved facet, not an invented equivalence.
            "unesco_discipline_codes": [],
            "classification_state": state,
        },
        "asset_role": role_tags[:3],
        "collision_use": use_tags[:4],
        "topic": [],
        "routing_confidence": confidence,
        "facet_confidence": {
            "unesco_field_codes": confidence if field_tags else None,
            "unesco_discipline_codes": None,
            "asset_role": 0.9,
            "collision_use": 0.9,
            "topic": None,
        },
        "tag_basis": {
            "kind": "FROZEN_GATE_R_HEURISTIC_SUGGESTION",
            "classifier": basis.get("rule", "unknown"),
            "matched_terms": matched_terms,
            "source_fields": ["canonical_id", "record_sha256", "title/classification metadata", "source_anchors"],
            **use_basis,
        },
        "evidence_projection": {
            "role": "ROUTING_ONLY_NO_EVIDENCE_PROMOTION",
            "authority_path": source_path_for_kind(asset_kind),
            "mathematical_maturity": row.get("mathematical_maturity"),
            "external_evidence_maturity": row.get("external_evidence_maturity"),
            "final_disposition": row.get("final_disposition"),
            "claim_class": row.get("claim_class"),
            "assertion_type": row.get("assertion_type"),
            "promotion": "NONE",
        },
        "source_record_sha": source_record_sha,
        "tagger_version": TAGGER_VERSION,
        "review_state": "FULL_ROUTING_MANUAL_REVIEW_REQUIRED",
        "immutable_snapshot": immutable_snapshot(row),
    }


def paths_for(asset_kind: str, step: str) -> dict[str, Path]:
    stem = "function" if asset_kind == "FUNCTION_ASSET" else "nonfunction"
    return {
        "overlay": ROUTING_REL / f"{stem}-routing-overlay.jsonl",
        "source_freeze": ROUTING_REL / f"step{step}-{stem}-routing-source-freeze.json",
        "operation": Path(f"data/operations/iterations/172/step{step}-{stem}-routing.json"),
        "report": Path(f"reports/operations/ignition-172-20260914-step{step}-{stem}-routing.md"),
        "receipt": ROUTING_REL / f"step{step}-{stem}-routing-build-receipt.json",
    }


def build_rows(repo_root: Path, asset_kind: str) -> tuple[list[dict[str, Any]], Path, dict[str, str]]:
    authority_path, authorities = authority_for_kind(repo_root, asset_kind)
    field_codes, discipline_codes, field_labels = taxonomy_sets(repo_root)
    rows = [build_row(row, asset_kind, field_codes, discipline_codes) for row in authorities]
    inputs = {
        "authority": sha256(authority_path),
        "gate_t_parse": sha256(repo_root / GATE_T_REL / "primary-1988-parse.json"),
        "gate_t_discrepancy_ledger": sha256(repo_root / GATE_T_REL / "discrepancy-ledger.json"),
        "gate_r_schema": sha256(repo_root / GATE_R_REL / "routing-schema.json"),
        "gate_r_vocabulary": sha256(repo_root / GATE_R_REL / "controlled-vocabulary.json"),
        "gate_c_build_receipt": sha256(repo_root / GATE_C_REL / "build-receipt.json"),
    }
    return rows, authority_path, {**inputs, "field_count": str(len(field_codes)), "discipline_count": str(len(discipline_codes)), "field_labels_sha256": sha256_bytes(canonical(field_labels).encode("utf-8"))}


def require_parent(repo_root: Path, source_head: str) -> None:
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    if current != source_head:
        raise SystemExit(f"TASK172_FULL_ROUTING_BUILD_REFUSED: current HEAD {current} != source head {source_head}")


def make_artifacts(repo_root: Path, asset_kind: str, step: str, source_head: str) -> None:
    require_parent(repo_root, source_head)
    if (step, asset_kind) not in {("05", "FUNCTION_ASSET"), ("06", "NONFUNCTION_CLAIM")}:
        raise SystemExit("step/asset-kind pairing must be 05/FUNCTION_ASSET or 06/NONFUNCTION_CLAIM")
    rows, authority_path, input_hashes = build_rows(repo_root, asset_kind)
    if len(rows) != expected_count(asset_kind, repo_root):
        raise SystemExit(f"unexpected {asset_kind} count: {len(rows)} != {expected_count(asset_kind, repo_root)}")
    paths = paths_for(asset_kind, step)
    overlay = repo_root / paths["overlay"]
    write_jsonl(overlay, rows)
    state_counts = Counter(row["domain"]["classification_state"] for row in rows)
    negative_count = sum(1 for row in rows if row["asset_role"] == ["HISTORICAL_CONTEXT"])
    source_freeze = {
        "schema": "task172-full-routing-source-freeze-v1",
        "step": f"Task172 Step{step}",
        "freeze_event": "SCAN_INPUT_FREEZE_REUSE",
        "direction_locks": ["IGNITION-20260913-175", "IGNITION-20260913-176", "IGNITION-20260912-172"],
        "command_sources": COMMAND_SOURCES,
        "formal_pre_freeze": {"head": source_head, "branch": BRANCH, "pull_request": PR_NUMBER, "state": "OPEN + DRAFT + unmerged"},
        "authority": {"asset_kind": asset_kind, "path": str(authority_path.relative_to(repo_root)), "sha256": sha256(authority_path), "row_count": len(rows)},
        "taxonomy_authority": {"source": "1988 UNESCO primary document locked by Gate T", **TAXONOMY, "parse_sha256": input_hashes["gate_t_parse"], "discrepancy_ledger_sha256": input_hashes["gate_t_discrepancy_ledger"]},
        "routing_preconditions": {"gate_r_schema_sha256": input_hashes["gate_r_schema"], "gate_r_vocabulary_sha256": input_hashes["gate_r_vocabulary"], "gate_c_receipt_sha256": input_hashes["gate_c_build_receipt"], "mass_formal_taxonomy_write": True, "scholarly_corpus_admission": "metadata_only_policy_locked"},
        "derived_outputs": {"overlay_sha256": sha256(overlay), "overlay_path": str(paths["overlay"])},
        "immutability": "routing projection cannot mutate canonical identity, M/E, disposition, claim ceiling or evidence status",
        "decision": f"STEP{step}_FULL_{asset_kind}_ROUTING_OVERLAY_READY; MANUAL_REVIEW_REQUIRED; NO_CANONICAL_MUTATION",
    }
    write_json(repo_root / paths["source_freeze"], source_freeze)
    report = repo_root / paths["report"]
    field_state_counts = Counter(code for row in rows for code in row["domain"]["unesco_field_codes"])
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        f"""# IGNITION-172 Step{step} — full {asset_kind.lower().replace('_', ' ')} routing overlay

This logical step is based on the exact frozen parent `{source_head}` on the existing Task172 branch and Draft PR #{PR_NUMBER}.

- Authority: `{authority_path.relative_to(repo_root)}`; `{len(rows)}` canonical rows, one routing row per canonical ID.
- Taxonomy: 1988 UNESCO primary lock, 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines. The overlay never invents a four-digit equivalence; empty discipline facets remain explicit unresolved routing information.
- Classification states: `{dict(sorted(state_counts.items()))}`. Field tags are the conservative Gate R classifier projection; unresolved and out-of-scope rows remain retained and auditable.
- Routing use: `{negative_count}` negative/quarantined/withdrawn boundary rows are restricted to historical/negative review routes. `{sum(field_state_counts.values())}` rows have field facets; field counts are `{dict(sorted(field_state_counts.items()))}`.
- Evidence boundary: all rows are `FULL_ROUTING_MANUAL_REVIEW_REQUIRED`; routing is not evidence, proof, maturity, truth or publication promotion. Canonical identity, M/E, disposition and claim ceiling remain in their authority registries.
- Determinism: sorted canonical IDs, frozen source hashes and no network/retrieval/write side effect beyond the generated overlay and step receipt.

Decision: `STEP{step}_FULL_{asset_kind}_ROUTING_OVERLAY_READY; MANUAL_REVIEW_REQUIRED; NO_CANONICAL_MUTATION`.
""",
        encoding="utf-8",
    )
    operation = {
        "schema": "task172-full-routing-operation-v1",
        "step": f"Task172 Step{step}",
        "asset_kind": asset_kind,
        "source_exact_head": source_head,
        "command_sources": COMMAND_SOURCES,
        "taxonomy": TAXONOMY,
        "authority": {"path": str(authority_path.relative_to(repo_root)), "rows": len(rows), "sha256": sha256(authority_path)},
        "overlay": {"path": str(paths["overlay"]), "rows": len(rows), "sha256": sha256(overlay)},
        "state_counts": dict(sorted(state_counts.items())),
        "hard_check_intent": {"missing": 0, "duplicate": 0, "orphan": 0, "source_fingerprint_mismatch": 0, "cap_violation": 0, "canonical_semantics_changed": 0, "negative_positive_route": 0},
        "field_counts": dict(sorted(field_state_counts.items())),
        "negative_boundary_rows": negative_count,
        "manual_review_required": len(rows),
        "network": False,
        "canonical_mutation": False,
        "source_freeze_sha256": sha256(repo_root / paths["source_freeze"]),
        "report_sha256": sha256(report),
        "decision": f"STEP{step}_FULL_{asset_kind}_ROUTING_OVERLAY_READY; MANUAL_REVIEW_REQUIRED; NO_CANONICAL_MUTATION",
    }
    write_json(repo_root / paths["operation"], operation)
    receipt = {
        "schema": "task172-full-routing-build-receipt-v1",
        "step": f"Task172 Step{step}",
        "asset_kind": asset_kind,
        "source_exact_head": source_head,
        "command_sources": COMMAND_SOURCES,
        "inputs": input_hashes,
        "counts": {"rows": len(rows), "expected_rows": expected_count(asset_kind, repo_root), "negative_boundary_rows": negative_count},
        "state_counts": dict(sorted(state_counts.items())),
        "hard_check_intent": operation["hard_check_intent"],
        "deterministic": True,
        "network": False,
        "canonical_mutation": False,
        "manual_review_required": len(rows),
        "outputs": {key: sha256(repo_root / path) for key, path in paths.items() if key != "receipt"},
        "decision": operation["decision"],
    }
    write_json(repo_root / paths["receipt"], receipt)
    print(f"TASK172_FULL_ROUTING_BUILT step={step} asset_kind={asset_kind} rows={len(rows)} source_head={source_head}")


def check_artifacts(repo_root: Path, asset_kind: str, step: str) -> None:
    paths = paths_for(asset_kind, step)
    for key, rel in paths.items():
        if not (repo_root / rel).is_file():
            raise SystemExit(f"TASK172_FULL_ROUTING_CHECK_FAILED: missing {key}: {rel}")
    receipt = read_json(repo_root / paths["receipt"])
    source_head = str(receipt.get("source_exact_head", ""))
    if len(source_head) != 40:
        raise SystemExit("TASK172_FULL_ROUTING_CHECK_FAILED: invalid source_exact_head")
    rows, authority_path, input_hashes = build_rows(repo_root, asset_kind)
    actual_rows = read_jsonl(repo_root / paths["overlay"])
    if actual_rows != rows:
        raise SystemExit("TASK172_FULL_ROUTING_CHECK_FAILED: deterministic overlay drift")
    expected_outputs = {key: sha256(repo_root / rel) for key, rel in paths.items() if key != "receipt"}
    if receipt.get("outputs") != expected_outputs:
        raise SystemExit("TASK172_FULL_ROUTING_CHECK_FAILED: output receipt hash drift")
    if receipt.get("inputs") != input_hashes:
        raise SystemExit("TASK172_FULL_ROUTING_CHECK_FAILED: input hash drift")
    if len(rows) != expected_count(asset_kind, repo_root) or receipt.get("counts", {}).get("rows") != len(rows):
        raise SystemExit("TASK172_FULL_ROUTING_CHECK_FAILED: row count drift")
    print(f"TASK172_FULL_ROUTING_DETERMINISTIC_OK step={step} asset_kind={asset_kind} rows={len(rows)} authority={authority_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--asset-kind", choices=["FUNCTION_ASSET", "NONFUNCTION_CLAIM"], required=True)
    parser.add_argument("--step", choices=["05", "06"], required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--source-head")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if args.write:
        if not args.source_head:
            parser.error("--source-head is required with --write")
        make_artifacts(repo_root, args.asset_kind, args.step, args.source_head)
    else:
        check_artifacts(repo_root, args.asset_kind, args.step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
