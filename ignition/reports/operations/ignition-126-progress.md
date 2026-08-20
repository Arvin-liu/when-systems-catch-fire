# IGNITION-20260818-126 — Epistemic Structural Induction R0 progress

This task-branch ledger records repository evidence only. `origin/main` stays
unchanged until the final ordinary fast-forward gate. Task 125 is not executed
by this run and remains `DEFERRED_PENDING_REBASE`.

## Step ledger

| Step | Status | Commit | Remote | Summary |
| --- | --- | --- | --- | --- |
| 00 | COMPLETED | pending closure | pending closure | Fresh formal baseline, canonical governance inventory, and explicit Task 125 deferral. |
| 01 | COMPLETED | pending closure | pending closure | Bounded ESI candidate definition, alternative explanations, claim ceiling and falsification/downgrade criteria. |
| 02 | COMPLETED | pending closure | pending closure | Machine-enforced soft-governance non-authority contract and fail-closed negative fixtures. |
| 03 | COMPLETED | pending closure | pending closure | Source-bound epistemic transition grammar with 12 rules, negative transitions and provenance validator. |
| 04 | COMPLETED | pending closure | pending closure | Deterministic original Structural Governance Surface generated from grammar, contract and Current identity. |
| 05 | COMPLETED | pending closure | pending closure | Five deterministic exposure/control projections with recorded relation, terminology, style and length properties. |

## Boundary

ESI is a candidate inference-time/contextual phenomenon, not a weight update,
hard safety boundary, truth layer, new law, or novelty claim. Soft structural
governance cannot grant permission, authorization, truth, M/E, Owner acceptance,
epistemic acceptance, external side-effect authorization, or safety release.
`CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain separate.

## Step 00 evidence

- Formal baseline: `42dfc19cb17d439c9e150caf2dd5e75e3db938bd`.
- Control source: `origin/relay/current` at `1aa40da9622b3d603bd008014ecf6828bf1f4202`.
- Machine audit: `data/operations/iterations/126/step00-baseline-audit.json`.
- Task 125: `DEFERRED_PENDING_REBASE`; it was not executed and its full
  Durability/Lifecycle deliverables are not included in this branch.
- Baseline gates passed; the next step is to define the candidate phenomenon
  and its alternative explanations without upgrading the claim.

## Handoff required after Step 17

`TASK125_DURABILITY_LIFECYCLE = DEFERRED_PENDING_REBASE`. After this task's
final formal main is known, the next Durability/Lifecycle task must be
re-audited and rewritten from that exact main, including any Structural
Governance Surface state and the non-authority invariant.

## Step 01 evidence

- Candidate record: `data/epistemic-governance/esi-candidate-boundary-r0.json`.
- Human boundary: `docs/architecture/epistemic-structural-induction-r0.md`.
- Validator: `tools/validate_esi_candidate.py` and `tests/test_esi_candidate.py` (`2/2`).
- Status remains `CANDIDATE_ESI_SIGNAL`; live-model evidence is not inferred.
- Alternative explanations include in-context learning, task inference,
  structural priming, style/terminology imitation, default alignment and
  contextual mimicry.

## Step 02 evidence

- Contract: `data/epistemic-governance/soft-governance-non-authority-invariant-r0.json`.
- Human explanation: `data/epistemic-governance/soft-governance-contract.md`.
- Validator: `tools/validate_soft_governance_authority.py` (`PASS`).
- Negative authority fixtures: `3/3` fail closed for authorization, truth
  status and Owner acceptance attempts.
- Unit tests: `tests/test_soft_governance_authority.py` (`4/4`).
- Runtime source scan found no coupling between a soft input and a hard
  authority effect.

## Step 03 evidence

- Registry: `data/epistemic-governance/transition-grammar-r0.json` (`12` rules,
  `24` source references).
- Schema: `schemas/epistemic-governance/transition-grammar-r0.schema.json`.
- Validator: `tools/validate_transition_grammar.py` (`PASS`, complete
  provenance coverage).
- Unit tests: `tests/test_transition_grammar.py` (`3/3`).
- Rules cover engineering, publication, knowledge, agent, owner and
  cross-cutting boundaries, including unknown retention and withdrawal/rebound.

## Step 04 evidence

- Generator: `tools/generate_structural_governance_surface.py`.
- Machine projection: `data/epistemic-governance/structural-surface-r0.json`.
- Human/machine reading surface: `docs/architecture/structural-governance-surface.md`.
- Projection contains `12/12` grammar relations and labels itself
  `ADVISORY_READING_SURFACE_NOT_PROMPT`.
- Deterministic generator check passed; unit tests `3/3` passed.

## Step 05 evidence

- Generator: `tools/generate_structural_projections.py`.
- Projection arms: `5/5` — delexicalized structure, terminology-only,
  structure-broken, style-matched control and concise capsule.
- Each arm has `12` matched item identities and records whether relations,
  terminology and style were preserved plus serialized content length.
- Deterministic projection check passed; unit tests `4/4` passed.
- The terminology-only arm contains vocabulary without transition relations;
  the delexicalized arm retains relations without named governance terms.
