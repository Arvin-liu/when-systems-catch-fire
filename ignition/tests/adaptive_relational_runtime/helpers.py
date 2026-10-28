"""Shared builders for ARR commit-4 fixtures, attacks, and tests.

These builders produce schema-valid Source / Observation / Assertion / Relation
records. Projection hints that the closed relation schema cannot carry directly
are placed in the schema-permitted `extensions` namespace (keys prefixed `x_`),
exactly as the runtime engine reads them in runtime.py.

No license header: this is a test helper, matching the repo tests/ convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tools.adaptive_relational_runtime import canonical  # noqa: E402

T = "2026-07-24T00:00:00Z"


def _rid(prefix: str, obj: dict) -> str:
    """Deterministic record_id (32-hex) matching the <kind>_<32hex> pattern."""
    return canonical.record_id(prefix, obj)


def make_source(*, source_type: str, locator: dict, content: str,
                tier: str = "SECONDARY_DERIVED",
                explicitness: str = "EXPLICIT",
                claim_ceiling: str = "SECONDARY",
                rights_boundary: dict | None = None,
                alternatives: list | None = None,
                domain: str = "demo",
                extra: dict | None = None) -> dict:
    rb = rights_boundary or {"classification": "public", "republication": "allowed"}
    src = {
        "record_kind": "Source",
        "schema_version": "arr-r1.0",
        "scope": {"domain": domain, "context_ref": None},
        "provenance": ["fixture"],
        "explicitness": explicitness,
        "claim_ceiling": claim_ceiling,
        "uncertainty": "none stated",
        "alternatives": alternatives if alternatives is not None else [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None,
                      "transition_ref": None},
        "time": {
            "publication_time": None, "publication_time_status": "ABSENT",
            "ingestion_time": T, "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_type": source_type,
        "content_hash": canonical.sha256_hex(content),
        "locator": locator,
        "tier": tier,
        "rights_boundary": rb,
    }
    if extra:
        src.update(extra)
    src["record_id"] = _rid("src", src)
    return src


def make_observation(*, source_id: str, raw_excerpt: dict,
                     observer: str = "fixture-collector",
                     collection_metadata: dict | None = None,
                     claim_ceiling: str = "SECONDARY",
                     explicitness: str = "EXPLICIT",
                     alternatives: list | None = None,
                     domain: str = "demo") -> dict:
    obs = {
        "record_kind": "Observation",
        "schema_version": "arr-r1.0",
        "scope": {"domain": domain, "context_ref": None},
        "provenance": ["fixture"],
        "explicitness": explicitness,
        "claim_ceiling": claim_ceiling,
        "uncertainty": "none stated",
        "alternatives": alternatives if alternatives is not None else [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None,
                      "transition_ref": None},
        "time": {
            "observation_time": T, "observation_time_status": "OK",
            "ingestion_time": T, "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_ref": source_id,
        "observer": observer,
        "raw_excerpt": raw_excerpt,
        "collection_metadata": collection_metadata or {
            "method": "manual", "tool_ref": "fixture", "parameters": {}},
    }
    obs["record_id"] = _rid("obs", obs)
    return obs


def make_assertion_reconstruction(*, subject_ref: str,
                                  observation_ref: str,
                                  alternatives: list,
                                  reconstruction_basis: dict,
                                  proposition: str,
                                  uncertainty: str = "reconstructed by interpreter; not asserted by speaker") -> dict:
    a = {
        "record_kind": "Assertion",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "demo", "context_ref": None},
        "provenance": ["interpreter-reconstruction"],
        "explicitness": "INTERPRETER_RECONSTRUCTION",
        "claim_ceiling": "SECONDARY",
        "uncertainty": uncertainty,
        "alternatives": alternatives,
        "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                      "transition_ref": None},
        "time": {"ingestion_time": T, "ingestion_time_status": "OK"},
        "extensions": {},
        "subject_refs": [subject_ref],
        "assertion_type": "interpreted_claim",
        "proposition": proposition,
        "speaker_commitment": "attributed_by_interpreter",
        "reconstruction_basis": reconstruction_basis,
    }
    a["record_id"] = _rid("ast", a)
    return a


def base_relation(**overrides) -> dict:
    """A schema-valid Relation template; attacks override relation_type /
    extensions / claim_ceiling / temporal_scope / causal_handoff_ref."""
    r = {
        "record_id": "rel_" + canonical.sha256_hex("attack-base")[:32],
        "record_kind": "Relation",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "demo", "context_ref": None},
        "provenance": ["attack"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": "SECONDARY",
        "uncertainty": "no conclusion drawn",
        "alternatives": [],
        "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                      "transition_ref": None},
        "time": {"ingestion_time": T, "ingestion_time_status": "OK"},
        "extensions": {},
        "relation_type": "references",
        "endpoints": [{"role": "subject", "ref": "obj_x"},
                      {"role": "object", "ref": "src_y"}],
        "directionality": "directed",
        "temporal_scope": None,
        "causal_handoff_ref": None,
    }
    r.update(overrides)
    return r


def full_temporal_scope(start: str, end: str) -> dict:
    return {
        "interval": {"start": start, "start_inclusive": True,
                     "end": end, "end_inclusive": True},
        "activation_ref": None,
    }
