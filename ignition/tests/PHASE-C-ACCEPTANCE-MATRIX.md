# Q32I Phase C acceptance matrix

All entries call `execute_plan`, the production executor entrypoint, against a real temporary Git repository and real subprocess producers/validators.

| ID | Requirement | Test | Expected and actual result | Status |
|---|---|---|---|---|
| C01 | Default dry-run, zero writes | `test_c01_default_dry_run_zero_write` | Producer/cache not written; structured dry-run record | PASS |
| C02 | Clean/isolated apply gate | `test_c02_apply_clean_and_isolated_gate` | Dirty ordinary tree rejected; explicit isolation applied | PASS |
| C03 | Registered argv only | `test_c03_only_registered_profile_argv_executes` | Caller-supplied command ignored; profile command ran | PASS |
| C04 | Shell metacharacters | `test_c04_shell_metacharacters_never_interpreted` | Metacharacter argv rejected; no side effect | PASS |
| C05 | Argv injection | `test_c05_argv_injection_rejected` | Shell/string producer rejected fail-closed | PASS |
| C06 | Path attacks | `test_c06_path_attacks_rejected` | POSIX absolute, Windows, traversal, symlink escape rejected | PASS |
| C07 | Unregistered output | `test_c07_unregistered_output_write_blocked` | Real rogue write detected, execution failed, rogue file removed | PASS |
| C08 | Complete action record | `test_c08_complete_execution_record` | Identity, argv, states, streams, code, fingerprints, validator, cache, rollback recorded | PASS |
| C09 | Legitimate cache hit | `test_c09_legitimate_cache_hit_revalidates_freshness` | First apply stored identity; unchanged rerun hit without producer | PASS |
| C10 | Cache tampering | `test_c10_cache_tampering_rejected` | Modified manifest failed integrity and missed | PASS |
| C11 | Profile identity | `test_c11_profile_identity_mismatch_rejected` | Schema/profile identity change missed old cache | PASS |
| C12 | Registry/topology identity | `test_c12_registry_and_topology_mismatch_rejected` | Each authority digest change independently missed | PASS |
| C13 | Producer/validator identity | `test_c13_producer_and_validator_identity_mismatch_rejected` | Each argv identity change independently missed | PASS |
| C14 | Stale generated output | `test_c14_stale_generated_output_is_not_cache_hit` | Changed output missed cache and rebuilt | PASS |
| C15 | Manual boundary | `test_c15_manual_authored_boundary` | Manual action recorded without subprocess | PASS |
| C16 | External attestation boundary | `test_c16_external_attestation_boundary` | Attestation required; forged local producer not run | PASS |
| C17 | Stop and rollback | `test_c17_failure_stops_and_rolls_back` | Second action failure stopped third and restored first output | PASS |
| C18 | Recovery package | `test_c18_failed_rollback_complete_recovery_package` | Backups, fingerprints, SHA-256, steps, logs, identities and unrecovered list emitted | PASS |
