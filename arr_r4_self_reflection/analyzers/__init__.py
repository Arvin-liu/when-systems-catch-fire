"""R4 analyzers package (R4 task §8).

Each analyzer consumes the sealed R3 reports (and the four-axis summary where
relevant) and emits a deterministic, machine-readable result. None hard-codes
the 836 count; counts are derived from the ingested data.
"""

from .source_dependency import analyze_source_dependency
from .false_consensus import analyze_false_consensus
from .temporal import analyze_temporal
from .evidence_ceiling import analyze_evidence_ceiling
from .limitation_attribution import analyze_limitation_attribution

__all__ = [
    "analyze_source_dependency",
    "analyze_false_consensus",
    "analyze_temporal",
    "analyze_evidence_ceiling",
    "analyze_limitation_attribution",
]
