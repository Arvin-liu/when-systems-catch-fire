# R0.3 Case: The Reedline Relay Change

Case ID: `IGNITION-20260918-187-GOV-01`

This is an independently authored synthetic engineering-and-governance
source. The service, people, events, measurements, and records below are
invented for this bounded case.

## Change-window notes

The fictional Reedline team maintains a relay simulator used by several
internal test rigs. A change request proposes shortening the retry interval
from five minutes to forty-five seconds so a disconnected rig can resume
earlier. The request describes the change as “timing only.”

- A test note records eight simulated reconnects. Seven showed a new retry
  interval in the relay log. The eighth rig remained offline until the run
  ended. The note does not say whether the control-plane display or the
  relay log is authoritative for the effective setting.
- A separate exercise shows that reconnecting rigs can send a burst of
  queued events. It used a different simulator configuration and does not
  record the proposed forty-five-second interval.
- At 09:10, an operator enabled the change on two of twelve test rigs. The
  control plane acknowledged both requests. One rig continued to display the
  old interval for several minutes; no one recorded its relay log during
  that period.
- The change ticket says payload fields are unchanged. A review note calls
  the sample events “operational telemetry”; the test fixture includes a
  fictional station label, but the ticket does not say whether that label is
  covered by the review.
- The release checklist marks “ready for observation.” The production flag
  remained off during the exercise. The notes do not identify who owns the
  next promotion decision or whether rollback was tested after a control-
  plane acknowledgement.

The evidence is limited to one simulation window. It contains no production
deployment, independent replay, complete event-delivery check, or record of
the promotion decision. The sources do not establish whether the display
delay reflects a setting delay, a cache delay, or a reporting delay.

## Open prompt

Using only these notes, give a bounded account of what was requested,
observed, acknowledged, and left undecided. Distinguish implementation
evidence from governance status, retain uncertainty about the mismatched
signals, and state what additional evidence would be needed for a stronger
conclusion.
