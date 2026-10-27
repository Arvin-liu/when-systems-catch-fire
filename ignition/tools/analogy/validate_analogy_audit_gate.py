#!/usr/bin/env python3
"""Q37-I1 Analogy-Audit & Transportability Gate — fail-closed deterministic validator/CLI.

Decides whether a repository-local analogy-audit bundle is admissible. An analogy bundle must
declare source/target domain and constructs, a proposer and Q35 authority, an originating Q34
claim, a candidate type, an explicit mapping (entities, correspondence pairs, cardinality,
directionality, invariants, known mismatches, omitted variables, hidden premises, scale/time/context
differences, digest), mechanism evidence (distinct from shared form), a transportability assessment
(overlap, invariances, shifts, boundary, falsifier, uncertainty), and an audit decision (classification,
mapping consistency, mechanism-evidence sufficiency, transportability status, counteranalogy status,
Q38 search permission, allowed use, forbidden inference, downgraded claim ceiling).

The gate forbids:
  - metaphor / local isomorphism / selective correspondence / unaudited structural maps / Q36 residual
    from being written as mechanism identity, causal proof or cross-domain universal law;
  - a local structural similarity being widened into a universal causal regularity;
  - shared vocabulary / shared form / correlation / similar shape being treated as independent
    mechanism evidence (or a mechanism claim circularly referencing itself);
  - Q36 residual / anomaly being upgraded to a shared-cause proof;
  - a transportability claim without overlap / invariance / boundary / falsifier;
  - counteranalogy / negative evidence / failed mappings being deleted or suppressed;
  - Q14 claim not committed_current or disallowing the analogy purpose;
  - Q35 actor/grant/trajectory being invalid, expired or scope-mismatched;
  - Q33 rights gate being bypassed (unknown / rejected / pending external material as evidence);
  - Q38 case retrieval being started before the audit gate passes.

Repository governance only. Does NOT prove any two domains share a mechanism, does NOT prove
real-world causal transportability, does NOT perform Q38 case retrieval, does NOT add an L7 / truth
layer, does NOT materialize F15/D1/D2.

Stable exit codes (machine-consumable, never free-text PASS):
  0  GATE_PASS
  2  SCHEMA_ERROR                  - bundle failed JSON schema / required-field check
  3  DOMAIN_UNRESOLVABLE           - source/target def empty or domain swapped (mechanism evidence domains != candidate domains)
  4  CORRESPONDENCE_REF_INVALID    - mapping correspondence source/target not in declared entities
  5  CARDINALITY_DIRECTION_MISMATCH- declared cardinality/directionality inconsistent with entity counts
  6  RELATION_PRESERVATION_OVERCLAIM- relation-preservation asserts more than the mapping supports
  7  NEGATIVE_EVIDENCE_SUPPRESSED  - mapping hides known mismatch / omitted variable / hidden premise
  8  SHIFT_UNDECLARED              - scale/time/context or transportability shift undeclared
  9  MECHANISM_UPGRADE_FORBIDDEN   - shared form / similarity upgraded to mechanism identity
  10 MECHANISM_EVIDENCE_INSUFFICIENT- mechanism claim without independent evidence / circular self-reference
  11 RESIDUAL_AS_CAUSE             - Q36 residual / anomaly upgraded to a shared-cause proof
  12 TRANSPORTABILITY_INCOMPLETE   - transportability missing overlap / invariance / boundary / falsifier
  13 COUNTERANALOGY_SUPPRESSED     - counteranalogy / negative evidence / failed mapping deleted or suppressed
  14 Q14_CLAIM_NOT_COMMITTED       - originating Q34 claim not committed_current or disallows analogy purpose
  15 Q35_AUTHORITY_INVALID         - Q35 actor/grant/trajectory missing / expired / scope-mismatch
  16 Q33_RIGHTS_BYPASS             - Q33 rights gate bypassed (unknown / rejected / pending external material)
  17 UNRESOLVABLE_REF              - malformed exact_head / mapping_digest / dangling analogy_id ref
  18 CLAIM_CEILING_OVERREACH       - local structural similarity widened into a universal causal regularity
  19 Q38_START_FORBIDDEN           - Q38 case retrieval started before the audit gate passes
  20 NEGATIVE_AUDIT_DELETED        - negative audit result (counteranalogy / rejected) not preserved
  21 SEMANTIC_CONSISTENCY_MISMATCH - audit classification / mapping consistency inconsistent with candidate

Usage:
  python tools/analogy/validate_analogy_audit_gate.py --bundle <bundle.json> \
      [--current-head <sha>] [--now <iso>] [--report <out.json>]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from tools.observation.validate_observation_prediction_gate import _verify_git_binding
SCHEMA_PATH = ROOT / "schemas" / "analogy" / "analogy-audit-contract.schema.json"

GATE_PASS = 0
SCHEMA_ERROR = 2
DOMAIN_UNRESOLVABLE = 3
CORRESPONDENCE_REF_INVALID = 4
CARDINALITY_DIRECTION_MISMATCH = 5
RELATION_PRESERVATION_OVERCLAIM = 6
NEGATIVE_EVIDENCE_SUPPRESSED = 7
SHIFT_UNDECLARED = 8
MECHANISM_UPGRADE_FORBIDDEN = 9
MECHANISM_EVIDENCE_INSUFFICIENT = 10
RESIDUAL_AS_CAUSE = 11
TRANSPORTABILITY_INCOMPLETE = 12
COUNTERANALOGY_SUPPRESSED = 13
Q14_CLAIM_NOT_COMMITTED = 14
Q35_AUTHORITY_INVALID = 15
Q33_RIGHTS_BYPASS = 16
UNRESOLVABLE_REF = 17
CLAIM_CEILING_OVERREACH = 18
Q38_START_FORBIDDEN = 19
NEGATIVE_AUDIT_DELETED = 20
SEMANTIC_CONSISTENCY_MISMATCH = 21
CONTENT_BINDING_INVALID = 22
MAPPING_DIGEST_INVALID = 23
CURRENT_HEAD_INVALID = 24

EXIT_NAMES = {
    0: "GATE_PASS", 2: "SCHEMA_ERROR", 3: "DOMAIN_UNRESOLVABLE",
    4: "CORRESPONDENCE_REF_INVALID", 5: "CARDINALITY_DIRECTION_MISMATCH",
    6: "RELATION_PRESERVATION_OVERCLAIM", 7: "NEGATIVE_EVIDENCE_SUPPRESSED",
    8: "SHIFT_UNDECLARED", 9: "MECHANISM_UPGRADE_FORBIDDEN",
    10: "MECHANISM_EVIDENCE_INSUFFICIENT", 11: "RESIDUAL_AS_CAUSE",
    12: "TRANSPORTABILITY_INCOMPLETE", 13: "COUNTERANALOGY_SUPPRESSED",
    14: "Q14_CLAIM_NOT_COMMITTED", 15: "Q35_AUTHORITY_INVALID",
    16: "Q33_RIGHTS_BYPASS", 17: "UNRESOLVABLE_REF", 18: "CLAIM_CEILING_OVERREACH",
    19: "Q38_START_FORBIDDEN", 20: "NEGATIVE_AUDIT_DELETED", 21: "SEMANTIC_CONSISTENCY_MISMATCH",
    22: "CONTENT_BINDING_INVALID", 23: "MAPPING_DIGEST_INVALID", 24: "CURRENT_HEAD_INVALID",
}

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

# a local structural similarity / shared form upgraded into a shared mechanism identity
MECHANISM_UPGRADE_TOKENS = [
    "proves shared mechanism", "shared mechanism proven", "mechanism equivalence proven",
    "mechanism identity established", "same mechanism in both domains",
    "demonstrates identical mechanism", "establishes mechanism equivalence",
    "this similarity proves the mechanism", "is the same mechanism",
]
# a local structural similarity widened into a universal cross-domain causal regularity
UNIVERSAL_LAW_TOKENS = [
    "universal law", "universal causal law", "proves a general law",
    "cross-domain universal regularity", "general causal regularity proven",
    "universal mechanism", "holds in all domains", "proven universal principle",
    "universal regularity", "general law proven", "universal causal regularity",
]
# a Q36 residual / anomaly upgraded into a shared-cause proof
RESIDUAL_CAUSE_TOKENS = [
    "residual proves common cause", "the anomaly is the shared cause",
    "residual establishes shared cause", "the leftover proves the mechanism is the same",
    "residue proves common cause", "anomaly proves shared cause",
]

# allowed downward reclassifications in the audit decision (a gate pass may downgrade, never upgrade)
ALLOWED_DOWNGRADES = {
    ("MECHANISM_CANDIDATE", "STRUCTURAL_ANALOGY"),
    ("MECHANISM_CANDIDATE", "INSUFFICIENTLY_SPECIFIED"),
    ("TRANSPORTABILITY_CANDIDATE", "STRUCTURAL_ANALOGY"),
    ("TRANSPORTABILITY_CANDIDATE", "MECHANISM_CANDIDATE"),
    ("TRANSPORTABILITY_CANDIDATE", "INSUFFICIENTLY_SPECIFIED"),
}


def _parse_time(value):
    if not value:
        return None
    try:
        v = value.replace("Z", "+00:00")
        return datetime.fromisoformat(v).astimezone(timezone.utc)
    except Exception:
        return None


def _result(code, errors, decision=None):
    return {"gate": "q37_i1_analogy_audit_gate", "exit_code": code,
            "exit_name": EXIT_NAMES.get(code, "UNKNOWN"), "decision": decision, "errors": errors}


def _index(lst, key):
    return {item.get(key): item for item in lst if isinstance(item, dict) and item.get(key)}


def _emit(out, report_path):
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if report_path:
        Path(report_path).write_text(text + "\n", encoding="utf-8")


def _json_from_binding(binding):
    content, error = _verify_git_binding(binding)
    if error:
        return None, error
    try:
        return json.loads(content), None
    except (TypeError, json.JSONDecodeError):
        return None, "bound Git bytes are not valid JSON"


def check_runtime_current_head(bundle, current_head):
    errs = []
    if not current_head or not HEAD_RE.fullmatch(str(current_head)):
        return ["--current-head must supply an exact 40-hex commit"]
    kind = subprocess.run(["git", "cat-file", "-t", current_head], cwd=ROOT, capture_output=True, text=True)
    if kind.returncode or kind.stdout.strip() != "commit":
        return [f"--current-head {current_head} is not an existing commit object"]
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if actual.returncode or actual.stdout.strip() != current_head:
        errs.append(f"--current-head {current_head} does not equal checked-out HEAD {actual.stdout.strip()}")
    return errs


def _mapping_digest(mapping):
    payload = {key: value for key, value in mapping.items() if key != "mapping_digest"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def check_mapping_digests(bundle):
    return [
        f"mapping {mapping.get('mapping_id')}: mapping_digest does not match canonical semantic content"
        for mapping in bundle.get("mappings", [])
        if mapping.get("mapping_digest") != _mapping_digest(mapping)
    ]


def check_canonical_content_bindings(bundle):
    errs = []
    bindings = bundle.get("canonical_bindings") or {}
    expected_paths = {
        "q34_claim_source": "data/discovery/claims/q33-seven-governance-components-current.json",
        "q35_actor_registry": "data/agent/canonical-actor-registry.json",
        "q35_grant_registry": "data/agent/canonical-grant-registry.json",
        "q35_action_source": "data/agent/pilot-q34-pr-controlled-op.json",
        "q36_obs_source": "data/observation/pilot-q34-closure-drift-prediction.json",
        "q36_int_source": "data/intervention/pilot-controlled-intervention.json",
    }
    documents = {}
    for name, expected_path in expected_paths.items():
        binding = bindings.get(name)
        if not isinstance(binding, dict) or binding.get("path") != expected_path:
            errs.append(f"canonical binding {name}: exact repository path required")
            continue
        document, error = _json_from_binding(binding)
        if error:
            errs.append(f"canonical binding {name}: {error}")
        else:
            documents[name] = document
    if errs:
        return errs

    claim_source = documents["q34_claim_source"]
    actors = _index(documents["q35_actor_registry"].get("actors", []), "actor_id")
    grant_registry = _index(documents["q35_grant_registry"].get("grants", []), "grant_id")
    q35_source = documents["q35_action_source"]
    q35_actions = _index(q35_source.get("actions", []), "action_id")
    q35_grants = _index(q35_source.get("grants", []), "grant_id")
    embedded_claims = _index(bundle.get("q34_claims", []), "claim_id")
    embedded_grants = _index(bundle.get("q35_grants", []), "grant_id")

    for candidate in bundle.get("analogy_candidates", []):
        cid = candidate.get("analogy_id")
        claim_id = candidate.get("originating_q34_claim_ref")
        expected_claim = {
            "claim_id": claim_source.get("claim_id"),
            "status": claim_source.get("state"),
            "claim_ceiling": claim_source.get("claim_ceiling"),
            "allows_analogy_purpose": True,
            "source_ref": bindings["q34_claim_source"]["path"],
        }
        if claim_id != claim_source.get("claim_id") or claim_source.get("state") != "committed_current" or embedded_claims.get(claim_id) != expected_claim:
            errs.append(f"candidate {cid}: Q34 seed is not the canonical committed claim bytes")

        proposer = candidate.get("proposer")
        if not actors.get(proposer) or actors[proposer].get("status") != "active":
            errs.append(f"candidate {cid}: proposer is not a canonical active Q35 actor")
        grant_id = candidate.get("q35_authority_ref")
        entry = grant_registry.get(grant_id)
        grant_artifact = None
        if entry:
            grant_doc, error = _json_from_binding(entry.get("binding"))
            if not error:
                grant_artifact = _index(grant_doc.get("grants", []), "grant_id").get(grant_id)
        action = q35_actions.get("act-q34-pilot")
        expected_grant = None
        if grant_artifact:
            expected_grant = {
                "grant_id": grant_id,
                "status": "revoked" if grant_artifact.get("revoked") else grant_artifact.get("status"),
                "grant_expires_at": grant_artifact.get("expires_at"),
                "scope": "repository explanation",
                "grantee": grant_artifact.get("grantee"),
                "granted_by": grant_artifact.get("grantor"),
                "action_refs": ["act-q34-pilot"],
            }
        if not entry or not grant_artifact or embedded_grants.get(grant_id) != expected_grant or q35_grants.get(grant_id) != grant_artifact or not action or action.get("grant_id") != grant_id:
            errs.append(f"candidate {cid}: Q35 grant/action is fictional, copied or not canonically byte-bound")

        expected_refs = {bindings["q36_obs_source"]["path"], bindings["q36_int_source"]["path"]}
        supplied_refs = set(candidate.get("evidence_refs", []))
        evidence_bindings = candidate.get("evidence_bindings") or []
        bound_refs = set()
        for binding in evidence_bindings:
            _, error = _verify_git_binding(binding)
            if error:
                errs.append(f"candidate {cid}: evidence binding invalid: {error}")
            else:
                bound_refs.add(binding.get("path"))
        if not expected_refs.issubset(supplied_refs) or not expected_refs.issubset(bound_refs):
            errs.append(f"candidate {cid}: Q36-OBS/Q36-INT evidence is not bound to actual repository bytes")
        for ref in supplied_refs:
            if ref.startswith("ext:") or ref.startswith("external:"):
                errs.append(f"candidate {cid}: fictive/unretrieved external evidence ref {ref!r} is forbidden")
    return errs


def validate_schema(bundle):
    """Authoritative JSON-Schema validation when jsonschema is available; a hand-rolled
    structural fallback otherwise (covers the critical required fields + enum/pattern basics)."""
    try:
        import jsonschema
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        errs = []
        for e in sorted(validator.iter_errors(bundle), key=lambda x: list(x.absolute_path)):
            path = ".".join(str(p) for p in e.absolute_path) or "<root>"
            errs.append(f"{path}: {e.message}")
            if len(errs) >= 25:
                errs.append("... (truncated)")
                break
        return errs
    except ImportError:
        errs = []
        for field in ("analogy_candidates", "mappings", "mechanism_evidence",
                     "transportability_assessments", "audit_decisions"):
            if field not in bundle or not isinstance(bundle.get(field), list):
                errs.append(f"missing required array: {field}")
        # minimal per-item required-field check for the five mandatory arrays
        req = {
            "analogy_candidates": ["analogy_id", "source_domain", "target_domain", "source_def",
                                   "target_def", "proposer", "q35_authority_ref",
                                   "originating_q34_claim_ref", "purpose", "candidate_type",
                                   "evidence_refs", "provenance", "claim_ceiling", "lifecycle",
                                   "exact_head"],
            "mappings": ["mapping_id", "analogy_id", "source_entities", "target_entities",
                         "correspondence_pairs", "relation_preservation", "directionality",
                         "cardinality", "cardinality_rationale", "invariants", "known_mismatches",
                         "omitted_variables", "hidden_premises", "scale_time_context_differences",
                         "representation_level", "mapping_digest"],
            "mechanism_evidence": ["evidence_id", "analogy_id", "source_domain_ref",
                                   "target_domain_ref", "evidence_kind", "status",
                                   "prohibited_promotions", "exact_head"],
            "transportability_assessments": ["assessment_id", "analogy_id", "source_population",
                                             "target_population", "transport_target",
                                             "required_invariances", "covariate_shift",
                                             "concept_measurement_shift", "mechanism_moderator_shift",
                                             "scale_time_regime_shift", "support_overlap",
                                             "boundary_conditions", "excluded_scopes", "uncertainty",
                                             "falsification_conditions", "status", "exact_head"],
            "audit_decisions": ["decision_id", "analogy_id", "classification", "mapping_consistency",
                                "mechanism_evidence_sufficiency", "transportability_status",
                                "counteranalogy_status", "q38_search_permission", "allowed_use",
                                "forbidden_inference", "downgraded_claim_ceiling",
                                "unresolved_issues", "reviewer_verifier", "exact_head"],
        }
        for field, fields in req.items():
            for item in bundle.get(field, []) or []:
                for f in fields:
                    if f not in item:
                        errs.append(f"{field} {item.get('analogy_id', item.get('mapping_id', item.get('evidence_id', item.get('assessment_id', item.get('decision_id', '?')))))}: missing {f}")
        return errs


def check_unresolvable_ref(bundle, current_head):
    errs = []
    # all analogy_ids referenced must resolve to a declared candidate
    cand_ids = {c.get("analogy_id") for c in bundle.get("analogy_candidates", [])}
    for field, key in (("mappings", "mapping_id"), ("mechanism_evidence", "evidence_id"),
                       ("transportability_assessments", "assessment_id"),
                       ("audit_decisions", "decision_id")):
        for item in bundle.get(field, []) or []:
            aid = item.get("analogy_id")
            if aid and aid not in cand_ids:
                errs.append(f"{field} {item.get(key)}: dangling analogy_id '{aid}' (no such candidate)")
    # exact_head + digest well-formed and (if given) matching the frozen head
    for c in bundle.get("analogy_candidates", []):
        if c.get("exact_head") == "CLI_CURRENT_HEAD":
            pass
        elif not HEAD_RE.match(str(c.get("exact_head", ""))):
            errs.append(f"candidate {c.get('analogy_id')}: malformed exact_head")
        if current_head and c.get("exact_head") and c.get("exact_head") not in (current_head, "CLI_CURRENT_HEAD"):
            errs.append(f"candidate {c.get('analogy_id')}: exact_head {c.get('exact_head')} "
                        f"!= required {current_head}")
    for m in bundle.get("mappings", []):
        if not HEAD_RE.match(str(m.get("exact_head", ""))) if "exact_head" in m else False:
            # mapping has no exact_head field; only check digest
            pass
        if not SHA256_RE.match(str(m.get("mapping_digest", ""))):
            errs.append(f"mapping {m.get('mapping_id')}: malformed mapping_digest")
    for o in bundle.get("mechanism_evidence", []):
        if o.get("exact_head") != "CLI_CURRENT_HEAD" and not HEAD_RE.match(str(o.get("exact_head", ""))):
            errs.append(f"mechanism_evidence {o.get('evidence_id')}: malformed exact_head")
    for t in bundle.get("transportability_assessments", []):
        if t.get("exact_head") != "CLI_CURRENT_HEAD" and not HEAD_RE.match(str(t.get("exact_head", ""))):
            errs.append(f"transportability {t.get('assessment_id')}: malformed exact_head")
    for d in bundle.get("audit_decisions", []):
        if d.get("exact_head") != "CLI_CURRENT_HEAD" and not HEAD_RE.match(str(d.get("exact_head", ""))):
            errs.append(f"audit_decision {d.get('decision_id')}: malformed exact_head")
    return errs


def check_domain_resolvable(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    for c in bundle.get("analogy_candidates", []):
        if not str(c.get("source_def", "")).strip() or not str(c.get("target_def", "")).strip():
            errs.append(f"candidate {c.get('analogy_id')}: empty source_def/target_def "
                        f"(domain construct not resolvable)")
    # mechanism evidence domains must not silently swap the candidate's domains
    for me in bundle.get("mechanism_evidence", []):
        c = cands.get(me.get("analogy_id"))
        if not c:
            continue
        if me.get("source_domain_ref") and me.get("source_domain_ref") != c.get("source_domain"):
            errs.append(f"mechanism_evidence {me.get('evidence_id')}: source_domain_ref "
                        f"'{me.get('source_domain_ref')}' swapped from candidate source "
                        f"'{c.get('source_domain')}'")
        if me.get("target_domain_ref") and me.get("target_domain_ref") != c.get("target_domain"):
            errs.append(f"mechanism_evidence {me.get('evidence_id')}: target_domain_ref "
                        f"'{me.get('target_domain_ref')}' swapped from candidate target "
                        f"'{c.get('target_domain')}'")
    return errs


def check_correspondence_refs(bundle):
    errs = []
    for m in bundle.get("mappings", []):
        src = set(m.get("source_entities", []))
        tgt = set(m.get("target_entities", []))
        for pair in m.get("correspondence_pairs", []):
            s = pair.get("source")
            t = pair.get("target")
            if s and s not in src:
                errs.append(f"mapping {m.get('mapping_id')}: correspondence source '{s}' "
                            f"not in declared source_entities")
            if t and t not in tgt:
                errs.append(f"mapping {m.get('mapping_id')}: correspondence target '{t}' "
                            f"not in declared target_entities")
    return errs


def check_cardinality_direction(bundle):
    errs = []
    for m in bundle.get("mappings", []):
        ns = len(m.get("source_entities", []))
        nt = len(m.get("target_entities", []))
        computed = None
        if ns == nt == 1:
            computed = "1:1"
        elif ns == 1 and nt > 1:
            computed = "1:n"
        elif ns > 1 and nt == 1:
            computed = "n:1"
        elif ns > 1 and nt > 1:
            computed = "n:m"
        declared = m.get("cardinality")
        if computed and declared and computed != declared:
            errs.append(f"mapping {m.get('mapping_id')}: declared cardinality '{declared}' "
                        f"inconsistent with entity counts (source {ns}, target {nt}) -> '{computed}'")
        # directionality must be declared when correspondence pairs exist
        if m.get("correspondence_pairs") and m.get("directionality") == "none":
            errs.append(f"mapping {m.get('mapping_id')}: directionality 'none' but correspondence "
                        f"pairs declared (must declare forward/backward/bidirectional)")
    return errs


def check_relation_preservation(bundle):
    errs = []
    for m in bundle.get("mappings", []):
        rp = str(m.get("relation_preservation", "")).lower()
        if not rp:
            continue
        qualities = [p.get("quality") for p in m.get("correspondence_pairs", [])]
        if qualities and all(q in ("analogous_only", "approximate") for q in qualities):
            overclaim = ("identical", "exactly preserved", "isomorphism holds exactly",
                         "fully isomorphic", "preserves exactly")
            if any(tok in rp for tok in overclaim):
                errs.append(f"mapping {m.get('mapping_id')}: relation_preservation overclaims "
                            f"('{rp}') beyond analogous/approximate correspondence support")
    return errs


def check_negative_evidence_suppressed(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    for m in bundle.get("mappings", []):
        c = cands.get(m.get("analogy_id"))
        ctype = c.get("candidate_type") if c else None
        if ctype == "INSUFFICIENTLY_SPECIFIED":
            continue
        km = m.get("known_mismatches") or []
        ov = m.get("omitted_variables") or []
        hp = m.get("hidden_premises") or []
        if not km and not ov and not hp:
            errs.append(f"mapping {m.get('mapping_id')}: suspiciously clean — no known_mismatch, "
                        f"omitted_variable or hidden_premise declared (negative evidence suppressed)")
    return errs


def check_shift_undeclared(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    for m in bundle.get("mappings", []):
        c = cands.get(m.get("analogy_id"))
        cross_domain = bool(c) and c.get("source_domain") and c.get("target_domain") \
            and c.get("source_domain") != c.get("target_domain")
        if cross_domain and not (m.get("scale_time_context_differences") or []):
            errs.append(f"mapping {m.get('mapping_id')}: cross-domain mapping with no declared "
                        f"scale/time/context difference (shift undeclared)")
    for t in bundle.get("transportability_assessments", []):
        for fld in ("covariate_shift", "concept_measurement_shift", "mechanism_moderator_shift",
                    "scale_time_regime_shift"):
            if not str(t.get(fld, "")).strip():
                errs.append(f"transportability {t.get('assessment_id')}: undeclared shift '{fld}'")
    return errs


def check_mechanism_upgrade_forbidden(bundle):
    errs = []
    for c in bundle.get("analogy_candidates", []):
        ctype = c.get("candidate_type")
        if ctype in ("METAPHOR_ONLY", "SURFACE_SIMILARITY"):
            text = str(c.get("claim_ceiling", ""))
            for tok in MECHANISM_UPGRADE_TOKENS + UNIVERSAL_LAW_TOKENS:
                if tok in text.lower():
                    errs.append(f"candidate {c.get('analogy_id')}: {ctype} upgraded to mechanism "
                                f"identity via claim_ceiling token '{tok}'")
                    break
    return errs


def check_mechanism_evidence(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    ev_by_analogy = {}
    for me in bundle.get("mechanism_evidence", []):
        ev_by_analogy.setdefault(me.get("analogy_id"), []).append(me)
    # shared form must not be treated as independent mechanism evidence
    for me in bundle.get("mechanism_evidence", []):
        if me.get("evidence_kind") in ("SHARED_VOCABULARY_ONLY", "SHARED_MATHEMATICAL_FORM",
                                        "SHARED_CAUSAL_GRAPH_CANDIDATE", "SHARED_PROCESS_EVIDENCE") \
           and me.get("status") == "BOUNDED_MECHANISM_EVIDENCE":
            errs.append(f"mechanism_evidence {me.get('evidence_id')}: shared form "
                        f"('{me.get('evidence_kind')}') must not be BOUNDED_MECHANISM_EVIDENCE")
        # circular self-reference
        if me.get("status") == "BOUNDED_MECHANISM_EVIDENCE":
            ref = me.get("mechanism_evidence_ref")
            if not ref:
                errs.append(f"mechanism_evidence {me.get('evidence_id')}: BOUNDED_MECHANISM_EVIDENCE "
                            f"missing mechanism_evidence_ref")
            elif ref == me.get("evidence_id"):
                errs.append(f"mechanism_evidence {me.get('evidence_id')}: circularly references "
                            f"itself as its own evidence")
    # MECHANISM_CANDIDATE requires at least one non-insufficient mechanism evidence
    for cid, c in cands.items():
        if c.get("candidate_type") != "MECHANISM_CANDIDATE":
            continue
        evs = ev_by_analogy.get(cid, [])
        if not evs or all(e.get("status") in ("INSUFFICIENT", "CONTRADICTED", "UNRESOLVED")
                          for e in evs):
            errs.append(f"candidate {cid}: MECHANISM_CANDIDATE without independent mechanism "
                        f"evidence (all evidence INSUFFICIENT/CONTRADICTED/UNRESOLVED)")
    return errs


def check_residual_as_cause(bundle):
    errs = []
    obs_ids = {o.get("observation_id") for o in bundle.get("q36_obs_snapshots", [])}
    for c in bundle.get("analogy_candidates", []):
        refs = set(c.get("evidence_refs", []))
        if refs & obs_ids:
            text = str(c.get("claim_ceiling", "")) + " " + str(c.get("provenance", ""))
            for tok in RESIDUAL_CAUSE_TOKENS:
                if tok in text.lower():
                    errs.append(f"candidate {c.get('analogy_id')}: Q36 residual upgraded to "
                                f"shared-cause proof via token '{tok}'")
                    break
    return errs


def check_transportability_incomplete(bundle):
    errs = []
    for t in bundle.get("transportability_assessments", []):
        if not (t.get("required_invariances") or []):
            errs.append(f"transportability {t.get('assessment_id')}: missing required_invariances")
        if not str(t.get("support_overlap", "")).strip():
            errs.append(f"transportability {t.get('assessment_id')}: missing support_overlap")
        if not (t.get("boundary_conditions") or []):
            errs.append(f"transportability {t.get('assessment_id')}: missing boundary_conditions")
        if not (t.get("falsification_conditions") or []):
            errs.append(f"transportability {t.get('assessment_id')}: missing falsification_conditions")
        if t.get("status") == "TRANSPORTABLE_WITHIN_DECLARED_SCOPE" and not str(t.get("uncertainty", "")).strip():
            errs.append(f"transportability {t.get('assessment_id')}: TRANSPORTABLE_WITHIN_DECLARED_SCOPE "
                        f"requires an uncertainty statement")
    return errs


def check_counteranalogy_suppressed(bundle):
    errs = []
    for d in bundle.get("audit_decisions", []):
        if d.get("counteranalogy_status") == "SUPPRESSED_DETECTED":
            errs.append(f"audit_decision {d.get('decision_id')}: counteranalogy / negative evidence "
                        f"marked SUPPRESSED_DETECTED (deleted or suppressed)")
    # a COUNTERANALOGY candidate must be preserved (PRESENT_PRESERVED), not suppressed
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    decs = _index(bundle.get("audit_decisions", []), "analogy_id")
    for cid, c in cands.items():
        if c.get("candidate_type") == "COUNTERANALOGY":
            d = decs.get(cid)
            if d and d.get("counteranalogy_status") == "SUPPRESSED_DETECTED":
                errs.append(f"candidate {cid}: COUNTERANALOGY suppressed (must be PRESENT_PRESERVED)")
    return errs


def check_q14_commitment(bundle):
    errs = []
    states = {}
    allows = {}
    for c in bundle.get("q34_claims", []) or []:
        states[c.get("claim_id")] = c.get("status")
        allows[c.get("claim_id")] = c.get("allows_analogy_purpose", False)
    for c in bundle.get("analogy_candidates", []):
        ref = c.get("originating_q34_claim_ref")
        if not ref:
            errs.append(f"candidate {c.get('analogy_id')}: missing originating_q34_claim_ref")
            continue
        if ref not in states:
            errs.append(f"candidate {c.get('analogy_id')}: Q34 claim '{ref}' not present in bundle")
            continue
        if states[ref] != "committed_current":
            errs.append(f"candidate {c.get('analogy_id')}: Q34 claim '{ref}' status "
                        f"'{states[ref]}' is not committed_current")
        if allows.get(ref) is not True:
            errs.append(f"candidate {c.get('analogy_id')}: Q34 claim '{ref}' does not allow "
                        f"the analogy purpose")
    return errs


def check_q35_authority(bundle, now):
    errs = []
    grants = _index(bundle.get("q35_grants", []) or [], "grant_id")
    now_t = _parse_time(now) if now else datetime.now(timezone.utc)
    for c in bundle.get("analogy_candidates", []):
        gid = c.get("q35_authority_ref")
        if not gid:
            errs.append(f"candidate {c.get('analogy_id')}: missing q35_authority_ref")
            continue
        g = grants.get(gid)
        if not g:
            errs.append(f"candidate {c.get('analogy_id')}: Q35 grant '{gid}' not resolvable in bundle")
            continue
        if g.get("status") != "active":
            errs.append(f"candidate {c.get('analogy_id')}: Q35 grant '{gid}' status "
                        f"'{g.get('status')}' is not active")
        exp = _parse_time(g.get("grant_expires_at"))
        if exp and now_t and now_t > exp:
            errs.append(f"candidate {c.get('analogy_id')}: Q35 grant '{gid}' expired at "
                        f"{g.get('grant_expires_at')}")
        scope = g.get("scope", "")
        purpose = c.get("purpose", "")
        if scope and purpose and purpose not in scope and scope not in purpose:
            errs.append(f"candidate {c.get('analogy_id')}: Q35 grant '{gid}' scope '{scope}' "
                        f"does not cover analogy purpose '{purpose}'")
    return errs


def check_q33_rights(bundle):
    errs = []
    rights = {}
    for r in bundle.get("q33_rights", []) or []:
        rights[r.get("material_id")] = r.get("rights_status")
    if not rights:
        return errs  # no rights registry in bundle -> not a bypass (caller may supply externally)
    refs = set()
    for c in bundle.get("analogy_candidates", []):
        for r in c.get("evidence_refs", []):
            refs.add(r)
    for me in bundle.get("mechanism_evidence", []):
        if me.get("independent_evidence_ref"):
            refs.add(me.get("independent_evidence_ref"))
    for rid in refs:
        st = rights.get(rid)
        if st is None:
            # unknown external material referenced as evidence without a clear rights record
            if "ext" in str(rid).lower() or any("external" in str(c.get("provenance", "")).lower()
                                                 for c in bundle.get("analogy_candidates", [])
                                                 if rid in c.get("evidence_refs", [])):
                errs.append(f"evidence ref '{rid}': external material with no Q33 rights record "
                            f"(rights gate bypassed)")
        elif st != "clear":
            errs.append(f"evidence ref '{rid}': Q33 rights_status '{st}' is not clear "
                        f"(rights gate bypassed)")
    return errs


def check_claim_ceiling_overreach(bundle):
    errs = []
    for c in bundle.get("analogy_candidates", []):
        if any(tok in str(c.get("claim_ceiling", "")).lower() for tok in UNIVERSAL_LAW_TOKENS):
            errs.append(f"candidate {c.get('analogy_id')}: claim_ceiling widens a local structural "
                        f"similarity into a universal causal regularity")
    for d in bundle.get("audit_decisions", []):
        if any(tok in str(d.get("downgraded_claim_ceiling", "")).lower() for tok in UNIVERSAL_LAW_TOKENS):
            errs.append(f"audit_decision {d.get('decision_id')}: downgraded_claim_ceiling still "
                        f"asserts a universal causal regularity")
    return errs


def check_q38_start_forbidden(bundle):
    errs = []
    if bundle.get("q38_case_retrieval_started") is True:
        errs.append("q38_case_retrieval_started is true (Q38 case retrieval must not start before "
                    "the Q37 audit gate passes)")
    return errs


def check_negative_audit_deleted(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    decs = {d.get("analogy_id") for d in bundle.get("audit_decisions", [])}
    for cid, c in cands.items():
        if c.get("candidate_type") == "COUNTERANALOGY" or c.get("lifecycle", {}).get("status") in (
                "rejected", "deprecated"):
            if cid not in decs:
                errs.append(f"candidate {cid}: negative / counteranalogy candidate has no audit "
                            f"decision (negative audit result not preserved)")
    return errs


def check_semantic_consistency(bundle):
    errs = []
    cands = _index(bundle.get("analogy_candidates", []), "analogy_id")
    decs = _index(bundle.get("audit_decisions", []), "analogy_id")
    for cid, c in cands.items():
        d = decs.get(cid)
        if not d:
            continue
        cls = d.get("classification")
        ctype = c.get("candidate_type")
        if cls != ctype and (ctype, cls) not in ALLOWED_DOWNGRADES:
            errs.append(f"candidate {cid}: audit classification '{cls}' inconsistent with candidate "
                        f"type '{ctype}' (not an allowed downgrade)")
    return errs


def main():
    ap = argparse.ArgumentParser(description="Q37-I1 analogy-audit & transportability gate (fail-closed)")
    ap.add_argument("--bundle", required=True, help="path to Q37-I1 analogy-audit bundle JSON")
    ap.add_argument("--claims", help="(optional) path to Q34 claims registry JSON (overrides bundle q34_claims)")
    ap.add_argument("--q35", help="(optional) path to Q35 grants JSON (overrides bundle q35_grants)")
    ap.add_argument("--q33-rights", help="(optional) path to Q33 rights JSON (overrides bundle q33_rights)")
    ap.add_argument("--current-head", help="required exact head SHA for candidates/evidence/decisions")
    ap.add_argument("--now", help="reference 'now' ISO time for grant-expiry checks (default: utc now)")
    ap.add_argument("--report", help="write machine-readable JSON report to this path")
    args = ap.parse_args()

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    # allow external registries to override the embedded read-only snapshots
    if args.claims:
        bundle["q34_claims"] = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
    if args.q35:
        bundle["q35_grants"] = json.loads(Path(args.q35).read_text(encoding="utf-8")).get("grants", [])
    if args.q33_rights:
        bundle["q33_rights"] = json.loads(Path(args.q33_rights).read_text(encoding="utf-8")).get("rights", [])

    checks = [
        (SCHEMA_ERROR, lambda: validate_schema(bundle)),
        (CURRENT_HEAD_INVALID, lambda: check_runtime_current_head(bundle, args.current_head)),
        (UNRESOLVABLE_REF, lambda: check_unresolvable_ref(bundle, args.current_head)),
        (DOMAIN_UNRESOLVABLE, lambda: check_domain_resolvable(bundle)),
        (CORRESPONDENCE_REF_INVALID, lambda: check_correspondence_refs(bundle)),
        (CARDINALITY_DIRECTION_MISMATCH, lambda: check_cardinality_direction(bundle)),
        (RELATION_PRESERVATION_OVERCLAIM, lambda: check_relation_preservation(bundle)),
        (NEGATIVE_EVIDENCE_SUPPRESSED, lambda: check_negative_evidence_suppressed(bundle)),
        (SHIFT_UNDECLARED, lambda: check_shift_undeclared(bundle)),
        (MECHANISM_UPGRADE_FORBIDDEN, lambda: check_mechanism_upgrade_forbidden(bundle)),
        (MECHANISM_EVIDENCE_INSUFFICIENT, lambda: check_mechanism_evidence(bundle)),
        (RESIDUAL_AS_CAUSE, lambda: check_residual_as_cause(bundle)),
        (TRANSPORTABILITY_INCOMPLETE, lambda: check_transportability_incomplete(bundle)),
        (COUNTERANALOGY_SUPPRESSED, lambda: check_counteranalogy_suppressed(bundle)),
        (SEMANTIC_CONSISTENCY_MISMATCH, lambda: check_semantic_consistency(bundle)),
        (Q14_CLAIM_NOT_COMMITTED, lambda: check_q14_commitment(bundle)),
        (Q35_AUTHORITY_INVALID, lambda: check_q35_authority(bundle, args.now)),
        (Q33_RIGHTS_BYPASS, lambda: check_q33_rights(bundle)),
        (CLAIM_CEILING_OVERREACH, lambda: check_claim_ceiling_overreach(bundle)),
        (Q38_START_FORBIDDEN, lambda: check_q38_start_forbidden(bundle)),
        (NEGATIVE_AUDIT_DELETED, lambda: check_negative_audit_deleted(bundle)),
        (MAPPING_DIGEST_INVALID, lambda: check_mapping_digests(bundle)),
        (CONTENT_BINDING_INVALID, lambda: check_canonical_content_bindings(bundle)),
    ]

    for code, fn in checks:
        errs = fn()
        if errs:
            out = _result(code, errs)
            _emit(out, args.report)
            sys.exit(code)

    out = _result(GATE_PASS, [], decision={
        "verdict": "ADMISSIBLE_WITHIN_DECLARED_SCOPE",
        "note": "Repository-native analogy-audit admissibility only; not a claim that any two domains "
                "share a mechanism, that real-world causal transportability is proven, or that a "
                "universal cross-domain law holds. Q38 case retrieval remains gated.",
    })
    _emit(out, args.report)
    sys.exit(GATE_PASS)


if __name__ == "__main__":
    main()
