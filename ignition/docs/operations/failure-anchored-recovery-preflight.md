# Failure-Anchored Recovery Preflight R0

`maintenance.preflight_failure_anchored_recovery` checks one proposed recovery plan against a caller-supplied failed-run record. It is an optional, default-off, offline review aid.

## Use it for

- preserving the original failure and append-only evidence excerpts;
- keeping observations separate from diagnosis hypotheses;
- checking that each diagnosis and proposed recovery step points to the same declared evidence;
- detecting a repeat of an unchanged action after the same failure signature;
- requiring a bounded permission and budget declaration, a verifier, and stop conditions before a recovery is considered for human review.

Run one bounded UTF-8 JSON input:

```sh
python3 -B ignition/tools/toolbox_failure_anchored_recovery.py --stdin < failure-recovery.json
```

The tool reads only stdin and its local input schema, writes one JSON result to stdout, and never modifies files or makes network calls.

## Decision meanings

- `READY_FOR_HUMAN_REVIEW` means the declared links and gates are internally consistent. It does not mean the diagnosis is true or the proposed recovery is safe or effective.
- `BLOCKED` means at least one evidence, preservation, repeat-attempt, permission, budget, verification, or stop-condition check failed. The tool returns `STOP_NO_RETRY` and no proposed instructions.
- Both outcomes set `execution_authorized=false` and `retry_authorized=false`.

For `OBSERVATION`, the statement must appear in one of the cited evidence excerpts. A `HYPOTHESIS` remains an unverified proposal and must include a falsifier. Excerpt hashes check only that the digest matches the caller-supplied text; source URLs, run IDs, commit IDs, measurements, commands, and caller identity are not independently authenticated.

## Boundaries

This tool does not retrieve logs, diagnose failures, write recovery plans, invoke validators, edit the failed artifact, retry a run, broaden permissions, or decide whether an operator should proceed. It does not replace `evidence.failure_case_evidence_gate`, which checks the evidence required to label a case as a reproduced implementation defect; `collaboration.validate_portable_research_episode`, which checks manifest relations; or `maintenance.preflight_governed_improvement_transition`, which compares declared system-level predecessor/successor measurements.

Use the existing failure-evidence gate when adjudicating an implementation-defect claim. Use this preflight when a caller has a specific failure record and a recovery proposal that needs evidence, verification, and stop-rule checks. If source authenticity, root-cause analysis, or recovery safety must be established, obtain independent review outside this tool.
