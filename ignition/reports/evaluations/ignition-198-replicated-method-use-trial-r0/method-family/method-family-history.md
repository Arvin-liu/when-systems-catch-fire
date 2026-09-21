# Task198 Method Family History — bounded replay contrast

This is a task-local synthetic method-family history for the replicated
preparation. It reuses Method-Use Trace R0; it is not a new schema, registry,
ontology, capability claim, or causal model.

## Candidate

`method:bounded-replay-contrast-r0` is a bounded probe that holds a synthetic
input constant, resets the local state when the case permits it, and compares a
predeclared discriminating observation across two local explanations. The
probe is useful only when the observation can be recorded without importing
external facts.

## Selection history

The candidate is selected when a case contains a repeated or repeatable local
input and two plausible local explanations that can be separated by a bounded
observation. A single snapshot explanation and a wording-only template are
alternatives, not substitutes for a recorded replay. The selection preserves
unknowns when the discriminating measurement is absent.

## Context constraints

- use synthetic case facts only;
- hold the named input constant when the case record permits it;
- keep observed facts separate from the expected discriminating observation;
- retain missing measurements and failed runs as recorded;
- do not attribute a difference to the method, claim general inheritance, or
  promote the trace into canonical knowledge.

## Case-specific application prompts

These are application constraints, not case answers. The future trace must
record the observed outcome from the corresponding facts source.

### REPL-CASE-01

Hold token `K7` constant and compare the two lane counters together with the
selector marker. A discriminating observation would require a replay-consistent
lane difference plus an independently captured pre-input `R` measurement. The
missing pre-input value and missing internal route read remain open.

### REPL-CASE-02

Hold batch `B3` constant and compare payload delivery, acknowledgement register,
and watchdog state within the four-tick window. A discriminating observation
would locate the acknowledgement boundary if the relevant event is recorded.
The recorded watchdog expiry remains a failure observation, not an inferred
cause.

### REPL-CASE-03

Hold `fold=2` constant across reset and compare primary cell, shadow cell, and
the delayed read channel. A discriminating observation would require a direct
read-channel source measurement between the immediate and delayed reads. The
repeated cell state and the read-channel boundary remain separate records.

## Revision boundary

If the discriminating observation is absent, retain `UNRESOLVED`. If the
bounded run reaches a recorded failure before the observation, retain the
failure and mark the application for `REVISE`. If the bounded observation is
available without a new contradiction, `NO_REVISION` may describe the trace,
but causal attribution remains `NOT_ESTABLISHED`.
