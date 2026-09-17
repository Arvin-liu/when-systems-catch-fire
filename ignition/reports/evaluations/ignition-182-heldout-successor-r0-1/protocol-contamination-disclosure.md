# IGNITION-20260917-182 protocol contamination

Status: `PROTOCOL_CONTAMINATED`.

During the S1 push attempt, repository-local Git configuration reported `core.hooksPath=ignition/evaluation/hooks`; `git push` returned `FAIL_TASK_BRANCH_MISMATCH`. This path is outside the successor-visible manifest allowlist, so the event is treated as an out-of-scope hook read. The exact hook file was not inspected. The ledger records the SHA256 of the captured rejection output, not the hook source bytes.

Normal successor work stopped. The two successor records and S1 freeze receipt were not changed after this event. S1 candidate commit `5aecee5d4b6becaa954e5882d6869a292d393725` remains local and was not pushed. Independent evaluation and Owner/GPT adjudication were not run.
