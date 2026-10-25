# Verify an Offline Source-Snapshot Run

`research.verify_offline_source_snapshot_run` checks a saved E37 run directory against its `receipt.json` declarations.
It reads the caller-selected run directory and writes one JSON result to stdout.

```bash
python3 -B ignition/tools/toolbox_verify_offline_source_snapshot_run.py \
  --run-dir /canonical/absolute/path/to/e37-run
```

The verifier accepts only `ignition-source-binding-slot-run-v1` receipts from the fixed `e37-source-snapshot-v1` adapter. It checks each listed file's byte length and SHA-256, and requires the directory's regular-file set to match the receipt plus `receipt.json`. It rejects symlinks, non-regular files, paths inside or containing the repository checkout, path traversal, duplicate JSON keys, concurrent tree changes and inputs beyond its bounds (128 artifacts, 64 MiB per artifact, 128 MiB total, and a 1 MiB receipt).

The tool has no network, model, search, secret, billing or write access. A passing result means only that the bytes read match the unkeyed receipt's declarations. It does not authenticate the receipt, capture origin, publisher, prior execution, semantic support or scientific validity. Missing or altered files are reported without repair or deletion.

The existing `collaboration.verify_handoff_artifact_files` tool checks a different `FederatedResultReceipt` contract under a repository-local `ignition/` workspace. It does not accept E37 run receipts or caller-selected external run directories; the two tools remain scoped separately.
