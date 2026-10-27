# Task 111 — Executable Target and Formalization Audit

## Frozen search boundary

The audit was run against formal `main` at `dddd5fec01abb69a61993c93104214425fca4791`,
after the historical preregistration commit had been pushed and verified as an
ancestor of the task-111 result branch. The audit covered the tracked
`case_failures/` library, Function OS v0.1 and v0.2, the Function OS tests and
the repository's causal/operation tooling. It did not add a new evaluator in
order to make the case reproducible.

The tracked case inventory is exactly:

- `case_failures/README.md`
- `case_failures/examples/README.md`
- `case_failures/examples/apple_gravity_failure.md`
- `case_failures/examples/cross_domain_synergy_risk.md`
- `case_failures/examples/technology_economic_growth_failure.md`

The case files contain narrative fields only. No case file supplies a target
commit, an exact governed input, an observed output, a run ID, a trace, an
oracle, a repeat count or a regression test.

## Candidate target inventory

| candidate | actual interface | result of audit |
|---|---|---|
| Function OS v0.1 N1–N9 | Parses and interprets bounded function specs, stores artifacts and feedback | Symbolic candidate pipeline; no apple case runner, historical corpus, causal evaluator or external oracle. Not a valid target for this claim. |
| Function OS v0.2 N1–N9 | `FunctionSpec` → symbolic representation → compiler/artifact → N5 interpreter → N6 trace → N7 validator → registry | Its scope contract is deterministic symbolic functions. N5 checks declared pre/postconditions and N6 records internal execution; a PASS is expressly not external truth. No apple case target exists. |
| v0.2 integration/benchmark tests | Addition, precondition failure, bounded benchmark fixtures and existing Function OS regression cases | No `apple_gravity_failure` input or historical-causal proposition. Existing benchmark defects and fixes concern Function OS's declared symbolic domain, not this case. |
| causal fabric / ARN / PSD tooling | Projectors, renderers, validators and model-internal maps | No executable historical truth oracle or case-specific apple target. These tools cannot convert a narrative label into a causal observation. |

The repository search found no case runner or prior run artifact, and no
Function OS path references `apple_gravity_failure`, `apple_fall` or a governed
apple-case input. The directory name and the original class value
`IMPLEMENTATION_DEFECT` are not target identity.

## Formalization finding

`C(apple_fall, gravitational_theory)` names a relation but does not specify:

- the event and time window;
- the counterfactual or intervention;
- the causal criterion and confounder boundary;
- the exact input representation;
- the accepted output domain;
- the external historical adjudicator; or
- how an internal trace would establish a fact about 1665–1727.

Function OS can execute a faithfully declared symbolic contract, but there is
no faithful contract here. The formalization status is therefore
`FORMALIZATION_UNDERSPECIFIED`, not `FORMALIZATION_FAITHFUL_WITHIN_SCOPE`.

## Final target status

`EXECUTABLE_TARGET_ABSENT`

No valid target was found or frozen for this case, so no output inspection was
performed and no reproduction run was started. The reproduction status is
`NO_REPRODUCTION_POSSIBLE_WITH_CURRENT_TARGET`. This is an evidence-gated
non-reproduction classification, not a task-level blocker and not a claim that
no future target could ever be designed.
