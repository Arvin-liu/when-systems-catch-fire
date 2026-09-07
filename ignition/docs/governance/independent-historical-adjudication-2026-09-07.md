# IGNITION-20260907-162: independent historical adjudication

The historical track uses repository history as a separate source channel from the external longform corpus. It is a procedural blind-separation exercise and is not claimed to be cognitively independent or human-adjudicated.

## Frozen sample and masking

The sample contains 240 residual leads from the Task160 repository universe and 160 C7 engineering negative controls. Selection was deterministic and completed before loading the Task161 model definitions. Packets are identified as `HP-0001` through `HP-0400`; candidate names and source-family labels are absent from packets. The hidden manifest records seven families (`C1`–`C7`) and the available August/September 2026 time slices. Ten packets contained source terms that were redacted from the evidence excerpt.

Each packet retains a source path/blob hash, observed history commit evidence, sanitized excerpt, and neutral facts such as endpoint properties, ordered intermediate events, cross-object binding, authorization/evidence, rollback, lifecycle, and other nonlocal dependencies. These neutral facts are evidence bookkeeping, not an independently adjudicated semantic taxonomy.

## Two-pass result

Pass 1 and pass 2 were run as separate procedural passes over the same frozen packets. Pass 1 used `CONFIRMED_CLEAN`; pass 2 used the stronger-negative name for the same clean condition. Reconciliation therefore changes only that label name and retains one final ledger.

| Final label | Packets |
| --- | ---: |
| `CONFIRMED_DEFECT` | 67 |
| `STRONG_NEGATIVE` | 72 |
| `UNDECIDABLE` | 261 |
| **Total** | **400** |

The preregistered defect floor of 40 is met, but the clean/strong-negative floor of 80 is not. The 261 undecidable packets prevent a strong historical conclusion. Labels are based on explicit repository text markers and correction/follow-up signals; they are not expert or human adjudication.

## Minimal nonlocal facts

The following counts are overlapping packet-level taxonomy observations, not mutually exclusive classes:

| Neutral fact | Confirmed defects (67) | Strong negatives (72) | Undecidable (261) |
| --- | ---: | ---: | ---: |
| Endpoint properties only | 63 | 63 | 230 |
| Unordered endpoint pair | 54 | 6 | 56 |
| Ordered intermediate events | 65 | 54 | 208 |
| Cross-object identity/binding | 48 | 29 | 141 |
| Authorization/evidence to a specific change | 63 | 56 | 214 |
| Rollback/inverse link | 25 | 2 | 36 |
| Epoch/staleness/lifecycle link | 59 | 59 | 179 |
| Other nonlocal fact | 58 | 38 | 113 |

The high overlap, especially for endpoint and ordered-event cues, shows why presence of a neutral fact cannot by itself identify a semantic defect.

## MS/MT adapter check

Only after the history labels were frozen was the Task161 model definition hash loaded: `ea12f8da31d343ef3bfc4d3da88542fcab55de46ecfbb452672d923ceb519999`. MS and MT were forced to use the same neutral facts; no parameters or packet labels were changed.

| Adapter | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MS | 65 | 63 | 2 | 9 | 0.507812 | 0.970149 |
| MT | 67 | 72 | 0 | 0 | 0.482014 | 1.000000 |

MT therefore adds no clean discrimination: it predicts all 72 strong negatives as defects. The required four-family MT increment is false, and procedural separation is not cognitive independence. The historical verdict is `HISTORICAL_UNDERDETERMINED`.

Frozen digests are recorded in `history-adjudication-freeze.json`: packet `615ce7640754efea1149dde7ef30b961a8dd896f05e3e92cbf2c5f54fbb36ada`, pass 1 `ec8827f4387ac450d944663ec67695a753420b617b6c00e457d5019f397635fb`, pass 2 `3c9e852ab0586172c19c91a38bfa04a723ff28051ffa944fcf69cd8eb826def7`, disagreement `946b390faa31d8c9b5f84d80b74dc88b8f33a7b3b1916f320ae56f9489380518`, and final labels `7088193f6b9eba3984b19e2d9569bc5646e06126aeca07509a141048bca46b90`.
