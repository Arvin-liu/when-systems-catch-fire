# 纯数学函数与推导覆盖报告

- run_id: `20260615-090847`
- generated_at: `2026-06-15T01:08:47.895672+00:00`
- total_required: 1177
- total_with_math: 1177
- blockers: 0
- converged: true
- supplement_hash_round_1: `b07a9ee0cc84fa50280c9e637bfb21f6a1e22df13d873d2cb8cd4d14a35ef6bb`
- supplement_hash_round_2: `b07a9ee0cc84fa50280c9e637bfb21f6a1e22df13d873d2cb8cd4d14a35ef6bb`
- delta_previous_round: 0

## 分层覆盖 / Layer Coverage

| Layer | Required | With math | Blockers |
|---|---:|---:|---:|
| function | 475 | 475 | 0 |
| case | 594 | 594 | 0 |
| prediction | 8 | 8 | 0 |
| answer | 12 | 12 | 0 |
| discovery | 88 | 88 | 0 |

## 门控规则 / Gate Rule

凡函数、案例、发现、预测、新答案的新增或改写，必须同时写入 `mathematical_formalization` 与 `mathematical_derivation`；缺失纯数学表达、定义域/值域、推导步骤、正反检查或收敛状态时，正反交叉自举循环判定该写入无效。
