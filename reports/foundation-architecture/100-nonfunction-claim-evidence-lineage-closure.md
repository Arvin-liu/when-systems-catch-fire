# Task 100 — corpus-wide non-function claim adjudication and evidence-lineage closure

## Verdict boundary

The task-100 registry gives each reproducibly discovered non-function claim candidate one canonical record, source lineage, thirteen audit results, independent M/E maturity, dependency resolution, evidence status, disposition and public wording ceiling. Closure is accounting closure by disposition or explicit quarantine. It is not a finding that the Ignition corpus is true, proved, novel, peer reviewed or externally replicated.

## Locked base and inherited authority

- Formal base: task-99 merge commit `ebe723fbf544f3fa1a87706e82493319d9f0af7e`.
- Task 98–99 function identity cards remain authoritative where a non-function claim depends on a function asset.
- Historical function and case tables remain byte-preserved sources, not current claim authority.
- The withdrawn conclusion “physics grand unification has been proved impossible” remains withdrawn and cannot return through a renamed structural or meta form.

## Discovery and canonicalization

`tools/foundation/adjudicate_nonfunction_claims.py` accounts for every tracked or unignored repository path. It explicitly imports existing canonical claims, extracts multilingual claim-like text from documents and structured fields, excludes generated task-100 and already-closed task-99 machine registries with recorded reasons, normalizes exact duplicates and assigns hash-stable `NFC-*` IDs. The generated coverage file records both candidates and no-candidate paths, so ambiguous discoveries cannot disappear silently.

The complete current counts and distributions are generated in `data/foundation/nonfunction-claims/closure-summary.json`; the human index is a bounded view, not a replacement for the machine registry.

## Adjudication and evidence lineage

Every record contains:

- atomic text, class, assertion type, internal/external boundary, scope and quantifier status;
- assumptions, definitions, proof/empirical/literature/prediction obligations and counterexample duties;
- function/claim dependencies, downstream references and explicit unresolved edges;
- independent mathematical and external-evidence maturity plus replication status;
- one disposition, one ceiling, prohibited wording and supersession lineage;
- thirteen audit gates and exact source anchors.

Automated adjudication never assigns high external-evidence maturity or external replication. Existing source anchors establish provenance only. T2 inherits its task-99 carrier-scoped mathematical status and E0; corrected physics assets inherit their more restrictive task-98/99 ceilings.

## Inference barriers

The validators enforce four central regressions:

1. local or single-model failure is not universal impossibility;
2. analogy, homomorphism and isomorphism are not interchangeable;
3. internal tests, simulation and formal presentation are not external evidence;
4. withdrawn conclusions are blocked under physical, structural, meta, deep, higher-order and framework renaming.

The current Ignition gate model does not unify the four interactions. Grand unification remains an open physical research problem; neither universal possibility nor universal impossibility follows from this repository.

## Public and future admission closure

The generated public-surface report maps relevant front-door fragments to claim ceilings and must contain zero current violations. Future claims must enter through `docs/foundation/future-claim-admission-protocol.md` and the canonical schema before being presented as current knowledge. Historical wording is retained through supersession lineage rather than deletion.

## Reproducibility

Run:

```bash
python3 tools/foundation/adjudicate_nonfunction_claims.py --check
python3 tools/foundation/validate_nonfunction_claim_closure.py
python3 -m unittest tests.foundation.test_nonfunction_claim_closure -v
python3 tools/foundation/validate_foundation.py
```

These commands validate repository artifacts and deterministic generation only. External factual, causal and scientific claims retain their separately recorded evidence obligations.
