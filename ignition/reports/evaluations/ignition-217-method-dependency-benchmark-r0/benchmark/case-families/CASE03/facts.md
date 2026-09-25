# CASE03 — Queued export with missing receipt

All identifiers, events, and service behavior in this case are synthetic.

[F01] One export request with immutable request key RQ-18 was submitted to a test queue.
[F02] The gateway returned QUEUED for RQ-18.
[F03] The client connection ended before a receipt body was stored.
[F04] The local event log contains no terminal ACCEPTED or NOT_ACCEPTED status.
[F05] A retry control and a status-lookup control are both available.
[F06] The incident record contains no evidence that a second submission occurred.
[F07] No rule in the event log classifies a missing receipt as success or failure.
