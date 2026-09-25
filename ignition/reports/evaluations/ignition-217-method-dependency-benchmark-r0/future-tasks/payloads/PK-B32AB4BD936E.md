Packet reference: PK-B32AB4BD936E

Six synthetic case records follow.

## Record CASE05
Source SHA-256: e76b2e6635d5f772af6cddb6776769c82a62a0abd6accaef6f0a7967fb7ed1ba


# CASE05 — Mixed-class export revision

All labels, versions, and files in this case are synthetic.

[F01] A proposed archive bundle contains a public procedure guide and a restricted annex.
[F02] The bundle request uses a single recipient group for the archive.
[F03] The available packager can combine files or produce separate sub-bundles.
[F04] The record contains labels for both files but no policy version or export decision.
[F05] No bundle has been created or transmitted.
[F06] The source record does not say whether an older bundling rule remains valid for other archive shapes.



# Supplemental record CASE05

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Older procedure V0: combine records in one bundle when every record has the same authorization class.
[A02] Counterexample record: a mixed-class bundle exposed a restricted supplement in the synthetic review.
[A03] Revised procedure V1: separate records when authorization classes differ.
[A04] Revision scope: V1 narrows the mixed-class case; it does not retire V0 for homogeneous sets.
[A05] Context record: the current archive contains one public guide and one restricted annex.
[A06] Expected observation: each output sub-bundle contains only one authorization class and its manifest preserves the supplied labels.
[A07] Disposition record: apply the scoped revision to a mixed-class set and preserve the older rule within its original homogeneous boundary.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R01] A02 is the counterexample linked to revision A03.
[R03] A05 identifies the present case as mixed-class.
[R04] A06 is the check for applying the revised procedure.
[R05] A07 records scoped revision rather than universal supersession.


## Record CASE02
Source SHA-256: 5c1f977c39ee5ecf1ec0a86df0b04fed1035c83902f33bf4a50f20017e0d3850


# CASE02 — Regional storefront revision

All names, observations, and systems in this case are synthetic.

[F01] A banner revision B-12 has been scheduled across five edge regions.
[F02] Two regions report B-12 as active; three still report B-11.
[F03] The purge control and the wait-for-convergence control are both available.
[F04] A preview from one B-12 region shows the new banner, while one B-11 region still serves the earlier copy.
[F05] The task record asks whether to purge the edge cache now or defer that action.
[F06] No cache operation is recorded as executed in this incident.
[F07] The incident record does not state what revision a purge would reload during mixed regional state.



# Supplemental record CASE02

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate record: a cache purge can be submitted for the banner key.
[A02] Candidate record: defer the purge and run named-region revision probes.
[A03] Boundary record: during mixed regional revision state, a purge may refill an edge from an older origin snapshot.
[A04] Context record: the boundary applies to a rollout whose region markers have not converged.
[A05] Expected observation: every named region reports the target revision and the origin warm marker is stable on two probes.
[A06] Failure interpretation: any old or unavailable region marker means convergence has not been demonstrated.
[A07] Disposition record: withhold the purge until the stated observation is satisfied; the current record does not establish that condition.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R01] A04 activates the boundary recorded in A03.
[R03] A05 is the observation required before reconsidering A01.
[R04] A06 interprets a stale or unavailable probe as incomplete, not as success.
[R05] A07 records bounded non-application.


## Record CASE06
Source SHA-256: a5f9758e62f7075181c41b94f89c139260848b178bbed219865b5571e39e6672


# CASE06 — Event check-in cohorts

All attendees, systems, and cohort records in this case are synthetic.

[F01] The event roster contains exact identifier matches, name aliases, and walk-in entries.
[F02] A self-service scanner accepts a valid event code; a staffed desk can review a name against the roster.
[F03] One prior cohort log contains scanner-completion times for exact identifier matches.
[F04] A separate cohort log contains desk-resolution times for aliases and walk-ins.
[F05] The two logs use different cohorts and do not include a head-to-head comparison.
[F06] Several current entries have a mismatch flag whose cause is not recorded.
[F07] The event plan asks for a check-in procedure and a disposition for unresolved mismatches.



# Supplemental record CASE06

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate procedure Q: self-service code scan for entries with exact roster identifiers.
[A02] Candidate procedure D: staffed roster review for aliases and walk-ins.
[A03] Source record Q-1: scan completion observations from a cohort of exact identifier matches.
[A04] Source record D-1: desk resolution observations from a different cohort of aliases and walk-ins.
[A05] Evidence boundary: Q-1 and D-1 are not a head-to-head comparison and do not rank universal performance.
[A06] Expected observation: an exact roster identifier is verified by its event code; an alias or walk-in is routed to a documented roster review.
[A07] Disposition record: retain both cohort-bounded procedures; leave an unexplained mismatch unresolved pending roster evidence.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R01] A03 supports A01 only for the exact-identifier cohort.
[R02] A04 supports A02 only for aliases and walk-ins.
[R03] A05 blocks a universal-winner inference.
[R05] A07 preserves coexistence and unresolved mismatches.


## Record CASE01
Source SHA-256: 84787990111e5a9c53a9ac8405df1e7cc411f08b46a28dcda3219bba7ed7c796


