# Task 111 — Apple/Gravity Historical Evidence Preregistration

Status at registration: `PREREGISTERED_BEFORE_OUTCOME_RESEARCH`.

This document fixes the historical questions, source policy, adjudication
categories and claim ceiling before any new outcome-bearing historical source
is consulted. A result commit may use only sources whose metadata, access time,
stable locator and relevant fragment are recorded after this preregistration.

## 1. Primary question without an assumed answer

For the proposition represented by `C(apple_fall, gravitational_theory)`, what
bounded historical claim is actually supported by reliable records?

The following questions must stay separate:

1. What does the existing apple narrative assert about Newton, the apple story
   and the development of gravitation?
2. What narrower proposition, if any, can be tested without turning a story
   into a universal causal law?
3. What does the repository expression `C(apple_fall, gravitational_theory)`
   operationally denote, if anything, in the current repository?
4. Does any current Pointfire or Function OS component claim to output a
   historical causal judgment for that exact input, and what interface would it
   accept?
5. Is any apparent failure located in factual premise, historical
   interpretation, formalization fidelity, runtime execution, causal
   interpretation or later narration?

No answer category is selected in advance. The existing prose is a hypothesis
and a source lead, not an adjudicated answer.

## 2. Source inclusion policy

Acceptable primary or near-primary source classes:

- Newton's own published works, correspondence or contemporaneous records,
  where the relevant passage is directly identifiable;
- early biographical or witness records with author, date, edition and stable
  bibliographic identity;
- authoritative scholarly editions, peer-reviewed historical scholarship or
  institutional collections that identify and critically discuss the primary
  record;
- authoritative reference works used only as contextual corroboration, never
  as the sole support for a strong historical conclusion.

Popular retellings, blogs, unsourced summaries and search snippets may be
logged as context or exclusion evidence but cannot be the sole authority for a
positive or negative historical finding.

## 3. Search and selection protocol

Search the bounded topic using combinations of Newton, apple, gravity,
gravitation, falling apple, Woolsthorpe, Cambridge, Hooke, Halley, Principia,
early biography and the relevant edition/collection identifiers. Record the
query or catalogue path, source class, author, title, date, edition, stable URL
or identifier, access timestamp, relevant page/location and a short fragment
or paraphrase.

Include a source only when it bears directly on the five questions above or
provides necessary provenance for a directly relevant primary record. Exclude
material that only repeats the popular story without independent provenance.

## 4. Adjudication categories

Each atomic historical proposition receives one of:

- `EVIDENCE_SUPPORTED_WITHIN_SCOPE`;
- `EVIDENCE_PARTIAL_OR_DISPUTED`;
- `EVIDENCE_CONTRADICTED`;
- `EVIDENCE_INCONCLUSIVE`;
- `EVIDENCE_INVALID` when the material cannot support the proposition.

Each proposition also records uncertainty, source class, direct/indirect status,
competing interpretations and the exact claim ceiling. No binary verdict is
forced where the record supports only a nuanced or disputed account.

## 5. Executable-target boundary

Historical evidence does not preregister or create an executable Pointfire
truth oracle. The repository target audit is a separate dimension. If no
existing component can faithfully accept the historical proposition and emit a
bounded causal judgment with output and trace, the result is
`EXECUTABLE_TARGET_ABSENT` or `TARGET_OUT_OF_SCOPE`; no new general causal
engine may be built for this task.

If a valid existing target is found, a separate reproduction preregistration
must be committed and remotely proven as an ancestor before target output for
the apple case is inspected.

## 6. Claim ceiling

The historical result may establish only the bounded status of the apple-story
proposition and its role in the development or narration of gravitation. It
may not establish a general theory of scientific discovery, genius, causality,
historical explanation, or the external truth of Function OS output.

## 7. Stop conditions and deviations

Stop the historical search when the bounded questions have at least one
primary/near-primary source path or when the available record is demonstrably
inconclusive. Do not expand into a general history of Newton, a complete
biography or a general theory of causality. Record failed searches, unavailable
sources, language/edition limitations and disagreements as limitations rather
than filling them with inference.

Any deviation from source classes, question scope, search boundary, quote
handling or adjudication categories must be recorded before using the deviating
material and must not silently upgrade the result.

## 8. Reproducibility and pre-query seal

- registration control: `b0f4ebe660de10e09f88ee524e9947243c80e0cc`;
- formal base: `dddd5fec01abb69a61993c93104214425fca4791`;
- preregistration branch: `agent/ignition-failure-case-evidence-gate-real-defect-reproduction-r1-20260801`;
- output-bearing historical research is forbidden until this file is present
  on the remote branch and proven as an ancestor of every historical result
  commit;
- raw source metadata and adjudication records will remain append-only; the
  original case Markdown and task-109/110 outputs will not be edited.
