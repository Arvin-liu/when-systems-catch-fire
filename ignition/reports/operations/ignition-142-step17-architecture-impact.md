# IGNITION-142 Step 17 — architecture impact

Step 17 records an architecture-changing transition. The existing registry-derived
system map remains the only map; it now projects three canonical OS overlays:
Formal Task Lifecycle R1, Open Obligation Registry R1 and Executor Admission R1.

Formal Task Lifecycle owns terminality from task scope, steps, publication and
witness. Open Obligation Registry owns the long-lived obligation identity and
carry-forward. Executor Admission is the provider-neutral gate before the live
bridge. The map keeps the compact visible relation subset while all six new
relations remain in the typed topology and are machine-validated.

Evidence: `data/operations/iterations/142/step17-architecture-impact.json`,
`data/operations/project-components.json` 2.4.0,
`data/operations/change-propagation-topology.json` 1.13.0,
`data/architecture/interactive-system-map.json` 0.16.0,
`data/architecture/current-system-identity.json` R8, and the Step 17 Current
State synchronization receipt.

The transition does not start a live process, read secret content, change
configuration or billing, or add a second system map. It does not establish
external truth, production readiness, Owner acceptance or epistemic acceptance.
