# Task229-R3 Interface Failure Taxonomy R0

## Scope and result

This is a mechanical replay of the historical `REFERENCE_M1` route traces for six lineages and cases A/B/C. It uses the frozen Task228 policy bytes, the frozen case-input map, the original R0 response schema, the frozen R1 session-run index, and the original `verify_trace` implementation. It contains no evaluator scores, target criteria, or target-success labels.

- Case traces accepted by the original verifier: **11/18**.
- Lineages with all three traces accepted: **3/6** (L01, L02, L03).
- Structurally valid R0 response cases: **18/18**.
- Policy ID and preserved-baseline checks: **18/18 match**.
- Multiple/conflicting route matches: **0**.

The case-level machine record is [`interface-failure-taxonomy.json`](interface-failure-taxonomy.json). It preserves each allowed binding and route-trace field, the exact policy and stdout hashes, the reference route replay, and the verifier predicates.

## Case-level findings

| Lineage | Case | Required input absent from binding | Reference → traced route | Absent input incorrectly traced | Classification |
|---|---|---|---|---|---|
| L01 | A | — | selector → selector | — | `TRACE_PASS` |
| L01 | B | — | fallback → fallback | — | `TRACE_PASS` |
| L01 | C | — | fallback → fallback | — | `TRACE_PASS` |
| L02 | A | — | fallback → fallback | — | `TRACE_PASS` |
| L02 | B | — | fallback → fallback | — | `TRACE_PASS` |
| L02 | C | — | selector → selector | — | `TRACE_PASS` |
| L03 | A | — | selector → selector | — | `TRACE_PASS` |
| L03 | B | — | fallback → fallback | — | `TRACE_PASS` |
| L03 | C | — | fallback → fallback | — | `TRACE_PASS` |
| L04 | A | F02B_GRAVIMETRIC_REPLICATES_AGREE | fallback → fallback | F02B_GRAVIMETRIC_REPLICATES_AGREE | `ABSENT_INPUT_ID_TRACED` |
| L04 | B | F02B_GRAVIMETRIC_REPLICATES_AGREE | fallback → fallback | F02B_GRAVIMETRIC_REPLICATES_AGREE | `ABSENT_INPUT_ID_TRACED` |
| L04 | C | F02B_GRAVIMETRIC_REPLICATES_AGREE | fallback → fallback | F02B_GRAVIMETRIC_REPLICATES_AGREE | `ABSENT_INPUT_ID_TRACED` |
| L05 | A | — | selector → selector | — | `TRACE_PASS` |
| L05 | B | — | fallback → fallback | — | `TRACE_PASS` |
| L05 | C | — | fallback → stop | — | `BOUND_INPUT_VALUE_REINTERPRETED`, `ROUTE_TYPE_MISMATCH`, `RULE_ID_MISMATCH` |
| L06 | A | F03B_ASSAY_REPLICATES_RECONCILE | fallback → fallback | F03B_ASSAY_REPLICATES_RECONCILE | `ABSENT_INPUT_ID_TRACED` |
| L06 | B | F03B_ASSAY_REPLICATES_RECONCILE | fallback → fallback | F03B_ASSAY_REPLICATES_RECONCILE | `ABSENT_INPUT_ID_TRACED` |
| L06 | C | F03B_ASSAY_REPLICATES_RECONCILE | fallback → fallback | F03B_ASSAY_REPLICATES_RECONCILE | `ABSENT_INPUT_ID_TRACED` |

## Exact failure causes

### L04 / POLICY_F02_B and L06 / POLICY_F03_B

The frozen binding has two present inputs and one required input absent in every case:

- L04: `F02B_GRAVIMETRIC_REPLICATES_AGREE` is absent.
- L06: `F03B_ASSAY_REPLICATES_RECONCILE` is absent.

The reference route is fallback for all six cases because the selector cannot fully match without the third input. Each historical trace still lists that absent input ID. The original verifier rejects it at the `input_id not in case_values` check before route selection is considered. The traced route type and null rule/action IDs otherwise match fallback. This is `ABSENT_INPUT_ID_TRACED`; it is not a policy-route mismatch and does not justify treating absence as null or false.

### L05 case C / POLICY_F03_A

The frozen binding records `F03A_MEASUREMENT_VALID=true`, group `P`, and pulse pattern `pulse_duration_indeterminate_due_to_trace_gap`. Those bound values produce fallback under the frozen policy. The historical trace selects `POLICY_F03_A_INVALID_MEASUREMENT_STOP`, whose condition requires `F03A_MEASUREMENT_VALID=false`. That contradicts the authoritative bound value. The original verifier therefore expects fallback and rejects the trace's stop route and non-null selected rule ID. The trace also omits two present route-relevant binding IDs; that is recorded as an R1 trace-completeness observation, while the original R0 verifier's direct rejection is the route-field mismatch.

### Passing lineages and cases

L01, L02, and L03 pass all three cases. L05 passes A and B. Their traced route type, selected rule/action, policy ID, and preserved baseline IDs match the original deterministic replay, and their trace input IDs are present and unique.

## Replay method and provenance

The diagnostic mirrors the frozen `verify_trace(response, policy, case_values)` logic from `tools/recompute.py` at `961603c2cb8b6cd1aac14ff72ecd946e26828aa5` (SHA-256 `2a81a493b2d40cde023b4017a72c3aa7dfe45dee96fc06e223639fb082902b54`). Conditions match only when the operator is `eq`, the input ID exists in the frozen case map, and its value equals the literal. The verifier checks policy ID and both baseline lists, rejects duplicate or unbound traced IDs, rejects multiple/conflicting route matches, then requires the selected route type and IDs to match the deterministic route. With no matching stop or selector, fallback requires null rule and action IDs.

Source locks:

- Task228 policy base: `d82a52077df6d4e96e998ace3757f2fb343b4db5`.
- Frozen six-policy SHA-256 values: recorded per case and in the machine file; they match Task228 `SHA256SUMS`.
- Task229 scientific-source commit: `961603c2cb8b6cd1aac14ff72ecd946e26828aa5`.
- Concrete prompt/input-map commit: `4ee132e8d50e8805c466cb5d681aaa18c34c9f68`.
- Case-input map SHA-256: `b2d44d56aa602e429a8f3ddded61e0b3524b16700a4d35232126a5e264ffa057`.
- Historical R1 route-trace source: Draft PR #240 head `d7c4715d0cdc23b8d2b0bf4c5285ce0ac6d5041b`; only the six `REFERENCE_M1` stdout files were opened, and each matched its frozen session index SHA-256.

This taxonomy supports only an interface-mechanics diagnosis. It does not establish live interface execution, reference-target compatibility, incremental policy effect, transfer, or any broader scientific claim.
