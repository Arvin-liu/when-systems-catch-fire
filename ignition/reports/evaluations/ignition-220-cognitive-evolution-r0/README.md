# IGNITION-20260926-220 — Cognitive Evolution R0 preparation

**Status:** design and freeze preparation only. This package does not launch a revision agent, transfer Successor, or Evaluator.

## Bounded question

Given an initial method `M0` and a source-bound failure/counterexample that exposes a boundary defect, can an independent revision agent produce a bounded `M1` that changes only what the evidence licenses, preserves unaffected `M0` scope, records explicit `M0 → evidence → M1` lineage, and enables a fresh successor to make better held-out decisions than `M0` alone or `M0` plus raw failure evidence without an explicit revision artifact?

This exploratory preparation adds a third proposed architecture layer:

`Representation → Cognitive Method → Cognitive Evolution`

The intended result is limited to three synthetic families and a future frozen protocol. It does not test autonomous recursive self-improvement, weights, model training, cross-model transfer, or real-world validity.

## Scientific premise

Task219-R2 is recorded in [TASK219-SCIENTIFIC-PREMISE.md](TASK219-SCIENTIFIC-PREMISE.md). Its method-dependency result is partial, runtime metadata is insufficient to assess confounding, and it does not establish general cognitive inheritance or a causal method-artifact effect. R1 and cross-model transfer are not authorized.

## Package layout

- `design/`: five independently prepared read-only proposals and the post-proposal disagreement register.
- `families/`: exactly three synthetic `M0` / `E1` family designs.
- `revision/`: neutral revision prompt, output schema, six opaque future-only manifests, and sealed revision targets.
- `transfer/`: neutral prompt, output schema, deterministic packet-construction template, and sealed transfer targets/condition-map template.
- `evaluator/`: condition-neutral criteria and the preregistered outcome rule.
- `freeze/`: content inventory and its digest sidecar.
- `validation/`: task-local hard-gate validator and its report.

Held-out case files and sealed targets are excluded from every future revision manifest. The final eighteen transfer packets will not be instantiated until six actual revision outputs exist. Future task templates are preparatory contracts only; all execution counts are zero at this freeze.

## Authority boundary

- Revision agents launched: `0`.
- Transfer Successors launched: `0`.
- Evaluators launched: `0`.
- Runtime/model/provider/reasoning effort/speed mode selected by Task220: `false`.
- R1, cross-model transfer, Ready, merge, and canonical promotion: not authorized.

The Formal anchor is `Arvin-liu/when-systems-catch-fire` PR #234 head `1f7286515768347a2a3a131dd0f6de87f631676c`; the Task220 branch is stacked on that exact head and targets the Task217 branch. This remains an Open + Draft + unmerged review artifact until Owner/GPT review.
