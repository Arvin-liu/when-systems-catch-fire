# IGNITION-20260907-162: basis-free longform induction

This document records the external-track induction after the source and hypothesis freezes. Candidate identifiers remain anonymous in the machine record so that later historical reconciliation cannot be treated as an answer-guided source choice.

## Candidate generation

Ten candidates, `EL-X01` through `EL-X10`, were generated from generic feature keys after the final corpus was frozen. Their observable keys were, respectively:

| Candidate | Generic measurement family |
| --- | --- |
| EL-X01 | causal explanation cues |
| EL-X02 | constraint/condition cues |
| EL-X03 | ordered procedure cues |
| EL-X04 | observation/support cues |
| EL-X05 | failure/exception cues |
| EL-X06 | reversal/repetition cues |
| EL-X07 | identity/particularity cues |
| EL-X08 | scope/boundary cues |
| EL-X09 | regulation/response cues |
| EL-X10 | model/definition cues |

This table is a post-freeze descriptive unblinding. It does not assert that any row is a new semantic axis. Feature counts use normalized lexical stems and ordered cue pairs; they are deliberately conservative and are not a semantic parser.

## Recurrence and holdout

The discovery split has 16 works across seven domain buckets. The held-out split has six works across six domain buckets. Every candidate was present in the discovery extraction, and held-out positive counts were:

| Candidate | Held-out positive works / 6 | Held-out domains / 6 | V2 status |
| --- | ---: | ---: | --- |
| EL-X01 | 5 | 6 | `UNDERDETERMINED` |
| EL-X02 | 4 | 6 | `UNDERDETERMINED` |
| EL-X03 | 4 | 6 | `UNDERDETERMINED` |
| EL-X04 | 3 | 6 | `UNDERDETERMINED` |
| EL-X05 | 2 | 6 | `UNDERDETERMINED` |
| EL-X06 | 3 | 6 | `UNDERDETERMINED` |
| EL-X07 | 3 | 6 | `UNDERDETERMINED` |
| EL-X08 | 1 | 6 | `UNDERDETERMINED` |
| EL-X09 | 4 | 6 | `UNDERDETERMINED` |
| EL-X10 | 2 | 6 | `UNDERDETERMINED` |

The holdout rows demonstrate lexical recurrence only. They do not establish L2 semantic increment, L3 a new question, L4 a counterfactual distinction, or L6 independent validation. L1 was not independently adjudicated and L5 is supportive-only. Consequently all ten candidates fail the final V2 gate; `all_candidates_pass_v2` is false.

## Existing-basis crosswalk and ablation

After external freeze, each candidate was conservatively cross-walked to existing broad ordered/causal/constraint/evidence language. Every row is marked `NOT_ESTABLISHED`, and `same_lost_question` is false. A deletion observation was recorded for each extractor, but deleting a feature and losing its count is method sensitivity, not proof that a semantic capability disappeared. No canonical deletion or runtime mutation was performed.

The controlling records are `basis-free-candidate-freeze.jsonl`, `external-v2-scores.jsonl`, `existing-basis-crosswalk.jsonl`, `candidate-ablation-results.jsonl`, and `candidate-deletion-conditions.jsonl`.

## Verdict

The external track supports only `INFORMATION_VOLUME_EFFECT_ONLY`. It does not support basis escape, a new canonical layer, a new generator, a Task159 V2 semantic-leap candidate, or a next semantic leap. The strongest positive statement is that generic feature counts recur across a large, diverse, legally accessible corpus; the strongest negative statement is that recurrence did not survive semantic V2 gates or the coherence advantage test.
