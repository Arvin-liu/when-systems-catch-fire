# Future non-function claim admission protocol

This protocol is the mandatory entry path for a new theorem, law, principle, mechanism, causal judgment, impossibility result, cross-domain correspondence, prediction, empirical assertion, ontology claim, interpretation rule or public summary. It extends the task 98–99 function-asset governance; it does not replace function identity cards.

Admission means that a claim has a traceable record and a permitted wording. It does not mean that the claim is true, novel, peer reviewed or independently replicated.

## 1. Submit one atomic claim

One record must state one proposition. Split conjunctions whose parts can have different truth values. Supply:

- a stable candidate ID and title;
- exact source path and line or machine locator;
- minimal claim text;
- claim class and assertion type;
- internal, external or unresolved status;
- domain, model class, scope and quantifiers;
- definitions, assumptions and declared exclusions.

Automatic discovery can propose a record, but cannot assign authoritative truth, proof, evidence or novelty status.

## 2. Declare independent maturity axes

Record mathematical maturity `M0`–`M7` and external-evidence maturity `E0`–`E7` independently. A proof does not raise E. Experiments do not repair an ill-typed theorem. AI agreement, numbering, repository inclusion, deterministic generation and green CI raise neither axis.

For empirical claims, declare replication as `NO_REPLICATION_CLAIMED`, `INTERNAL_REPLAY_ONLY` or `EXTERNAL_REPLICATION_DOCUMENTED`. Never infer independent replication from repeated runs of the same data, code, author or model.

## 3. Resolve lineage and dependencies

Link every premise, source, evidence item, function identity card and downstream consumer. Each edge must resolve to a registered claim or function asset, or be marked `EXTERNAL_OR_UNRESOLVED`. Preserve historical wording with supersession links; do not delete or silently rewrite it.

Claims depending on task 98–99 function identities inherit their claim ceilings. They do not inherit external truth. In particular, D127 is a structural metaphor; D182/D184 are scoped toy models; D183 requires rewrite; D185–D187 are structural metaphors; D188 is invalid as a physical projection; D189–D190 are research candidates; D260 is an index without a calibrated real-world threshold. T2 is proved only for its declared algebraic carrier and assumptions.

## 4. Run all applicable gates

The record must explicitly contain these thirteen results:

1. definition;
2. quantifier;
3. proof and circularity;
4. counterexample;
5. type and dimension;
6. internal versus external;
7. model class;
8. cross-domain relation;
9. evidence;
10. novelty;
11. prediction;
12. conclusion rebound;
13. public surface.

Allowed gate values are `PASS`, `FAIL`, `REQUIRES_HUMAN_REVIEW` and `NOT_APPLICABLE`. Uncertain automation must return `REQUIRES_HUMAN_REVIEW`.

Special fail-closed rules:

- a local or single-model failure cannot establish universal impossibility;
- analogy, partial mapping, homomorphism and isomorphism are distinct;
- an isomorphism claim needs objects, a bijection and structure-preservation proof;
- a causal claim needs an explicit causal model, intervention semantics and identification evidence;
- a prediction needs preregistered parameters, data cutoff, evaluation rule, uncertainty and a disconfirming outcome;
- a literature claim needs primary-source adjudication for the exact proposition;
- a withdrawn conclusion cannot re-enter under “structural”, “meta”, “deep”, “higher-order” or framework-internal renaming.

## 5. Assign exactly one disposition and ceiling

Use one disposition from the canonical schema. A failed or unresolved gate must produce a pending, rewrite, quarantine, withdrawal, rejection or historical-only state appropriate to the failure. `ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT` requires a scoped proof and sufficient M maturity. `ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT` requires exact external evidence and documented replication appropriate to the claim.

Every record must include maximum permitted public wording and prohibited wording. Public pages may summarize the claim only within that ceiling.

## 6. Review, generate and propagate

Before merge:

```bash
python3 tools/foundation/adjudicate_nonfunction_claims.py
python3 tools/foundation/adjudicate_nonfunction_claims.py --check
python3 tools/foundation/validate_nonfunction_claim_closure.py
python3 -m unittest tests.foundation.test_nonfunction_claim_closure -v
python3 tools/foundation/validate_foundation.py
```

Review the exact remote commit. If the disposition or ceiling changes, propagate it through every dependency and all public surfaces. Preserve the old record in `supersession-lineage.jsonl`. A registry can be closed by explicit quarantine, but removing quarantine requires new evidence that discharges the recorded obligations and a reviewed regeneration of all derived artifacts.
