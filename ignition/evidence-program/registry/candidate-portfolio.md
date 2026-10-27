# Evidence Candidate Portfolio (Task 103 §4)

This portfolio is derived deterministically from the governed corpus: current open
questions, public claims, high reverse-dependency assets, Function OS / MCF / PSD /
ARN candidates, quarantined/pending assets, and the external-source registry.

## Scoring method (documented; numeric score is NOT truth — §4)

Each candidate is scored 0–1 on: `falsifiability`, `data_availability`,
`provenance_quality`, `baseline_availability` (higher = better), and
`evidence_cost`, `confounding_risk` (higher = worse). Composite
`ranking_score` weights the "higher-is-better" axes and subtracts a fraction of the
"higher-is-worse" axes:

```
score = 0.30*falsifiability + 0.20*data_availability + 0.15*provenance_quality
        + 0.15*baseline_availability - 0.10*evidence_cost - 0.10*confounding_risk
```

The score is a prioritization aid, not an authorization. Human reasoning decides.

## Ranked portfolio

| ID | Candidate | Decision | Score | Why |
| --- | --- | --- | --- | --- |
| C-01 | Crossref re-verification of 117 source-registry DOIs | **PRIMARY** | 0.86 | Real external oracle, cheap, falsifiable, directly tests a repo claim (METADATA_VERIFIED tier). |
| C-03 | DOI cross-source OpenAlex check | RESERVE | 0.74 | Second independent oracle for the same DOIs. |
| C-02 | Case-table historical anchors (Wikipedia) | RESERVE | 0.72 | Bounded historical-anchor existence test. |
| C-04 | Function OS v0.2 correctness | DEFERRED | 0.58 | Needs a constructed reference oracle; next pilot. |
| C-07 | Open-questions registry claims | DEFERRED | 0.45 | Depends on the registry this pilot creates. |
| C-05 | Multiscale causal fabric edge-case | DEFERRED | 0.50 | Internal-consistency only (not external evidence, §3.5). |
| C-06 | Four-force unification / quantum gravity | DEFERRED | 0.12 | §3.9: not chosen for narrative; no bounded feasible protocol this round. |

## Selection rationale

- **Primary = C-01.** It is the only candidate that is (a) genuinely external
  (Crossref is an independent authority, not the repo), (b) cheap and fully bounded,
  (c) directly falsifiable per-DOI, and (d) able to change a real repo state — the
  `evidence_tier_104: METADATA_VERIFIED` rating of the external-source atlas. A
  failure here is meaningful (it would downgrade source reliability); a pass is
  earned, not flattering.
- **Reserve = C-03 / C-02.** Both are bounded external-oracle checks; held as ready
  follow-ups if C-01 is blocked (e.g., Crossref policy) or to extend coverage.
- **Deferred grand-physics (C-06).** Per §3.9, no unification/quantum-gravity claim
  is selected merely for narrative importance, and no bounded, independently testable
  protocol exists this round. Explicitly deferred.
- **Deferred internal-consistency (C-05).** Internal consistency is not external
  evidence (§3.5); lower priority than an external-oracle pilot.

## Why this is "minimal but real"

The portfolio is reproducible: re-running the scoring on the same corpus yields the
same ranking. The primary pilot is small enough to finish in this task yet meaningful
enough to move an E rating / claim wording / quarantine status (§4).

## Task 110 state overlay

The table above is retained as the immutable task-103/task-109 historical portfolio;
its scores and selection labels are not rewritten after seeing task-110 results.
The governed state overlay in `task-110-portfolio-state.json` reconciles those labels
against authoritative lifecycle/evidence records:

- `C-01` → `COMPLETED_SUPPORTED` (task 103), excluded from active scheduling.
- `C-04` → `COMPLETED_SUPPORTED` within its bounded domain (task 105), excluded from
  active scheduling.
- `C-03` → `COMPLETED_PARTIAL` (task 110 OpenAlex metadata replication), retained in
  history and not silently rescheduled.
- Corrected active queue: `CF-apple_gravity_failure`, followed by reserves
  `CF-cross_domain_synergy_risk` and `CF-technology_economic_growth_failure`.

This overlay is a lifecycle projection, not a replacement portfolio and not an
authorization to create task 111.
