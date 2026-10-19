#!/usr/bin/env python3
"""Build, verify, and locally simulate rollback for a versioned component bundle.

This tool never publishes or activates an artifact. Its output status is always
PREPARED_UNPUBLISHED; GitHub publication is a separately authorized workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations.route_component_validation import (  # noqa: E402
    MAP_PATH,
    REGISTRY_PATH,
    RoutingBlocked,
    canonical_json,
    load_json,
)
from tools.operations.verify_component_validation_evidence import verify_evidence  # noqa: E402

POLICY_PATH = ROOT / "data/operations/component-release-policy-r1.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/operations/component-release-policy-r1.schema.json"
MANIFEST_SCHEMA_PATH = ROOT / "schemas/operations/component-release-manifest-r1.schema.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
INTERNAL_RELEASE_PATH = ".component/release.json"
INTERNAL_PLAN_PATH = ".component/validation-plan.json"
INTERNAL_RECEIPT_PATH = ".component/validation-receipt.json"


def _git(repo_root: Path, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RoutingBlocked(f"git {' '.join(args[:2])} failed: {message}")
    return result.stdout if binary else result.stdout.decode("utf-8", errors="strict").strip()


def _exact_commit(repo_root: Path, value: str, label: str) -> str:
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        raise RoutingBlocked(f"{label} must be an exact lowercase commit SHA")
    resolved = _git(repo_root, "rev-parse", "--verify", f"{value}^{{commit}}")
    if resolved != value:
        raise RoutingBlocked(f"{label} does not resolve to the supplied commit")
    return value


def _tree_index(repo_root: Path, commit_sha: str) -> dict[str, dict[str, str]]:
    raw = _git(repo_root, "ls-tree", "-r", "-z", "--full-tree", commit_sha, binary=True)
    result: dict[str, dict[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_sha = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8", errors="strict")
        pure = PurePosixPath(path)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise RoutingBlocked(f"Git tree contains a non-canonical path: {path!r}")
        if path in result:
            raise RoutingBlocked(f"Git tree contains duplicate path: {path}")
        result[path] = {"mode": mode, "type": object_type, "object_sha": object_sha}
    return result


def _matches(path: str, pattern: str) -> bool:
    # Component registry paths are relative to ignition/, while Git tree paths
    # include that checkout directory. Match the registry's canonical path at
    # its repository location when selecting immutable bundle blobs.
    repo_pattern = pattern if pattern.startswith("ignition/") else f"ignition/{pattern}"
    return path.startswith(repo_pattern) if repo_pattern.endswith("/") else path == repo_pattern


def _policy_and_registry(policy: dict[str, Any] | None = None, registry: dict[str, Any] | None = None):
    policy = policy or load_json(POLICY_PATH)
    registry = registry or load_json(REGISTRY_PATH)
    policy_schema = load_json(POLICY_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(policy_schema).iter_errors(policy), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        raise RoutingBlocked(f"component release policy schema error at {list(first.path)}: {first.message}")
    components = {item["component_id"]: item for item in registry.get("components", [])}
    entries = {item["component_id"]: item for item in policy["components"]}
    if len(entries) != len(policy["components"]):
        raise RoutingBlocked("component release policy has duplicate component IDs")
    return policy, components, entries


def _manifest_validate(manifest: dict[str, Any]) -> None:
    schema = load_json(MANIFEST_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        raise RoutingBlocked(f"component release manifest schema error at {list(first.path)}: {first.message}")


def _zip_entry(archive: zipfile.ZipFile, path: str, content: bytes, *, executable: bool = False) -> None:
    info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = ((0o100755 if executable else 0o100644) & 0xFFFF) << 16
    info.flag_bits = 0
    info.extra = b""
    info.comment = b""
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def prepare_release(
    *, repo_root: Path, component_id: str, version: str, source_sha: str,
    source_repository: str, plan_path: Path, receipt_path: Path, output_dir: Path,
    policy: dict[str, Any] | None = None, registry: dict[str, Any] | None = None,
    previous_manifest_path: Path | None = None, previous_archive_path: Path | None = None,
) -> dict[str, Any]:
    if not SEMVER.fullmatch(version):
        raise RoutingBlocked("component release version must be semantic major.minor.patch")
    source_sha = _exact_commit(repo_root, source_sha, "source_sha")
    policy, registry_components, policy_components = _policy_and_registry(policy, registry)
    release_policy = policy_components.get(component_id)
    if release_policy is None:
        raise RoutingBlocked(f"component has no independently reviewed release policy: {component_id}")
    missing_components = sorted(set(release_policy["bundle_components"]) - set(registry_components))
    if missing_components:
        raise RoutingBlocked(f"release bundle references undeclared components: {missing_components}")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    validation_sha = plan.get("source", {}).get("validation_sha")
    evidence = verify_evidence(
        plan, receipt, expected_validation_sha=validation_sha,
        expected_mode=plan.get("mode"),
    )
    missing_targets = sorted(set(release_policy["validation_target_ids"]) - set(evidence["selected_target_ids"]))
    if missing_targets:
        raise RoutingBlocked(f"component release evidence does not include required target tests: {missing_targets}")

    source_index = _tree_index(repo_root, source_sha)
    validation_index = _tree_index(repo_root, validation_sha)
    file_owners: dict[str, str] = {}
    for bundled_component in release_policy["bundle_components"]:
        component = registry_components[bundled_component]
        patterns = component.get("path_patterns", [])
        matched = [
            path for path, item in source_index.items()
            if any(_matches(path, pattern) for pattern in patterns)
        ]
        if not matched:
            raise RoutingBlocked(f"bundle component has no regular source files at {source_sha}: {bundled_component}")
        for path in matched:
            source_entry = source_index[path]
            if source_entry["type"] != "blob" or source_entry["mode"] not in {"100644", "100755"}:
                raise RoutingBlocked(f"bundle component contains a non-regular source path: {path}")
            previous_owner = file_owners.get(path)
            if previous_owner and previous_owner != bundled_component:
                raise RoutingBlocked(f"bundle source path is assigned to multiple components: {path}")
            file_owners[path] = bundled_component

    files: list[dict[str, Any]] = []
    file_bytes: dict[str, bytes] = {}
    for path, owner in sorted(file_owners.items()):
        source_entry = source_index[path]
        validation_entry = validation_index.get(path)
        if (
            source_entry["type"] != "blob"
            or source_entry["mode"] not in {"100644", "100755"}
            or validation_entry is None
            or validation_entry["type"] != "blob"
            or validation_entry["mode"] != source_entry["mode"]
            or validation_entry["object_sha"] != source_entry["object_sha"]
        ):
            raise RoutingBlocked(f"component file is not the same regular Git blob in the tested tree: {path}")
        content = _git(repo_root, "cat-file", "blob", source_entry["object_sha"], binary=True)
        file_bytes[path] = content
        files.append({
            "path": path,
            "component_id": owner,
            "git_blob_sha": source_entry["object_sha"],
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "executable": source_entry["mode"] == "100755",
        })

    previous_release: dict[str, str] | None = None
    if (previous_manifest_path is None) != (previous_archive_path is None):
        raise RoutingBlocked("previous manifest and archive must be supplied together")
    if previous_manifest_path is not None and previous_archive_path is not None:
        previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        validate_release_manifest(previous_manifest, previous_archive_path)
        if previous_manifest["component_id"] != component_id:
            raise RoutingBlocked("previous release belongs to another component")
        if tuple(map(int, previous_manifest["version"].split("."))) >= tuple(map(int, version.split("."))):
            raise RoutingBlocked("new component version must be greater than the recorded previous release")
        previous_release = {
            "version": previous_manifest["version"],
            "release_tag": previous_manifest["release_tag"],
            "artifact_sha256": previous_manifest["artifact_sha256"],
        }

    source_tree_sha = _git(repo_root, "rev-parse", f"{source_sha}^{{tree}}")
    release_tag = release_policy["release_tag_template"].format(version=version)
    artifact_name = f"{component_id}-{version}.zip"
    internal_release = {
        "schema_version": "component-bundle-content-r1",
        "component_id": component_id,
        "version": version,
        "source_commit_sha": source_sha,
        "source_tree_sha": source_tree_sha,
        "bundle_component_ids": release_policy["bundle_components"],
        "files": files,
        "validation_plan_sha256": evidence["plan_sha256"],
        "validation_receipt_sha256": evidence["receipt_sha256"],
    }
    plan_bytes = (canonical_json(plan) + "\n").encode("utf-8")
    receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / artifact_name
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in files:
            _zip_entry(archive, item["path"], file_bytes[item["path"]], executable=item["executable"])
        _zip_entry(archive, INTERNAL_RELEASE_PATH, (canonical_json(internal_release) + "\n").encode("utf-8"))
        _zip_entry(archive, INTERNAL_PLAN_PATH, plan_bytes)
        _zip_entry(archive, INTERNAL_RECEIPT_PATH, receipt_bytes)
    archive_bytes = archive_path.read_bytes()
    manifest: dict[str, Any] = {
        "schema_version": "component-release-manifest-r1",
        "component_id": component_id,
        "version": version,
        "release_tag": release_tag,
        "source_repository": source_repository,
        "source_commit_sha": source_sha,
        "source_tree_sha": source_tree_sha,
        "artifact_file": artifact_name,
        "artifact_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "artifact_bytes": len(archive_bytes),
        "artifact_state": "CONTENT_ADDRESSED",
        "bundle_component_ids": release_policy["bundle_components"],
        "files": files,
        "validation": {
            "plan_sha256": evidence["plan_sha256"],
            "receipt_sha256": evidence["receipt_sha256"],
            "validation_sha": evidence["validation_sha"],
            "validation_map_sha256": evidence["validation_map_sha256"],
            "selected_target_ids": evidence["selected_target_ids"],
        },
        "previous_release": previous_release,
        "claim_ceiling": "deterministic source bundle and verified repository test evidence; no publication, activation, source-access, or semantic research claim is established",
    }
    _manifest_validate(manifest)
    manifest_path = output_dir / "component-release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "component-validation-plan.json").write_bytes(plan_bytes)
    (output_dir / "component-validation-receipt.json").write_bytes(receipt_bytes)
    validate_release_manifest(manifest, archive_path, policy=policy, registry=registry_components)
    return manifest


def validate_release_manifest(
    manifest: dict[str, Any], archive_path: Path, *,
    repo_root: Path | None = None, policy: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _manifest_validate(manifest)
    if not archive_path.is_file():
        raise RoutingBlocked("component archive is missing")
    archive_bytes = archive_path.read_bytes()
    if (
        len(archive_bytes) != manifest["artifact_bytes"]
        or hashlib.sha256(archive_bytes).hexdigest() != manifest["artifact_sha256"]
    ):
        raise RoutingBlocked("component archive digest or size does not match its manifest")
    policy, registry_components, policy_components = _policy_and_registry(policy, registry)
    release_policy = policy_components.get(manifest["component_id"])
    if release_policy is None or release_policy["bundle_components"] != manifest["bundle_component_ids"]:
        raise RoutingBlocked("manifest component bundle does not match the current release policy")

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise RoutingBlocked("component archive contains duplicate entry names")
            expected_names = {item["path"] for item in manifest["files"]}
            expected_names.update({INTERNAL_RELEASE_PATH, INTERNAL_PLAN_PATH, INTERNAL_RECEIPT_PATH})
            if set(names) != expected_names:
                raise RoutingBlocked("component archive entries do not exactly match the manifest")
            for item in manifest["files"]:
                content = archive.read(item["path"])
                if len(content) != item["bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
                    raise RoutingBlocked(f"component source entry digest mismatch: {item['path']}")
                mode = stat.S_IMODE(archive.getinfo(item["path"]).external_attr >> 16)
                if mode != (0o755 if item["executable"] else 0o644):
                    raise RoutingBlocked(f"component source entry mode mismatch: {item['path']}")
            internal = json.loads(archive.read(INTERNAL_RELEASE_PATH).decode("utf-8"))
            plan = json.loads(archive.read(INTERNAL_PLAN_PATH).decode("utf-8"))
            receipt = json.loads(archive.read(INTERNAL_RECEIPT_PATH).decode("utf-8"))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RoutingBlocked(f"component archive is invalid or incomplete: {exc}") from exc

    expected_internal = {
        "schema_version": "component-bundle-content-r1",
        "component_id": manifest["component_id"],
        "version": manifest["version"],
        "source_commit_sha": manifest["source_commit_sha"],
        "source_tree_sha": manifest["source_tree_sha"],
        "bundle_component_ids": manifest["bundle_component_ids"],
        "files": manifest["files"],
        "validation_plan_sha256": manifest["validation"]["plan_sha256"],
        "validation_receipt_sha256": manifest["validation"]["receipt_sha256"],
    }
    if internal != expected_internal:
        raise RoutingBlocked("embedded component metadata does not match the external manifest")
    evidence = verify_evidence(
        plan, receipt, expected_validation_sha=manifest["validation"]["validation_sha"],
        expected_mode=plan.get("mode"),
    )
    for field in ("plan_sha256", "receipt_sha256", "validation_map_sha256", "validation_sha"):
        if evidence[field] != manifest["validation"][field]:
            raise RoutingBlocked(f"embedded validation evidence disagrees with manifest field {field}")
    if not set(release_policy["validation_target_ids"]).issubset(set(evidence["selected_target_ids"])):
        raise RoutingBlocked("embedded validation evidence omits a required component target")

    if repo_root is not None:
        source_sha = _exact_commit(repo_root, manifest["source_commit_sha"], "manifest source SHA")
        validation_sha = _exact_commit(repo_root, manifest["validation"]["validation_sha"], "manifest validation SHA")
        if _git(repo_root, "rev-parse", f"{source_sha}^{{tree}}") != manifest["source_tree_sha"]:
            raise RoutingBlocked("manifest source tree SHA does not match the exact source commit")
        source_index = _tree_index(repo_root, source_sha)
        validation_index = _tree_index(repo_root, validation_sha)
        for item in manifest["files"]:
            source_entry = source_index.get(item["path"])
            validation_entry = validation_index.get(item["path"])
            if (
                source_entry is None or validation_entry is None
                or source_entry["object_sha"] != item["git_blob_sha"]
                or source_entry["object_sha"] != validation_entry["object_sha"]
                or source_entry["mode"] not in {"100644", "100755"}
                or validation_entry["mode"] != source_entry["mode"]
            ):
                raise RoutingBlocked(f"manifest source or validation tree does not contain its exact path blob: {item['path']}")
            source_bytes = _git(repo_root, "cat-file", "blob", source_entry["object_sha"], binary=True)
            if len(source_bytes) != item["bytes"] or hashlib.sha256(source_bytes).hexdigest() != item["sha256"]:
                raise RoutingBlocked(f"manifest source SHA-256 disagrees with its exact Git blob: {item['path']}")
    return {
        "component_id": manifest["component_id"],
        "version": manifest["version"],
        "source_commit_sha": manifest["source_commit_sha"],
        "artifact_sha256": manifest["artifact_sha256"],
        "validation_receipt_sha256": manifest["validation"]["receipt_sha256"],
        "artifact_state": manifest["artifact_state"],
    }


def simulate_rollback(
    current_manifest: dict[str, Any], current_archive: Path,
    previous_manifest: dict[str, Any], previous_archive: Path,
) -> dict[str, Any]:
    validate_release_manifest(current_manifest, current_archive)
    validate_release_manifest(previous_manifest, previous_archive)
    if current_manifest["component_id"] != previous_manifest["component_id"]:
        raise RoutingBlocked("rollback target must be the same component")
    current_version = tuple(map(int, current_manifest["version"].split(".")))
    previous_version = tuple(map(int, previous_manifest["version"].split(".")))
    if previous_version >= current_version:
        raise RoutingBlocked("rollback target must be an earlier component version")
    if current_manifest["artifact_sha256"] == previous_manifest["artifact_sha256"]:
        raise RoutingBlocked("rollback target must identify different immutable artifact bytes")
    return {
        "schema_version": "component-rollback-simulation-r1",
        "component_id": current_manifest["component_id"],
        "from_release": {
            "version": current_manifest["version"],
            "release_tag": current_manifest["release_tag"],
            "artifact_sha256": current_manifest["artifact_sha256"],
        },
        "selected_previous_release": {
            "version": previous_manifest["version"],
            "release_tag": previous_manifest["release_tag"],
            "artifact_sha256": previous_manifest["artifact_sha256"],
        },
        "release_status": "SIMULATED_UNPUBLISHED",
        "activation_performed": False,
        "claim_ceiling": "validated local selection of a previous content-addressed bundle; no remote publication or runtime activation is established",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--repo-root", type=Path, required=True)
    prepare.add_argument("--component-id", required=True)
    prepare.add_argument("--version", required=True)
    prepare.add_argument("--source-sha", required=True)
    prepare.add_argument("--source-repository", required=True)
    prepare.add_argument("--plan", type=Path, required=True)
    prepare.add_argument("--receipt", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--previous-manifest", type=Path)
    prepare.add_argument("--previous-archive", type=Path)
    validate = commands.add_parser("validate")
    validate.add_argument("--repo-root", type=Path)
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--archive", type=Path, required=True)
    rollback = commands.add_parser("simulate-rollback")
    rollback.add_argument("--current-manifest", type=Path, required=True)
    rollback.add_argument("--current-archive", type=Path, required=True)
    rollback.add_argument("--previous-manifest", type=Path, required=True)
    rollback.add_argument("--previous-archive", type=Path, required=True)
    rollback.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            manifest = prepare_release(
                repo_root=args.repo_root.resolve(), component_id=args.component_id,
                version=args.version, source_sha=args.source_sha,
                source_repository=args.source_repository,
                plan_path=args.plan.resolve(), receipt_path=args.receipt.resolve(),
                output_dir=args.output_dir.resolve(),
                previous_manifest_path=args.previous_manifest.resolve() if args.previous_manifest else None,
                previous_archive_path=args.previous_archive.resolve() if args.previous_archive else None,
            )
            print(json.dumps({"operation_status": "PREPARED_UNPUBLISHED", "manifest": manifest}, ensure_ascii=False, sort_keys=True))
        elif args.command == "validate":
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            result = validate_release_manifest(
                manifest, args.archive.resolve(),
                repo_root=args.repo_root.resolve() if args.repo_root else None,
            )
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            current = json.loads(args.current_manifest.read_text(encoding="utf-8"))
            previous = json.loads(args.previous_manifest.read_text(encoding="utf-8"))
            event = simulate_rollback(current, args.current_archive.resolve(), previous, args.previous_archive.resolve())
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(event, ensure_ascii=False, sort_keys=True))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, RoutingBlocked, ValueError) as exc:
        print(f"component release operation blocked: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
