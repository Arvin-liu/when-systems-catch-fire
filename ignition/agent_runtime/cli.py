"""Command line entrypoint for local Agent Runtime R1 runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .actions import CrashInjected
from .control import ControlConflict
from .memory import MEMORY_TYPES, MemoryEntry, MemoryStoreError, OperationalMemoryStore
from .pack_registry import PackRegistry, PackRegistryError
from .r1_runtime import AgentRuntimeR1, R1RunSpec, RuntimeR1Error
from .supervisor import EpisodeSpec, Supervisor, SupervisorError


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

    packs = sub.add_parser("packs")
    pack_sub = packs.add_subparsers(dest="pack_command", required=True)
    for name in ("list", "validate"):
        command = pack_sub.add_parser(name)
        command.add_argument("--packs-root", default=Path("packs"), type=Path)
        command.add_argument("--json", action="store_true", dest="json_mode")
    show = pack_sub.add_parser("show")
    show.add_argument("--pack-id", required=True)
    show.add_argument("--packs-root", default=Path("packs"), type=Path)
    show.add_argument("--json", action="store_true", dest="json_mode")

    memory = sub.add_parser("memory")
    memory_sub = memory.add_subparsers(dest="memory_command", required=True)

    add_memory = memory_sub.add_parser("add")
    add_memory.add_argument("--store", required=True, type=Path)
    add_memory.add_argument("--memory-id", required=True)
    add_memory.add_argument("--memory-type", required=True, choices=sorted(MEMORY_TYPES))
    add_memory.add_argument("--source-run-id", required=True)
    add_memory.add_argument("--summary", required=True)
    add_memory.add_argument("--provenance-ref", action="append", default=[])
    add_memory.add_argument("--owner-feedback-ref", action="append", default=[])
    add_memory.add_argument("--tag", action="append", default=[])
    add_memory.add_argument("--retention-class", default="LONG")
    add_memory.add_argument("--visibility", default="SHARED_OPERATIONAL")
    add_memory.add_argument("--sensitivity-class", default="INTERNAL_OPERATIONAL")
    add_memory.add_argument("--forget-policy", default="MANUAL")
    add_memory.add_argument("--expires-at")
    add_memory.add_argument("--related-ref", action="append", default=[])
    add_memory.add_argument("--json", action="store_true", dest="json_mode")

    query_memory = memory_sub.add_parser("query")
    query_memory.add_argument("--store", required=True, type=Path)
    query_memory.add_argument("--memory-type")
    query_memory.add_argument("--source-run-id")
    query_memory.add_argument("--tag")
    query_memory.add_argument("--visibility")
    query_memory.add_argument("--include-inactive", action="store_true")
    query_memory.add_argument("--json", action="store_true", dest="json_mode")

    show_memory = memory_sub.add_parser("show")
    show_memory.add_argument("--store", required=True, type=Path)
    show_memory.add_argument("--memory-id", required=True)
    show_memory.add_argument("--json", action="store_true", dest="json_mode")

    forget_memory = memory_sub.add_parser("forget")
    forget_memory.add_argument("--store", required=True, type=Path)
    forget_memory.add_argument("--memory-id", required=True)
    forget_memory.add_argument("--reason", default="explicit forget request")
    forget_memory.add_argument("--json", action="store_true", dest="json_mode")

    supersede_memory = memory_sub.add_parser("supersede")
    supersede_memory.add_argument("--store", required=True, type=Path)
    supersede_memory.add_argument("--memory-id", required=True)
    supersede_memory.add_argument("--replacement-id", required=True)
    supersede_memory.add_argument("--summary", required=True)
    supersede_memory.add_argument("--json", action="store_true", dest="json_mode")

    export_memory = memory_sub.add_parser("export")
    export_memory.add_argument("--store", required=True, type=Path)
    export_memory.add_argument("--max-entries", type=int, default=16)
    export_memory.add_argument("--max-chars", type=int, default=4000)
    export_memory.add_argument("--source-run-id")
    export_memory.add_argument("--tag", action="append", default=[])
    export_memory.add_argument("--json", action="store_true", dest="json_mode")

    audit_memory = memory_sub.add_parser("audit")
    audit_memory.add_argument("--store", required=True, type=Path)
    audit_memory.add_argument("--json", action="store_true", dest="json_mode")

    episode = sub.add_parser("episode")
    episode_sub = episode.add_subparsers(dest="episode_command", required=True)
    start_episode = episode_sub.add_parser("start")
    start_episode.add_argument("--spec", required=True, type=Path)
    start_episode.add_argument("--run-dir", required=True, type=Path)
    start_episode.add_argument("--json", action="store_true", dest="json_mode")
    for name in ("status", "resume", "trace", "pending-approval"):
        command = episode_sub.add_parser(name)
        command.add_argument("--run-dir", required=True, type=Path)
        command.add_argument("--json", action="store_true", dest="json_mode")
    approve_episode = episode_sub.add_parser("approve")
    approve_episode.add_argument("--run-dir", required=True, type=Path)
    approve_episode.add_argument("--run-id", required=True)
    approve_episode.add_argument("--request-id", required=True)
    approve_episode.add_argument("--decision", required=True, choices=("allow", "deny"))
    approve_episode.add_argument("--authority", required=True)
    approve_episode.add_argument("--authority-type", default="human", choices=("human", "operator", "synthetic_pilot", "cli"))
    approve_episode.add_argument("--reason", default="explicit typed episode approval decision")
    approve_episode.add_argument("--json", action="store_true", dest="json_mode")
    handoff_episode = episode_sub.add_parser("handoff")
    handoff_episode.add_argument("--run-dir", required=True, type=Path)
    handoff_episode.add_argument("--run-id", required=True)
    handoff_episode.add_argument("--executor-instance-id", required=True)
    handoff_episode.add_argument("--executor-class-id")
    handoff_episode.add_argument("--json", action="store_true", dest="json_mode")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "packs":
            registry = PackRegistry.discover(args.packs_root)
            if args.pack_command == "list":
                value = [registry.get(pack_id).to_dict() for pack_id in registry.pack_ids]
                status = 0
            elif args.pack_command == "show":
                manifest = registry.get(args.pack_id)
                value = {"status": "PASS", "pack": manifest.to_dict(), "routes": [route.to_dict() for route in registry.routes() if route.pack_id == args.pack_id]}
                status = 0
            else:
                value = registry.validate()
                status = 0 if value["status"] == "PASS" else 2
            _emit(value, args.json_mode)
            return status
        if args.command == "memory":
            store = OperationalMemoryStore(args.store)
            if args.memory_command == "add":
                value = store.append(MemoryEntry.create(
                    memory_id=args.memory_id,
                    memory_type=args.memory_type,
                    source_run_id=args.source_run_id,
                    summary=args.summary,
                    provenance_refs=args.provenance_ref,
                    owner_feedback_refs=args.owner_feedback_ref,
                    tags=args.tag,
                    retention_class=args.retention_class,
                    visibility=args.visibility,
                    sensitivity_class=args.sensitivity_class,
                    forget_policy=args.forget_policy,
                    expires_at=args.expires_at,
                    related_refs=args.related_ref,
                )).to_dict()
            elif args.memory_command == "query":
                value = [entry.to_dict() for entry in store.query(
                    memory_type=args.memory_type,
                    source_run_id=args.source_run_id,
                    tag=args.tag,
                    visibility=args.visibility,
                    active_only=not args.include_inactive,
                )]
            elif args.memory_command == "show":
                value = store.show(args.memory_id).to_dict()
            elif args.memory_command == "forget":
                value = store.forget(args.memory_id, reason=args.reason)
            elif args.memory_command == "supersede":
                old = store.show(args.memory_id)
                replacement = MemoryEntry.create(
                    memory_id=args.replacement_id,
                    memory_type=old.memory_type,
                    source_run_id=old.source_run_id,
                    summary=args.summary,
                    provenance_refs=old.provenance_refs,
                    owner_feedback_refs=old.owner_feedback_refs,
                    tags=old.tags,
                    retention_class=old.retention_class,
                    visibility=old.visibility,
                    sensitivity_class=old.sensitivity_class,
                    forget_policy=old.forget_policy,
                    expires_at=old.expires_at,
                    supersedes=old.memory_id,
                    related_refs=old.related_refs,
                )
                value = store.supersede(old.memory_id, replacement).to_dict()
            elif args.memory_command == "export":
                value = store.export_capsule(max_entries=args.max_entries, max_chars=args.max_chars, source_run_id=args.source_run_id, tags=args.tag)
            else:
                value = store.audit()
            _emit(value, args.json_mode)
            return 0
        if args.command == "episode":
            supervisor = Supervisor(args.run_dir)
            if args.episode_command == "start":
                value = supervisor.start(EpisodeSpec.from_dict(json.loads(args.spec.read_text(encoding="utf-8"))))
            elif args.episode_command == "status":
                value = supervisor.status()
            elif args.episode_command == "resume":
                value = supervisor.resume()
            elif args.episode_command == "trace":
                value = supervisor.trace()
            elif args.episode_command == "pending-approval":
                value = supervisor.pending_approvals()
            elif args.episode_command == "approve":
                value = supervisor.approve(
                    args.run_id,
                    args.request_id,
                    args.decision,
                    authority_id=args.authority,
                    authority_type=args.authority_type,
                    reason_summary=args.reason,
                )
            else:
                value = supervisor.handoff(
                    args.run_id,
                    args.executor_instance_id,
                    executor_class_id=args.executor_class_id,
                )
            _emit(value, args.json_mode)
            return 0
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
    except (RuntimeR1Error, SupervisorError, ControlConflict, PackRegistryError, MemoryStoreError, ValueError, OSError, json.JSONDecodeError) as exc:
        value = {"status": "ERROR", "error_type": type(exc).__name__, "summary": str(exc)}
        _emit(value, args.json_mode)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
