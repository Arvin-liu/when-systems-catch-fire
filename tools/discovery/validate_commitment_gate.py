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
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

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
CLAIM_DIGEST_MISMATCH = 15
INVALID_EVIDENCE_BINDING = 16
UNRESOLVED_ACTOR = 17
INVALID_REVIEW_DECISION = 18
INDEPENDENCE_VIOLATION = 19
SELF_REFERENCE = 20
PLACEHOLDER_VALUE = 21

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
    CLAIM_DIGEST_MISMATCH: "CLAIM_DIGEST_MISMATCH",
    INVALID_EVIDENCE_BINDING: "INVALID_EVIDENCE_BINDING",
    UNRESOLVED_ACTOR: "UNRESOLVED_ACTOR",
    INVALID_REVIEW_DECISION: "INVALID_REVIEW_DECISION",
    INDEPENDENCE_VIOLATION: "INDEPENDENCE_VIOLATION",
    SELF_REFERENCE: "SELF_REFERENCE",
    PLACEHOLDER_VALUE: "PLACEHOLDER_VALUE",
}

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER_TOKENS = {
    "", "null", "none", "todo", "tbd", "unknown", "unknown_as_pass",
    "placeholder", "n/a", "na", "pending",
}
CANONICAL_CLAIM_FIELDS = (
    "claim_id", "claim_text", "claim_type", "scope", "claim_ceiling",
    "exact_head_binding", "relations", "claim_roles",
)

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


