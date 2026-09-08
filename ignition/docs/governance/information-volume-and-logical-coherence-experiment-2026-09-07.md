# IGNITION-20260907-162: information volume and logical coherence

This is a research-only ablation of longform input. It asks whether more ordered text and preserved logical/section order have distinguishable effects in the frozen measurement, without treating lexical counts as semantic validation.

## Design

The final 22-work corpus was processed in source order with ten anonymous, generic feature extractors (`EL-X01` through `EL-X10`). The feature names describe broad lexical/argument cues only: causal explanation, constraints, ordered procedure, observation support, failure/exception, reversal/repetition, identity/particularity, scope/boundary, regulation/response, and model/definition. These are not proposed new bases.

The ordered section state retained local definitions, unresolved premises, concept-term sets, causal/constraint edges, revision ledgers, later question/falsifier counts, and cross-section links. Across the final corpus this produced 8,883 causal/constraint edges, 22,431 revision entries, 6,830 questions, 3,491 falsifier cues, 835,114 cross-section dependencies, and 327 claim/reason/example/counterexample chains. These are extraction diagnostics, not adjudicated semantic objects.

## Volume ladder

The ladder used the same frozen source order and measured 10%, 25%, 50%, 75%, and 100% of each work. No threshold was chosen after looking at the result.

| Fraction of each work | Rows | Mean anonymous factor count | Minimum | Maximum |
| ---: | ---: | ---: | ---: | ---: |
| 10% | 22 | 9.545455 | 8 | 10 |
| 25% | 22 | 9.863636 | 8 | 10 |
| 50% | 22 | 9.954545 | 9 | 10 |
| 75% | 22 | 9.954545 | 9 | 10 |
| 100% | 22 | 9.954545 | 9 | 10 |

The frozen result is a small increase with an apparent plateau by 50%. The machine verdict is `INFORMATION_VOLUME_EFFECT_ONLY`: the 100% mean exceeds the 10% mean, but the measurement does not establish a semantic capability or a new basis.

## Cross-work accumulation

Three fixed permutations were evaluated at work nodes 1, 4, 8, 12, 16, and 20. All ten anonymous factors were visible at node 1. At node 4, permutation 1 retained nine while permutations 2 and 3 retained ten; all three permutations retained ten factors at nodes 8, 12, 16, and 20. Thus the accumulation result is recurrence of the generic extractors under the frozen corpus, not independent discovery of ten semantic laws.

The complete node-by-permutation record is `cross-book-accumulation-results.jsonl`. It is intentionally reported separately from the historical track because a recurring lexical cue is not the same object as a historical failure mechanism.

## Coherence ablation

Coherence was evaluated on the 16 discovery works only. Each work has:

- `O_ORIGINAL_ORDER`: original section order;
- `S_SEEDED_CHAPTER_SHUFFLE`: deterministic chapter/section shuffle;
- `F_FRAGMENT_BAG`: deterministic fragment bag;
- identical token counts and identical token-multiset digests across O/S/F after the final segmentation repair.

There are 16 paired work comparisons. Original order has a higher ordered-cue-pair count than both controls in 5 of 16 comparisons (`0.3125`), below the preregistered 0.60 support threshold. Mean ordered-cue pairs were 264.875 for O, 263.8125 for S, and 264.0000 for F. Therefore the coherence ablation does not support a reliable original-order advantage. This is a negative result against the stronger logical-coherence hypothesis, not proof that order never matters.

The exact rows, sequence digests, token-preservation flags, and pair calculations are in `coherence-ablation-results.jsonl`. Run 02's failed token-preservation output remains under `invalidated-runs/run-02/` and is not included in the final comparison.

## Interpretation ceiling

The combined input result is not `VOLUME_AND_COHERENCE_EFFECT_SUPPORTED_AS_RESEARCH_FINDING`. Volume is the only measured effect that clears its simple directional check, and its plateau plus lexical dependence make it a bounded research/heuristic observation. The coherence comparison is not supportive. No canonical runtime, validator, Current surface, production behavior, or external-truth claim follows.
