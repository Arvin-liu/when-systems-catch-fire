# Task 111 — Apple Case Historical Evidence Dossier

## Scope and gate boundary

This dossier is the post-preregistration historical review for the frozen
source `case_failures/examples/apple_gravity_failure.md`. It does not alter the
source file or the task-109/task-110 classification bytes. It evaluates only
what the cited historical record can support; it does not supply an execution
result for Function OS and does not manufacture a causal oracle.

The source's sentence that the story is “后人虚构” is an uncited narrative
outcome, not a recorded run. Its `Prediction` says `系统可能会输出 true`,
which is explicitly hypothetical. The evidence gate therefore treats the
original `IMPLEMENTATION_DEFECT` directory classification as unproven until a
versioned executable target, exact input/output, trace, oracle and regression
record exist.

## Propositions adjudicated

| proposition | bounded result | reason |
|---|---|---|
| H1. An early written memoir tradition reports that Newton associated an apple falling with a thought about gravitation. | `EVIDENCE_SUPPORTED_WITHIN_SCOPE` | Stukeley's memoir records a 1726 conversation; Conduitt's 1727 memoir copy carries a related account. Both are later memoir sources and therefore indirect. |
| H2. The popular details “the apple hit Newton” and “one instant discovered the complete theory” are established by those sources. | `EVIDENCE_INCONCLUSIVE` | The reviewed sources do not provide those details as a controlled observation. The timeline places later development, correspondence and publication between the anecdote and the completed theory. |
| H3. The apple observation was the sole direct causal trigger of the universal theory. | `EVIDENCE_INCONCLUSIVE` | The repository predicate has no defined counterfactual, time window, causal criterion or external adjudicator. A memoir report cannot answer that formal causal question by itself. |
| H4. The entire apple account is proven to be fabricated. | `EVIDENCE_PARTIAL_OR_DISPUTED` | The early memoir records make a wholly-fabricated classification too strong, while their provenance and later transmission do not establish every popular detail. |

The case-level external-evidence status is therefore
`EVIDENCE_PARTIAL_OR_DISPUTED`. This is a provenance-bounded result, not a
finding that the anecdote is true, false, or a scientific explanation.

## Source handling

`SOURCES.jsonl` records the source URLs, archive identities, retrieval time,
query context, bounded excerpts and limitations. The primary inputs are the
Newton Project transcriptions of Stukeley and Conduitt. The Newton Project
timeline, Haycock's catalogue introduction and the Royal Society catalogue
are used only as contextual or provenance controls. No search result snippet,
LLM output or uncited repository prose is used as historical evidence.

The historical evidence chain is:

1. Stukeley's diplomatic transcription reports the 1726 conversation and the
   apple/gravity recollection.
2. Stukeley's normalized record preserves his warning that the memoir combines
   personal knowledge and heard accounts.
3. Conduitt's early memoir copy supplies an independent-in-time transmission of
   the apple observation story, while remaining a later memoir rather than a
   contemporaneous note.
4. The Newton Project timeline separates the anecdote from the intervening
   development and 1687 publication of the theory.

## Claim ceiling

The evidence may support only this sentence:

> Later memoir sources report that Newton associated observing a falling apple
> with a thought about gravitation; the sources do not establish the popular
> impact detail or a sole direct causal trigger for the completed theory.

It may not be promoted to a Function OS `true`/`false` result, an empirical
causal law, a proof that the case is an implementation defect, or a statement
that the whole story is fabricated.

## Stop and uncertainty conditions

- Stop historical adjudication when the proposition exceeds provenance and
  bounded narrative scope; do not search indefinitely for a source that would
  turn a memoir into a controlled counterfactual.
- If a future run claims a defect, it must use a separately preregistered
  target and record the exact semantic proposition, not merely the string
  `C(apple_fall, gravitational_theory)`.
- Any change to the formalization, target commit, oracle, or historical claim
  ceiling invalidates the corresponding reproduction result and requires a new
  preregistration.
