# Propagation Obligations — Task 109 (contract §11)

Mechanism reused from tasks 106–108. This artifact records the bounded propagation
of establishing the iteration planner. It is a decision-support projection, not a new
truth layer; it does not alter any Foundation claim.

## Lifecycle candidate event

- event: `iteration-planner-establishment`
- phase: before content merge (recorded pre-merge; terminalized after terminalization merge)
- authoritative: NO — planner output is not an authoritative discovery input.

## Nine-dimensional impact

| dimension | impact | note |
|---|---|---|
| claims | none | no claim added/changed |
| evidence | additive (new pilot queue) | proposes evidence pilots; does not alter existing evidence |
| architecture | none | no component added |
| system-map | NO_MAP_IMPACT | see below |
| editorial / article | additive | new article under `data/operations/iterations/109/article.md` |
| governance | additive (governed backlog) | new governance artifact, gated by anti-meta |
| dependencies | none | planner reads existing sources only |
| CI | additive | new workflow `iteration-planner-ci.yml` (Layer A + B) |
| human-visible surfaces | additive | article + recommendation + backlog published |

## Current-truth projection

The backlog inventory reflects current truth at `origin/main` (captured at planning
time). It is a snapshot, not a permanent truth layer. Re-running the planner on a
later `origin/main` may change rankings; that is expected and documented.

## Article stale/review handling

The article is newly authored for this iteration; no prior stale article to reconcile.
It will be reconciled in a future iteration if the planner's recommendation is executed.

## System-map impact

**NO_MAP_IMPACT.** Machine justification: the planner adds `tools/iteration_planner/`
(tooling) and `data/operations/iterations/109/` (governed outputs). Neither is a
runtime system component, capability node, or architectural edge. No `interactive-system-map.json`
node or edge is created, removed, or retyped. Therefore no system-map delta is required.

## Repository-path classification + Foundation fixed point

- `tools/iteration_planner/**` → tooling (non-authoritative)
- `data/operations/iterations/109/**` → governed iteration output (non-Foundation)
- `docs/editorial/articles/...` (if surfaced) → human-readable surface
- Foundation fixed point: no file under `data/foundation/` or any claim-bearing path is
  modified. The Foundation claim set is unchanged.

## Human-visible result surfaces

- `data/operations/iterations/109/article.md`
- `data/operations/iterations/109/next_iteration_recommendation.md`
- `data/operations/iterations/109/ranked_queue.json` (+ dossiers)
