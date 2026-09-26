# CASE03 — Queued request acknowledgement

All identifiers, events, and service behavior are synthetic.

[F01] An export request with immutable idempotency key RQ-18 was submitted to a test queue.
[F02] The gateway returned QUEUED for RQ-18.
[F03] The client connection ended before a receipt body was stored.
[F04] The local event log contains no terminal ACCEPTED or NOT_ACCEPTED status.
[F05] A status-query control and a resubmit control using the same key are available.
[F06] The queue contract says reuse of RQ-18 does not create a second request, but does not state whether the first request is terminal.
[F07] The incident record contains no follow-up action.
