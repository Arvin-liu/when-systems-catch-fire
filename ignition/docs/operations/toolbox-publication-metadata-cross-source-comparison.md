# Cross-source publication metadata comparison

`research.compare_publication_metadata_snapshots` compares the title and publication year in one existing Crossref verifier result and one OpenAlex lookup result for the same bare DOI. It reads a bounded JSON envelope on stdin and emits field-level `AGREE`, `DISAGREE`, or `INSUFFICIENT` outcomes with the provider response digests. The displayed observations preserve each provider's title string; comparison normalization uses Unicode compatibility forms, case folding, and whitespace only.

The tool is a local post-processor. It makes no network request, reads or writes no files, and does not contact either provider. Crossref and OpenAlex results must have been collected separately under the caller's own permissions. The result objects are not authenticated by this comparator; their included response digests are preserved as supplied by the adapters.

The comparison normalizes Unicode compatibility forms, case, and whitespace in titles. It does not remove punctuation, infer title equivalence, adjudicate publication identity, validate source authenticity, review article contents, establish scientific truth, or interpret retraction signals. Agreement on title and year is only agreement on these two returned metadata fields. A missing field or unavailable provider remains `INSUFFICIENT`; a disagreement is reported without selecting a preferred source.

The supported adapter versions and JSON input/output contracts are defined in `ignition/schemas/operations/publication-metadata-comparison-input-r0.schema.json` and `ignition/schemas/operations/publication-metadata-comparison-output-r0.schema.json`. Example:

```json
{
  "schema_version": "ignition.publication-metadata-comparison-input-r0",
  "doi": "10.3982/ecta15732",
  "source_results": [
    {"tool_id": "research.verify_crossref_metadata", "result": {}},
    {"tool_id": "research.lookup_openalex_work_metadata", "result": {}}
  ]
}
```

The empty result objects above are placeholders; real invocations must pass complete outputs from both supported adapters. The tool is experimental, default-off, and only eligible when the caller already has both result objects and explicitly requests a cross-source title/year comparison. It complements the source-specific adapters and does not replace either one.
