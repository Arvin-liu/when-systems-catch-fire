# R0 Complexity, Retirement, and Next Gate

**Status:** design preparation only; all eight Successor tasks remain unlaunched.

## Design complexity and claim ceiling

The planned matrix has four input conditions and two independent conversations per condition: eight future conversations and 24 nested case records. Each conversation sees the same three synthetic cases in one of two predeclared orders. Within each order block, all four packets use the same case order. The common neutral prompt, output schema, read contract, and freeze contract are byte-identical across packets.

The packet contents intentionally differ in amount and structure: one has no reference item, one has a local procedure, one has a source-bound complete trace and history, and one has an incomplete trace fragment and source. That content can reveal its nature to a careful reader; opaque packet IDs hide direct assignment labels but do not make the inputs indistinguishable. The condition map stays in the evaluator-only path and is released only after two independent score sheets are locked. Repository path separation is protocol-only, not cryptographic secrecy from repository readers.

The independent unit is the conversation. The three case outputs within one conversation are nested. With two conversations per condition, this R0 supports descriptive comparisons only. It cannot establish causal method inheritance, general cognitive inheritance, R1 authorization, cross-model transfer, or canonical promotion. Runtime identity remains bounded by the evidence actually recorded; command assignment alone does not become independent verification.

## Trial stop and retirement rules

Retire this packet-set version without mid-run repair if any of these occur:

- Any common prompt, schema, packet manifest, case, provenance, or artifact hash differs from the frozen packet manifest.
- A Successor reads outside its single packet and read manifest, receives evaluator criteria/mapping, or shares conversation history with another task.
- Any tracked deletion, tracked modification, or staging/index change occurs: mark `TRIAL_WORKTREE_MUTATION_INVALID` immediately. If it occurs in the shared worktree, stop the entire run family because later conversations may be contaminated.
- Any untracked file is created outside the predeclared `trial-output/<opaque-packet-id>/` directory: mark `TRIAL_WORKTREE_MUTATION_INVALID` and stop the affected run family.
- A packet, prompt, output record, runtime receipt, or provenance record is missing, mismatched, or altered after the freeze.
- A conversation is not fresh/independent, the model/runtime assignment differs across the eight tasks, or the task order was changed after launch began.

Do not replace an invalid output, swap a packet, tune a prompt, revise criteria, or rerun a condition inside this R0. Any repair requires a new numbered command and a new frozen design.

If all runs are protocol-valid but outcomes are mixed, weak, or ambiguous, report them as such. Do not retire an inconvenient result or extend R0 after inspecting outcomes. A later experiment must name one changed factor in advance and retain the old result as history.

## Required next gate

1. Owner authorizes a separate future task and records the exact prepared PR head as the launch commit.
2. Before launch, hash-check all eight packets and the shared contracts, select one runtime configuration for all eight conversations, freeze a randomized task execution order, and record the worktree baseline.
3. Run one fresh isolated Successor conversation per task. Save three schema-valid JSONL records per conversation and its runtime receipt. Any freeze-contract breach triggers the retirement rule above.
4. Lock all eight outputs, hashes, receipts, and protocol status before evaluators receive them. Two evaluators independently score the opaque packets and outputs; retain both score sheets and reconcile disagreements without erasing them.
5. Release the condition map only after both score sheets are locked. Report the eight conversation-level summaries and nested case-level records descriptively.
6. Return the bounded report for new Owner/GPT adjudication. R1, cross-model transfer, canonical promotion, MetaRSI, Model-RSI, and training each require separate explicit authorization; this preparation grants none of them.

The final state of this command is readiness to authorize the later Successor trials, not authorization to start them.
