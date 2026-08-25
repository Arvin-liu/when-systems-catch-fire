# IGNITION-139 Step 03 — Durable capture before model context

The provider-neutral process transport now accepts an initialized
`LiveCaptureWriter` before `Popen`. Each stdout/stderr chunk is streamed to the
attempt-specific host spool and digested while a separate bounded context view
is retained for the caller. Oversized context output therefore sets an
explicit context-truncation observation without killing a healthy process or
discarding the durable bytes.

Public JSONL events are parsed incrementally into the capture capsule. The
capsule is finalized before `LiveProcessResult` is returned, with opaque/redacted
process metadata, stream byte counts/digests, event sequence/count/digest,
return code, timeout and process-group status. Structured result attachment can
occur after process finalization, and normal known-terminal handling cleans the
raw spool; timeout/reconciliation keeps it pending.

The existing adapters use capture only when the transport explicitly supports
it, so deterministic fake transports remain suitable for offline tests. No
provider, auth, workspace, channel, browser, remote Git, or billing boundary was
changed.

Evidence: the legacy transport/adapter set ran 34 tests and the new durable
transport set ran 2 tests, all with 0 failures, 0 errors, and 0 skips. A 1MB+
stdout fixture returned normally with a bounded context view while the capsule
retained the complete stream count and digest.

Claim ceiling: repository-local capture and transport evidence only.
