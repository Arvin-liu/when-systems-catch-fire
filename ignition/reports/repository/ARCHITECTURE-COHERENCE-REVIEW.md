# Architecture Coherence Review — Line D (D3)

Scope: relation audit among L0–L6, Language–Thought Logic Plane, Function OS, Research Executive OS candidate, Q12/Q13/Q14, claim governance & Charter Gate, iteration method & lifecycle, and publication/knowledge surfaces. Every finding binds to exact files/fields.

Evidence base: `data/operations/project-components.json` (62 components: 7 architecture layers, 11 governance constraints, 12 overlays, 9 publication-chain, 5 interpretation boundaries, plus infrastructure/front-door/model-projection types), `data/architecture/interactive-system-map.json` (50 nodes / 52 edges at Line B verification), Foundation/Lifecycle validators via their canonical workflows.

## Findings

**F1. Duplicate authority — governed, not accidental.** `allowed_path_overlaps` declares 9 explicit shared-path authorities with written reasons (e.g. Foundation spans `data/foundation/` across L0–L3; `formal/` shared Foundation/L4; `docs/publication/cases/` shared external_input/case_source/L6; `reports/publication/` shared L6/ignition_increment/point_fire_analysis). Classification: **documented design**, not defect — overlaps carry `authority_source` citations. Residual risk: overlap growth without review would silently erode single-owner accountability; recommend owner periodically re-adjudicate the overlap table (`RECOMMENDATION_ONLY`).

**F2. Circular provenance — none found at component level.** Component authorities point upward to canonical documents (`ARCHITECTURE.md`, `FOUNDATION.md`, plane docs); no component cites a generated projection as its authority. Generated projections (`current-truth-projection.json`, system map, path manifest) each declare their generator and are excluded from authoritative inputs by the path-classification anti-backflow allowlist (only the two CJK master tables may feed Foundation assertion discovery). Classification: **clean**.

**F3. Orphan components — none unjustified.** 11 registry components do not appear as system-map nodes; every one carries an explicit `map_projection.no_change_reason` (interpretation-boundary markers such as `foundation_data`, `system_map`, `historical_reports`, and infrastructure like `propagation_calculator`, `incremental_execution`, `stage_snapshot_publication`, `project_component_registry`, `iteration_manifest_contract`, `system_map_layout`, `system_map_projection`, `human_knowledge_surfaces`). INV-08 enforces this closure continuously. Classification: **documentation ambiguity resolved by the invariant**, not a defect.

**F4. Stale generated counts — closed at Line B.** Foundation census/deep-adjudication/nonfunction outputs and the path manifest drift whenever tracked paths change; Line B repaired the drift to a fixed point via canonical generators (63/63). INV-11 + the external validator references keep this monitored. Classification: **real defect, repaired in Line B**.

**F5. Contradictory current-state claims — guarded.** The current-truth projection excludes non-terminal tasks (`_non_terminal_tasks_excluded`), and INV-02/INV-04 verify no open candidate appears as accepted/current. Task 115, PR #189 and R2 are nowhere represented as accepted. Classification: **clean at this head**.

**F6. Missing propagation routes — one candidate-only gap.** Research Executive OS (Task 115) is a Draft candidate: its integration adapters reference L0–L6/Function OS/Q12/Q13/claim governance/language-thought read-through, but no accepted propagation route exists yet because the capability is not accepted. This is a **candidate-only gap**, correct for the phase; it becomes a real obligation only if/when Task 115 proceeds toward acceptance.

**F7. Acceptance/current bypass paths — blocked by construction.** The path-classification engine forces every tracked path through classification (UNRESOLVED must be zero), the AUTHORITATIVE allowlist is restricted, and terminal tags + the merged ledger are the only acceptance evidence (INV-02/03/07). No file-name or timestamp route to acceptance exists in the checked machinery. Classification: **clean**.

## Separation of finding classes

- real defect repaired: F4 (Line B);
- documentation ambiguity resolved by invariant: F3;
- candidate-only gap: F6;
- historical residue: none materialized as state (old drafts tracked as unknown, see disposition report);
- false positives avoided during calibration: strict system-map membership (justified non-projections) and llms.txt prose labels — both bound to exact files and re-encoded as rules.
