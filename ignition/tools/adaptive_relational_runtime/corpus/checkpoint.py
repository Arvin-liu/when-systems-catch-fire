# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Checkpoint, resume, and crash-safe run state for the R3 corpus run (IGNITION §10).

Design guarantees:
  * The authoritative artifact is the per-object receipt, written ATOMICALLY
    (write ``.tmp`` then ``os.replace``). A crash mid-write never leaves a partial
    receipt; the key is absent from the checkpoint, so it is reprocessed on resume.
  * The checkpoint records only COMMITTED keys+outcomes. After a crash, the run
    state contains exclusively committed old/new outcomes — never a partial
    authoritative object.
  * Resume = all_keys - committed_keys. Idempotent: replaying a completed run
    produces no new authoritative records.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from . import schemas


def atomic_write(path: str | Path, text: str) -> None:
    """Write text to ``path`` atomically (tmp + os.replace)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, str(p))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


class Checkpoint:
    """Loads/saves a ``RunState`` and tracks committed keys idempotently."""

    def __init__(self, state_path: str | Path):
        self.state_path = Path(state_path)
        self._state: Optional[schemas.RunState] = None

    @property
    def state(self) -> Optional[schemas.RunState]:
        return self._state

    def load(self) -> Optional[schemas.RunState]:
        if self.state_path.exists():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self._state = schemas.RunState.from_dict(data)
        else:
            self._state = None
        return self._state

    def init(self, run_id: str) -> schemas.RunState:
        self._state = schemas.RunState(
            run_id=run_id,
            generation=1,
            committed_keys=[],
            outcomes={},
            shard_status={},
            checkpoint_index=0,
            state_digest="",
        )
        self._recompute_digest()
        self.save()
        return self._state

    def is_committed(self, key: str) -> bool:
        return self._state is not None and key in self._state.outcomes

    def mark_committed(self, key: str, outcome: str, shard_id: Optional[str] = None) -> None:
        if self._state is None:
            raise RuntimeError("checkpoint not initialized")
        self._state.outcomes[key] = outcome
        if key not in self._state.committed_keys:
            self._state.committed_keys.append(key)
        self._state.committed_keys.sort()
        self._state.checkpoint_index += 1
        if shard_id is not None:
            self._state.shard_status[shard_id] = "committed"
        self._recompute_digest()

    def pending_keys(self, all_keys: list[str]) -> list[str]:
        if self._state is None:
            return list(all_keys)
        committed = set(self._state.outcomes)
        return [k for k in all_keys if k not in committed]

    def _recompute_digest(self) -> None:
        if self._state is None:
            return
        payload = schemas.canonical_json(
            {
                "run_id": self._state.run_id,
                "generation": self._state.generation,
                "committed_keys": self._state.committed_keys,
                "outcomes": self._state.outcomes,
            }
        )
        self._state.state_digest = schemas.digest_of(payload)

    def save(self) -> None:
        if self._state is None:
            return
        atomic_write(self.state_path, json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2))


def crash_safe_step(checkpoint: Checkpoint, key: str, receipt_text: str, receipt_path: str | Path) -> None:
    """Persist a receipt atomically and only then record the key as committed.

    Order matters: if the process dies between the atomic write and
    ``mark_committed``, the receipt exists but the key is uncommitted, so resume
    will recompute and re-place the identical receipt (exact-once, idempotent).
    If it dies before the atomic write, no receipt and no commit — reprocessed.
    Either way no partial authoritative object survives.
    """
    atomic_write(receipt_path, receipt_text)
    checkpoint.mark_committed(key, "SUCCESS")
    checkpoint.save()
