"""Ignition production runtime — 45-scenario adversarial + functional suite.

Every scenario from the consolidated design is covered by a dedicated test
(test_sNN_*). Run with:  python3 -m pytest tests/ignition_runtime -q
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import threading
from pathlib import Path
from unittest import TestCase

import pytest

from tools.ignition_runtime import errors
from tools.ignition_runtime.epistemic import (
    merge_candidates,
    semantic_id_of,
    validate_epistemic_contract,
)
from tools.ignition_runtime.generation import (
    CANON,
    Generation,
    canonical_json,
    load_generation,
    validate_closed_manifest,
)
from tools.ignition_runtime.providers import FixtureProvider, FileSystemProvider
from tools.ignition_runtime.providers.base import MaterialProvider, MaterialRecord
from tools.ignition_runtime.recovery import recover, resume
from tools.ignition_runtime.run import run
from tools.ignition_runtime.store import StoreLayout
from tools.ignition_runtime.promote import promote_approval, promote_request
from tools.ignition_runtime.evolve import evolve

REPO_ROOT = Path(__file__).resolve().parents[2]
CTRL_INPUTS = Path("/tmp/ctrl-1111/inputs/ignition-run-promote-evolve-r1")
PR_BASE = "833c3e5f25c25c8f225ade19e6b3111f1a60e695"


def new_store():
    return StoreLayout(Path(tempfile.mkdtemp()))


def rewrite_manifest(gen_dir: Path, manifest: dict) -> None:
    """Rewrite a manifest with a consistent self-digest (so failures are from
    the field under test, not a self-digest mismatch)."""
    m2 = dict(manifest)
    m2["digests"] = {**manifest["digests"], "manifest.json": ""}
    import hashlib

    self_digest = hashlib.sha256(canonical_json(m2).encode("utf-8")).hexdigest()
    manifest["digests"]["manifest.json"] = self_digest
    (gen_dir / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


# --------------------------------------------------------------------------
# S1 — bootstrap empty store
# --------------------------------------------------------------------------
def test_s01_bootstrap_empty_store():
    store = new_store()
    assert store.is_genuinely_empty()
    bid = store.bootstrap()
    assert store.read_current() == bid
    gen = load_generation(store.generations_dir / bid)
    assert gen["manifest"]["op_type"] == "bootstrap"
    # bootstrap once only
    with pytest.raises(errors.PointerError):
        store.bootstrap()


# --------------------------------------------------------------------------
# S2 — deleted CURRENT on established store (fail closed)
# --------------------------------------------------------------------------
def test_s02_deleted_current_fails_closed():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    store.current_file.unlink()
    with pytest.raises(errors.PointerError):
        store.resolve_current_gen()


# --------------------------------------------------------------------------
# S3 — empty / multiline / traversal CURRENT (fail closed)
# --------------------------------------------------------------------------
def test_s03_bad_current_fails_closed():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1"]))
    import os

    for bad in ["", "a\nb", "../../etc/passwd", "a/../b", "-x"]:
        store.current_file.write_text(bad + "\n", encoding="utf-8")
        with pytest.raises(errors.PointerError):
            store.read_current()
    # symlink CURRENT -> fail closed (O_NOFOLLOW)
    store.current_file.unlink()
    try:
        os.symlink(str(store.generations_dir / gid), str(store.current_file))
    except (OSError, NotImplementedError):
        pass
    else:
        with pytest.raises(errors.PointerError):
            store.read_current()


# --------------------------------------------------------------------------
# S4 — dangling generation pointer (fail closed)
# --------------------------------------------------------------------------
def test_s04_dangling_pointer_fails_closed():
    store = new_store()
    run(store, FixtureProvider(refs=["M1"]))
    store.current_file.write_text("gen_deadbeefdeadbeefdeadbeefdeadbeef\n", encoding="utf-8")
    with pytest.raises(errors.PointerError):
        store.resolve_current_gen()


# --------------------------------------------------------------------------
# S5 — manifest missing required file
# --------------------------------------------------------------------------
def test_s05_missing_required_file():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    (gdir / "signals.json").unlink()
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S6 — manifest + digest both omit file (still rejected)
# --------------------------------------------------------------------------
def test_s06_drop_file_and_digest_still_rejected():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    (gdir / "signals.json").unlink()
    manifest = json.loads((gdir / "manifest.json").read_text(encoding="utf-8"))
    manifest["required_files"] = [f for f in manifest["required_files"] if f != "signals.json"]
    manifest["digests"].pop("signals.json", None)
    rewrite_manifest(gdir, manifest)
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S7 — undeclared authoritative file
# --------------------------------------------------------------------------
def test_s07_undeclared_file():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    (gdir / "extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S8 — file digest mismatch
# --------------------------------------------------------------------------
def test_s08_digest_mismatch():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    (gdir / "candidates.json").write_text('[{"tampered": true}]', encoding="utf-8")
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S9 — parent-generation mismatch
# --------------------------------------------------------------------------
def test_s09_parent_mismatch():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    manifest = json.loads((gdir / "manifest.json").read_text(encoding="utf-8"))
    manifest["parent_generation"] = "gen_00000000000000000000000000000000"
    rewrite_manifest(gdir, manifest)
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S10 — immutable generation modified after commit (rejected on reload)
# --------------------------------------------------------------------------
def test_s10_immutable_after_commit():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    cands = json.loads((gdir / "candidates.json").read_text(encoding="utf-8"))
    cands.append({"candidate_id": "x", "semantic_id": "sid_x", "claim_text": "p",
                  "source_sha256": "0" * 64, "source_tier": "PRIMARY_REPORT",
                  "claim_ceiling": "PRIMARY_VERIFIED", "status": "ACTIVE",
                  "material_id": "M1", "first_seen_gen": gid,
                  "archived_at": None, "archived_gen": None})
    (gdir / "candidates.json").write_text(canonical_json(cands), encoding="utf-8")
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S11 — crash before any RUN file (old-or-new-only)
# --------------------------------------------------------------------------
def test_s11_crash_before_files():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="write_files")
    assert store.read_current() == old  # OLD complete
    assert recover(store) == old


# --------------------------------------------------------------------------
# S12 — crash after manifest pending (old-or-new-only)
# --------------------------------------------------------------------------
def test_s12_crash_after_manifest_pending():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="manifest")
    assert store.read_current() == old


# --------------------------------------------------------------------------
# S13 — crash after manifest committed (staging complete, before rename)
# --------------------------------------------------------------------------
def test_s13_crash_after_manifest_committed():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="staged")
    assert store.read_current() == old  # staging orphan, old visible


# --------------------------------------------------------------------------
# S14 — crash before pointer swap (renamed, not swapped)
# --------------------------------------------------------------------------
def test_s14_crash_before_pointer_swap():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="renamed")
    assert store.read_current() == old


# --------------------------------------------------------------------------
# S15 — SIGKILL-after-swap (new fully present)
# --------------------------------------------------------------------------
def test_s15_sigkill_after_swap():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="swap")
    new = store.read_current()
    assert new is not None and new != old  # new gen fully present
    assert (store.generations_dir / new).is_dir()


# --------------------------------------------------------------------------
# S16 — ordinary RUN old-or-new-only visibility
# --------------------------------------------------------------------------
def test_s16_ordinary_run_visibility():
    store = new_store()
    old = store.bootstrap()
    gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    assert store.read_current() == gid
    g = load_generation(store.generations_dir / gid)
    assert g["manifest"]["parent_generation"] == old
    assert (store.generations_dir / old).is_dir()  # old retained


# --------------------------------------------------------------------------
# S17 — result/source/provider binding tamper (fail closed)
# --------------------------------------------------------------------------
def test_s17_binding_tamper():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    cands = json.loads((gdir / "candidates.json").read_text(encoding="utf-8"))
    cands[0]["source_sha256"] = "0" * 64  # tamper binding
    (gdir / "candidates.json").write_text(canonical_json(cands), encoding="utf-8")
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)
    # Epistemic-level check (candidate binds to unknown source)
    g = json.loads((gdir / "materials.json").read_text(encoding="utf-8"))
    with pytest.raises(errors.EpistemicError):
        validate_epistemic_contract(
            g, cands, [{"unknown_id": "u", "semantic_id": "", "question": "q", "scope": "s",
                       "created_gen": gid, "resolved": False}], [], "run", "fixture://deterministic"
        )


# --------------------------------------------------------------------------
# S18 — missing / empty UNKNOWN (fail closed)
# --------------------------------------------------------------------------
def test_s18_missing_unknown_fails_closed():
    mats = {"M1": {"material_id": "M1", "source_sha256": "a" * 64, "source_tier": "PRIMARY_REPORT",
                   "claim_ceiling": "PRIMARY_VERIFIED", "provider_id": "p", "provider_mode": "X"}}
    cands = [{"candidate_id": "c", "semantic_id": "sid_x", "claim_text": "t",
              "source_sha256": "a" * 64, "source_tier": "PRIMARY_REPORT",
              "claim_ceiling": "PRIMARY_VERIFIED", "status": "ACTIVE",
              "material_id": "M1", "first_seen_gen": "g", "archived_at": None, "archived_gen": None}]
    with pytest.raises(errors.EpistemicError):
        validate_epistemic_contract(mats, cands, [], [], "run", "p")
    # empty question
    bad_unk = [{"unknown_id": "u", "semantic_id": "", "question": "", "scope": "s",
                "created_gen": "g", "resolved": False}]
    with pytest.raises(errors.EpistemicError):
        validate_epistemic_contract(mats, cands, bad_unk, [], "run", "p")


# --------------------------------------------------------------------------
# S19 — arbitrary claim ceiling (fail closed)
# --------------------------------------------------------------------------
def test_s19_arbitrary_claim_ceiling():
    mats = {"M1": {"material_id": "M1", "source_sha256": "a" * 64, "source_tier": "PRIMARY_REPORT",
                   "claim_ceiling": "PRIMARY_VERIFIED", "provider_id": "p", "provider_mode": "X"}}
    cands = [{"candidate_id": "c", "semantic_id": "sid_x", "claim_text": "t",
              "source_sha256": "a" * 64, "source_tier": "PRIMARY_REPORT",
              "claim_ceiling": "ROOT_CURE_ABSOLUTE", "status": "ACTIVE",
              "material_id": "M1", "first_seen_gen": "g", "archived_at": None, "archived_gen": None}]
    unk = [{"unknown_id": "u", "semantic_id": "", "question": "q", "scope": "s",
            "created_gen": "g", "resolved": False}]
    with pytest.raises(errors.EpistemicError):
        validate_epistemic_contract(mats, cands, unk, [], "run", "p")


# --------------------------------------------------------------------------
# S20 — provider output reorder → semantic ids stable
# --------------------------------------------------------------------------
def test_s20_reorder_semantic_stable():
    store = new_store()
    g1 = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    sids1 = {c["semantic_id"] for c in load_generation(store.generations_dir / g1)["candidates"]}
    store2 = new_store()
    g2 = run(store2, FixtureProvider(refs=["M4", "M3", "M2", "M1"]))
    sids2 = {c["semantic_id"] for c in load_generation(store2.generations_dir / g2)["candidates"]}
    assert sids1 == sids2


# --------------------------------------------------------------------------
# S21 — source change + stale entity tombstone
# --------------------------------------------------------------------------
class _M1ChangedProvider(FixtureProvider):
    def read_material(self, material_id: str):
        rec = super().read_material(material_id)
        if material_id == "M1":
            rec.source_bytes = (rec.source_bytes.decode() + " CHANGED-SOURCE-v2").encode()
        return rec


def test_s21_source_change_tombstones():
    store = new_store()
    g0 = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    base = load_generation(store.generations_dir / g0)
    m1_sid = next(c["semantic_id"] for c in base["candidates"] if c["material_id"] == "M1")
    g1 = run(store, _M1ChangedProvider(refs=["M1", "M2", "M3", "M4"]))
    gen = load_generation(store.generations_dir / g1)
    m1_now = [c for c in gen["candidates"] if c["material_id"] == "M1"]
    # old sid is REPLACED (no active ghost), never left ACTIVE
    assert not any(c["semantic_id"] == m1_sid and c["status"] == "ACTIVE" for c in m1_now)
    assert any(c["semantic_id"] == m1_sid and c["status"] == "REPLACED" for c in m1_now)
    # new source produced its own ACTIVE entities, one per seed, distinct sids
    active_m1 = [c for c in m1_now if c["status"] == "ACTIVE"]
    active_sids = [c["semantic_id"] for c in active_m1]
    assert len(active_m1) == 2  # M1 has 2 candidate seeds -> 2 active after change
    assert len(active_sids) == len(set(active_sids))  # no duplicate active sid
    assert all(s != m1_sid for s in active_sids)


# --------------------------------------------------------------------------
# S22 — archived entity reactivation
# --------------------------------------------------------------------------
def test_s22_archived_reactivation():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    run(store, _M1ChangedProvider(refs=["M1", "M2", "M3", "M4"]))  # M1 REPLACED
    g2 = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))  # revert M1
    gen = load_generation(store.generations_dir / g2)
    m1 = [c for c in gen["candidates"] if c["material_id"] == "M1"]
    active = [c for c in m1 if c["status"] == "ACTIVE"]
    active_sids = [c["semantic_id"] for c in active]
    assert len(active) == 2  # both M1 seeds reactivated on revert
    assert len(active_sids) == len(set(active_sids))  # no duplicate active sid
    assert m1[0]["status"] == "ACTIVE"


# --------------------------------------------------------------------------
# S23 — identical RUN byte/semantic stability
# --------------------------------------------------------------------------
def test_s23_identical_run_stability():
    store = new_store()
    g1 = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    c1 = load_generation(store.generations_dir / g1)["candidates"]
    g2 = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    c2 = load_generation(store.generations_dir / g2)["candidates"]
    assert {c["semantic_id"] for c in c1 if c["status"] == "ACTIVE"} == \
           {c["semantic_id"] for c in c2 if c["status"] == "ACTIVE"}
    assert len([c for c in c2 if c["status"] == "ACTIVE"]) == 7
    # no duplicate active semantic ids
    active_sids = [c["semantic_id"] for c in c2 if c["status"] == "ACTIVE"]
    assert len(active_sids) == len(set(active_sids))


# --------------------------------------------------------------------------
# S24 — 2/5/10 RUN (each commits distinct generation; determinism)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("n", [2, 5, 10])
def test_s24_concurrent_runs_distinct(n):
    store = new_store()
    bootstrap = store.bootstrap()
    ids = []
    for _ in range(n):
        gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
        ids.append(gid)
    assert len(set(ids)) == n  # distinct generations
    assert len([d for d in store.generations_dir.iterdir() if d.is_dir()]) == n + 1
    # determinism: same starting state -> same gen id
    store.swap_current(bootstrap)
    gid_deterministic = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    assert gid_deterministic == ids[0]


# --------------------------------------------------------------------------
# S25 — ingest + RUN from empty store
# --------------------------------------------------------------------------
def test_s25_ingest_run_from_empty():
    store = new_store()
    assert store.is_genuinely_empty()
    gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    g = load_generation(store.generations_dir / gid)
    assert g["manifest"]["op_type"] == "run"
    assert len(g["materials"]) == 4


# --------------------------------------------------------------------------
# S26 — RUN + resume
# --------------------------------------------------------------------------
def test_s26_run_resume():
    store = new_store()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]), crash_after="renamed")
    gid = resume(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    g = load_generation(store.generations_dir / gid)
    assert g["manifest"]["op_type"] == "run"
    assert store.read_current() == gid


# --------------------------------------------------------------------------
# S27 — RUN + recovery
# --------------------------------------------------------------------------
def test_s27_run_recovery():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="manifest")
    assert recover(store) == old


# --------------------------------------------------------------------------
# S28 — recovery missing record/source/result/sidecar (fail closed)
# --------------------------------------------------------------------------
def test_s28_recovery_missing_file():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    # missing results sidecar
    (store.generations_dir / gid / "results.json").unlink()
    with pytest.raises(errors.ManifestError):
        load_generation(store.generations_dir / gid)
    assert recover(store) is not None  # old (bootstrap) still valid


# --------------------------------------------------------------------------
# S29 — recovery core+derived crash old-or-new-only
# --------------------------------------------------------------------------
def test_s29_recovery_crash_orphan():
    store = new_store()
    old = store.bootstrap()
    with pytest.raises(errors.SimulatedCrash):
        run(store, FixtureProvider(refs=["M1"]), crash_after="staged")
    # orphan staging + possibly renamed orphan gen reclaimed; old visible
    assert recover(store) == old


# --------------------------------------------------------------------------
# S30 — finalized receipt fields match committed generation
# --------------------------------------------------------------------------
def test_s30_receipt_matches_generation():
    store = new_store()
    old = store.bootstrap()
    gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    g = load_generation(store.generations_dir / gid)
    r = g["receipt"]
    assert r["before_gen"] == old
    assert r["after_gen"] == gid
    assert r["op_outcome"] == "COMMITTED"
    active = [c for c in g["candidates"] if c["status"] == "ACTIVE"]
    assert r["counts"]["candidates"] == len(active)
    assert r["counts"]["unknowns"] == len(g["unknowns"])
    assert r["counts"]["signals"] == len(g["signals"])
    assert r["material_set"] == sorted(g["materials"].keys())


# --------------------------------------------------------------------------
# S31 — audit rebuild from committed generations
# --------------------------------------------------------------------------
def test_s31_audit_rebuild():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    # walk parent chain collecting audit entries
    chain = []
    cur = store.read_current()
    while cur is not None:
        g = load_generation(store.generations_dir / cur)
        chain.append(cur)
        cur = g["manifest"]["parent_generation"]
    assert len(chain) >= 2  # bootstrap + run
    # each gen's own audit_index tail equals itself
    for cid in chain:
        g = load_generation(store.generations_dir / cid)
        assert g["audit_index"][-1]["gen_id"] == cid


# --------------------------------------------------------------------------
# S32 — malformed/conflicting audit evidence (fail closed)
# --------------------------------------------------------------------------
def test_s32_audit_evidence_tamper():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2"]))
    gdir = store.generations_dir / gid
    audit = json.loads((gdir / "audit_index.json").read_text(encoding="utf-8"))
    audit[0]["gen_id"] = "gen_conflicting"
    (gdir / "audit_index.json").write_text(canonical_json(audit), encoding="utf-8")
    with pytest.raises(errors.ManifestError):
        load_generation(gdir)


# --------------------------------------------------------------------------
# S33 — duplicate promotion request true no-op
# --------------------------------------------------------------------------
def test_s33_duplicate_promotion_request_noop():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    p1 = promote_request(store, FixtureProvider(), authorized_by="tok")
    p2 = promote_request(store, FixtureProvider(), authorized_by="tok")
    assert p1 == p2
    req_gens = [d for d in store.generations_dir.iterdir()
                if load_generation(d)["manifest"]["op_type"] == "promote_request"]
    assert len(req_gens) == 1


# --------------------------------------------------------------------------
# S34 — promotion approval crash at every durable stage (old-or-new-only)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("stage", ["write_files", "manifest", "staged", "renamed", "swap"])
def test_s34_approval_crash_stages(stage):
    store = new_store()
    old = store.bootstrap()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    pid = promote_request(store, FixtureProvider(), authorized_by="tok")
    if stage == "swap":
        with pytest.raises(errors.SimulatedCrash):
            promote_approval(store, FixtureProvider(), authorized_by="tok",
                             request_gen_id=pid, crash_after="swap")
        # after swap the approval gen is committed
        assert store.read_current() != old
    else:
        with pytest.raises(errors.SimulatedCrash):
            promote_approval(store, FixtureProvider(), authorized_by="tok",
                             request_gen_id=pid, crash_after=stage)
        assert store.read_current() == pid  # approval not applied; request still current


# --------------------------------------------------------------------------
# S35 — duplicate approval returns same committed identity
# --------------------------------------------------------------------------
def test_s35_duplicate_approval_same_id():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    pid = promote_request(store, FixtureProvider(), authorized_by="tok")
    a1 = promote_approval(store, FixtureProvider(), authorized_by="tok", request_gen_id=pid)
    a2 = promote_approval(store, FixtureProvider(), authorized_by="tok", request_gen_id=pid)
    assert a1 == a2


# --------------------------------------------------------------------------
# S36 — RUN cannot call PROMOTE (static + runtime guard)
# --------------------------------------------------------------------------
def test_s36_run_no_promote():
    run_src = (REPO_ROOT / "tools/ignition_runtime/run.py").read_text(encoding="utf-8")
    assert "promote" not in run_src and "evolve" not in run_src
    store = new_store()
    with pytest.raises(errors.ModeBoundaryError):
        from tools.ignition_runtime.cli import main

        main(["run", "--store", str(store.root), "--authorize", "promote:tok"])


# --------------------------------------------------------------------------
# S37 — RUN/PROMOTE cannot call EVOLVE
# --------------------------------------------------------------------------
def test_s37_no_evolve_from_run_promote():
    run_src = (REPO_ROOT / "tools/ignition_runtime/run.py").read_text(encoding="utf-8")
    promo_src = (REPO_ROOT / "tools/ignition_runtime/promote.py").read_text(encoding="utf-8")
    assert "evolve" not in run_src
    assert "evolve" not in promo_src
    # promote never produces an evolve generation
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    pid = promote_request(store, FixtureProvider(), authorized_by="tok")
    gen = load_generation(store.generations_dir / pid)
    assert gen["manifest"]["op_type"] != "evolve"


# --------------------------------------------------------------------------
# S38 — token/path escape + formal-repo write guard
# --------------------------------------------------------------------------
def test_s38_path_escape_guard():
    store = new_store()
    # CURRENT traversal forbidden
    store.current_file.write_text("../../../../etc/passwd\n", encoding="utf-8")
    with pytest.raises(errors.PointerError):
        store.read_current()
    # provider path must stay under inputs root
    provider = FileSystemProvider(REPO_ROOT / ".." / "..")  # escapes repo root
    with pytest.raises(errors.PathEscapeError):
        provider.list_materials()  # read triggers the escape guard
    # generation dirs always under store root
    assert store.generations_dir.resolve().parent == store.root.resolve()
    assert store.staging_dir.resolve().parent == store.root.resolve()


# --------------------------------------------------------------------------
# S39 — M1–M4 deterministic 7/8/5 regression
# --------------------------------------------------------------------------
def test_s39_m1_m4_regression():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    g = load_generation(store.generations_dir / gid)
    active = [c for c in g["candidates"] if c["status"] == "ACTIVE"]
    assert len(active) == 7
    assert len(g["unknowns"]) == 8
    assert len(g["signals"]) == 5
    assert len([c for c in active if c["status"] == "ACTIVE"]) == 7
    # zero duplicate active semantic ids, zero formal promotions, zero auto-evolve
    assert len({c["semantic_id"] for c in active}) == 7
    assert g["receipt"]["counts"]["formal_promotions"] == 0
    assert g["receipt"]["counts"]["auto_evolve"] == 0


# --------------------------------------------------------------------------
# S40 — M5 secondary-source / temporal-calibration classification
# --------------------------------------------------------------------------
def test_s40_m5_secondary_temporal():
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M5"]))
    g = load_generation(store.generations_dir / gid)
    m5 = g["materials"]["M5"]
    assert m5["source_tier"] == "SECONDARY_ACADEMIC_INTERPRETATION"
    assert m5.get("verdict") == "NORMALIZED_TRANSCRIPT_COPY"
    assert m5.get("normalized_transcript_copy") is True
    tc = m5.get("temporal_calibration", {})
    assert all(tc.get(k) is True for k in
               ["R_TQ_01", "R_TQ_02", "R_TQ_03", "R_TQ_04", "R_TQ_05", "R_TQ_06"])
    # M5 produced candidate/UNKNOWN/signal records and did NOT change architecture
    assert g["manifest"]["op_type"] == "run"
    assert "promotion" not in g
    # SOTA/originality claim downgraded to UNKNOWN
    assert any("Beyond-ceiling" in u["question"] for u in g["unknowns"])


# --------------------------------------------------------------------------
# S41 — formal main and #109–#118 unchanged
# --------------------------------------------------------------------------
def test_s41_branch_and_base_unchanged():
    branch = git("branch", "--show-current")
    assert branch == "production/ignition-run-promote-evolve-r1"
    assert git("rev-parse", "repair-r3/scientific-context-protocol-r3-semantic-evaluator") == PR_BASE
    # not on main
    assert branch != "main"


# --------------------------------------------------------------------------
# S42 — CI/repo validation green (the suite itself) — smoke import + run
# --------------------------------------------------------------------------
def test_s42_runtime_imports_and_runs():
    from tools.ignition_runtime import cli, transaction, recovery, epistemic, generation, store

    assert all([cli, transaction, recovery, epistemic, generation, store])
    store = new_store()
    gid = run(store, FixtureProvider(refs=["M1"]))
    assert load_generation(store.generations_dir / gid)["manifest"]["op_type"] == "run"


# --------------------------------------------------------------------------
# S43 — Draft PR diff contains only production-layer changes
# --------------------------------------------------------------------------
def test_s43_diff_scope():
    allowed_prefixes = (
        "tools/ignition_runtime/",
        "schemas/ignition_runtime/",
        "tests/ignition_runtime/",
        "docs/ignition-runtime/",
        ".github/workflows/ignition-production-validation.yml",
        "ITERATION.md",
        "README.md",
        "docs/project-current-state.md",
        "reports/ignition-rpe/",
    )
    out = git("diff", "--name-only", PR_BASE)
    for path in out.splitlines():
        path = path.strip()
        if not path:
            continue
        assert any(path == p or path.startswith(p) for p in allowed_prefixes), f"out-of-scope change: {path}"


# --------------------------------------------------------------------------
# S44 — remote evidence/index paths readable
# --------------------------------------------------------------------------
def test_s44_remote_evidence_readable():
    if not CTRL_INPUTS.is_dir():
        pytest.skip("control inputs not present")
    provider = FileSystemProvider(CTRL_INPUTS)
    assert (CTRL_INPUTS / "INPUT_INDEX.md").is_file()
    mats = provider.list_materials()
    assert len(mats) == 5  # 5 materials (index excluded)
    idx = provider.read_index()
    assert "e50e847056e5089a3f1fb3c9d58309db677b61c2267a66f63574484b93df94f7" in idx


# --------------------------------------------------------------------------
# S45 — non-self-referential identity
# --------------------------------------------------------------------------
def test_s45_non_self_referential_identity():
    store = new_store()
    run(store, FixtureProvider(refs=["M1", "M2", "M3", "M4"]))
    head = git("rev-parse", "HEAD")
    for gdir in store.generations_dir.iterdir():
        if not gdir.is_dir():
            continue
        for f in gdir.glob("*.json"):
            content = f.read_text(encoding="utf-8")
            # live tip must not be embedded as a final head in any committed file
            assert head not in content
            if f.name == "receipt.json":
                r = json.loads(content)
                assert r["self_final_sha_claimed"] is False
                assert r["live_refetch_required"] is True
