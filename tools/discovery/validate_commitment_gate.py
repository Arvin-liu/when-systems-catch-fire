#!/usr/bin/env python3
"""Q34 Discovery-Commitment Gate — fail-closed deterministic validator/CLI.

Decides whether a claim may be COMMITTED as a current project conclusion. It does
NOT assert real-world truth, legality, causality or completeness. It enforces the
repository-native boundary between "discovered a candidate claim" and "allowed to
commit that claim as a current conclusion".

Stable exit codes (machine-consumable, never free-text PASS):
  0  GATE_PASS            - claim may be committed within its declared claim_ceiling
  2  SCHEMA_ERROR         - claim/contract JSON failed schema
  3  EVIDENCE_UNRESOLVABLE- an evidence reference cannot be resolved
  4  SELF_CERTIFICATION   - sole evidence is self-authored / circular
  5  NO_INDEPENDENT_EVIDENCE - no independent (or deterministic) evidence for commit
  6  CLAIM_CEILING_BREACH - commitment text exceeds declared claim_ceiling
  7  ANALOGY_AS_MECHANISM - STRUCTURAL_ANALOGY asserted as causal mechanism
  8  STALE_EXACT_HEAD     - evidence bound to a different/old head than required
  9  SELECTIVE_REPORTING  - commitment with no search/rejection process
  10 LIFECYCLE_INCONSISTENT- committed state inconsistent with iteration lifecycle
  11 HISTORY_VIOLATION    - supersession/retraction overwrote history, or uncommitted
                            candidate appears on a Current/Accepted surface
  12 EXTERNAL_ATTESTATION_MISSING - external_world claim lacks valid external attestation
  13 MISSING_INDEPENDENT_REVIEW   - commit requires but lacks an independent reviewer
  14 INVALID_TRANSITION   - state machine jump not allowed (e.g. discovered->committed)

Usage:
  python tools/discovery/validate_commitment_gate.py --claim <claim.json> \
      [--registry <registry.json>] [--current-main-head <sha>] \
      [--require-external-attestation] [--require-independent-review] \
      [--report <out.json>]
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT / "schemas" / "discovery" / "commitment-claim.schema.json"

# Exit codes
GATE_PASS = 0
SCHEMA_ERROR = 2
EVIDENCE_UNRESOLVABLE = 3
SELF_CERTIFICATION = 4
NO_INDEPENDENT_EVIDENCE = 5
CLAIM_CEILING_BREACH = 6
ANALOGY_AS_MECHANISM = 7
STALE_EXACT_HEAD = 8
SELECTIVE_REPORTING = 9
LIFECYCLE_INCONSISTENT = 10
HISTORY_VIOLATION = 11
EXTERNAL_ATTESTATION_MISSING = 12
MISSING_INDEPENDENT_REVIEW = 13
INVALID_TRANSITION = 14

EXIT_NAMES = {
    GATE_PASS: "GATE_PASS",
    SCHEMA_ERROR: "SCHEMA_ERROR",
    EVIDENCE_UNRESOLVABLE: "EVIDENCE_UNRESOLVABLE",
    SELF_CERTIFICATION: "SELF_CERTIFICATION",
    NO_INDEPENDENT_EVIDENCE: "NO_INDEPENDENT_EVIDENCE",
    CLAIM_CEILING_BREACH: "CLAIM_CEILING_BREACH",
    ANALOGY_AS_MECHANISM: "ANALOGY_AS_MECHANISM",
    STALE_EXACT_HEAD: "STALE_EXACT_HEAD",
    SELECTIVE_REPORTING: "SELECTIVE_REPORTING",
    LIFECYCLE_INCONSISTENT: "LIFECYCLE_INCONSISTENT",
    HISTORY_VIOLATION: "HISTORY_VIOLATION",
    EXTERNAL_ATTESTATION_MISSING: "EXTERNAL_ATTESTATION_MISSING",
    MISSING_INDEPENDENT_REVIEW: "MISSING_INDEPENDENT_REVIEW",
    INVALID_TRANSITION: "INVALID_TRANSITION",
}

# States that may appear on a Current/Accepted surface
CURRENT_STATES = {"committed_current"}
# States that must never appear on a Current/Accepted surface
NON_CURRENT_STATES = {"discovered", "hypothesis", "evidence_bound_candidate",
                      "validated_within_scope", "commitment_candidate",
                      "deferred", "rejected"}

# Allowed forward transitions (from_state -> set of to_state)
ALLOWED_TRANSITIONS = {
    "discovered": {"hypothesis", "evidence_bound_candidate", "deferred", "rejected"},
    "hypothesis": {"evidence_bound_candidate", "deferred", "rejected"},
    "evidence_bound_candidate": {"validated_within_scope", "commitment_candidate", "deferred", "rejected"},
    "validated_within_scope": {"commitment_candidate", "deferred", "rejected"},
    "commitment_candidate": {"committed_current", "deferred", "rejected", "retracted", "superseded"},
    "committed_current": {"retracted", "superseded"},
    "deferred": {"evidence_bound_candidate", "rejected", "retracted"},
    "rejected": {"retracted"},
    "retracted": {"superseded"},
    "superseded": set(),
}

# Tokens that mark a claim as a real-world / universal assertion
REAL_WORLD_TOKENS = [
    "global", "worldwide", "all jurisdictions", "proven compliant",
    "real-world truth", "legal compliance proven", "guaranteed legal",
    "compliance is proven", "exhaustive", "universal law",
]
ANALOGY_TOKENS = ["structural_analogy", "analogy", "isomorphic", "homomorphic", "structural mapping"]
MECHANISM_TOKENS = ["causal mechanism", "causes", "mechanism by which", "produces the effect", "drives"]


def _load_json(path: Path):
    try:
        return json.loads(path.read_text()), None
    except Exception as e:  # noqa: BLE001
        return None, f"{path}: cannot read/parse: {e}"


def _result(exit_code, errors, claim_id=None, decision=None):
    return {
        "gate": "q34_commitment_gate",
        "exit_code": exit_code,
        "exit_name": EXIT_NAMES.get(exit_code, "UNKNOWN"),
        "decision": decision,
        "claim_id": claim_id,
        "errors": errors,
    }


def validate_schema(claim, claim_path):
    """Structural validation without external jsonschema dependency expectations."""
    errors = []
    if not isinstance(claim, dict):
        return ["claim document is not a JSON object"]
    required = ["claim_id", "claim_text", "claim_type", "scope", "state",
                "discovered_by", "evidence", "claim_ceiling", "search_process",
                "relations", "history"]
    for f in required:
        if f not in claim:
            errors.append(f"missing required field: {f}")
    if errors:
        return errors
    if not re.match(r"^[a-z0-9][a-z0-9._-]*$", str(claim.get("claim_id", ""))):
        errors.append("claim_id does not match ^[a-z0-9][a-z0-9._-]*$")
    valid_types = {"repository_fact", "governance_state", "observation", "prediction",
                   "mechanism", "structural_analogy", "interpretation", "external_world"}
    if claim.get("claim_type") not in valid_types:
        errors.append(f"invalid claim_type: {claim.get('claim_type')}")
    valid_states = {"discovered", "hypothesis", "evidence_bound_candidate",
                    "validated_within_scope", "commitment_candidate",
                    "committed_current", "deferred", "rejected", "retracted", "superseded"}
    if claim.get("state") not in valid_states:
        errors.append(f"invalid state: {claim.get('state')}")
    if not isinstance(claim.get("evidence"), list):
        errors.append("evidence must be an array")
    sp = claim.get("search_process", {})
    if not isinstance(sp, dict) or not sp.get("summary"):
        errors.append("search_process.summary is required")
    if not isinstance(claim.get("claim_ceiling"), str) or not claim.get("claim_ceiling"):
        errors.append("claim_ceiling must be a non-empty string")
    return errors


def check_evidence_resolvable(claim, registry_index):
    errors = []
    for ev in claim.get("evidence", []):
        ref = ev.get("reference", "")
        # Resolve against registry index (path, run id, commit, artifact, receipt)
        if registry_index is not None and ref not in registry_index:
            errors.append(f"evidence '{ev.get('ref_id')}' reference not resolvable: {ref}")
    return errors


def check_self_certification(claim):
    """Fail if the ONLY evidence is self-authored (circular self-proof)."""
    errors = []
    evs = claim.get("evidence", [])
    if not evs:
        return errors  # no evidence handled by independence check
    author = claim.get("discovered_by", {}).get("actor")
    all_self = all(
        ev.get("independence") == "self" or ev.get("produced_by") == author
        for ev in evs
    )
    if all_self:
        errors.append(
            "all evidence is self-authored/circular; a claim cannot certify itself")
    return errors


def check_independent_evidence(claim):
    """Commitment requires at least one independent or deterministic evidence."""
    errors = []
    evs = claim.get("evidence", [])
    if not evs:
        errors.append("commitment has no evidence at all")
        return errors
    has_independent = any(
        ev.get("independence") == "independent"
        or ev.get("kind") in ("deterministic_test", "machine_proof", "ci_run", "external_attestation")
        for ev in evs
    )
    if not has_independent:
        errors.append("no independent or deterministic evidence supports commitment")
    return errors


def check_claim_ceiling(claim):
    """Commitment text must not exceed the declared claim_ceiling."""
    errors = []
    ceiling = claim.get("claim_ceiling", "")
    text = claim.get("claim_text", "")
    ceiling_l = ceiling.lower()
    text_l = text.lower()
    # If the ceiling is repository-scoped but the text asserts real-world universality -> breach
    ceiling_repo_scoped = any(t in ceiling_l for t in
                              ["repository", "in-repo", "repo", "within", "representative",
                               "candidate_only", "projection", "does not assert", "not assert"])
    text_real_world = any(t in text_l for t in REAL_WORLD_TOKENS)
    if ceiling_repo_scoped and text_real_world:
        errors.append(
            "claim_text asserts real-world/universal scope that exceeds a repository-scoped claim_ceiling")
    return errors


def check_analogy_not_mechanism(claim):
    errors = []
    if claim.get("claim_type") == "structural_analogy":
        text_l = claim.get("claim_text", "").lower()
        if any(t in text_l for t in MECHANISM_TOKENS):
            errors.append(
                "STRUCTURAL_ANALOGY claim_text asserts a causal mechanism; analogy may not be upgraded to mechanism")
    return errors


def check_exact_head(claim, current_main_head):
    errors = []
    binding = claim.get("exact_head_binding")
    if not binding:
        return errors
    claim_head = binding.get("head")
    for ev in claim.get("evidence", []):
        eh = ev.get("exact_head")
        if eh and claim_head and eh != claim_head:
            errors.append(
                f"evidence '{ev.get('ref_id')}' exact_head {eh} != claim bound head {claim_head}")
    if current_main_head and claim_head and claim_head != current_main_head:
        errors.append(
            f"claim exact_head_binding {claim_head} != current main head {current_main_head} (stale)")
    return errors


def check_selective_reporting(claim):
    errors = []
    sp = claim.get("search_process", {})
    if claim.get("state") in ("commitment_candidate", "committed_current"):
        if not sp.get("considered_paths"):
            errors.append("commitment without any considered_paths (search space)")
        if not sp.get("summary"):
            errors.append("commitment without search_process.summary")
    return errors


def check_transitions(claim):
    errors = []
    hist = claim.get("history", [])
    for ev in hist:
        frm = ev.get("from_state")
        to = ev.get("to_state")
        if frm in ALLOWED_TRANSITIONS and to not in ALLOWED_TRANSITIONS.get(frm, set()):
            # initial discovery events use from_state == to_state bootstrap; allow DISCOVER
            if ev.get("decision") == "DISCOVER" and frm == to:
                continue
            errors.append(f"invalid transition {frm} -> {to}")
    # Final state must match the last history to_state
    if hist:
        last_to = hist[-1].get("to_state")
        if last_to and last_to != claim.get("state"):
            errors.append(
                f"final state '{claim.get('state')}' != last history to_state '{last_to}'")
    return errors


def check_external_attestation(claim, require_external):
    errors = []
    if claim.get("claim_type") == "external_world" or require_external:
        has_ext = any(
            ev.get("kind") == "external_attestation" and ev.get("independence") == "independent"
            for ev in claim.get("evidence", [])
        )
        if not has_ext:
            errors.append("external_world claim lacks a valid independent external attestation")
    return errors


def check_independent_review(claim, require_review):
    errors = []
    if require_review or claim.get("state") in ("commitment_candidate", "committed_current"):
        author = claim.get("discovered_by", {}).get("actor")
        verifier = claim.get("verifier", {})
        v_actor = verifier.get("actor")
        if not v_actor:
            errors.append("commitment requires a verifier / independent review authority")
        elif v_actor == author:
            errors.append("verifier equals discovered_by actor (self-approval not allowed)")
    return errors


def check_history_and_current(claim, current_surface_claim_ids=None):
    errors = []
    state = claim.get("state")
    # Non-current states must never be on a Current/Accepted surface
    if current_surface_claim_ids and state in NON_CURRENT_STATES:
        if claim.get("claim_id") in current_surface_claim_ids:
            errors.append(
                f"uncommitted state '{state}' appears on Current/Accepted surface")
    # Superseded/retracted relations: target claim must not remain committed_current silently
    # (The registry-level cross-check is performed in validate_registry.)
    return errors


def validate_claim(claim, claim_path, registry_index=None, current_main_head=None,
                   require_external=False, require_review=False,
                   current_surface_claim_ids=None):
    errors = validate_schema(claim, claim_path)
    if errors:
        return _result(SCHEMA_ERROR, errors, claim.get("claim_id"))

    state = claim.get("state")
    committing = state in ("commitment_candidate", "committed_current")

    # Universal checks (apply to every claim)
    for fn, code in (
        (check_self_certification, SELF_CERTIFICATION),
        (check_analogy_not_mechanism, ANALOGY_AS_MECHANISM),
        (check_transitions, INVALID_TRANSITION),
    ):
        errs = fn(claim)
        if errs:
            return _result(code, errs, claim.get("claim_id"))

    errs = check_exact_head(claim, current_main_head)
    if errs:
        return _result(STALE_EXACT_HEAD, errs, claim.get("claim_id"))

    errs = check_evidence_resolvable(claim, registry_index)
    if errs:
        return _result(EVIDENCE_UNRESOLVABLE, errs, claim.get("claim_id"))

    errs = check_history_and_current(claim, current_surface_claim_ids)
    if errs:
        return _result(HISTORY_VIOLATION, errs, claim.get("claim_id"))

    if committing:
        errs = check_independent_evidence(claim)
        if errs:
            return _result(NO_INDEPENDENT_EVIDENCE, errs, claim.get("claim_id"))
        errs = check_claim_ceiling(claim)
        if errs:
            return _result(CLAIM_CEILING_BREACH, errs, claim.get("claim_id"))
        errs = check_selective_reporting(claim)
        if errs:
            return _result(SELECTIVE_REPORTING, errs, claim.get("claim_id"))
        errs = check_independent_review(claim, require_review)
        if errs:
            return _result(MISSING_INDEPENDENT_REVIEW, errs, claim.get("claim_id"))
        errs = check_external_attestation(claim, require_external)
        if errs:
            return _result(EXTERNAL_ATTESTATION_MISSING, errs, claim.get("claim_id"))

    return _result(GATE_PASS, [], claim.get("claim_id"),
                   decision=("COMMIT" if committing else "DEFER"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Q34 discovery-commitment gate (fail-closed)")
    ap.add_argument("--claim", required=True, help="path to claim JSON")
    ap.add_argument("--registry", help="path to resolvable-evidence registry JSON (list of reference strings)")
    ap.add_argument("--current-main-head", help="current main head SHA for staleness check")
    ap.add_argument("--current-surface", help="path to JSON list of claim_ids on the Current/Accepted surface")
    ap.add_argument("--require-external-attestation", action="store_true")
    ap.add_argument("--require-independent-review", action="store_true")
    ap.add_argument("--report", help="write machine-readable JSON report to this path")
    args = ap.parse_args(argv)

    claim_path = Path(args.claim)
    claim, err = _load_json(claim_path)
    if err:
        out = _result(SCHEMA_ERROR, [err])
        return _emit(out, args)

    registry_index = None
    if args.registry:
        reg, rerr = _load_json(Path(args.registry))
        if rerr:
            out = _result(SCHEMA_ERROR, [rerr])
            return _emit(out, args)
        registry_index = set(reg if isinstance(reg, list) else reg.get("references", []))

    current_surface = None
    if args.current_surface:
        cs, cerr = _load_json(Path(args.current_surface))
        if not cerr:
            current_surface = set(cs if isinstance(cs, list) else cs.get("claim_ids", []))

    out = validate_claim(
        claim, claim_path,
        registry_index=registry_index,
        current_main_head=args.current_main_head,
        require_external=args.require_external_attestation,
        require_review=args.require_independent_review,
        current_surface_claim_ids=current_surface,
    )
    return _emit(out, args)


def _emit(out, args):
    if args.report:
        Path(args.report).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return out["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
