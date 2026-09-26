# Agent E — Condition-neutral preregistration and statistics proposal

## Review setup

Score each output against the same frozen, condition-neutral rubric. Before outputs are generated or shown, adjudicate and seal a case key for every lineage and case: its categorical disposition, required response elements, acceptable bounded variations, preserved scope, forbidden overreactions, and critical errors. Use the brief’s three dispositions: **A — bounded change required**, **B — preserve prior scope**, and **C — edge unresolved**. If the evidence cannot support a determinate key, flag that case as a design defect before output review; do not repair the key after seeing outputs.

Have two reviewers independently score outputs. Remove condition and model labels, randomize presentation order, and provide both reviewers the same source evidence, sealed lineage target, case key, output, and rubric. Condition labels stay hidden through scoring and adjudication.

## Scoring

For each lineage-condition, record `REVISION_VALIDITY_SUCCESS` as binary. It is 1 only when all five requirements hold: source evidence licenses the bounded change; the operation matches the sealed target; preserved scope is retained; the lineage is represented; and there is no forbidden overreaction or critical error. Otherwise it is 0. Record criterion-level failure codes to make the binary result auditable.

For each case-condition, record `TRANSFER_TARGET_SUCCESS` as binary against the sealed case key, regardless of condition. On A, separately code the target response, overreaction (`O_A`), and critical error (`F_A`), preserving all component codes. Compute the lineage-condition chain mechanically from the recorded fields:

`R AND (E_A AND NOT O_A AND NOT F_A) AND E_B AND E_C`

Do not let success on one case compensate for failure on another.

## Disagreement and records

Keep both initial reviewer records. A disagreement on any component goes to a third reviewer, who sees the frozen evidence, key, rubric, output, and anonymized initial codes, but not condition labels. The third reviewer assigns the final code under the rubric; retain the initial and adjudicated codes and identify which fields required adjudication. Do not resolve disagreements by changing the key or rubric after output review.

Record categorical codes and, where useful, a short output span or evidence locator supporting a code. Do not request or collect hidden chain-of-thought. If a frozen case is found to be unscorable due to an evidence or key defect, report that as a protocol defect with its denominator impact; do not silently omit it or convert it into a success.

## Descriptive reporting

For each condition, report raw counts and denominators: revision success out of 6 lineages; transfer success out of 18 cases, also split by A, B, and C (6 each); and chain success out of 6 lineages. Show paired lineage-level outcomes across conditions, criterion-level failure counts, overreaction and critical-error counts, and initial reviewer agreement and adjudication counts. Keep invalid or unscorable units visible with reasons and fixed denominator rules. Treat these as descriptive summaries for this small synthetic set; do not infer population effects or claim statistical significance.

## Claim boundary

The result supports, at most, a bounded R0 synthetic-only statement about applying a presealed rubric to these six lineages and eighteen held-out case instances. It does not establish real-world transfer, general capability, safety, causal effects, or performance outside this synthetic set.
