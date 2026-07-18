#!/usr/bin/env python3
"""Safe Q32I executor: dry-run by default, identity-bound cache, rollback."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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


def tree_state(root: Path, ignored_roots: tuple[Path, ...] = ()) -> dict[str, str]:
    state: dict[str, str] = {}
    ignored = {p.resolve() for p in ignored_roots}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        resolved = path.resolve()
        if any(resolved == base or base in resolved.parents for base in ignored):
            continue
        state[path.relative_to(root).as_posix()] = digest_file(path) or ""
    return state


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
    snapshots: dict[str, bytes | None],
    restored: list[str],
    unrecovered: list[str],
) -> Path:
    package = Path(tempfile.mkdtemp(prefix="recovery-", dir=cache_dir))
    backup_dir = package / "backups"
    backup_dir.mkdir()
    sha256: dict[str, str] = {}
    for raw, content in snapshots.items():
        if content is None:
            continue
        destination = backup_dir / raw
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        sha256[f"backups/{raw}"] = digest_bytes(content)
    manifest = {
        "manifest_version": "1.0.0",
        "plan_hash": plan["plan_hash"],
        "component_identity": [r["component_id"] for r in records],
        "failed_action": next((r for r in records if r["end_status"] == "failed"), None),
        "original_fingerprints": {k: digest_bytes(v) if v is not None else None for k, v in snapshots.items()},
        "current_fingerprints": {k: digest_file(validate_relative_path(k, root)) for k in snapshots},
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
    if apply and not isolated_worktree and not git_is_clean(root):
        raise DefensiveBoundaryError("E_DIRTY_WORKTREE", "apply requires clean tree or explicit isolated worktree")
    if apply and cache_hit(cache_dir, plan, profiles_path, profiles, root):
        return {"ok": True, "cache_hit": True, "cache_decision": "HIT_FRESH", "records": [], "input_rejections": ignored_input_codes}

    records: list[dict] = []
    snapshots: dict[str, bytes | None] = {}
    allowed_outputs: set[str] = set()
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
            snapshots.setdefault(raw, path.read_bytes() if path.is_file() else None)
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
        before_tree = tree_state(root, (cache_dir,))
        record["start_status"] = "running"
        started = time.time_ns()
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True, shell=False)
        after_tree = tree_state(root, (cache_dir,))
        changed = {p for p in set(before_tree) | set(after_tree) if before_tree.get(p) != after_tree.get(p)}
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
        for raw, content in snapshots.items():
            path = validate_relative_path(raw, root)
            if recovery_only:
                unrecovered.append(raw)
                continue
            try:
                if content is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                restored.append(raw)
            except OSError:
                unrecovered.append(raw)
        for raw in unregistered:
            path = validate_relative_path(raw, root)
            try:
                if before_tree.get(raw) is None and path.exists():
                    path.unlink()
            except OSError:
                unrecovered.append(raw)
        record["rollback_status"] = "restored" if not unrecovered else "recovery-package-required"
        records.append(record)
        cache_dir.mkdir(parents=True, exist_ok=True)
        package = recovery_package(root, cache_dir, plan, records, snapshots, restored, unrecovered)
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
