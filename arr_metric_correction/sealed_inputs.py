"""Sealed historical R3 input identities for the correction layer.

These are the EXACT historical values recorded in the frozen R3 evidence
(``agent/adaptive-relational-runtime-r3-waic-corpus-scale-r1-20260725`` and the
sealed ``AGGREGATE_METRICS`` / run-ledger / crash / incremental / temporal
reports). The correction layer references them by report identity and value;
it never mutates them. Digests are computed over a canonical JSON
serialization so the immutability audit can re-verify them against the frozen
evidence without re-running the 836-note corpus.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


# Frozen corpus + object constants (public spec constants, not private content).
CORPUS_OBJECTS = 836
FROZEN_CORPUS_REF = "50393395ce9e6a1592787d991e630e364c5b6a09"

# Exact historical values. The aggregate column is the defective historical
# report; the run-ledger / demo-report columns are the authoritative sources
# the correction layer elevates.
SEALED_R3_INPUTS: Dict[str, Dict[str, Any]] = {
    "AGGREGATE_METRICS": {
        "crash_recovery_success_rate": 0.0,
        "incremental_selectivity": 0.0,
        "unknown_retention": 0,
        "corpus_notes_selected": 836,
    },
    "CORPUS_RUN_LEDGER": {
        "crash_recovery_success_rate": 1.0,
        "incremental_selectivity": 0.0011961722488038277,  # 1 / 836
    },
    "CRASH_RECOVERY_REPORT": {
        "all_resume_complete": True,
        "scenario_count": 3,
    },
    "INCREMENTAL_RERUN_REPORT": {
        "reprocessed_on_change": 1,
        "selective": True,
    },
    "TEMPORAL_AMBIGUITY_LEDGER": {
        "unknown_event_time_count": 449,
        "temporal_ambiguity_rate": 0.5371,
    },
    "CAPABILITY_COVERAGE_MATRIX": {
        "all_pass": True,
        "total_items": 27,
    },
}


def _canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sealed_input_digest(report_id: str) -> str:
    """SHA-256 of the canonical serialization of one sealed report identity."""
    return hashlib.sha256(_canonical_bytes(SEALED_R3_INPUTS[report_id])).hexdigest()


def build_sealed_manifest() -> Dict[str, Any]:
    """Deterministic manifest of all sealed input identities + digests."""
    digests = {rid: sealed_input_digest(rid) for rid in SEALED_R3_INPUTS}
    return {
        "schema": "r3r4/sealed-input-manifest/v1",
        "frozen_corpus_ref": FROZEN_CORPUS_REF,
        "corpus_objects": CORPUS_OBJECTS,
        "report_identities": sorted(SEALED_R3_INPUTS.keys()),
        "report_digests": digests,
        "mutable": False,
        "note": "Historical sealed inputs are referenced, never mutated, by the correction layer.",
    }


def input_identity_checks(sealed: Dict[str, Dict[str, Any]]) -> List[str]:
    """Fail-closed check that the supplied sealed inputs match the contract.

    Returns a list of violation strings (empty == identical to the contract).
    """
    failures: List[str] = []
    for rid, expected in SEALED_R3_INPUTS.items():
        got = sealed.get(rid)
        if got is None:
            failures.append(f"sealed input {rid} missing")
            continue
        if got != expected:
            failures.append(f"sealed input {rid} mutated: {got} != {expected}")
    for rid in sealed:
        if rid not in SEALED_R3_INPUTS:
            failures.append(f"unexpected sealed input {rid}")
    return failures
