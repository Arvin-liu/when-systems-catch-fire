#!/usr/bin/env python3
"""Watchdog for dual-channel bootstrap runs."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = REPO_ROOT / "data/runs/dual-channel-full-bootstrap"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_log(run_dir: Path, message: str) -> None:
    path = run_dir / "logs/watchdog.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{utc_now()} {message}\n")


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def check_run(run_id: str, stale_seconds: int, restart: bool) -> dict[str, Any]:
    run_dir = RUN_ROOT / run_id
    state = read_json(run_dir / "state.json", {})
    heartbeat = read_json(run_dir / "heartbeat.json", {})
    lock_present = (run_dir / "lock").exists()
    pid = heartbeat.get("pid")
    alive = pid_alive(pid)
    heartbeat_ts = parse_time(heartbeat.get("heartbeat_at"))
    now = time.time()
    stale = heartbeat_ts is None or now - heartbeat_ts > stale_seconds
    status = "ok"
    actions: list[str] = []

    if state.get("phase") == "complete" or heartbeat.get("status") == "complete":
        status = "complete"
    elif not lock_present:
        status = "missing_lock"
    elif not alive:
        status = "worker_not_alive"
    elif stale:
        status = "stale_heartbeat"

    if status in {"worker_not_alive", "stale_heartbeat"} and restart:
        if alive and pid:
            os.kill(pid, signal.SIGTERM)
            actions.append(f"terminated stale worker pid={pid}")
        proc = subprocess.Popen(
            ["python3", "scripts/run_dual_channel_full_bootstrap.py", "--run-id", run_id, "--resume"],
            cwd=REPO_ROOT,
            stdout=(run_dir / "logs/worker-restarted.log").open("a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
        actions.append(f"restarted worker pid={proc.pid}")

    payload = {
        "run_id": run_id,
        "checked_at": utc_now(),
        "status": status,
        "lock_present": lock_present,
        "worker_pid": pid,
        "worker_alive": alive,
        "heartbeat_stale": stale,
        "heartbeat": heartbeat,
        "state": state,
        "actions": actions,
    }
    write_json(run_dir / "watchdog-status.json", payload)
    append_log(run_dir, f"status={status} alive={alive} stale={stale} actions={actions}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or watch a dual-channel bootstrap run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stale-seconds", type=int, default=300)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()

    if not args.watch:
        print(json.dumps(check_run(args.run_id, args.stale_seconds, args.restart), ensure_ascii=False, indent=2))
        return 0

    while True:
        payload = check_run(args.run_id, args.stale_seconds, args.restart)
        if payload["status"] == "complete":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
