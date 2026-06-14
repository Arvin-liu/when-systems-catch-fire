# 纯数学函数与推导覆盖报告

- run_id: `20260614-101101`
- generated_at: `2026-06-14T02:11:01.364640+00:00`
- total_required: 1187
- total_with_math: 1187
- blockers: 0
- converged: true
- supplement_hash_round_1: `5aed2386cb945587356123adbaad433be816611a78d73b208ae3692f784d846f`
- supplement_hash_round_2: `5aed2386cb945587356123adbaad433be816611a78d73b208ae3692f784d846f`
- delta_previous_round: 0

## 分层覆盖 / Layer Coverage

| Layer | Required | With math | Blockers |
|---|---:|---:|---:|
| function | 470 | 470 | 0 |
| case | 578 | 578 | 0 |
| prediction | 8 | 8 | 0 |
| answer | 12 | 12 | 0 |
| effect | 36 | 36 | 0 |
| discovery | 83 | 83 | 0 |

## 门控规则 / Gate Rule

凡函数、案例、发现、预测、新答案、新效应的新增或改写，必须同时写入 `mathematical_formalization` 与 `mathematical_derivation`；缺失纯数学表达、定义域/值域、推导步骤、正反检查或收敛状态时，正反交叉自举循环判定该写入无效。
