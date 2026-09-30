# IGNITION-20260929-229 — Clean Transfer Interface Test R0

This subtree contains the frozen preregistration and deterministic analysis contract for the Task229 transfer-only experiment. It is created before any Task225 A/B/C case or sealed target content is opened.

The six Task228 policies and their source instruments remain immutable. The experiment has six fixed lineages and three conditions per lineage. `M0_PLUS_E1` is descriptive only. The exact session mapping is in `condition-manifest.json`; the execution order is in `session-order.json`.

Run the pre-freeze mechanical checks with:

```sh
python3 ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/validate_preregistration.py
python3 ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/freeze_manifest.py --check
python3 ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/tools/recompute.py --self-test
```

The target-opening gate is separate from preregistration validation. No case or target material may be opened until the frozen PR exact head has successful exact-head CI and `tools/target_opening_gate.py` writes a passing receipt under `run/`.
