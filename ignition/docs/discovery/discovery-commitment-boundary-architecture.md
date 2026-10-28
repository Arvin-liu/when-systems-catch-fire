# Q34-I1 Architecture Decision — Discovery–Commitment Boundary & Verifiable Commitment Gate

- task_id: `121Q34-I1` (revision `I1R`)
- executor: Kimi-K3 Max (build-first campaign, checkpoint 1)
- trusted_main_base: `81edff4039619b8343a82cb1b84785c8a9f6a990`
- legacy LAB: `lab/121q34-discovery-commitment-night` (tip `d4b6ae59`), preserved via tag `legacy-lab-q34-discovery-commitment-night-12026-07-17`; selectively reimplemented, NOT merged/cherry-picked.
- status: Draft candidate (not reviewed, not merged, not Current)

## 1. Purpose

Separate **"we discovered a candidate claim"** from **"the project is allowed to commit this claim as a current conclusion."** The boundary must be repository-native, evidence-bound, deterministically verifiable, and must preserve uncommitted paths and retraction history. It must block commitments that are unsupported, self-certifying, beyond their claim ceiling, or that pass structural mapping off as real-world truth.

This is **not** a proof that any project conclusion is true in the real world, and it does **not** create L7, a truth layer, or an automatic reality arbiter.

## 2. Repo-native forensics (what already exists)

| Existing capability (reused, not duplicated) | Where | Role in Q34 |
|---|---|---|
| L0–L6 architecture + L5→L6 publication boundary | `ARCHITECTURE.md`, system map | Commitment plane maps to L6/Current surface; discovery plane is pre-L6 |
| claim ceiling | iteration manifests/seals, F12 receipt, Q33 components | Every claim carries a ceiling the gate enforces and never widens |
| evidence refs / provenance / exact-head binding | `validate_external_attestation.py` (F12), iteration manifests | Claim evidence references must resolve and bind to exact heads |
| external attestation (F12 lifecycle) | `tools/validate_external_attestation.py`, `data/governance` | Commitments requiring external attestation must reference valid receipts |
| Q33 fail-closed publication/rights gate | `tools/governance/fail_closed_publication_gate.py`, `data/governance/*` | Answers "may we (re)publish", a **separate** question from "may we commit" |
| iteration manifest / completion seal / lifecycle | `tools/validate_iteration_sync.py`, `data/operations/iterations/` | Q34 registers as an iteration manifest + seal; lifecycle consistency enforced |
| generated-output authority | `tools/operations/validate_generated_output_authority.py`, `data/operations/generated-output-authority.json` | Q34 generated registry/map outputs registered as producer_command outputs |
| change propagation + system map | `tools/operations/compute_change_propagation.py`, `tools/generate_interactive_system_map.py` | Q34 components registered in project-components; map regenerated |
| retraction / supersession / history | governance history, iteration seals | State machine keeps retracted/superseded/deferred history |

## 3. What is genuinely new in Q34 (the gap)

1. A **typed claim/proposition record** with explicit discovery-vs-commitment state.
2. A **state machine** that forbids jumping straight from discovery to commitment.
3. A **commitment decision object** (COMMIT / DEFER / REJECT / DOWNGRADE_SCOPE / REQUIRE_INDEPENDENT_REVIEW / RETRACT_OR_SUPERSEDE) with a non-self-approval rule.
4. A **fail-closed deterministic commitment gate** (`validate_commitment_gate.py`) that mechanically blocks the forbidden commitment patterns.

## 4. Why the commitment gate is NOT merged into the Q33 rights/publication gate

- Q33 answers: **"even if commitable, do we have the rights to (re)publish this material?"** (source rights, jurisdiction, non-republication).
- Q34 answers: **"is this claim allowed to become a project conclusion at all?"** (evidence, independence, ceiling, self-certification, lifecycle).
- These are different authorities with different failure modes. Call order:

```
discover candidate → bind evidence → validate scope → COMMITMENT GATE (Q34) → rights/publication gate (Q33) → L6 / Current surface
```

A claim can pass Q34 (committable) yet fail Q33 (no republication rights), and vice versa. They are deliberately not one gate.

## 5. Why NO L7 / truth layer / automatic reality arbiter

The gate only decides whether a claim is **repository-committable under its declared claim ceiling and bound evidence**. It does not assert real-world truth, legality, causality, or completeness. Structural analogy, repository consistency, or test-passing are recorded as *in-repo* facts and are explicitly prevented (by the ceiling and the `STRUCTURAL_ANALOGY` rule) from being upgraded to real-world mechanism/truth. Adding a truth layer would violate the claim ceiling and the project convention that Main is "best current belief under current evidence," not permanent truth.

## 6. How Q34 serves Q35 / Q36

- Q35 (execution vs governance responsibility) consumes the **commitment decision + actor** fields to distinguish who is responsible for a commitment vs an execution.
- Q36 (observation/prediction/intervention) consumes the **claim type + scope + evidence independence** fields to treat observations/predictions/interventions as distinct claim kinds with distinct ceilings.
- The gate exposes a stable typed contract (`schemas/discovery/commitment-claim.schema.json`) and a deterministic validator with stable exit codes — the interface Q35/Q36 build on.

## 7. Provenance

Inspired by (but not certified by) the legacy LAB prototype `lab/121q34-discovery-commitment-night`. Dual-plane / three-gate / promotion-demotion-residue ideas were selectively reimplemented; Q33-superseded rights assets, hardcoded SHAs, self-attesting tests, and LAB text were rejected (see `q34-legacy-lab-salvage-matrix.json`). No legacy commit was cherry-picked.
