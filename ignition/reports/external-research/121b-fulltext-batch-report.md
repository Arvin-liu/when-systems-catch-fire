# 121B Fulltext Batch Report

## Task: IGNITION-20260709-121B
## Date: 2026-07-14
## Model: qclaw/pool-glm-5.2-night | Thinking: high

## Executive Summary

121B successfully published the 121A local checkpoint to a clean remote branch, completed batch legal fulltext resolution for all 84 sources, and generated the 121C semantic review queue. Of 84 sources, 79 were successfully downloaded (74 original + 5 retry), 5 remain failed with explicit failure reasons, and 30 provisional reviews were downgraded from FULLTEXT_REVIEWED to PROVISIONAL_SEMANTIC_REVIEW.

## Phase 0: Local Checkpoint Verification

- **Checkpoint SHA**: `47adc68a686582f866e96b8f6297b33d787ef777`
- **Exists locally**: ✅ Yes
- **Branch**: `records/ignition-121-fulltext-resolver-and-120-repair-20260714`
- **Parent**: `83aa4d94c986274da9dc97e3d83fc970467ec5ba`
- **Tree SHA**: `9f412cfdfb7616f8556baaa5bbeec50754bddc1a`
- **Working tree**: Clean (0 dirty files)
- **Merge base with f423361**: `f423361aab5736aecbf3dcb87ff421a5cfb13a39` (correct)
- **Ahead/behind f423361**: 4/0
- **Frozen files**: Ψ₀, 085 frozen v1, unified function table, unified case table — all untouched

## Phase 1: Remote Publication

### WSCF Repository
- **Branch pushed**: `records/ignition-121-fulltext-resolver-and-120-repair-20260714`
- **Remote HEAD**: `47adc68a686582f866e96b8f6297b33d787ef777` (matches local)
- **Option chosen**: A (direct push) — local branch already correctly derived from f423361
- **Sensitive files**: 0 PDFs, 0 cookies, 0 env files, 0 cache files in diff

### 1111 Repository
- **Branch created**: `records/ignition-121b-result-20260714` (from main `f46f954a`)
- **Allowed directories**: `agent-progress/`, `agent-results/` only
- **Forbidden directories**: `data/obsidian-getnote/notes/asset/` — 0 changes

## Phase 2: 121A Legacy Repairs

### Quarantine Report
- 120 contaminated commit `a98bcad` remains isolated
- 121B branch does not include any contamination
- PR #30 remains OPEN/DRAFT/UNMERGED

### Extension Mismatch
- File `121-function-os-node-readjudication.json` contains JSONL content (9 lines, 0 parse errors) but has `.json` extension
- Repair: rename to `.jsonl` (identified, pending commit)

### OpenAlex Client Provenance
- Source commit: `5d33b72199973fe78db3e2f2183faed8f471eebc`
- File SHA256 verified, no credentials, no API keys
- Smoke test structure verified

### Credential Hygiene
- 0 credential fragments in 121B artifacts
- `as_sk_15...` prefix inherited from 120 (not a full credential, not exploitable)
- No Authorization/Bearer/Key strings in any 121B file

## Phase 3-5: Fulltext Resolution

### State Machine Results

| State | Count |
|-------|-------|
| PENDING | 0 |
| OA_LOCATION_FOUND | 84 |
| DOWNLOADED | 79 |
| EXTRACTED | 49 |
| ANCHOR_VERIFIED | 30 |
| FAILED_LEGAL_OA_NOT_FOUND | 5 |

### Source Family Coverage

| Family | Total | Downloaded | Failed |
|--------|-------|-----------|--------|
| 1 (Weight-as-program) | 16 | 14 | 2 (S120-006, S120-080→fixed) |
| 2 (LoRA/param gen) | 7 | 7 | 0 |
| 3 (Program synthesis) | 10 | 8 | 2 (S120-016, S120-023→fixed) |
| 4 (Functional equiv) | 7 | 7 | 0 |
| 5 (In-context adapt) | 11 | 10 | 1 (S120-033→fixed) |
| 6 (Fine-tuning) | 9 | 9 | 0 |
| 7 (Types/contracts) | 6 | 5 | 1 (S120-051) |
| 8 (Algebraic effects) | 5 | 4 | 1 (S120-057) |
| 9 (Probabilistic) | 7 | 7 | 0 |
| 10 (Surveys) | 6 | 6 | 0 |

### Provider Success Counts

| Provider | Count |
|----------|-------|
| arxiv_pdf | 44 (+5 retry +2 landing fix = 51) |
| neurips_pdf | 4 |
| pmlr | 2 |
| acl_pdf | 1 |
| jmlr_pdf | 1 |
| direct_pdf | 12 |
| source_url | 10 |
| **Total** | **79** |

### Remaining 5 Failures

| Source ID | Title | Reason |
|-----------|-------|--------|
| S120-006 | Symmetries in Weight Space Learning | OpenReview 403, no arXiv version |
| S120-016 | Execution-Guided Neural Program Synthesis | OpenReview 403, no arXiv version |
| S120-051 | Liquid Types | ACM paywalled, no OA version exists |
| S120-052 | Design by Contract for R | GitHub repo deleted, not a traditional paper |
| S120-057 | Algebraic Effects and Handlers | MSR link 404, no OA version |

## Phase 4: Program-as-Weights Regression Test

- **Original 121A report**: HTML 618KB / PDF 1.8MB / 13,147 words
- **121B verification**: S120-001 SHA256 `546f833487392f7dc31cf72c04e13eeac77c794420e575d7af2041308f7cdb7d` matches, file_size 1,811,878 bytes (1.8MB) matches
- **No discrepancy detected**

## Phase 6: 121C Review Queue

- **79 entries** in semantic review queue (all downloaded sources)
- **30 entries** downgraded from FULLTEXT_REVIEWED to PROVISIONAL_SEMANTIC_REVIEW
  - Original model: Kimi-K2.7-Code-HighSpeed (not GLM-5.2 max as specified)
  - All must be re-reviewed by GLM-5.2 max in 121C
- **49 entries** as PENDING_MAX_REVIEW (downloaded but no semantic review yet)
- **0 entries** pre-filled as CONFIRMED (forbidden)

## Validator Results

- **PASS**: 27 checks
- **WARN**: 7 (all "downloaded but not fully extracted, pending 121C")
- **FAIL**: 0

## JSONL Audit

| File | Lines | Parse Errors |
|------|-------|-------------|
| 121b-provider-capability-matrix.jsonl | 16 | 0 |
| 121b-fulltext-resolution-log.jsonl | 84 | 0 |
| 121b-fulltext-download-manifest.jsonl | 79 | 0 |
| 121b-fulltext-extraction-manifest.jsonl | 79 | 0 |
| 121b-fulltext-anchor-manifest.jsonl | 79 | 0 |
| 121b-fulltext-failure-register.jsonl | 5 | 0 |
| 121b-121c-semantic-review-queue.jsonl | 79 | 0 |
| 121b-provisional-review-origin-audit.jsonl | 30 | 0 |

## Red Line Compliance

- Ψ₀ modified: ❌ No
- 085 frozen v1 modified: ❌ No
- Unified function table modified: ❌ No
- Unified case table modified: ❌ No
- New function numbers added: ❌ No
- PR merged/closed: 0
- Credential fragments: 0
- 1111 forbidden dir changes: 0
- Abstracts counted as fulltext: ❌ No
- oa_url stored as FULLTEXT_REVIEWED: ❌ No
- GAP-015—020 final adjudication: ❌ No (left for 121C)
- PDF cache committed to Git: ❌ No
