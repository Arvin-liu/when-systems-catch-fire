# IGNITION-135 Step 02 — deterministic projection preflight

本步把 full suite 前的 generated-output cleanliness 变成显式、只读、可机器判定的 preflight。`tools/run_projection_preflight.py --check` 从自身路径推导 repository/application root，在 `ignition/` 作为 subprocess cwd，逐项执行 contract 中的 `--check`/validator 命令；不会自动 regeneration。`--record` 是单独的、显式的 receipt 写入动作。

覆盖面包括 function/nonfunction canonical projections、function adjudication/closure、Knowledge Experience、Fire Seeds census 与 validator、blast-radius report、Current Facts/Snapshot/七个 Surface Compiler surface、Current semantic/determinism checks、Human Surface contract/fingerprint、volatile registry、durability projection hygiene 与 repository path manifest。

本步的 stale fixtures 位于 `ignition/data/operations/iterations/135/step02-projection-preflight-fixtures-r1.json`。fixture contract 直接把任一 stale check 映射为 `projection_checks_pass=false` 与 `release_admission=false`；因此“先跑 suite、之后再知道 projection stale”不能进入 release gate。

验证记录写入 `ignition/data/operations/iterations/135/step02-projection-preflight.json`。11 项 Human Surface 的语义审计在 `step02-human-surface-semantic-audit.json`，最终 fingerprint-only 收口在 `step02-human-surface-final-fingerprint-refresh.json`；两者都明确记录没有改写人话或 claim ceiling。由于 preflight 记录属于本步尚未提交的工作树，它可以记录 `clean_tree_before=false`；正式 candidate release gate 必须使用同一 runner 的 `--require-clean`，并在 full suite 前后再次证明 clean。任何 check 造成 tracked/untracked tree 变化都会使 preflight FAIL。

修复边界：Fire Seeds census 新增了真正的 `--check` 分支；该分支只比较新鲜派生内容，不写入 `seed-census.json`。其余生成器继续遵循“显式 generator repair，再次 `--check`”的分离。

claim ceiling：本步只证明 repository-local deterministic projection cleanliness 与 gate 行为，不证明外部真值、生产安全、Owner acceptance 或 epistemic acceptance。
