# Proposal A — Minimal Observable, Bounded Cognitive Evolution Chain

**Scope:** Design only. This proposal defines one auditable chain from an existing model snapshot through a revision and one held-out successor use. It does not authorize an experiment or establish general cognitive inheritance.

## 1. Minimal chain and provenance objects

Represent each object as immutable, with a stable ID and content digest. Relations are explicit records linking object IDs; each relation records who asserted it and when.

| Object | Minimum contents | Required relations |
|---|---|---|
| **M0 — baseline snapshot** | Snapshot ID and digest; claim/rule IDs; applicable scope and context. | Starting point for the revision. |
| **E — observed evidence** | Actual input, output, and relevant conditions; source and capture method; timestamp; digest of the preserved evidence. Identify the specific M0 claim it supports or contradicts. | `supports` or `contradicts` → M0 claim. |
| **R — revision operation** | Operation type; affected claim IDs; evidence IDs; rationale; explicit semantic change. | `based_on` → M0; `uses_evidence` → E. |
| **M1 — revised snapshot** | New snapshot ID and digest; explicit change set; scope. M1 is a new version, never an overwrite of M0. | `derived_from` → M0; `implements` → R. |
| **U — fresh successor use** | Successor instance; exact M1 digest and input digest; protocol; frozen successor output and digest. Record that the successor had no access to the held-out answer or outcome before its output was frozen. | `consumes` → M1. |
| **O — held-out outcome** | Predeclared criterion and baseline; evaluator and method; held-out case reference and digest; outcome and supporting evidence. | `evaluates` → U; `tests` → the targeted claim or change in M1. |

Evidence and relation records must bind to the actual preserved bytes. Keep the successor output frozen before revealing or recording O. A result from this one chain supports only a bounded claim about this use and outcome.

## 2. Revision operation semantics

Every operation creates a new versioned claim or snapshot and preserves the prior record and its provenance.

- **Update:** Change a claim’s content while keeping its stated scope. Record the semantic delta and evidence that motivates it.
- **Narrow boundary:** Restrict a claim to a smaller, explicit scope. Link the new claim with `narrows` or `supersedes`; leave excluded contexts unresolved unless separate evidence supports a rule for them.
- **Split / coexist:** Split a claim into scoped variants when evidence supports different contexts. If evidence does not resolve competing interpretations, preserve them as coexisting claims and mark the ambiguity.
- **Reject / retire:** **Reject** a claim when the defined evidence/test contradicts it; **retire** one when it is no longer applicable under a stated scope or condition. Preserve the claim, reason, and evidence with a rejected or retired status.

A wording-only rewrite is not a revision operation. It must not silently change, remove, or replace the claim’s provenance or history.

## 3. Bounded interpretation

The minimum chain is one M0, one actual E package, one R, one M1, one fresh U, and one O. Record outcomes as pass, partial, fail, or indeterminate against criteria declared before U. A failed or incomplete chain is not evidence of successful transfer; a successful single chain does not establish general inheritance or promotion.

---

No shared repository state was inspected or changed, and no GitHub contact or experiment was performed.
