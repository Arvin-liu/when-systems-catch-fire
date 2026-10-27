# Bounded JSONL record selector R0

`knowledge.select_jsonl_records` reads one caller-selected regular JSONL file under `ignition/`, applies one exact JSON Pointer plus JSON scalar equality condition, and returns matching record text with its line number, byte offsets, record digest, and whole-source digest. Strings compare exactly; JSON numbers compare by numeric value, so `1` matches `1.0`; booleans remain distinct from numbers; `null` matches only `null`.

Origin: a narrow prototype for the original-data-preserving targeted-retrieval hypothesis in [Workbench PR #86, TR26-06](https://github.com/Arvin-liu/ignition-architecture-workbench/pull/86). It adds no cache and does not adopt claims about token savings or external-project performance.

The request names the file and sets source, returned-byte, and match-count limits. The scan has a fixed 1 MiB per-record parse bound and a 32 MB maximum source bound. It rejects traversal, symlink components, non-regular files, duplicate JSON keys, malformed or blank rows, non-object rows, invalid pointer escapes, and any request whose full matching output would exceed its limits. It never writes or caches files and makes no network request.

This is an explicitly invoked optional tool and remains off in routing by default. It can reduce the amount of a structured local source returned for inspection; it reports bytes, not tokens, elapsed time, cost, semantic relevance, or retrieval completeness. Returned records are not redacted. Use only on data the caller and output audience are authorized to read.

Example invocation:

```sh
python3 -B ignition/tools/toolbox_jsonl_selector.py --workspace-root "$PWD" --stdin
```

Fallback: scan the named JSONL file with a short standard-library Python script, parse each row, apply the same JSON Pointer and typed equality, and inspect the exact source line. The selector's C1 evidence records parity with that fallback on one real local lookup; it does not establish replacement value, net benefit, token savings, or default-routing authority.
