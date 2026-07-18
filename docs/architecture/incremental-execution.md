# Incremental Execution and Selective Materialization

Status: `121Q32I / method 1.3.0 Draft candidate`. Method 1.2.0 and system map 0.2.0 remain Current. Q32I is not independently reviewed, accepted, merged or Current.

## Purpose and authority

Q32I adds a repository-level execution layer after Current typed change propagation. Its authority chain is:

`change request -> propagation closure -> component profiles -> deterministic planner -> NonImpactProof / rebuild decisions -> structured executor -> unified validator -> rollback or recovery evidence`

This chain governs declared repository dependency and materialization. It does not identify real-world causality, prove that the registries exhaust the project, or add L7.

The production entrypoints are:

- `tools/operations/generate_component_profiles.py` and `validate_component_profiles.py`;
- `tools/operations/plan_incremental_execution.py`;
- `tools/operations/run_incremental_execution.py`;
- `tools/operations/validate_incremental_execution.py`;
- `tools/operations/validate_phase_d_closeout.py` and `validate_phase_e_candidate.py`.

## Planner and NonImpactProof

The planner resolves real changed paths through the component registry and typed topology. Every registered component receives exactly one decision. Affected automatic components rebuild; affected manual/external components revalidate or require attestation. A component may receive `NO_CHANGE_WITH_PROOF` only when it is outside the declared closure and its proof binds the component, plan hash, authority fingerprint, traversed/excluded relations, fingerprint policy, recheck condition and claim ceiling.

Unknown paths, unresolved residue, missing profiles or changes to registry, topology, profile policy, generator, planner, executor, validator or core schemas fail closed as `FULL_REBUILD_REQUIRED`. Q32I changes those authorities, so its self-hosting plan correctly assigns full rebuild to every component.

## Executor, cache and recovery

Authority type and local execution capability are independent. Every production profile is explicitly `automatic`, `validation_only`, `manual`, or `external_attestation`. Only `system_map_projection` is currently automatic: its deterministic producer materializes both the JSON projection and SVG from registry, topology, and layout inputs. `pages_pipeline` and `propagation_calculator` are validation-only; workflow deployment and parameterized closure production cannot be impersonated by unrelated legacy builders.

The executor is dry-run by default. Before apply performs any producer, validator, output, cache, or recovery write, the unified production validator completes a fail-closed authority preflight over schema/hash, decision cardinality, closure/order, execution capability, registry/topology/profile identity, argv/cwd/input/output identity, NonImpactProof, lifecycle, scope, path, symlink, and worktree boundaries. Apply accepts only profile-registered argv arrays and always uses `shell=False`; caller-supplied commands are not authority. Repository-relative inputs, outputs, profile paths, cache paths, working directory, recovery targets and symlink resolutions must remain inside the authorized repository. Producers may write only registered outputs.

Cache is a performance layer, never a second truth source. Reuse requires an intact manifest and exact identity across profile schema/registry, component registry, topology, producer, validator, plan, authoritative inputs and generated outputs. Any mismatch becomes a miss or validator rejection.

Execution stops at the first failure. Apply snapshots the complete supported repository state before producer execution. Rollback removes newly created unregistered objects and restores modified/deleted pre-existing unregistered files, directories, symlinks, bytes, type, and mode. `restored` is emitted only after exact before/after comparison; any mismatch is `unrecovered` and requires a recovery package. Recovery evidence does not authorize lifecycle promotion.

## Unified validation and lifecycle boundary

The unified validator independently checks profile coverage, path confinement, plan cardinality and hash, affected decisions, proof bindings, execution order and command identity, cache integrity/identity, rollback/recovery consistency and stable error codes. The promoted production probes add one clean-worktree profile materialization test, seven complete-rollback tests, and nine preflight zero-side-effect rejection tests; manual, validation-only, and external profiles never start a producer.

Candidate objects cannot claim Accepted, Merged or Current, cannot cite their own current HEAD as their validity premise, and cannot mix Q33-Q40, lab, shadow or unauthorized Phase E assets. Exact commit IDs may be recorded only as observed identifiers. Independent review remains a separate future action.

## Compatibility and claim ceiling

Method 1.2.0 remains Current and fully valid without invoking the 1.3 candidate executor. Critical gates may always force full rebuild. Manual and external-attestation components remain non-automatic. No cache hit, test pass, CI run, artifact, graph edge or successful materialization upgrades factual, causal, proof, governance or lifecycle status.

Claim ceiling: deterministic repository planning, execution and recovery evidence under declared authorities only; no causal identification, completeness, acceptance, merge or Current claim.
