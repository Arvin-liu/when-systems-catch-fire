"""Bounded process-group and descendant cleanup for one Codex app-server turn."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Iterable


def _process_table() -> dict[int, tuple[int, int, str]]:
    result = subprocess.run(
        ["/bin/ps", "-axo", "pid=,ppid=,pgid=,lstart="],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    )
    table: dict[int, tuple[int, int, str]] = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 3)
        if len(fields) != 4:
            continue
        try:
            pid, ppid, pgid = (int(field) for field in fields[:3])
        except ValueError:
            continue
        table[pid] = (ppid, pgid, fields[3])
    return table


def _descendants(root_pid: int, table: dict[int, tuple[int, int, str]]) -> set[int]:
    children: dict[int, list[int]] = {}
    for pid, (ppid, _pgid, _start_time) in table.items():
        children.setdefault(ppid, []).append(pid)
    result: set[int] = set()
    pending = list(children.get(root_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in result:
            continue
        result.add(pid)
        pending.extend(children.get(pid, ()))
    return result


def _signal_pid(pid: int, sig: int) -> None:
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        pass


@dataclass(frozen=True)
class SupervisionResult:
    pid: int
    process_group_id: int
    exit_code: int | None
    timed_out: bool
    observed_descendant_pids: tuple[int, ...]
    term_sent: bool
    kill_sent: bool
    surviving_process_group_pids: tuple[int, ...]
    surviving_observed_pids: tuple[int, ...]
    cleanup_proven: bool


class ProcessSupervisor:
    def __init__(self, proc: subprocess.Popen, *, poll_seconds: float = 0.1):
        if proc.pid <= 0 or proc.stdin is None or proc.stdout is None:
            raise ValueError("supervised process needs a PID and stdio pipes")
        self.proc = proc
        self.pgid = os.getpgid(proc.pid)
        self.poll_seconds = poll_seconds
        table = _process_table()
        root = table.get(proc.pid)
        if root is None:
            raise RuntimeError("supervised process disappeared before identity capture")
        self.root_start_time = root[2]
        self.observed: dict[int, str] = {}

    def observe(self) -> dict[int, tuple[int, int, str]]:
        table = _process_table()
        for pid in _descendants(self.proc.pid, table):
            self.observed[pid] = table[pid][2]
        for pid, (_ppid, pgid, start_time) in table.items():
            if pgid == self.pgid and pid != self.proc.pid:
                self.observed[pid] = start_time
        return table

    def wait_for_exit(self, timeout_seconds: float) -> SupervisionResult:
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        while self.proc.poll() is None:
            self.observe()
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(self.poll_seconds)
        if not timed_out:
            self.observe()
        return self._cleanup(timed_out=timed_out)

    def terminate(self) -> SupervisionResult:
        self.observe()
        return self._cleanup(timed_out=False, force=True)

    def _cleanup(self, *, timed_out: bool, force: bool = False) -> SupervisionResult:
        term_sent = False
        kill_sent = False
        table = self.observe()
        group_members = {
            pid
            for pid, (_ppid, pgid, start_time) in table.items()
            if pgid == self.pgid
            and (
                pid == self.proc.pid and start_time == self.root_start_time
                or self.observed.get(pid) == start_time
            )
        }
        live_observed = {
            pid
            for pid, start_time in self.observed.items()
            if pid in table and table[pid][2] == start_time and pid != os.getpid()
        }
        targets = group_members | live_observed
        if force or timed_out or targets:
            term_sent = True
            try:
                os.killpg(self.pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
            for pid in targets:
                _signal_pid(pid, signal.SIGTERM)
            grace_deadline = time.monotonic() + 1.0
            while time.monotonic() < grace_deadline:
                table = self.observe()
                remaining = {
                    pid
                    for pid, (_ppid, pgid, start_time) in table.items()
                    if pgid == self.pgid
                    and (
                        pid == self.proc.pid and start_time == self.root_start_time
                        or self.observed.get(pid) == start_time
                    )
                } | {
                    pid
                    for pid, start_time in self.observed.items()
                    if pid in table and table[pid][2] == start_time and pid != os.getpid()
                }
                if not remaining:
                    break
                time.sleep(self.poll_seconds)
            table = self.observe()
            remaining = {
                pid
                for pid, (_ppid, pgid, start_time) in table.items()
                if pgid == self.pgid
                and (
                    pid == self.proc.pid and start_time == self.root_start_time
                    or self.observed.get(pid) == start_time
                )
            } | {
                pid
                for pid, start_time in self.observed.items()
                if pid in table and table[pid][2] == start_time and pid != os.getpid()
            }
            if remaining:
                kill_sent = True
                try:
                    os.killpg(self.pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    pass
                for pid in remaining:
                    _signal_pid(pid, signal.SIGKILL)
                kill_deadline = time.monotonic() + 2.0
                while time.monotonic() < kill_deadline:
                    table = self.observe()
                    remaining = {
                        pid
                        for pid, (_ppid, pgid, start_time) in table.items()
                        if pgid == self.pgid
                        and (
                            pid == self.proc.pid and start_time == self.root_start_time
                            or self.observed.get(pid) == start_time
                        )
                    } | {
                        pid
                        for pid, start_time in self.observed.items()
                        if pid in table and table[pid][2] == start_time and pid != os.getpid()
                    }
                    if not remaining:
                        break
                    time.sleep(self.poll_seconds)

        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(self.pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.proc.wait(timeout=2)

        final_table = self.observe()
        group_survivors = tuple(
            sorted(
                pid
                for pid, (_ppid, pgid, start_time) in final_table.items()
                if pgid == self.pgid
                and (
                    pid == self.proc.pid and start_time == self.root_start_time
                    or self.observed.get(pid) == start_time
                )
            )
        )
        observed_survivors = tuple(
            sorted(
                pid
                for pid, start_time in self.observed.items()
                if pid in final_table
                and final_table[pid][2] == start_time
                and pid != os.getpid()
            )
        )
        return SupervisionResult(
            pid=self.proc.pid,
            process_group_id=self.pgid,
            exit_code=self.proc.returncode,
            timed_out=timed_out,
            observed_descendant_pids=tuple(sorted(set(self.observed) - {self.proc.pid})),
            term_sent=term_sent,
            kill_sent=kill_sent,
            surviving_process_group_pids=group_survivors,
            surviving_observed_pids=observed_survivors,
            cleanup_proven=not group_survivors and not observed_survivors,
        )


def run_fixture(command: Iterable[str], timeout_seconds: float) -> SupervisionResult:
    proc = subprocess.Popen(
        list(command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    supervisor = ProcessSupervisor(proc)
    result = supervisor.wait_for_exit(timeout_seconds)
    proc.stdout.close()
    return result
