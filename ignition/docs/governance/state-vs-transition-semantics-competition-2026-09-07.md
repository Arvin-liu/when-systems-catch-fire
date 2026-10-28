# State versus transition semantics competition

Task IGNITION-20260907-161 is a research-only prospective comparison. The controlling specification is Arvin-liu/1111/agent-commands/IGNITION-20260907-161.md at command commit 59003ae23c56a2f0c4ac6389d5235c938cd5f5fd, blob 610febea27a1e4cb62d9c32da4b19a9113a243ec, complete content SHA-256 9f1df434d39aa379fac5eb2254b250530720e994176526da3c971ee0e84d06de. Formal repository is Arvin-liu/when-systems-catch-fire, with required base work/IGNITION-20260907-160@9ceb4c4eb84203bee2b62dcdbe0d5c1c09707438 and Formal PR #210. Missing instructions/CURRENT.md and relay/current pointers were preserved and recorded as STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL. No canonical runtime, validator, Current pointer, Ready transition, merge, Owner acceptance, or external action is claimed.

## Result

Primary verdict: UNDERDETERMINED

Synthetic threshold candidate verdict: FIRST_CLASS_TRANSITION_SEMANTICS_SUPPORTED_AS_RESEARCH_CANDIDATE; this is not independent validation and is capped at DETECTOR_NOT_VALIDATED.

The fresh suite contains 144 paired fixtures and 288 instances across F1-F12. Calibration has 48 pairs; in-family holdout has 48; transfer holdout has 48. Pair members remain in the same split, and transfer uses unseen family/template combinations.

MT incremental detections beyond MS are 48 instances in-family and 72 in transfer. New-control false positives are 0. The two clean-clone blind score files are byte-identical: True.

The result is a research candidate only. It does not establish production readiness, canonical semantics, lifecycle truth, Current status, or Owner acceptance. Final branch HEAD and CI state are bound in the Draft PR and independent receipt after commit; this report deliberately does not self-embed a final commit SHA.

## Frozen design

H0 tests state-local sufficiency; H1 tests an irreducible first-class transition relation; H2 tests reducibility to fair local patchwork; H3 keeps path/non-Cartesian semantics as a separate hypothesis. Historical Task160 transition-over-state rows are discovery leads only, are deduplicated, and are never used as positive labels. Answer-key data is joined only after both blind scores.

MS is the strongest fair local patchwork and has no shared transition object, identity, algebra, path, or central authority. MT reads the exact same raw facts and adds only a minimal transition relation and constraint checks. MH is diagnostic.

## V2 gate

The Task159 V2 signature is copied verbatim into v2-semantic-leap-score.json. L1-L6, challenger priority, compile-away, fresh all-old-check failures, control FP, metamorphic, and determinism gates are reported there. No threshold or signature definition was rewritten.
