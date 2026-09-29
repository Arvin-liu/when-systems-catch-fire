# Task228 runtime report — Phase 04 through Phase 07

## Scope and terminal claim

Task: `IGNITION-20260929-228`. This run resumed at Phase 04 after the A1 Owner/GPT adjudication. The controlling 1111 snapshot was `55a0add295b70afa4283fa2a75bbc26ac4bc63b3`; the requested instruction/checklist/current-state set was consistent at that locked revision.

The result is limited to the reconciliation of Task227's human and machine policy-contract layers, and six target-blind reference instrument candidates that pass the Task228 machine and independent semantic audit gates and rebuild byte-identically. No transfer experiment, revision-generation experiment, full-chain run, target evaluation, R1, cross-model work, Model-RSI, or training was performed or established.

## Frozen Task227 anchor

Task227 PR #237 remained OPEN + DRAFT + UNMERGED at exact head `7d979b1aa523030b16f773a973477cbfca1e4513`. Its four required exact-head workflows were successful, with run IDs and conclusions recorded in the 1111 machine receipt. The 52 frozen files and six M0/E1 inputs remained hash-valid. No Task227 files or results were modified.

## Phase gates

- Phase 04: A1 adjudications are encoded consistently in the normative contract, JSON Schema, validator, rubric, and authoring guide. Conformance tests cover positive and adversarial cases.
- Phase 05: six researcher-authored target-blind mappings (two per family) are serialized deterministically. All six candidates pass the Task228 validator. The compiler's `--check` result is `BYTE_IDENTICAL`.
- Phase 06, round 1: raw independent sheets are preserved. Auditor A passed all six. Auditor B found the required nested evidence-coverage rule missing for F02_A and F02_B. The requirement was added explicitly to the contract, validator, rubric, and adversarial tests; the matching F02 mappings were corrected. No result-driven rule relaxation or audit reconciliation was used.
- Phase 06, round 2: two separate read-only packages were supplied. Both auditors passed all six candidates across all 15 machine predicates and nine semantic dimensions. The exact package file hashes and tree digest are in `audit/round-2/package-manifest.json`. The raw first- and second-round sheets are preserved under `audit/round-1/` and `audit/round-2/`.
- Machine verification: validator 6/6; conformance tests 4/4; Task227 diagnostic regression 3/3; compiler byte-identical; v2 package validators/compiler checks passed in each auditor copy.

## Reproducibility and boundaries

Candidate/mapping/compiler/source hashes and the six-candidate build status are in `build/candidate-build-manifest.json` (SHA-256: `dc679675af1401a3b4c7c816bcded9e7485dbf49f109d3e08f757011f21eb484`). Audit package tree digest: `aea6dae3ff3b13c5ccb06710abd8547bcfe1bc92eb130b707730ca307884e082`; package file count: 22. Raw v2 audit sheet hashes: Auditor A `3c1b694c60f7b457a6864fdc23ebeb31c133a7c9890f363dcef632c1488a14ec`; Auditor B `7be06bb661935fdf3ead9197a84ade14b753db67def0b548ec7e1e0ffdfe481b`.

The candidate compiler and both reviewers received only the contract, schema, rubric, guide, mapping declaration, candidate artifacts, compiler/validator, the sanitized M0/E1 source manifest, and the six corresponding M0/E1 files. No A/B/C target material or Task227 evaluation outcomes were in either package. Build manifests state target access false and experiment flags false; no target was opened.

## Repository path accounting

The first final-head preflight identified 36 newly tracked Task228 subtree paths missing from the repository-wide generated classification manifest. The existing classification engine regenerated the manifest without changing its rules; all 36 paths are classified as EVALUATION_EVIDENCE. Local --check reports 5,528/5,528 tracked paths accounted for and 10/10 checks passed; --self-test passed. Generated manifest SHA-256: 7342705c2a946dbc3afb4877d6122150a2fdd371fea8d8ffbc7e630513da8c45.

## Formal publication reference

Formal repository: `Arvin-liu/when-systems-catch-fire`. Task228 branch: `work/IGNITION-20260929-228-policy-contract-reconciliation-r0`, stacked from the exact Task227 head above. Draft PR #238 is [OPEN + DRAFT + UNMERGED](https://github.com/Arvin-liu/when-systems-catch-fire/pull/238), with base branch `work/IGNITION-20260928-227-cognitive-evolution-component-isolation-r0` at `7d979b1aa523030b16f773a973477cbfca1e4513`. It was opened at Task228 head `2470849b4af68916c5492e708a34b6d834a92f22`. This publication-metadata update advances the PR head after opening. The final current head SHA and exact-head CI run IDs/conclusions are recorded in the terminal 1111 relay receipt after verification against that final head. At final receipt publication, the receipt branch must not be merged to 1111 main.

## Claim ceiling

This report supports only the bounded Phase 01–07 Task228 claims stated above. It establishes no transfer interface, revision-generation capability, Cognitive Evolution, general inheritance, causal method effect, cross-model transfer, R1, Model-RSI, or training benefit.
