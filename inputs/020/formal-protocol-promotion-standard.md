# Formal Protocol Promotion Standard
## 1. Purpose

Define a repeatable, evidence-backed gate for deciding when a protocol may be recommended for formal promotion to `formal_protocol`.

This standard does not itself change repository state. It only produces audit recommendations.

## 2. Scope

Applies to:
- the 12 meta-protocols under `docs/meta-protocols/` and `data/meta-protocols/`
- current candidate status `candidate_formalized`
- local audits performed on this machine

Does not apply to:
- Psi0 mathematics
- the official function table
- the official case table
- formal repository updates
- approval or commit actions

## 3. Status Model

- `candidate_formalized`: structurally defined but not fully gated for formal promotion.
- `machine_eligible`: passes the content, consistency, evidence, and conflict gates in audit output, but is not yet formally approved in the repository.
- `formal_protocol`: formally approved and reflected in the repository with traceable update history.
- `pending`: insufficient information for a reliable decision.
- `rejected`: clear evidence that the item is not a protocol-layer item.

## 4. Result Codes

- `PASS`: evidence is sufficient and condition is satisfied.
- `FAIL`: evidence clearly shows the condition is not satisfied.
- `PENDING`: evidence is insufficient for a reliable decision.
- `NOT_APPLICABLE`: the condition does not apply and the rule explicitly allows that outcome.
- `NOT_FOUND`: required source, field, or evidence is missing.

Rules:
- Missing evidence is never treated as `PASS`.
- Hard-gate `FAIL`, `PENDING`, or `NOT_FOUND` blocks `machine_eligible`.
- `NOT_APPLICABLE` is only allowed where explicitly declared by the gate.

## 5. Gate Types

- `hard`: blocks `machine_eligible` when not satisfied.
- `soft`: quality or maintainability guidance; does not by itself block `machine_eligible`.
- `governance`: required for `formal_protocol`, not for `machine_eligible`.

## 6. Hard Gates

### G01 Unique Protocol ID
- Purpose: ensure stable protocol identity.
- Object: `protocol_id`
- Rule: exists, format is valid, unique in Protocol layer, not confused with function/case numbering.
- Evidence: protocol index, machine data, document title.

### G02 Unique Chinese Name
- Purpose: prevent semantic duplication.
- Object: `title_zh`
- Rule: exists and is unique among protocols.

### G03 Unique English Name / Stable English Identifier
- Purpose: maintain cross-file consistency.
- Object: `title_en`
- Rule: exists and matches across document and machine data.

### G04 Valid Status Field
- Purpose: keep lifecycle states unambiguous.
- Object: `status`
- Rule: status is in allowed enum and consistent across document and machine data.

### G05 Normative Definition Exists
- Purpose: ensure the item is normative, not merely descriptive.
- Object: `definition`
- Rule: definition must specify allowance, prohibition, requirement, or constraint.

### G06 Constrained Object Clear
- Purpose: ensure the protocol has a target.
- Object: `constrained_object`
- Rule: protocol must specify what it constrains.

### G07 Trigger Conditions Clear
- Purpose: define when it becomes active.
- Object: `trigger_conditions`
- Rule: input/trigger conditions are explicit.

### G08 Result / Constraint Output Clear
- Purpose: define what happens when it applies.
- Object: `constraint_result`
- Rule: output, constraint, or allowed/forbidden effect is explicit.

### G09 Scope Clear
- Purpose: prevent overgeneralization.
- Object: `scope`
- Rule: applicable systems, levels, and scenarios are explicit.

### G10 Exclusions / Failure Conditions Clear
- Purpose: define stopping conditions.
- Object: `exclusions`, `invalid_conditions`
- Rule: non-applicability or failure conditions are explicit.

### G11 Boundary vs Neighbor Protocols Clear
- Purpose: avoid overlap.
- Object: `neighbor_protocols`
- Rule: at least one close boundary distinction is explicit.

### G12 Not a Plain Function Rename
- Purpose: protect layer separation.
- Object: definition and relation fields
- Rule: the item must be a constraint/permission/prohibition/meta-rule, not a mechanism function renamed.

### G13 Conflict / Priority Mechanism Clear
- Purpose: resolve overlaps.
- Object: `conflict_resolution`
- Rule: conflict handling is explicit or unresolved conflict is explicitly documented.

### G14 No Circular Definition
- Purpose: prevent self-referential dead ends.
- Object: definition and relation fields
- Rule: protocol does not rely solely on itself without external anchor.

### G15 Psi0 Mapping Clear
- Purpose: locate protocol in the frame.
- Object: `psi0_mapping`
- Rule: major and minor Psi0 component relations are explicit.

### G16 P_meta Relation Clear
- Purpose: connect protocol layer to generation layer.
- Object: `p_meta_relation`
- Rule: relation to `P_meta` is explicit.

### G17 Does Not Claim to Rewrite Psi0
- Purpose: preserve the frame.
- Object: definition / notes
- Rule: protocol may constrain or project through Psi0 but must not rewrite Psi0.

### G18 Function Layer Relation Clear
- Purpose: connect to function layer precisely.
- Object: `function_layer_relation`
- Rule: relation must be one of `constrain`, `permit`, `prohibit`, `generate`, `select`, `prioritize`, `terminate`, `validate`, `reference`, `other`.

### G19 Not Counted as Function
- Purpose: keep numbering domains separate.
- Object: repo indexes and machine data
- Rule: protocol is not counted in the formal function total.

