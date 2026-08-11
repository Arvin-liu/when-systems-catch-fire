# GetNote 1329 pipeline as an internal pressure test

Status: `PUBLICATION_SAFE_ROLE_F_CANDIDATE`  
Architecture: **Epistemic Governance Kernel and Federated Planes**  
Architecture disposition: `FEDERATED_ARCHITECTURE_ONLY`

## Boundary and conclusion

The frozen public aggregate records 160 selected notes, 154 claim-bearing notes, 6 body-recovery-blocked notes, 1329 claim rows and 1328 normalized distinct claim texts. It records ceilings of 931 `EVIDENTIALLY_SUPPORTED`, 307 `SEMANTICALLY_INTERPRETED`, 3 `STRUCTURALLY_VALID` and 88 `NOT_ASSIGNED`; adjudication closes as 1241 terminal decisions plus 38 `ABSTAIN` plus 50 not adjudicated; `EPISTEMICALLY_ACCEPTED=0`.

This is evidence that Pointfire's internal source, claim, review, ceiling, suspension and publication hand-offs were exercised under volume and incomplete inputs. It is not evidence of 1329 independent facts, 1329 externally verified claims, or general validity of the architecture. The row count measures a projection. The distinct-text count measures normalization, not source independence. A note key is not a source family, and repetition within or across notes does not create independent evidence.

## Pipeline-to-automata mapping

The public synthesis describes projection, normalization/deduplication, theme mapping, review/conflict retention and bounded publication. These operations compose several local automata; they do not instantiate one universal lifecycle.

| GetNote operation or outcome | Governed object | Local automaton / hand-off | Kernel constraint | What may be inferred | What may not be inferred |
|---|---|---|---|---|---|
| select 160 notes | source candidate | `DISCOVER → SOURCE-BIND` | provenance and privacy must remain bound | a bounded corpus was selected | corpus completeness or representativeness |
| 6 body recoveries blocked | source / source body | `SOURCE-BIND → BODY_RECOVERY_BLOCKED` | fail closed; no inferred body | required material was unavailable | missing content, claim text or negative truth |
| extract 1329 claim rows | atomic-claim candidate | `SOURCE-BIND → ATOMIZE` | row identity is not truth identity | a machine-readable projection exists | 1329 true or independent claims |
| normalize to 1328 distinct texts | semantic projection | `ATOMIZE → NORMALIZE/IDENTIFY` | preserve provenance and collision risk | one exact/normalized near-duplicate was removed under the public count | semantic equivalence, independent evidence or canonical claim identity |
| assign 931/307/3/88 ceilings | claim projection | `CLASSIFY → ASSIGN-CEILING` or legal `NOT_ASSIGNED` | ceilings remain local; no cross-axis promotion | maximum public wording within this run | external truth, E-axis maturity or final acceptance |
| retain source family and lineage questions | source/evidence relation | `SOURCE-BIND → SOURCE-FAMILY-ASSESS` | duplicate/derivative sources cannot become independent by count | independence is a required review dimension | note-key count as independent source count |
| review 1241 terminal rows | adjudication artifact | `REVIEW → LOCAL TERMINAL` | reviewer authority is scoped | the named review question reached a local terminal result | truth, external replication or Owner acceptance |
| 38 `ABSTAIN` | adjudication artifact | `REVIEW → ABSTAIN` | suspension is legal and re-enterable | reviewer did not force a verdict | rejection, support, or missing source |
| 50 not adjudicated | workflow obligation | `REVIEW → PENDING/NOT_ADJUDICATED` | incomplete is distinct from abstention | adjudication did not close | a hidden positive or negative result |
| conflict markers and alternatives | counterexample / review cue | `TEST/COUNTEREXAMPLE → REVIEW` | lexical cues cannot adjudicate contradiction automatically | candidates for scoped re-review exist | that a contradiction is established or resolved |
| theme synthesis | result-unit candidate | `LOCAL CLAIMS → SANITIZE/PROJECT` | aggregation must not widen any local ceiling | a bounded, source-bound narrative can be written | theme hit totals as evidence or additive independent results |
| public metrics and Results Book | public projection | `PROJECT → PUBLISH` | provenance/ceiling/privacy routes; publication cannot upgrade source | publication-safe aggregate and limitations are visible | visibility, polish or registry inclusion as truth |
| future correction | result unit / claim | `PUBLISH → REVISE/DOWNGRADE/SUPERSEDE/WITHDRAW` | append-only lineage and anti-rebound | later evidence may change permission and wording | silent historical rewrite |

## Meaning of the four ceiling counts

