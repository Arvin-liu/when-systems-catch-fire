#!/usr/bin/env python3
"""Shared semantic evaluator primitive for repair-r3 (RB09-CALLER-ASSERTED-SEMANTICS).

This module is the single, capability-agnostic recomputation core. A capability
gate supplies three things via its ``CONFIG``:

  * ``CONFIG["evaluator"]``  – a callable ``(bundle, config, evidence) -> EvalReport``
  * ``CONFIG["evidence_matrix"]`` – ``rule_id -> {"roles": [...], "types": [...]}``
  * a ``rule_fields`` binding (carried by the per-capability evaluator closure)

The evaluator recomputes EVERY rule predicate from the bundle's record ``value``
fields and the engine-verified ``evidence`` bytes. Caller-declared ``facts[rid]``
and ``rule_assertions[rid].status`` are treated as *declarations only* and are
NEVER read as truth.

Contract objects (documentation, also enforced structurally by the engine):

  ResolvedEvidence = dict with keys:
      evidence_id, declared_role, record_type, rights_status,
      repository_relative_path, commit_sha, blob_sha, sha256, exact_head,
      bytes  (authoritative bytes from ``git show {commit_sha}:{path}``),
      decoded (typed decode when record_type indicates structure, else str).

  RuleResult = {"rule_id", "verdict": "PASS"|"FAIL",
                "used_evidence": list[str], "detail": str}
  EvalReport = {"capability", "results": dict[rule_id, RuleResult]}
"""
import json

__all__ = ["semantic_evaluate"]


def _text_of(ev):
    """Return a normalized text form of a ResolvedEvidence's authoritative bytes."""
    b = ev.get("bytes")
    if isinstance(b, (bytes, bytearray)):
        return b.decode("utf-8", "replace")
    d = ev.get("decoded")
    if isinstance(d, str):
        return d
    if isinstance(d, (bytes, bytearray)):
        return d.decode("utf-8", "replace")
    if isinstance(d, (dict, list)):
        return json.dumps(d, sort_keys=True, ensure_ascii=False)
    return ""


def _val_str(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def semantic_evaluate(bundle, config, evidence, matrix, rule_fields):
    """Recompute every rule from record values + evidence bytes.

    ``matrix`` maps rule_id -> {"roles":[allowed declared_role], "types":[allowed record_type]}.
    ``rule_fields`` maps rule_id -> the primary boundedField name whose ``value``
    must be corroborated by evidence bytes for that rule.

    Returns an EvalReport keyed EXACTLY by ``config["rules"]``.
    """
    results = {}
    assertions = {}
    for a in bundle.get("rule_assertions", []):
        if isinstance(a, dict) and a.get("rule_id"):
            assertions[a["rule_id"]] = a

    # Index records: field -> (value, evidence_refs)
    field_values = {}
    field_refs = {}
    for rec in bundle.get("records", []):
        if not isinstance(rec, dict):
            continue
        for k, v in rec.items():
            if k in ("record_id", "record_type"):
                continue
            if isinstance(v, dict) and "value" in v:
                if k not in field_values:
                    field_values[k] = v["value"]
                refs = v.get("evidence_refs")
                if isinstance(refs, list) and k not in field_refs:
                    field_refs[k] = refs

    for rid in config["rules"]:
        spec = matrix.get(rid) or {"roles": [], "types": []}
        allowed_roles = set(spec.get("roles") or [])
        allowed_types = set(spec.get("types") or [])
        fld = rule_fields.get(rid)
        used = []
        detail = ""
        verdict = "PASS"

        # Resolve which evidence objects this rule points at.
        refs = []
        if fld and fld in field_refs:
            refs = list(field_refs[fld])
        if not refs and rid in assertions:
            refs = list(assertions[rid].get("evidence_refs") or [])
        if not refs:
            # Fallback: any registered evidence whose role is allowed for this rule.
            refs = [
                eid for eid, ev in evidence.items()
                if ev.get("declared_role") in allowed_roles
            ]

        if not refs:
            results[rid] = {
                "rule_id": rid,
                "verdict": "FAIL",
                "used_evidence": [],
                "detail": f"{rid}: no evidence bound to this rule (declarations ignored)",
            }
            continue

        blob_texts = []
        for ref in refs:
            ev = evidence.get(ref)
            if ev is None:
                continue
            used.append(ref)
            role = ev.get("declared_role")
            rtype = ev.get("record_type")
            if allowed_roles and role not in allowed_roles:
                verdict = "FAIL"
                detail = (
                    f"{rid}: evidence {ref} declared_role {role!r} not in allowed "
                    f"set {sorted(allowed_roles)}"
                )
                break
            if allowed_types and rtype not in allowed_types:
                verdict = "FAIL"
                detail = (
                    f"{rid}: evidence {ref} record_type {rtype!r} not in allowed "
                    f"set {sorted(allowed_types)}"
                )
                break
            blob_texts.append(_text_of(ev))

        if verdict == "FAIL":
            results[rid] = {
                "rule_id": rid,
                "verdict": "FAIL",
                "used_evidence": used,
                "detail": detail,
            }
            continue

        # Content corroboration: record value must be corroborated by evidence bytes.
        val = field_values.get(fld) if fld else None
        val_s = _val_str(val)
        combined = "\n".join(blob_texts)
        if fld is None:
            # Structural rule with no primary field binding: role/type gate already applied.
            pass
        elif val_s == "":
            verdict = "FAIL"
            detail = (
                f"{rid}: record field {fld!r} has empty/absent value "
                f"(nothing to corroborate against evidence)"
            )
        elif val_s not in combined and combined not in val_s:
            verdict = "FAIL"
            detail = (
                f"{rid}: record field {fld!r} value is not corroborated by evidence "
                f"bytes (caller-asserted facts/status are NOT truth authority)"
            )

        results[rid] = {
            "rule_id": rid,
            "verdict": verdict,
            "used_evidence": used,
            "detail": detail,
        }

    return {"capability": config["capability"], "results": results}
