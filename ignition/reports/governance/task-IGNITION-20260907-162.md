# Governance report: IGNITION-20260907-162

## Controlling specification and lifecycle

The controlling specification is `Arvin-liu/1111/agent-commands/IGNITION-20260907-162.md` at command commit `8ab1aac0cdedd4874c798f4593614335cdd79e76`, blob `df58765e5c21cf3b0aba15f804ce461b4b1c542e`, complete-content SHA-256 `e4e61e12ca3798b72b714c0fc2e9cf1ec0b1224529dee138c9740a0fc2b4b65a`. The Formal base is `Arvin-liu/when-systems-catch-fire` branch `work/IGNITION-20260907-161` at `5ccb15d45cec259d5397f1843278fd98011105aa`.

The command was executed as research-only work. The required `instructions/CURRENT.md` and `relay/current` pointers were missing in the exact base and remain untouched, recorded as `STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL`. No canonical runtime, canonical validator, Current/relay surface, Ready transition, merge, Owner acceptance, production claim, external action, or Task163 was performed.

The result remains `RESEARCH_ONLY_DRAFT_PENDING`.

## Formal publication receipt

Formal Draft PR #212 was created at `https://github.com/Arvin-liu/when-systems-catch-fire/pull/212`. At the first exact-head observation, it was OPEN and DRAFT with base `work/IGNITION-20260907-161` at `5ccb15d45cec259d5397f1843278fd98011105aa` and head `work/IGNITION-20260907-162` at `e94a067f94f572afe886a422354a3257ce03b116`. The first exact-head Actions snapshot showed `foundation-validation` run 876, `repository-path-accounting-preflight` run 270, and `architecture-pages` run 33 all `in_progress`. This is a pending CI observation, not acceptance.

## Explicit answers to the command questions

1. **How much eligible corpus was actually obtained?** Twenty-two eligible works, 4,368,310 normalized words, 8,083 ordered sections, nine domains, and 18 book/monograph/open-textbook-scale works. The 23rd retrieved candidate, NIST SP 800-218, was excluded at 15,964 words/86 sections.

2. **How were domains, authors, years, and publication types controlled?** The protocol froze nine domain buckets, fixed source order, legal access rules, a four-work/domain ceiling, a two-work/author ceiling, and a catalog-order replacement rule. The selected maximum author count is two; selected types are public-domain books/monographs, official NIST handbooks, official RFCs, and OpenStax open textbooks. The corpus is access- and language-biased and is not population-representative.

3. **What does the 10/25/50/75/100% ladder show?** Mean anonymous-factor counts are 9.545455, 9.863636, 9.954545, 9.954545, and 9.954545 respectively. The directional result is volume-only with a plateau by 50%.

4. **Do factors accumulate across books and permutations?** At nodes 1/4/8/12/16/20 across three permutations, all ten generic factors are retained at every node except permutation 1 at node 4, where nine remain. This is recurrence of frozen extractors, not semantic discovery.

5. **Does logical coherence survive O/S/F ablation?** No reliable support. On 16 discovery pairs with identical token counts and per-work multiset digests, original order beats both shuffled and fragment controls in 5/16 (`0.3125`), below the 0.60 threshold.

6. **Is the owner-level book hypothesis supported?** Only in the bounded form `INFORMATION_VOLUME_EFFECT_ONLY`; the stronger volume-plus-coherence claim is not supported.

7. **Do the external factors map to an existing basis or a new lost question?** After the external freeze they map conservatively to broad existing ordered/causal/constraint/evidence language. Every crosswalk row has `same_lost_question=false`; no new semantic basis is established.

8. **Did deletion or ablation prove a new generator/meta-protocol?** No. Deletion records only that removing a generic extractor removes its count. No semantic capability loss was independently adjudicated and no canonical change was made.

9. **Did any external candidate pass independent holdout and V2?** No. Ten anonymous candidates recur lexically across the discovery split and have heldout positives from 1/6 to 5/6 works over six heldout domains, but L2/L3/L4/L6 are not established for every candidate and L1 was not independently adjudicated.

10. **What did the historical track contain?** Four hundred blind packets: 240 residual leads and 160 C7 controls. Final labels are 67 `CONFIRMED_DEFECT`, 72 `STRONG_NEGATIVE`, and 261 `UNDECIDABLE`.

11. **What nonlocal facts recur in the historical packets?** Overlapping counts in defects/strong negatives/undecidables are, respectively: endpoint-only 63/63/230; unordered pair 54/6/56; ordered events 65/54/208; cross-object binding 48/29/141; authorization/evidence 63/56/214; rollback 25/2/36; lifecycle 59/59/179; other nonlocal fact 58/38/113.

12. **How do MS and MT score?** MS: TP 65, FP 63, FN 2, TN 9, precision 0.507812, recall 0.970149. MT: TP 67, FP 72, FN 0, TN 0, precision 0.482014, recall 1.0. MT predicts every strong negative as a defect.

13. **Is there independent external/history convergence?** No. The tracks are separate in provenance but not independently semantically adjudicated; the convergence record is `NO_INDEPENDENT_CONVERGENCE_ESTABLISHED`.

14. **Does the run independently support Task161 or a prior candidate?** No. Historical evidence is `HISTORICAL_UNDERDETERMINED`; external evidence is lexical/volume-only. No Task161 candidate is promoted.

15. **How many candidates pass the Task159 V2 gate?** Zero of ten. `v2-final-gate.json` records `all_candidates_pass_v2=false` and status `UNDERDETERMINED`.

16. **What is the next semantic leap?** None is validated or named. The strongest negative is the combination of no coherence advantage, volume plateau, zero V2 candidates, and high historical false positives. No Task163 was created.

## Evidence and residuals

The machine evidence is in `ignition/data/research/longform-emergence-and-historical-adjudication-2026-09-07/`, including the source/search freezes, section-state extraction, O/S/F and volume outputs, historical packets and two passes, MS/MT scores, crosswalks, V2 gate, verdict, and restart ledger. The two invalidated runs are preserved under `invalidated-runs/` and are excluded from final scoring.

Residuals are explicit: lexical extraction is not independent semantic adjudication; historical labels use repository text markers rather than human adjudication; procedural pass separation is not cognitive independence; canonical validation and remote Task162 CI are not yet observed at report authoring time; and the inherited Task161 Foundation drift is recorded separately. The epistemic status is `DETECTOR_NOT_VALIDATED / UNDERDETERMINED`, not acceptance.
