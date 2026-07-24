# 点火生产运行时操作法 / Ignition Production Runtime — Operation

This document describes how to operate the `tools/ignition_runtime` production
layer. It is a **draft build** on branch
`production/ignition-run-promote-evolve-r1`; it is not merged, not accepted and
not current project capability. It does not change the seven-layer epistemic
architecture, the iteration method `1.3.0`, or any frozen formal protocol.

## 0. Hard boundaries (RUN / PROMOTE / EVOLVE)

The runtime has three modes with hard, statically-enforced boundaries:

| Mode | Trigger | May produce | May invoke PROMOTE/EVOLVE |
|------|---------|-------------|---------------------------|
| RUN | default; `--provider fixture|filesystem` | a `run` generation | **NO** (static guard: `run.py` contains neither `promote` nor `evolve`) |
| PROMOTE | `--authorize promote:<token>` | `promote_request` / `promote_approval` | NO (never produces an `evolve` generation) |
| EVOLVE | `--authorize evolve:<token>` + `--approved-signal <id>` | `evolve` generation | NO |

No data automatically invokes PROMOTE or EVOLVE. A `run` never auto-applies
review and never auto-triggers formal promotion or engineering work.

## 1. Core invariant

Every authoritative state change — including an ordinary RUN — commits a NEW
immutable generation under `generations/<gen_id>/`. Committed generations are
**never mutated in place**. A crash leaves exactly the old generation or the new
one as the visible `CURRENT`; there is no half-written visible state.

Storage layout (on-disk):

```
<store>/
  CURRENT                      # strict pointer: one safe token, no traversal, O_NOFOLLOW
  generations/
    <gen_id>/
      manifest.json            # closed manifest (self-digest; complete_file_list == digest_keys == actual)
      store_identity.json
      materials.json
      results.json
      candidates.json
      unknowns.json
      signals.json
      promotion.json           # present only for promote_request / promote_approval
      receipt.json             # self_final_sha_claimed=false, live_refetch_required=true
      audit_index.json
  .staging/<gen_id>/           # durable staging before atomic rename + pointer swap
```

## 2. Publish sequence (old-or-new-only)

`publish_generation` is the single write path. `crash_after` injects a
`SimulatedCrash` at a durable stage to prove old-or-new-only visibility:

1. compute content-derived `gen_id` (idempotent no-op if it already exists and validates);
2. stage all ledger files under `.staging/<gen_id>` (`crash_after=write_files` → old visible);
3. write manifest + receipt + audit_index (`crash_after=manifest` → old visible);
4. `fsync` every staged file + staging dir (`crash_after=staged` → old visible, staging orphan);
5. atomic `os.replace` staging → `generations/<gen_id>` (`crash_after=renamed` → old visible);
6. atomic pointer `swap` (`crash_after=swap` → new fully present).

## 3. Closed manifest (triple equality)

For each `op_type`, `CANON` fixes the required file set. Validation proves:

```
complete_file_list (CANON[op_type]) == digest_keys == actual_files
```

Deleting a file **and** its digest entry is still rejected because the required
set is fixed by `op_type`. The manifest also carries its own `sha256`
(self-digest, computed with its own entry blanked), `committed=true`,
`immutable=true`, and a receipt that asserts `self_final_sha_claimed=false` and
`live_refetch_required=true`.

## 4. Commands

```bash
# RUN (default mode; never imports promote/evolve)
python3 -m tools.ignition_runtime run --store <dir> --provider fixture --materials M1,M2,M3,M4

# PROMOTE (reviewable package only; no formal knowledge applied)
python3 -m tools.ignition_runtime promote --store <dir> --authorize promote:<token>
python3 -m tools.ignition_runtime promote --store <dir> --authorize promote:<token> --approve <request_gen_id>

# EVOLVE (engineering work only; requires an approved signal)
python3 -m tools.ignition_runtime evolve --store <dir> --authorize evolve:<token> --approved-signal <signal_id>

# Recovery (strict; walks back past any corrupt link to the last valid generation)
python3 -m tools.ignition_runtime recover --store <dir>
python3 -m tools.ignition_runtime resume  --store <dir>   # re-run from established store
```

## 5. Strict pointer (fail closed)

An empty store bootstraps **once**. An established store with a damaged `CURRENT`
(missing, empty, multiline, traversal, symlink, dangling) **fails closed** via
`PointerError`; readers never silently re-initialize an empty ledger.

## 6. Epistemic contract

- every `candidate` claim binds to a real material `source_sha256` (ACTIVE candidates only);
- claim ceilings are bounded: `PRIMARY_VERIFIED` / `SECONDARY` / `UNKNOWN`;
- `UNKNOWN` ledger is never empty;
- `semantic_id = sha256(normalized source + claim)`, deterministic across provider reorder;
- source change tombstones the stale `semantic_id` (status `REPLACED`); revert reactivates it;
- no auto-promotion: a `run` never turns candidates into formal knowledge.

## 7. Validation

```bash
python3 -m pytest tests/ignition_runtime -q        # 45 scenarios (51 cases w/ parametrization)
python3 tools/validate_iteration_sync.py          # foundation (must stay green)
python3 -m unittest tests.test_iteration_sync
python3 tools/validate_human_front_door.py        # foundation (must stay green)
python3 -m unittest tests.test_human_front_door
```
