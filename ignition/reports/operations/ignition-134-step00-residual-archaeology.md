# IGNITION-20260822-134 Step 00 — Residual archaeology and projection contract audit

Status: `BASELINE_REPRODUCED`

The refreshed control ref is `Arvin-liu/1111:origin/relay/current@3fc8a329eb4f581d1940688046bdc16f4594417d`. The isolated formal worktree starts from `Arvin-liu/when-systems-catch-fire:main@517510aed545ff440c3464536ba2964c94e5f560` and was clean before the audit.

## Current path manifest

`ignition/tools/foundation/validate_repository_path_classification.py` explicitly defines `classification-manifest.jsonl` as a generated snapshot of the deterministic live engine. Its `--check` mode compares the live Git path set to the committed manifest and fails closed on missing, stale, duplicate, category-drift, unresolved, and anti-backflow violations. The clean Current baseline therefore cannot treat missing paths as an immutable historical snapshot merely because the missing paths were introduced by prior tasks.

The observed baseline is:

- live tracked paths: **2,958**;
- committed manifest rows: **2,720**;
- missing Current paths: **238**;
- missing-object-set SHA-256: `23b63fe8caa68223c6eeea99eb6c4cfb800e6f7408ac189a68890ea7ca54027c`;
- stale: **0**, unresolved: **0**, duplicate: **0**, category drift: **0**, anti-backflow violations: **0**.

The validator fails only `manifest:all-tracked-accounted`; the representative missing paths are the Task129/130/132 formal result and machine-receipt paths. Git history and prior receipts remain the historical record; the Current manifest must be regenerated for the live tree.

## Human Surface and other residuals

The Human/front-door validator reproduces exactly these 11 source-hash drifts: `D127`, `D182`, `D190`, `D260`, `T2`, `Y1`, `NFC-015cfd6ba387c9b1`, `NFC-02f68962a6f13abc`, `NFC-0331afe8d84f2538`, `NFC-14866124cc1a2cae`, and `NFC-154bdc1ff37c47f6`. No semantic decision is made in Step 00; each item is held for the Step 06 source-revision and human-surface audit.

The historical 104–106 propagation validator reports nine mismatch dimensions across the three sealed historical tasks (`MACHINE_RECORD_IMPACT`, `PROJECT_STATE_IMPACT`, and `SYSTEM_MAP_IMPACT`). The T16 probe reports `SYMPY_UNAVAILABLE:ModuleNotFoundError`; the repository inventory already classifies this as one environmental residual and it is not a proof pass.

The prior Task133 result records full unittest discovery as `TIMEOUT_CLASSIFIED_AT_30_SECONDS`. Task134 changes the execution contract: the full command must receive a genuinely long window, and any non-completion must identify the concrete test or child process rather than reuse the short timeout label.

## Historical trend and decision

Prior receipts record path-manifest observations of 96 (Task129), 194 (Task132), and 198 baseline / 232 candidate (Task133), while the live Task134 baseline is already 238 because the published Task133 result paths are tracked. The repeated growth is evidence of Current projection drift, not permission to enlarge a historical residual. Task134 therefore establishes a stable residual ledger and delta gate, regenerates the Current manifest, and preserves all old observations by commit and receipt provenance.

This audit is repository-local evidence only. It does not establish external truth, production readiness, Owner acceptance, or epistemic acceptance.
