# Minimal experiment candidates (proposal only)

These five items are research designs, not implementation requests. They are marked `RESEARCH_ONLY_NOT_IMPLEMENTED`; none has been run, and no model weights, external systems, held-out payloads, or successor/evaluator outputs were used in Task186.

## Candidate ordering by dependency

1. **Capability-profile freshness:** a low-cost offline metadata check for stale version bindings and permission non-expansion. It tests a prerequisite for responsible capability claims, not capability calibration.
2. **Evaluator write-surface isolation:** a disposable contract test for whether a candidate can alter evaluator code, held-out manifests, thresholds, or promotion state. This protects later experiments but does not validate the evaluator's scientific quality.
3. **Memory retirement with rollback:** a fixed synthetic corpus and query set can test utility loss, false retirement, provenance, and exact restoration. Human review may be needed for semantic duplicate labels.
4. **Skill versus method:** a small deterministic simulator compares no artifact, a reusable skill, and a method for producing/checking skills. The task oracle must prevent answer leakage.
5. **Cross-model method transfer:** the highest-cost proposal compares base, facts-only, skill-only, and method-artifact conditions across versioned models. A separate custodian must keep the test set and evaluator outside candidate write/read surfaces; no weight training is part of this proposal.

## Shared safeguards

Before any one of these is implemented, its owner should freeze the exact task family, base/successor versions, development and protected-test partition, evaluator source, outcome measure, stop conditions, rollback path, and claim ceiling. A result on a synthetic task family would remain synthetic-task evidence. No test should be promoted to a general intelligence, external truth, or cognitive-inheritance claim without separate admission and replication.

Each candidate record includes the question, external mechanism, Pointfire baseline, exact gap, reversible test, evaluator/holdout design, stop condition, failure criterion, non-proving result, and engineering cost class in `minimal-experiment-candidates.jsonl`.
