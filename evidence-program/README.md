# Evidence Program (Task 103 §9)

A minimal, reusable evidence layer for Pointfire falsifiable validation pilots. Built
only to the size required by the first real pilot — no unused platform.

## Layout

```
evidence-program/
  schemas/                       # 7 JSON schemas (every field exercised by the live pilot or a fixture)
  registry/
    candidate-portfolio.jsonl   # Phase A: ranked candidate portfolio (machine)
    candidate-portfolio.md      # Phase A: human-readable ranking + deferral reasoning
  preregistration/              # Phase B: immutable preregistration (machine + human), committed BEFORE results
  runs/<pilot-id>/
    run-manifest.json           # Phase D: how the run was executed
    source-manifest.jsonl       # Phase C: per-source provenance (one record per DOI)
    result-adjudication.json    # Phase E: outcome + E-axis decision
    deviation-log.json          # explicit, timestamped deviations only
  tools/
    validate_evidence_program.py  # deterministic validator (stdlib-only): schema + ordering + post-hoc + provenance + leakage
    run_crossref_verification.py  # primary pilot runner (real Crossref queries)
  tests/test_evidence_program.py  # regression fixtures exercising every schema + integrity check
```

## Pilot portfolio state

The first pilot (Crossref DOI verification, task 103) is `SUPPORTED_WITHIN_SCOPE` and
closed. The next pilot — **Function OS v0.2 correctness (candidate C-4)** — was
executed by task 105: preregistered, then adversarially validated on a curated
baseline. Original-target verdict `PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES`
(25 false_reject from an N2 nested-equality defect); repaired-target verdict
`SUPPORTED_WITHIN_BOUNDED_DOMAIN`. It is recorded as a completed bounded pilot;
the evidence ceiling is bounded-domain only — no claim of complete sandboxing,
production readiness, or universal correctness. Remaining narrower questions
(broader expression coverage, hostile-environment security, production
reliability, real-world utility) are tracked as OQ-103-6 in `RESULTS/OPEN-QUESTIONS.md`.

## Reproduce the first pilot

```bash
# 1) Preregistration is already committed (see run-manifest.preregistration_commit).
# 2) Run the external verification:
python evidence-program/tools/run_crossref_verification.py \
    --registry data/external-research/104-source-registry.jsonl \
    --out evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/source-manifest.jsonl

# 3) Validate the whole program (schema + preregistration-before-result + post-hoc + provenance + leakage):
python evidence-program/tools/validate_evidence_program.py --root evidence-program
```

## Invariants enforced

1. **Preregistration before result** — `run-manifest.preregistration_commit` must be an
   ancestor of the commit containing the run, and its timestamp must precede result generation.
2. **No post-hoc substitution** — `result-adjudication.thresholds_used` must be byte-identical
   to the preregistration's success/partial/null/contradiction/invalid conditions.
3. **Source provenance completeness** — every `OK` source record must carry
   `response_sha256`, `licence`, `retrieval_timestamp_utc`, `canonical_identifier`.
4. **No leakage** — observed metrics must be a subset of preregistered metrics.
5. **Failures are explicit** — non-`OK` acquisitions record a status, never silently dropped.

## Task 110 independent replication

Task 110 keeps the original candidate portfolio immutable and adds a state overlay
at `registry/task-110-portfolio-state.json`. The completed C-01 Crossref obligation
and completed C-04 bounded benchmark are historical and excluded from active
scheduling; C-03 is now a completed partial OpenAlex pilot. The pilot's full 117-row
source manifest, raw-response hashes, adjudication and bounded result are under
`runs/IGNITION-EVIDENCE-PILOT-R1-OPENALEX-DOI-REPLICATION-20260801/`.

The result is metadata-only: 101 supported, 8 partial, 7 null/inconclusive and no
contradictions in the 116-record primary denominator. It does not validate paper
content, scientific truth, Pointfire physics, MCF, PSD, ARN or maturity/disposition.
