# 121Q25C Lifecycle-Gate Deadlock Repair

Q25B correctly separated completion states but incorrectly required `project_synchronization_complete` for Accepted. Because Pages can be deployed from main only after merge, this made acceptance and merge mutually unreachable.

Q25C evaluates each triggered surface's `blocks` list at Ready, Accepted, Merged, Current and Closed. The Pages homepage is post-merge and blocks only Current/Closed. It may remain pending through independent acceptance and merge, while Current/Closed continue to require main deployment and live fetch.

Every triggered external surface now has an individual attestation record. A global true value cannot hide a missing, pending, duplicate, unknown or wrong-authority surface entry. Repository evidence must resolve to an existing path; external evidence uses a typed `external:<authority-kind>:<locator>` form. Local validation always reports live external truth false.

Q25B is preserved as superseded non-ready history. Q25C is the sole final Ready method candidate on PR #57. This report proves only the repository contract and tests; it does not attest production Pages or make method 1.1.0 current.
