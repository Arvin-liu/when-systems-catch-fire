#!/usr/bin/env python3
"""Supervisor for dual-channel full bootstrap verification."""

from __future__ import annotations

import argparse
import json
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


def run_git(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=check)


def append_log(run_dir: Path, message: str) -> None:
    path = run_dir / "logs/supervisor.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{utc_now()} {message}\n")


def status_payload(run_id: str) -> dict[str, Any]:
    run_dir = RUN_ROOT / run_id
    return {
        "run_id": run_id,
        "state": read_json(run_dir / "state.json", {}),
        "progress": read_json(run_dir / "progress.json", {}),
        "heartbeat": read_json(run_dir / "heartbeat.json", {}),
        "watchdog": read_json(run_dir / "watchdog-status.json", {}),
        "final_report": read_json(run_dir / "reports/final-report.json", {}),
    }


def ensure_branch(run_id: str) -> str:
    target = f"run/dual-channel-full-bootstrap-{run_id}"
    current = run_git(["branch", "--show-current"]).stdout.strip()
    if current == target:
        return target
    existing = run_git(["branch", "--list", target]).stdout.strip()
    if existing:
        run_git(["checkout", target], check=True)
    else:
        run_git(["checkout", "-b", target], check=True)
    return target


def changed_paths() -> list[str]:
    proc = run_git(["status", "--short"])
    paths = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:])
    return paths


def checkpoint_commit(run_id: str, message: str) -> str | None:
    paths = changed_paths()
    if not paths:
        return None
    add_paths = [
        "scripts",
        "data/rebuild",
        "data/runs",
        "data/sync",
        "data/functions/unified-functions.json",
        "data/functions/unified-functions.jsonl",
        "data/functions/unified-functions.min.json",
        "data/cases/unified-cases.json",
        "data/cases/unified-cases.jsonl",
        "data/cases/unified-cases.min.json",
    ]
    run_git(["add", *add_paths], check=True)
    commit = run_git(["commit", "-m", message])
    if commit.returncode != 0:
        return None
    return run_git(["rev-parse", "--short", "HEAD"], check=True).stdout.strip()


def push_current_branch(branch: str) -> None:
    run_git(["push", "-u", "origin", branch], check=True)


def run_checks() -> list[dict[str, Any]]:
    commands = [
        ["python3", "scripts/validate_ignition_repository.py", "--quick"],
        ["python3", "scripts/validate_ignition_repository.py", "--full"],
        [
            "python3",
            "scripts/sync_ignition_knowledge_base.py",
            "--dry-run",
            "--quick",
            "--timeout",
            "60",
            "--no-network",
            "--no-academic-search",
            "--no-raw-scan",
        ],
        ["python3", "scripts/ignition_sync_heartbeat.py", "--once", "--dry-run", "--timeout", "60"],
        ["python3", "scripts/detect_repetitive_text.py", "--check"],
    ]
    results = []
    for cmd in commands:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        results.append(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "ok": proc.returncode == 0,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        )
        if proc.returncode != 0:
            break
    return results


def supervise(run_id: str, max_hours: float, auto_resume: bool) -> int:
    run_dir = RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (RUN_ROOT / "latest-run-id.txt").write_text(run_id + "\n", encoding="utf-8")
    branch = ensure_branch(run_id)
    append_log(run_dir, f"supervisor start branch={branch}")

    deadline = time.time() + max_hours * 3600
    attempts = 0
    returncode = 1
    while time.time() < deadline:
        attempts += 1
        append_log(run_dir, f"worker attempt={attempts}")
        proc = subprocess.run(
            ["python3", "scripts/run_dual_channel_full_bootstrap.py", "--run-id", run_id, "--resume"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        (run_dir / "logs/worker-supervised.stdout.log").write_text(proc.stdout, encoding="utf-8", newline="\n")
        (run_dir / "logs/worker-supervised.stderr.log").write_text(proc.stderr, encoding="utf-8", newline="\n")
        append_log(run_dir, f"worker returncode={proc.returncode}")
        returncode = proc.returncode
        if proc.returncode == 0:
            break
        if not auto_resume:
            break
        time.sleep(5)

    final_report = read_json(run_dir / "reports/final-report.json", {})
    checks = run_checks()
    write_json(run_dir / "reports/final-checks.json", {"generated_at": utc_now(), "checks": checks})
    checks_ok = all(item["ok"] for item in checks)
    commit_sha = checkpoint_commit(run_id, f"Run dual-channel bootstrap verification {run_id}")
    push_current_branch(branch)
    write_json(
        run_dir / "supervisor-result.json",
        {
            "run_id": run_id,
            "branch": branch,
            "worker_returncode": returncode,
            "checks_ok": checks_ok,
            "commit": commit_sha,
            "final_report": final_report,
            "updated_at": utc_now(),
        },
    )
    append_log(run_dir, f"supervisor complete checks_ok={checks_ok} commit={commit_sha}")
    return 0 if returncode == 0 and checks_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Supervise dual-channel bootstrap verification.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-hours", type=float, default=8)
    parser.add_argument("--auto-resume", action="store_true")
    parser.add_argument("--checkpoint-every-item", action="store_true")
    parser.add_argument("--push-progress-every", type=int, default=50)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(status_payload(args.run_id), ensure_ascii=False, indent=2))
        return 0
    return supervise(args.run_id, args.max_hours, args.auto_resume)


if __name__ == "__main__":
    raise SystemExit(main())