# CASE01 — Archive approval trail

All names, records, dates, and tools in this case are synthetic.

[F01] A review packet contains a signed version 3 transcript from checkpoint C-17 and a later version 4 correction marked unsigned.
[F02] The export console offers Route Alder, which emits the most recent signed document and its signature timestamp.
[F03] The console also offers Route Birch, which emits the version chronology and a digest for each file.
[F04] The request asks for a record from which a later auditor can identify what content was present at each approval checkpoint.
[F05] The console preview does not show how either route relates a file version to a particular checkpoint.
[F06] Neither route is recorded as selected or run for this packet.
[F07] No approval event is recorded for the unsigned correction.



# Supplemental record CASE01

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate record: Route Alder emits the most recent signed document and its signature timestamp.
[A02] Candidate record: Route Birch emits the version chronology and file digests and can include an approval-event pointer.
[A03] Selection criterion: a checkpoint audit needs the content digest joined to the approval event for that checkpoint.
[A04] Context record: source version labels, checkpoint identifiers, and signature markers must be intact before export.
[A05] Expected observation: the delivered manifest associates each included content digest with a checkpoint and approval event.
[A06] Failure interpretation: a missing digest-to-event join leaves the approved content unresolved; an unsigned later correction is not an approval event.
[A07] Disposition record: keep a correction without an approval event pending; do not infer that a later file was part of an earlier checkpoint.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R02] A04 is the precondition for applying the selection rule.
[R03] A05 is the discriminator to inspect after export.
[R04] A06 interprets a missing join without inventing approval.
[R05] A07 bounds the disposition of the later correction.


## Record CASE03
Source SHA-256: 96e03fa356f35a0c30868c1a47f7e868617c7021e05d78a3bd08fbc56f64ce7b


# CASE03 — Queued export with missing receipt

All identifiers, events, and service behavior in this case are synthetic.

[F01] One export request with immutable request key RQ-18 was submitted to a test queue.
[F02] The gateway returned QUEUED for RQ-18.
[F03] The client connection ended before a receipt body was stored.
[F04] The local event log contains no terminal ACCEPTED or NOT_ACCEPTED status.
[F05] A retry control and a status-lookup control are both available.
[F06] The incident record contains no evidence that a second submission occurred.
[F07] No rule in the event log classifies a missing receipt as success or failure.



# Supplemental record CASE03

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate record: status lookup by the original immutable request key.
[A02] Candidate record: a new submission under a new request key.
[A03] Observed response: the original request returned QUEUED before the client connection ended without storing a receipt body.
[A04] Failure interpretation: a missing receipt after QUEUED is an acknowledgement-unknown state, not a terminal rejection.
[A05] Expected observation: a status query under the same key returns pending, terminal accepted, terminal not accepted, or remains unavailable.
[A06] Boundary record: another submission is not licensed while the original key has a non-terminal or unavailable status.
[A07] Disposition record: reconcile the original key first; only a recorded terminal NOT_ACCEPTED state permits a new submission.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R01] A03 supports the acknowledgement-unknown interpretation in A04.
[R03] A05 discriminates the terminal state under the original key.
[R04] A06 bounds any further submission.
[R05] A07 records the conditional disposition.


## Record CASE04
Source SHA-256: 2de34564f2d749a651b6d8d4fbe2ee18d10508686020d6dbac693f8b417aaf5f


# CASE04 — Root-zone sample timing

All crops, instruments, values, and observations in this case are synthetic.

[F01] A greenhouse tray shows curled leaves in two rows.
[F02] Air temperature at canopy height was 31 degrees during the prior hour.
[F03] The feed tank conductivity was recorded as 1.4 mS/cm before refill.
[F04] No root-zone sample was recorded after the refill.
[F05] A handheld meter, a root-zone sampling port, and a recirculation timer are available.
[F06] The work note asks whether the next action should change the feed concentration or continue observation.
[F07] The record contains no post-recirculation root-zone measurement and no recorded cause.



# Supplemental record CASE04

Representation note: this excerpt preserves the same atomic records and source context as the companion trace, but its relation field is absent.

## Independently listed records
[A01] Candidate explanation: elevated root-zone salt concentration.
[A02] Candidate explanation: canopy heat exposure.
[A03] Candidate observation: a root-zone conductivity reading collected after four minutes of recirculation.
[A04] Selection rationale: the incoming feed value alone does not distinguish accumulated root-zone salt from canopy heat.
[A05] Boundary record: do not change feed concentration from leaf appearance or feed-tank conductivity alone.
[A06] Expected observation: compare the timed root-zone value with the recorded inlet value; a difference of at least 0.6 mS/cm supports accumulation, while a smaller difference leaves the two explanations unresolved.
[A07] Disposition record: request the timed root-zone observation and keep the cause unresolved until it is recorded.

No source record in this excerpt joins the listed records into an ordered selection, test, interpretation, and disposition chain.

## Recorded relations retained in this control
[R02] A05 blocks an unsupported immediate feed change.
[R03] A03 specifies the location and timing required for A06.
[R04] A06 interprets the possible observation without assigning a cause from missing data.
[R05] A07 records the unresolved disposition.
