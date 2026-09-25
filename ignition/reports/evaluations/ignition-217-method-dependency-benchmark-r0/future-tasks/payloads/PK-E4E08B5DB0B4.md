Packet reference: PK-E4E08B5DB0B4

Six synthetic case records follow.

## Record CASE03
Source SHA-256: 778589ea714b94a7cf57ba84bec2936583f0e980c6a36dd512068e50cdf071c6

# CASE03 — Queued request acknowledgement

All identifiers, events, and service behavior are synthetic.

[F01] An export request with immutable idempotency key RQ-18 was submitted to a test queue.
[F02] The gateway returned QUEUED for RQ-18.
[F03] The client connection ended before a receipt body was stored.
[F04] The local event log contains no terminal ACCEPTED or NOT_ACCEPTED status.
[F05] A status-query control and a resubmit control using the same key are available.
[F06] The queue contract says reuse of RQ-18 does not create a second request, but does not state whether the first request is terminal.
[F07] The incident record contains no follow-up action.


# Supplemental record CASE03

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate-diagnostic record: status query using the original immutable request key.
[A02] Candidate-operation record: resubmit control using the same idempotency key.
[A03] Gateway record: the original key received a QUEUED response.
[A04] Connection record: the client ended before storing a receipt body.
[A05] Status-field record: a query can return pending, terminal accepted, terminal not accepted, or unavailable.
[A06] Key record: RQ-18 is immutable and reuse does not create a second request.
[A07] Follow-up record: no status query or later submission is present in the event log.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A06 --IDENTIFIES--> A03 :: The immutable key identifies the stored QUEUED response.
[R02] A04 --FAILURE_TO_DIAGNOSTIC--> A01 :: Treat QUEUED followed by a lost receipt as acknowledgement status unknown. Query the original key first; do not submit while status is pending, non-terminal, or unavailable, and permit a new submission only after terminal NOT_ACCEPTED is recorded.
[R03] A05 --DISCRIMINATES_STATUS_FOR--> A03 :: The status fields distinguish pending, terminal, and unavailable states for the original request.
[R04] A06 --KEY_IDENTITY_FOR--> A02 :: RQ-18 names the same request identity; this record does not establish the request's present status or the safe next operation.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The event log separates a proposed diagnostic from a query already performed.


## Record CASE01
Source SHA-256: 5571dbf60194725aa4342bdf1abf9738713a904474e7bb48db128f049c301e4d

# CASE01 — Checkpoint export selection

All names, records, dates, and tools are synthetic.

[F01] A packet contains signed document version 3 associated with checkpoint C-17 and a later version 4 correction marked unsigned.
[F02] Route Alder's preview lists a signed-document field, signature timestamp, and approval-event reference; it does not list a per-file digest.
[F03] Route Birch's preview lists a version sequence and per-file digest; its optional approval-event field is not verified in the preview.
[F04] The request asks for an export from which a later auditor can reconstruct which content was present at each approval checkpoint.
[F05] Neither route has been selected or run.
[F06] No approval event is recorded for the unsigned correction.
[F07] The packet does not establish which route's available fields are sufficient to identify checkpoint membership.


# Supplemental record CASE01

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate record: Route Alder returns a signed-document field, signature-timestamp field, and approval-event reference, but no per-file digest.
[A02] Candidate record: Route Birch returns a version sequence and per-file digest; its optional approval-event field has unverified output behavior.
[A03] Audit objective record: reconstruct content membership at each approval checkpoint.
[A04] Source precondition record: version labels, checkpoint identifiers, and signature markers are available for comparison.
[A05] Output-field record: a delivered manifest may expose multiple source identifiers; the current preview does not establish how its fields join.
[A06] Preview limitation record: at least one optional field's delivered behavior is not verified by the current preview.
[A07] Version record: version 4 is marked unsigned; the observed C-17 document is version 3.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --SELECTS_FOR_AUDIT--> A02 :: Propose Route Birch as the checkpoint-level verification candidate because its chronology and per-file digest can identify content; assert membership only if the delivered digest joins to the checkpoint and approval event, and keep the unsigned correction outside the approved record.
[R02] A04 --PRECONDITION_FOR--> A03 :: Version, checkpoint, and signature identifiers must be intact before interpreting a checkpoint export.
[R03] A05 --OBSERVATION_FOR--> A02 :: The delivered package can be compared with the source records after a proposed export.
[R04] A06 --LIMITS_INTERPRETATION_OF--> A05 :: A field not verified in a preview must be checked in the delivered package before describing that field.
[R05] A07 --PROVENANCE_FOR--> A03 :: The observed C-17 version and unsigned-correction marker remain separate provenance entries.


