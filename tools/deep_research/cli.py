"""Deep Research Capability — CLI / API invocation surface (Round 3).

Entry points required by TASK.md Round 3:
  * one episode            (episode)
  * one queue step         (queue-step)
  * queue run until stop   (run-until-stop)
  * inspect / pause / resume / replay
  * claim and obligation operations missing from PR #190

The module is deliberately offline-safe: it never performs network I/O itself.
Live fetching is wired by the adapters (Round 6 pilot). All commands operate on
local JSON files and the in-repo Python objects, so they are unit-testable.

Usage (from repo root):
    python3 tools/deep_research/cli.py episode --question "..." --strategy-pack sp
    python3 tools/deep_research/cli.py queue-step --queue q.json --now 2026-...
    python3 tools/deep_research/cli.py run-until-stop --queue q.json
    python3 tools/deep_research/cli.py inspect --episode ep.json
    python3 tools/deep_research/cli.py pause --episode ep.json
    python3 tools/deep_research/cli.py resume --episode ep.json
    python3 tools/deep_research/cli.py replay --episode ep.json
    python3 tools/deep_research/cli.py claim-add --episode ep.json --text "..." --ceiling TENTATIVE
    python3 tools/deep_research/cli.py obligation-add --episode ep.json --claim claim-1 --class PRIMARY_SOURCE
    python3 tools/deep_research/cli.py obligation-set --episode ep.json --id obl-001 --status SATISFIED
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from research_os import kernel as K
from deep_research import records as R
from deep_research import queue_runtime as Q
from deep_research import episode_loop as E
from deep_research.episode_loop import _safe_pack, DEFAULT_STRATEGY_PACK
from deep_research import adapters as A


# ---------------------------------------------------------------------------
# Episode-facing pure operations
# ---------------------------------------------------------------------------
def inspect_episode(ep: dict) -> dict:
    return {
        "episode_id": ep.get("episode_id"),
        "state": ep.get("state"),
        "is_terminal": K.is_terminal(ep),
        "event_count": K.event_count(ep),
        "obligations": len(ep.get("evidence_obligations", [])),
        "open_obligations": [o for o in ep.get("evidence_obligations", [])
                             if o.get("status") != "SATISFIED"],
        "claims": len(ep.get("candidate_claims", [])),
        "observations": len(ep.get("observations", [])),
    }


def pause(ep_path: str | Path, to_state: str = "PAUSED_RESUMABLE") -> dict:
    ep = K.load(ep_path)
    E.pause_episode(ep) if to_state == "PAUSED_RESUMABLE" else K.transition(ep, to_state)
    K.save(ep, ep_path)
    return inspect_episode(ep)


def resume(ep_path: str | Path, to_state: str = "EVIDENCE_GATHERING") -> dict:
    ep = K.load(ep_path)
    E.resume_episode(ep, to_state)
    K.save(ep, ep_path)
    return inspect_episode(ep)


def replay(ep_path: str | Path) -> list[dict]:
    ep = K.load(ep_path)
    return E.replay_events(ep)


def claim_add(ep_path: str | Path, text: str, ceiling: str,
              claim_id: Optional[str] = None) -> dict:
    ep = K.load(ep_path)
    claim = E.add_claim(ep, text, ceiling, claim_id)
    K.save(ep, ep_path)
    return claim


def obligation_add(ep_path: str | Path, claim_id: str, obligation_class: str,
                  severity: str = "MEDIUM", status: str = "OPEN") -> dict:
    ep = K.load(ep_path)
    obl = E.add_obligation(ep, claim_id, obligation_class, severity, status)
    K.save(ep, ep_path)
    return obl


def obligation_set(ep_path: str | Path, obligation_id: str, status: str) -> bool:
    ep = K.load(ep_path)
    ok = E.set_obligation_status(ep, obligation_id, status)
    if ok:
        K.save(ep, ep_path)
    return ok


# ---------------------------------------------------------------------------
# Queue-facing orchestration
# ---------------------------------------------------------------------------
def queue_step(queue: Q.SerialQueue, controller: E.EpisodeController,
               plan_provider: Optional[Callable[[dict], list[dict]]] = None,
               now_iso: Optional[str] = None) -> Optional[dict]:
    """Select the next item, run one bounded episode for it, and ingest the
    result back into the queue. Returns the completed episode result, or None if
    the queue has nothing selectable. The executor never approves its own
    stop/report — finalization is driven by the controller's sufficiency eval."""
    now_iso = now_iso or "2026-01-01T00:00:00Z"
    item = queue.select_next(now_iso=now_iso)
    if item is None:
        return None
    ep = K.new_episode(
        episode_id=item.get("episode_id") or f"ep-{item['queue_item_id']}",
        question_version="v1",
        research_type="deep_research",
        strategy_pack=_safe_pack((item.get("topic_candidate") or {}).get("proposed_strategy_pack", "")),
    )
    brief = R.make_brief(
        question=(item.get("topic_candidate") or {}).get("proposed_question", "unfrozen"),
        scope={"population": "unspecified", "object": "unspecified",
               "timeframe": "unspecified", "outcomes": []},
        strategy_pack=_safe_pack((item.get("topic_candidate") or {}).get("proposed_strategy_pack", "")),
    )
    controller.freeze_scope(ep, brief)
    plan = (plan_provider(item) if plan_provider else []) or []
    controller.run_plan(ep, plan)
    result = R.make_episode_result(
        episode_id=ep["episode_id"],
        final_state=ep["state"],
        claims=ep.get("candidate_claims", []),
        obligations_status={"open": len([o for o in ep.get("evidence_obligations", [])
                                         if o.get("status") != "SATISFIED"])},
        machine_trace_ref=f"trace-{ep['episode_id']}",
    )
    item["episode_id"] = ep["episode_id"]
    queue.ingest_result(result, now_iso=now_iso)
    return result


