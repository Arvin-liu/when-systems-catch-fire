# Historical Input Binding Migration Proof R1

Result: `18/18` frozen Task229 case records serialize into the R1 typed binding format with identical present-value key sets, identical value payloads, and identical missingness sets.

## Frozen inputs

- Historical input map: commit `4ee132e8d50e8805c466cb5d681aaa18c34c9f68`, path `ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/run/case-input-values-and-route-expectations.json`, SHA-256 `b2d44d56aa602e429a8f3ddded61e0b3524b16700a4d35232126a5e264ffa057`.
- Task228 policy base: `d82a52077df6d4e96e998ace3757f2fb343b4db5`; all six exact policy hashes are repeated in the machine proof and pinned in the R1 contract.
- The proof uses the map's frozen case-value objects directly. It does not reconstruct values from case prose, alter the map, evaluate target criteria, inspect evaluator material, or run a successor/evaluator.

## Result

The machine proof has one record for each of the six lineages and cases A/B/C. For every record, the canonical JSON digest of the frozen map values equals the digest of the R1 binding's present values, the input ID sets match exactly, and missing IDs equal the policy-required IDs absent from the frozen map.

Missingness is preserved for all three L04 records (`F02B_GRAVIMETRIC_REPLICATES_AGREE`) and all three L06 records (`F03B_ASSAY_REPLICATES_RECONCILE`). The other 12 records have no policy-required missing IDs. The report stores value digests and ID lists rather than copying the historical values into a second corpus.

`source_case_record_sha256` identifies a deterministic source-case envelope made from the exact frozen map entry. It is not a claim that the map entry is the original raw visible case file. The full source map hash remains the source binding for this migration proof.

## Reproduction

Extract the map bytes from the pinned source commit and the six policy files from the pinned Task228 base, verify their hashes against `typed-route-interface-contract-r1.json`, then run:

```text
python3 ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/tools/prove_historical_binding_migration.py --input-map INPUT_MAP.json --policy-root POLICY_DIRECTORY --output PROOF.json
```

The proof tool is read-only with respect to the frozen map and policies. It writes only the requested proof output. Its result is a serialization/conformance fact and does not establish live interface execution or transfer compatibility.
