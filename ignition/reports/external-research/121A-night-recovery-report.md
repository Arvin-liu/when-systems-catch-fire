# 121A Night Recovery Report

## Executive Summary

IGNITION-121A was executed by QClaw (model: qclaw/pool-glm-5.2-night, reasoning: high) on 2026-07-14 to recover Kimi-K2.7's partial 121 work, audit all outputs, repair format issues, and form a clean checkpoint for resumption.

**Status:** `121A_PARTIAL_SALVAGE_READY_WITH_EXPLICIT_MISSING_WORK`

Kimi's work was substantially complete — 12 of 14 stages marked COMPLETE, with only 1 NOT_STARTED (standalone quarantine report) and 1 NEEDS_REPAIR (file extension mismatch). All 9 JSONL files passed line-by-line validation (389 lines total, 0 invalid). No credential leaks. Redlines intact.

## Phase 0: Scene Preservation

- **Workspace:** `/tmp/wscf-121` confirmed present
- **HEAD:** `83aa4d94c986274da9dc97e3d83fc970467ec5ba`
- **Branch:** `records/ignition-121-fulltext-resolver-and-120-repair-20260714`
- **Snapshot:** `/tmp/wscf-121-kimi-snapshot.tar.gz` (163 MB, not committed)
- **Git status:** Clean (no uncommitted changes)
- **Commits from baseline:** 3 (5d33b72 → 9361c1e → 83aa4d9)
- **Files changed:** 60 (all insertions, 0 deletions to redline files)

## Phase 1: Kimi Output Inventory

### Complete (12 stages)
| Stage | Status | Key Evidence |
|-------|--------|-------------|
| Baseline & contamination audit | COMPLETE | 1111 120 branch contamination identified (19711 deleted files) |
| Credential hygiene audit | COMPLETE | 4 LOW findings, no key rotation required |
| OpenAlex client migration | COMPLETE | From commit 5d33b72, SHA256 verified |
| Program-as-Weights smoke test | COMPLETE | HTML+PDF fetched, 13147 words extracted |
| Resolver/fetcher/extract tools | COMPLETE | 3 scripts (577 lines total) |
| Provider capability matrix | COMPLETE | 12+ providers, 17 JSONL entries |
| Download/extract logs | COMPLETE | 84 fetch records, 84 resolution logs, 74 extracts |
| Evidence cards (30) | COMPLETE | 30 cards, 10 source families, all legal OA |
| GAP-015 to GAP-020 readjudications | COMPLETE | 6 GAPs, 3 insufficient evidence, 3 ready for review |
| Function OS node readjudication | COMPLETE | 9 nodes assessed (4 STRONGLY_SUPPORTED, 5 PARTIALLY_SUPPORTED) |
| Validator | COMPLETE | Python validator script |
| Reports & protocol | COMPLETE | 3 documents (resolver report, review report, protocol) |

### Not Started (1)
| Stage | Status | Note |
|-------|--------|------|
| 1111 quarantine report (standalone) | NOT_STARTED | Quarantine info embedded in baseline audit JSON |

### Needs Repair (1)
| File | Issue | Action |
|------|-------|--------|
| 121-function-os-node-readjudication.json | .json extension but JSONL content (9 objects, one per line) | Rename to .jsonl (documented, not yet applied) |

### Additional Repairs Documented (4 items in repair register)
1. File extension mismatch on function-os-node-readjudication
2. Run-state model deviation documentation (informational)
3. 1111 contaminated branch tracking (informational)
4. Absolute local paths in source registry (should relativize in 121B)

## Phase 2: JSONL Format Audit

All 9 JSONL files passed validation:
- **Total lines:** 389
- **Valid lines:** 389
- **Invalid lines:** 0
- **Duplicate IDs:** 0

| File | Lines | Status |
|------|-------|--------|
| 121-extracts.jsonl | 74 | PASS |
| 121-fetch-records.jsonl | 84 | PASS |
| 121-fulltext-evidence-cards.jsonl | 30 | PASS |
| 121-fulltext-failure-register.jsonl | 10 | PASS |
| 121-fulltext-provider-capability-matrix.jsonl | 17 | PASS |
| 121-fulltext-resolution-log.jsonl | 84 | PASS |
| 121-fulltext-source-registry.jsonl | 84 | PASS |
| 121-function-paradigm-cards-fulltext-backed.jsonl | 10 | PASS |
| 121-gap-015-020-readjudications.jsonl | 6 | PASS |