### G20 Not a Duplicate of Existing Function
- Purpose: avoid layer confusion.
- Object: function-table cross-check
- Rule: if a close function exists, layer difference must be explicit.

### G21 Positive Evidence Exists
- Purpose: support usefulness or necessity.
- Object: `positive_evidence`
- Rule: at least one supporting case, material, or structure evidence exists, or a valid PENDING explanation is provided.

### G22 Boundary / Negative Evidence Exists
- Purpose: support falsifiability.
- Object: `boundary_evidence`
- Rule: at least one boundary case, counterexample, or failure condition exists, or a valid PENDING explanation is provided.

### G23 Case Relation Type Clear
- Purpose: avoid overstating evidence.
- Object: `case_layer_relation`
- Rule: relationship must be labeled `support`, `limit`, `falsify`, `boundary`, `illustrate`, or `pending`.

### G24 Source References Complete
- Purpose: enable traceability.
- Object: `source_references`
- Rule: definition and key judgments have traceable sources.

### G25 Evidence Path Available
- Purpose: enable reproducible audit.
- Object: document path, index entry, machine record path
- Rule: validator can point to file path and field or line evidence.

### G26 Assertion Level Explicit
- Purpose: separate internal inference from external proof.
- Object: `assertion_level`
- Rule: conclusion must not conflate framework inference, external fact, mathematical proof, and field consensus.

### G27 Independent Entry Exists
- Purpose: ensure formal presence.
- Object: protocol document and machine record
- Rule: each protocol has a unique main record.

### G28 Index Entry Exists
- Purpose: make the protocol discoverable.
- Object: `index_entry`
- Rule: protocol ID and name are retrievable from index or overview.

### G29 Machine Record Exists
- Purpose: support automation.
- Object: `machine_record_path`
- Rule: protocol exists in machine-readable data.

### G30 Key Fields Match
- Purpose: avoid doc/data drift.
- Object: document vs machine record
- Rule: ID, names, status, definition summary, Psi0 relation, function relation, and sources align.

### G31 Schema Valid
- Purpose: make machine validation repeatable.
- Object: machine record
- Rule: data validates against `formal-protocol-promotion.schema.json`.

### G32 No Blocking Conflict
- Purpose: prevent unsafe promotion.
- Object: all protocol fields and related records
- Rule: no unresolved ID, definition, status, hierarchy, or evidence conflicts.

### G33 Human Review Completed
- Purpose: require accountable review.
- Object: review metadata
- Rule: reviewer, review_date, review_decision, and review_notes are present for audit output.

### G34 Governance Approval Exists
- Purpose: require project-level approval for `formal_protocol`.
- Object: governance record
- Rule: explicit approval record exists before formal state change.

### G35 Formal State Change Is Recorded
- Purpose: ensure traceability of approval.
- Object: repository history
- Rule: protocol update, index update, machine data update, and tracked change record exist.

## 7. Soft Gates

### S01 Bilingual Definition Quality
- Check whether Chinese and English definitions are both readable and aligned.

### S02 Example Sufficiency
- Check whether examples are enough to understand the protocol.

### S03 Cross-Domain Interpretability
- Check whether the protocol can be explained across layers without collapsing into a function.

### S04 Relation Map Quality
- Check whether neighbor relations and layer relations are easy to follow.

### S05 Formalization Quality
- Check whether a concise formal expression or pseudo-code exists where appropriate.

### S06 Test Coverage Quality
- Check whether the protocol can be exercised by examples or tests.

### S07 Risk / Misuse Notes
- Check whether the protocol includes misuse or boundary warnings.

### S08 Version History Quality
- Check whether version/source history is sufficiently traceable.

## 8. machine_eligible Rule

A protocol is `machine_eligible` only if:
- every hard gate is `PASS` or explicitly permitted `NOT_APPLICABLE`
- no hard gate is `FAIL`, `PENDING`, or `NOT_FOUND`
- no blocking conflict exists
- the audit output includes evidence paths for each hard gate

`machine_eligible` is an audit recommendation, not a repository state change.

## 9. formal_protocol Approval Rule

A protocol may be formally promoted only when:
- it is `machine_eligible`
- governance approval exists
- the repository is updated with traceable changes
- the update is reflected in protocol document, index, machine data, and version history

## 10. Human Review Process

1. Run validator.
2. Inspect hard-gate failures and pending items.
3. Review evidence paths.
4. Resolve ambiguities or collect missing evidence.
5. Record review decision and notes.
6. If approved, prepare a separate formal change set.

## 11. Version Change Requirements

- Keep audit rules versioned.
- Do not silently change gate meaning.
- Record gate changes separately from protocol changes.

## 12. Rollback / Downgrade Rules

- If a promoted protocol later fails hard gates, downgrade recommendation to candidate or pending.
- If formal repository updates are inconsistent, revert to audit review before promotion.

## 13. Exception Handling Rules

- Explicit `NOT_APPLICABLE` only when the gate definition permits it.
- Unknown evidence is `PENDING`, not `PASS`.
- Missing source data is `NOT_FOUND`, not `PASS`.

## 14. Boundary With Psi0 / Function Layer / Case Layer

- Psi0 remains the frame; this standard does not modify Psi0.
- Function layer remains separate numbering and semantic space.
- Case layer remains separate evidence space.

## 15. No Auto-Approval Rule

Validator output never equals formal approval.
Machine audit result and formal repository approval are separate steps.
