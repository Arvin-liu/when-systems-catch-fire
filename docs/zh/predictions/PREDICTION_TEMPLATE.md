# 预测模板 / Prediction Template

```json
{
  "id": "PRED-0001",
  "title": {"zh": "预测标题", "en": "Prediction Title"},
  "statement": {"zh": "预测判断内容", "en": "Prediction statement"},
  "basis": {"zh": "推出依据", "en": "Basis"},
  "test_condition": {"zh": "可验证条件", "en": "Test condition"},
  "falsification_condition": {"zh": "可证伪条件", "en": "Falsification condition"},
  "time_window": {"zh": "观察窗口或触发条件", "en": "Observation window or trigger condition"},
  "categories": [],
  "related_functions": [],
  "related_cases": [],
  "related_discoveries": [],
  "source_refs": [],
  "confidence": "low / medium / high",
  "status": "draft / active / active_pending_novelty_review / draft_pending_novelty_review / verified / falsified / deprecated / merged",
  "academic_novelty": {"status": "pending / passed / failed / inconclusive", "checked_at": "YYYY-MM-DD", "query_terms": [], "sources_checked": [], "nearest_matches": [], "novelty_claim": {"zh": "", "en": ""}, "reviewer_note": ""},
  "mathematical_formalization": {"symbol": "P_{PRED-0001}", "domain": "X_t × R_+", "codomain": "{0,1}", "math_expression": "P_{PRED-0001}(t+Δt)=1 ⇔ S_F(x_t)-S_C(x_t)>θ_{PRED-0001}", "validity_condition": "J_n^+(P_{PRED-0001})=1 ∧ J_n^-(P_{PRED-0001})=0"},
  "mathematical_derivation": {"status": "converged", "kind": "testable_prediction_inequality_derivation", "steps_math": ["define support score", "define counter-loss", "derive strict test inequality"], "forward_check": {"status": "pass", "condition": "J_n^+(P)=1"}, "reverse_check": {"status": "fail", "condition": "J_n^-(P)=0"}, "convergence": "ΔP=∅ ∧ (J_n^+,J_n^-)=(1,0)"},
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD",
  "page": "docs/zh/predictions/items/PRED-0001.md"
}
```

每条正式预测必须有可验证条件、可证伪条件、时间窗口、来源回指、相关对象、分类、状态与置信度。
每条正式预测还必须有 academic_novelty 字段；active 条目只有在 academic_novelty.status = passed 时才可保持 active。
每条新增或改写预测必须写入 `mathematical_formalization` 与 `mathematical_derivation`；缺少纯数学表达、定义域/值域、推导步骤、正反检查或收敛状态时，按正反交叉自举循环判定为无效写入。