def _canonical_json(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_claim_digest(claim):
    """Digest only immutable claim semantics, never review/lifecycle assertions."""
    body = {field: claim.get(field) for field in CANONICAL_CLAIM_FIELDS}
    return "sha256:" + hashlib.sha256(_canonical_json(body)).hexdigest()


def _placeholder(value):
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if normalized in PLACEHOLDER_TOKENS:
        return True
    if SHA256_RE.fullmatch(normalized) and set(normalized.removeprefix("sha256:")) == {"0"}:
        return True
    return bool(normalized) and len(set(normalized)) == 1 and len(normalized) >= 32


def _repo_relative_path(raw):
    if _placeholder(raw) or not isinstance(raw, str) or "\\" in raw:
        return None
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or raw.startswith("/"):
        return None
    if any(part in ("", ".", "..") for part in candidate.parts):
        return None
    normalized = candidate.as_posix()
    if normalized != raw or normalized.startswith("../"):
        return None
    return normalized


def _git_bytes(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=False
    )


def _read_git_blob(commit, repo_path):
    """Return (bytes, blob, error) from an exact commit without the worktree."""
    if not HEX40_RE.fullmatch(str(commit or "")):
        return None, None, "exact_commit is not a 40-hex Git object id"
    kind = _git_bytes("cat-file", "-t", commit)
    if kind.returncode != 0 or kind.stdout.strip() != b"commit":
        return None, None, f"exact_commit {commit} is not a resolvable commit"
    path = _repo_relative_path(repo_path)
    if path is None:
        return None, None, f"path is not canonical repo-relative: {repo_path!r}"
    entry = _git_bytes("ls-tree", "-z", commit, "--", path)
    if entry.returncode != 0 or not entry.stdout:
        return None, None, f"path {path} does not exist at exact commit {commit}"
    records = [row for row in entry.stdout.split(b"\0") if row]
    exact = []
    for row in records:
        try:
            metadata, encoded_path = row.split(b"\t", 1)
            mode, obj_type, blob = metadata.decode("ascii").split()
            decoded_path = encoded_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
        if decoded_path == path:
            exact.append((mode, obj_type, blob))
    if len(exact) != 1:
        return None, None, f"path {path} did not resolve to one exact tree entry"
    mode, obj_type, blob = exact[0]
    if mode == "120000" or obj_type != "blob":
        return None, None, f"path {path} is a symlink or non-blob object"
    content = _git_bytes("cat-file", "blob", blob)
    if content.returncode != 0:
        return None, None, f"blob {blob} cannot be read"
    return content.stdout, blob, None


def _actor_index(registry):
    if not isinstance(registry, dict) or not isinstance(registry.get("actors"), list):
        return None
    index = {}
    for actor in registry["actors"]:
        if not isinstance(actor, dict) or _placeholder(actor.get("actor_id")):
            return None
        actor_id = actor["actor_id"]
        if actor_id in index:
            return None
        index[actor_id] = actor
    return index


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


def check_claim_digest_binding(claim):
    declared = claim.get("claim_digest")
    if _placeholder(declared):
        return PLACEHOLDER_VALUE, ["claim_digest is missing, zero, or placeholder"]
    if not SHA256_RE.fullmatch(str(declared)):
        return CLAIM_DIGEST_MISMATCH, ["claim_digest must be sha256:<64 lowercase hex>"]
    expected = canonical_claim_digest(claim)
    if declared != expected:
        return CLAIM_DIGEST_MISMATCH, [
            f"claim_digest {declared} != canonical immutable claim body {expected}"
        ]
    return GATE_PASS, []


def check_actor_resolution_and_independence(claim, actor_index):
    if actor_index is None:
        return UNRESOLVED_ACTOR, ["canonical actor registry is missing or malformed"]
    roles = claim.get("claim_roles")
    if not isinstance(roles, dict):
        return UNRESOLVED_ACTOR, ["claim_roles must resolve claim_author and builder"]
    actor_ids = {
        "discoverer": claim.get("discovered_by", {}).get("actor"),
        "claim_author": roles.get("claim_author"),
        "builder": roles.get("builder"),
        "reviewer": claim.get("verifier", {}).get("actor"),
    }
    errors = []
    for role, actor_id in actor_ids.items():
        if _placeholder(actor_id) or actor_id not in actor_index:
            errors.append(f"{role} actor does not resolve in canonical registry: {actor_id!r}")
            continue
        if actor_index[actor_id].get("status") != "active":
            errors.append(f"{role} actor is not active: {actor_id}")
    if errors:
        return UNRESOLVED_ACTOR, errors
    reviewer_id = actor_ids["reviewer"]
    reviewer = actor_index[reviewer_id]
    if "independent_reviewer" not in reviewer.get("roles", []):
        return UNRESOLVED_ACTOR, [
            f"reviewer {reviewer_id} lacks canonical independent_reviewer role"
        ]
    if claim.get("scope") not in reviewer.get("authority_scopes", []):
        return UNRESOLVED_ACTOR, [
            f"reviewer {reviewer_id} lacks authority for scope {claim.get('scope')}"
        ]
    nonreview_roles = {
        actor_ids["discoverer"], actor_ids["claim_author"], actor_ids["builder"]
    }
    if reviewer_id in nonreview_roles:
        return INDEPENDENCE_VIOLATION, [
            "reviewer equals discoverer, claim author, or builder"
        ]
    if reviewer.get("conflicts_with") and nonreview_roles.intersection(
        reviewer.get("conflicts_with", [])
    ):
        return INDEPENDENCE_VIOLATION, [
            "canonical reviewer registry records a role conflict"
        ]
    return GATE_PASS, []


def check_evidence_byte_bindings(claim, claim_path, actor_index):
    claim_digest = claim.get("claim_digest")
    claim_repo = claim.get("exact_head_binding", {}).get("repo")
    try:
        claim_relative = claim_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        claim_relative = None
    for ev in claim.get("evidence", []):
        ref_id = ev.get("ref_id", "<missing>")
        required = (
            "repository", "path", "exact_commit", "git_blob", "sha256",
            "supports_claim_digest", "scope",
        )
        for field in required:
            if _placeholder(ev.get(field)):
                return PLACEHOLDER_VALUE, [
                    f"evidence {ref_id} field {field} is missing, zero, or placeholder"
                ]
        path = _repo_relative_path(ev.get("path"))
        if path is None:
            return INVALID_EVIDENCE_BINDING, [
                f"evidence {ref_id} path is not canonical repo-relative"
            ]
        lowered = path.lower()
        if path == claim_relative or "receipt" in PurePosixPath(path).name.lower() \
                or lowered.endswith("validate_commitment_gate.py") \
                or "gate-output" in lowered:
            return SELF_REFERENCE, [
                f"evidence {ref_id} uses claim/receipt/validator output as independent evidence: {path}"
            ]
        if ev.get("repository") != claim_repo:
            return INVALID_EVIDENCE_BINDING, [
                f"evidence {ref_id} repository does not match claim repository"
            ]
        if ev.get("supports_claim_digest") != claim_digest:
            return CLAIM_DIGEST_MISMATCH, [
                f"evidence {ref_id} supports a different claim digest"
            ]
        if ev.get("scope") != claim.get("scope"):
            return INVALID_EVIDENCE_BINDING, [
                f"evidence {ref_id} scope does not match claim scope"
            ]
        producer = ev.get("produced_by")
        if _placeholder(producer) or actor_index is None or producer not in actor_index:
            return UNRESOLVED_ACTOR, [
                f"evidence {ref_id} producer does not resolve: {producer!r}"
            ]
        content, blob, error = _read_git_blob(ev.get("exact_commit"), path)
        if error:
            return INVALID_EVIDENCE_BINDING, [f"evidence {ref_id}: {error}"]
        if ev.get("git_blob") != blob:
            return INVALID_EVIDENCE_BINDING, [
                f"evidence {ref_id} git_blob {ev.get('git_blob')} != actual {blob}"
            ]
        actual_digest = "sha256:" + hashlib.sha256(content).hexdigest()
        if ev.get("sha256") != actual_digest:
            return INVALID_EVIDENCE_BINDING, [
                f"evidence {ref_id} sha256 {ev.get('sha256')} != actual {actual_digest}"
            ]
    return GATE_PASS, []


def check_review_decision_binding(claim):
    binding = claim.get("review_decision")
    if not isinstance(binding, dict):
        return INVALID_REVIEW_DECISION, ["COMMIT requires a review_decision binding"]
    for field in (
        "evidence_ref_id", "reviewer_id", "decision", "reviewed_claim_digest",
        "scope", "claim_ceiling", "subject_head",
    ):
        if _placeholder(binding.get(field)):
            return PLACEHOLDER_VALUE, [
                f"review_decision.{field} is missing or placeholder"
            ]
    matching = [
        ev for ev in claim.get("evidence", [])
        if ev.get("ref_id") == binding.get("evidence_ref_id")
    ]
    if len(matching) != 1 or matching[0].get("kind") != "independent_review":
        return INVALID_REVIEW_DECISION, [
            "review_decision must identify exactly one independent_review evidence item"
        ]
    ev = matching[0]
    content, _, error = _read_git_blob(ev.get("exact_commit"), ev.get("path"))
    if error:
        return INVALID_REVIEW_DECISION, [error]
    try:
        decision_artifact = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        return INVALID_REVIEW_DECISION, [f"review decision bytes are not JSON: {exc}"]
    expected = {
        "reviewer_id": claim.get("verifier", {}).get("actor"),
        "decision": binding.get("decision"),
        "reviewed_claim_digest": claim.get("claim_digest"),
        "scope": claim.get("scope"),
        "claim_ceiling": claim.get("claim_ceiling"),
        "subject_head": claim.get("exact_head_binding", {}).get("head"),
    }
    for field, value in expected.items():
        if binding.get(field) != value:
            return INVALID_REVIEW_DECISION, [
                f"review_decision.{field} does not bind the claim/verifier"
            ]
        if decision_artifact.get(field) != value:
            return INVALID_REVIEW_DECISION, [
                f"review decision artifact field {field} does not match bound value"
            ]
    if binding.get("decision") not in {
        "PASS_WITH_NONBLOCKING_FINDINGS_MERGE_AUTHORIZED",
        "ACCEPT_WITHIN_SCOPE",
        "COMMIT_WITHIN_SCOPE",
    }:
        return INVALID_REVIEW_DECISION, ["review decision is not an allowed scoped acceptance"]
    sources = decision_artifact.get("external_sources")
    if not isinstance(sources, list) or len(sources) < 2:
        return INVALID_REVIEW_DECISION, [
            "review decision lacks external review and main-closeout source bindings"
        ]
    for source in sources:
        for field in ("repository", "path", "exact_commit", "git_blob", "sha256"):
            if _placeholder(source.get(field)):
                return PLACEHOLDER_VALUE, [
                    f"review decision external source {field} is placeholder"
                ]
    return GATE_PASS, []


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
                   current_surface_claim_ids=None, actor_index=None):
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
        code, errs = check_claim_digest_binding(claim)
        if errs:
            return _result(code, errs, claim.get("claim_id"))
        code, errs = check_actor_resolution_and_independence(claim, actor_index)
        if errs:
            return _result(code, errs, claim.get("claim_id"))
        code, errs = check_evidence_byte_bindings(
            claim, claim_path, actor_index
        )
        if errs:
            return _result(code, errs, claim.get("claim_id"))
        code, errs = check_review_decision_binding(claim)
        if errs:
            return _result(code, errs, claim.get("claim_id"))

    return _result(GATE_PASS, [], claim.get("claim_id"),
                   decision=("COMMIT" if committing else "DEFER"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Q34 discovery-commitment gate (fail-closed)")
    ap.add_argument("--claim", required=True, help="path to claim JSON")
    ap.add_argument("--registry", help="path to resolvable-evidence registry JSON (list of reference strings)")
    ap.add_argument("--current-main-head", help="current main head SHA for staleness check")
    ap.add_argument("--current-surface", help="path to JSON list of claim_ids on the Current/Accepted surface")
    ap.add_argument(
        "--actor-registry",
        default=str(ROOT / "data" / "discovery" / "actor-authority-registry.json"),
        help="canonical actor/reviewer authority registry",
    )
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

    actor_registry, aerr = _load_json(Path(args.actor_registry))
    if aerr:
        out = _result(SCHEMA_ERROR, [aerr], claim.get("claim_id"))
        return _emit(out, args)
    actor_index = _actor_index(actor_registry)
    if actor_index is None:
        out = _result(
            SCHEMA_ERROR,
            ["canonical actor registry is malformed or contains duplicate ids"],
            claim.get("claim_id"),
        )
        return _emit(out, args)

    out = validate_claim(
        claim, claim_path,
        registry_index=registry_index,
        current_main_head=args.current_main_head,
        require_external=args.require_external_attestation,
        require_review=args.require_independent_review,
        current_surface_claim_ids=current_surface,
        actor_index=actor_index,
    )
    return _emit(out, args)


def _emit(out, args):
    if args.report:
        Path(args.report).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return out["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
