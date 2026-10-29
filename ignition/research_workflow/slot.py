#!/usr/bin/env python3
"""Run one fixed Source/Evidence Binding adapter before a research run starts.

This is a deliberately small adapter slot, not a registry or execution engine.
Both adapters feed the same existing claim-anchor consumer in ``cli.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Support both ``python -m ignition.research_workflow.slot`` and unittest discovery.
    from . import cli
except ImportError:  # pragma: no cover - exercised by the repository's discovery command.
    import cli  # type: ignore[no-redef]


LEGACY_COMMIT = "f17477dd9761c898563dbf5670c63914a5ecedfa"
CANDIDATE_COMMIT = "e37b8f2b222c9718fdd5383c3a7fb9c782e4f5db"
ADAPTERS = {
    "legacy-openalex-v1": {
        "source_commit": LEGACY_COMMIT,
        "capabilities": ["normalized_openalex_records", "abstract_text"],
    },
    "e37-source-snapshot-v1": {
        "source_commit": CANDIDATE_COMMIT,
        "capabilities": ["offline_source_snapshots", "capture_bytes", "captured_text_anchor"],
    },
}
SLOT_CAPABILITIES = [
    "common_abstract_anchor_consumer",
    "expected_capture_sha256_lock",
    "canonical_source_set_sha256_lock",
    "run_artifact_receipt",
]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_abstract(text: str) -> str:
    """Remove web-reader line labels while keeping the frozen abstract text."""
    return re.sub(r"(?m)^L[0-9]+:\s*", "", text)


def _canonical_source_set_digest(sources: list[dict[str, Any]]) -> str:
    """Bind the shared, normalized evidence text and its source identity."""
    canonical = []
    for source in sorted(sources, key=lambda item: item["source_id"]):
        abstract = source.get("abstract")
        if not isinstance(abstract, str) or not abstract.strip():
            raise ValueError(f"source {source.get('source_id')} requires non-empty abstract text")
        canonical.append({
            "source_id": source["source_id"],
            "title": source["title"],
            "source_url": source["source_url"],
            "abstract_sha256": _sha256(abstract.encode("utf-8")),
        })
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(payload)


def _read_jsonl(path: str | Path, label: str) -> tuple[list[dict[str, Any]], bytes]:
    raw = Path(path).read_bytes()
    rows = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} JSON is invalid on line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{label} line {line_number} must be a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{label} must contain at least one record")
    return rows, raw


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()


def _write_json(path: Path, value: Any) -> None:
    _write_bytes(path, (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    data = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for row in rows
    )
    _write_bytes(path, data)


def _read_digest_lock(path: str | Path | None, source_ids: list[str]) -> tuple[dict[str, str], bytes]:
    if path is None:
        raise ValueError("candidate adapter requires --expected-digests; missing digest lock is not accepted")
    try:
        lock_bytes = Path(path).read_bytes()
        value = json.loads(lock_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("expected digest lock must be a readable JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError("expected digest lock must be a JSON object")
    missing = sorted(set(source_ids) - set(value))
    extra = sorted(set(value) - set(source_ids))
    if missing:
        raise ValueError("expected digest lock is missing source IDs: " + ", ".join(missing))
    if extra:
        raise ValueError("expected digest lock contains unknown source IDs: " + ", ".join(extra))
    for source_id, digest in value.items():
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError(f"expected digest for {source_id} must be a lowercase SHA-256")
    return value, lock_bytes


def _legacy_sources(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, str], bytes]:
    records, input_bytes = _read_jsonl(path, "legacy normalized-record input")
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(records, 1):
        source_id = row.get("source_id")
        if source_id != f"S{index}" or source_id in seen:
            raise ValueError("legacy records must use unique, ordered source IDs S1..Sn")
        seen.add(source_id)
        for field in ("title", "source_url", "abstract"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"legacy record {source_id} requires non-empty {field}")
        abstract = row["abstract"]
        sources.append({
            "source_id": source_id,
            "provider": "LEGACY_OPENALEX_NORMALIZED_FIXTURE",
            "openalex_id": row.get("openalex_id"),
            "doi": row.get("doi"),
            "title": row["title"],
            "year": row.get("year"),
            "source_url": row["source_url"],
            "abstract": abstract,
            "source_version": row.get("source_version"),
            "capture_status": "UNAVAILABLE",
            "capture_sha256": None,
            "capture_bytes": None,
            "origin_authenticity": "UNVERIFIED",
            "raw_evidence": [],
        })
    return sources, {}, input_bytes


def _snapshot_sources(
    manifest_path: str | Path,
    digest_lock_path: str | Path | None,
    query_count: int,
) -> tuple[list[dict[str, Any]], dict[str, str], list[tuple[str, bytes]], bytes, bytes]:
    snapshots, manifest_bytes = cli._read_source_snapshots(manifest_path, query_count)
    source_ids = [f"S{index}" for index in range(1, len(snapshots) + 1)]
    expected, digest_lock_bytes = _read_digest_lock(digest_lock_path, source_ids)
    sources: list[dict[str, Any]] = []
    captured_text_by_source: dict[str, str] = {}
    captures: list[tuple[str, bytes]] = []
    for source_id, snapshot in zip(source_ids, snapshots):
        raw = snapshot["raw_bytes"]
        observed_sha = _sha256(raw)
        if observed_sha != expected[source_id]:
            raise ValueError(f"capture digest mismatch for {source_id}: expected {expected[source_id]}, observed {observed_sha}")
        suffix = "json" if snapshot["capture_kind"] == "official_api_json" else "txt"
        raw_path = f"raw/source-{source_id}.{suffix}"
        captures.append((raw_path, raw))
        captured_text_by_source[source_id] = snapshot["captured_text"]
        sources.append({
            "source_id": source_id,
            "provider": "E37_SOURCE_SNAPSHOT",
            "title": snapshot["title"],
            "source_url": snapshot["source_url"],
            "abstract": _normalize_abstract(snapshot["captured_text"]),
            "locator": snapshot["locator"],
            "source_version": snapshot["captured_at_utc"],
            "capture_kind": snapshot["capture_kind"],
            "capture_status": "ATTACHED_BYTES_HASH_MATCHED",
            "capture_sha256": observed_sha,
            "capture_bytes": len(raw),
            "origin_authenticity": "UNVERIFIED",
            "raw_evidence": [{
                "path": raw_path,
                "capture_sha256": observed_sha,
                "capture_kind": snapshot["capture_kind"],
                "manifest_capture_path": snapshot["capture_path"],
            }],
        })
    return sources, captured_text_by_source, captures, manifest_bytes, digest_lock_bytes


def _status(acquisition_status: str, claim_review_status: str, draft_error: str | None) -> str:
    return cli._overall_run_status(acquisition_status, claim_review_status, draft_error)


def _artifact_index(out: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(item for item in out.rglob("*") if item.is_file() and item.name != "receipt.json"):
        data = path.read_bytes()
        rows.append({"path": path.relative_to(out).as_posix(), "sha256": _sha256(data), "bytes": len(data)})
    return rows


def run_binding(
    *,
    adapter_id: str,
    question: str,
    output_dir: str | Path,
    draft_path: str | Path,
    claim_review_path: str | Path,
    task_id: str,
    episode_id: str,
    source_set_id: str,
    namespace: str,
    authorization_scope: str,
    implementation_commit: str,
    expected_source_set_digest: str,
    legacy_records_path: str | Path | None = None,
    source_snapshots_path: str | Path | None = None,
    expected_digests_path: str | Path | None = None,
    query_count: int = 12,
) -> dict[str, Any]:
    """Select exactly one fixed adapter, then map/check without same-run fallback."""
    selected_at = _utc_now()
    if adapter_id not in ADAPTERS:
        raise ValueError(f"unsupported adapter_id: {adapter_id}")
    if not all(isinstance(value, str) and value.strip() for value in (
        task_id, episode_id, source_set_id, namespace, authorization_scope, implementation_commit, question,
    )):
        raise ValueError("run context fields must be non-empty strings")
    if not isinstance(expected_source_set_digest, str) or not SHA256_RE.fullmatch(expected_source_set_digest):
        raise ValueError("expected source-set digest must be a lowercase SHA-256")
    if adapter_id == "legacy-openalex-v1":
        if legacy_records_path is None or source_snapshots_path is not None or expected_digests_path is not None:
            raise ValueError("legacy-openalex-v1 supports normalized records only; snapshot inputs are UNSUPPORTED_CAPABILITY")
        sources, evidence_text_by_source, input_bytes = _legacy_sources(legacy_records_path)
        adapter_inputs = {"legacy-normalized-records.jsonl": input_bytes}
        captures: list[tuple[str, bytes]] = []
        input_kind = "normalized_openalex_records"
        acquisition_status = "NORMALIZED_RECORDS_RECEIVED"
        input_sha = _sha256(input_bytes)
        digest_lock_sha256 = None
        manifest_sha256 = None
    else:
        if source_snapshots_path is None or legacy_records_path is not None:
            raise ValueError("e37-source-snapshot-v1 supports offline source snapshots only; normalized-record inputs are UNSUPPORTED_CAPABILITY")
        sources, evidence_text_by_source, captures, input_bytes, digest_lock_bytes = _snapshot_sources(
            source_snapshots_path, expected_digests_path, query_count,
        )
        adapter_inputs = {
            "source-snapshot-manifest.jsonl": input_bytes,
            "expected-capture-digests.json": digest_lock_bytes,
        }
        input_kind = "offline_source_snapshots"
        acquisition_status = "IMPORTED"
        input_sha = _sha256(input_bytes)

        digest_lock_sha256 = _sha256(digest_lock_bytes)
        manifest_sha256 = input_sha

    source_set_digest = _canonical_source_set_digest(sources)
    if source_set_digest != expected_source_set_digest:
        raise ValueError(
            "canonical source-set digest mismatch: expected "
            f"{expected_source_set_digest}, observed {source_set_digest}"
        )

    # Parse all inputs before creating a run directory so malformed inputs never
    # leave capture files without a matching receipt.
    claim_review_bytes = Path(claim_review_path).read_bytes()
    reviews = cli._read_claim_reviews(claim_review_bytes)
    if not reviews:
        raise ValueError("source-binding slot requires at least one claim-review row")
    if adapter_id == "legacy-openalex-v1" and any(row.get("evidence_field") == "captured_text" for row in reviews):
        raise ValueError("legacy-openalex-v1 does not support captured_text evidence; use the shared abstract field")
    draft_bytes = Path(draft_path).read_bytes()
    draft = draft_bytes.decode("utf-8")
    ledger, claim_review_status = cli._build_claim_review_ledger(
        reviews, sources, evidence_text_by_source=evidence_text_by_source,
    )
    draft_error = None
    try:
        cli._validate_draft(draft, {source["source_id"] for source in sources})
    except ValueError as exc:
        draft_error = str(exc)

    out = Path(output_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError(f"output directory must be absent or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    _write_bytes(out / "inputs" / "draft.md", draft_bytes)
    _write_bytes(out / "inputs" / "claim-review.jsonl", claim_review_bytes)
    _write_bytes(
        out / "inputs" / "expected-source-set-digest.txt",
        (expected_source_set_digest + "\n").encode("ascii"),
    )
    for filename, data in adapter_inputs.items():
        _write_bytes(out / "inputs" / filename, data)
    for path, raw in captures:
        _write_bytes(out / path, raw)

    status = _status(acquisition_status, claim_review_status, draft_error)
    adapter = ADAPTERS[adapter_id]
    context = {
        "task_id": task_id,
        "episode_id": episode_id,
        "source_set_id": source_set_id,
        "namespace": namespace,
        "authorization_scope": authorization_scope,
        "selected_at_utc": selected_at,
        "adapter_id": adapter_id,
        "adapter_source_commit": adapter["source_commit"],
        "slot_implementation_commit": implementation_commit,
        "capabilities": adapter["capabilities"],
        "slot_capabilities": SLOT_CAPABILITIES,
        "canonical_source_set_sha256": source_set_digest,
        "draft_sha256": _sha256(draft_bytes),
        "claim_review_sha256": _sha256(claim_review_bytes),
        "selection_policy": "fixed_at_run_start_no_hot_swap",
    }
    _write_json(out / "run-manifest.json", context)
    _write_jsonl(out / "sources.jsonl", sources)
    _write_jsonl(out / "claim-review.jsonl", ledger)
    report_lines = [
        f"# Source-binding run: {question}",
        "",
        f"- Run status: `{status}`",
        f"- Acquisition status: `{acquisition_status}`",
        f"- Claim review status: `{claim_review_status}`",
        f"- Selected adapter: `{adapter_id}` at `{adapter['source_commit']}`",
        f"- Slot implementation: `{implementation_commit}`",
        f"- Sources: {len(sources)}; claim rows: {len(ledger)}; exact anchors: {sum(row['evidence_anchor_status'] == 'EXACT_MATCH' for row in ledger)}",
        "",
        "## Interpretation ceiling",
        "",
        "Exact quote anchoring checks only that supplied text occurs in the selected evidence field. It does not authenticate the publisher origin, judge whether a quote supports a claim, or validate a human review label.",
        "Adapter selection is fixed for this run. A later independent run may select `legacy-openalex-v1`; no same-run fallback or overwrite is performed.",
    ]
    if draft_error:
        report_lines += ["", f"Draft rejected: `{draft_error}`"]
    _write_bytes(out / "report.md", ("\n".join(report_lines) + "\n").encode("utf-8"))
    receipt = {
        "schema": "ignition-source-binding-slot-run-v1",
        "context": context,
        "input": {
            "kind": input_kind,
            "sha256": input_sha,
            "manifest_sha256": manifest_sha256,
            "expected_capture_digest_lock_sha256": digest_lock_sha256,
            "canonical_source_set_sha256": source_set_digest,
            "expected_source_set_sha256": expected_source_set_digest,
            "source_set_digest_match": source_set_digest == expected_source_set_digest,
            "draft_sha256": _sha256(draft_bytes),
            "claim_review_sha256": _sha256(claim_review_bytes),
        "query_count": query_count if adapter_id == "e37-source-snapshot-v1" else None,
            "adapter_input_artifacts": [
                {"path": f"inputs/{filename}", "sha256": _sha256(data), "bytes": len(data)}
                for filename, data in sorted(adapter_inputs.items())
            ],
        },
        "status": status,
        "acquisition_status": acquisition_status,
        "claim_review_status": claim_review_status,
        "draft_error": draft_error,
        "claim_review_ceiling": "exact_anchor_only_no_source_authentication_or_semantic_support_validation",
        "semantic_validation_status": "NOT_PERFORMED",
        "counts": {
            "sources": len(sources),
            "claim_review_rows": len(ledger),
            "exact_anchors": sum(row["evidence_anchor_status"] == "EXACT_MATCH" for row in ledger),
            "not_found": sum(row["evidence_anchor_status"] == "NOT_FOUND" for row in ledger),
            "unknown_source": sum(row["evidence_anchor_status"] == "UNKNOWN_SOURCE" for row in ledger),
            "capture_bytes_retained": sum(source.get("capture_status") == "ATTACHED_BYTES_HASH_MATCHED" for source in sources),
            "model_calls": 0,
            "search_calls": 0,
            "network_requests": 0,
        },
        "rollback": {
            "same_run_fallback": False,
            "next_independent_run_adapter_id": "legacy-openalex-v1",
            "existing_nonempty_output_directory": "rejected",
        },
        "artifacts": _artifact_index(out),
        "limitations": [
            "The legacy arm is an offline normalized-record fixture replay, not a live OpenAlex search.",
            "The candidate arm imports the same frozen abstract observations; this comparison does not measure search, retrieval, or source-origin authenticity.",
            "The common source-set digest binds normalized abstract text and source identity; capture hashes bind saved bytes only.",
            "Neither digest authenticates the publisher or establishes semantic support.",
            "Human review judgments are supplied input and are not validated by exact matching.",
            "Human operator time, tokens, and remote retrieval costs were not measured by this local run.",
        ],
    }
    _write_json(out / "receipt.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--question", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--claim-reviews", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--source-set-id", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--authorization-scope", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--expected-source-set-digest", required=True)
    parser.add_argument("--legacy-records")
    parser.add_argument("--source-snapshots")
    parser.add_argument("--expected-digests")
    parser.add_argument("--query-count", type=int, default=12)
    args = parser.parse_args(argv)
    try:
        receipt = run_binding(
            adapter_id=args.adapter,
            question=args.question,
            output_dir=args.output_dir,
            draft_path=args.draft,
            claim_review_path=args.claim_reviews,
            task_id=args.task_id,
            episode_id=args.episode_id,
            source_set_id=args.source_set_id,
            namespace=args.namespace,
            authorization_scope=args.authorization_scope,
            implementation_commit=args.implementation_commit,
            expected_source_set_digest=args.expected_source_set_digest,
            legacy_records_path=args.legacy_records,
            source_snapshots_path=args.source_snapshots,
            expected_digests_path=args.expected_digests,
            query_count=args.query_count,
        )
    except (ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "adapter_id": receipt["context"]["adapter_id"],
        "status": receipt["status"],
        "acquisition_status": receipt["acquisition_status"],
        "claim_review_status": receipt["claim_review_status"],
        "receipt": str(Path(args.output_dir) / "receipt.json"),
    }, ensure_ascii=False))
    return 0 if receipt["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
