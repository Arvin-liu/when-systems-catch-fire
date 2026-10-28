# 096 CLM 对齐层 v2

- 基于：Ψ₀ := C×M×I_iso×L_meta×G_δ×P_meta（未改动）
- 新增对象类型接口（补丁库侧）：intervention_control, 新增 level_scale 对象类型, 新增 temporal_dynamics 对象类型, 新增 stochastic_uncertainty 对象类型, 新增 optimization_tradeoff 对象类型, 新增 path_dependence 对象类型, 新增 representation_language 对象类型, 新增 computational_complexity 对象类型
- 增强接口（引擎内部字段）：GAP-009, GAP-010, GAP-011, GAP-012, GAP-013, GAP-014

## 路由规则
点火框架接收外部学科输入时，先按 gap 路由到对应 object_type 接口；接口仅承载外部理论的结构化表示，不参与 Ψ₀ 核心判定；核心判定仍由 Ψ₀ 六组件执行。

_不修改 Ψ₀:= 定义，不新增函数编号。_
