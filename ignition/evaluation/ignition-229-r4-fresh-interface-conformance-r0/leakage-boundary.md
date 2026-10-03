# Task229-R4 Leakage and Access Boundary

## Frozen boundary

Allowed input paths and exact digests are listed in allowed-input-manifest.json. All other paths are denied. The historical input map contributes only the 18 case-input value records used to build typed R1 bindings. No historical case prose is used; the same neutral case_prose literal is used for every unit.

The successor receives only the frozen policy JSON, typed binding JSON, neutral case_prose, and the exact R3 reference_execution_json required by the frozen prompt. The validator-side expected trace digest, run matrix, thresholds, other unit outputs, and receipts are not sent as additional context. No target success labels, evaluator score sheets, sealed criteria, answer-quality adjudication, or evaluator commentary are allowed.

The R3 prompt requires reference_execution_json as a structured input, including its route_trace. This is an interface input under the frozen prompt contract. The distinct expected digest used for post-response mechanical comparison remains in the validator-side run matrix.

## Access events during R4 preregistration

The following broad reads were accidental and are disclosed. None was used to tune the prompt, policy, binding, threshold, or expected outcome.

1. A GitHub connector fetch of PR #244 returned its metadata, body, and an extensive diff with patch excerpts. The tool output was truncated and the full displayed scope is not known. The R3 head and Open/Draft/Unmerged state were used for Phase 00; no diff excerpt was used to design R4. Because the complete output scope is unknown, this record does not claim that no forbidden material appeared in the returned output.
2. A GitHub compare request for the R4 instruction branch against 1111 main returned a large commit comparison (281 commits ahead and 255 behind) and changed-file path metadata. The output was truncated. No file bodies from that comparison were fetched or used.
3. A recursive tree request at the R3 receipt commit returned repository-wide path metadata for Arvin-liu/1111. The output was truncated. No file bodies from that tree were fetched or used.
4. A Task230 pull-request search returned several PR summaries and bodies, including unrelated PR text. It was used only as a secondary check; the R3 machine receipt remains the authoritative Phase 00 record. No evaluator or target material from those summaries was used.
5. An initial git status in a shallow --no-checkout clone emitted thousands of tracked-path deletion names because no worktree had been populated. The output was truncated; no file bodies were read.
6. The file-level sparse checkout expanded to the full 20-file R3 interface artifact subtree plus the six pinned policy files. The exact R3 artifacts named in allowed-input-manifest.json and the six policies were read as required. The additional materialized R3 subtree files were not opened or used for R4 design.
7. While preparing the append-only receipt from the pinned R3 receipt commit in Arvin-liu/1111, an initial checkout was started before sparse checkout was configured. Git attempted a lazy object fetch for the broader checkout; the operation was interrupted after the remote pack request stalled and ended with an unexpected disconnect. The transferred-object scope is unknown. No file bodies or paths from that attempt were examined or used; only the already pinned R3 receipt metadata was subsequently read through the sparse checkout. This event is disclosed and requires Owner/GPT disposition before any positive R4 result.

These events are not silently treated as proof of contamination or proof of no contamination. The PR diff event has an unknown truncated exposure scope. Before any positive R4 result is claimed, Owner/GPT must review and disposition these events. No positive live result is claimed by this preregistration.

## Hard stops for future execution

- Stop before any live call if an unlisted source, target/evaluator source, mismatched hash, modified prompt/schema, wrong runtime, or changed policy is found.
- Stop immediately on an accidental forbidden-source access during execution; preserve the event and mark the run invalidated by protocol deviation.
- Do not use target answers, scores, labels, or evaluation comments for tuning.
- Do not expose expected trace digests as prose or pass validator-only manifests to the successor.
- Do not use one R4 output to tune or change any later run.
- Keep PR #244 Open, Draft, Unmerged, and unchanged.

## Reconciliation addendum — Owner/GPT disposition and interpretation lock

Owner/GPT reviewed the original disclosures above and accepted:

`R4_PREREG_ACCESS_EVENTS_DISCLOSED_NO_EVIDENCE_OF_TUNING_CONTAMINATION`

The broad/truncated PR diff, repository/path metadata, Task230 PR-summary search, shallow/sparse checkout path output, extra materialized R3 subtree files, and interrupted lazy object fetch remain disclosed. Unknown/truncated exposure scope remains unknown; it is not rewritten as proof that no forbidden content was accessed. No evidence was found that those events were used to alter the frozen prompt, policies, typed bindings, thresholds, expected traces, run matrix, or target/evaluator behavior. Those events do not by themselves invalidate the preregistration. Any new forbidden-source access during live execution remains a hard protocol stop.

