# Function-Paradigm Full-Text Review Report — IGNITION-121

## Scope
This report documents the 121 full-text review of 30 core papers selected from the 84 sources in IGNITION-120. The review focused on identifying source-specific support and non-support for ignition's Function OS model and the six GAPs GAP-015 to GAP-020.

## Model Note
This review was executed with **model=qclaw/pool-kimi-k2.7-code-highspeed, thinking=adaptive**. The task file originally specified GLM-5.2 + max; this deviation is recorded. **Semantic裁决 of paper support and the GAP-015 to GAP-020 readjudications are flagged for subsequent GLM-5.2 Max review** where the highest reasoning depth is required.

## Reviewed Sources (30)

| Family | Sources |
|--------|---------|
| 1: Program-as-Weights / Weight-space | S120-001, S120-002, S120-004, S120-007 |
| 2: Hypernetworks | S120-009, S120-010, S120-011 |
| 3: Program Synthesis | S120-017, S120-018, S120-020, S120-021, S120-022 |
| 4: Neural Operators | S120-027, S120-030 |
| 5: LoRA / Adapters / MAML | S120-031, S120-035, S120-036, S120-075 |
| 6: Weight-space Averaging / Merging | S120-039, S120-045, S120-046 |
| 7: Refinement Types / Verification | S120-047, S120-050 |
| 8: Algebraic Effects | S120-053, S120-055 |
| 9: Probabilistic Programming | S120-058, S120-059, S120-064 |
| 10: Skill Libraries / Agents | S120-065, S120-070 |

## Evidence Standard
Each source was fetched as a full PDF or HTML, SHA256-hashed, page-counted, and had text extracted. Evidence cards record:
- access channel, URL, timestamp, version, license
- file SHA256 and local cache path
- page count and section/anchor list
- what the paper supports (specific mechanism, model, dataset)
- what the paper does not support (limitation, scope, missing formalism)
- claim_support_status: all 30 are PARTIAL

## Key Cross-Cutting Findings
1. **Representation (Node 2)** is the strongest Function OS node. Weight-space, operator, and adapter representations are well-supported across multiple families.
2. **Compiler (Node 3)** has many concrete instantiations but no unified compiler for all input types.
3. **Artifact (Node 4)** is demonstrated by PAW adapters, LoRA matrices, hypernetwork-generated weights, and merged models.
4. **Interpreter (Node 5)** is supported by frozen interpreters, PDE operator evaluation, and effect-handler semantics.
5. **FunctionSpec (Node 1)** and **Validator (Node 7)** are weak for neural/weight-space functions; formal verification only exists for symbolic code.
6. **ComposerRouter (Node 8)** has strong practical evidence but lacks formal composition semantics.
7. **VersionedRegistry (Node 9)** is strongly supported by LoRA pools, model soups, and skill libraries.
8. **ExecutionTrace (Node 6)** is partially supported; execution feedback is used but not systematically stored.

## GAP Readjudications
- **GAP-015 (specification language):** PARTIALLY_SUPPORTED_WITH_MAJOR_GAPS. Refinement types cover symbolic code; neural/weight-space specs remain unsolved.
- **GAP-016 (weight-space composition algebra):** PARTIALLY_SUPPORTED_WITH_MAJOR_GAPS. Empirical composition exists but no formal algebra guarantees correctness.
- **GAP-017 (equivalence checking):** MINIMALLY_SUPPORTED. No cross-representation equivalence checker exists in the reviewed literature.
- **GAP-018 (effect tracking):** PARTIALLY_SUPPORTED. Algebraic effects provide a strong theoretical foundation; integration with neural execution is open.
- **GAP-019 (versioned registry):** STRONGLY_SUPPORTED. Adapter pools, model soups, and skill libraries demonstrate the concept.
- **GAP-020 (probabilistic semantics):** STRONGLY_SUPPORTED. Probabilistic programming languages and effect handlers provide a rigorous foundation.

## Red Lines Observed
- No Ψ₀ mathematical definitions were modified.
- No new function numbers were added.
- 085 frozen v1 was not modified.
- Unified function/case tables were not modified.
- No source was treated as full-text evidence without actual download and hash verification.
- No strict function equivalence was claimed from similarity or performance.
- No model-generated summary was presented as a paper's conclusion.
- No paywalls or Sci-Hub were bypassed.
- No API keys or tokens were leaked.
- PR #30 was not modified, closed, or merged.

## Limitations and Recommended Next Steps
- All 30 evidence cards are marked PARTIAL. No source fully satisfies a complete Function OS node.
- Semantic裁决 by Kimi-K2.7-Code-HighSpeed is operational but should be reviewed by GLM-5.2 Max for the highest-confidence final adjudication.
- The 10 unresolved/failed sources should be re-attempted in a future task when network conditions allow or when additional legal OA endpoints are identified.

## Conclusion
The Function OS model has substantial full-text evidence across representation, artifact, interpreter, and registry nodes. However, formal specification, equivalence checking, and verified composition remain open gaps. The 121 evidence set is ready for architecture review but must be accompanied by the explicit gaps documented above.
