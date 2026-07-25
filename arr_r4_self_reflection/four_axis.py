"""Four-axis outcome derivation (R4 task §5).

For every sealed object the deriver emits exactly one status on each of the
four axes. The rules are deterministic and derived ONLY from fields already
present in the immutable R3 receipt/envelope. Critical invariants enforced
here (and re-checked by tests):

  * PIPELINE_COMPLETE never implies SEMANTIC_REPRESENTATION_SUFFICIENT.
  * INDEPENDENTLY_SUPPORTED is never assigned unless the sealed evidence truly
    contains independent verification (R3 has none -> count stays 0).
  * A repeated/source-dependent note is never upgraded to independent support.
  * An inference-labeled transcript is never upgraded to verified fact or
    speaker belief.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import AxisStatus, FourAxisRecord
from .taxonomy import (
    AUTHOR_OR_SPEAKER_REPORT,
    CONSENT_OR_RIGHTS_LIMITED,
    BOUNDARY_HELD,
    EVIDENCE_AXIS,
    GOVERNANCE_AXIS,
    PIPELINE_AXIS,
    SEMANTIC_AXIS,
    SOURCE_DEPENDENT,
    TRANSCRIPT_OR_INTERPRETER_INFERENCE,
)


def _status(axis: str, status: str, rule_id: str, refs: List[str], confidence: str = "unknown") -> AxisStatus:
    if axis == "pipeline" and status not in PIPELINE_AXIS:
        raise ValueError(f"bad pipeline status {status}")
    if axis == "semantic" and status not in SEMANTIC_AXIS:
        raise ValueError(f"bad semantic status {status}")
    if axis == "evidence" and status not in EVIDENCE_AXIS:
        raise ValueError(f"bad evidence status {status}")
    if axis == "governance" and status not in GOVERNANCE_AXIS:
        raise ValueError(f"bad governance status {status}")
    return AxisStatus(axis=axis, status=status, rule_id=rule_id, evidence_refs=refs, confidence=confidence)


class FourAxisDeriver:
    def derive(self, receipt: Dict[str, Any], envelope: Dict[str, Any]) -> FourAxisRecord:
        key = receipt.get("object_key") or envelope.get("object_key") or "unknown"
        pipeline = self._pipeline(receipt, key)
        semantic = self._semantic(receipt, envelope, key)
        evidence = self._evidence(receipt, key)
        governance = self._governance(receipt, key)
        return FourAxisRecord(
            object_key=key,
            pipeline=pipeline,
            semantic=semantic,
            evidence=evidence,
            governance=governance,
        )

    # -- A. pipeline -------------------------------------------------------

    def _pipeline(self, receipt: Dict[str, Any], key: str) -> AxisStatus:
        outcome = receipt.get("outcome")
        if outcome == "SUCCESS":
            return _status("pipeline", "PIPELINE_COMPLETE", "pipeline.outcome_success",
                           [f"receipt:{key}:outcome=SUCCESS"])
        # R3 produced only SUCCESS outcomes; the branches below are generic so
        # the tool is reusable on other corpora without re-coding.
        if outcome in ("PARTIAL", "PARTIALLY_PROCESSED"):
            return _status("pipeline", "PIPELINE_PARTIAL", "pipeline.outcome_partial",
                           [f"receipt:{key}:outcome={outcome}"])
        if outcome in ("FAILED", "ERROR"):
            return _status("pipeline", "PIPELINE_FAILED", "pipeline.outcome_failed",
                           [f"receipt:{key}:outcome={outcome}"])
        return _status("pipeline", "PIPELINE_QUARANTINED", "pipeline.outcome_quarantined",
                       [f"receipt:{key}:outcome={outcome}"])

    # -- B. semantic -------------------------------------------------------

    def _semantic(self, receipt: Dict[str, Any], envelope: Dict[str, Any], key: str) -> AxisStatus:
        # R3 performed extraction -> representation -> receipt. It never ran a
        # semantic-understanding / verification stage. The deriver therefore
        # never assigns SEMANTIC_REPRESENTATION_SUFFICIENT from pipeline success.
        claim_class = receipt.get("claim_class")
        inference_labeled = bool(envelope.get("inference_labeled", False))
        if inference_labeled or claim_class == "TRANSCRIPT_INFERENCE":
            # An interpretive inference was generated and labeled: this is a
            # representation of an interpretation, NOT verified understanding.
            return _status("semantic", "SEMANTIC_REPRESENTATION_LIMITED",
                           "semantic.transcript_inference_labeled",
                           [f"receipt:{key}:claim_class={claim_class}",
                            f"envelope:{key}:inference_labeled=true"],
                           confidence="low")
        # Extraction/representation only; no semantic-understanding step was
        # attempted or verified.
        return _status("semantic", "SEMANTIC_NOT_ATTEMPTED",
                       "semantic.no_understanding_stage",
                       [f"receipt:{key}:claim_class={claim_class}"],
                       confidence="unknown")

    # -- C. evidence -------------------------------------------------------

    def _evidence(self, receipt: Dict[str, Any], key: str) -> AxisStatus:
        # INDEPENDENTLY_SUPPORTED requires the sealed evidence to truly contain
        # independent verification. R3 has zero independently verified claim
        # classes and only an *estimate* of independent sources, so this branch
        # is intentionally unreachable for R3 and stays at 0 (test-guarded).
        if receipt.get("independent_verified") is True:
            return _status("evidence", "INDEPENDENTLY_SUPPORTED", "evidence.independent_verified",
                           [f"receipt:{key}:independent_verified=true"])
        claim_class = receipt.get("claim_class")
        if claim_class == "TRANSCRIPT_INFERENCE":
            return _status("evidence", TRANSCRIPT_OR_INTERPRETER_INFERENCE,
                           "evidence.transcript_inference",
                           [f"receipt:{key}:claim_class=TRANSCRIPT_INFERENCE"],
                           confidence="low")
        if claim_class == "AUTHOR_OBSERVATION":
            return _status("evidence", AUTHOR_OR_SPEAKER_REPORT,
                           "evidence.author_observation",
                           [f"receipt:{key}:claim_class=AUTHOR_OBSERVATION"])
        if claim_class == "SECONDARY_ARCHIVE_CLAIM":
            return _status("evidence", SOURCE_DEPENDENT,
                           "evidence.secondary_archive_claim",
                           [f"receipt:{key}:claim_class=SECONDARY_ARCHIVE_CLAIM"])
        return _status("evidence", "EVIDENCE_UNKNOWN", "evidence.unknown",
                       [f"receipt:{key}:claim_class={claim_class}"])

    # -- D. governance -----------------------------------------------------

    def _governance(self, receipt: Dict[str, Any], key: str) -> AxisStatus:
        if receipt.get("real_world_action") or receipt.get("promote_called") or receipt.get("evolve_called"):
            return _status("governance", "ACTION_PROHIBITED", "governance.prohibited_action",
                           [f"receipt:{key}:real_world_action={receipt.get('real_world_action')}",
                            f"receipt:{key}:promote_called={receipt.get('promote_called')}",
                            f"receipt:{key}:evolve_called={receipt.get('evolve_called')}"])
        source_ref_present = bool(receipt.get("source_ref_present"))
        rights_boundary = receipt.get("rights_boundary")
        if rights_boundary == "private" and not source_ref_present:
            # Safety boundary held (no action), but consent/rights cannot be
            # verified because provenance (source_ref) is absent.
            return _status("governance", CONSENT_OR_RIGHTS_LIMITED,
                           "governance.consent_unverifiable",
                           [f"receipt:{key}:rights_boundary=private",
                            f"receipt:{key}:source_ref_present=false",
                            "note: BOUNDARY_HELD also true (no prohibited action)"],
                           confidence="unknown")
        return _status("governance", BOUNDARY_HELD, "governance.boundary_held",
                       [f"receipt:{key}:rights_boundary={rights_boundary}",
                        f"receipt:{key}:source_ref_present={source_ref_present}"])