- **931 `EVIDENTIALLY_SUPPORTED`**: the controlled source/material layer supported the corresponding projected wording up to that local ceiling. It does not mean independent external replication, causal identification, or epistemic acceptance.
- **307 `SEMANTICALLY_INTERPRETED`**: a bounded interpretation was available, while the wording must remain visibly interpretive. Semantic coherence cannot raise external-evidence maturity.
- **3 `STRUCTURALLY_VALID`**: the projection satisfied a structural/formal condition. Structure does not establish empirical support.
- **88 `NOT_ASSIGNED`**: no ceiling assignment was made in the frozen public run. This is not `ABSTAIN`, rejection, falsehood or a license for theme prose to absorb the rows.

The four categories are local public-ceiling outcomes, not a scalar truth ladder. They cannot be averaged or silently mapped onto Foundation M/E coordinates.

## Suspension, blocking and non-acceptance

The counts expose three different automata:

1. `BODY_RECOVERY_BLOCKED` belongs to source recovery. Processing requiring the body must stop until provenance-bound recovery occurs.
2. `ABSTAIN` belongs to reviewer authority. It is separate from the 1241 terminal decisions and records that a scoped reviewer did not force a positive or negative verdict; re-entry requires new evidence, clearer scope or differently authorized review.
3. not-adjudicated belongs to workflow completion. It records an unclosed obligation, not a reviewer decision.

`EPISTEMICALLY_ACCEPTED=0` is compatible with internal governance success because the pipeline did not convert throughput, source-bound support, structural validity or reviewer terminality into acceptance. It is not proof that every local decision was correct, that all relevant counterexamples were found, or that the federation works outside this corpus.

## What predated GetNote, what it changed, and what remains open

### Already present before the pressure test

- source/provenance binding and the L0–L6 transformation spine;
- claim ceiling and the prohibition on public wording exceeding it;
- M/E independence and proof/evidence/type separation;
- J+/J−, counterexample and independent-review roles;
- fail-closed review, dependency impact, supersession and withdrawal;
- private/public separation and the rule that publication does not create truth.

### Reinforced or made operationally visible in GetNote

- recovery blocking as a legitimate source-automaton state at nontrivial corpus scale;
- explicit separation of row count, normalized text count, note-key count and source-family independence;
- `ABSTAIN`, unadjudicated and `NOT_ASSIGNED` as three non-equivalent outcomes;
- a practical ceiling distribution that refused a single accepted/not-accepted collapse;
- conflict retention, alternative explanations and theme synthesis under a narrower public boundary;
- the need to couple machine aggregates to a human Results Book without copying private bodies.

### Newly forced or more sharply specified

- source-family independence must be an explicit assessment rather than inferred from note keys or repeated citations;
- review-capacity debt must remain measurable when automation produces more candidates than adjudicators can close;
- projection metrics require a publication-safe aggregate contract that excludes raw bodies, identifiers and internal inventory;
- public synthesis needs an anti-absorption rule: prose cannot silently adjudicate `NOT_ASSIGNED`, `ABSTAIN`, blocked or pending rows.

These are architecture-interface clarifications produced by the run. They are not new truth authorities and do not upgrade the STEP04 decision beyond `FEDERATED_ARCHITECTURE_ONLY`.

### Residual architecture gaps

- no frozen, independently validated source-family census for the 1329 projection;
- external verification remains not globally completed/assessed, and no independent cross-domain replay exists;
- no demonstrated lossless crosswalk from GetNote ceiling labels to all Foundation/local ceiling vocabularies;
- no machine-semantic crosswalk that safely unifies `ABSTAIN`, `NOT_ASSIGNED`, not-adjudicated and recovery blocking—and such a unification may be undesirable;
- review capacity and backlog aging are not yet a canonical maturity axis;
- candidate conflict markers still require source-, scope-, time-, negation- and number-aware adjudication;
- 6 blocked sources and 50 open adjudications leave a bounded completeness residual.

## Falsification and downgrade triggers

This pressure-test interpretation must be downgraded if any of the following is shown:

- the published aggregates cannot be reproduced from the frozen, authorized projection;
- theme prose widened a row's local ceiling or absorbed suspended/open rows without adjudication;
- duplicate note keys or repeated source material were counted as independent source families;
- blocked bodies were reconstructed by inference rather than recovered with provenance;
- reviewer terminality, publication or `EPISTEMICALLY_ACCEPTED=0` was used as evidence of external truth;
- the relationship mapping requires copying local claim states into a second authority.

## Publication-safe bottom line

GetNote supplies bounded internal evidence that the federation can preserve provenance, multiple ceiling outcomes, legal suspension, incomplete work and public/private routing under a 1329-row projection. The strongest defensible claim is operational: the system sometimes refused to manufacture acceptance under scale. Its external validity, source independence and generality remain unestablished.
