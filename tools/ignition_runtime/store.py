"""Strict pointer (CURRENT) and store bootstrap.

Fail-closed rules (C durable-state architecture §3):
- CURRENT is a regular file (O_NOFOLLOW), one safe token, no traversal.
- A genuinely empty store may bootstrap exactly once.
- An established store with a damaged pointer FAILS CLOSED; readers never
  silently initialize an empty ledger.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from .errors import PointerError, SimulatedCrash
from .generation import (
    CANON,
    Generation,
    canonical_json,
    validate_closed_manifest,
)
from .hashutil import (
    assert_under_root,
    is_safe_token,
    safe_open_nofollow,
    sha256_text,
)


class StoreLayout:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.current_file = self.root / "CURRENT"
        self.generations_dir = self.root / "generations"
        self.staging_dir = self.root / ".staging"
        self.root.mkdir(parents=True, exist_ok=True)
        self.generations_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    # --- emptiness / bootstrap eligibility -----------------------------
    def is_genuinely_empty(self) -> bool:
        no_current = not self.current_file.exists()
        gens = self.generations_dir
        empty_gens = not gens.exists() or not any(gens.iterdir())
        return no_current and empty_gens

    # --- strict pointer read -------------------------------------------
    def read_current(self) -> str | None:
        """Return the active gen id, or None if the store is genuinely empty.

        Any corruption on an established store raises PointerError (fail closed).
        """
        if not self.current_file.exists():
            if self.is_genuinely_empty():
                return None
            raise PointerError("CURRENT missing on established store")
        # Reject symlink / traversal via O_NOFOLLOW.
        try:
            fd = safe_open_nofollow(self.current_file, os.O_RDONLY)
        except OSError as exc:
            raise PointerError(f"CURRENT is a symlink or unreadable: {exc}") from exc
        try:
            raw = os.read(fd, 4096)
        finally:
            os.close(fd)
        text = raw.decode("utf-8", "replace")
        # multiline / embedded newline in the middle => reject
        if "\n" in text.strip("\n"):
            raise PointerError("CURRENT contains multiple lines")
        token = text.strip()
        if token == "":
            raise PointerError("CURRENT is empty")
        if not is_safe_token(token):
            raise PointerError(f"CURRENT token is not safe: {token!r}")
        # dangling reference => fail closed
        gen_dir = self.generations_dir / token
        if not gen_dir.is_dir():
            raise PointerError(f"CURRENT points to nonexistent generation: {token}")
        return token

    # --- strict pointer write (atomic swap) ----------------------------
    def swap_current(self, gen_id: str) -> None:
        tmp = self.root / "CURRENT.tmp"
        tmp.write_text(gen_id + "\n", encoding="utf-8")
        os.replace(str(tmp), str(self.current_file))

    # --- resolution -----------------------------------------------------
    def resolve_current_gen(self) -> Path | None:
        """Resolve the current generation directory, or None if empty store.

        Established-store pointer damage raises PointerError. The resolved
        generation is validated via the closed manifest (all corruption fails
        closed)."""
        gen_id = self.read_current()
        if gen_id is None:
            return None
        gen_dir = self.generations_dir / gen_id
        validate_closed_manifest(gen_dir)  # raises ManifestError / PointerError
        return gen_dir

    # --- bootstrap (once only) -----------------------------------------
    def bootstrap(self) -> str:
        if not self.is_genuinely_empty():
            raise PointerError("refusing to bootstrap a non-empty store")
        store_identity = {
            "store_id": str(uuid.uuid4()),
            "schema_version": "ignition_runtime/1.0.0",
        }
        gen = Generation(
            op_type="bootstrap",
            operation_id="op_" + sha256_text("bootstrap")[:32],
            parent_generation=None,
            store_identity=store_identity,
            provider_identity="fixture://deterministic",
            timestamps={"observed_at": None, "published_at": None},
        )
        gen.gen_id = gen.compute_gen_id()
        gen.receipt = _bootstrap_receipt(gen.gen_id, store_identity)
        gen.audit_index = [
            {
                "gen_id": gen.gen_id,
                "op_id": gen.operation_id,
                "op_type": "bootstrap",
                "checksum": _gen_checksum("bootstrap", gen.gen_id),
                "ts": None,
            }
        ]
        gen_dir = self.generations_dir / gen.gen_id
        digests = gen.write_files(gen_dir)
        gen.write_manifest(gen_dir, digests)
        validate_closed_manifest(gen_dir)
        self.swap_current(gen.gen_id)
        return gen.gen_id


def _bootstrap_receipt(gen_id: str, store_identity: dict) -> dict:
    from .generation import RUNTIME_VERSION, CONTRACT_VERSION

    return {
        "receipt_id": "rcpt_" + sha256_text("bootstrap-receipt-" + gen_id)[:32],
        "op_type": "bootstrap",
        "operation_id": "op_" + sha256_text("bootstrap")[:32],
        "before_gen": None,
        "after_gen": gen_id,
        "material_set": [],
        "provider_identity": "fixture://deterministic",
        "counts": {
            "candidates": 0,
            "unknowns": 0,
            "signals": 0,
            "formal_promotions": 0,
            "auto_evolve": 0,
        },
        "result_digests": [],
        "op_outcome": "COMMITTED",
        "timestamps": {"start": None, "end": None},
        "self_final_sha_claimed": False,
        "live_refetch_required": True,
    }


def _gen_checksum(op_type: str, gen_id: str) -> str:
    return sha256_text(canonical_json({"op": op_type, "gen": gen_id}))
