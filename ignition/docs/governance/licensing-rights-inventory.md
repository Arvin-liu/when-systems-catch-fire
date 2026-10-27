# Licensing Rights Inventory

Status: candidate audit for IGNITION-20260715-121Q8. This document is not legal advice and does not change the effective repository license.

## Current License History

The repository currently contains a root `LICENSE` file with the MIT License and the README states that the project uses the MIT License. Git history shows license-related commits including `05dd3b4c` (CC BY-NC-SA content-license attempt), `47cf04c5`, and `74ebfb82` (current MIT root license). Existing public releases and copies made under MIT cannot be retroactively withdrawn by this candidate transition.

Future versions may adopt a different layered license only after explicit maintainer approval and appropriate legal review. The boundary between already-published MIT material and future candidate-licensed material must remain visible.

## Observed Contributors

`git shortlog -sne HEAD` shows the dominant authorship under identities controlled by the project maintainer, plus local agent identities such as OpenClaw, QClaw Agent, Codex, Ignition Agent, and `agent`. These agent-authored commits should be treated as maintainer-directed contributions unless a later audit proves otherwise. This is a provenance observation, not a legal conclusion.

## Material Classes

| Class | Examples | Candidate Treatment | Notes |
| --- | --- | --- | --- |
| Original software | `tools/`, workflow glue, validation scripts, future executors, Function OS implementations | BUSL-1.1 candidate with four-year conversion to AGPL-3.0-or-later | Do not apply retroactively to existing MIT grants. |
| Original documentation and reports | `docs/`, `reports/`, README prose, governance notes | CC BY-NC-SA 4.0 candidate | Commercial reuse requires separate permission. |
| Original structured data | `data/foundation/`, project registries, generated ledgers | CC BY-NC-SA 4.0 or database-specific review candidate | Factual claims and third-party metadata may not be ownable; verify per dataset. |
| Public interfaces and schema | `schemas/`, `llms.txt`, interoperable protocol/interface descriptions | CC BY-SA 4.0, Apache-2.0, or similarly open candidate | Keep interoperability broad while protecting core implementation. |
| Third-party material | cited papers, external references, quoted materials, provider outputs, upstream legal text | Original rights retained by their owners | Do not relicense without permission. |
| Unclear rights | imported exports, generated content with uncertain source, legacy material with incomplete attribution | Quarantine or retain current status pending audit | Do not place under new candidate license until resolved. |
| Project name and marks | `点火`, `When Systems Catch Fire`, logos or official badges if added | Trademark/name-use control candidate | Code/content license does not grant endorsement. |

## Required Follow-up Before Effective Migration

- Identify release/version boundary for future licensing.
- Decide whether contributor agreement, inbound=outbound, or dual-license grant is required.
- Separate legal text from explanatory summaries.
- Review third-party quoted/cited material and any generated content with uncertain rights.
- Keep root `LICENSE` unchanged until explicit approval.
