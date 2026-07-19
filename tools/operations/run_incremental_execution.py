#!/usr/bin/env python3
"""Safe Q32I executor: dry-run by default, identity-bound cache, rollback."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


class DefensiveBoundaryError(ValueError):
    """Stable fail-closed rejection raised before any producer is started."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str | None:
    return digest_bytes(path.read_bytes()) if path.is_file() else None


def validate_relative_path(raw: str, root: Path) -> Path:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw:
        raise DefensiveBoundaryError("E_UNSAFE_PATH", f"unsafe repository path: {raw!r}")
    if len(raw) > 2 and raw[1] == ":":
        raise DefensiveBoundaryError("E_UNSAFE_PATH", f"Windows path rejected: {raw}")
    parts = PurePosixPath(raw).parts
    if ".." in parts or "." in parts:
        raise DefensiveBoundaryError("E_UNSAFE_PATH", f"non-canonical path rejected: {raw}")
    resolved = (root / raw).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise DefensiveBoundaryError("E_UNSAFE_PATH", f"path escapes repository: {raw}")
    return resolved


def validate_repository_location(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise DefensiveBoundaryError("E_UNSAFE_PATH", f"{label} escapes repository: {path}")
    return resolved


def validate_argv(argv: object) -> list[str]:
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        raise DefensiveBoundaryError("E_COMMAND_ARGV", "producer/validator must be a non-empty argv array")
    forbidden = (";", "&&", "|", "$(", "`")
    if any(any(token in arg for token in forbidden) for arg in argv):
        raise DefensiveBoundaryError("E_COMMAND_ARGV", "shell metacharacter or command injection rejected")
    return argv


def git_is_clean(root: Path) -> bool:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=True)
    return not result.stdout.strip()


def repository_snapshot(root: Path, ignored_roots: tuple[Path, ...] = ()) -> dict[str, dict]:
    """Capture byte/type/mode state without following symlinks."""
    ignored_rel = {p.absolute().relative_to(root.absolute()).as_posix() for p in ignored_roots}
    state: dict[str, dict] = {}
    for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base_path = Path(base)
        rel_base = base_path.relative_to(root).as_posix()
        dirs[:] = [d for d in dirs if d != ".git" and not any((rel_base + "/" + d).strip("/") == x or (rel_base + "/" + d).strip("/").startswith(x + "/") or x.startswith((rel_base + "/" + d).strip("/") + "/") for x in ignored_rel)]
        for name in sorted(dirs + files):
            path = base_path / name
            raw = path.relative_to(root).as_posix()
            if any(raw == x or raw.startswith(x + "/") or x.startswith(raw + "/") for x in ignored_rel):
                continue
            info = path.lstat()
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISLNK(info.st_mode):
                state[raw] = {"type": "symlink", "target": os.readlink(path), "mode": mode}
            elif stat.S_ISDIR(info.st_mode):
                state[raw] = {"type": "directory", "mode": mode}
            elif stat.S_ISREG(info.st_mode):
                state[raw] = {"type": "file", "bytes": path.read_bytes(), "mode": mode}
            else:
                state[raw] = {"type": "unsupported", "mode": mode}
    return state


def snapshot_fingerprint(entry: dict | None) -> str | None:
    if entry is None: return None
    material = {k: (digest_bytes(v) if k == "bytes" else v) for k, v in entry.items()}
    return digest_bytes(canonical(material).encode())


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file(): path.unlink()
    elif path.is_dir(): shutil.rmtree(path)


