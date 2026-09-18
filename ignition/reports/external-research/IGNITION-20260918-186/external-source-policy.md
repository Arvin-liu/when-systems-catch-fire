# External source policy — IGNITION-20260918-186

Frozen research baseline: 2026-09-18. Formal repository base: `Arvin-liu/when-systems-catch-fire` at Task181 commit `7cab7541895620d68d5bce2d16c46871ebd03ac0`. The separate instruction repository is not a Formal project source.

## Source hierarchy and labels

- A versioned research paper, official project repository, official documentation, release artifact, or benchmark artifact is primary for the claims it directly supports. Every record in `source-freeze.jsonl` names a pinned version, commit, or snapshot; mutable pages are explicitly marked unversioned and are context only.
- Media, announcements, and independent summaries are secondary. They may be recorded only as `SECONDARY_SOURCE`, never as evidence for a mechanism when a primary source is available. No secondary source is used as authority in this bundle.
- Evidence labels are intentionally separate: `PAPER_CLAIM`, `CODE_OBSERVED`, `DOC_CLAIM`, `SECONDARY_PARAPHRASE`, and `OUR_INFERENCE`. A paper description is not code evidence. Static inspection does not establish runtime behavior, reproduction, independent validation, or real-world generality.
- A code observation names the frozen repository commit and inspected path. An absence means “not found in the frozen files inspected,” not proof that a feature cannot exist elsewhere.

## Freeze, unavailable sources, and licensing

- Prefer versioned arXiv URLs and immutable Git commit URLs. Record access date, version/hash, license as displayed at the frozen source, and exact paths or paper sections inspected. If a source cannot be reached or pinned, record `SOURCE_UNAVAILABLE`, the attempted locator and date, and narrow or withhold the affected conclusion; do not replace it with a secondary summary.
- The CosmosMind research page is unversioned and is frozen only as a dated, access-time comparison. The MetaRSI paper’s versioned arXiv v2 is the controlling paper snapshot. A difference in title/version labels is recorded; no full-text equivalence is assumed.
- Research papers and software have distinct licenses. Preserve the source’s stated license; do not infer a code license from an arXiv paper license or vice versa. The frozen RSI-Harness repository does not declare a license in its checked root/package metadata. This report quotes no source code and integrates no external software.
- No paywall bypass, private endpoint, credentialed hidden artifact, benchmark answer key, or case-specific held-out payload is used. Public source metadata and public benchmark descriptions are in scope; no protected evaluation payload is opened.

## Benchmark interpretation ceiling

Report a result only with its paper, task family, model/provider, evaluation protocol, and scope. A paper-reported score is not independently reproduced here. Code existence or a test suite is not proof of a benchmark claim. Machine-checkable task success supports only the measured task slice; it does not establish general cognition, method inheritance, external truth, or epistemic acceptance. Evaluation access, evaluator identity, contamination protections, and promotion authority are assessed separately.

## Negative results and unresolved items

Negative findings are bounded to the pinned papers, repository snapshots, documentation, and paths listed in the records. Missing license metadata, absent benchmark/training code, unversioned pages, unknown evaluator independence, and unverified cross-model transfer remain explicit. A signal-freshness rule is not treated as a self-model expiration rule. Any analogy to Pointfire is `OUR_INFERENCE` and cannot change canonical terminology or state.
