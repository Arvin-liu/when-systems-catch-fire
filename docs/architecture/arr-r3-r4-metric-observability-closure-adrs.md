# ARR R3/R4 Metric Semantics & Observability Closure — ADR

- task: `ARR-R3-R4-METRIC-SEMANTICS-OBSERVABILITY-CLOSURE-R1-RELAY-20260725`
- control commit: `afb3089a54798bd5d4dcdb10c796a36f219ef724`
- formal predecessor: `27af5f99e13d8217961cbc803520c648ce791c68` (PR #128)
- status: `DRAFT_AWAITING_EXTERNAL_REVIEW`

## 1. Problem

R4 metric-disclosure & relay-receipt repair (PR #128) closed the 27-item
capability closed set, separated governance enum from the no-action safety
invariant, and distinguished contradiction attribution from repair. Four
lower-level metric / reporting issues remain before R5 can rely on
observability:

1. **M3** — R3 aggregate reports `crash_recovery_success_rate = 0.0`; the
   authoritative demo evidence reports 3/3 successful crash-resume scenarios and
   the run ledger records 1.0. The aggregate used a different (zero) denominator
   (in-run crash events) and understated demo success.
2. **M4** — R3 aggregate reports `incremental_selectivity = 0.0`; the isolated
   changed-note rerun reprocessed exactly 1/836 and the run ledger records
   0.001196. The old name is also ambiguous (a low reprocess fraction is good).
3. **M5** — R3 `all_pass = true` disclosed no dimension allocation. R4 now
   supplies a closed set, but the historical R3 output must receive a versioned
   correction/erratum rather than remain the only machine-readable
   interpretation.
4. **R4 semantic conflation** — the repaired output assigns four checks to the
   SEMANTIC dimension with `pass = 4` yet also `measured = false`, conflating
   "were semantic guardrails executed" with "was semantic understanding
   measured".

## 2. Decision: a versioned correction layer, not history rewrite

We implement a **versioned correction layer** (`arr_metric_correction/`) that
references exact historical input digests, exposes original value, authoritative
source, corrected interpretation/value and lifecycle, and marks the historical
value as preserved-but-superseded for current interpretation.

### Immutable-history boundary (never mutated)

- the frozen 836-note corpus and its source notes;
- R3 per-object receipts / envelopes / demonstration reports;
- R3 historical `AGGREGATE_METRICS.json`, `CAPABILITY_COVERAGE_MATRIX.json`, run
  ledger and other evidence files;
- R4 and R4-repair private evidence;
- PR #126 / #127 / #128 branches and tags;
- Main (`81edff40…`).

The correction layer has **no write path** to any of the above. It only reads
sealed input identities (digests) and emits new public correction artifacts.

### Correction-layer authority

- Sealed historical values are referenced by report identity + SHA-256 digest.
- A corrected metric carries `historical_value` + `historical_source`, the
  authoritative `authority_source`, `precedence_rule`, and
  `supersedes_for_interpretation` (true only where the current interpretation
  replaces the historical one; the historical artifact itself is unchanged).
- Every corrected rate/fraction fails closed on missing numerator/denominator/
  population/applicability, and maps denominator 0 to `NOT_APPLICABLE` rather
  than a misleading `0.0`.

## 3. Schema contract (§5)

`MetricDefinition` carries `metric_id`, `schema_version`, `display_name`,
`semantic_kind`, explicit `numerator`/`denominator` (label/value/source),
`population`, `applicability`, `value`/`unit`, `directionality`,
`authority_source`/`precedence_rule`, `historical_value`/`historical_source`,
`correction_status`, `underlying_defect_present`,
`underlying_defect_repaired_in_current_layer`, `supersedes_for_interpretation`,
`evidence_refs`, `note`. `validate_metric_definition` enforces the fail-closed
rules.

## 4. Lifecycle closure (§8)

`underlying_defect_repaired_in_current_layer` is **never hard-coded**; it is
derived from validator evidence (the `corrections_validated` map produced by
running the validators). M3/M4 defects are repaired in the correction layer when
their projections validate; M5 historical artifact is preserved, and only the
current/superseding interpretation is marked repaired. M1/M2/M6 have no underlying
code defect; after clarification, `followup_required` is false.

## 5. Non-goals / red lines

- No R5 implementation, Life Integrity, Embodied Life, Modern Wuzhen, Domain
  Pack/Federation.
- No PROMOTE / EVOLVE / real-world action.
- No corpus rerun or modification of the 836 notes.
- No private note content, titles, transcripts, full URL lists, PII or
  reconstructive features in public output.
