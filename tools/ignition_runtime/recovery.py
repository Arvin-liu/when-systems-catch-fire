"""Recovery: strict re-resolution and resume after a crash.

A crash leaves either the prior complete generation (CURRENT still old) or a
new complete generation (CURRENT swapped). Orphan staging dirs are discarded;
the last fully-sealed generation is the only source of truth. Readers never
auto-bootstrap an empty ledger after damage.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .errors import PointerError
from .generation import validate_closed_manifest
from .providers.base import MaterialProvider
from .run import run
from .store import StoreLayout


def cleanup_orphans(store: StoreLayout) -> None:
    committed = {p.name for p in store.generations_dir.iterdir()} if store.generations_dir.is_dir() else set()
    # Staging orphans (never renamed into generations) are always reclaimed.
    if store.staging_dir.is_dir():
        for d in store.staging_dir.iterdir():
            if d.is_dir() and d.name not in committed:
                shutil.rmtree(d)
    # Reclaim generation dirs not reachable from CURRENT. The reachable set is
    # the parent chain from CURRENT, read TOLERANTLY (a corrupt link does not
    # abort recovery; it only stops the walk). This is conservative: when CURRENT
    # is corrupt we must NOT prune reachable committed generations.
    reachable: set[str] = set()
    try:
        token = store.read_current()
    except Exception:
        token = None
    cur = token
    while cur is not None and cur in committed:
        reachable.add(cur)
        try:
            m = json.loads((store.generations_dir / cur / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            break
        parent = m.get("parent_generation")
        cur = parent if parent is not None else None
    if token is not None:
        for d in store.generations_dir.iterdir():
            if d.is_dir() and d.name not in reachable:
                shutil.rmtree(d)


def recover(store: StoreLayout) -> str | None:
    """Strictly resolve the current generation, walking back past any corrupt
    link to the last fully-sealed (closed-manifest-valid) generation.

    Fail closed: returns None only when no committed generation is recoverable.
    """
    cleanup_orphans(store)
    try:
        token = store.read_current()
    except Exception:
        return None
    cur = token
    while cur is not None:
        gen_dir = store.generations_dir / cur
        try:
            validate_closed_manifest(gen_dir)
        except Exception:
            # corrupt link: step to its parent (if the manifest is still readable)
            try:
                m = json.loads((gen_dir / "manifest.json").read_text(encoding="utf-8"))
                cur = m.get("parent_generation")
            except Exception:
                return None
            continue
        # valid: make it current and return it
        store.swap_current(cur)
        return cur
    return None


def resume(store: StoreLayout, provider: MaterialProvider, **kwargs) -> str:
    """Resume a RUN after a crash: re-run from the established store.

    Because RUN is content-derived and atomic, a clean re-run either commits the
    pending generation (if not yet committed) or returns the already-committed
    identity (no-op)."""
    return run(store, provider, **kwargs)