def run_until_stop(queue: Q.SerialQueue, controller: E.EpisodeController,
                   plan_provider: Optional[Callable[[dict], list[dict]]] = None,
                   now_iso: Optional[str] = None) -> tuple[int, Optional[str]]:
    """Run queue steps until the campaign should stop. Returns (steps_run, reason)."""
    now_iso = now_iso or "2026-01-01T00:00:00Z"
    steps = 0
    while True:
        stopped, reason = queue.should_stop(now_iso=now_iso)
        if stopped:
            return steps, reason
        res = queue_step(queue, controller, plan_provider, now_iso=now_iso)
        if res is None:
            return steps, "NO_SELECTABLE_ITEM"
        steps += 1


# ---------------------------------------------------------------------------
# argparse entry point
# ---------------------------------------------------------------------------
def _load_ep(path: str) -> dict:
    return K.load(path)


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="deep-research-cli", description="Deep Research capability CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("inspect", help="inspect an episode")
    sp.add_argument("--episode", required=True)

    sp = sub.add_parser("pause", help="pause an episode")
    sp.add_argument("--episode", required=True)

    sp = sub.add_parser("resume", help="resume a paused episode")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--to-state", default="EVIDENCE_GATHERING")

    sp = sub.add_parser("replay", help="replay an episode event log")
    sp.add_argument("--episode", required=True)

    sp = sub.add_parser("claim-add", help="add a candidate claim (PR #190 gap)")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--text", required=True)
    sp.add_argument("--ceiling", required=True)
    sp.add_argument("--id", default=None)

    sp = sub.add_parser("obligation-add", help="add an evidence obligation (PR #190 gap)")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--claim", required=True)
    sp.add_argument("--class", dest="obligation_class", required=True)
    sp.add_argument("--severity", default="MEDIUM")
    sp.add_argument("--status", default="OPEN")

    sp = sub.add_parser("obligation-set", help="set an obligation status (PR #190 gap)")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--id", required=True)
    sp.add_argument("--status", required=True)

    sp = sub.add_parser("episode", help="run one episode from a question")
    sp.add_argument("--question", required=True)
    sp.add_argument("--strategy-pack", default="default")
    sp.add_argument("--plan", default=None, help="path to a JSON plan file")
    sp.add_argument("--out", default=None, help="episode output JSON path")

    sp = sub.add_parser("queue-step", help="run one queue step")
    sp.add_argument("--queue", required=True, help="path to a SerialQueue JSON")
    sp.add_argument("--now", default="2026-01-01T00:00:00Z")

    sp = sub.add_parser("run-until-stop", help="run queue until campaign stop")
    sp.add_argument("--queue", required=True)
    sp.add_argument("--now", default="2026-01-01T00:00:00Z")

    args = p.parse_args(argv)

    if args.cmd == "inspect":
        print(json.dumps(inspect_episode(_load_ep(args.episode)), indent=2))
    elif args.cmd == "pause":
        print(json.dumps(pause(args.episode), indent=2))
    elif args.cmd == "resume":
        print(json.dumps(resume(args.episode, args.to_state), indent=2))
    elif args.cmd == "replay":
        print(json.dumps(replay(args.episode), indent=2))
    elif args.cmd == "claim-add":
        print(json.dumps(claim_add(args.episode, args.text, args.ceiling, args.id), indent=2))
    elif args.cmd == "obligation-add":
        print(json.dumps(obligation_add(args.episode, args.claim, args.obligation_class,
                                        args.severity, args.status), indent=2))
    elif args.cmd == "obligation-set":
        print(json.dumps({"ok": obligation_set(args.episode, args.id, args.status)}, indent=2))
    elif args.cmd == "episode":
        ctrl = E.EpisodeController(adapters=A.build_default_adapters())
        ep = K.new_episode("ep-cli", "v1", "deep_research", _safe_pack(args.strategy_pack))
        ctrl.freeze_scope(ep, R.make_brief(question=args.question,
                                            strategy_pack=_safe_pack(args.strategy_pack)))
        plan = json.loads(Path(args.plan).read_text()) if args.plan else []
        ctrl.run_plan(ep, plan)
        out = args.out or f"data/operations/iterations/115/candidate/workbuddy-takeover/ep-{ep['episode_id']}.json"
        K.save(ep, out)
        print(json.dumps(inspect_episode(ep), indent=2))
    elif args.cmd == "queue-step":
        q = Q.SerialQueue()
        # queue JSON persisted as {"campaign":..., "items":..., "stats":...}
        blob = json.loads(Path(args.queue).read_text())
        q.campaign = blob.get("campaign", q.campaign)
        q.items = blob.get("items", [])
        q.stats = blob.get("stats", q.stats)
        ctrl = E.EpisodeController(adapters=A.build_default_adapters())
        res = queue_step(q, ctrl, now_iso=args.now)
        Path(args.queue).write_text(json.dumps(
            {"campaign": q.campaign, "items": q.items, "stats": q.stats}, indent=2))
        print(json.dumps(res, indent=2) if res else "NO_SELECTABLE_ITEM")
    elif args.cmd == "run-until-stop":
        q = Q.SerialQueue()
        blob = json.loads(Path(args.queue).read_text())
        q.campaign = blob.get("campaign", q.campaign)
        q.items = blob.get("items", [])
        q.stats = blob.get("stats", q.stats)
        ctrl = E.EpisodeController(adapters=A.build_default_adapters())
        steps, reason = run_until_stop(q, ctrl, now_iso=args.now)
        Path(args.queue).write_text(json.dumps(
            {"campaign": q.campaign, "items": q.items, "stats": q.stats}, indent=2))
        print(json.dumps({"steps": steps, "stop_reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