## Record CASE04
Source SHA-256: 0f0a83087bc9728a375e09211c0bd767108b8456703d2e0fdaaa562b5cdcb31f

# CASE04 — Greenhouse symptom discriminator

All crops, instruments, values, and observations are synthetic.

[F01] A greenhouse tray shows curled leaves in two rows.
[F02] Air temperature at canopy height was 31 degrees during the prior hour.
[F03] Feed-tank conductivity was 1.4 mS/cm before refill.
[F04] No root-zone sample was recorded after refill.
[F05] A handheld meter, root-zone port, recirculation timer, and canopy humidity sensor are available.
[F06] The work note lists feed adjustment, increased airflow, a root-zone sample, and a canopy humidity reading as possible next steps.
[F07] No cause or post-refill measurement is recorded.


# Supplemental record CASE04

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Hypothesis record: elevated salt concentration in the root zone.
[A02] Hypothesis record: canopy heat or humidity stress.
[A03] Measurement-definition record: a root-zone conductivity reading can be collected after recirculation; the exact interval is selected by the operating protocol.
[A04] Existing-value record: the feed-tank value of 1.4 mS/cm predates refill.
[A05] Instrument record: root-zone port, recirculation timer, and canopy humidity sensor are available.
[A06] Calibration-record index: the protocol has an inlet-comparison rule; its threshold and interpretation are kept in the referenced calibration record.
[A07] Current-record status: no post-refill root-zone reading or cause is present.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A01 --SELECTS_DISCRIMINATOR--> A03 :: To distinguish the competing root-salt and canopy-stress explanations, request a root-zone conductivity reading after four minutes of recirculation and compare it with the recorded inlet value.
[R02] A04 --TEMPORAL_LIMIT_FOR--> A01 :: The pre-refill feed value does not record the current root-zone state.
[R03] A05 --SUPPORTS_MEASUREMENT--> A03 :: The listed port and timer make a post-refill reading technically available; they do not select a measurement or interval.
[R04] A06 --INTERPRETS--> A03 :: A difference of at least 0.6 mS/cm supports root-zone accumulation. A smaller difference leaves both explanations unresolved; do not change feed concentration from the current observations.
[R05] A07 --RESULT_STATUS_FOR--> A03 :: The current record contains no post-refill measurement result.


## Record CASE02
Source SHA-256: a01b147be30e6e1d26831ab85b21860aee2ac452e0e8681a0fb3c7f02b29e12e

# CASE02 — Regional cache boundary

All names, observations, and systems are synthetic.

[F01] Banner revision B-12 is scheduled across five edge regions.
[F02] Two regions report B-12 active; three report B-11.
[F03] A purge control and a wait-and-probe control are both available.
[F04] A preview from one B-12 region shows the new banner, while one B-11 region serves the earlier copy.
[F05] The incident asks which operation should be proposed while regional markers differ.
[F06] The incident log contains no cache-operation result and no record of which revision a purge would reload during mixed state.
[F07] No cache operation is recorded as executed.


# Supplemental record CASE02

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Candidate-operation record: the purge control refreshes the selected edge-cache key.
[A02] Candidate-operation record: the wait-and-probe control records regional revision markers and the origin warm marker.
[A03] Current-state record: two named regions report B-12 and three report B-11.
[A04] Origin record: an older origin snapshot remains available during the rollout window.
[A05] Probe-field record: a regional marker and origin warm marker can be recorded at a stated time.
[A06] Probe-coverage record: a preview from one region is not a record for the other named regions.
[A07] Operation-log record: no cache-action result is present for this incident.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --STATE_SET_FOR--> A04 :: The regional-marker set and origin-snapshot record describe the same rollout interval.
[R02] A03 --BOUNDARY_TO_NONAPPLICATION--> A01 :: Mixed regional markers with an older origin snapshot make a purge inapplicable now. Defer it until every named region reports B-12 and the origin warm marker is stable on two probes; an old or unavailable marker fails this condition.
[R03] A05 --OBSERVED_FIELDS_FOR--> A02 :: The regional marker and origin warm marker are fields returned by a probe.
[R04] A06 --LIMITS_COVERAGE_OF--> A05 :: A single-region preview does not establish the state of every named region.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The incident log distinguishes a proposed operation from an operation result.


