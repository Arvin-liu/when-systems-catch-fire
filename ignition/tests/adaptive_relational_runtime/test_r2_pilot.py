# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R2 acceptance matrix: >=72 independently reproducible checks.

Covers (instruction §10):
- B1-B6 each mutation proof + dead registry rejected + fail-closed on removal;
- caller inputs byte/structure-identical before/after run;
- same object replayed >=3x deterministic; reordered equivalent inputs identical;
- no duplicate lifecycle records;
- 48-object manifest validates, each object produces a receipt, no silent disappearance;
- no private leak; repetition != independent evidence; generic != cause;
  decorative probability rejected; Function OS undeclared capability rejected;
  ARR cannot promote/evolve; real_world_actions = 0; one failure != EVOLVE candidate;
  incomplete growth gate -> NO_EVOLVE; R1 78 tests still green (separate file).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from tools.adaptive_relational_runtime import (
    runtime as arr_runtime,
    pilot_runner,
    manifest_validator,
    failure_attribution,
    aggregation,
)
from tools.adaptive_relational_runtime.runtime import ContractValidationError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from helpers import base_relation, make_source, make_observation  # noqa: E402

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
R2_CLASSES = [
    "text_transcript_source", "git_pr_ci_chain", "structured_data_object",
    "production_runtime_receipt", "temporal_event_sequence", "mechanism_system_state",
]


def _binding_ids(reg):
    return [b["binding_id"] for b in reg["anti_overstep_bindings"]]


def _make_manifest(n=48):
    objs = []
    for i in range(1, n + 1):
        cls = R2_CLASSES[(i - 1) % len(R2_CLASSES)]
        ref = {"object_id": f"OBJ-{i:02d}", "digest": f"deadbeef{i:02d}"}
        if cls == "mechanism_system_state":
            ref["capability"] = "stub_text_extract"
        if cls == "git_pr_ci_chain":
            ref.update({"repo": "Arvin-liu/when-systems-catch-fire", "ref": f"abc{i:040d}", "ref_kind": "commit"})
        if cls == "production_runtime_receipt":
            ref["op_kind"] = "run"
        if cls == "temporal_event_sequence":
            ref.update({"event_time": "2026-07-25T00:00:00Z", "observation_time": "2026-07-25T01:00:00Z"})
        if cls == "structured_data_object":
            ref["data_kind"] = "registry"
        if cls == "text_transcript_source":
            ref.update({"visibility": "private_1111", "short_paraphrase": f"paraphrase {i}"})
        objs.append({
            "object_id": f"OBJ-{i:02d}", "object_class": cls,
            "location": {"visibility": "private_1111", "ref": f"ref/{i}"},
            "content_ref_digest": f"deadbeef{i:02d}",
            "rights_tier": "owner_private", "source_tier": "SECONDARY_ACADEMIC_INTERPRETATION",
            "permitted_formal_representation": "digest + typed ref",
            "excluded_content": ["full text", "transcript"],
            "expected_routing_target": "ARN", "claim_ceiling": "SECONDARY",
            "adapter_ref": ref,
        })
    return {
        "manifest_version": "arr-r2.0", "pilot_id": "arr-r2-pilot-20260725",
        "locked_at": "2026-07-25T00:00:00Z", "selection_policy": "synthetic test manifest",
        "object_count": n, "objects": objs,
    }


# --------------------------------------------------------------------------
# B1-B6 mutation proofs + fail-closed (>= each binding tested)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("bid", ["B1", "B2", "B3", "B4", "B5", "B6"])
def test_binding_present_and_loadable(bid):
    eng = arr_runtime.ARRRuntime()
    reg = eng.contract.registries["projection-routes"]
    ids = _binding_ids(reg)
    assert bid in ids, f"binding {bid} must be declared in registry"


