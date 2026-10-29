# Object–Relation–Mechanism Model / 对象–关系–机制模型(九原语合同)

Status: DRAFT SCAFFOLD (stacked on production/ignition-run-promote-evolve-r1 @ 6723cdfa) — not a Current capability

This document is the **nine-primitive object-model contract** of the Adaptive Relational Runtime (ARR) R1 scaffold (Plane 2, plus the Plane 1 Source/Observation boundary). It is a Draft/candidate scaffold contract, not a Current capability, not a validated model of any real domain, and not evidence of scientific or causal validity. It defines the smallest cross-domain primitive set; domain-specific types must live in versioned registries or controlled extension namespaces — this contract builds no giant ontology.

## Boundary rules

- Nine primitives only: Source, Observation, Object, State, Event, Assertion, Relation, Mechanism, Action. Every record has exactly one `record_kind`; one record can never play two layers at once.
- `source bytes/reference ≠ observation ≠ interpretation ≠ assertion ≠ mechanism`. Cross-layer reference uses `*_ref` pointers only; lower-layer content is never embedded.
- UNKNOWN is a first-class outcome: any missing, malformed or undecidable field degrades to UNKNOWN or explicit `null` — never to a guess.
- Stable interoperability objects are closed (`additionalProperties: false`); extensions require an `x_`-prefixed key registered in the extension-namespace registry.
- Adjacency, recurrence, similarity, embedding distance, centrality and repetition are never promoted to causality, truth, importance, value or evidence independence inside this model.

## 1. Shared envelope (12 fields, closed)

Every primitive record carries the same closed envelope:

| Field | Type / rule | Meaning |
|---|---|---|
| `record_id` | string, `<prefix>_<32 hex>` (§3) | deterministic identity derived from canonical content + declared scope |
| `record_kind` | enum, one of the nine primitives | the unique primitive layer this record plays |
| `schema_version` | string, e.g. `arr-r1.0` | schema contract version (registry-tracked) |
| `scope` | object `{domain, context_ref}` | declared scope in which the record holds; participates in identity |
| `provenance` | array of nonblank strings, minItems 1 | provenance chain (repository-native nonblank rule) |
| `explicitness` | five-level enum (§5) | explicitness of this record relative to its sources |
| `claim_ceiling` | nonblank string from the ceiling vocabulary | claim ceiling (reuses Foundation/MCF/`epistemic.py` vocabulary; e.g. `PRIMARY_VERIFIED` / `SECONDARY` / `UNKNOWN`) |
| `uncertainty` | nonblank string | natural-language statement of uncertainty; bare numbers are forbidden |
| `alternatives` | array of strings | competing interpretations not ruled out; minItems 1 under `INTERPRETER_RECONSTRUCTION` |
| `lifecycle` | object `{state, entered_at_scope, transition_ref}` | lifecycle state from the ten-state vocabulary (state machine itself is owned by the evidence/lifecycle plane) |
| `time` | object (§4) | six-time-scale sub-object; per-primitive required/forbidden fields |
| `extensions` | object, may be empty | only `x_`-prefixed keys, each registered (§7) |

The envelope is `additionalProperties: false` at every level. Identity hashing input excludes `record_id` itself and the declared runtime-annotation fields (`lifecycle.entered_at_scope`; a registered `extensions.x_provenance_ingest` if it exists); **everything else — including `time`, `provenance`, `scope` — participates in identity**. There are no exemptions beyond this declared list.

## 2. The nine primitives

### 2.1 Source

A typed reference to external material (text, audio, image, video, code, commit, PR, CI, structured data, runtime receipt, institution, declared real-world event). A Source answers "where are the bytes, what are they, whose are they" — never "what did I observe".

Required beyond the envelope: `source_type` (registry enum), `content_hash` (64-hex sha256; private corpora store hash only), `locator {ref_type, ref_value}` (`ref_type ∈ {git_commit, git_blob, url, doi, repo_path, external_ref}`; a bare filesystem path alone is never an identity), `tier ∈ {PRIMARY, SECONDARY_DERIVED, DERIVED_COMPUTED}`, `rights_boundary` (§6), plus `time.publication_time` (nullable).

Forbidden: observation-time fields, interpretation fields, any evaluative field.

### 2.2 Observation

The product of one collection/read act upon a Source. One Source may be referenced by many Observations with distinct observation provenance.

Required: `source_ref` (missing → fail closed), `observer` (role or service name, not natural-person private data), `raw_excerpt {kind: inline|hash_only|none, value}` (private corpora force `hash_only` or `none`), `collection_metadata {method, tool_ref, parameters}`, `time.observation_time` + status.

Forbidden: interpretation or assertion content.

### 2.3 Object

A typed entity objectivized out of Observations, usable as a Relation/Assertion endpoint. The "noun slot"; carries no truth.

Required: `object_type` (object-type registry), `observation_refs` (minItems 1), `canonical_repr` (objectivized canonical representation; key-sorted into identity).

