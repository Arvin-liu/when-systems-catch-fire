"""Command line entrypoint for local Agent Runtime R1 runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .actions import CrashInjected
from .control import ControlConflict
from .r1_runtime import AgentRuntimeR1, R1RunSpec, RuntimeR1Error


def _emit(value: object, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return
    if isinstance(value, dict) and "terminal" in value:
        terminal = value.get("terminal") or {}
        print(f"run_id={value.get('run_id')} phase={value.get('phase')} state={terminal.get('state', 'RUNNING')} next_action={value.get('next_action_index')}")
        if value.get("pending_approval"):
            print(f"approval_pending={value['pending_approval'].get('request_id')}")
        return
    if isinstance(value, list):
        for item in value:
            print(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return
    print(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("--spec", required=True, type=Path)
    run.add_argument("--run-dir", required=True, type=Path)
    run.add_argument("--json", action="store_true", dest="json_mode")

    for name in ("status", "pending-approval", "resume", "trace"):
        command = sub.add_parser(name)
        command.add_argument("--run-dir", required=True, type=Path)
        command.add_argument("--json", action="store_true", dest="json_mode")

    approve = sub.add_parser("approve")
    approve.add_argument("--run-dir", required=True, type=Path)
    approve.add_argument("--request-id", required=True)
    approve.add_argument("--decision", required=True, choices=("allow", "deny"))
    approve.add_argument("--authority", required=True)
    approve.add_argument("--authority-type", default="human", choices=("human", "operator", "synthetic_pilot", "cli"))
    approve.add_argument("--reason", default="explicit typed approval decision")
    approve.add_argument("--json", action="store_true", dest="json_mode")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            spec = R1RunSpec.from_dict(json.loads(args.spec.read_text(encoding="utf-8")))
            value = AgentRuntimeR1(args.run_dir).start(spec)
        elif args.command == "status":
            value = AgentRuntimeR1(args.run_dir).status()
        elif args.command == "pending-approval":
            value = AgentRuntimeR1(args.run_dir).pending_approval()
        elif args.command == "approve":
            value = AgentRuntimeR1(args.run_dir).approve(
                args.request_id, args.decision, authority_id=args.authority,
                authority_type=args.authority_type, reason_summary=args.reason,
            )
        elif args.command == "resume":
            value = AgentRuntimeR1(args.run_dir).resume(executor_instance_id="cli-resume")
        else:
            value = AgentRuntimeR1(args.run_dir).trace()
        _emit(value, args.json_mode)
        return 0
    except CrashInjected as exc:
        value = {"status": "CRASH_INJECTED", "summary": str(exc)}
        try:
            value["state"] = AgentRuntimeR1(args.run_dir).status()
        except Exception:
            pass
        _emit(value, args.json_mode)
        return 75
    except (RuntimeR1Error, ControlConflict, ValueError, OSError, json.JSONDecodeError) as exc:
        value = {"status": "ERROR", "error_type": type(exc).__name__, "summary": str(exc)}
        _emit(value, args.json_mode)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
