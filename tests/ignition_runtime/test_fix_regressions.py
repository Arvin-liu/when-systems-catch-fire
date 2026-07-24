"""One-time fix regressions for agent F (G2b/G3/G8 binding; H B1/W2).

Closes:
- G2b/G3/G8: dir-name <-> content-id binding fails closed on load (rename, or a
  consistent rewritten data+manifest that no longer matches the directory name).
- H B1: provider-identity incoherence now fails closed for ALL schemes
  (incl. fixture://), not just upload://.
- H W2: beyond-ceiling guard normalized (NFKC + alnum-only) before substring match.

Run with:  python3 -m pytest tests/ignition_runtime -q
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from tools.ignition_runtime import errors
from tools.ignition_runtime.epistemic import is_beyond_ceiling
from tools.ignition_runtime.generation import canonical_json, load_generation
from tools.ignition_runtime.hashutil import sha256_text
from tools.ignition_runtime.providers import FixtureProvider
from tools.ignition_runtime.providers.base import MaterialProvider
from tools.ignition_runtime.run import run
from tools.ignition_runtime.store import StoreLayout


def new_store() -> StoreLayout:
    return StoreLayout(Path(tempfile.mkdtemp()))


def _rewrite_manifest_consistently(gen_dir: Path, manifest: dict) -> None:
    """Rewrite a manifest with a consistent self-digest (the forger's move)."""
    m2 = dict(manifest)
    m2["digests"] = {**manifest["digests"], "manifest.json": ""}
    self_digest = hashlib.sha256(canonical_json(m2).encode("utf-8")).hexdigest()
    manifest["digests"]["manifest.json"] = self_digest
    (gen_dir / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")


# --------------------------------------------------------------------------
# Fix (1) G2b/G3/G8 — dir-name <-> content-id binding fails closed
# --------------------------------------------------------------------------
def test_fix_load_binding_renamed_dir_fails_closed():
    """Renaming a committed gen dir away from its content id must fail closed."""
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    gdir = store.generations_dir / gid
    new_dir = store.generations_dir / ("gen_" + "0" * 31 + "1")
    gdir.rename(new_dir)
    with pytest.raises(errors.GenerationIntegrityError):
        load_generation(new_dir)


def test_fix_load_binding_rewritten_manifest_fails_closed():
    """A consistent forger (data + manifest digests) still fails the binding
    because the directory name / manifest.generation_id no longer match the
    content-derived id."""
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    cands = json.loads((gdir / "candidates.json").read_text(encoding="utf-8"))
    cands.append(
        {
            "candidate_id": "x",
            "semantic_id": "sid_test_forge",
            "claim_text": "p",
            "source_sha256": "0" * 64,
            "source_tier": "PRIMARY_REPORT",
            "claim_ceiling": "PRIMARY_VERIFIED",
            "status": "ACTIVE",
            "material_id": "M1",
            "first_seen_gen": gid,
            "archived_at": None,
            "archived_gen": None,
        }
    )
    (gdir / "candidates.json").write_text(canonical_json(cands), encoding="utf-8")
    manifest = json.loads((gdir / "manifest.json").read_text(encoding="utf-8"))
    manifest["digests"]["candidates.json"] = sha256_text(canonical_json(cands))
    _rewrite_manifest_consistently(gdir, manifest)  # self-consistent forger
    with pytest.raises(errors.GenerationIntegrityError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# Fix (2) H B1 — provider-identity incoherence fails closed for fixture scheme
# --------------------------------------------------------------------------
class _EvilIdentityProvider(FixtureProvider):
    def provider_identity(self) -> str:
        # Incoherent with the fixture:// material provider_ids, and NOT
        # prefix-coherent (upload:// vs fixture://). Must now fail closed.
        return "upload://evil-attacker"


def test_fix_provider_identity_incoherence_fixture_fails_closed():
    store = new_store()
    with pytest.raises(errors.EpistemicError):
        run(store, _EvilIdentityProvider(refs=["M1", "M2", "M3", "M4"]))


# --------------------------------------------------------------------------
# Fix (3) H W2 — beyond-ceiling normalization (HEURISTIC guard, not classifier)
# --------------------------------------------------------------------------
def test_fix_beyond_ceiling_normalization():
    # spacing / punctuation obfuscations are now caught (NFKC + alnum-only)
    assert is_beyond_ceiling("the root   cure is here")  # original hyphen/space split missed
    assert is_beyond_ceiling("a state of the art approach")  # hyphen -> spaces
    assert is_beyond_ceiling("achieves SOTA on the benchmark")
    # character-set substitution (leetspeak) is a documented HEURISTIC miss
    assert not is_beyond_ceiling("r00t cure applied")
    # nominal claim is not flagged
    assert not is_beyond_ceiling("the system catches fire on thermal runaway")
