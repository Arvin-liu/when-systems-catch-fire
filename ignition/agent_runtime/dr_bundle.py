"""Verifiable disposable disaster-recovery bundle for local continuity."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json

from .control import _atomic_json


DR_BUNDLE_SCHEMA = "ignition-durability-dr-bundle-r1"
DR_BUNDLE_EPOCH = "dr-bundle-epoch-1"
REQUIRED_CHUNKS = (
    "trusted-snapshot", "tail-event-lineage", "schema-migration", "namespace-registry", "pack-lifecycle",
    "executor-admission", "capability-revocation", "accounting", "reconciliation", "memory-integrity",
    "soft-governance", "operator-checkpoint",
)
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_FILE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "access_token", "token", "cookie", "authorization", "secret"})
_HARD_FIELDS = frozenset({"permission", "permissions", "authorization", "authorize", "truth", "truth_status", "owner_acceptance", "epistemic_acceptance", "safety_release", "capability_grant"})


class DRBundleError(ValueError):
    """Raised when a recovery bundle cannot be built or verified."""


class DRBundleIntegrityError(DRBundleError):
    """Raised for missing, stale, corrupt or cross-namespace bundle material."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise DRBundleError(f"{field} is not a canonical identifier")
    return value


def _public_json(value: Any, field: str = "payload") -> Any:
    if isinstance(value, str):
        if not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
            raise DRBundleError(f"{field} contains private or hidden material")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not key.strip() or any(marker in key.casefold() for marker in _FORBIDDEN):
                raise DRBundleError(f"{field} contains a private field")
            result[key] = _public_json(child, f"{field}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_public_json(child, f"{field}[]") for child in value]
    raise DRBundleError(f"{field} is not JSON-safe")


def _payload_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _validate_soft_governance(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise DRBundleError("soft-governance chunk must be an object")
    if value.get("status") not in {"ADVISORY_ONLY", "CANDIDATE_ESI_SIGNAL", "READY_NOT_RUN", "NOT_RUN_LIVE_EXTERNAL", "WITHDRAWN"}:
        raise DRBundleError("soft-governance status is not advisory")
    effects = value.get("authority_effects", ["NONE"])
    if not isinstance(effects, list) or any(effect != "NONE" for effect in effects):
        raise DRBundleError("soft-governance bundle attempts an authority effect")
    if value.get("claim_ceiling") and "advisory" not in str(value["claim_ceiling"]).casefold():
        raise DRBundleError("soft-governance claim ceiling is not advisory")
    for key, child in value.items():
        if str(key).casefold() in _HARD_FIELDS and not (child is None or child == "NONE" or child == [] or child == {}):
            raise DRBundleError("soft-governance field attempts soft-to-hard injection")
        if isinstance(child, Mapping):
            _validate_soft_governance(child)


class RecoveryBundleBuilder:
    """Build one immutable-looking bundle directory through a staging rename."""

    def __init__(self, target: str | Path) -> None:
        self.target = Path(target)

    def build(
        self,
        *,
        bundle_id: str,
        namespace_id: str,
        schema_epoch: str,
        source_ledger_head_hash: str,
        chunks: Mapping[str, Mapping[str, Any]],
        unresolved_reconciliation_refs: tuple[str, ...] = (),
        operator_checkpoint: str = "operator-checkpoint-unreviewed",
        created_at: float = 0.0,
    ) -> dict[str, Any]:
        _id(bundle_id, "bundle_id")
        _id(namespace_id, "namespace_id")
        _id(schema_epoch, "schema_epoch")
        _id(operator_checkpoint, "operator_checkpoint")
        if not isinstance(source_ledger_head_hash, str) or len(source_ledger_head_hash) != 64 or any(char not in "0123456789abcdef" for char in source_ledger_head_hash):
            raise DRBundleError("source_ledger_head_hash must be a lowercase SHA-256 digest")
        if not isinstance(created_at, (int, float)) or created_at < 0:
            raise DRBundleError("created_at must be non-negative")
        if set(REQUIRED_CHUNKS) - set(chunks):
            raise DRBundleError("required recovery bundle chunk is missing")
        if self.target.exists():
            raise DRBundleError("bundle target already exists; overwrite is forbidden")
        normalized: dict[str, Mapping[str, Any]] = {}
        for name, payload in chunks.items():
            if not isinstance(name, str) or not _FILE.fullmatch(name):
                raise DRBundleError(f"invalid chunk name: {name}")
            public = _public_json(payload, f"chunk.{name}")
            if not isinstance(public, Mapping):
                raise DRBundleError(f"chunk.{name} must be an object")
            if "namespace_id" in public and public["namespace_id"] != namespace_id:
                raise DRBundleIntegrityError(f"chunk.{name} namespace mismatch")
            if name == "soft-governance":
                _validate_soft_governance(public)
            normalized[name] = public
        self.target.parent.mkdir(parents=True, exist_ok=True)
        staging: Path | None = Path(tempfile.mkdtemp(prefix=f".{self.target.name}.staging-", dir=self.target.parent))
        try:
            chunk_dir = staging / "chunks"
            chunk_dir.mkdir(parents=True, exist_ok=False)
            manifest_chunks: list[dict[str, Any]] = []
            for name in sorted(normalized):
                path = chunk_dir / f"{name}.json"
                _atomic_json(path, dict(normalized[name]))
                manifest_chunks.append({"name": name, "path": f"chunks/{name}.json", "sha256": _payload_digest(normalized[name]), "required": name in REQUIRED_CHUNKS})
            manifest = {
                "schema": DR_BUNDLE_SCHEMA, "bundle_epoch": DR_BUNDLE_EPOCH, "bundle_id": bundle_id, "namespace_id": namespace_id,
                "schema_epoch": schema_epoch, "source_ledger_head_hash": source_ledger_head_hash, "created_at": created_at,
                "external_reexecution": "FORBIDDEN", "operator_checkpoint": operator_checkpoint,
                "unresolved_reconciliation_refs": sorted(set(unresolved_reconciliation_refs)), "chunks": manifest_chunks,
                "claim_ceiling": "Disposable local recovery evidence only; no automatic external side-effect reexecution.",
            }
            manifest["manifest_sha256"] = sha256_json(manifest)
            _atomic_json(staging / "manifest.json", manifest)
            os.replace(staging, self.target)
            staging = None
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging)
        return RecoveryBundleVerifier.verify(self.target, namespace_id=namespace_id, schema_epoch=schema_epoch, expected_source_ledger_head_hash=source_ledger_head_hash)


class RecoveryBundleVerifier:
    """Verify a bundle without executing or dispatching anything."""

    @staticmethod
    def _safe_path(root: Path, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise DRBundleIntegrityError("bundle chunk path escapes bundle root")
        resolved = (root / path).resolve()
        if root.resolve() not in resolved.parents and resolved != root.resolve():
            raise DRBundleIntegrityError("bundle chunk path resolves outside bundle root")
        return resolved

    @classmethod
    def verify(cls, root: str | Path, *, namespace_id: str, schema_epoch: str, expected_source_ledger_head_hash: str | None = None) -> dict[str, Any]:
        root = Path(root)
        _id(namespace_id, "namespace_id")
        _id(schema_epoch, "schema_epoch")
        try:
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DRBundleIntegrityError("bundle manifest is unreadable") from exc
        required = {"schema", "bundle_epoch", "bundle_id", "namespace_id", "schema_epoch", "source_ledger_head_hash", "created_at", "external_reexecution", "operator_checkpoint", "unresolved_reconciliation_refs", "chunks", "claim_ceiling", "manifest_sha256"}
        if set(manifest) != required or manifest.get("schema") != DR_BUNDLE_SCHEMA or manifest.get("bundle_epoch") != DR_BUNDLE_EPOCH:
            raise DRBundleIntegrityError("bundle manifest schema mismatch")
        unsigned = {key: manifest[key] for key in manifest if key != "manifest_sha256"}
        if manifest["manifest_sha256"] != sha256_json(unsigned):
            raise DRBundleIntegrityError("bundle manifest digest mismatch")
        if manifest["namespace_id"] != namespace_id or manifest["schema_epoch"] != schema_epoch:
            raise DRBundleIntegrityError("bundle namespace or schema epoch mismatch")
        if expected_source_ledger_head_hash is not None and manifest["source_ledger_head_hash"] != expected_source_ledger_head_hash:
            raise DRBundleIntegrityError("bundle is stale for the requested ledger head")
        if manifest["external_reexecution"] != "FORBIDDEN" or "local recovery" not in manifest["claim_ceiling"].casefold():
            raise DRBundleIntegrityError("bundle external reexecution or claim ceiling is unsafe")
        entries = manifest["chunks"]
        if not isinstance(entries, list) or len({item.get("name") for item in entries}) != len(entries):
            raise DRBundleIntegrityError("bundle chunk manifest is malformed")
        found: dict[str, Mapping[str, Any]] = {}
        for entry in entries:
            if not isinstance(entry, Mapping) or set(entry) != {"name", "path", "sha256", "required"} or not entry.get("required"):
                raise DRBundleIntegrityError("bundle chunk manifest entry is malformed")
            name = entry["name"]
            path = cls._safe_path(root, entry["path"])
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DRBundleIntegrityError(f"bundle chunk is unreadable: {name}") from exc
            public = _public_json(payload, f"chunk.{name}")
            if _payload_digest(public) != entry["sha256"]:
                raise DRBundleIntegrityError(f"bundle chunk digest mismatch: {name}")
            if isinstance(public, Mapping) and "namespace_id" in public and public["namespace_id"] != namespace_id:
                raise DRBundleIntegrityError(f"bundle chunk namespace mismatch: {name}")
            if name == "soft-governance":
                _validate_soft_governance(public)
            found[name] = public
        missing = sorted(set(REQUIRED_CHUNKS) - set(found))
        if missing:
            raise DRBundleIntegrityError("bundle is missing required chunks: " + ",".join(missing))
        if found["namespace-registry"].get("namespace_id") != namespace_id:
            raise DRBundleIntegrityError("namespace registry does not match bundle namespace")
        return {"status": "PASS", "bundle_id": manifest["bundle_id"], "namespace_id": namespace_id, "schema_epoch": schema_epoch, "canonical_digest": manifest["manifest_sha256"], "chunk_count": len(found), "unresolved_reconciliation_refs": list(manifest["unresolved_reconciliation_refs"]), "external_reexecution": manifest["external_reexecution"], "chunks": found}

    @classmethod
    def restore(cls, root: str | Path, *, namespace_id: str, schema_epoch: str, expected_source_ledger_head_hash: str | None = None) -> dict[str, Any]:
        """Verify and return local JSON chunks; never re-dispatches external effects."""
        return cls.verify(root, namespace_id=namespace_id, schema_epoch=schema_epoch, expected_source_ledger_head_hash=expected_source_ledger_head_hash)


__all__ = ["DR_BUNDLE_EPOCH", "DR_BUNDLE_SCHEMA", "DRBundleError", "DRBundleIntegrityError", "RecoveryBundleBuilder", "RecoveryBundleVerifier", "REQUIRED_CHUNKS"]
