# 121Q25 Human Front-Door Audit

Starting `main`: `7fc4b309720ea1b4e9c4b47477c2f423860d53df`.

Claim ceiling: `validated_human_front_door_sync_candidate_only`. This report verifies repository surfaces and records external rendering evidence; it does not make MCF, PSD or ARN a truth layer or proven scientific theory.

## Before

| Surface | MCF | PSD | ARN | Q24 | Finding |
| --- | --- | --- | --- | --- | --- |
| GitHub README visible summary | STALE | STALE | STALE | PARTIAL | Iteration link existed, but the current capability paragraph omitted all four. |
| Rendered GitHub Pages | STALE | STALE | PARTIAL | PARTIAL | Live page was built from the stale README; ARN appeared only in the collapsed directory. |
| Project current state | CURRENT | CURRENT | CURRENT | PARTIAL | Content was current, but scope still named PR #55 as the total baseline. |
| Expanded human AI guide | STALE | STALE | STALE | STALE | Priority files and questions omitted all four. |
| Embedded README AI prompt | STALE | STALE | STALE | PARTIAL | `ITERATION.md` was listed, but its capability and all three architecture relations were absent. |
| AI-START-HERE.md | CURRENT | CURRENT | CURRENT | CURRENT | No change required. |
| llms.txt | CURRENT | CURRENT | CURRENT | CURRENT | No change required. |
| SUMMARY.md | CURRENT | CURRENT | CURRENT | CURRENT | No change required. |

The public page mechanism is `.github/workflows/pages.yml`: it copies the root `README.md` into `site/index.md`, builds with the official Pages Jekyll action, uploads the artifact, and deploys it. It is not a separate content authority.

## Candidate repair

- The visible README names and briefly relates MCF, PSD, ARN and the current iteration method.
- README provides direct MCF, PSD and ARN architecture links.
- README and the expanded AI guide contain byte-identical copyable prompts with the current priority files, relation question and claim boundary.
- The current-state scope names the post-PR #56 / Q24D lifecycle boundary without embedding its own future commit SHA.
- `tools/validate_human_front_door.py` checks semantic names, paths, relation and claim-boundary language, prompt identity, current-state scope and README-derived Pages configuration.
- Adversarial tests remove each capability from both human front doors, alter the visible summary, split the prompts, restore stale PR #55 wording and replace the Pages source.

## No change with reason

- `AI-START-HERE.md`: already names MCF, PSD, ARN and the iteration boundary.
- `llms.txt`: already records the post-PR #56 current version and all four capability boundaries.
- `SUMMARY.md`: already links MCF, PSD, ARN and describes the Q24 method as current.
- `AI-HANDOFF.md`: already requires the ARN/MCF/PSD and Q24 reading chain.
- `docs/VERSIONING.md`: already distinguishes the Foundation baseline from later current capabilities and Q24.
- Pages templates and workflow: README is already the single content source; no second page copy is needed.

## After

Repository-local candidate state is `CURRENT` for all four capability names and boundaries across README, the expanded guide, current-state scope and Pages source. The actual deployed page remains an external fact and must be fetched after the exact candidate HEAD is deployed; its run ID, HEAD and rendered-content observation belong in the PR body and 1111 receipt.