After that review, a premature `git status` in the incomplete temporary sparse reconciliation worktree emitted a truncated large list of tracked-path names while checkout was still running. The returned output contained path names only; no file bodies were printed or opened through this command. The full path scope is not enumerated. This additional path-listing event was not used to alter the frozen experiment semantics or generated outputs. No additional Owner/GPT disposition is claimed for this new event; it must be reviewed before any positive live R4 result.

A later targeted fetch to create the missing local tracking ref for the reconciliation head also auto-followed and displayed Git tag/ref names. The command output showed the ref names; whether additional tag-object history or commits were transferred was not separately inspected. No tag contents were opened or used to alter the frozen experiment semantics or generated outputs. No additional Owner/GPT disposition is claimed for this event; review it before any positive live R4 result.

## Reference-assisted conformance interpretation lock

The frozen R3 prompt supplies `reference_execution_json`, including the deterministic R3 route trace, to the live successor. R4 is therefore a reference-assisted live interface/serialization conformance test. A later PASS can establish only that the successor consumed the frozen package and emitted a mechanically conforming response under this prompt. It does not establish independent route derivation from policy plus typed binding without reference assistance.

## Reconciliation follow-up disclosures — pending Owner/GPT review before any positive result

1. To diagnose the required exact-head Foundation CI failure, the GitHub job-log tool returned a large, truncated log for job `111202860548`. The visible log included broad checkout branch/tag names, unrelated validation/test summaries, and the exact `KNOWLEDGE_EXPERIENCE_OUTPUT_DRIFT` failure. Because the returned log was truncated, its complete displayed scope is unknown. It was used only to identify the failing registered deterministic generator; no R4 prompt, policy, binding, schema, expected trace, target output, or evaluator score/commentary was sought or used.
2. A path-only audit of the existing human-results ledger found 208 unique, explicitly registered `reports/evaluations/` source paths and zero Task229/R4 source references. To run the canonical Knowledge Experience generator for the CI-reported drift, those 208 registered sources were materialized and read by the generator. Their contents were not displayed or used to alter R4 experiment semantics. The canonical regeneration changed only the four drifted Knowledge Experience products. No additional Owner/GPT disposition is claimed for either reconciliation follow-up event; both must be reviewed before any positive live R4 result.

3. The exact-head `foundation-validation` run `37127689810` at `ec1fdfe424787c1c16894f5c33c5b958a92b6b01` had job `111216257733`. Its job-log payload was fetched and filtered by a wrapper; only the human-results, self-correction, Knowledge Experience and Fire Seeds summary/error lines were surfaced for inspection. They showed the first three validators passing, followed by `AssertionError: source hash drift: docs/foundation/nonfunction-claim-adjudication-index.md`. Other log lines were not emitted for inspection, and the complete filtered-out scope was not enumerated. No R4 prompt, policy, binding, schema, expected trace, target output, or evaluator result was sought or used. No additional Owner/GPT disposition is claimed; review this event before any positive live R4 result.

4. The canonical `build_fire_seed_census.py` generator was run twice after the registered Knowledge Experience outputs were refreshed, and `validate_fire_seeds.py --check` was run. The generator parsed the human Fire Seeds page and Knowledge Experience origin metadata, then hashed the bounded 857-path source census (including 208 explicitly registered historical evaluation-report paths and 791 Knowledge Experience origins); the validator re-hashed those census sources. A path audit found no Task229/R4 source path in this census. Only aggregate counts, hashes, and validation status were surfaced; source bodies were not displayed. The deterministic census changed only source hashes for the nonfunction closure summary and adjudication index, while the append-only changelog recorded `NO_SEED_DELTA` (64 total entries; 40 content and 24 methodology seeds). No seed content or frozen R4 semantics changed. No additional Owner/GPT disposition is claimed; review this event before any positive live R4 result.

5. During post-push synchronization verification, `git ls-remote --heads origin` returned repository-wide branch/ref names; the command output was truncated, so the full displayed ref-name scope is not enumerated. It retrieved names only and no Git objects or file contents. This listing was not used to alter the frozen experiment or generated outputs. No additional Owner/GPT disposition is claimed; review this event before any positive live R4 result.
