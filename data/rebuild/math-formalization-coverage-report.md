# 纯数学函数与推导覆盖报告

- run_id: `20260614-050603`
- generated_at: `2026-06-13T21:06:03.650336+00:00`
- total_required: 1068
- total_with_math: 1068
- blockers: 0
- converged: true
- supplement_hash_round_1: `4fc4415ee5a6f103d7b40c9506b2b89c6b68c94a347fad1c79df2bc582bb44c6`
- supplement_hash_round_2: `4fc4415ee5a6f103d7b40c9506b2b89c6b68c94a347fad1c79df2bc582bb44c6`
- delta_previous_round: 0

## 分层覆盖 / Layer Coverage

| Layer | Required | With math | Blockers |
|---|---:|---:|---:|
| function | 470 | 470 | 0 |
| case | 578 | 578 | 0 |
| prediction | 8 | 8 | 0 |
| answer | 12 | 12 | 0 |
| discovery | 0 | 0 | 0 |

## 门控规则 / Gate Rule

凡函数、案例、发现、预测、新答案的新增或改写，必须同时写入 `mathematical_formalization` 与 `mathematical_derivation`；缺失纯数学表达、定义域/值域、推导步骤、正反检查或收敛状态时，正反交叉自举循环判定该写入无效。