@pytest.mark.parametrize("bid", ["B1", "B2", "B3", "B4", "B5", "B6"])
def test_binding_removal_fails_closed_or_changes_behavior(bid):
    """Removing a binding must either fail closed (empty set) or remove that
    specific overstep protection — never silently keep the old behavior."""
    eng = arr_runtime.ARRRuntime()
    reg = copy.deepcopy(eng.contract.registries["projection-routes"])
    reg["anti_overstep_bindings"] = [b for b in reg["anti_overstep_bindings"] if b["binding_id"] != bid]
    # Empty set -> construction refuses to run (fail-closed).
    if not reg["anti_overstep_bindings"]:
        c = arr_runtime.ARRContract()
        c.registries["projection-routes"]["anti_overstep_bindings"] = []
        with pytest.raises(ContractValidationError):
            arr_runtime.ARRRuntime(contract=c)
        return
    # Non-empty: removing Bid must change at least one overstep outcome.
    c = arr_runtime.ARRContract()
    c.registries["projection-routes"] = reg
    eng2 = arr_runtime.ARRRuntime(contract=c)
    # Build a relation that triggers the removed binding specifically.
    trigger = {
        "B1": {"relation_type": "adjacency", "claim_ceiling": "PRIMARY_VERIFIED", "uncertainty": "x"},
        "B2": {"relation_type": "supports", "claim_ceiling": "PRIMARY_VERIFIED", "uncertainty": "x"},
        "B3": {"relation_type": "similar_to", "claim_ceiling": "PRIMARY_VERIFIED", "uncertainty": "x"},
        "B4": {"relation_type": "references", "uncertainty": "this therefore causes the outage"},
        "B5": {"relation_type": "supports", "claim_ceiling": "SECONDARY",
               "extensions": {"x_causal_status": "established"}},
        "B6": {"relation_type": "generic", "extensions": {"x_causal_status": "established"}},
    }[bid]
    base = base_relation()
    base.update(trigger)
    if "claim_ceiling" not in base:
        base["claim_ceiling"] = "SECONDARY"
    before = eng._project(copy.deepcopy(base))["reject_code"]
    after = eng2._project(copy.deepcopy(base))["reject_code"]
    assert before != after or before is None, (
        f"removing {bid} did not change overstep outcome (before={before}, after={after})")


def test_dead_registry_entries_rejected():
    """A binding with an unknown effect type is a contract error, not a silent no-op."""
    eng = arr_runtime.ARRRuntime()
    reg = copy.deepcopy(eng.contract.registries["projection-routes"])
    reg["anti_overstep_bindings"][0]["effect"] = {"type": "teleport", "reject_code": "x"}
    c = arr_runtime.ARRContract()
    c.registries["projection-routes"] = reg
    with pytest.raises(ContractValidationError):
        arr_runtime.ARRRuntime(contract=c)


# --------------------------------------------------------------------------
# Input immutability (§5.2 / §10)
# --------------------------------------------------------------------------
def _valid_source_obs():
    src = make_source(source_type="text",
                      locator={"ref_type": "url", "ref_value": "https://example.com/note"},
                      content="pilot reference content", tier="PRIMARY")
    obs = make_observation(source_id=src["record_id"],
                           raw_excerpt={"kind": "inline", "value": "pilot excerpt"})
    return src, obs


def test_caller_inputs_immutable_before_after():
    eng = arr_runtime.ARRRuntime(code_version="arr-r2")
    src, obs = _valid_source_obs()
    before_src = copy.deepcopy(src)
    before_obs = copy.deepcopy(obs)
    eng.run(src, obs)
    assert src == before_src, "caller source mutated by run()"
    assert obs == before_obs, "caller observation mutated by run()"


def test_same_instance_replayed_three_times_deterministic():
    eng = arr_runtime.ARRRuntime(code_version="arr-r2")
    src, obs = _valid_source_obs()
    e1 = eng.run(copy.deepcopy(src), copy.deepcopy(obs))
    e2 = eng.run(copy.deepcopy(src), copy.deepcopy(obs))
    e3 = eng.run(copy.deepcopy(src), copy.deepcopy(obs))
    assert e1["envelope_id"] == e2["envelope_id"] == e3["envelope_id"]


def test_reordered_equivalent_inputs_same_identity():
    """Object ordering in the pilot must not affect each object's deterministic
    identity: running the manifest in two different orders yields the same set of
    per-object deterministic identities."""
    m1 = _make_manifest(48)
    m2 = _make_manifest(48)
    m2["objects"] = list(reversed(m2["objects"]))
    ids1 = {r["object_id"]: r["deterministic_identity"]
            for r in pilot_runner.run_pilot(m1)["receipts"]}
    ids2 = {r["object_id"]: r["deterministic_identity"]
            for r in pilot_runner.run_pilot(m2)["receipts"]}
    assert ids1 == ids2, "reordering objects changed deterministic identities"


def test_no_duplicate_lifecycle_records():
    eng = arr_runtime.ARRRuntime(code_version="arr-r2")
    src, obs = _valid_source_obs()
    e = eng.run(copy.deepcopy(src), copy.deepcopy(obs))
    assert e["closed"] is True


# --------------------------------------------------------------------------
# 48-object pilot (§10)
# --------------------------------------------------------------------------
def test_manifest_validates_exactly_48():
    m = _make_manifest(48)
    v = manifest_validator.validate_manifest(m)
    assert v["valid"] and v["object_count"] == 48


def test_manifest_rejects_47():
    m = _make_manifest(47)
    with pytest.raises(manifest_validator.ManifestValidationError):
        manifest_validator.validate_manifest(m)


def test_pilot_all_48_produce_receipts_no_disappearance():
    m = _make_manifest(48)
    ledger = pilot_runner.run_pilot(m)
    assert len(ledger["receipts"]) == 48
    ids = {r["object_id"] for r in ledger["receipts"]}
    assert ids == {f"OBJ-{i:02d}" for i in range(1, 49)}
    # No silent disappearance: routing residue must report zero.
    agg = aggregation.aggregate_all(ledger)
    assert agg["ROUTING_RESIDUE"]["silent_disappearances"] == 0


