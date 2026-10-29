"""R4 schema definitions: typed containers for ingested evidence, derived
four-axis records, metric-contradiction records, limitation records and
architecture-candidate records. All containers are serializable to JSON so the
deterministic report projector can emit them without special-casing.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class AxisStatus:
    axis: str
    status: str
    rule_id: str
    evidence_refs: List[str]
    confidence: str = "unknown"  # "high" | "medium" | "low" | "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class FourAxisRecord:
    object_key: str  # opaque id only; never carries title/text
    pipeline: AxisStatus
    semantic: AxisStatus
    evidence: AxisStatus
    governance: AxisStatus

    def axes(self):
        return (self.pipeline, self.semantic, self.evidence, self.governance)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_key": self.object_key,
            "pipeline": self.pipeline.to_dict(),
            "semantic": self.semantic.to_dict(),
            "evidence": self.evidence.to_dict(),
            "governance": self.governance.to_dict(),
        }


@dataclasses.dataclass
class MetricContradiction:
    contradiction_id: str
    statement: str
    observed_values: Dict[str, Any]
    disposition: str
    evidence_refs: List[str]
    reconciled: str
    lifecycle: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class LimitationRecord:
    limitation_id: str
    primary_class: str
    secondary_factors: List[str]
    exclusion: Dict[str, str]  # adjacent class -> why it does not fit
    evidence_refs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ArchitectureCandidate:
    candidate_id: str
    observation: str
    conditions: Dict[str, bool]
    disposition: str  # "ARCHITECTURE_CANDIDATE" | "NO_EVOLVE"
    failed_conditions: List[str]
    evidence_refs: List[str]
    r5_request: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class SealedInputManifest:
    receipts_total: int
    envelopes_total: int
    receipt_digests: Dict[str, str]
    envelope_digests: Dict[str, str]
    report_digests: Dict[str, str]
    closed_set_ok: bool
    identity_audit: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipts_total": self.receipts_total,
            "envelopes_total": self.envelopes_total,
            "closed_set_ok": self.closed_set_ok,
            "identity_audit": self.identity_audit,
            # Digests are large; the full map lives in INPUT_EVIDENCE_MANIFEST.json
            "receipt_digest_count": len(self.receipt_digests),
            "envelope_digest_count": len(self.envelope_digests),
            "report_digest_count": len(self.report_digests),
        }
