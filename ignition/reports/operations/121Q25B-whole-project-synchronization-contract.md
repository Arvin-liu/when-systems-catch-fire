# 121Q25B Whole-Project Synchronization Contract

Status: superseded non-ready method 1.1.0 Draft candidate on PR #57. Q25C preserves this history and repairs its lifecycle deadlock.

## Reproduced defect

The prior validator loaded only `reports/operations/121Q24-completion-seal.json` and passed that object while iterating every manifest. Seal checks ran only when task IDs matched, so Q25 could pass without any Q25 manifest/seal comparison. The generic validator now resolves each manifest's declared seal path, or infers `<task_id>-completion-seal.json` for method 1.0.0 compatibility, and rejects missing, duplicate or mismatched bindings.

## Contract

`data/operations/synchronization-surfaces.json` is the canonical topology of synchronization obligations. It does not store substantive capability truth. Method 1.1.0 manifests declare transition subjects/dimensions, a registry-derived closure and separated completion states.

Repository-local validation reports implementation consistency and repository synchronization closure. It always reports live external truth as false. External Pages production verification remains a post-merge obligation.

## Self-hosting result

Q25B assesses all triggered human, AI/Agent, machine, history and deployment surfaces. Q25's accepted README/current-state/AI-guide content remains unchanged with evidence. Agent/machine entrances, templates, version records, method assets and Draft Pages workflow change. The external homepage remains an explicit unresolved post-merge action without blocking Draft readiness; it blocks acceptance/current/closed until attested.

## Claim boundary

This contract can detect declared synchronization omissions and lifecycle inflation under its registry. It does not prove repository file dependencies are physical causality, prove substantive claims, or verify live external state locally.
