# Historical Basis-Leaps Reconstruction — IGNITION-20260906-158

Status: research-only; `DETECTOR_NOT_VALIDATED / UNDERDETERMINED`; no canonical, production, authority, capability, lifecycle, external-truth, or Owner-acceptance change.

## Provenance and scope

This reconstruction executes the command source `Arvin-liu/1111:agent-commands/IGNITION-20260906-158.md`.

- source Git blob: `918dce85cc18f6e653422b162c593af6b33d60a8`
- source content SHA-256: `513146ae504d794d6a1440c86b3d534d6ed0ba90f4e12c4946a943682461c8f9`
- formal execution base: `main@212322d41db79bce2dbd116166d3f1ad226291f3`
- reconstruction mode: historical replay with frozen blind packets, counterfactual review, and research-only adjudication

The exact phrase `丹无定型` was not found by exact-text search in the execution-time formal repository or its Git history. It is therefore treated as an Owner-supplied research premise from the command, not as canonical repository provenance. The reconstruction uses observable Git trigger material, changed-object summaries, and bounded repository evidence.

## Frozen detector

The detector emitted `basis_change_signal=true` only when the trigger material jointly satisfied:

`representation_change AND ontology_mutation AND (generator_mutation OR backward_reinterpretation)`

The frozen candidate gate required all of the following:

1. at least three independent corpus families;
2. basis-free rediscovery;
3. positive holdout gain;
4. ablation loss; and
5. a falsifier.

The frozen control thresholds were positive holdout detection in at least 1/2 and negative holdout false positives in at most 0/2. Answer labels were withheld during packet construction and blind scoring.

## Historical controls

| ID | Historical trigger | Split | Unblinded reference label | Detector signal |
| --- | --- | --- | --- | --- |
| P01 | function/case reframe — `a1295d737e290105069f915c577105c0cf5ff26f` | positive calibration | `TRUE_LEAP` | true |
| P02 | section-zero bootstrap — `0a04b42a1e7d21549593dc38ef5993e1503cdc5e` | positive calibration | `TRUE_LEAP` | true |
| P03 | dual-channel bootstrap — `9d924fe140f0c99f1f2a4952ea48dedc80dd348b` | positive holdout | `TRUE_LEAP` | true |
| P04 | 12 meta-protocols / 64-combination generation — `974b121e36145d6ed35b214619312001f97b21f8` | positive holdout | `TRUE_LEAP` | true |
| N01 | 116-note source synchronization — `911f97b66568dbf8ef012a6e8ffc28749c32e91c` | negative calibration | `ORDINARY_GROWTH` | false |
| N02 | incremental registry and extractor — `ab90558ae1c158d9a67146ebd288678b67e1c4c3` | negative calibration | `ORDINARY_GROWTH` | true |
| N03 | canonical protocol migration — `4c452149a451f074d949739086cfccdb3ec5bd56` | negative holdout | `ORDINARY_GROWTH` | true |
| N04 | publication/projection maintenance — `d4bfaa886908bd3b3f109c7d8220a89a5d469186` | negative holdout | `ORDINARY_GROWTH` | false |

The controls were purposefully selected historical cases, not a population estimate. N02 is a calibration false positive and N03 is a holdout false positive.

## Results

- positive controls detected: 4/4;
- positive holdout detected: 2/2;
- negative controls flagged: 2/4;
- negative holdout false positives: 1/2 (`N03`);
- frozen negative ceiling: 0/2;
- detector validation: failed.

The detector therefore cannot distinguish the required leap/non-leap distinction on the historical holdout. The command's mandatory stop condition is triggered. The result is not allowed to select `TRUE_EPISTEMIC_FIXED_POINT`, `REPRESENTATIONAL_LOCK_IN`, `GENERATOR_LOCK_IN`, or the mixed-lock-in verdict as a validated conclusion.

## Descriptive observations retained after the stop

The holdout and calibration material is still useful as a bounded descriptive audit:

- the positive examples all changed representation/object language in ways captured by the proxy;
- the N03 ordinary migration also satisfied the same proxy, demonstrating that the proxy is too permissive;
- the 64-combination event was detected through representation, ontology, and generator features, but its backward-reinterpretation feature was false;
- no causal claim about “basis escape,” generator lock-in, or a new epistemic fixed point survives the failed detector gate.

The corresponding machine records are in `ignition/data/research/basis-escape-meta-plasticity-2026-09-06/`. The data-level blind process was not cognitively independent: the same Codex process produced the detector, the answer key, and the unblind analysis.

## Boundary

This file is a reconstruction and review record. It does not modify the existing meta-protocol meanings, the 64 matrix, Psi-zero semantics, runtime behavior, permissions, authority, schemas, registries, mandatory validators, or production gates. Formal and receipt Draft PR evidence remains separate from this research result.
