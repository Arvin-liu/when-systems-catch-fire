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
