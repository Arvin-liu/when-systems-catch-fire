# IGNITION-20260917-181 — Cognitive Inheritance R0.1 Isolation Handoff

**Lifecycle:** `READY_FOR_HELD_OUT_SUCCESSOR_TRIAL`

## Frozen subject and branch

- Target: `Arvin-liu/when-systems-catch-fire`
- Base branch: `work/IGNITION-20260916-179-cognitive-inheritance-evolution-r0`
- Exact base: `12e133c6d58a5e22437e42bb75fd912607bb4540`
- Task branch: `work/IGNITION-20260917-181-cognitive-inheritance-r0-1-isolation-protocol`
- Final head: this handoff commit; resolve its exact SHA from PR #221
- Draft PR: [#221](https://github.com/Arvin-liu/when-systems-catch-fire/pull/221), open and Draft

## Bootstrap Guard R0.1

`target_repository_preflight_r0_1.py` checks the Formal origin and push URL,
repository marker, task branch, protected historical branches, repo-local and
effective author/committer noreply identity, staged-only worktree, and exact
push destination. The pre-commit hook runs the guard before a commit. The
pre-push hook accepts only a fast-forward update of this task branch. Fixture
tests exercise all six required positive/negative identity and repository
cases, plus an actual blocked `git commit`; no commit is created when a private
email is configured. See `bootstrap-receipt-r0.1.json`.

## Task180 adjudication input

`task180-adjudication-input-r0.1.json` pins the Task180 final head and hashes
its verdict, blind log, comparison, controls, continuation records, freeze, and
contamination addendum. It records the partial evaluator verdict, partial
reconstruction, two supplied-case continuation pass, 8/8 negative-control
pass, PD-01 self-revealing packet, failed scan isolation, BC-01/BC-02 timings,
and final CI as one pass plus two failures.

The Task181 command supplies `ADOPT_PROVISIONALLY` as the frozen Owner/GPT
disposition with a bounded method-transfer ceiling. The Task180 verdict artifact
itself says `owner_gpt_adjudication: NOT_YET_RUN`. Both facts are preserved; this
handoff does not claim a new Owner/GPT adjudication.

## Evaluation Plane Isolation R0.1

Evaluation artifacts are typed `EVALUATION_EVIDENCE`, counted by repository
path accounting, provenance-hashed, and excluded from shared function and
nonfunction auto-discovery by the common admission policy. Nonfunction discovery
still writes `EXCLUDED_EVALUATION_EVIDENCE_ONLY` audit rows. Regression fixtures
add evaluator report, validator, and contamination-disclosure paths and compare
canonical products and claim closure. The explicit transition helper accepts a
matching authorized source transition only as
`ADJUDICATION_CANDIDATE_ONLY`; it has no write side effects and cannot
canonicalize. Self-correction consults the same shared admission policy before
selecting Knowledge-oriented paths, including evaluator reports under `reports/`.

## Held-out successor protocol

The successor-visible packet is exactly the `packet-manifest.json` allowlist
and its separately listed read-ledger schema. It contains one bounded content
excerpt and one engineering/governance object with source refs and hashes. It
contains no case-specific answer key, gold IR, gold relations, transition,
human confirmation, expected continuation, or evaluator answer. Task183 must
preregister its own source anchors before seeing Task182 outputs. This is
procedural allowlisting, not cryptographic secrecy. Evaluation dimensions and
thresholds are frozen in evaluator-only `evaluation-criteria-r0.1.json`.
Neither successor nor evaluator has been run by Task181.

## Generated surfaces and validation

Task179 base: path classification has 4,602 tracked paths and 4,602 manifest
rows; Foundation function census has 6,158 rows and scans 4,279 text files;
nonfunction closure has 18,003 claims and accounts for 6,033 discovery sources.

The final generated surfaces, audit delta, semantic invariants, validation
results, second-pass fixed point, and clean-clone evidence are recorded below.

### Final gate evidence

- Path accounting: 4,632 tracked paths / 4,632 manifest rows; 0 unresolved and 0 stale; 28 paths classified `EVALUATION_EVIDENCE`.
- Foundation: `CHECKS_TOTAL=63 CHECKS_PASSED=63 CHECKS_FAILED=0`; R0 validator PASS; targeted R0.1/evaluation/admission tests 26/26 PASS.
- Function assets: 6,158 census rows across 4,279 scanned text files; deterministic `--check` and adjudication `--check` PASS; census JSONL is byte-identical to Task179 base.
- Nonfunction claims: 18,003 canonical claims / 31,102 candidate fragments / 6,063 discovery rows; deterministic generation check PASS; canonical claim registry is byte-identical to Task179 base; 28 evaluation-only rows are explicitly excluded.
- Knowledge Experience: 691 cards / 586 changes / 612 layers / 24,773 search rows; builder check and audit PASS, including 28,807 links. Changed source hashes are limited to the refreshed generated audit index and path-classification manifest; no asset identity, content, or status changed.
- Self-correction: 717 deltas / 10 rules; generator check PASS. Evaluation evidence under both configured prefixes is excluded; ordinary operations history and human function assets retain existing eligibility.
- Fire Seeds: 64 entries (40 content / 24 methodology), 678 source paths / 612 layered origins; census check and validator PASS.
- Human Visibility, Claim Browsers, overall architecture, knowledge admission, evaluation-plane receipt validation, and the 14-file held-out packet manifest PASS. Packet manifest SHA256: `cdc54e1600de691fadc01b630f086c4bb81c8b0c606d0a92b8df656dbe679295`.
- Second generator/check pass: path classification, function census/adjudication, nonfunction claims, self-correction, Knowledge Experience, Fire Seeds, Claim Browsers, and overall architecture all PASS.
- Full-history clean clone: detached at implementation head
  `8f495b3aed76d22701cf4e3bc2fd4bcbf96704f1`; not shallow; worktree clean;
  evaluation-plane validator, R0 validator, path-accounting check, held-out
  manifest check, and 26/26 targeted tests PASS. The final handoff commit changes
  this receipt only; exact final-head checkouts and workflow conclusions are
  recorded in PR #221.
- Exact-head workflow evidence: see PR #221 Checks and the linked final handoff
  evidence in its description. The branch remains Draft at this lifecycle.

## Complexity and limits

The scope uses existing path classification, admission, and provenance patterns;
it adds no second Foundation, generic provenance service, ontology, or semantic
registry. Current additions and retirement candidates are recorded in
`heldout/r0.1/README.md`. No claim about general cognitive inheritance, model
improvement, external truth, R1 readiness, or epistemic acceptance is made.

**Final lifecycle:** `READY_FOR_HELD_OUT_SUCCESSOR_TRIAL` only after all required
Task181 gates pass and exact-head evidence is recorded. This task must stop at
that state. Do not launch Task182 or Task183 here.
