# Q37-I1 — Interface & Project Wiring

Minimal接入 surfaces (spec §七) for the analogy-audit & transportability gate. All cross-Q
references are **read-only copies** embedded in the Q37 bundle; Q37 never re-adjudicates an
upstream claim, grant, observation, intervention or right.

## Upstream contracts reused (read-only)

| Upstream | Contract / gate | Q37 field that consumes it | Check family |
|----------|-----------------|----------------------------|--------------|
| Q34 (discovery / commitment) | `schemas/discovery/commitment-claim.schema.json`, `tools/discovery/validate_commitment_gate.py` (`ANALOGY_AS_MECHANISM = 7`) | `analogy_candidates[].originating_q34_claim_ref` → `q34_claims[]` | `Q14_CLAIM_NOT_COMMITTED` (14) |
| Q35 (agent responsibility) | `schemas/agent/responsibility-contract.schema.json`, `tools/agent/validate_responsibility_gate.py` | `analogy_candidates[].q35_authority_ref` → `q35_grants[]` | `Q35_AUTHORITY_INVALID` (15) |
| Q36-OBS (observation/prediction) | `schemas/observation/observation-prediction-contract.schema.json` | `q36_obs_snapshots[]` (residuals feed candidate evidence) | `RESIDUAL_AS_CAUSE` (11) |
| Q36-INT (intervention failure) | `schemas/intervention/intervention-failure-dynamics-contract.schema.json` | `q36_int_snapshots[]` (mechanism hypotheses feed mechanism evidence) | `CLAIM_CEILING_OVERREACH` (18) defense |
| Q33 (source rights) | `schemas/governance/*` rights entries | `q33_rights[]` (every external evidence ref) | `Q33_RIGHTS_BYPASS` (16) |

## Suggested call order (spec §七)

```
Q34 committed_current claim permits analogy purpose
  → Q35 grant authorizes propose/audit
    → Q36-OBS residual / Q36-INT mechanism hypothesis supplied as candidate inputs
      → Q37 classifies, maps, audits counteranalogy & mechanism & transportability
        → only audited TRANSPORTABILITY_CANDIDATE may enter Q38 as restricted search seed
          → failed/negative mappings enter Q39 failure-memory interface
```

## Q37 → Q38 interface (`audited_search_seed`)

- `audit_decisions[].q38_search_permission == "ALLOWED_AS_RESTRICTED_SEED"` is the ONLY signal that
  lets a candidate become a Q38 retrieval seed. It means *may enter Q38 as a restricted retrieval
  seed* — it does NOT assert the analogy is true or the mechanism holds.
- `bundle.q38_case_retrieval_started` MUST remain `false` in Q37; setting it `true` fails closed
  (`Q38_START_FORBIDDEN`, 19). Q37 never performs Q38 case retrieval.

## Q37 → Q39 interface (failure memory)

- `COUNTERANALOGY` candidates and `audit_decisions[].counteranalogy_status == "PRESENT_PRESERVED"`
  are the negative / failure outputs. They MUST be preserved (not deleted / suppressed); deletion
  fails closed (`NEGATIVE_AUDIT_DELETED`, 20; `COUNTERANALOGY_SUPPRESSED`, 13). These feed Q39's
  failure-memory interface.

## Real-repo pilot (spec §六 item 24)

`data/analogy/fixtures/24-real-repo-pilot-q34-analogy-as-mechanism.json` audits the existing
`data/discovery/fixtures/05-analogy-as-mechanism.json` (Q34's `ANALOGY_AS_MECHANISM` attack
fixture). It is an honest **repository replay**, not fabricated external mechanism fact:
provenance = `repo replay of data/discovery/fixtures/05-analogy-as-mechanism.json (Q34
ANALOGY_AS_MECHANISM; commitment_candidate, not committed_current)`. Q34's own gate rejects the
same fixture (`ANALOGY_AS_MECHANISM = 7`); Q37's replay reaches the consistent verdict via its
`Q14_CLAIM_NOT_COMMITTED` (14) check, proving the two gates agree without Q37 re-litigating Q34.

## Forbidden by design (hard boundary)

- No `MECHANISM_EQUIVALENCE_PROVEN` / `UNIVERSAL_LAW_PROVEN` as repository auto-outputs.
- No Q38 case retrieval inside Q37.
- No claim that two domains share a mechanism, that real-world causal transport is proven, or
  that a universal cross-domain law holds.
- No materialization of F15 / D1 / D2.
