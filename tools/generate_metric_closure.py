"""Deterministic generator for the R3/R4 metric observability closure artifacts.

Produces the non-reconstructive public correction artifacts under
``docs/architecture/arr-r3-r4-metric-closure/`` from the versioned correction
layer in ``arr_metric_correction``. Running it twice yields byte-identical
output (deterministic). It never reads or emits private corpus content.

NOTE: this generator lives at the top level of ``tools/`` (NOT under
``tools/adaptive_relational_runtime``) because it legitimately imports from the
top-level ``arr_metric_correction`` package and ``r4_fixtures`` and writes
files; the ARR anti-second-executor static gate only scans
``tools/adaptive_relational_runtime``.
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
TESTS_DIR = os.path.join(REPO_ROOT, "tests", "adaptive_relational_runtime")
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

from arr_metric_correction import (  # noqa: E402
    SCHEMA_VERSION,
    CORPUS_OBJECTS,
    FROZEN_CORPUS_REF,
    SEALED_R3_INPUTS,
    build_sealed_manifest,
    project_all,
)
from r4_fixtures import r4_capability_matrix  # noqa: E402

OUT_DIR = os.path.join(REPO_ROOT, "docs", "architecture", "arr-r3-r4-metric-closure")

CORRECTIONS_VALIDATED = {"M2": True, "M3": True, "M4": True, "M5": True}


def _write(name: str, obj: dict) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote", os.path.relpath(path, REPO_ROOT))


def main() -> None:
    projection = project_all(
        SEALED_R3_INPUTS,
        r4_capability_matrix(),
        corrections_validated=CORRECTIONS_VALIDATED,
    )
    corrections = projection["corrections"]

    meta = {
        "task_id": "ARR-R3-R4-METRIC-SEMANTICS-OBSERVABILITY-CLOSURE-R1-RELAY-20260725",
        "control_commit": "afb3089a54798bd5d4dcdb10c796a36f219ef724",
        "formal_predecessor": "27af5f99e13d8217961cbc803520c648ce791c68",
        "frozen_corpus_ref": FROZEN_CORPUS_REF,
        "corpus_objects": CORPUS_OBJECTS,
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tools/generate_metric_closure.py",
        "validation_ok": projection["validation_ok"],
        "validation_failures": projection["validation_failures"],
    }

    # M2 / M3 / M4 / M5 / R4-split / lifecycle closures (non-reconstructive).
    _write("CRASH_RECOVERY_METRIC_CLOSURE.json",
           {"meta": meta, "schema": "r3r4/crash-recovery-closure/v1",
            "metrics": corrections["M3_CRASH_RECOVERY"]})
    _write("INCREMENTAL_RERUN_METRIC_CLOSURE.json",
           {"meta": meta, "schema": "r3r4/incremental-rerun-closure/v1",
            "metrics": corrections["M4_INCREMENTAL_RERUN"]})
    _write("UNKNOWN_RETENTION_METRIC_CLOSURE.json",
           {"meta": meta, "schema": "r3r4/unknown-retention-closure/v1",
            "metrics": corrections["M2_UNKNOWN_RETENTION"]})
    _write("CAPABILITY_CLOSED_SET_V2.json",
           {"meta": meta, "schema": "r3r4/capability_interpretation_correction/v1",
            "interpretation": corrections["M5_CAPABILITY"]})
    _write("SEMANTIC_GUARDRAIL_UNDERSTANDING_SPLIT.json",
           {"meta": meta, "schema": "r3r4/semantic-guardrail-understanding-split/v1",
            "split": corrections["R4_SEMANTIC_SPLIT"]})
    _write("CONTRADICTION_LIFECYCLE_CLOSURE.json",
           {"meta": meta, "schema": "r3r4/contradiction_lifecycle/v1",
            "lifecycle": corrections["CONTRADICTION_LIFECYCLE"]})

    # Registry (schema + enumerated metric ids) and full ledger.
    metric_ids = []
    for group in ("M2_UNKNOWN_RETENTION", "M3_CRASH_RECOVERY", "M4_INCREMENTAL_RERUN"):
        metric_ids.extend(sorted(corrections[group].keys()))
    _write("METRIC_DEFINITION_REGISTRY.json",
           {"meta": meta, "schema_version": SCHEMA_VERSION,
            "metric_ids": metric_ids,
            "fail_closed_rules": [
                "rate/fraction requires numerator(value+source), denominator(source), population, applicability",
                "applicability must be resolved (not UNKNOWN) for any rate/fraction",
                "denominator 0 => NOT_APPLICABLE, never a misleading numeric 0.0",
                "every metric references at least one evidence source",
            ]})
    _write("METRIC_CORRECTION_LEDGER.json",
           {"meta": meta, "schema": "r3r4/correction-projection/v1",
            "sealed_inputs": build_sealed_manifest(),
            "corrections": corrections})


if __name__ == "__main__":
    main()
