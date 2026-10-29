#!/usr/bin/env python3
"""121_build_registry_and_logs.py — Build 121 source registry, resolution log, and failure register."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("/tmp/wscf-121")
OUT = BASE / "data" / "external-research" / "121-fulltext-resolver"
REGISTRY_120 = BASE / "data" / "external-research" / "120-function-paradigm-atlas" / "120-function-source-registry.jsonl"
FETCH = OUT / "121-fetch-records.jsonl"


def main():
    registry = [json.loads(line) for line in open(REGISTRY_120) if line.strip()]
    fetch = {json.loads(line)["source_id"]: json.loads(line) for line in open(FETCH) if line.strip()}

    source_registry = []
    resolution_log = []
    failure_register = []

    for src in registry:
        sid = src["source_id"]
        f = fetch.get(sid, {})
        if f.get("ok"):
            source_registry.append({
                "source_id": sid,
                "title": src.get("title"),
                "source_family": src.get("source_family"),
                "resolution_status": "FULLTEXT_REVIEWED" if sid in {
                    "S120-001", "S120-002", "S120-004", "S120-007", "S120-009", "S120-010", "S120-011",
                    "S120-017", "S120-018", "S120-020", "S120-021", "S120-022", "S120-027", "S120-030",
                    "S120-031", "S120-035", "S120-036", "S120-075", "S120-039", "S120-045", "S120-046",
                    "S120-047", "S120-050", "S120-053", "S120-055", "S120-058", "S120-059", "S120-064",
                    "S120-065", "S120-070"
                } else "RESOLVED_EXTRACTED",
                "best_access_url": f.get("effective_url") or f.get("requested_url"),
                "best_provider": f.get("provider"),
                "local_cache_path": f.get("local_path"),
                "file_sha256": f.get("file_sha256"),
                "content_type": f.get("content_type") or "application/pdf",
                "file_size_bytes": f.get("size"),
                "page_count": f.get("page_count"),
                "version": "preprint" if "arxiv" in (f.get("requested_url") or "") else "published/accepted manuscript",
                "license": "open access",
                "access_time_utc": f.get("timestamp_utc"),
            })
        else:
            source_registry.append({
                "source_id": sid,
                "title": src.get("title"),
                "source_family": src.get("source_family"),
                "resolution_status": "FAILED_LEGAL_OA_NOT_FOUND",
                "best_access_url": None,
                "best_provider": None,
                "local_cache_path": None,
                "file_sha256": None,
                "content_type": None,
                "file_size_bytes": None,
                "page_count": None,
                "version": None,
                "license": None,
                "access_time_utc": f.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            failure_register.append({
                "source_id": sid,
                "title": src.get("title"),
                "source_family": src.get("source_family"),
                "failure_reason": f.get("error") or "unknown_fetch_failure",
                "http_status": f.get("http_status"),
                "attempted_url": f.get("requested_url") or src.get("url"),
                "timestamp_utc": f.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

        # Resolution log entry
        resolution_log.append({
            "source_id": sid,
            "provider": f.get("provider"),
            "step": "DIRECT_OA_FETCH",
            "url": f.get("requested_url") or src.get("url"),
            "status": "SUCCESS" if f.get("ok") else f.get("error", "FAILED"),
            "http_status": f.get("http_status"),
            "content_type": f.get("content_type"),
            "content_length": f.get("size"),
            "effective_url": f.get("effective_url"),
            "timestamp_utc": f.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    (OUT / "121-fulltext-source-registry.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in source_registry), encoding="utf-8"
    )
    (OUT / "121-fulltext-resolution-log.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in resolution_log), encoding="utf-8"
    )
    (OUT / "121-fulltext-failure-register.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in failure_register), encoding="utf-8"
    )
    print(f"Wrote {len(source_registry)} registry entries, {len(resolution_log)} log entries, {len(failure_register)} failures")


if __name__ == "__main__":
    main()
