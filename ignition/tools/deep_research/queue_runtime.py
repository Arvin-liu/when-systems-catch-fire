"""Deep Research Capability — serial, crash-resumable queue runtime (Round 2).

A deterministic outer queue that invokes ONE active research episode by default.
It consumes the Round 1 record schemas (research-queue-item, research-campaign,
research-topic-candidate, research-episode-result) but is intentionally free of
any episode-execution logic — that belongs to Round 3.

Design invariants (per TASK.md Round 2):
* Deterministic: ranking is a pure function; ties break by queue_item_id; the
  selector never uses randomness. A provided model proposal may reorder among
  equally-passing candidates but CANNOT override a hard gate (e.g. a lease held
  by another owner, or a BLOCKED item).
* Crash-resumable: items left ACTIVE with an expired/missing lease are returned
  to QUEUED by ``recover``; every transition records a per-episode checkpoint
  identity (``checkpoint_commit``).
* Idempotent claim / duplicate prevention: re-claiming by the same owner
  refreshes the lease; a second distinct owner cannot take an unexpired lease.
* Campaign stopping is independent of any single episode: a long report, many
  URLs, or an executor ``success`` NEVER stops the queue. Only the seven
  campaign-level conditions stop it.

Run from the repository root:
    python3 tools/deep_research/queue_runtime.py   # self smoke-test
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from deep_research import records as R  # noqa: E402

# Ranking factors. Benefit factors raise the score; penalty factors lower it.
BENEFIT_FACTORS = (
    "materiality",
    "expected_information_gain",
    "tractability",
    "access",
    "freshness",
    "diversity",
)
PENALTY_FACTORS = ("cost", "risk")
LOW_INFORMATION_THRESHOLD = 3

# Statuses that mean "still in the runnable pool".
_RUNNABLE = ("QUEUED", "ACTIVE")


# ---------------------------------------------------------------------------
# Time helpers (ISO-8601 UTC; schema-valid string fields)
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _add_ttl_iso(iso: str, ttl_seconds: float) -> str:
    return (_parse_iso(iso) + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lease_expired(lease: dict, now_iso: str) -> bool:
    expiry = lease.get("expiry")
    if not expiry:
        return True
    return _parse_iso(expiry) < _parse_iso(now_iso)


# ---------------------------------------------------------------------------
# Pure ranking
# ---------------------------------------------------------------------------
def rank_score(candidate: dict) -> float:
    """Deterministic, inspectable ranking score.

    Benefit factors raise the score; penalty factors (cost, risk) lower it.
    Accepts either a topic-candidate dict directly or a queue-item dict (in which
    case the factors are read from its nested ``topic_candidate``). Returns 0.0
    for a candidate missing all factors (still deterministic).
    """
    c = candidate.get("topic_candidate") or candidate
    score = 0.0
    for f in BENEFIT_FACTORS:
        score += float(c.get(f, 0.0) or 0.0)
    for f in PENALTY_FACTORS:
        score -= float(c.get(f, 0.0) or 0.0)
    return score


def rank_candidates(candidates: list[dict]) -> list[tuple[float, dict]]:
    """Return (score, candidate) sorted by score desc, then queue_item_id asc."""
    scored = [(rank_score(c), c) for c in candidates]
    scored.sort(key=lambda x: (-x[0], x[1].get("queue_item_id", "")))
    return scored


# ---------------------------------------------------------------------------
# Hard-gate for selection (cannot be overridden by a model proposal)
# ---------------------------------------------------------------------------
def passes_selection_gate(item: dict, now_iso: str) -> bool:
    """A QUEUED item is selectable unless a hard gate blocks it.

    Hard gates: item must be in the runnable pool; a live lease held by ANOTHER
    owner cannot be taken over (duplicate prevention); BLOCKED/SKIPPED/COMPLETED
    are never selectable. A model proposal may reorder, but it cannot select an
    item that fails this gate.
    """
    if item.get("status") not in _RUNNABLE:
        return False
    lease = item.get("lease")
    if lease and lease.get("owner") and _parse_iso(lease.get("expiry", "0001")) >= _parse_iso(now_iso):
        # unexpired lease held by someone — selector must not take it over
        return False
    return True


# ---------------------------------------------------------------------------
# Lease: idempotent claim, duplicate prevention, expiry
# ---------------------------------------------------------------------------
def claim_lease(item: dict, owner: str, now_iso: str, ttl_seconds: float = 3600) -> tuple[bool, str]:
    """Attempt to claim/refresh a lease on ``item`` for ``owner``.

    Returns (granted, reason). Reasons:
      LEASE_REFRESHED   — same owner re-claimed an unexpired lease (idempotent)
      LEASE_ACQUIRED    — new or expired-other lease acquired
      LEASE_HELD_BY_OTHER — an unexpired lease is held by a different owner
    """
    lease = item.get("lease")
    if lease and lease.get("owner") != owner:
        if not _lease_expired(lease, now_iso):
            return False, "LEASE_HELD_BY_OTHER"
    claim_id = (lease or {}).get("claim_id") or f"lease-{uuid.uuid4().hex[:12]}"
    item["lease"] = {
        "owner": owner,
        "expiry": _add_ttl_iso(now_iso, ttl_seconds),
        "claim_id": claim_id,
    }
    if lease and lease.get("owner") == owner:
        return True, "LEASE_REFRESHED"
    return True, "LEASE_ACQUIRED"


def release_lease(item: dict, owner: str) -> bool:
    lease = item.get("lease")
    if lease and lease.get("owner") == owner:
        item["lease"] = None
        return True
    return False


# ---------------------------------------------------------------------------
# Crash recovery
# ---------------------------------------------------------------------------
def recover(items: list[dict], now_iso: str) -> list[str]:
    """Return ACTIVE items with a missing/expired lease back to QUEUED.

    This is what makes the queue crash-resumable: if the process died while an
    episode was ACTIVE, on restart the lease is expired and the item is returned
    to the runnable pool (its per-episode ``checkpoint_commit`` is preserved so
    the episode can resume rather than restart blind).
    """
    recovered: list[str] = []
    for item in items:
        if item.get("status") != "ACTIVE":
            continue
        lease = item.get("lease")
        if not lease or _lease_expired(lease, now_iso):
            item["status"] = "QUEUED"
            item["lease"] = None
            recovered.append(item.get("queue_item_id", ""))
    return recovered


# ---------------------------------------------------------------------------
# Episode-result ingestion (never stops the queue)
# ---------------------------------------------------------------------------
def _is_low_information(result: dict) -> bool:
    decision = ((result.get("sufficiency_decision") or {}).get("decision"))
    final_state = result.get("final_state")
    return decision == "STOP_INSUFFICIENT_EVIDENCE" or final_state == "INSUFFICIENT_EVIDENCE_COMPLETE"


def ingest_result(items: list[dict], result: dict, now_iso: Optional[str] = None) -> Optional[str]:
    """Mark the queue item for ``result.episode_id`` COMPLETED and record its
    per-episode checkpoint identity. Returns the queue_item_id, or None if no
    matching ACTIVE/QUEUED item was found. This NEVER triggers a queue stop —
    continuation is decided solely by ``should_stop`` against campaign state."""
    episode_id = result.get("episode_id")
    target = None
    for item in items:
        if item.get("episode_id") == episode_id and item.get("status") in _RUNNABLE:
            target = item
            break
    if target is None:
        return None
    target["status"] = "COMPLETED"
    target["checkpoint_commit"] = result.get("machine_trace_ref") or result.get("report_ref")
    target["lease"] = None
    return target.get("queue_item_id")


# ---------------------------------------------------------------------------
# Campaign-level stopping (independent of any single episode)
# ---------------------------------------------------------------------------
def should_stop(campaign: dict, items: list[dict], stats: dict,
                now_iso: str, low_info_threshold: int = LOW_INFORMATION_THRESHOLD) -> tuple[bool, Optional[str]]:
    """Evaluate campaign stop conditions. Returns (should_stop, reason).

    Long reports, many URLs, and executor ``success`` are intentionally absent —
    they must never stop the queue. Only these conditions stop it:
      OWNER_STOP, DEADLINE, MAX_EPISODES, BUDGET, QUEUE_EMPTY, SAFETY_BLOCKER,
      LOW_INFORMATION.
    """
    sc = campaign.get("stop_conditions", {}) or {}

    if sc.get("owner_stop"):
        return True, "OWNER_STOP"

    deadline = sc.get("deadline")
    if deadline and _parse_iso(deadline) < _parse_iso(now_iso):
        return True, "DEADLINE"

    max_ep = sc.get("max_episodes") or sc.get("max_attempts")
    if max_ep is not None and stats.get("completions", 0) >= int(max_ep):
        return True, "MAX_EPISODES"

    budget = sc.get("budget")
    if budget is not None and float(stats.get("cost", 0.0)) >= float(budget):
        return True, "BUDGET"

    remaining = [i for i in items if i.get("status") in _RUNNABLE]
    if not remaining and sc.get("queue_empty_stops"):
        return True, "QUEUE_EMPTY"

    if sc.get("safety_blocker_stops") and any(i.get("status") == "BLOCKED" for i in items):
        return True, "SAFETY_BLOCKER"

    if sc.get("low_information_stops") and stats.get("consecutive_low_info", 0) >= low_info_threshold:
        return True, "LOW_INFORMATION"

    return False, None


# ---------------------------------------------------------------------------
# Selector
# ---------------------------------------------------------------------------
def select_next(items: list[dict], now_iso: str,
                model_proposal: Optional[list[str]] = None,
                owner: Optional[str] = None,
                ttl_seconds: float = 3600) -> Optional[dict]:
    """Deterministically select the next runnable item, optionally claiming a
    lease for ``owner``. A model proposal may reorder among gate-passing items
    but cannot select an item that fails ``passes_selection_gate``."""
    candidates = [i for i in items if passes_selection_gate(i, now_iso)]
    if not candidates:
        return None

    if model_proposal:
        prop_index = {cid: idx for idx, cid in enumerate(model_proposal)}
        def _key(i: dict):
            cid = i.get("queue_item_id", "")
            p = prop_index.get(cid, 10 ** 9)
            return (p, -rank_score(i), cid)
        ordered = sorted(candidates, key=_key)
    else:
        ordered = [i for _, i in rank_candidates(candidates)]

    selected = ordered[0]
    if owner:
        claim_lease(selected, owner, now_iso, ttl_seconds)
        selected["status"] = "ACTIVE"
    return selected


# ---------------------------------------------------------------------------
# Convenience container
# ---------------------------------------------------------------------------
class SerialQueue:
    """Thin stateful wrapper over the pure functions above."""

    def __init__(self, campaign: Optional[dict] = None, items: Optional[list[dict]] = None,
                 owner: str = "workbuddy"):
        self.campaign = campaign or R.make_campaign()
        self.items = items or []
        self.owner = owner
        self.stats = {"completions": 0, "attempts": 0, "cost": 0.0, "consecutive_low_info": 0}

    def add_candidate(self, candidate: dict, queue_item_id: Optional[str] = None) -> dict:
        qid = queue_item_id or candidate.get("candidate_id") or f"qi-{uuid.uuid4().hex[:8]}"
        item = R.make_queue_item(queue_item_id=qid, topic_candidate=candidate, status="QUEUED")
        self.items.append(item)
        return item

    def select_next(self, now_iso: Optional[str] = None,
                    model_proposal: Optional[list[str]] = None,
                    ttl_seconds: float = 3600) -> Optional[dict]:
        return select_next(self.items, now_iso or _now_iso(), model_proposal,
                           self.owner, ttl_seconds)

    def recover(self, now_iso: Optional[str] = None) -> list[str]:
        return recover(self.items, now_iso or _now_iso())

    def ingest_result(self, result: dict, now_iso: Optional[str] = None) -> Optional[str]:
        qid = ingest_result(self.items, result, now_iso or _now_iso())
        if qid is not None:
            self.stats["completions"] += 1
            self.stats["attempts"] += 1
            if _is_low_information(result):
                self.stats["consecutive_low_info"] += 1
            else:
                self.stats["consecutive_low_info"] = 0
            cost = (result.get("sufficiency_decision") or {}).get("cost")
            if cost is not None:
                self.stats["cost"] = float(self.stats["cost"]) + float(cost)
        return qid

    def should_stop(self, now_iso: Optional[str] = None) -> tuple[bool, Optional[str]]:
        return should_stop(self.campaign, self.items, self.stats, now_iso or _now_iso())

    def set_checkpoint(self, queue_item_id: str, commit: str) -> bool:
        for i in self.items:
            if i.get("queue_item_id") == queue_item_id:
                i["checkpoint_commit"] = commit
                return True
        return False


# ---------------------------------------------------------------------------
# Self smoke-test
# ---------------------------------------------------------------------------
def _smoke() -> None:
    now = "2026-02-01T00:00:00Z"
    q = SerialQueue(
        campaign=R.make_campaign(stop_conditions={"queue_empty_stops": True, "max_episodes": 5}),
        owner="workbuddy",
    )
    a = q.add_candidate(R.make_topic_candidate(
        candidate_id="cand-A", proposed_question="A", materiality=0.9, risk=0.1))
    b = q.add_candidate(R.make_topic_candidate(
        candidate_id="cand-B", proposed_question="B", materiality=0.4, risk=0.8))
    sel = q.select_next(now_iso=now)
    assert sel is not None and sel["queue_item_id"] == "cand-A", "must pick highest-ranked"
    # crash recovery: simulate ACTIVE with expired lease
    q.items[0]["lease"]["expiry"] = "2020-01-01T00:00:00Z"
    rec = q.recover(now_iso=now)
    assert "cand-A" in rec, "expired ACTIVE lease must be recovered to QUEUED"
    # ingest a 'success' result with many URLs — must NOT stop the queue
    a["episode_id"] = "ep-A"
    b["episode_id"] = "ep-B"
    q.ingest_result(R.make_episode_result(episode_id="ep-A", final_state="CANDIDATE_COMPLETE"),
                    now_iso=now)
    stopped, reason = q.should_stop(now_iso=now)
    assert not stopped, "executor success + many URLs must never stop the queue"
    # queue empty stop after completing everything
    q.ingest_result(R.make_episode_result(episode_id="ep-B", final_state="CANDIDATE_COMPLETE"),
                    now_iso=now)
    stopped, reason = q.should_stop(now_iso=now)
    assert stopped and reason == "QUEUE_EMPTY", f"expected QUEUE_EMPTY, got {reason}"
    print("queue_runtime.py smoke OK")


if __name__ == "__main__":
    _smoke()
