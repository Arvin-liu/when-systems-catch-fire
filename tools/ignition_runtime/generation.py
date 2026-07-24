"""Generation data model + closed-manifest (triple-equality) validation.

A generation is one directory ``gen_<id>/`` inside ``<store>/generations/``.
The closed manifest proves ``complete_file_list == digest_keys == actual_files``
where ``complete_file_list`` is fixed by ``op_type`` (``CANON``). Deleting a file
AND its digest entry is still rejected because the required set is fixed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import GenerationIntegrityError, ManifestError
from .hashutil import sha256_text
from .schemas_loader import validate_schema

SCHEMA_VERSION = "ignition_runtime/1.0.0"
RUNTIME_VERSION = "1.0.0"
CONTRACT_VERSION = "1.0.0"

# Canonical required-file set per op type (the "complete_file_list").
CANON: dict[str, frozenset[str]] = {
    "bootstrap": frozenset(
        {"store_identity.json", "manifest.json", "receipt.json", "audit_index.json"}
    ),
    "run": frozenset(
        {
            "store_identity.json",
            "manifest.json",
            "materials.json",
            "results.json",
            "candidates.json",
            "unknowns.json",
            "signals.json",
            "receipt.json",
            "audit_index.json",
        }
    ),
    "promote_request": frozenset(
        {
            "store_identity.json",
            "manifest.json",
            "materials.json",
            "results.json",
            "candidates.json",
            "unknowns.json",
            "signals.json",
            "promotion.json",
            "receipt.json",
            "audit_index.json",
        }
    ),
    "promote_approval": frozenset(
        {
            "store_identity.json",
            "manifest.json",
            "materials.json",
            "results.json",
            "candidates.json",
            "unknowns.json",
            "signals.json",
            "promotion.json",
            "receipt.json",
            "audit_index.json",
        }
    ),
    "evolve": frozenset(
        {
            "store_identity.json",
            "manifest.json",
            "materials.json",
            "results.json",
            "candidates.json",
            "unknowns.json",
            "signals.json",
            "receipt.json",
            "audit_index.json",
        }
    ),
}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


@dataclass
class Generation:
    op_type: str
    operation_id: str
    parent_generation: str | None
    store_identity: dict
    materials: dict = field(default_factory=dict)
    results: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    unknowns: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    promotion: dict | None = None
    receipt: dict | None = None
    audit_index: list = field(default_factory=list)
    gen_id: str | None = None
    provider_identity: str = "fixture://deterministic"
    timestamps: dict = field(default_factory=dict)

    # --- identity -------------------------------------------------------
    def core_payload(self) -> dict:
        core = {
            "parent": self.parent_generation,
            "op_type": self.op_type,
            "materials": self.materials,
            "results": self.results,
            "candidates": self.candidates,
            "unknowns": self.unknowns,
            "signals": self.signals,
        }
        if self.op_type in ("promote_request", "promote_approval") and self.promotion is not None:
            core["promotion"] = self.promotion
        return core

    def compute_gen_id(self) -> str:
        # Content-derived, immutable, unique. For RUN the parent (immediate
        # prior generation) is part of the identity so re-running from a new
        # state always yields a distinct generation. For PROMOTE/EVOLVE the
        # parent is the mutable pointer and must NOT be part of the identity,
        # otherwise a repeated (logical no-op) request would compute a different
        # id after the first publish advanced CURRENT. PROMOTE/EVOLVE ids are
        # derived from their stable logical inputs (source run / authorized_by /
        # signal), guaranteeing identical calls collapse to the same generation.
        payload = self.core_payload()
        if self.op_type in ("promote_request", "promote_approval", "evolve"):
            payload = {k: v for k, v in payload.items() if k != "parent"}
        return "gen_" + sha256_text(canonical_json(payload))[:32]

    def compute_operation_id(self, authorized_by: str = "") -> str:
        seed = canonical_json(
            {
                "parent": self.parent_generation,
                "op_type": self.op_type,
                "material_ids": sorted(self.materials.keys()),
                "provider_identity": self.provider_identity,
                "authorized_by": authorized_by,
            }
        )
        return "op_" + sha256_text(seed)[:32]

    # --- serialization --------------------------------------------------
    def _ledger_payload(self, name: str) -> Any:
        return {
            "store_identity.json": self.store_identity,
            "materials.json": self.materials,
            "results.json": self.results,
            "candidates.json": self.candidates,
            "unknowns.json": self.unknowns,
            "signals.json": self.signals,
            "receipt.json": self.receipt,
            "audit_index.json": self.audit_index,
            "promotion.json": self.promotion,
        }[name]

    def write_files(self, gen_dir: Path) -> dict[str, str]:
        """Write all required data files (per CANON, manifest excluded) into
        ``gen_dir``; return digests (filename->sha256)."""
        gen_dir.mkdir(parents=True, exist_ok=True)
        digests: dict[str, str] = {}
        for name in CANON[self.op_type]:
            if name == "manifest.json":
                continue
            obj = self._ledger_payload(name)
            data = canonical_json(obj).encode("utf-8")
            (gen_dir / name).write_bytes(data)
            digests[name] = sha256_text(canonical_json(obj))
        return digests

    def build_manifest(self, digests: dict[str, str]) -> dict:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "store_identity_ref": "store_identity.json",
            "parent_generation": self.parent_generation,
            "op_type": self.op_type,
            "operation_id": self.operation_id,
            "generation_id": self.gen_id,
            "required_files": sorted(CANON[self.op_type]),
            "digests": {k: digests[k] for k in sorted(CANON[self.op_type]) if k != "manifest.json"},
            "receipt_ref": "receipt.json",
            "committed": True,
            "immutable": True,
            "provider_identity": self.provider_identity,
            "timestamps": self.timestamps,
        }
        # Self-digest: hash the manifest with its own digest blanked, then record it.
        manifest_no_self = dict(manifest)
        manifest_no_self["digests"] = {**manifest["digests"], "manifest.json": ""}
        manifest["digests"]["manifest.json"] = sha256_text(canonical_json(manifest_no_self))
        validate_schema(manifest, "generation_manifest")
        return manifest

    def write_manifest(self, gen_dir: Path, digests: dict[str, str]) -> dict:
        manifest = self.build_manifest(digests)
        (gen_dir / "manifest.json").write_text(
            canonical_json(manifest), encoding="utf-8"
        )
        return manifest


# --- load + closed-manifest validation ---------------------------------
def _recompute_gen_id(gen_dir: Path, manifest: dict, op_type: str) -> str:
    """Recompute the content-derived generation id using the SAME function
    (``Generation.compute_gen_id``) used at publish time, from the ledgers on
    disk. This is the load-path content-addressing root of trust."""

    def _load(name: str):
        p = gen_dir / name
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
        return None

    store_identity = _load("store_identity.json") or {}
    materials = _load("materials.json") or {}
    results = _load("results.json") or []
    candidates = _load("candidates.json") or []
    unknowns = _load("unknowns.json") or []
    signals = _load("signals.json") or []
    promotion = _load("promotion.json")  # None when absent (run / evolve)
    gen = Generation(
        op_type=op_type,
        operation_id=manifest.get("operation_id", ""),
        parent_generation=manifest.get("parent_generation"),
        store_identity=store_identity,
        materials=materials,
        results=results,
        candidates=candidates,
        unknowns=unknowns,
        signals=signals,
        promotion=promotion,
        provider_identity=manifest.get("provider_identity", "fixture://deterministic"),
    )
    return gen.compute_gen_id()


def _assert_generation_binding(gen_dir: Path, manifest: dict, op_type: str) -> None:
    """Fail-closed dir-name <-> content-id binding (closes G2b/G3/G8).

    Recompute the content-derived generation id with the SAME function used at
    publish time (parent + op + materials + results + ledgers digests) and assert
    BOTH ``directory_name == computed_gen_id`` AND
    ``manifest["generation_id"] == computed_gen_id``. Any mismatch raises
    ``GenerationIntegrityError``.

    SCOPE: local trust model only. This is a content-addressing / crash-consistency
    check; it does NOT resist an attacker with full local store write permission
    (who can rewrite data, manifest, and directory name consistently). Cross-trust-
    boundary authenticity is borne by external Git commit, remote refetch, and
    evidence anchors.
    """
    computed = _recompute_gen_id(gen_dir, manifest, op_type)
    claimed = manifest.get("generation_id")
    if gen_dir.name != computed or claimed != computed:
        raise GenerationIntegrityError(
            f"{gen_dir}: generation binding violated "
            f"(dir={gen_dir.name!r} manifest.generation_id={claimed!r} computed={computed!r})"
        )


def _list_authoritative(gen_dir: Path) -> set[str]:
    return {p.name for p in gen_dir.glob("*.json")}


def validate_closed_manifest(gen_dir: Path, op_type: str | None = None,
                             generations_root: Path | None = None) -> dict:
    """Prove closure: declared == digest_keys == actual. Raise ManifestError on any gap."""
    manifest_path = gen_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ManifestError(f"{gen_dir}: missing manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ot = op_type or manifest["op_type"]
    required = CANON[ot]

    # Resolve the generations root so parent links are checked in the right place
    # even while staging under `.staging/<gen_id>`.
    if generations_root is None:
        if gen_dir.parent.name == ".staging":
            generations_root = gen_dir.parent.parent / "generations"
        else:
            generations_root = gen_dir.parent

    declared = set(manifest.get("required_files", []))
    digest_keys = set(manifest.get("digests", {}).keys())
    actual = _list_authoritative(gen_dir)

    # 1. declared set equals canonical required set for op type
    if declared != required:
        raise ManifestError(
            f"{gen_dir}: declared required_files {sorted(declared)} != CANON {sorted(required)}"
        )
    # 2. digest keys equal declared
    if digest_keys != declared:
        raise ManifestError(
            f"{gen_dir}: digest keys {sorted(digest_keys)} != declared {sorted(declared)}"
        )
    # 3. actual authoritative files equal declared (no missing, no extra)
    if actual != declared:
        extra = actual - declared
        missing = declared - actual
        raise ManifestError(
            f"{gen_dir}: actual files != declared; missing={sorted(missing)} extra={sorted(extra)}"
        )
    # 4. each file present and digest matches
    for name in required:
        fpath = gen_dir / name
        if not fpath.is_file():
            raise ManifestError(f"{gen_dir}: required file missing: {name}")
        import hashlib

        if name == "manifest.json":
            # Recompute self-digest from the manifest with its own entry blanked.
            m = json.loads(fpath.read_text(encoding="utf-8"))
            m2 = dict(m)
            m2["digests"] = {**m["digests"], "manifest.json": ""}
            digest = hashlib.sha256(canonical_json(m2).encode("utf-8")).hexdigest()
        else:
            digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if digest != manifest["digests"][name]:
            raise ManifestError(f"{gen_dir}: digest mismatch for {name}")
    # 5. committed + immutable
    if manifest.get("committed") is not True:
        raise ManifestError(f"{gen_dir}: manifest not committed")
    if manifest.get("immutable") is not True:
        raise ManifestError(f"{gen_dir}: manifest not immutable")
    # 6. receipt identity + parent resolution
    receipt = json.loads((gen_dir / "receipt.json").read_text(encoding="utf-8"))
    if manifest["operation_id"] != receipt.get("operation_id"):
        raise ManifestError(f"{gen_dir}: manifest.op_id != receipt.op_id")
    if manifest["op_type"] != receipt.get("op_type"):
        raise ManifestError(f"{gen_dir}: manifest.op_type != receipt.op_type")
    parent = manifest.get("parent_generation")
    if parent is not None:
        if not (generations_root / parent).is_dir():
            raise ManifestError(f"{gen_dir}: parent generation dangling: {parent}")
    # 7. finalization identity (no self final head claim)
    if receipt.get("self_final_sha_claimed") is not False:
        raise ManifestError(f"{gen_dir}: receipt must claim self_final_sha_claimed=False")
    if receipt.get("live_refetch_required") is not True:
        raise ManifestError(f"{gen_dir}: receipt must require live refetch")
    # 8. load-path content-addressing binding (closes G2b/G3/G8). Runs after the
    #    closed-manifest proof so it only executes on an otherwise-valid generation.
    _assert_generation_binding(gen_dir, manifest, ot)
    return manifest


def load_generation(gen_dir: Path, op_type: str | None = None) -> dict:
    """Strictly load a generation; validate closed manifest first."""
    validate_closed_manifest(gen_dir, op_type)
    out: dict[str, Any] = {"manifest": json.loads((gen_dir / "manifest.json").read_text(encoding="utf-8"))}
    for name in CANON[out["manifest"]["op_type"]]:
        if name == "manifest.json":
            continue
        key = name[:-5] if name.endswith(".json") else name
        out[key] = json.loads((gen_dir / name).read_text(encoding="utf-8"))
    return out