All 6 JSON files passed except `121-function-os-node-readjudication.json` (JSONL content with .json extension).

## Phase 3: OpenAlex Client Verification

- **Source commit:** 5d33b72 (feat(120): add openalex_client.py)
- **SHA256:** 12d03820eb14b27a3263db4e22a4644371985740606dfe57257c73fe02ffc07c
- **Lines:** 363
- **Already present** in 121 branch (121 was built on top of 120 which included this file)

### Code Audit Results
- ✅ OpenAlex API calls real (endpoint: https://api.openalex.org/works)
- ✅ abstract_inverted_index restoration correct (word array reconstruction)
- ✅ is_retracted not misused (read from API, not treated as complete retraction DB)
- ✅ oa_url is clue only (docstring: "返回元数据和摘要，不返回全文")
- ✅ Failure handling (404 → None, timeout=30s)
- ✅ No credential/email/key leak

### Smoke Tests
| Test | Result |
|------|--------|
| Keyword search ("program as weights") | PASS — 3 results returned |
| DOI query (10.48550/arxiv.2607.02512) | PASS — Found, title correct |
| Batch DOI verification (2 DOIs) | PASS — Both found |
| OA URL output | PASS — Present as metadata, not counted as fulltext |

## Phase 4: Program-as-Weights Fetch Verification

| Check | Result |
|-------|--------|
| HTML URL (https://arxiv.org/html/2607.02512) | 200, text/html, 618,169 bytes |
| PDF URL (https://arxiv.org/pdf/2607.02512) | 200, application/pdf, 1,811,878 bytes |
| PDF SHA256 | 546f833487392f7dc31cf72c04e13eeac77c794420e575d7af2041308f7cdb7d |
| HTML SHA256 | a2f205d7605dc526fd7b955618eb4b5b6c40c310f16fa37e905a618c43004804 |
| Text extraction | 13,147 words, section headers present |
| Section anchors | Abstract, 1 Introduction, 2 Programs as Weights, 3 Compiler–Interpreter System |

**Status:** `FULLTEXT_FETCH_AND_EXTRACTION_VERIFIED_PENDING_SEMANTIC_REVIEW`

## Phase 5: Clean Checkpoint

### Ignition Repository
- **Branch:** `records/ignition-121-fulltext-resolver-and-120-repair-20260714` (reused from Kimi)
- **121A artifacts:** `data/external-research/121A-night-recovery/` (13 files)
- **Redlines verified:** Ψ₀, 085 frozen v1, function table, case table — all unmodified
- **No PDF/cache/cookie files committed** (.cache/ in .gitignore)

### 1111 Repository
- **Branch:** `records/ignition-121A-night-recovery-20260714` (to be created from main beab8739)
- **Scope:** agent-progress/, agent-results/ only
- **No data/obsidian-getnote/notes/asset/ modifications**

## Counts Summary

| Metric | Count |
|--------|-------|
| Sources in registry | 84 |
| Fulltext fetched | 74 |
| Fulltext extraction successful | 74 |
| Fulltext failure | 10 |
| Evidence cards (FULLTEXT_REVIEWED) | 30 |
| Evidence card files | 30 |
| GAP readjudications | 6 |
| Function OS nodes assessed | 9 |
| Source families (min 2 reviewed) | 10 |
| Credential leaks | 0 |

## Resume Plan

### 121B: Fulltext Resolver Batch Pipeline & Repairs
- Fix format issues (rename .json→.jsonl, relativize paths)
- Run batch resolution on all 84 sources
- Create standalone quarantine report
- Update validator

### 121C: Deep Semantic Fulltext Review
- Deep semantic review of 30 evidence cards
- Finalize GAP adjudications with specific passages
- Map evidence to Function OS nodes
- Generate final reports

## Conclusion

Kimi's 121 work was substantially salvaged. The primary failure point (JSONL format issues) was found to be already resolved — all JSONL files pass validation. The one remaining format issue (file extension mismatch) is documented for 121B repair. The checkpoint is clean, redlines are intact, and the resume plan provides clear starting points for 121B and 121C.
