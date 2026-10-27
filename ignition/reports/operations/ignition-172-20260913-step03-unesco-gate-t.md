# IGNITION-20260912-172 — Gate T UNESCO taxonomy authority lock

Status: `GATE_T_PASS_FOR_AUTHORITY_LOCK; MASS_INGESTION_REMAINS_GATED_BY_GATE_R_AND_GATE_C`

This is the next Formal logical step after the Task172 Step02/Foundation exact-head checkpoint. The command direction is `Arvin-liu/1111@b1fc45fb`, `agent-commands/IGNITION-20260913-176.md`, blob `98fd25bd1886cf8675992413d6c55d1e09b4502f`. The Formal pre-freeze head was `9dc446517ccc02b5e5d8ca383f0aed28ab7e4afc`; PR #218 remains OPEN + DRAFT + unmerged.

## Source and rights boundary

Primary authority: UNESCO, *Proposed International Standard Nomenclature for Fields of Science and Technology*, `UNESCO/NS/ROU/257 rev.1 / SC-88/WS-80`, 1988. The recovered scanned PDF is bound by SHA-256 `78f37a0efdd34647e35d408fae8d958d4bf10021275b153c11b3539dceadbefa`. PDF and bulk OCR remain outside Formal. Formal persists only minimum code, label, hierarchy, discrepancy, and provenance metadata. BARTOC, SKOS, CyTA, and the historical EPI table are cross-checks, not substitutes for the primary.

The scan-sensitive inputs were frozen before this step in `data/research/task172-gate-t-unesco-1988/source-freeze.json`. The generated closure is reproducible from the frozen primary-scan hashes, coordinate-bound repairs, and visual row anchors; the second scratch build produced `GATE_T_SECOND_RUN_NO_DIFF`.

## Exact authority and counts

| Representation | Fields | Four-digit disciplines | Six-digit subdisciplines | Role |
|---|---:|---:|---:|---|
| 1988 UNESCO primary scan | 24 | 245 | 2178 | authority |
| SKOS mirror | 24 | 248 | 2232 | machine-readable cross-check |
| Formal local inventory | 24 | 250 | — | legacy comparison |
| Historical EPI comparison table | — | 245 | 2183 | secondary corroboration only |

`245` is the count of four-digit discipline headings recovered from the 1988 primary scan, with the explicitly recorded printed/OCR heading anomalies resolved by page context. It is not imported from the local 250 list.

`248` is the SKOS mirror count. Its exact extras relative to the primary are `2290`, `2390`, and `2490`; no SKOS discipline is missing from the primary set after this comparison. They remain representation/variant discrepancies, not authority substitutions.

`250` is the Formal local inventory count. Relative to the primary it has the exact extras `2290`, `2390`, `2391`, `2490`, `6115`, and `7100`; it lacks primary `6101`. No local code was silently deleted or promoted.

The secondary table reports 2183 six-digit rows, but the page-level primary scan census is 2178. The exact five CyTA rows absent from the primary scan are `1210.99`, `2415.01`, `2415.02`, `3206.12`, and `3206.13`. The primary scan has exact rows absent from CyTA: `2205.11`, `3206.14`, and `3206.15`. Therefore 2183 is retained as a secondary discrepancy, not forced into the primary taxonomy.

## Six-digit discrepancy ledger

The primary-only rows are `2205.11`, `3206.14`, `3206.15`.

The 57 mirror-only rows are:

`1210.99`, `2205.09`, `2207.90`, `2209.90`, `2210.90`, `2210.91`, `2210.93`, `2211.90`, `2211.91`, `2290.01`, `2302.90`, `2302.91`, `2306.90`, `2306.91`, `2390.01`, `2401.90`, `2401.91`, `2407.90`, `2409.90`, `2409.91`, `2409.92`, `2414.90`, `2415.01`, `2415.02`, `2417.90`, `2417.91`, `2417.92`, `2420.91`, `2490.01`, `2490.02`, `2510.90`, `2510.91`, `2510.92`, `3103.90`, `3103.91`, `3104.90`, `3206.12`, `3206.13`, `3302.90`, `3303.90`, `3305.90`, `3307.90`, `3307.91`, `3307.92`, `3307.93`, `3309.90`, `3309.91`, `3309.92`, `3309.93`, `3309.95`, `3315.90`, `3321.90`, `5310.90`, `5310.91`, `5312.90`, `5506.90`, `5907.90`.

The 47 suffix variants (`.90`, `.91`, `.92`, `.93`, `.95`) and the four discipline-block rows are recorded as exact mirror differences. They are not attributed to CSIC or another chronology without a primary citation.

## Gate disposition

Gate T is closed for the authority lock: the primary parse, discrepancy ledger, authority order, exact 24/245 count, minimum-rights note, deterministic validator, and second-run no-diff evidence are present. Gate R is not passed by this step. The prior 750-row routing pilot remains scratch-only and must be recomputed against this authority lock; its unresolved rate was 288/750. Gate C is not passed. No scholarly metadata is promoted to evidence, no full text is persisted, and no 24-field Formal mass ingestion is authorized.

The next Formal step is Gate R. Until Gate R and Gate C both pass, all 24 field lanes may continue scratch candidate discovery, provider probing, query preparation, cleaning, and dedupe only; they may not write authoritative taxonomy, routing, or scholarly corpus records.
