"""Deterministic fixture provider for materials M1-M4 (7 active candidates /
8 UNKNOWNs / 5 engineering signals) and M5 (SECONDARY source, temporal
calibration, NORMALIZED_TRANSCRIPT_COPY verdict).

The records are curated so the RUN pipeline yields EXACTLY the required counts
for M1-M4. M5 is held to a SECONDARY tier and never changes the production
architecture; it adds only candidate/UNKNOWN/engineering-signal records.
"""

from __future__ import annotations

from .base import MaterialProvider, MaterialRecord

FIXTURE_PROVIDER_ID = "fixture://deterministic"

# Curated counts for M1-M4: 2/2/1 + 2/2/1 + 2/2/1 + 1/2/2 = 7 candidates / 8 unknowns / 5 signals.
_FIXTURE: dict[str, dict] = {
    "M1": {
        "tier": "PRIMARY_REPORT",
        "text": "M1 deterministic primary report: stable candidate set alpha and beta.",
        "candidates": [
            {"claim_text": "M1 alpha: system catches fire on thermal runaway", "inference_claims": [], "source_claims": ["thermal runaway"]},
            {"claim_text": "M1 beta: recovery requires external attestation", "inference_claims": [], "source_claims": ["external attestation"]},
        ],
        "unknowns": [
            {"question": "What is the exact thermal threshold for M1 trigger?", "scope": "M1 threshold"},
            {"question": "Does M1 generalize across hardware vendors?", "scope": "M1 generalization"},
        ],
        "signals": [
            {"description": "M1 needs a vendor-agnostic threshold signal"},
        ],
    },
    "M2": {
        "tier": "PRIMARY_REPORT",
        "text": "M2 deterministic primary report: candidates gamma and delta.",
        "candidates": [
            {"claim_text": "M2 gamma: incremental execution reduces rework", "inference_claims": [], "source_claims": ["incremental execution"]},
            {"claim_text": "M2 delta: selective materialization bounds cost", "inference_claims": [], "source_claims": ["selective materialization"]},
        ],
        "unknowns": [
            {"question": "What is the cost bound for M2 at scale?", "scope": "M2 cost"},
            {"question": "Is M2 reversible without side effects?", "scope": "M2 reversibility"},
        ],
        "signals": [
            {"description": "M2 needs a cost-bound monitoring signal"},
        ],
    },
    "M3": {
        "tier": "PRIMARY_REPORT",
        "text": "M3 deterministic primary report: candidates epsilon and zeta.",
        "candidates": [
            {"claim_text": "M3 epsilon: closed manifest proves closure", "inference_claims": [], "source_claims": ["closed manifest"]},
            {"claim_text": "M3 zeta: strict pointer fails closed on damage", "inference_claims": [], "source_claims": ["strict pointer"]},
        ],
        "unknowns": [
            {"question": "Can M3 closure be proven under concurrency?", "scope": "M3 concurrency"},
            {"question": "Does M3 hold across filesystem types?", "scope": "M3 fs portability"},
        ],
        "signals": [
            {"description": "M3 needs a concurrency-proof signal"},
        ],
    },
    "M4": {
        "tier": "SECONDARY_ACADEMIC_INTERPRETATION",
        "text": "M4 secondary academic interpretation: candidate eta plus two signals.",
        "candidates": [
            {"claim_text": "M4 eta: semantic ids stabilize across reorder", "inference_claims": [], "source_claims": ["semantic id stability"]},
        ],
        "unknowns": [
            {"question": "Does M4 eta hold under provider reorder?", "scope": "M4 reorder"},
            {"question": "Is M4 interpretation reproducible by a second reader?", "scope": "M4 reproducibility"},
        ],
        "signals": [
            {"description": "M4 needs a reorder-stability signal"},
            {"description": "M4 needs a reproducibility signal"},
        ],
    },
    "M5": {
        "tier": "SECONDARY_ACADEMIC_INTERPRETATION",
        "text": "M5 QC-MHM temporal KGQA reprint (normalized transcript copy; NOT byte-identical).",
        "extra": {
            "verdict": "NORMALIZED_TRANSCRIPT_COPY",
            "normalized_transcript_copy": True,
            "temporal_calibration": {
                "R_TQ_01": True,
                "R_TQ_02": True,
                "R_TQ_03": True,
                "R_TQ_04": True,
                "R_TQ_05": True,
                "R_TQ_06": True,
            },
        },
        "candidates": [
            {"claim_text": "M5 temporal query calibrates time windows before answering", "inference_claims": [], "source_claims": ["temporal calibration"]},
        ],
        "unknowns": [
            {"question": "Are M5 embedded images/formulas independently verifiable?", "scope": "M5 unverifiable media"},
        ],
        "signals": [
            {"description": "M5 needs a temporal-window fail-closed signal"},
        ],
        # A SOTA/originality claim that must be downgraded to UNKNOWN (not primary-verified).
        "sota_seed": {
            "claim_text": "M5 achieves SOTA on CronQuestions with a root cure for time-blindness",
            "inference_claims": ["root cure for time-blindness"],
            "source_claims": [],
        },
    },
}


class FixtureProvider(MaterialProvider):
    def __init__(self, refs: list[str] | None = None):
        self._refs = refs

    def provider_identity(self) -> str:
        return FIXTURE_PROVIDER_ID

    def list_materials(self, refs: list[str] | None = None) -> list[MaterialRecord]:
        wanted = refs or self._refs or list(_FIXTURE.keys())
        return [self.read_material(m) for m in wanted if m in _FIXTURE]

    def read_material(self, material_id: str) -> MaterialRecord:
        spec = _FIXTURE[material_id]
        seeds_c = [dict(s) for s in spec.get("candidates", [])]
        extra_seeds = []
        if "sota_seed" in spec:
            extra_seeds.append(dict(spec["sota_seed"]))
        return MaterialRecord(
            material_id=material_id,
            source_bytes=spec["text"].encode("utf-8"),
            source_tier=spec["tier"],
            provider_id=FIXTURE_PROVIDER_ID,
            provider_mode="DETERMINISTIC_FIXTURE",
            candidate_seeds=seeds_c + extra_seeds,
            unknown_seeds=[dict(u) for u in spec.get("unknowns", [])],
            signal_seeds=[dict(s) for s in spec.get("signals", [])],
            extra=dict(spec.get("extra", {})),
        )
