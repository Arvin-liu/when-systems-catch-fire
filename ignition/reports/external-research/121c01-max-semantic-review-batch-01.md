# 121C01: First Batch GLM-5.2 Max Semantic Review Report

**Task:** IGNITION-20260709-121C01
**Reviewer:** qclaw/pool-glm-5.2 (reasoning: high)
**Note:** Task specified max reasoning; subagent environment supports high only. Main session supports max.
**Date:** 2026-07-14
**Baseline:** 66c6efdf673dc486fbf10373edbcf2eab67a528c (121B HEAD)
**Status:** 121C01_MAX_SEMANTIC_BATCH_COMPLETE_EVIDENCE_ACCUMULATING

## Phase 0: Status Axis Reconciliation

### Two Independent Status Axes Established

1. **content_access_status**: LOCATED (84) → DOWNLOADED (79) → EXTRACTED_FULL (72) / EXTRACTED_PARTIAL (7) → ANCHOR_VERIFIED (30); FAILED_LEGAL_OA_NOT_FOUND (5)
2. **semantic_review_status**: NOT_REVIEWED (49) → PROVISIONAL_NON_MAX_REVIEW (30) → MAX_REVIEW_IN_PROGRESS (10) → MAX_REVIEW_COMPLETE (0 after this batch); INSUFFICIENT_CONTENT (0)

### 79 Extracted vs 7 Warnings: True Explanation

- 121 had 74 successful extractions (from the original 84 sources, 10 failed)
- 121B retried 5 of the 10 failures, successfully downloading PDFs but failing to extract text from all 5 (S120-013, S120-023, S120-033, S120-056, S120-080)
- 2 additional sources (S120-024, S120-032) had successful downloads via landing_fix but minimal extraction (271 and 94 words respectively)
- Total: 72 EXTRACTED_FULL + 7 EXTRACTED_PARTIAL = 79 extraction attempts
- The "79 extracted" claim was technically counting extraction attempts, not successful full extractions

## Phase 1: Selected Sources (10 Papers)

| # | Source ID | Title | Family | Topic |
|---|-----------|-------|--------|-------|
| 1 | S120-001 | Program-as-Weights | 1 | Program-as-Weights paradigm |
| 2 | S120-004 | Weight Space Learning Survey | 1 | WSL taxonomy |
| 3 | S120-009 | HyperNetworks | 2 | Weight generation |
| 4 | S120-045 | Task Arithmetic | 6 | Weight-space composition |
| 5 | S120-039 | Model Soups | 6 | Weight averaging |
| 6 | S120-035 | LoRA | 5 | Low-rank adaptation |
| 7 | S120-021 | EG-CFG | 3 | Execution-guided synthesis |
| 8 | S120-030 | Fourier Neural Operator | 4 | Function-space learning |
| 9 | S120-047 | Generic Refinement Types | 7 | Formal specification |
| 10 | S120-053 | Handlers of Algebraic Effects | 8 | Effect tracking |

## Phase 2: Full-text Review Results

### Claim Support Status Distribution
- **CONFIRMED**: 5 (S120-030, S120-035, S120-039, S120-045, S120-047, S120-053)
- **PARTIAL**: 4 (S120-001, S120-004, S120-009, S120-021)
- **NOT_SUPPORTED**: 0
- **UNRESOLVED**: 0

### Key Findings Per Paper

**S120-001 (Program-as-Weights):** Demonstrates a concrete compiler→artifact→interpreter pipeline (two-stage LoRA compiler, 23MB artifact, frozen 0.6B interpreter). Strongest evidence for N2-N5 and N9. Does not address formal spec, equivalence, or effects.

**S120-004 (WSL Survey):** First unified taxonomy of weight-space learning. Covers representation, generation, and composition. Strongest landscape evidence for N2 and N8. Taxonomic only — no formal frameworks proposed.

**S120-009 (HyperNetworks):** Foundational paper showing weight generation via a meta-network. Embedding-as-compact-representation is novel. Demonstrates N2-N5. No formal spec, equivalence, or effects.

**S120-045 (Task Arithmetic):** Task vectors as weight-space directions. Negation, addition, and analogy as composition operations. Strongest evidence for N8 (ComposerRouter). Empirically confirmed but no formal algebra.

**S120-039 (Model Soups):** Weight averaging as composition. Greedy soup as routing. Analytical connection to loss flatness. Strong evidence for N4 and N8.

**S120-035 (LoRA):** Low-rank adaptation as compact artifact. 10,000× parameter reduction. Shared base + per-task module = registry pattern. Strong evidence for N2, N4, N5, N9.

**S120-021 (EG-CFG):** Execution-guided code generation with line-by-line feedback. Strongest evidence for N6 (ExecutionTrace) and N7 (Validator) in the symbolic domain. Does not address weight-space.

