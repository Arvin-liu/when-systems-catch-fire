"""arr_r4_self_reflection — deterministic R4 self-reflection and failure-attribution engine.

Public surface:
  - SealedEvidenceIngestor: closed-set validation + digests of sealed R3 evidence.
  - FourAxisDeriver: per-object four-axis status derivation (no pipeline->semantic leak).
  - MetricContradictionEngine: recomputes the 6 mandatory contradictions, assigns dispositions.
  - analyzers.*: source-dependency, false-consensus, temporal, evidence-ceiling, limitation.
  - ArchitectureCandidateGate: 8-condition gate, default NO_EVOLVE, mutation-tested.
  - report.project_public_summary: non-private projection.
  - runner.run: orchestrates the full audit and writes the 20 private evidence files.

The package accepts generic evidence directories and synthetic fixtures; it never
hard-codes the 836 note ids, private titles, or R3 result values as passing conditions.
"""

from .arch_gate import ArchitectureCandidateGate
from .four_axis import FourAxisDeriver
from .ingest import SealedEvidenceIngestor
from .metric_consistency import MetricContradictionEngine
from .report import project_public_summary
from .runner import run

__all__ = [
    "ArchitectureCandidateGate",
    "FourAxisDeriver",
    "SealedEvidenceIngestor",
    "MetricContradictionEngine",
    "project_public_summary",
    "run",
]