def restore_repository_snapshot(root: Path, before: dict[str, dict], ignored_roots: tuple[Path, ...] = ()) -> tuple[list[str], list[str]]:
    current = repository_snapshot(root, ignored_roots)
    restored: list[str] = []
    unrecovered: list[str] = []
    removable = (set(current) - set(before)) | {raw for raw in set(current) & set(before) if current[raw]["type"] != before[raw]["type"]}
    for raw in sorted(removable, key=lambda x: (x.count("/"), x), reverse=True):
        try: remove_path(root / raw); restored.append(raw)
        except OSError: unrecovered.append(raw)
    for raw, entry in sorted(before.items(), key=lambda item: (item[0].count("/"), item[0])):
        if entry["type"] != "directory": continue
        path = root / raw
        try:
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(path, 0o700)
            restored.append(raw)
        except OSError: unrecovered.append(raw)
    for raw, entry in sorted(before.items(), key=lambda item: (item[0].count("/"), item[0])):
        if entry["type"] == "directory": continue
        path = root / raw
        try:
            if entry["type"] == "file":
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(entry["bytes"])
            elif entry["type"] == "symlink":
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink() and os.readlink(path) != entry["target"]: path.unlink()
                if not path.is_symlink(): path.symlink_to(entry["target"])
            else:
                unrecovered.append(raw); continue
            if entry["type"] == "file": os.chmod(path, entry["mode"])
            restored.append(raw)
        except OSError: unrecovered.append(raw)
    for raw, entry in sorted(before.items(), key=lambda item: (item[0].count("/"), item[0]), reverse=True):
        if entry["type"] == "directory":
            try: os.chmod(root / raw, entry["mode"])
            except OSError: unrecovered.append(raw)
    after = repository_snapshot(root, ignored_roots)
    mismatches = sorted(raw for raw in set(before) | set(after) if snapshot_fingerprint(before.get(raw)) != snapshot_fingerprint(after.get(raw)))
    return sorted(set(restored)), sorted(set(unrecovered) | set(mismatches))


def profile_identity(profiles_path: Path, profiles: dict, root: Path, plan: dict) -> dict:
    registry = root / "data/operations/project-components.json"
    topology = root / "data/operations/change-propagation-topology.json"
    producer_identity = digest_bytes(canonical([p.get("producer_argv") for p in profiles["profiles"]]).encode())
    validator_identity = digest_bytes(canonical([p.get("validator_argv") for p in profiles["profiles"]]).encode())
    component_ids = plan.get("execution_order", [])
    by_id = {p["component_id"]: p for p in profiles["profiles"]}
    input_fingerprints = {
        raw: digest_file(validate_relative_path(raw, root))
        for cid in component_ids
        for raw in by_id[cid].get("authoritative_inputs", [])
    }
    return {
        "profile_schema_version": profiles["schema_version"],
        "profile_registry_digest": digest_file(profiles_path),
        "component_registry_digest": digest_file(registry),
        "propagation_topology_digest": digest_file(topology),
        "producer_identity": producer_identity,
        "validator_identity": validator_identity,
        "input_fingerprints": input_fingerprints,
        "output_fingerprints": output_fingerprints(profiles, root, component_ids),
        "plan_hash": plan["plan_hash"],
    }


def output_fingerprints(profiles: dict, root: Path, component_ids: list[str]) -> dict[str, str | None]:
    by_id = {p["component_id"]: p for p in profiles["profiles"]}
    result: dict[str, str | None] = {}
    for cid in component_ids:
        for raw in by_id[cid].get("generated_outputs", []):
            result[raw] = digest_file(validate_relative_path(raw, root))
    return result


def cache_hit(cache_dir: Path, plan: dict, profiles_path: Path, profiles: dict, root: Path) -> bool:
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        integrity = document.pop("integrity_digest")
    except (OSError, KeyError, json.JSONDecodeError):
        return False
    if integrity != digest_bytes(canonical(document).encode()):
        return False
    if document.get("identity") != profile_identity(profiles_path, profiles, root, plan):
        return False
    ids = plan.get("execution_order", [])
    return document.get("output_fingerprints") == output_fingerprints(profiles, root, ids)


