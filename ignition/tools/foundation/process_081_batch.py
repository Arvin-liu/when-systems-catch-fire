#!/usr/bin/env python3
"""IGNITION-081: Batch semantic adjudication processor.

Reads pending queue items, reads legacy source files, produces adjudication records,
updates run state, and handles batch commits.

This script handles the mechanical parts (file reading, hashing, schema validation,
batch writing, run-state updates). The semantic judgment fields are populated
by the agent's reading of the source text.
"""
from __future__ import annotations

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT / "data/foundation/work-queues/080-semantic-review-queue.jsonl"
ADJ_PATH = ROOT / "data/foundation/adjudications/080-source-text-adjudications.jsonl"
ESCALATION_PATH = ROOT / "data/foundation/escalations/080-highest-model-queue.jsonl"
QUALITY_PATH = ROOT / "data/foundation/adjudications/080-quality-audits.jsonl"
RUN_STATE_PATH = ROOT / "data/foundation/adjudications/080-run-state.json"

TZ = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def save_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_source_file(legacy_path: str) -> tuple[str, str, int]:
    """Read a legacy source file, return (content, sha256, line_count)."""
    full_path = ROOT / legacy_path
    if not full_path.exists():
        raise FileNotFoundError(f"Source file not found: {legacy_path}")
    content = full_path.read_text(encoding="utf-8")
    sha = compute_sha256(content)
    lines = content.splitlines()
    return content, sha, len(lines)


def get_pending_batch(queue: list[dict], start_id: str | None = None, batch_size: int = 25) -> list[dict]:
    """Get next batch of pending items, optionally starting from a specific ID."""
    pending = [q for q in queue if q.get("status") == "PENDING"]
    if start_id:
        # Find the index of start_id and take from there
        idx = next((i for i, q in enumerate(pending) if q["stable_id"] == start_id), 0)
        return pending[idx:idx + batch_size]
    return pending[:batch_size]


def update_queue_status(queue: list[dict], completed_ids: set[str]) -> list[dict]:
    """Mark completed IDs in the queue."""
    for item in queue:
        if item["stable_id"] in completed_ids:
            item["status"] = "COMPLETED_ACCEPTED"
            item["last_updated_at"] = now_iso()
    return queue


def main():
    import argparse
    parser = argparse.ArgumentParser(description="081 batch processor")
    parser.add_argument("--list-pending", action="store_true", help="List pending IDs")
    parser.add_argument("--read-source", type=str, help="Read a source file by stable_id")
    parser.add_argument("--stats", action="store_true", help="Show current stats")
    args = parser.parse_args()

    if args.list_pending:
        queue = load_jsonl(QUEUE_PATH)
        pending = [q for q in queue if q.get("status") == "PENDING"]
        for p in pending[:50]:
            print(f"{p['stable_id']:6s}  {p['legacy_path']}")
        print(f"... total pending: {len(pending)}")

    elif args.read_source:
        queue = load_jsonl(QUEUE_PATH)
        item = next((q for q in queue if q["stable_id"] == args.read_source), None)
        if not item:
            print(f"ID {args.read_source} not found in queue")
            sys.exit(1)
        content, sha, nlines = read_source_file(item["legacy_path"])
        print(f"=== {item['stable_id']} ===")
        print(f"Path: {item['legacy_path']}")
        print(f"SHA-256: {sha}")
        print(f"Lines: {nlines}")
        print(f"Risk: {item.get('risk_level', '?')}")
        print("---")
        print(content)

    elif args.stats:
        queue = load_jsonl(QUEUE_PATH)
        reviews = load_jsonl(ADJ_PATH)
        escalations = load_jsonl(ESCALATION_PATH)
        run_state = json.loads(RUN_STATE_PATH.read_text(encoding="utf-8"))
        pending = [q for q in queue if q.get("status") == "PENDING"]
        completed = [q for q in queue if q.get("status") == "COMPLETED_ACCEPTED"]
        print(f"Queue total: {len(queue)}")
        print(f"Completed: {len(completed)}")
        print(f"Pending: {len(pending)}")
        print(f"Reviews: {len(reviews)}")
        print(f"Escalations: {len(escalations)}")
        print(f"Run state status: {run_state.get('status')}")
        print(f"Next pending: {run_state.get('next_pending_stable_id')}")
        print(f"Next batch: {run_state.get('next_pending_batch')}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