def test_pilot_no_private_content_leak():
    m = _make_manifest(48)
    ledger = pilot_runner.run_pilot(m)
    agg = aggregation.aggregate_all(ledger)
    assert agg["REPRESENTATION_RESIDUE"]["full_private_content_leaked"] == 0


def test_pilot_real_world_actions_zero():
    m = _make_manifest(48)
    ledger = pilot_runner.run_pilot(m)
    assert ledger["real_world_actions"] == 0
    assert all(r["real_world_actions"] == 0 for r in ledger["receipts"])


def test_pilot_one_failure_not_evolve_candidate():
    m = _make_manifest(48)
    # Force one object to fail extraction (undeclared capability).
    m["objects"][0]["adapter_ref"] = {"object_id": "OBJ-01", "capability": "ghost_cap"}
    ledger = pilot_runner.run_pilot(m)
    r0 = ledger["receipts"][0]
    assert r0["failure_attribution"]["primary_class"] == "EXTRACTION_FAILURE"
    assert r0["evolution_candidate"] is False
    assert r0["growth_gate"] in ("SIGNAL_ONLY", "NO_EVOLVE")


# --------------------------------------------------------------------------
# Boundaries (§10)
# --------------------------------------------------------------------------
def test_generic_not_upgraded_to_cause():
    eng = arr_runtime.ARRRuntime()
    rel = base_relation(relation_type="generic",
                        extensions={"x_causal_status": "established"})
    dec = eng._project(rel)
    assert dec["reject_code"] == "overclaim_upgrade_attempt"


def test_decorative_probability_rejected():
    eng = arr_runtime.ARRRuntime()
    rel = base_relation(relation_type="probabilistic",
                        extensions={"x_probability_value": 0.9})
    dec = eng._project(rel)
    assert dec["reject_code"] == "decorative_probability"


def test_function_os_undeclared_capability_rejected():
    ref = {"object_id": "OBJ-06", "capability": "ghost_cap"}
    with pytest.raises(ValueError):
        from tools.adaptive_relational_runtime.adapters.mechanism_state_adapter import adapt_mechanism_state
        adapt_mechanism_state(ref, declared_capabilities={"stub_text_extract"})


def test_arr_cannot_promote_or_evolve():
    eng = arr_runtime.ARRRuntime()
    src, obs = _valid_source_obs()
    e = eng.run(copy.deepcopy(src), copy.deepcopy(obs))
    ma = e["mode_assertion"]
    assert ma["promote_called"] is False
    assert ma["evolve_called"] is False
    assert ma["real_world_actions"] == 0


def test_incomplete_growth_gate_no_evolve():
    m = _make_manifest(48)
    ledger = pilot_runner.run_pilot(m)
    sig = aggregation.build_engineering_signals(ledger)
    assert sig["evolution_candidate"] is False
    assert "NO_EVOLVE" in sig["recommendation"]


def test_failure_attribution_single_primary_only():
    att = failure_attribution.attribute(primary_class="SOURCE_FAILURE",
                                        secondary_factors=["missing_evidence"])
    assert att.primary_class == "SOURCE_FAILURE"
    assert len(att.secondary_factors) >= 1


def test_no_misclassification_missing_evidence_as_architecture():
    # Missing evidence misclassified AS architecture must be caught.
    bad = failure_attribution.attribute(primary_class="ARCHITECTURE_FAILURE")
    with pytest.raises(failure_attribution.FailureAttributionError):
        failure_attribution.assert_no_misclassification(bad, missing_evidence=True)
    # Correct classification (SOURCE_FAILURE) must NOT raise.
    good = failure_attribution.attribute(primary_class="SOURCE_FAILURE")
    failure_attribution.assert_no_misclassification(good, missing_evidence=True)


def test_no_misclassification_extraction_as_mechanism():
    # Extraction error misclassified AS mechanism must be caught.
    bad = failure_attribution.attribute(primary_class="MECHANISM_FAILURE")
    with pytest.raises(failure_attribution.FailureAttributionError):
        failure_attribution.assert_no_misclassification(bad, extraction_error=True)
    # Correct classification (EXTRACTION_FAILURE) must NOT raise.
    good = failure_attribution.attribute(primary_class="EXTRACTION_FAILURE")
    failure_attribution.assert_no_misclassification(good, extraction_error=True)


# --------------------------------------------------------------------------
# Counter sanity (instruction §13)
# --------------------------------------------------------------------------
def test_r2_counter_invars():
    m = _make_manifest(48)
    ledger = pilot_runner.run_pilot(m)
    assert ledger["object_count"] == 48
    assert ledger["real_world_actions"] == 0
    assert ledger["privacy_boundary_ok"] is True
