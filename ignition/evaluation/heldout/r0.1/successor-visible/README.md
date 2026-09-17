# Held-out Successor Packet R0.1

This directory is the complete case-visible packet for a future Task182 run.
Only paths listed in `packet-manifest.json`, plus that manifest itself, are in
scope. The read-ledger schema is separately listed. A future successor must
hash the manifest and record every actual read. Any out-of-scope read makes the
trial contaminated and requires the successor to stop.

This is **procedural isolation**, not cryptographic secrecy. A normal Git clone
can read other repository paths. The future Task182 executor must use the
manifest as its read allowlist and must not search or open unlisted paths.

The packet contains two new bounded source objects. It contains no gold IR,
gold relations, transition records, human confirmation, expected continuation,
or evaluator answer key. Provenance identifies source location and hashes only.

The future trial has four independent roles: Task181 Builder (complete), Task182
Successor, Task183 Independent Evaluator in a fresh conversation, and
Owner/GPT Adjudicator. The Builder will not run either future role.
