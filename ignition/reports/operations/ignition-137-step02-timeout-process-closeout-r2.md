# IGNITION-20260824-137 — Step 02 Timeout / Timestamp / Process Closeout R2

The live transport now records separate wall-clock `started_at` and
`ended_at`, monotonic elapsed time, the requested timeout, whether termination
was requested, signals sent, final process-group status, first public-event
latency, and stdout/stderr byte counts plus SHA-256 digests. Raw stdout and
stderr remain bounded in memory and are not written as durable receipt data.

The new `live-executor-receipt-r2` carries this transport evidence. The old
Task136 `live-executor-receipt-r1` remains readable for historical evidence but
was not rewritten; a new live receipt cannot silently omit the closeout fields.
Wall-clock inversion is recorded as drift while monotonic elapsed remains the
duration authority. If an exited leader leaves inherited pipes open outside its
original process group, the transport reports `CHILD_LEFT_BEHIND` and does not
claim cleanup.

Targeted deterministic tests passed: `21 tests / 0 failures / 0 errors / 0
skips`. They cover valid slow startup, hard timeout, SIGTERM-to-SIGKILL
escalation, a child left behind outside the leader's group, timestamp drift,
bounded output, legacy receipt parsing, and live-execution receipt binding.

Claim ceiling: this step makes timeout evidence auditable and fail closed. It
does not prove that an external timeout had no effect and does not promote any
executor result to completion.
