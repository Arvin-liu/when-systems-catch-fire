# IGNITION-137 Step 14 — adversarial / fault matrix

The inherited live fault matrix exercised 27 cases and returned `all_fail_closed=true`: stale leases, executor/permission/workspace widening, workspace mutations, malformed results, wrong answers, duplicate dispatch/receipts, timeout/cancellation uncertainty, capability revocation and drift, privacy fields, channel/browser/remote-Git effects, billing authority, forged completion, and advisory priority escalation.

The Task137 overlay explicitly maps all 18 required dimensions, including depth-two reentrancy, copied nonce, forged reconciliation closeout, output bounds, environment leakage, private session pointer, formal-repo mutation, retry-before-reconciliation, epistemic acceptance escalation, and production-readiness inference. The one real attempt’s unchanged formal HEAD/status and `NO_BLIND_RETRY` decision are included as observed evidence.

The matrix and 21 targeted tests passed with 0 failures, 0 errors, and 0 skips. This is offline adversarial evidence only; it does not promote the failed live attempt or close `LIVE_EXTERNAL_INVOCATION`.
