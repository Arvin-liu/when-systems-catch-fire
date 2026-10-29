# Producer Consumer Semantic Preflight R0

`maintenance.preflight_producer_consumer_semantics` checks a bounded producer text against constant `re.search` patterns in one caller-supplied Python consumer function. It parses the source with Python `ast`, never imports or executes it, then applies the extracted patterns to the producer text. The CLI reads one JSON object from standard input and writes one deterministic JSON result.

Run it with:

```sh
python3 -B ignition/tools/toolbox_producer_consumer_semantic_preflight.py --stdin < input.json
```

The input is defined by `ignition/schemas/operations/toolbox-producer-consumer-semantic-input-r0.schema.json`. It carries the source excerpt, a function name, the expected SHA-256 of that excerpt, producer text, and its expected SHA-256. A hash match only compares caller-provided bytes to caller-provided digests; it does not authenticate a Git revision or source origin.

The analyzer accepts only a narrow contract: direct `re.search` calls with constant patterns and a direct text variable, with all result variables jointly guarded by a simple fail-closed `if not ... or not ...: raise`. It supports a bounded regex subset with character-class or digit repeats, literal delimiters, and simple captures. Dynamic patterns, transformations, unrecognized control flow, unsupported regex features, or ambiguous parser structure return `NOT_EVALUABLE`.

Each extracted check reports `PRESENT`, `ABSENT`, `CASE_VARIANT`, `MALFORMED_OR_REORDERED`, `AMBIGUOUS`, or `CONTRADICTORY`. Assignment-like field labels found immediately before capture groups are listed with occurrence counts and value hashes; raw captured values are not returned. Duplicate fields are not silently accepted. A mismatch means only that the static pattern contract did not match the supplied text.

This is useful before freezing a handoff or other serialized producer output when the consumer contains simple, constant regex checks. It does not prove runtime acceptance, full parser behavior, field units, version semantics, data-flow through arbitrary transformations, source provenance, execution, scientific meaning, or equivalence of producer and consumer semantics. Never use it to edit or reinterpret an old frozen artifact, restart an experiment, or infer permission to execute the consumer. Use a reviewed runtime test when actual consumer acceptance is required and separately authorized.

### Evidence and comparison

The first task-derived check uses the frozen Workbench #73 parser and A-handoff bytes only as supplied input. It is a repository-local static mismatch observation, not a rerun of the experiment or a scientific result. The referenced Workbench repository has no root `LICENSE` at the inspected ref; no Workbench implementation code is vendored here. Existing manifest, Agent-plan, and receipt-byte validators use different input contracts. Comparative quality and cost remain `COMPARISON_UNKNOWN`; the tool is default-off and does not replace or retire them.

The input size is capped at 262144 bytes, consumer source at 131072 UTF-8 bytes, producer text at 65536 UTF-8 bytes, patterns at 512 characters, regex checks at 16, and capture groups at 32. It reads only the local input schema and caller-supplied stdin. It has no network, secret, billing, write, import, dispatch, or external-action capability.