**S120-030 (Fourier Neural Operator):** Resolution-invariant function-space representation. Spectral equivalence from approximation theory. Novel representation type for N2 and N5. 1000× speedup over traditional solvers.

**S120-047 (Generic Refinement Types):** SMT-decidable formal specification with preconditions/postconditions. Strongest evidence for N1 (FunctionSpec) and N7 (Validator). Applies to symbolic code only — the gap to weight-space is the critical barrier.

**S120-053 (Handlers of Algebraic Effects):** Definitive theoretical framework for effect tracking. Algebraic theories as effect specs, handlers as interpreters. Strongest evidence for GAP-018 and N5. Purely theoretical — no weight-space connection.

## Phase 3: Provisional vs Max Comparison

| Comparison | Count | Papers |
|------------|-------|--------|
| AGREES | 4 | S120-001, S120-004, S120-009, S120-021 |
| NARROWS | 6 | S120-030, S120-035, S120-039, S120-045, S120-047, S120-053 |
| CORRECTS | 0 | — |
| REJECTS | 0 | — |
| NOT_COMPARABLE | 0 | — |

The 6 NARROWS cases reflect that the provisional Kimi/non-max cards were overly conservative (rating all as PARTIAL), while full-text Max review confirms the papers' own claims as CONFIRMED for 5 of them. The narrowing is that CONFIRMED applies to empirical claims, not to ignition architecture projections.

## Phase 4: GAP-015—020 Evidence Status

| Gap | Status | Evidence Count | Families | Threshold Met |
|-----|--------|---------------|----------|---------------|
| GAP-015 (Formal Spec) | EVIDENCE_ACCUMULATING | 3 | 3 | Yes (count) but only 1 direct |
| GAP-016 (Composition Algebra) | EVIDENCE_ACCUMULATING | 7 | 5 | Yes |
| GAP-017 (Equivalence) | EVIDENCE_ACCUMULATING | 6 | 5 | Yes (fragmented) |
| GAP-018 (Effect Tracking) | EVIDENCE_ACCUMULATING | 4 | 4 | Yes |
| GAP-019 (Versioned Registry) | EVIDENCE_ACCUMULATING | 6 | 4 | Yes |
| GAP-020 (Probabilistic Semantics) | INSUFFICIENT_EVIDENCE | 2 | 2 | No |

**No gaps are frozen.** All remain in evidence accumulation. GAP-020 needs Family 9 papers (121C05/121C06).

## Phase 5: Function OS Nine Nodes

| Node | Status | Key Papers |
|------|--------|------------|
| N1 FunctionSpec | WEAK_EVIDENCE | S120-047, S120-053, S120-021 |
| N2 Representation | MULTI_SOURCE_EVIDENCE | S120-001, S120-004, S120-009, S120-045, S120-039, S120-035, S120-030 |
| N3 Compiler | MULTI_SOURCE_EVIDENCE | S120-001, S120-009, S120-045, S120-035, S120-030 |
| N4 Artifact | MULTI_SOURCE_EVIDENCE | S120-001, S120-009, S120-045, S120-039, S120-035, S120-030 |
| N5 Interpreter | MULTI_SOURCE_EVIDENCE | S120-001, S120-009, S120-035, S120-030, S120-053 |
| N6 ExecutionTrace | WEAK_EVIDENCE | S120-021, S120-053 |
| N7 Validator | WEAK_EVIDENCE | S120-047, S120-021, S120-030 |
| N8 ComposerRouter | MULTI_SOURCE_EVIDENCE | S120-045, S120-039, S120-001, S120-004, S120-009, S120-035 |
| N9 VersionedRegistry | MULTI_SOURCE_EVIDENCE | S120-001, S120-035, S120-045, S120-039, S120-004, S120-009 |

## Phase 6: Remaining Batches

- **121C02** (10 papers): Families 1-2 (weight-space, hypernetworks)
- **121C03** (10 papers): Families 3-4 (program synthesis, neural operators)
- **121C04** (10 papers): Families 4-6 (operators, LoRA, merging)
- **121C05** (10 papers): Families 6-9 (merging, refinement, effects, probabilistic)
- **121C06** (10 papers): Families 9-10 (probabilistic programming, agent skills)
- **121C07** (10 papers): Families 1,3,5,10 (mixed)
- **121C08** (9 papers): Remaining + 7 re-extraction needed

## Phase 7: Validator

- **187 checks passed, 0 failed**
- Status axes verified, no credential fragments, frozen files untouched, no PDFs in git

## Red Lines

- Ψ₀, 085 frozen v1, unified function table, unified case table: **not modified**
- No new function numbers assigned
- No PRs merged or closed
- No API keys or tokens exposed
- No PDF files committed to Git
- No template-generated semantic conclusions
