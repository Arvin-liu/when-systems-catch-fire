# Handoff Advisory Selector

This optional read-only tool creates a review-only suggestion for omitting an advisory message when its exact text, ordered source references, and task scope already appear in a caller-declared receiver context. It never edits a bundle, sends a message, or decides whether a message is semantically unnecessary.

Run the bounded example from the repository root:

```sh
python3 -B ignition/tools/toolbox_handoff_advisory_selector.py --stdin < ignition/tests/fixtures/toolbox-handoff-advisory-selection/valid-input-r0.json
```

The tool can suggest omitting only a unique, caller-marked optional `ADVISORY` whose exact digest is present in the caller-supplied receiver-context digest list. The digest binds exact text, ordered source references, task scope, and caller-declared receiver-state revision. `ACTION`, `AUTHORITY`, `OUTCOME`, `WITNESS`, `SOURCE`, `UNKNOWN`, and caller-marked `must_forward` messages are always retained. Repeated copies in the pending bundle are retained as well.

## Scope and limits

- Hashes the decoded UTF-8 message text, its ordered source references, caller-supplied task scope, and receiver-state revision. No whitespace or Unicode normalization is applied.
- Treats `receiver_state_ref`, message kind, `must_forward`, and context digests as caller declarations. It does not authenticate the receiver or establish that the declared context exists or is current.
- Exact byte identity is not semantic equivalence. The tool does not compress text, select source documents, refresh shared state, escalate a receiver, validate permissions, or judge task relevance.
- The output contains IDs, hashes, a narrow content-byte count, and suggested omissions; it does not return message text. The caller must review and apply any suggestion independently.
- Reads one bounded stdin JSON object and writes one JSON result to stdout. It makes no network requests and writes no files.

The candidate is `EXPERIMENTAL_AVAILABLE`, default-off, and `READ_ONLY_RUN`. Its local synthetic smoke and tests establish only deterministic contract behavior. Real receiver utility, outcome quality, context authenticity, token savings, latency, and costs remain unknown.
