"""Atomic publish of a new immutable generation.

publish_generation is the SINGLE write path for every op type. It implements
the staging -> digest -> manifest -> fsync -> atomic rename -> atomic pointer
swap sequence. ``crash_after`` lets the test harness inject a SimulatedCrash at
a durable stage to prove old-or-new-only visibility.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ManifestError, SimulatedCrash
from .generation import (
    RUNTIME_VERSION,
    CONTRACT_VERSION,
    Generation,
    canonical_json,
    validate_closed_manifest,
)
from .hashutil import sha256_text
from .store import StoreLayout


def _fsync_file(path: Path) -> None:
    with open(path, "rb") as handle:
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _finalize_receipt(gen: Generation) -> dict:
    counts = {
        "candidates": len([c for c in gen.candidates if c.get("status") == "ACTIVE"]),
        "unknowns": len(gen.unknowns),
        "signals": len(gen.signals),
        "formal_promotions": 0,
        "auto_evolve": 0,
    }
    result_digests = [sha256_text(canonical_json(r)) for r in gen.results]
    return {
        "receipt_id": "rcpt_" + sha256_text(gen.op_type + (gen.gen_id or ""))[:32],
        "op_type": gen.op_type,
        "operation_id": gen.operation_id,
        "before_gen": gen.parent_generation,
        "after_gen": gen.gen_id,
        "material_set": sorted(gen.materials.keys()),
        "provider_identity": gen.provider_identity,
        "counts": counts,
        "result_digests": result_digests,
        "op_outcome": "COMMITTED",
        "timestamps": {"start": None, "end": None},
        "self_final_sha_claimed": False,
        "live_refetch_required": True,
    }


def _build_audit_index(store: StoreLayout, gen: Generation) -> list:
    parent_entry = []
    if gen.parent_generation:
        parent_dir = store.generations_dir / gen.parent_generation
        try:
            parent_entry = json.loads(
                (parent_dir / "audit_index.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            parent_entry = []
    entry = {
        "gen_id": gen.gen_id,
        "op_id": gen.operation_id,
        "op_type": gen.op_type,
        "checksum": sha256_text(canonical_json(gen.core_payload())),
        "ts": None,
    }
    return parent_entry + [entry]


def publish_generation(
    store: StoreLayout,
    gen: Generation,
    *,
    crash_after: str = "none",
    authorized_by: str = "",
) -> str:
    """Publish ``gen`` as a new immutable generation. Returns the gen id.

    crash_after in {none, write_files, manifest, staged, swap}.
    """
    if crash_after not in ("none", "write_files", "manifest", "staged", "renamed", "swap"):
        raise ValueError(f"invalid crash_after: {crash_after}")

    # 1. identity (content-derived; parent included)
    if not gen.operation_id:
        gen.operation_id = gen.compute_operation_id(authorized_by)
    gen.gen_id = gen.compute_gen_id()

    # Idempotency: identical content already committed -> logical no-op.
    existing = store.generations_dir / gen.gen_id
    if existing.is_dir():
        try:
            validate_closed_manifest(existing)
            # Ensure CURRENT points at the already-committed generation.
            store.swap_current(gen.gen_id)
            return gen.gen_id
        except (ManifestError, OSError):
            pass  # corrupt twin: overwrite with a fresh copy below

    staging = store.staging_dir / gen.gen_id
    if staging.exists():
        import shutil

        shutil.rmtree(staging)

    # 2. stage all data files (except manifest) into staging
    staging.mkdir(parents=True, exist_ok=True)
    if crash_after == "write_files":
        raise SimulatedCrash("crash before any RUN file was written")

    # write_files writes all ledger files (manifest is NOT part of that set);
    # the receipt/audit_index it writes are placeholders (None/[]) overwritten below.
    digests = gen.write_files(staging)

    if crash_after == "manifest":
        raise SimulatedCrash("crash after data files, before manifest")

    # 3. finalize receipt, audit index, manifest
    gen.receipt = _finalize_receipt(gen)
    (staging / "receipt.json").write_text(
        canonical_json(gen.receipt), encoding="utf-8"
    )
    digests["receipt.json"] = sha256_text(canonical_json(gen.receipt))
    gen.audit_index = _build_audit_index(store, gen)
    (staging / "audit_index.json").write_text(
        canonical_json(gen.audit_index), encoding="utf-8"
    )
    digests["audit_index.json"] = sha256_text(canonical_json(gen.audit_index))
    manifest = gen.write_manifest(staging, digests)
    validate_closed_manifest(staging, gen.op_type, generations_root=store.generations_dir)  # closed-manifest proof

    # 4. fsync every staged file + staging dir
    for f in sorted(staging.iterdir()):
        _fsync_file(f)
    _fsync_dir(staging)

    if crash_after == "staged":
        raise SimulatedCrash("crash after staged gen complete, before pointer swap")

    # 5. atomic rename staging -> generations/<gen_id>
    os.replace(str(staging), str(store.generations_dir / gen.gen_id))
    _fsync_dir(store.generations_dir)

    if crash_after == "renamed":
        raise SimulatedCrash("crash after rename, before pointer swap (old still visible)")

    # 6. atomic pointer swap (FINAL durable step)
    store.swap_current(gen.gen_id)
    _fsync_dir(store.root)

    if crash_after == "swap":
        raise SimulatedCrash("crash after pointer swap (new gen fully present)")

    return gen.gen_id
