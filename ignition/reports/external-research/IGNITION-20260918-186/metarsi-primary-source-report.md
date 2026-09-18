# MetaRSI primary-source report

## Frozen source set

The controlling paper is arXiv `2609.06396v2`, updated 2026-09-09 and labeled MetaRSI-v1 in the paper. Its formal title, complete author list, arXiv license, official CosmosMind page, RSI-Harness Git commit, and Hugging Face snapshot are recorded in `metarsi-source-freeze.json`. The public page is unversioned and dated 2026-09-03; its title label differs from the arXiv title. The versioned arXiv HTML is therefore the paper locator for this report.

## Paper's central architecture claim

The paper's strongest architectural contribution is a shared improvement contract over a typed deployed-system triple: training data, model state, and execution harness. Three operators write disjoint surfaces and share a compiled evidence signal. A horizontal scheduler selects operator order; a vertical path revises operator proposal policies; a meta layer changes the scheduler. The paper makes method revision explicit as a different object from output revision, prompt editing, or optimizer execution. These remain `PAPER_CLAIM` statements, not reproduced findings.

The paper also specifies authority boundaries: operators propose; fixed or deterministic evaluation and a protected release rule decide whether a candidate can advance. The held-out task set, evaluator, release rule, and budget ledger are outside all operator write surfaces. For generated data, however, the Operator and blind Anchor are roles of the same target model; the paper explicitly says they are separated by input isolation rather than model identity. Its use of “independent evaluation layer” should therefore be read as an architecture role and protected measurement boundary, not automatically as a different model or independent institution.

## Freshness, carrier, cost, and subtraction

The paper describes the compiled learning signal as perishable: after a behavior-changing step, previous evidence must be recompiled for the new system. Its typed adapters also reject stale artifacts. This is an explicit freshness mechanism for evidence/artifacts; the bounded v2 text search found no separate time-to-live or expiry rule for a persistent self-knowledge or capability profile.

The paper distinguishes three carriers and costs. Harness changes are immediately usable but consume inference context on every run. Model changes consume bounded training compute and are intended to internalize behavior across scaffolds. Data changes amplify only behavior already exhibited in experience. Figure 3 proposes an H→D→M→H sequence that retires scaffolding after internalization; the Harness description also claims auditable memory consolidation, deduplication, and a hard complexity budget. The arXiv text does not name a separate compression algorithm, and the public repository is not evidence that this retirement path is executable.

## Verifier and experiment scope

The paper says model-driven roles are all played by the target model. Its reported tasks are executable coding and closed-form scientific reasoning with test suites, exact-match, or numeric keys. It explicitly limits such scores to benchmark-bound slices. The provider-interface route applies Data-RSI and Harness-RSI where weights cannot be written; Model-RSI is reported for the open-weight target. No benchmark result is reproduced by this source review.

## Code and documentation status

The frozen official repository is RSI-Harness, not a full implementation claim for every paper component. Its README and Genome documentation describe Pi-compatible execution, a self-contained Genome configuration, and a harness-rsi Genome that scans selected session sources, proposes a plan, and waits for user confirmation before writing. The README says the repository lacks benchmark, data-generation, training, and evaluation code. The npm package declares `private: true`; no repository license or package license field was found in the inspected snapshot. The Hugging Face snapshot has `config={}` and no model weights. Step02 will make the paper/repository distinction file-specific.

## Primary-source ceiling

What is new in the paper, if its claims hold, is the typed composition of data/harness/model changes under a shared evidence signal plus explicit horizontal and vertical scheduling of the improvement procedure. The same source also states its own limits: its validation is benchmark-bound, and its verifier/role separation is not equivalent to independent model identity. The versioned paper does not establish general cognitive inheritance, and this task does not promote that claim.