Forbidden: truth/causality/importance fields; embedding distances, centrality and similar derived quantities may only appear as declared derived attributes of Relation/Assertion.

### 2.4 State

A condition snapshot of one or more Objects holding over a persistent interval.

Required: `object_refs` (minItems 1), `state_variables`, `activation_ref` (Event ref or null), `time.validity_interval` (required). PSD semantics additionally require a declared system boundary (owned by the projection plane).

### 2.5 Event

A localized, bounded occurrence under an observer frame.

Required: `object_refs` (minItems 1), `event_type` (registry), `time.event_time` (nullable but then explicitness degrades to UNKNOWN), `observer_frame`. Optional `duration`; carrying a duration does not turn an Event into a State.

Forbidden: `validity_interval` (that is a State field).

### 2.6 Assertion

A propositional claim about Objects/States/Events; the only "sentence slot" carrying explicitness judgment and claim-ceiling semantic load.

Required: `subject_refs` (minItems 1), `assertion_type` (registry), `proposition` (nonblank), `explicitness` with the §5 judgment rule, `evidence_refs` (may be an explicit empty array — never omitted).

Conditional (schema-enforced): `explicitness = INTERPRETER_RECONSTRUCTION` ⇒ `speaker_commitment = attributed_by_interpreter`, `alternatives` minItems 1, and `reconstruction_basis {method, from_observation_refs}` required; `PLAUSIBLE_ASSUMPTION` ⇒ `reconstruction_basis` required and `alternatives` minItems 1. An interpreter reconstruction is never written as a verified speaker belief; `speaker_commitment ∈ {asserted_by_speaker, attributed_by_interpreter, unknown}` is machine-checkable at schema level.

### 2.7 Relation

A typed relation connecting two or more endpoints; carries no causal/truth/value judgment by itself. Causal semantics only ever enter via an MCF handoff record; a generic Relation can never set `causal_status=established` (the field does not exist).

Required: `relation_type` (registry), `endpoints` (array of `{role, ref}`, minItems 2; endpoint order does not participate in identity — endpoints are normalized by (role, ref) lexicographic order), `directionality ∈ {directed, undirected, bidirectional, unknown}`, `temporal_scope {interval, activation_ref}` (nullable), `causal_handoff_ref` (nullable; non-null points at an MCF handoff record without the Relation itself asserting any causal conclusion).

Forbidden: `repetition_count`, `centrality`, `similarity_score` as first-class fields; if genuinely needed they live only under registered `extensions.x_*` with a declared claim ceiling. Higher-order relations (an endpoint referencing a Relation) must never silently collapse into pairs.

### 2.8 Mechanism

An executability description of "how inputs become outputs" — a mechanism contract, not an execution. Execution belongs to Function OS / the production runtime.

Required (seven-element contract, all required): `mechanism_type` (registry), `input_contract` (missing → fail closed), `output_contract`, `executable_surface {kind: function_os_capability|deterministic_stub, target}`, `preconditions`, `side_effects`, `rollback` — the last three are explicit arrays/objects whose empty value means "none"; an undeclared side effect realized at run time is a rejection — plus `claim_ceiling` from the envelope and `adapter_capability_ref` (nullable; unregistered capabilities cannot execute).

Forbidden: embedded executable code; any reference to PROMOTE/EVOLVE paths.

### 2.9 Action

A proposed, decided or pending action intent inside Charter/governance boundaries. An Action is not an execution receipt; execution results only re-enter the model as `runtime_receipt`-typed Sources plus Observations.

Required: `action_type` (registry), `mechanism_ref` (nullable), `authorization_ref` (nullable; any PROMOTE/EVOLVE-semantics `action_type` forces non-null pointing at an explicit human authorization record), `execution_ref` (nullable; always null inside this scaffold — no real execution).

Forbidden: execution-result fields; self-coined PROMOTE/EVOLVE vocabulary.

## 3. Deterministic identity

`record_id = <kind_prefix>_<first 32 hex of sha256(canonical_bytes)>` with prefixes `src_ / obs_ / obj_ / sta_ / evt_ / ast_ / rel_ / mec_ / act_` (envelope and registry items: `env_ / reg_`), reusing the `tools/ignition_runtime/hashutil.py:deterministic_id` convention.

Canonicalization rules (all mandatory):

1. Unicode NFC normalization for all strings.
2. Trim and internal whitespace folding (prose fields only; hash/ref/enum fields stay verbatim).
3. Recursive key sorting; compact separators.
4. Set-semantics arrays (`endpoints`, `provenance`, `observation_refs`, `evidence_refs`, `alternatives`, `object_refs`, `subject_refs`) are element-canonicalized then sorted before hashing (order-independent); sequence-semantics arrays keep declared order and must be registry-marked `order_semantic: true`.
5. Integers verbatim; floats are forbidden in identity — decimal-looking quantities are stored as strings with a declared scale.
6. `null` and absent are distinct at canonicalization; nullable fields are given explicitly as `null`, never defaulted.

