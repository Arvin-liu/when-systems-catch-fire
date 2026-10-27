# 121Q13 Attention, Distribution, And Compression Report

Status: `READY_AS_ATTENTION_DISTRIBUTION_CONTROL_CANDIDATE`

## What Changed

121Q13 adds three control surfaces on top of 121Q12:

- Attention and attractor control: records IterationDelta and detects no-information-gain loops.
- Distribution and decision collapse control: records samples, hypothesis distributions, and action collapse without promoting them to truth.
- Compression integrity gate: audits whether high-frequency terms can expand, generate questions, reduce burden, and continue inquiry.

These controls do not change L0-L6, Ψ0, Function OS, Charter Gate, or the claim ceilings established by 121Q12.

## Step Evidence

- Step 000: baseline and overlap audit from PR #47 head `338cfff999e26dce623c6c55d810587db4a668ba`.
- Step 001: IterationDelta schema, attractor taxonomy, and three read-only attention audits.
- Step 002: SampleEnvelope, HypothesisDistribution, DecisionCollapseRecord, NarrativeProvenanceLedger, and Action / Claim / Scale thresholds.
- Step 003: ChunkAudit schema, five high-frequency term audits, architecture integration, validator, report, and seal.

## Guardrails

The implementation records that:

- AI samples are not fact evidence;
- action decisions are not mechanism truth;
- new terminology is not theory upgrade;
- repeated same-context outputs are not independent evidence;
- CI success is not theory success.

## Claim Ceiling

The local claim ceiling is `schema_validated` after the 121Q13 validator passes. Remote workflow success can only support `workflow_passed` for the specific run and head SHA.

The real-world effect of these controls remains pending later use, review, and external feedback.
