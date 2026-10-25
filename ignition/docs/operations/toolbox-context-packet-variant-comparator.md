# ContextPacket Variant Comparator

Tool ID: maintenance.compare_context_packet_variants

## Purpose

Compare two outputs from knowledge.assemble_context_packet for the same
caller-declared question, current reference, and ordered required obligations.
The comparator reports excerpt text UTF-8 bytes, source identity counts, and
caller-declared structural coverage changes. It does not return either packet's
excerpt text.

The tool supports a narrow part of the Workbench GitHub Trending blueprint
TR26-06: compare how much selected context text two variants expose while
keeping their declared source and obligation inputs visible. The source is the
noncanonical, unexecuted queue at
Arvin-liu/ignition-architecture-workbench commit
1c8542328f482f39986a0a79ce1e0514aa14b398,
sources/GITHUB-TRENDING-2026-10-24-WEEK-MONTH-IGNITION-DELTA-R0.md.
No third-party code is copied or executed.

## Limits

The comparison authenticates neither packet nor source. A matching current
reference and operation ID are caller declarations, not resolved repository
state. Structural obligation presence comes from packet fields and is not a
semantic coverage or relevance judgment.

The tool does not evaluate task outcome, important-error recall, evidence
quality, source completeness, retrieval quality, provider token counts, or
billing. Its exact text-byte count is a local representation measure, not a
provider cost estimate. Sufficiency always remains NOT_EVALUATED.

## Runtime boundary

- Input: one JSON object containing a baseline and candidate ContextPacket R0.
- Maximum input: 256,000 bytes.
- Execution: local stdin only.
- Reads: no files.
- Writes, network, credentials, billing, and external actions: none.
- Output: matched task binding, excerpt line/character/UTF-8-byte counts,
  caller-reported source-read totals, and declared obligation deltas.
- The output does not contain excerpt content and sets execution_authorized
  to false.

Run with:

    python3 -B ignition/tools/toolbox_context_packet_variant_comparator.py --stdin

The two packets must declare the same operation_or_question_id, current_ref,
and ordered required obligations. The comparison fails closed when these
bindings differ, when a packet claims semantic coverage or sufficiency, or when
a packet enables execution.