Identity never depends on list order, runtime/wall-clock timestamps, or filesystem paths alone. Identical canonical content + scope ⇒ identical ID (natural dedupe); identical `content_hash` with different collection metadata ⇒ one Source plus several Observations.

## 4. Six time scales

| Field | Owner | Meaning |
|---|---|---|
| `event_time` | Event (required) | occurrence time under the observer frame |
| `publication_time` | Source (nullable) | the source's own publication time; never guessed from URL/filename |
| `observation_time` | Observation (required) | collection time; not forced ≥ event_time (an inversion yields an UNKNOWN Assertion, not an error) |
| `ingestion_time` | all primitives (required) | ingestion time of this record; caller-supplied, never auto-filled from wall clock; participates in identity |
| `validity_interval` | State (required), Relation.temporal_scope (nullable) | validity interval `{start, start_inclusive, end, end_inclusive}`, default left-closed right-open |
| `execution_time` | only inside runtime_receipt-typed Sources | real execution start/end; this scaffold never produces it, only consumes it by typed reference |

Every time field carries a sibling `<field>_status ∈ {OK, ABSENT, MALFORMED}`. Any parse failure ⇒ value set to `null` + status `MALFORMED`; no heuristic guessing (no filename dates, no git author dates, no mtimes). Malformed temporal metadata routes downstream as UNKNOWN and never participates in time-respecting path judgments. `start > end` (when comparable) ⇒ reject; incomparable ⇒ the whole field is marked malformed.

## 5. Explicitness (five levels)

`EXPLICIT / STRONGLY_IMPLIED / PLAUSIBLE_ASSUMPTION / INTERPRETER_RECONSTRUCTION / UNKNOWN`

- `EXPLICIT`: every substantive content of the proposition corresponds verbatim to referenced Observation raw content.
- `STRONGLY_IMPLIED`: derived via a fidelity-preserving rule registered in the explicitness-rules registry, with the rule itself present as an EXPLICIT Assertion.
- `PLAUSIBLE_ASSUMPTION`: interpreter-introduced assumption; `reconstruction_basis` required; `alternatives` minItems 1.
- `INTERPRETER_RECONSTRUCTION`: reconstruction of unspoken argument structure; `reconstruction_basis` required; `alternatives` minItems 1; concrete `uncertainty` required; `speaker_commitment = attributed_by_interpreter` (schema-enforced).
- `UNKNOWN`: explicitness undecidable / material missing / temporal malformed / any degradation exit.

The judgment takes the lowest level whose conditions are all met (rather low than high). Explicitness can only degrade; an upgrade requires new Observation evidence and a new Assertion, with the original Assertion going SUPERSEDED (history preserved). Source/Observation/Object records narrow the enum to `EXPLICIT | UNKNOWN` (these layers produce no interpretation).

## 6. Source tier and rights_boundary

Tier vocabulary: `PRIMARY` (original material), `SECONDARY_DERIVED` (secondary/interpretive), `DERIVED_COMPUTED` (in-system computed products whose provenance must point at the producing Mechanism + input refs). Generalized from `ignition_runtime/unknown.schema.json` tier vocabulary; the migration mapping lives in a registry.

`rights_boundary` (required on Source):

```
{ classification: public | private_corpus | copyrighted_excerpt | internal_only,
  republication: allowed | hash_only | paraphrase_only | prohibited,
  paraphrase: string | null,        # required when paraphrase_only; ≤ 280 chars; original writing
  attribution_ref: string | null,
  notes: string | null }
```

Rules: `private_corpus` forces `republication ∈ {hash_only, paraphrase_only}` and forces Observation `raw_excerpt.kind ∈ {hash_only, none}`; a paraphrase is an independently written short restatement (no ≥ 15-word contiguous excerpt); public fixtures referencing private corpora carry only the triple {content hash, typed reference, paraphrase}; missing classification ⇒ fail closed (treated as `internal_only` and reported at validation).

## 7. Extension namespace

1. Extra fields live only inside `extensions`, keyed `x_[a-z0-9_]+`.
2. Every `x_*` key must be registered in the versioned extension-namespace registry `{key, owner, semantics, schema_ref, claim_ceiling_default}`; unregistered keys are rejected.
3. `x_*` fields do not participate in identity unless the registry entry declares `identity_relevant: true`.
4. All stable interoperability objects (nine primitives + envelope + registry items) are `additionalProperties: false`.

## 8. State vs Event discrimination

Applied in order, first hit decides:

1. Persistence: subject is a condition holding over an interval ⇒ State; a bounded occurrence ⇒ Event.
2. Fields: has `validity_interval` ⇒ State; has `event_time` ⇒ Event. The two fields are mutually exclusive in one record.
3. Causal role: States carry maintenance/decay/termination conditions and an activation event; Events have occurrence time (optional duration is not persistence).
4. Undecidable ⇒ record an Assertion with `explicitness = UNKNOWN` describing the ambiguity; never hard-pick one.
