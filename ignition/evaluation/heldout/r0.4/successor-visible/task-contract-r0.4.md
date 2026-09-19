# Successor Task Contract R0.4

Task ID: `IGNITION-20260919-188-R0.4`

This packet is prepared for a fresh held-out Successor conversation created by the Owner/GPT only after the Builder reaches `READY_FOR_R0_4_HELD_OUT_SUCCESSOR_TRIAL`. The Owner's exact task command must bind the repository, branch, base, remote, public noreply identity, allowed operations, and local authorization receipt. This packet alone grants no branch or remote-write authority.

## Work

1. Read only the cognitive files listed in `packet-manifest-r0.4.json`; record each read path and content SHA256 in the R0.4 ledger. Reading either held-out case source or its provenance is authorized cognitive evidence.
2. For each case, distinguish observations, interpretations, uncertainties, and additional evidence needed. Return one response for each case ID using `successor-output-r0.4.schema.json`.
3. Record every pre-closure operational execution and finite status observation in the R0.4 ledger. Execute the branch guard through `bootstrap-r0.4.sh`; observe only its finite result. An operational status must not contain case-specific information.
4. Stage trial output and the read ledger before running the bootstrap check so the guard can inspect a fully staged worktree. Record its finite status in the ledger and stage that row. Once the ledger is closed, do not edit it, run a further ledgered operation, commit, or push.
5. Invoke the manifest-listed R0.4 finalizer once with the ledger, exact packet manifest, and the receipt destination provided by the Owner outside the Successor-visible packet. Observe only the finite status printed by the tool. Do not open, read, copy, or interpret the receipt.
6. Return the output object, finalizer status, and factual limitations in the Successor conversation. Do not issue a verdict or claim inheritance.

## Stop conditions

Do not read operational source, the clone-local authorization receipt, the final validation receipt, evaluator-sealed paths, answer keys, or gold materials. If an unlisted source, operational case-specific exposure, evaluator artifact, or gold answer is observed, stop further cognitive reads and ordinary operational work; preserve the evidence and do not retry or self-adjudicate.

Do not invoke an Evaluator, Adjudicator, R1, MetaRSI, Model-RSI, weight training, canonical promotion, or a Ready/merge operation. The R0.4 trial is local-only and does not request a Git commit or push.

This contract contains no answer key, expected relation, expected continuation, score, or acceptance threshold. Any later Builder repair or Evaluator review requires a separate Owner-authorized task.
