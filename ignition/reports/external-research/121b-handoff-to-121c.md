# 121B → 121C Handoff

## Date: 2026-07-14
## From: 121B (GLM-5.2 night, high)
## To: 121C (GLM-5.2 max)

## What 121B Delivered

### Remote Checkpoints (verifiable by GPT)
- **WSCF branch**: `records/ignition-121-fulltext-resolver-and-120-repair-20260714`
  - HEAD: `47adc68a686582f866e96b8f6297b33d787ef777`
  - Contains all 121 + 121A + 121B artifacts
- **1111 branch**: `records/ignition-121b-result-20260714`
  - HEAD: (to be committed after this handoff)
  - Contains 121B result files in `agent-progress/` and `agent-results/`

### Fulltext Batch Status
- **84 sources** entered state machine
- **79 downloaded** (74 original + 5 retry success)
- **79 extracted** (74 original + 5 first-page-verified, full extraction pending)
- **30 anchor-verified** (with section headings and page anchors)
- **5 failed** with explicit reasons and retry conditions
- **2 landing-page fixes** (S120-024, S120-032 were HTML landing pages, now real PDFs)

### What 121C Must Do

1. **Full text extraction** for 7 sources (5 retry + 2 landing fix):
   - S120-013, S120-023, S120-033, S120-056, S120-080 (retry downloads)
   - S120-024, S120-032 (landing page fixes)
   - PDFs are in `/tmp/121b-oa-downloads/` — extract full text and generate section anchors

2. **Semantic review** for 79 sources:
   - Read full text of each downloaded source
   - Evaluate against GAP-015—020 candidates
   - Generate evidence cards with `claim_support_status`
   - **MUST NOT** pre-fill CONFIRMED — all start as PENDING_MAX_REVIEW

3. **Re-review 30 provisional reviews**:
   - 121A's 30 evidence cards were created by Kimi-K2.7-Code-HighSpeed, not GLM-5.2 max
   - All downgraded to PROVISIONAL_SEMANTIC_REVIEW
   - 121C must verify each against the actual full text
   - File: `121b-provisional-review-origin-audit.jsonl`

4. **Handle 5 failed sources**:
   - S120-006, S120-016: Retry with browser session for OpenReview
   - S120-051: No OA version exists — document and skip or request from authors
   - S120-052: Source is not a paper — reclassify or skip
   - S120-057: Tutorial document — check archive.org or contact author

5. **Final GAP-015—020 adjudication**:
   - 121B explicitly did NOT do this (red line)
   - 121C must read full texts and make adjudications
   - Use the review queue: `121b-121c-semantic-review-queue.jsonl`

## Files for 121C

### Input (from 121B)
- `data/external-research/121b-fulltext-batch/121b-121c-semantic-review-queue.jsonl` — 79 entries
- `data/external-research/121b-fulltext-batch/121b-provisional-review-origin-audit.jsonl` — 30 entries to re-review
- `data/external-research/121b-fulltext-batch/121b-fulltext-download-manifest.jsonl` — 79 downloads with SHA256
- `data/external-research/121b-fulltext-batch/121b-fulltext-anchor-manifest.jsonl` — 30 anchor-verified, 49 pending
- `data/external-research/121-fulltext-resolver/121-fulltext-evidence-cards.jsonl` — 30 provisional cards (Kimi origin)
- `data/external-research/121-fulltext-resolver/121-extracts.jsonl` — 74 extracted texts

### Output (121C must produce)
- Updated evidence cards with GLM-5.2 max review
- Final GAP-015—020 adjudications
- Full extraction for 7 pending sources
- Section anchors for 49 EXTRACTED (not yet ANCHOR_VERIFIED) sources

## Key Constraints for 121C

1. Model: GLM-5.2 max (not night, not Kimi)
2. Must read actual full text, not just abstracts
3. Must not pre-fill CONFIRMED
4. Must not modify frozen files (Ψ₀, 085, tables)
5. Must not merge/close any PR
6. Must not commit PDF cache to Git
7. Credential fragments must remain 0

## Retry Conditions for 5 Failed Sources

| Source | Retry Condition |
|--------|----------------|
| S120-006 | Browser session for OpenReview (forum=ptfu9Pr3dk) |
| S120-016 | Browser session for OpenReview (id=H1gfOiAqYm) |
| S120-051 | Purchase from ACM or request from authors (DOI: 10.1145/1375581.1375602) |
| S120-052 | Reclassify as non-paper or find alternative source |
| S120-057 | Check archive.org for MSR tutorial or contact Daan Leijen |
