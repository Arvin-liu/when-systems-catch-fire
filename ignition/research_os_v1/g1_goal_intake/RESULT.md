# V1 G1 read-only Goal intake candidate checkpoint

Status: `V1_G1_READ_ONLY_ADAPTER_CANDIDATE_READY_FOR_OWNER_REVIEW`

This is a bounded synthetic preflight candidate. It is **not** a G1 gate pass, an authenticated Owner decision, or evidence about Stage08.

## Scope and source binding

- Repository: `Arvin-liu/when-systems-catch-fire`
- Draft PR: [#251](https://github.com/Arvin-liu/when-systems-catch-fire/pull/251), remains open and draft
- Branch: `draft/v1-g1-goal-intake-independent-20261010`
- Parent/base: `main@f17477dd9761c898563dbf5670c63914a5ecedfa`
- Initial branch head: `846d567d834159e97a5d44be1cf10f4d25b93acc`
- Implementation commit: `a64f5a32df059c14dbeacd736116f6b8b4a8bacf`
- Pinned work order: `Arvin-liu/1111@16b67e1340b6eafd568ee39c16c4877c39fbca0b:instructions/goal-mode/IGNITION-2026-10-10-v1-g1-parallel.md`
- Work-order and Steering source anchors are pinned in the generated admission report by ref and blob SHA.
- All authored paths are under `ignition/research_os_v1/g1_goal_intake/` or the new `ignition/tests/test_research_os_v1_g1_goal_intake.py` test path.

The adapter validates and projects only supplied synthetic request/snapshot bytes through existing Steering types. It writes no canonical records, creates no approval receipt, does not mutate a Goal lifecycle, makes no completion decision, and does not dispatch work. Trust roots and source currentness remain unknown offline; the required next action is Owner review.

## Verification

Commands were run from the `ignition/` directory at implementation commit `a64f5a32df059c14dbeacd736116f6b8b4a8bacf`:

| Command | Result |
| --- | --- |
| `python3 -m py_compile research_os_v1/g1_goal_intake/*.py tests/test_research_os_v1_g1_goal_intake.py` | exit 0 |
| `PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_research_os_v1_g1_*.py' -v` | 58 tests passed, exit 0 |
| `PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_steering_episode_binding.py' -v` | 4 tests passed, exit 0 |
| `PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_steering_completion.py' -v` | 5 tests passed, exit 0 |

The CLI was run twice against `research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json` into separate temporary directories:

```sh
python3 -m research_os_v1.g1_goal_intake --input research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json --report-dir /tmp/g1-goal-intake-terminal-20261010-final-a1
python3 -m research_os_v1.g1_goal_intake --input research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json --report-dir /tmp/g1-goal-intake-terminal-20261010-final-b1
cmp /tmp/g1-goal-intake-terminal-20261010-final-a1/admission-report.json /tmp/g1-goal-intake-terminal-20261010-final-b1/admission-report.json
cmp /tmp/g1-goal-intake-terminal-20261010-final-a1/summary.md /tmp/g1-goal-intake-terminal-20261010-final-b1/summary.md
```

Both runs returned `REQUIRES_OWNER_AUTHORITY` and `CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY`; both `cmp` checks exited 0.

| Artifact | SHA-256 |
| --- | --- |
| Synthetic input fixture | `8f0f9d226ba0ab83d34a31dfaf3f560752040d5268ba6505b8433102a9d0e84e` |
| Admission JSON report | `4c84d20c1cd5d117345e627b98a78101788c84aa70fa9ee54950d91354c001c0` |
| Human Markdown summary | `95135eac9d649bc89e4dc10b3ddb84ff3c0a29fb3d80348181a58abeacdd328a` |

## Independent review

An independent A6 reviewer (`/root/a2_authority_review`) reviewed the source and evidence without touching Stage08, the workbench, or the PR. The reviewer ran the 58 new tests and both existing Steering regression suites (4 and 5 tests); all passed. The reviewer also confirmed repeatable CLI output, fail-closed synchronized-contract tampering, Unicode confusables, and deeply nested JSON handling. Reviewed source digests were `preflight.py=f666d3c3e3cae96fbeae84b0f2e81aede08a35de4bd399836e4dd3a26415f7b4` and `test_research_os_v1_g1_goal_intake.py=cd812806207ae089f43f2f113558b2931d295ab8317d8588ef26b2c07a120a96`. No remaining review blocker was reported.

## Failure and repair record

- The first 50-test run had one assertion failure and two assertion errors because tests expected summary keys for inputs rejected before a summary was constructed; one nested non-text deliverable correctly returned `bounded_text_required` while its test expected `bounded_string_list_required`. Assertions were corrected to check the observed fail-closed `INVALID_INPUT` outcomes and that rejected raw values were not echoed. No acceptance state or production behavior was relaxed.
- Independent review found that a caller-controlled report directory could target an arbitrary path. The CLI now confines writes to explicit system temporary roots and rejects outside paths and symlink escapes before writing (tests 51-52). No protected path write was attempted.
- Review found case/separator/compact `RUN_PASS` shortcuts and a synchronized untrusted-contract alteration path. The policy guard now normalizes shortcut spellings and enforces the invariant independently of the supplied forbidden list (tests 53-56).
- Review found deeply nested JSON could raise `RecursionError`; it now fails closed as malformed input (test 57).
- Review found Unicode confusable policy tokens could evade ASCII policy checks; non-ASCII policy tokens are rejected (test 58).
- The final manifest check was first invoked from the repository root, where its `ignition/`-relative paths could not resolve. Re-running from the documented `ignition/` directory verified all 11 entries. This was a working-directory mistake, not a checksum mismatch.
- A pre-commit guard compared the entire `git var GIT_AUTHOR_IDENT` line to an earlier line, including its dynamic timestamp, and stopped before staging or committing. The local author and committer name/email were then checked independently against the authenticated account's public noreply identity; no commit was made by the failed guard.
- A later combined pre-commit command regenerated the relative-path manifest from the repository root but checked it from `ignition/`, so all 11 prefixed paths failed to resolve and the command stopped before staging. The manifest was regenerated and verified from the documented `ignition/` working directory; this was another path mismatch, not a file hash mismatch.

## Terminal boundary

The final exact branch head is recorded in the terminal checkpoint appended to PR #251 after the report commit is pushed. PR #251 remains Draft. No merge, Ready transition, `Current` mutation, Stage08 access, Task229 R4, AB-19, or Task230 action is authorized or claimed here.
