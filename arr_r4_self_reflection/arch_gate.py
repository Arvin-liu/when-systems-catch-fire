"""Architecture-candidate gate (R4 task §7).

Default disposition is NO_EVOLVE. A limitation may be labeled ARCHITECTURE_CANDIDATE
only when ALL eight conditions hold. The gate is deliberately pure and
side-effect free so it can be mutation-tested: removing or falsifying any single
condition must flip a would-be candidate back to NO_EVOLVE.

R4 produces zero candidates (every observed weakness is explained by a lower-level
class), so the gate is exercised here as a verified guard rather than as a
promotion engine. R4 must not implement any candidate.
"""

from __future__ import annotations

from typing import Dict

from .schemas import ArchitectureCandidate
from .taxonomy import ARCH_CANDIDATE_DISPOSITION, ARCH_GATE_CONDITIONS, DEFAULT_ARCH_DISPOSITION


def decide(conditions: Dict[str, bool]) -> tuple[str, list[str]]:
    """Return (disposition, failed_conditions). Pure function; mutation-test target."""
    failed = [c for c in ARCH_GATE_CONDITIONS if not conditions.get(c, False)]
    if not failed:
        return ARCH_CANDIDATE_DISPOSITION, []
    return DEFAULT_ARCH_DISPOSITION, failed


class ArchitectureCandidateGate:
    def evaluate(self, candidate: ArchitectureCandidate) -> ArchitectureCandidate:
        disposition, failed = decide(candidate.conditions)
        candidate.disposition = disposition
        candidate.failed_conditions = failed
        return candidate

    def would_be_candidate(self, conditions: Dict[str, bool]) -> bool:
        return decide(conditions)[0] == ARCH_CANDIDATE_DISPOSITION