## Record CASE06
Source SHA-256: 9c8990f65ed6e5e4eb8aa729dfa774d68cc8c1c12f801afda16995e2501bacdc

# CASE06 — Cohort-specific event routing

All attendees, systems, and cohort records are synthetic.

[F01] The event roster contains exact identifier matches, aliases, and walk-in entries.
[F02] Some entries have a valid event token; several others have a mismatch flag whose cause is not recorded.
[F03] Station Q accepts an entry identifier and optional event token and returns status fields.
[F04] Station D accepts an entry identifier and optional event token and returns status fields with an evidence note.
[F05] The event asks for a procedure and a disposition for unresolved mismatches.
[F06] No current entry has been checked in, and the facts assign no station to an entry category.
[F07] Historical timing records, if any, come from separate cohorts without a head-to-head comparison.


# Supplemental record CASE06

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Procedure record Q: process a set of entry identifiers and optional event tokens and return status fields.
[A02] Procedure record D: process entry identifiers and optional event tokens one row at a time and return status fields with an evidence note.
[A03] Historical timing record: a result is recorded for cohort H1.
[A04] Historical timing record: a separate result is recorded for cohort H2; entry categories and procedure assignment are not in this record.
[A05] Comparison record: H1 and H2 are separate cohorts without a head-to-head comparison.
[A06] Current-entry record: roster identifier status, entry type, event-token status, and mismatch status are recorded for each entry.
[A07] Check-in status record: no current entry has a resolved check-in event.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --SOURCE_RECORD_FOR--> A05 :: H1 is the source cohort for its recorded timing observation.
[R02] A04 --SOURCE_RECORD_FOR--> A05 :: H2 is a separate source cohort for its recorded timing observation.
[R03] A05 --DOES_NOT_RANK--> A01 :: Separate cohorts do not establish a universal procedure winner.
[R04] A06 --MAPS_COHORT_TO_PROCEDURE--> A01 :: Route exact roster identifiers with a valid event code to Q; route aliases and walk-ins to D. Keep unexplained mismatches unresolved pending roster evidence.
[R05] A07 --LIMITS_STATUS_CLAIM_FOR--> A06 :: The current status record contains no completed check-in event.


## Record CASE05
Source SHA-256: 8fc8fef77dcddb8055b3906e868d2e6051d46ca9f22e43d7db49eca399e9a9ba

# CASE05 — Archive grouping revision scope

All labels, versions, and files are synthetic.

[F01] A proposed archive contains a public guide and restricted annex under one request identifier.
[F02] Packaging procedure V0 groups files by request identifier.
[F03] Packaging procedure V1 groups files by signatory class.
[F04] A prior package review recorded a cross-access event, but its raw event record omits the grouping key, permission record, and procedure version.
[F05] The current request includes two signatory classes.
[F06] No grouping procedure is selected, and no archive has been created or transmitted.
[F07] The record does not state how the prior event should affect this request.


# Supplemental record CASE05

Representation note: structured synthetic records; relation rows connect source-linked records.

<!-- ATOM_BLOCK_BEGIN -->
## Atomic records
[A01] Procedure record V0: package records that share a request identifier into one group.
[A02] Procedure record V1: group records by signatory class.
[A03] Counterexample record: a prior mixed-signatory archive had a cross-access event; the raw event record omits grouping key and procedure version.
[A04] Revision-history record: V1 was recorded after V0; the version log contains no universal-retirement field.
[A05] Current archive record: one request identifier contains a public guide and restricted annex with two signatory classes.
[A06] Verification-field record: output groups can be inspected for request identifier, signatory class, and supplied file labels.
[A07] Execution-status record: no procedure is selected and no archive output exists.
<!-- ATOM_BLOCK_END -->

## Recorded relations
[R01] A03 --COUNTEREXAMPLE_REVISES_SCOPE--> A02 :: The cross-access counterexample is the recorded reason V1 applies to mixed-signatory archives; it does not retire V0 for single-class records.
[R02] A04 --ORDERS_VERSION_RECORDS--> A01 :: The version log records V0 before V1; it does not encode a case-specific procedure selection.
[R03] A05 --IDENTIFIES_CURRENT_SHAPE--> A06 :: The current archive identifiers and labels are available for output verification.
[R04] A05 --VERIFICATION_FIELDS_FOR--> A06 :: Request identifier and signatory-class labels can be compared with output groups after any proposed procedure.
[R05] A07 --EXECUTION_STATUS_FOR--> A01 :: The archive record distinguishes a proposed grouping procedure from a completed export.
