# CASE01 — Checkpoint export selection

All names, records, dates, and tools are synthetic.

[F01] A packet contains signed document version 3 associated with checkpoint C-17 and a later version 4 correction marked unsigned.
[F02] Route Alder's preview lists a signed-document field, signature timestamp, and approval-event reference; it does not list a per-file digest.
[F03] Route Birch's preview lists a version sequence and per-file digest; its optional approval-event field is not verified in the preview.
[F04] The request asks for an export from which a later auditor can reconstruct which content was present at each approval checkpoint.
[F05] Neither route has been selected or run.
[F06] No approval event is recorded for the unsigned correction.
[F07] The packet does not establish which route's available fields are sufficient to identify checkpoint membership.
