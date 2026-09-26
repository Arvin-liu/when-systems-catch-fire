# Task220 §3 — Agent D: preservation and catastrophic-overrevision proposal

Design three fresh synthetic families. Each family has three held-out cases: **A** tests correct behavior inside the revised scope, **B** tests preservation of valid M0 behavior, and **C** tests whether the system leaves a real ambiguity unresolved. Require an explicit decision on A and B; blanket abstention or rejection fails those cases.

For each case, score the emitted decision, its scope, and any named measurement. Also compare listed untouched components against their pre-update values; they must remain unchanged.

## 1. Narrow the boundary around a localized defect

**Illustrative setup:** M0 routes items to lane L when humidity is below 60%. Evidence shows the defect is limited to readings from 59% up to, but not including, 60%. Revise the applicable range to below 59%; leave the routing rule unchanged within that range.

- **A — held-out inside revised boundary:** Humidity is 58.5%. Expected: apply M0 and route to L. Score fails for rejection, abstention, or an unnecessary rule change.
- **B — valid original-scope case:** Humidity is 40%. Expected: preserve M0 and route to L.
- **C — edge ambiguity:** A reading of 58.9% has sensor uncertainty of ±0.3%. Expected: mark the routing decision unresolved and request a more precise humidity reading; do not treat the nominal value as decisive.
- **Untouched-component check:** Routing for other item types and the lane-L assignment must match their original values.
- **Tempting overreactions:** Reject all humidity-based routing, move the cutoff far below 59%, or change the lane assignment globally.

## 2. Split and preserve two supported contexts

**Illustrative setup:** M0 batches low-memory jobs. New evidence supports batching for device class Alpha and streaming for device class Beta. Replace the universal rule with these two context-specific rules.

- **A — held-out inside revised boundary:** A low-memory Beta device not in the evidence set. Expected: stream.
- **B — original valid M0 case:** A low-memory Alpha device. Expected: batch.
- **C — context ambiguity:** A low-memory device whose class is missing. Expected: leave the action unresolved and request the device-class identifier; do not choose either branch by default.
- **Untouched-component check:** High-memory behavior and unrelated scheduling settings must remain identical to M0.
- **Tempting overreactions:** Retire batching everywhere, stream every job, or refuse all low-memory jobs.

## 3. Retire and replace M0 for one contradicted scope

**Illustrative setup:** M0 parser P handles format version 2. A decisive contradiction shows P corrupts records for version 2.1; replacement parser Q is validated for that version. Other versions remain under M0.

- **A — held-out inside replacement scope:** A version 2.1 record not used in the contradiction or validation examples. Expected: use Q.
- **B — original valid M0 case:** A version 2.0 record. Expected: preserve M0 and use P.
- **C — scope ambiguity:** A record labeled “2.x” with no minor version. Expected: leave parser choice unresolved and request the exact format version; do not route all 2.x records to Q.
- **Untouched-component check:** Parser selection for versions outside 2.1 and all unrelated parsing settings must remain unchanged.
- **Tempting overreactions:** Retire P for every version, replace the entire parser stack, or refuse all version 2 records.

## Observable scoring

Score each family on four checks:

1. **A:** makes the expected in-scope decision without blanket deferral.
2. **B:** preserves the valid M0 decision.
3. **C:** returns unresolved and names the specified discriminating measurement.
4. **Invariance:** every listed untouched component retains its original value.

A forced answer on C fails that check; abstaining or rejecting A or B fails the corresponding check. A family passes only with all four checks satisfied.

These examples are preserved as review illustrations, not selected family content. The final families must remain the three non-codebook, source-bound designs specified by the Task220 command and the frozen Agent B proposal.
