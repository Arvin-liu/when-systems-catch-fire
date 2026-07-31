#!/usr/bin/env python3
"""Event-sourced iteration lifecycle resolver (task 108, contract §3/§5).

Task 108 replaces the circular one-row terminality model (where a single
``merged-iteration-ledger`` row had to know its own future merge commit) with
an append-only, event-sourced model:

  * ``ITERATION_CANDIDATE``        — immutable event committed BEFORE the
                                     content PR merges. It contains no invented
                                     future merge commit.
  * ``TERMINALIZATION_PROJECTION`` — appended AFTER the content PR is ordinarily
                                     merged; it binds the now-known content PR
                                     and merge, and is the only event allowed to
                                     carry terminal-tag facts.
  * ``LEGACY_TERMINAL_SUCCESS``     — backward-compatible wrapper for historical
                                     terminal rows (104/105) so the resolver
                                     treats them as resolved without rewriting
                                     them.

A task's status is *derived* deterministically from the valid event set plus
annotated terminal tags. Raw history is preserved; nothing is deleted or
rewritten.

The resolver FAILS CLOSED: if full Git history or required tags are
unavailable, or any consistency rule is violated, the affected task resolves to
``INVALID``/``BLOCKED`` rather than being silently accepted.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

DEFAULT_EVENTS_PATH = os.path.join(REPO, "data", "operations", "lifecycle-events.jsonl")

# Resolved lifecycle states recognized by the contract (§5).
RESOLVED_STATES = {
    "READY_FOR_CONTENT_MERGE",
    "CONTENT_MERGED_AWAITING_TERMINALIZATION",
    "AWAITING_TERMINAL_TAG",
    "TERMINAL_SUCCESS",
    "BLOCKED",
    "INVALID",
}

VALID_EVENT_TYPES = {
    "ITERATION_CANDIDATE",
    "TERMINALIZATION_PROJECTION",
    "LEGACY_TERMINAL_SUCCESS",
}

TERMINAL_TAG_RE = re.compile(r"^ignition/iterations/(\d+)/terminal-r1$")


# ---------------------------------------------------------------------------
# Loading / validation of raw events
# ---------------------------------------------------------------------------

def events_path() -> str:
    return os.path.abspath(DEFAULT_EVENTS_PATH)


def load_events(path: Optional[str] = None) -> List[Dict]:
    p = os.path.abspath(path or DEFAULT_EVENTS_PATH)
    if not os.path.exists(p):
        raise FileNotFoundError(f"lifecycle events not found: {p}")
    events: List[Dict] = []
    with open(p, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p}:{lineno}: invalid JSON: {exc}") from exc
    return events


def validate_event_schema(event: Dict) -> List[str]:
    """Structural validation of a single event. Does not require Git."""
    problems: List[str] = []
    tn = event.get("task_number")
    if not isinstance(tn, int):
        problems.append(f"event missing integer task_number: {event.get('task_id')}")
        return problems
    et = event.get("event_type")
    if et not in VALID_EVENT_TYPES:
        problems.append(f"task {tn}: invalid event_type {et!r}")
    if et == "ITERATION_CANDIDATE":
        if event.get("lifecycle_state") != "READY_FOR_CONTENT_MERGE":
            problems.append(f"task {tn}: ITERATION_CANDIDATE must be READY_FOR_CONTENT_MERGE")
        # A candidate must NOT contain invented future merge commits.
        for forb in ("content_merge_commit", "terminalization_merge_commit",
                     "terminal_tag_object_sha", "terminal_tag_target", "core_receipt_sha256"):
            if event.get(forb) not in (None, "", "null"):
                problems.append(f"task {tn}: candidate must not contain future {forb}")
        # A candidate must not carry a fabricated exact head placeholder.
        hv = event.get("exact_reviewed_content_head")
        if isinstance(hv, str) and (hv.startswith("<") or hv in ("", "null", "placeholder")):
            problems.append(f"task {tn}: candidate exact_reviewed_content_head is a placeholder, not a real commit")
        prn = event.get("formal_content_pr_number")
        if prn is not None and (not isinstance(prn, int)):
            problems.append(f"task {tn}: candidate formal_content_pr_number must be int or null")
    if et == "TERMINALIZATION_PROJECTION":
        if not isinstance(event.get("content_pr_number"), int):
            problems.append(f"task {tn}: TERMINALIZATION_PROJECTION requires content_pr_number")
        cmc = event.get("content_merge_commit")
        if not isinstance(cmc, str) or cmc in ("", "null", "<placeholder>"):
            problems.append(f"task {tn}: TERMINALIZATION_PROJECTION requires a real content_merge_commit")
    return problems


# ---------------------------------------------------------------------------
# Git history helpers (fail-closed: any failure => None, treated as missing)
# ---------------------------------------------------------------------------

def _git(*args: str) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "-C", REPO, *args],
            capture_output=True, text=True, timeout=120,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except Exception:
        return None


def commit_exists(sha: str) -> bool:
    return _git("cat-file", "-t", sha) == "commit"


def is_ancestor(ancestor: str, descendant: str) -> bool:
    if _git("merge-base", "--is-ancestor", ancestor, descendant) == "":
        return True
    return False


def ref_exists(ref: str) -> bool:
    return _git("rev-parse", "--verify", "--quiet", ref) is not None


def annotated_tag_object_sha(tag_name: str) -> Optional[str]:
    """Return the tag *object* SHA for an annotated tag, or None if not annotated."""
    # For an annotated tag, `git rev-parse <tag>` gives the commit it points to,
    # while `git rev-list -n1 --objects <tag>` / `git cat-file` gives the tag object.
    obj = _git("rev-parse", f"{tag_name}^{{}}")  # dereferences to the tagged object
    tag_obj = _git("rev-parse", f"refs/tags/{tag_name}")
    if tag_obj is None:
        return None
    # Determine if it is annotated: compare tag ref type.
    typ = _git("cat-file", "-t", f"refs/tags/{tag_name}")
    if typ == "tag":
        # tag object sha is the ref's resolved sha (the tag object itself)
        return tag_obj
    return None  # lightweight tag (no tag object) -> None


def tag_points_to(tag_name: str, target_commit: str) -> bool:
    deref = _git("rev-parse", f"{tag_name}^{{}}")
    return deref == target_commit


def tag_message(tag_name: str) -> Optional[str]:
    return _git("tag", "-l", "--format=%(contents)", tag_name)


# ---------------------------------------------------------------------------
# Terminal tag verification against Git (fail-closed)
# ---------------------------------------------------------------------------

def verify_terminal_tag(event: Dict, main_ref: str = "origin/main") -> List[str]:
    """Verify an annotated terminal tag declared by a projection event.

    Fails closed on: missing tag, lightweight (not annotated) tag, target
    mismatch, malformed/missing message fields, or core-receipt mismatch.
    """
    problems: List[str] = []
    tn = event["task_number"]
    tag_name = event.get("terminal_tag_name")
    if not tag_name:
        problems.append(f"task {tn}: terminal tag name missing")
        return problems
    if not TERMINAL_TAG_RE.match(tag_name or ""):
        problems.append(f"task {tn}: terminal tag name {tag_name!r} does not match ignition/iterations/<n>/terminal-r1")
        return problems
    if not ref_exists(f"refs/tags/{tag_name}"):
        problems.append(f"task {tn}: terminal tag {tag_name} not found in repo")
        return problems
    obj_sha = annotated_tag_object_sha(tag_name)
    if obj_sha is None:
        problems.append(f"task {tn}: terminal tag {tag_name} is lightweight, not annotated (force-move / wrong type)")
        return problems
    declared_obj = event.get("terminal_tag_object_sha")
    if declared_obj and declared_obj != obj_sha:
        problems.append(f"task {tn}: terminal tag object sha mismatch declared={declared_obj} actual={obj_sha}")
    target = event.get("terminal_tag_target")
    if target and not tag_points_to(tag_name, target):
        problems.append(f"task {tn}: terminal tag {tag_name} does not point to declared target {target}")
    msg = tag_message(tag_name) or ""
    for field in ("task_number", "task_id", "terminal_state", "core_receipt_sha256", "attestation_mode"):
        if field not in msg:
            problems.append(f"task {tn}: terminal tag message missing required field {field}")
    declared_core = event.get("core_receipt_sha256")
    if declared_core and declared_core not in msg:
        problems.append(f"task {tn}: terminal tag message does not bind declared core_receipt_sha256 {declared_core}")
    return problems


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def resolve_task(
    events: List[Dict],
    task_number: int,
    main_ref: str = "origin/main",
    git_available: bool = True,
) -> Dict:
    """Deterministically resolve a single task's lifecycle state.

    Returns a dict with: task_number, resolved_state, errors[], sources[].
    NEVER raises; fails closed to INVALID/BLOCKED.
    """
    task_events = [e for e in events if e.get("task_number") == task_number]
    errors: List[str] = []
    sources: List[str] = []

    if not task_events:
        return {
            "task_number": task_number,
            "resolved_state": "INVALID",
            "errors": ["no lifecycle event for task"],
            "sources": [],
        }

    # Schema validity.
    for ev in task_events:
        errors += validate_event_schema(ev)

    candidates = [e for e in task_events if e.get("event_type") == "ITERATION_CANDIDATE"]
    projections = [e for e in task_events if e.get("event_type") == "TERMINALIZATION_PROJECTION"]
    legacies = [e for e in task_events if e.get("event_type") == "LEGACY_TERMINAL_SUCCESS"]

    # Legacy rows resolve directly (backward compatibility).
    if len(legacies) == 1 and not candidates and not projections:
        lg = legacies[0]
        if lg.get("lifecycle_state") == "TERMINAL_SUCCESS":
            return {
                "task_number": task_number,
                "resolved_state": "TERMINAL_SUCCESS",
                "errors": errors,
                "sources": ["LEGACY_TERMINAL_SUCCESS"],
            }

    if len(candidates) != 1:
        errors.append(f"expected exactly one ITERATION_CANDIDATE, got {len(candidates)}")

    if len(projections) > 1:
        errors.append(f"duplicate/conflicting TERMINALIZATION_PROJECTION events: {len(projections)}")

    candidate = candidates[0] if candidates else {}

    # Consistency: candidate must not pretend to be terminal.
    if candidate.get("lifecycle_state") in ("TERMINAL_SUCCESS", "AWAITING_TERMINAL_TAG"):
        errors.append("candidate event must not assert terminal lifecycle_state")

    # Projection must not precede its content merge (fail-closed).
    if projections:
        proj = projections[0]
        content_merge = proj.get("content_merge_commit")
        content_pr = proj.get("content_pr_number")
        candidate_content_pr = candidate.get("formal_content_pr_number")
        if git_available:
            if content_merge and not commit_exists(content_merge):
                errors.append(f"projection content_merge_commit {content_merge} not found in history")
            if content_pr and candidate_content_pr and content_pr != candidate_content_pr:
                errors.append(f"projection content_pr {content_pr} != candidate content_pr {candidate_content_pr}")
            # Reject terminal projection that has a terminal tag before content merge.
            tag_name = proj.get("terminal_tag_name")
            if tag_name and ref_exists(f"refs/tags/{tag_name}"):
                if content_merge and not is_ancestor(content_merge, f"refs/tags/{tag_name}^{{}}"):
                    errors.append("terminal tag points to a non-terminalization commit (not descendant of content merge)")
        if proj.get("terminal_tag_name") and git_available:
            errors += verify_terminal_tag(proj, main_ref)

    resolved = "READY_FOR_CONTENT_MERGE"
    if candidate.get("formal_content_pr_number") or candidate.get("exact_reviewed_content_head"):
        resolved = "CONTENT_MERGED_AWAITING_TERMINALIZATION" if projections else "CONTENT_MERGED_AWAITING_TERMINALIZATION"
    if projections and projections[0].get("terminal_tag_name"):
        resolved = "AWAITING_TERMINAL_TAG"
    if projections and projections[0].get("terminal_state") == "TERMINAL_SUCCESS":
        resolved = "TERMINAL_SUCCESS" if not errors else "INVALID"

    if errors:
        # Prefer INVALID over a green state when any rule was violated.
        if resolved == "TERMINAL_SUCCESS":
            resolved = "INVALID"

    return {
        "task_number": task_number,
        "resolved_state": resolved,
        "errors": errors,
        "sources": [e.get("event_type") for e in task_events],
    }


def resolve_all(events: List[Dict], task_numbers: Optional[List[int]] = None,
                main_ref: str = "origin/main") -> Dict[int, Dict]:
    if task_numbers is None:
        task_numbers = sorted({e.get("task_number") for e in events if isinstance(e.get("task_number"), int)})
    out: Dict[int, Dict] = {}
    for tn in task_numbers:
        out[tn] = resolve_task(events, tn, main_ref)
    return out


def derive_current_truth(events: List[Dict], main_ref: str = "origin/main") -> Dict:
    """Produce a derived resolved lifecycle view from events + tags."""
    resolved = resolve_all(events, main_ref=main_ref)
    terminal = [tn for tn, r in resolved.items() if r["resolved_state"] == "TERMINAL_SUCCESS"]
    non_terminal = [tn for tn, r in resolved.items() if r["resolved_state"] != "TERMINAL_SUCCESS"]
    latest_terminal = max(terminal) if terminal else None
    return {
        "schema_version": "1.0.0",
        "derived_from": "lifecycle-events.jsonl + annotated terminal tags",
        "terminal_tasks": terminal,
        "non_terminal_tasks": non_terminal,
        "current_accepted_iteration": latest_terminal,
        "resolved": {str(k): v["resolved_state"] for k, v in resolved.items()},
        "errors": {str(k): v["errors"] for k, v in resolved.items() if v["errors"]},
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--events", default=None)
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    evs = load_events(args.events or os.path.join(repo, "data", "operations", "lifecycle-events.jsonl"))
    view = derive_current_truth(evs, args.main_ref)
    view = derive_current_truth(evs, args.main_ref)
    if args.json:
        print(json.dumps(view, ensure_ascii=False, indent=2))
        return 0
    problems = 0
    for tn, st in view["resolved"].items():
        flag = "" if st == "TERMINAL_SUCCESS" else "  <-- NOT TERMINAL"
        if st != "TERMINAL_SUCCESS":
            problems += 1
        print(f"task {tn}: {st}{flag}")
    if view["errors"]:
        for tn, errs in view["errors"].items():
            for e in errs:
                print(f"  ERROR task {tn}: {e}", file=sys.stderr)
    if problems:
        print(f"LIFECYCLE_NOT_ALL_TERMINAL tasks={len(view['resolved'])} non_terminal={problems}", file=sys.stderr)
        return 1
    print("LIFECYCLE_OK all events resolve TERMINAL_SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
