"""Research OS CLI (Checkpoint B).

Inspectable control loop over an episode JSON file. Commands:
  init | observe | diagnose | plan | dispatch-spec | record-result |
  review | pause | resume | stop | reopen | replay

All commits go through the deterministic core; an LLM is never required. The CLI
is the human/agent-facing surface of the observe -> diagnose -> choose -> dispatch
-> inspect -> update -> stop/escalate loop.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import diagnosis as dx
from . import executor_contract as ec
from . import gates
from . import kernel
from . import obligation_graph as og
from . import scheduler


def _load_ep(path: str) -> dict:
    return kernel.load(path)


def _save_ep(path: str, ep: dict) -> None:
    kernel.save(ep, path)


def _emit(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_init(args) -> int:
    ep = kernel.new_episode(args.id, args.question, args.type, args.pack, budgets=args.budgets)
    if args.freeze:
        kernel.transition(ep, "QUESTION_FROZEN", actor="cli")
    _save_ep(args.episode, ep)
    _emit({"created": args.episode, "episode_id": args.id, "state": ep["state"]})
    return 0


def cmd_observe(args) -> int:
    ep = _load_ep(args.episode)
    obs = json.loads(args.observation) if args.observation else json.load(open(args.observation_file))
    kernel.observe(ep, obs, actor="cli")
    _save_ep(args.episode, ep)
    _emit({"observations": len(ep["observations"]), "last_event": ep["event_log"][-1]})
    return 0


def cmd_diagnose(args) -> int:
    ep = _load_ep(args.episode)
    result = dx.diagnose(ep)
    ep["current_diagnosis"] = result
    _save_ep(args.episode, ep)
    _emit(result)
    return 0


def cmd_plan(args) -> int:
    ep = _load_ep(args.episode)
    if ep.get("current_diagnosis") is None or args.rediagnose:
        ep["current_diagnosis"] = dx.diagnose(ep)
    selection = scheduler.plan(ep, ep["current_diagnosis"])
    kernel.record_action_selection(ep, selection, actor="cli")
    _save_ep(args.episode, ep)
    _emit(selection)
    return 0


def cmd_dispatch_spec(args) -> int:
    ep = _load_ep(args.episode)
    action = args.action or (ep.get("selected_action") or {}).get("selected_action")
    if not action:
        print("no action selected; run plan first or pass --action", file=sys.stderr)
        return 2
    spec = ec.build_dispatch_spec(ep, action, actor="cli")
    if args.out:
        Path(args.out).write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    _emit(spec)
    return 0


def cmd_record_result(args) -> int:
    ep = _load_ep(args.episode)
    ret = json.loads(args.result) if args.result else json.load(open(args.result_file))
    ec.validate_return(ret)  # raises on self-approval / missing fields
    scheduler.mark_action_taken(ep, args.action)
    kernel.observe(ep, ret, actor="cli")
    # record any completed calculations referenced by the executor
    for calc in ret.get("calculations_completed", []) or []:
        if calc not in ep.get("calculations_completed", []):
            ep.setdefault("calculations_completed", []).append(calc)
    ep["current_diagnosis"] = dx.diagnose(ep)
    _save_ep(args.episode, ep)
    _emit({"validated": True, "diagnostic_findings": len(ep["current_diagnosis"]["findings"])})
    return 0


def cmd_review(args) -> int:
    ep = _load_ep(args.episode)
    diag = dx.diagnose(ep)
    result = gates.evaluate_gates(ep, diag)
    result["recommendation"] = gates.recommend(ep, diag, result)
    _emit(result)
    return 0


def cmd_pause(args) -> int:
    ep = _load_ep(args.episode)
    ep["paused_from"] = ep["state"]
    kernel.transition(ep, "PAUSED_RESUMABLE", actor="cli")
    _save_ep(args.episode, ep)
    _emit({"state": ep["state"], "paused_from": ep["paused_from"]})
    return 0


def cmd_resume(args) -> int:
    ep = _load_ep(args.episode)
    if ep["state"] != "PAUSED_RESUMABLE":
        print("episode not paused", file=sys.stderr)
        return 2
    target = ep.get("paused_from") or "EVIDENCE_GATHERING"
    # The legal resume targets are the successors of PAUSED_RESUMABLE, not the
    # successors of the target itself (previous code compared target against
    # its own successor list, so resume could never return to paused_from).
    allowed = kernel.ALLOWED_NEXT.get("PAUSED_RESUMABLE", [])
    if target not in allowed:
        target = "EVIDENCE_GATHERING"
    kernel.transition(ep, target, actor="cli")
    ep.pop("paused_from", None)
    _save_ep(args.episode, ep)
    _emit({"state": ep["state"]})
    return 0


def cmd_stop(args) -> int:
    ep = _load_ep(args.episode)
    ep.setdefault("stop_conditions", {})["reason"] = args.reason
    kernel.transition(ep, "INSUFFICIENT_EVIDENCE_COMPLETE", actor="cli")
    _save_ep(args.episode, ep)
    _emit({"state": ep["state"], "reason": args.reason, "note": "honest-null / insufficient-evidence stop; not a positive finding"})
    return 0


def cmd_reopen(args) -> int:
    ep = _load_ep(args.episode)
    kernel.transition(ep, "REOPENED", actor="cli")
    kernel.transition(ep, "EVIDENCE_GATHERING", actor="cli")
    _save_ep(args.episode, ep)
    _emit({"state": ep["state"]})
    return 0


def cmd_replay(args) -> int:
    """Replay a structured packet (episode JSON) through diagnose + plan."""
    ep = _load_ep(args.episode)
    diag = dx.diagnose(ep)
    selection = scheduler.plan(ep, diag)
    _emit({
        "episode_id": ep.get("episode_id"),
        "strategy_pack": ep.get("strategy_pack"),
        "state": ep.get("state"),
        "diagnosis": diag,
        "selected_action": selection["selected_action"],
        "ranked_candidates": selection["ranked_candidates"],
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="research-os", description="Pointfire Research Executive OS CLI (Task 115 Draft candidate)")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="create a new episode")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--id", required=True)
    sp.add_argument("--question", required=True)
    sp.add_argument("--type", required=True)
    sp.add_argument("--pack", required=True)
    sp.add_argument("--budgets", default="{}")
    sp.add_argument("--freeze", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("observe", help="record an executor observation")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--observation", default=None)
    sp.add_argument("--observation-file", default=None)
    sp.set_defaults(func=cmd_observe)

    sp = sub.add_parser("diagnose", help="run deterministic diagnosis")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_diagnose)

    sp = sub.add_parser("plan", help="select next action (inspectable)")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--rediagnose", action="store_true")
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("dispatch-spec", help="build executor dispatch spec")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--action", default=None)
    sp.add_argument("--out", default=None)
    sp.set_defaults(func=cmd_dispatch_spec)

    sp = sub.add_parser("record-result", help="validate + record executor return")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--action", required=True)
    sp.add_argument("--result", default=None)
    sp.add_argument("--result-file", default=None)
    sp.set_defaults(func=cmd_record_result)

    sp = sub.add_parser("review", help="run review gates")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("pause", help="pause with resumable checkpoint")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_pause)

    sp = sub.add_parser("resume", help="resume from pause")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_resume)

    sp = sub.add_parser("stop", help="stop with insufficient evidence")
    sp.add_argument("--episode", required=True)
    sp.add_argument("--reason", required=True)
    sp.set_defaults(func=cmd_stop)

    sp = sub.add_parser("reopen", help="reopen a closed/paused episode")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_reopen)

    sp = sub.add_parser("replay", help="replay a packet through diagnose+plan")
    sp.add_argument("--episode", required=True)
    sp.set_defaults(func=cmd_replay)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
