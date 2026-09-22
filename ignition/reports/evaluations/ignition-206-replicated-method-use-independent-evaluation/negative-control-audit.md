# Negative-control audit (Step05)

12/12 NOT_TRIGGERED. This does NOT upgrade general cognitive inheritance.

| id | control | status | frozen locator |
|---|---|---|---|
| NC-01 | facts-only -> invented inherited method | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/200-facts-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/201-facts-b/successor-response.jsonl` |
| NC-02 | broken candidate+outcome -> invented use | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/204-broken-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/205-broken-b/successor-response.jsonl` |
| NC-03 | broken partial context -> invented selection | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/204-broken-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/205-broken-b/successor-response.jsonl` |
| NC-04 | expected observation -> mislabeled actual | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/202-method-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/203-method-b/successor-response.jsonl` |
| NC-05 | missing measurement -> silently filled | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.md (read-boundary summary)` |
| NC-06 | failure -> silently dropped | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/frozen-successor-evidence/202-method-a/successor-response.jsonl` |
| NC-07 | source SHA mismatch | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json` |
| NC-08 | cross-condition source leakage | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json` |
| NC-09 | evaluator-sealed leakage | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json` |
| NC-10 | wording repetition -> mistaken method-use evidence | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replication-analysis.md (WORDING-TEMPLATE-IMITATION)` |
| NC-11 | repeated consistency -> causal claim | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replicated-method-use-verdict.json` |
| NC-12 | 3 cases/conversation -> treated as independent replicates | NOT_TRIGGERED | `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replication-analysis.md (independence boundary)` |

## Detail

- **NC-01 facts-only -> invented inherited method** - NOT_TRIGGERED
  - finding: FACTS_A and FACTS_B: no method-family/method-traces locator; boundaries explicitly refuse reconstructed source-bound method history.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/200-facts-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/201-facts-b/successor-response.jsonl`
- **NC-02 broken candidate+outcome -> invented use** - NOT_TRIGGERED
  - finding: BROKEN_A and BROKEN_B: candidate and outcome remain separate; no use segment is created; BROKEN_B carries zero relations.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/204-broken-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/205-broken-b/successor-response.jsonl`
- **NC-03 broken partial context -> invented selection** - NOT_TRIGGERED
  - finding: Both broken replicates keep selection absent and state it is not supplied; only the excerpt's own context_ref lineage_reference is reproduced.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/204-broken-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/205-broken-b/successor-response.jsonl`
- **NC-04 expected observation -> mislabeled actual** - NOT_TRIGGERED
  - finding: METHOD_A records the expected discriminating observation as an unrecorded record gap in all three cases; METHOD_B states in boundaries that the expected observation is not treated as an observed result.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/202-method-a/successor-response.jsonl; ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/203-method-b/successor-response.jsonl`
- **NC-05 missing measurement -> silently filled** - NOT_TRIGGERED
  - finding: pre-input R, route decision, ack write boundary and read-channel source remain in unknowns/obligations or are typed NOT_MEASURED in all 18 records.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.md (read-boundary summary)`
- **NC-06 failure -> silently dropped** - NOT_TRIGGERED
  - finding: REPL-CASE-02 watchdog expiry and empty acknowledgement register are recorded in FACTS_A, FACTS_B, METHOD_A, METHOD_B, BROKEN_A and BROKEN_B.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/frozen-successor-evidence/202-method-a/successor-response.jsonl`
- **NC-07 source SHA mismatch** - NOT_TRIGGERED
  - finding: Step00: every recorded SHA equals the packet pin and the exact-base final bytes across all six bundles; 0 mismatches.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json`
- **NC-08 cross-condition source leakage** - NOT_TRIGGERED
  - finding: Step00: 0 cross-condition reads; facts packets exclude method-family/, method-traces/ and trace-excerpts/; method packets exclude trace-excerpts/.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json`
- **NC-09 evaluator-sealed leakage** - NOT_TRIGGERED
  - finding: Step00: 0 evaluator-sealed reads; no successor read-manifest entry points at evaluator-sealed/ or criteria/.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/frozen-successor-evidence/evidence-freeze.json`
- **NC-10 wording repetition -> mistaken method-use evidence** - NOT_TRIGGERED
  - finding: The repeated candidate identifier was not accepted as method-use evidence on its own; each case was required to supply a case-bound rationale and a trace locator.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replication-analysis.md (WORDING-TEMPLATE-IMITATION)`
- **NC-11 repeated consistency -> causal claim** - NOT_TRIGGERED
  - finding: No replicate or report converts repeated A/B consistency into a causal claim; the fixed interpretation ceiling is applied everywhere.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replicated-method-use-verdict.json`
- **NC-12 3 cases/conversation -> treated as independent replicates** - NOT_TRIGGERED
  - finding: Reports count 6 conversation-level replicates, not 18 independent replicates; non-independence and absent random-seed control are stated explicitly.
  - locator: `ignition/reports/evaluations/ignition-206-replicated-method-use-independent-evaluation/replication-analysis.md (independence boundary)`