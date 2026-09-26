# CASE06 — Cohort-specific event routing

All attendees, systems, and cohort records are synthetic.

[F01] The event roster contains exact identifier matches, aliases, and walk-in entries.
[F02] Some entries have a valid event token; several others have a mismatch flag whose cause is not recorded.
[F03] Station Q accepts an entry identifier and optional event token and returns status fields.
[F04] Station D accepts an entry identifier and optional event token and returns status fields with an evidence note.
[F05] The event asks for a procedure and a disposition for unresolved mismatches.
[F06] No current entry has been checked in, and the facts assign no station to an entry category.
[F07] Historical timing records, if any, come from separate cohorts without a head-to-head comparison.