def recovery_package(
    root: Path,
    cache_dir: Path,
    plan: dict,
    records: list[dict],
    snapshots: dict[str, dict],
    restored: list[str],
    unrecovered: list[str],
) -> Path:
    package = Path(tempfile.mkdtemp(prefix="recovery-", dir=cache_dir))
    backup_dir = package / "backups"
    backup_dir.mkdir()
    sha256: dict[str, str] = {}
    for raw, entry in snapshots.items():
        if entry.get("type") != "file":
            continue
        content = entry["bytes"]
        destination = backup_dir / raw
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        sha256[f"backups/{raw}"] = digest_bytes(content)
    manifest = {
        "manifest_version": "1.0.0",
        "plan_hash": plan["plan_hash"],
        "component_identity": [r["component_id"] for r in records],
        "failed_action": next((r for r in records if r["end_status"] == "failed"), None),
        "original_fingerprints": {k: snapshot_fingerprint(v) for k, v in snapshots.items()},
        "current_fingerprints": {k: snapshot_fingerprint(repository_snapshot(root, (cache_dir,)).get(k)) for k in snapshots},
        "sha256": sha256,
        "restored_files": restored,
        "unrecovered_files": unrecovered,
        "restore_steps": ["Copy each backups/<path> file to the same repository-relative <path>.", "Re-run validators before apply."],
        "records": records,
    }
    manifest["integrity_digest"] = digest_bytes(canonical(manifest).encode())
    (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package


def execute_plan(
    plan: dict,
    *,
    apply: bool = False,
    isolated_worktree: bool = False,
    root: Path = DEFAULT_ROOT,
    profiles_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict:
    root = root.resolve()
    ignored_input_codes = ["E_CALLER_COMMAND_IGNORED"] if any(
        field in plan for field in ("producer_argv", "validator_argv", "command", "shell_command")
    ) else []
    profiles_path = validate_repository_location(
        profiles_path or root / "data/operations/component-execution-profiles.json", root, "profiles path"
    )
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    by_id = {p["component_id"]: p for p in profiles["profiles"]}
    if len(by_id) != len(profiles["profiles"]):
        raise DefensiveBoundaryError("E_PROFILE_DUPLICATE_COMPONENT", "duplicate execution profile")
    order = plan.get("execution_order", [])
    if any(cid not in by_id for cid in order):
        raise DefensiveBoundaryError("E_EXECUTION_ORDER", "execution order references unknown profile")
    cache_dir = validate_repository_location(cache_dir or root / ".cache/q32i-executor", root, "cache directory")
    if apply:
        # The unified production validator is the single apply-authority gate.
        # Importing here avoids the validator/executor identity helper cycle.
        from tools.operations.validate_incremental_execution import validate_incremental_execution
        preflight = validate_incremental_execution(plan, root=root, profiles_path=profiles_path)
        if not preflight["ok"]:
            first = preflight["errors"][0]
            raise DefensiveBoundaryError(first["code"], first["reason"])
    if apply and not isolated_worktree and not git_is_clean(root):
        raise DefensiveBoundaryError("E_DIRTY_WORKTREE", "apply requires clean tree or explicit isolated worktree")
    if apply and cache_hit(cache_dir, plan, profiles_path, profiles, root):
        return {"ok": True, "cache_hit": True, "cache_decision": "HIT_FRESH", "records": [], "input_rejections": ignored_input_codes}

    records: list[dict] = []
    snapshots: dict[str, dict] = {}
    allowed_outputs: set[str] = set()
    whole_repo_before = repository_snapshot(root, (cache_dir,)) if apply else {}
    for cid in order:
        profile = by_id[cid]
        capability = profile.get("execution_capability", profile.get("execution_kind"))
        record = {
            "component_id": cid,
            "argv": profile.get("producer_argv"),
            "cwd": ".",
            "start_status": "planned",
            "end_status": "dry-run" if not apply else "pending",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "before_input_fingerprints": {},
            "before_output_fingerprints": {},
            "after_output_fingerprints": {},
            "validator_result": "not-run",
            "cache_decision": "MISS_OR_DISABLED" if apply else "DRY_RUN_NO_CACHE",
            "rollback_status": "not-required",
        }
        outputs = profile.get("generated_outputs", [])
        for raw in outputs:
            path = validate_relative_path(raw, root)
            allowed_outputs.add(raw)
            if raw in whole_repo_before: snapshots.setdefault(raw, whole_repo_before[raw])
            record["before_output_fingerprints"][raw] = digest_file(path)
        for raw in profile.get("authoritative_inputs", []):
            path = validate_relative_path(raw, root)
            record["before_input_fingerprints"][raw] = digest_file(path)
        if not apply:
            records.append(record)
            continue
        if capability in {"manual", "validation_only"}:
            record["end_status"] = "manual-boundary"
            record["validator_result"] = "manual-or-validation-only"
            records.append(record)
            continue
        if capability in {"external_attestation", "attestation"}:
            record["end_status"] = "attestation-required"
            record["validator_result"] = "external-attestation-required-no-local-producer"
            records.append(record)
            continue
        if capability != "automatic":
            raise ValueError(f"unknown execution capability for {cid}")
        argv = validate_argv(profile.get("producer_argv"))
        validator = validate_argv(profile.get("validator_argv"))
        before_tree = repository_snapshot(root, (cache_dir,))
        record["start_status"] = "running"
        started = time.time_ns()
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True, shell=False)
        after_tree = repository_snapshot(root, (cache_dir,))
        changed = {p for p in set(before_tree) | set(after_tree) if snapshot_fingerprint(before_tree.get(p)) != snapshot_fingerprint(after_tree.get(p))}
        unregistered = sorted(changed - set(outputs))
        record.update(stdout=completed.stdout, stderr=completed.stderr, return_code=completed.returncode, duration_ns=time.time_ns() - started)
        if unregistered:
            record["stderr"] += f"\nunregistered outputs: {unregistered}"
            record["error_code"] = "E_UNREGISTERED_WRITE"
            completed = subprocess.CompletedProcess(argv, 90, record["stdout"], record["stderr"])
            record["return_code"] = 90
        if completed.returncode == 0:
            validation = subprocess.run(validator, cwd=root, text=True, capture_output=True, shell=False)
            record["validator_result"] = {"return_code": validation.returncode, "stdout": validation.stdout, "stderr": validation.stderr}
            if validation.returncode:
                completed = subprocess.CompletedProcess(argv, 91, completed.stdout, validation.stderr)
                record["return_code"] = 91
        for raw in outputs:
            record["after_output_fingerprints"][raw] = digest_file(validate_relative_path(raw, root))
        if completed.returncode == 0:
            record["end_status"] = "success"
            records.append(record)
            continue

        record["end_status"] = "failed"
        restored: list[str] = []
        unrecovered: list[str] = []
        recovery_only = profile.get("rollback_policy") == "recovery_package_only"
        if recovery_only:
            unrecovered = sorted(changed)
        else:
            restored, unrecovered = restore_repository_snapshot(root, whole_repo_before, (cache_dir,))
        final_state = repository_snapshot(root, (cache_dir,))
        byte_exact = all(snapshot_fingerprint(whole_repo_before.get(raw)) == snapshot_fingerprint(final_state.get(raw)) for raw in set(whole_repo_before) | set(final_state))
        if not byte_exact:
            unrecovered = sorted(set(unrecovered) | {raw for raw in set(whole_repo_before) | set(final_state) if snapshot_fingerprint(whole_repo_before.get(raw)) != snapshot_fingerprint(final_state.get(raw))})
        record["rollback_status"] = "restored" if not unrecovered else "recovery-package-required"
        records.append(record)
        cache_dir.mkdir(parents=True, exist_ok=True)
        package = recovery_package(root, cache_dir, plan, records, whole_repo_before, restored, unrecovered)
        return {"ok": False, "cache_hit": False, "cache_decision": "MISS", "records": records, "recovery_package": str(package), "input_rejections": ignored_input_codes}

    if not apply:
        return {"ok": True, "cache_hit": False, "cache_decision": "DRY_RUN_NO_CACHE", "records": records, "input_rejections": ignored_input_codes}
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "identity": profile_identity(profiles_path, profiles, root, plan),
        "output_fingerprints": output_fingerprints(profiles, root, order),
        "records": records,
    }
    manifest["integrity_digest"] = digest_bytes(canonical(manifest).encode())
    (cache_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "cache_hit": False, "cache_decision": "MISS_STORED", "records": records, "cache_manifest": str(cache_dir / "manifest.json"), "input_rejections": ignored_input_codes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--isolated-worktree", action="store_true")
    parser.add_argument("--cache-dir", type=Path)
    args = parser.parse_args()
    try:
        result = execute_plan(json.loads(args.plan.read_text(encoding="utf-8")), apply=args.apply, isolated_worktree=args.isolated_worktree, cache_dir=args.cache_dir)
    except DefensiveBoundaryError as exc:
        result = {"ok": False, "error_code": exc.code, "error": str(exc), "records": []}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
