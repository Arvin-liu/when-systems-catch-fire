# IGNITION-20260910-169 result

## Controlling command

This bounded execution is controlled by `Arvin-liu/1111@5854e36`,
`agent-commands/IGNITION-20260910-169.md`.

- Command blob: `47506a24c6a1163ebc3f92fed884d5a748179260`

## Exact baseline

- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Formal remote `main`: `f2a94aaa62b5eed36c63a457a5a20e185b7f16c6`
- Starting candidate head: `f2a94aaa62b5eed36c63a457a5a20e185b7f16c6`
- Branch: `work/IGNITION-20260910-169`
- Worktree: fresh full clone with no pre-existing user changes

## Bounded execution facts

- `.github/README.md` section 3 was replaced with the command-provided text.
- `.github/README.md` architecture image and entry text were replaced with the command-provided presentation/reading links.
- `ignition/RESULTS/LATEST.md` was replaced in full with the command-provided thin route text.
- The existing stable architecture SVG, interactive HTML, canonical architecture source, authored topology and Pages publication route were not modified.
- The homepage projection validator and human front-door validator now distinguish the presentation URL from the reading URL.
- Targeted tests mechanically protect the command-provided README section 3, architecture entries and LATEST routes.

## Browser acceptance facts

The existing `?present=1` Presentation Stage was checked in a real browser at 1440×900 and 1920×1080. Both viewports set `html[data-present="true"]`, kept document scroll height equal to the viewport height, removed the ordinary reader max-width, gave the diagram the remaining presentation height, and matched the SVG client dimensions to the diagram content box. Search, zoom and drag interactions also passed at the 1920×1080 viewport.

No Current identity, architecture identity, iteration method, operating method, epistemic status, claim ceiling, canonical research verdict, runtime capability or Owner authority was changed.

This result is finalized before the final full-repository derivation. Final generator fixed-point, exact-head, clean-clone and remote CI facts are recorded in the PR metadata and execution handoff.
