"""Deterministic subprocess probes for executor runtime filesystem separation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping


_STARTUP_PROBE = r'''
import json, os
from pathlib import Path

home = Path(os.environ["HOME"])
tmpdir = Path(os.environ["TMPDIR"])
codex_home = Path(os.environ.get("CODEX_HOME") or (home / ".codex"))
codex_home.mkdir(parents=True, exist_ok=True)
(codex_home / "helper.bin").write_text("helper", encoding="utf-8")
(tmpdir / "runtime.tmp").write_text("runtime", encoding="utf-8")
print(json.dumps({"type": "startup.ready", "structured": True}, sort_keys=True))
'''

_ENV_PROBE = r'''
import json, os
print(json.dumps({"parent_marker_present": "POINTFIRE_PARENT_RUNTIME_MARKER" in os.environ}, sort_keys=True))
'''


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _set_tree_mode(root: Path, *, writable: bool) -> None:
    file_mode = stat.S_IRUSR | stat.S_IWUSR if writable else stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    dir_mode = stat.S_IRWXU if writable else stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        path.chmod(file_mode if path.is_file() else dir_mode)
    root.chmod(dir_mode)


def _cleanup_tree(root: Path) -> bool:
    if root.is_symlink():
        return False
    if not root.exists():
        return True
    _set_tree_mode(root, writable=True)
    shutil.rmtree(root)
    return not root.exists()


@dataclass(frozen=True)
class FilesystemProbeObservation:
    case_id: str
    returncode: int
    structured_result: bool
    helper_write_succeeded: bool
    workspace_unchanged: bool
    scratch_changed: bool
    scratch_cleanup: bool
    failure_stage: str
    expected: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "returncode": self.returncode,
            "structured_result": self.structured_result,
            "helper_write_succeeded": self.helper_write_succeeded,
            "workspace_unchanged": self.workspace_unchanged,
            "scratch_changed": self.scratch_changed,
            "scratch_cleanup": self.scratch_cleanup,
            "failure_stage": self.failure_stage,
            "expected": self.expected,
        }


def run_startup_probe(
    *,
    case_id: str,
    workspace: Path,
    scratch: Path,
    home: Path,
    tmpdir: Path,
    codex_home: Path | None,
    expected: str,
) -> FilesystemProbeObservation:
    """Run a non-model subprocess that mimics Codex's startup file writes."""

    workspace_before = _tree_digest(workspace)
    scratch_before = _tree_digest(scratch)
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home),
        "TMPDIR": str(tmpdir),
    }
    if codex_home is not None:
        env["CODEX_HOME"] = str(codex_home)
    completed = subprocess.run(
        [sys.executable, "-c", _STARTUP_PROBE],
        cwd=str(workspace),
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    structured = False
    if completed.returncode == 0:
        try:
            event = json.loads(completed.stdout.strip())
            structured = event == {"structured": True, "type": "startup.ready"}
        except json.JSONDecodeError:
            structured = False
    workspace_after = _tree_digest(workspace)
    scratch_after = _tree_digest(scratch)
    scratch_changed = scratch_before != scratch_after
    helper_target = codex_home or (home / ".codex")
    helper_write_succeeded = (helper_target / "helper.bin").exists()
    cleanup = _cleanup_tree(scratch)
    if completed.returncode == 0 and structured:
        failure_stage = "NONE"
    elif completed.returncode != 0:
        failure_stage = "PRE_INFERENCE_STARTUP"
    else:
        failure_stage = "RETURNED_MALFORMED"
    return FilesystemProbeObservation(
        case_id=case_id,
        returncode=completed.returncode,
        structured_result=structured,
        helper_write_succeeded=helper_write_succeeded,
        workspace_unchanged=workspace_before == workspace_after,
        scratch_changed=scratch_changed,
        scratch_cleanup=cleanup,
        failure_stage=failure_stage,
        expected=expected,
    )


def run_parent_environment_allowlist_probe(workspace: Path) -> dict[str, bool]:
    """Prove a parent-only marker is absent from the sanitized child env."""

    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(workspace), "TMPDIR": str(workspace)}
    completed = subprocess.run(
        [sys.executable, "-c", _ENV_PROBE],
        cwd=str(workspace),
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if completed.returncode != 0:
        return {"probe_completed": False, "parent_marker_present": True}
    try:
        result = json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        return {"probe_completed": False, "parent_marker_present": True}
    return {
        "probe_completed": True,
        "parent_marker_present": bool(result.get("parent_marker_present", True)),
    }


def run_reproduction_matrix() -> tuple[FilesystemProbeObservation, ...]:
    """Run the complete deterministic startup collision matrix."""

    observations: list[FilesystemProbeObservation] = []
    with tempfile.TemporaryDirectory(prefix="ignition-138-filesystem-harness-") as directory:
        root = Path(directory)
        workspace = root / "workspace"
        scratch = root / "scratch"
        workspace.mkdir()
        scratch.mkdir()
        (workspace / "README.txt").write_text("read-only fixture\n", encoding="utf-8")
        _set_tree_mode(workspace, writable=False)

        def probe(**kwargs: Any) -> FilesystemProbeObservation:
            observation = run_startup_probe(**kwargs)
            scratch.mkdir(exist_ok=True)
            return observation

        observations.append(probe(
            case_id="readonly_home_and_tmpdir",
            workspace=workspace, scratch=scratch, home=workspace, tmpdir=workspace, codex_home=None,
            expected="FAIL_PRE_INFERENCE_PERMISSION_DENIED",
        ))
        observations.append(probe(
            case_id="isolated_writable_runtime_scratch",
            workspace=workspace, scratch=scratch, home=scratch, tmpdir=scratch, codex_home=scratch / ".codex",
            expected="PASS_WORKSPACE_READONLY_SCRATCH_WRITABLE",
        ))
        observations.append(probe(
            case_id="codex_home_workspace_collision",
            workspace=workspace, scratch=scratch, home=scratch, tmpdir=scratch, codex_home=workspace / ".codex",
            expected="FAIL_PRE_INFERENCE_CODEX_HOME_COLLISION",
        ))
        observations.append(probe(
            case_id="tmpdir_workspace_collision",
            workspace=workspace, scratch=scratch, home=scratch, tmpdir=workspace, codex_home=scratch / ".codex",
            expected="FAIL_PRE_INFERENCE_TMPDIR_COLLISION",
        ))
        _set_tree_mode(scratch, writable=False)
        observations.append(probe(
            case_id="runtime_scratch_permission_mismatch",
            workspace=workspace, scratch=scratch, home=scratch, tmpdir=scratch, codex_home=scratch / ".codex",
            expected="FAIL_PRE_INFERENCE_SCRATCH_NOT_WRITABLE",
        ))
        _set_tree_mode(scratch, writable=True)
        observations.append(probe(
            case_id="isolated_runtime_after_permission_repair",
            workspace=workspace, scratch=scratch, home=scratch, tmpdir=scratch, codex_home=scratch / ".codex",
            expected="PASS_WORKSPACE_READONLY_SCRATCH_WRITABLE",
        ))
    return tuple(observations)


__all__ = [
    "FilesystemProbeObservation", "run_parent_environment_allowlist_probe", "run_reproduction_matrix",
    "run_startup_probe",
]
