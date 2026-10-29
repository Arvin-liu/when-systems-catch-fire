# Resume Plan: 121B and 121C

## Context
IGNITION-121A was a night-recovery task to salvage Kimi's partial 121 work, audit/repair format issues, and form a clean checkpoint. The task is now complete with status `121A_PARTIAL_SALVAGE_READY_WITH_EXPLICIT_MISSING_WORK`.

## What 121A Found
- Kimi completed 12 of 14 stages (COMPLETE), 1 NOT_STARTED, 1 NEEDS_REPAIR
- All 9 JSONL files pass validation (389 lines, 0 invalid)
- 1 JSON file has extension mismatch (.json but JSONL content)
- 30 evidence cards produced and validated
- 6 GAP readjudications completed
- 9 Function OS nodes readjudicated
- OpenAlex client verified and smoke-tested
- Program-as-Weights (arXiv:2607.02512) fetch+extraction verified
- No credential leaks
- Redlines intact (Ψ₀, 085 frozen v1, two tables unmodified)

## What 121A Did NOT Do
- Did not modify Kimi's original files (preservation principle)
- Did not create standalone 121-1111-quarantine-report.md
- Did not relativize local_cache_path fields in source registry
- Did not rename 121-function-os-node-readjudication.json to .jsonl
- Did not perform semantic review of fulltext content
- Did not create Draft PRs

## 121B: Fulltext Resolver Batch Pipeline & Repairs

### Starting Point
- Branch: `records/ignition-121-fulltext-resolver-and-120-repair-20260714`
- HEAD: `83aa4d9` (Kimi's last commit) + 121A artifacts commit

### Tasks
1. **Format repairs** (from 121A repair register):
   - Rename `121-function-os-node-readjudication.json` → `.jsonl`
   - Relativize `local_cache_path` fields in `121-fulltext-source-registry.jsonl`
   - Create standalone `121-1111-quarantine-report.md`
2. **Batch fulltext resolution**:
   - Run `fulltext_resolver.py` on all 84 sources from 120 registry
   - Re-fetch any failed sources with alternate providers
   - Update `121-fulltext-source-registry.jsonl` with complete results
3. **Failure analysis**:
   - For each of the 10 failed sources, document specific failure reason
   - Attempt alternate legal OA channels
   - Record final status for each source
4. **Validator update**:
   - Update `121-validator.py` to check all 121A repair items
   - Add path relativization check
   - Add extension consistency check
5. **Commit and PR**:
   - Commit to 121 branch
   - Create Draft PR to main (DO NOT MERGE)

### Success Criteria
- All 84 sources have resolution status (RESOLVED or FAILED_WITH_REASON)
- All JSONL files pass line-by-line validation
- No absolute local paths in any output file
- No credential leaks
- Redlines intact

## 121C: Deep Semantic Fulltext Review

### Starting Point
- 121B complete checkpoint
- 30+ evidence cards with fulltext fetched and extracted

### Tasks
1. **Deep semantic review** of each evidence card:
   - Read full extracted text
   - Identify source-specific claims relevant to Function OS nodes
   - Generate source-specific evidence statements (not generic summaries)
2. **GAP adjudication finalization**:
   - For each GAP-015 to GAP-020, review all supporting sources
   - Upgrade/downgrade adjudication based on fulltext evidence
   - Document specific passages supporting each adjudication
3. **Function OS node assessment**:
   - For each of 9 nodes, map specific evidence to node capabilities
   - Identify what's proven vs. what's hypothesized
   - Generate architecture readiness assessment
4. **Function paradigm cards**:
   - Update `121-function-paradigm-cards-fulltext-backed.jsonl`
   - Each card must cite specific passages from fulltext
5. **Reports**:
   - Final `121-legal-fulltext-resolver-report.md`
   - Final `121-function-paradigm-fulltext-review-report.md`
6. **Commit and PR**:
   - Commit to 121 branch
   - Update Draft PR (DO NOT MERGE)

### Success Criteria
- All 30 evidence cards have source-specific claims (not template text)
- All 6 GAP adjudications cite specific passages
- All 9 Function OS nodes have evidence mapping
- No `FULLTEXT_REVIEWED` status without actual semantic review
- Redlines intact

## Estimated Scope
- **121B**: ~2-3 hours of agent work (batch processing, repairs, validator)
- **121C**: ~4-6 hours of agent work (deep reading, semantic analysis, report writing)

## Dependencies
- 121B depends on 121A checkpoint (READY)
- 121C depends on 121B completion
- Neither depends on model fallback or switching
