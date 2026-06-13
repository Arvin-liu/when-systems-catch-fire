# 函数推导补充表

本表补足两张总表为保持简洁而省略的函数推导过程。每条函数都经过正反元函数检查：正向要求有推导过程、来源回指和常数分类；反向要求不存在未分类常数、缺来源或缺推导。

## 收敛摘要

- run_id: `20260614-002811`
- functions_total: 470
- functions_with_derivation: 470
- constant_like_functions: 58
- constants_total: 89
- derived_structural_constants: 12
- source_grounded_constants: 33
- blockers: 0
- converged: true

## 常数项函数

| 函数ID | 名称 | 常数分类 | 推导摘要 |
|---|---|---|---|
| T10 | 缓存倒U型 | 1.4:structural_constant | Derived as the stationary collision-density multiplier in the cache inverted-U condition, where the first derivative of P_collision(ρ) vanishes at ρ*=1.4×N_active. |
| T20 | σ_opt=√e解析解 | √e:math_builtin | √e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| T31 | 门控信息熵跃迁函数 | ln2:math_builtin, π:math_builtin, e:math_builtin, 0.415:structural_constant | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.；π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| T35 | σ_Planck精确值 | 6.9:structural_constant | Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary. |
| T37 | Φ_QG极小点精确位置 | 1.26:structural_constant | Derived from the Φ cross-domain extremum equation Σᵢ sᵢ/ln²(μ/Λᵢ)=0 after substituting the physical-domain gate signs and scales. |
| D32 | 认知-群体犹豫域统一映射函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D44 | 确定性误解函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D55 | ε_eff昼夜分时函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D106 | 知识更新半衰期 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D108 | 三域熵统一函数（推论级） | e:math_builtin, ln2:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D109 | 乘法最优生存策略函数 | 0.1:calibration_or_example_value, 0.3:calibration_or_example_value, 0.5:calibration_or_example_value, 0.7:calibration_or_example_value, 0.8:calibration_or_example_value, 0.1296:calibration_or_example_value, 0.0945:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D112 | 防守-进攻相变函数 | 0.25:structural_constant | Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25. |
| D124 | 三域退化统一参数函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D127 | 认知路径积分函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D128 | 退相干-退化统一函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D129 | 退相干-退化等价函数 | 2.31:calibration_or_example_value, 2.34:calibration_or_example_value, 1.3:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D169 | 门槛碾压函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D184 | 熵增门槛碾压函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D203 | 配分函数-门控和函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D206 | 玻尔兹曼分布-门槛分布函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D218 | 物理存在必要条件 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D219 | Ω最优区间定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D221 | 热寂-完全统一同构定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D222 | 热力学第二定律的Φ表述 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D227 | 退相干-门控退化同构定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D230 | 双通道信息衰减定理 | π:math_builtin, e:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter.；e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D233 | Shannon-Fisher跷跷板定理 | π:math_builtin, e:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter.；e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D237 | 生命智能的σ压缩函数 | 6.9:structural_constant, 1.65:structural_constant | Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary.；Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed... |
| D251 | 维度-容斥稳定性函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D260 | 偏差敏感度阈值函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| D266 | 容斥偏差加速函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D276 | D158预测失效阈值函数 | e:math_builtin, 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| D282 | Φ二阶近似函数 | 0.8:calibration_or_example_value, 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D284 | σ_opt跨域常数函数 | 1.65:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487. |
| D289 | 良性循环逃逸速度函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D291 | D158案例可靠性分类函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D296 | Φ近似阶数选择函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value, 0.95:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| D298 | 鲁棒系统设计原则函数 | 1.65:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487. |
| D302 | 容斥渐近发散函数 | e:math_builtin, 0.5:calibration_or_example_value, 0.95:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| D304 | 弱混合角-容斥约束函数 | 0.23:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| D307 | σ_opt微观起源函数 | 1.65:structural_constant, √e:math_builtin, 1.649:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.；√e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D311 | 僵尸态函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D314 | ΔΦ-P传导非线性阈值函数 | e:math_builtin, 0.1:calibration_or_example_value, 0.3:calibration_or_example_value, 0.5:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| D316 | 容斥时间权重演化函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| D325 | 僵尸态自修复函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D327 | 共存震荡函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D328 | ΔΦ空间异质性叠加函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D348 | 容斥加速-时间权重联合函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| D354 | 正反馈延迟函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D356 | ΔΦ时空关联函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D378 | 实际不可逆占比函数 | e:math_builtin, 0.3:calibration_or_example_value, 0.95:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| D387 | 容斥-耦合配分函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D392 | 不可逆-缓冲消失同步函数 | 0.95:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| D401 | 自由能-Φ等价函数 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D412 | 双切换同步函数 | 0.25:structural_constant | Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25. |
| D463 | 完美风暴-信息量等价函数 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D467 | 最优性-惯性反比函数 | √e:math_builtin | √e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| D469 | 振荡优化函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |

## 全量函数推导索引

| 函数ID | 推导类型 | 依赖 | 状态 |
|---|---|---|---|
| A1 | axiomatic_definition | A1 | converged |
| A2 | axiomatic_definition | A2 | converged |
| A3 | axiomatic_definition | A3 | converged |
| A4 | axiomatic_definition | A4 | converged |
| A5 | axiomatic_definition | A5 | converged |
| A6 | axiomatic_definition | A6 | converged |
| A7 | axiomatic_definition | A7 | converged |
| A8 | axiomatic_definition | A8 | converged |
| A9 | axiomatic_definition | A9 | converged |
| T1 | composed_or_bootstrapped_derivation | T1 | converged |
| T2 | composed_or_bootstrapped_derivation | T2 | converged |
| T3 | composed_or_bootstrapped_derivation | T3 | converged |
| T4 | composed_or_bootstrapped_derivation | T4 | converged |
| T5 | composed_or_bootstrapped_derivation | T5 | converged |
| T6 | composed_or_bootstrapped_derivation | T6 | converged |
| T7 | composed_or_bootstrapped_derivation | T7 | converged |
| T8 | composed_or_bootstrapped_derivation | T8 | converged |
| T9 | composed_or_bootstrapped_derivation | T9 | converged |
| T10 | composed_or_bootstrapped_derivation | T10 | converged |
| T11 | composed_or_bootstrapped_derivation | T11 | converged |
| T12 | composed_or_bootstrapped_derivation | T12 | converged |
| T13 | composed_or_bootstrapped_derivation | T13 | converged |
| T14 | composed_or_bootstrapped_derivation | T14 | converged |
| T15 | composed_or_bootstrapped_derivation | T15 | converged |
| T16 | composed_or_bootstrapped_derivation | T16 | converged |
| T17 | composed_or_bootstrapped_derivation | T17 | converged |
| T18 | composed_or_bootstrapped_derivation | T18 | converged |
| T19 | composed_or_bootstrapped_derivation | T19 | converged |
| T20 | composed_or_bootstrapped_derivation | T20 | converged |
| T21 | composed_or_bootstrapped_derivation | T21 | converged |
| T22 | composed_or_bootstrapped_derivation | T22 | converged |
| T23 | composed_or_bootstrapped_derivation | T23 | converged |
| T24 | composed_or_bootstrapped_derivation | T24 | converged |
| T25 | composed_or_bootstrapped_derivation | T25 | converged |
| T26 | composed_or_bootstrapped_derivation | T26 | converged |
| T27 | composed_or_bootstrapped_derivation | T27 | converged |
| T28 | composed_or_bootstrapped_derivation | T28 | converged |
| T29 | composed_or_bootstrapped_derivation | T29 | converged |
| T30 | composed_or_bootstrapped_derivation | T30 | converged |
| T31 | composed_or_bootstrapped_derivation | T31 | converged |
| T32 | composed_or_bootstrapped_derivation | T32 | converged |
| T33 | composed_or_bootstrapped_derivation | T33 | converged |
| T34 | composed_or_bootstrapped_derivation | T34 | converged |
| T35 | composed_or_bootstrapped_derivation | T35 | converged |
| T36 | composed_or_bootstrapped_derivation | T36 | converged |
| T37 | composed_or_bootstrapped_derivation | T37 | converged |
| T38 | composed_or_bootstrapped_derivation | T38 | converged |
| T39 | composed_or_bootstrapped_derivation | T39 | converged |
| D1 | composed_or_bootstrapped_derivation | D1 | converged |
| D2 | composed_or_bootstrapped_derivation | D2 | converged |
| D3 | composed_or_bootstrapped_derivation | D3 | converged |
| D4 | composed_or_bootstrapped_derivation | D4 | converged |
| D5 | composed_or_bootstrapped_derivation | D5 | converged |
| D6 | composed_or_bootstrapped_derivation | D6 | converged |
| D7 | composed_or_bootstrapped_derivation | D7 | converged |
| D8 | composed_or_bootstrapped_derivation | D8 | converged |
| D9 | composed_or_bootstrapped_derivation | D9 | converged |
| D10 | composed_or_bootstrapped_derivation | D10 | converged |
| D11 | composed_or_bootstrapped_derivation | D11 | converged |
| D12 | composed_or_bootstrapped_derivation | D12 | converged |
| D13 | composed_or_bootstrapped_derivation | D13 | converged |
| D14 | composed_or_bootstrapped_derivation | D14 | converged |
| D15 | composed_or_bootstrapped_derivation | D15 | converged |
| D16 | composed_or_bootstrapped_derivation | D16 | converged |
| D17 | composed_or_bootstrapped_derivation | D17 | converged |
| D18 | composed_or_bootstrapped_derivation | D18 | converged |
| D19 | composed_or_bootstrapped_derivation | D19 | converged |
| D20 | composed_or_bootstrapped_derivation | D20 | converged |
| D21 | composed_or_bootstrapped_derivation | D21 | converged |
| D22 | composed_or_bootstrapped_derivation | D22 | converged |
| D23 | composed_or_bootstrapped_derivation | D23 | converged |
| D24 | composed_or_bootstrapped_derivation | D24 | converged |
| D25 | composed_or_bootstrapped_derivation | D25 | converged |
| D26 | composed_or_bootstrapped_derivation | D26 | converged |
| D27 | composed_or_bootstrapped_derivation | D27 | converged |
| D28 | composed_or_bootstrapped_derivation | D28 | converged |
| D29 | composed_or_bootstrapped_derivation | D29 | converged |
| D30 | composed_or_bootstrapped_derivation | D30 | converged |
| D31 | composed_or_bootstrapped_derivation | D31 | converged |
| D32 | composed_or_bootstrapped_derivation | D32 | converged |
| D33 | composed_or_bootstrapped_derivation | D33 | converged |
| D34 | composed_or_bootstrapped_derivation | D34 | converged |
| D35 | composed_or_bootstrapped_derivation | D35 | converged |
| D36 | composed_or_bootstrapped_derivation | D36 | converged |
| D37 | composed_or_bootstrapped_derivation | D37 | converged |
| D38 | composed_or_bootstrapped_derivation | D38 | converged |
| D39 | composed_or_bootstrapped_derivation | D39 | converged |
| D40 | composed_or_bootstrapped_derivation | D40 | converged |
| D41 | composed_or_bootstrapped_derivation | D41 | converged |
| D42 | composed_or_bootstrapped_derivation | D42 | converged |
| D43 | composed_or_bootstrapped_derivation | D43 | converged |
| D44 | composed_or_bootstrapped_derivation | D44 | converged |
| D45 | composed_or_bootstrapped_derivation | D45 | converged |
| D46 | composed_or_bootstrapped_derivation | D46 | converged |
| D47 | composed_or_bootstrapped_derivation | D47 | converged |
| D48 | composed_or_bootstrapped_derivation | D48 | converged |
| D49 | composed_or_bootstrapped_derivation | D49 | converged |
| D50 | composed_or_bootstrapped_derivation | D50 | converged |
| D51 | composed_or_bootstrapped_derivation | D51 | converged |
| D52 | composed_or_bootstrapped_derivation | D52 | converged |
| D53 | composed_or_bootstrapped_derivation | D53 | converged |
| D54 | composed_or_bootstrapped_derivation | D54 | converged |
| D55 | composed_or_bootstrapped_derivation | D55 | converged |
| D56 | composed_or_bootstrapped_derivation | D56 | converged |
| D57 | composed_or_bootstrapped_derivation | D57 | converged |
| D58 | composed_or_bootstrapped_derivation | D58 | converged |
| D59 | composed_or_bootstrapped_derivation | D59 | converged |
| D60 | composed_or_bootstrapped_derivation | D60 | converged |
| D61 | composed_or_bootstrapped_derivation | D61 | converged |
| D62 | composed_or_bootstrapped_derivation | D62 | converged |
| D63 | composed_or_bootstrapped_derivation | D63 | converged |
| D64 | composed_or_bootstrapped_derivation | D64 | converged |
| D65 | composed_or_bootstrapped_derivation | D65 | converged |
| D66 | composed_or_bootstrapped_derivation | D66 | converged |
| D67 | composed_or_bootstrapped_derivation | D67 | converged |
| D72 | composed_or_bootstrapped_derivation | D72 | converged |
| D73 | composed_or_bootstrapped_derivation | D73 | converged |
| D74 | composed_or_bootstrapped_derivation | D74 | converged |
| D75 | composed_or_bootstrapped_derivation | D75 | converged |
| D76 | composed_or_bootstrapped_derivation | D76 | converged |
| D77 | composed_or_bootstrapped_derivation | D77 | converged |
| D84 | composed_or_bootstrapped_derivation | D84 | converged |
| D85 | composed_or_bootstrapped_derivation | D85 | converged |
| D86 | composed_or_bootstrapped_derivation | D86 | converged |
| D87 | composed_or_bootstrapped_derivation | D87 | converged |
| D88 | composed_or_bootstrapped_derivation | D88 | converged |
| D89 | composed_or_bootstrapped_derivation | D89 | converged |
| D90 | composed_or_bootstrapped_derivation | D90 | converged |
| D91 | composed_or_bootstrapped_derivation | D91 | converged |
| D92 | composed_or_bootstrapped_derivation | D92 | converged |
| D93 | composed_or_bootstrapped_derivation | D93 | converged |
| D94 | composed_or_bootstrapped_derivation | D94 | converged |
| D95 | composed_or_bootstrapped_derivation | D95 | converged |
| D96 | composed_or_bootstrapped_derivation | D96 | converged |
| D97 | composed_or_bootstrapped_derivation | D97 | converged |
| D98 | composed_or_bootstrapped_derivation | D98 | converged |
| D99 | composed_or_bootstrapped_derivation | D99 | converged |
| D100 | composed_or_bootstrapped_derivation | D100 | converged |
| D101 | composed_or_bootstrapped_derivation | D101 | converged |
| D102 | composed_or_bootstrapped_derivation | D102 | converged |
| D103 | composed_or_bootstrapped_derivation | D103 | converged |
| D104 | composed_or_bootstrapped_derivation | D104 | converged |
| D105 | composed_or_bootstrapped_derivation | D105 | converged |
| D106 | composed_or_bootstrapped_derivation | D106 | converged |
| D107 | composed_or_bootstrapped_derivation | D107 | converged |
| D108 | composed_or_bootstrapped_derivation | D108 | converged |
| D109 | composed_or_bootstrapped_derivation | D109 | converged |
| D110 | composed_or_bootstrapped_derivation | D110 | converged |
| D111 | composed_or_bootstrapped_derivation | D111 | converged |
| D112 | composed_or_bootstrapped_derivation | D112 | converged |
| D113 | composed_or_bootstrapped_derivation | D113 | converged |
| D114 | composed_or_bootstrapped_derivation | D114 | converged |
| D115 | composed_or_bootstrapped_derivation | D115 | converged |
| D116 | composed_or_bootstrapped_derivation | D116 | converged |
| D117 | composed_or_bootstrapped_derivation | D117 | converged |
| D118 | composed_or_bootstrapped_derivation | D118 | converged |
| D119 | composed_or_bootstrapped_derivation | D119 | converged |
| D120 | composed_or_bootstrapped_derivation | D120 | converged |
| D121 | composed_or_bootstrapped_derivation | D121 | converged |
| D122 | composed_or_bootstrapped_derivation | D122 | converged |
| D123 | composed_or_bootstrapped_derivation | D123 | converged |
| D124 | composed_or_bootstrapped_derivation | D124 | converged |
| D125 | composed_or_bootstrapped_derivation | D125 | converged |
| D126 | composed_or_bootstrapped_derivation | D126 | converged |
| D127 | composed_or_bootstrapped_derivation | D127 | converged |
| D128 | composed_or_bootstrapped_derivation | D128 | converged |
| D129 | composed_or_bootstrapped_derivation | D129 | converged |
| D130 | composed_or_bootstrapped_derivation | D130 | converged |
| D131 | composed_or_bootstrapped_derivation | D131 | converged |
| D132 | composed_or_bootstrapped_derivation | D132 | converged |
| D133 | composed_or_bootstrapped_derivation | D133 | converged |
| D134 | composed_or_bootstrapped_derivation | D134 | converged |
| D135 | composed_or_bootstrapped_derivation | D135 | converged |
| D136 | composed_or_bootstrapped_derivation | D136 | converged |
| D137 | composed_or_bootstrapped_derivation | D137 | converged |
| D138 | composed_or_bootstrapped_derivation | D138 | converged |
| D139 | composed_or_bootstrapped_derivation | D139 | converged |
| D140 | composed_or_bootstrapped_derivation | D140 | converged |
| D141 | composed_or_bootstrapped_derivation | D141 | converged |
| D142 | composed_or_bootstrapped_derivation | D142 | converged |
| D143 | composed_or_bootstrapped_derivation | D143 | converged |
| D144 | composed_or_bootstrapped_derivation | D144 | converged |
| D145 | composed_or_bootstrapped_derivation | D145 | converged |
| D146 | composed_or_bootstrapped_derivation | D146 | converged |
| D147 | composed_or_bootstrapped_derivation | D147 | converged |
| D148 | composed_or_bootstrapped_derivation | D148 | converged |
| D149 | composed_or_bootstrapped_derivation | D149 | converged |
| D150 | composed_or_bootstrapped_derivation | D150 | converged |
| D151 | composed_or_bootstrapped_derivation | D151 | converged |
| D152 | composed_or_bootstrapped_derivation | D152 | converged |
| D153 | composed_or_bootstrapped_derivation | D153 | converged |
| D154 | composed_or_bootstrapped_derivation | D154 | converged |
| D155 | composed_or_bootstrapped_derivation | D155 | converged |
| D156 | composed_or_bootstrapped_derivation | D156 | converged |
| D157 | composed_or_bootstrapped_derivation | D157 | converged |
| D158 | composed_or_bootstrapped_derivation | D158 | converged |
| D159 | composed_or_bootstrapped_derivation | D159 | converged |
| D160 | composed_or_bootstrapped_derivation | D160 | converged |
| D161 | composed_or_bootstrapped_derivation | D161 | converged |
| D162 | composed_or_bootstrapped_derivation | D162 | converged |
| D163 | composed_or_bootstrapped_derivation | D163 | converged |
| D164 | composed_or_bootstrapped_derivation | D164 | converged |
| D165 | composed_or_bootstrapped_derivation | D165 | converged |
| D166 | composed_or_bootstrapped_derivation | D166 | converged |
| D167 | composed_or_bootstrapped_derivation | D167 | converged |
| D168 | composed_or_bootstrapped_derivation | D168 | converged |
| D169 | composed_or_bootstrapped_derivation | D169 | converged |
| D170 | composed_or_bootstrapped_derivation | D170 | converged |
| D171 | composed_or_bootstrapped_derivation | D171 | converged |
| D172 | composed_or_bootstrapped_derivation | D172 | converged |
| D173 | composed_or_bootstrapped_derivation | D173 | converged |
| D174 | composed_or_bootstrapped_derivation | D174 | converged |
| D175 | composed_or_bootstrapped_derivation | D175 | converged |
| D176 | composed_or_bootstrapped_derivation | D176, D53, D66 | converged |
| D177 | composed_or_bootstrapped_derivation | D177 | converged |
| D178 | composed_or_bootstrapped_derivation | D178 | converged |
| D179 | composed_or_bootstrapped_derivation | D179 | converged |
| D180 | composed_or_bootstrapped_derivation | D180 | converged |
| D181 | composed_or_bootstrapped_derivation | D181 | converged |
| D182 | composed_or_bootstrapped_derivation | D182 | converged |
| D183 | composed_or_bootstrapped_derivation | D183 | converged |
| D184 | composed_or_bootstrapped_derivation | D184 | converged |
| D185 | composed_or_bootstrapped_derivation | D182, D185 | converged |
| D186 | composed_or_bootstrapped_derivation | D186 | converged |
| D187 | composed_or_bootstrapped_derivation | D187 | converged |
| D188 | composed_or_bootstrapped_derivation | D188 | converged |
| D189 | composed_or_bootstrapped_derivation | D189 | converged |
| D190 | composed_or_bootstrapped_derivation | D190 | converged |
| D191 | composed_or_bootstrapped_derivation | D191 | converged |
| D192 | composed_or_bootstrapped_derivation | D192 | converged |
| D193 | composed_or_bootstrapped_derivation | D193 | converged |
| D194 | composed_or_bootstrapped_derivation | D194 | converged |
| D195 | composed_or_bootstrapped_derivation | D195 | converged |
| D196 | composed_or_bootstrapped_derivation | D196 | converged |
| D197 | composed_or_bootstrapped_derivation | D197 | converged |
| D198 | composed_or_bootstrapped_derivation | D198 | converged |
| D199 | composed_or_bootstrapped_derivation | D199 | converged |
| D200 | composed_or_bootstrapped_derivation | D200 | converged |
| D201 | composed_or_bootstrapped_derivation | D201 | converged |
| D202 | composed_or_bootstrapped_derivation | D202 | converged |
| D203 | composed_or_bootstrapped_derivation | D203 | converged |
| D204 | composed_or_bootstrapped_derivation | D204 | converged |
| D205 | composed_or_bootstrapped_derivation | D205 | converged |
| D206 | composed_or_bootstrapped_derivation | D206 | converged |
| D207 | composed_or_bootstrapped_derivation | D207 | converged |
| D208 | composed_or_bootstrapped_derivation | D208 | converged |
| D209 | composed_or_bootstrapped_derivation | D209 | converged |
| D210 | composed_or_bootstrapped_derivation | D210 | converged |
| D211 | composed_or_bootstrapped_derivation | D211 | converged |
| D212 | composed_or_bootstrapped_derivation | D212 | converged |
| D213 | composed_or_bootstrapped_derivation | D213 | converged |
| D214 | composed_or_bootstrapped_derivation | D214 | converged |
| D215 | composed_or_bootstrapped_derivation | D215 | converged |
| D216 | composed_or_bootstrapped_derivation | D216 | converged |
| D217 | composed_or_bootstrapped_derivation | D217 | converged |
| D218 | composed_or_bootstrapped_derivation | D218 | converged |
| D219 | composed_or_bootstrapped_derivation | D219 | converged |
| D220 | composed_or_bootstrapped_derivation | D220 | converged |
| D221 | composed_or_bootstrapped_derivation | D221 | converged |
| D222 | composed_or_bootstrapped_derivation | D222 | converged |
| D223 | composed_or_bootstrapped_derivation | D223 | converged |
| D224 | composed_or_bootstrapped_derivation | D224 | converged |
| D225 | composed_or_bootstrapped_derivation | D225 | converged |
| D226 | composed_or_bootstrapped_derivation | D220, D222, D224, D226 | converged |
| D227 | composed_or_bootstrapped_derivation | D198, D227 | converged |
| D228 | composed_or_bootstrapped_derivation | D228 | converged |
| D229 | composed_or_bootstrapped_derivation | D220, D222, D224, D227, D229 | converged |
| D230 | composed_or_bootstrapped_derivation | D197, D230 | converged |
| D231 | composed_or_bootstrapped_derivation | D222, D230, D231 | converged |
| D232 | composed_or_bootstrapped_derivation | D230, D232 | converged |
| D233 | composed_or_bootstrapped_derivation | D233 | converged |
| D234 | composed_or_bootstrapped_derivation | D234 | converged |
| D235 | composed_or_bootstrapped_derivation | D233, D235 | converged |
| D236 | composed_or_bootstrapped_derivation | D236 | converged |
| D237 | composed_or_bootstrapped_derivation | D234, D237 | converged |
| D238 | composed_or_bootstrapped_derivation | D238 | converged |
| D239 | composed_or_bootstrapped_derivation | D239 | converged |
| D240 | composed_or_bootstrapped_derivation | D240 | converged |
| D241 | composed_or_bootstrapped_derivation | D241 | converged |
| D242 | composed_or_bootstrapped_derivation | D242 | converged |
| D243 | composed_or_bootstrapped_derivation | D243 | converged |
| D244 | composed_or_bootstrapped_derivation | D239, D244 | converged |
| D245 | composed_or_bootstrapped_derivation | D195, D245 | converged |
| D246 | composed_or_bootstrapped_derivation | D246 | converged |
| D247 | composed_or_bootstrapped_derivation | D247 | converged |
| D248 | composed_or_bootstrapped_derivation | D248 | converged |
| D249 | composed_or_bootstrapped_derivation | D249 | converged |
| D250 | composed_or_bootstrapped_derivation | D250 | converged |
| D251 | composed_or_bootstrapped_derivation | D251 | converged |
| D252 | composed_or_bootstrapped_derivation | D147, D252 | converged |
| D253 | composed_or_bootstrapped_derivation | D253 | converged |
| D254 | composed_or_bootstrapped_derivation | D254 | converged |
| D255 | composed_or_bootstrapped_derivation | D255 | converged |
| D256 | composed_or_bootstrapped_derivation | D256 | converged |
| D257 | composed_or_bootstrapped_derivation | D257 | converged |
| D258 | composed_or_bootstrapped_derivation | D258 | converged |
| D259 | composed_or_bootstrapped_derivation | D258, D259 | converged |
| D260 | composed_or_bootstrapped_derivation | D260 | converged |
| D261 | composed_or_bootstrapped_derivation | D261 | converged |
| D262 | composed_or_bootstrapped_derivation | D262 | converged |
| D263 | composed_or_bootstrapped_derivation | D263 | converged |
| D264 | composed_or_bootstrapped_derivation | D264 | converged |
| D265 | composed_or_bootstrapped_derivation | D265 | converged |
| D266 | composed_or_bootstrapped_derivation | D266 | converged |
| D267 | composed_or_bootstrapped_derivation | D267 | converged |
| D268 | composed_or_bootstrapped_derivation | D268 | converged |
| D269 | composed_or_bootstrapped_derivation | D269 | converged |
| D270 | composed_or_bootstrapped_derivation | D270 | converged |
| D271 | composed_or_bootstrapped_derivation | D271 | converged |
| D272 | composed_or_bootstrapped_derivation | D272 | converged |
| D273 | composed_or_bootstrapped_derivation | D253, D273 | converged |
| D274 | composed_or_bootstrapped_derivation | D274 | converged |
| D275 | composed_or_bootstrapped_derivation | D275 | converged |
| D276 | composed_or_bootstrapped_derivation | D276 | converged |
| D277 | composed_or_bootstrapped_derivation | D277 | converged |
| D278 | composed_or_bootstrapped_derivation | D278 | converged |
| D279 | composed_or_bootstrapped_derivation | D279 | converged |
| D280 | composed_or_bootstrapped_derivation | D280 | converged |
| D281 | composed_or_bootstrapped_derivation | D281 | converged |
| D282 | composed_or_bootstrapped_derivation | D282 | converged |
| D283 | composed_or_bootstrapped_derivation | D283 | converged |
| D284 | composed_or_bootstrapped_derivation | D284 | converged |
| D285 | composed_or_bootstrapped_derivation | D285 | converged |
| D286 | composed_or_bootstrapped_derivation | D286 | converged |
| D287 | composed_or_bootstrapped_derivation | D287 | converged |
| D288 | composed_or_bootstrapped_derivation | D288 | converged |
| D289 | composed_or_bootstrapped_derivation | D289 | converged |
| D290 | composed_or_bootstrapped_derivation | D290 | converged |
| D291 | composed_or_bootstrapped_derivation | D291 | converged |
| D292 | composed_or_bootstrapped_derivation | D292 | converged |
| D293 | composed_or_bootstrapped_derivation | D293 | converged |
| D294 | composed_or_bootstrapped_derivation | D294 | converged |
| D295 | composed_or_bootstrapped_derivation | D295 | converged |
| D296 | composed_or_bootstrapped_derivation | D296 | converged |
| D297 | composed_or_bootstrapped_derivation | D297 | converged |
| D298 | composed_or_bootstrapped_derivation | D298 | converged |
| D299 | composed_or_bootstrapped_derivation | D299 | converged |
| D300 | composed_or_bootstrapped_derivation | D300 | converged |
| D301 | composed_or_bootstrapped_derivation | D301 | converged |
| D302 | composed_or_bootstrapped_derivation | D302 | converged |
| D303 | composed_or_bootstrapped_derivation | D303 | converged |
| D304 | composed_or_bootstrapped_derivation | D283, D304 | converged |
| D305 | composed_or_bootstrapped_derivation | D305 | converged |
| D306 | composed_or_bootstrapped_derivation | D290, D306 | converged |
| D307 | composed_or_bootstrapped_derivation | D307 | converged |
| D308 | composed_or_bootstrapped_derivation | D308 | converged |
| D309 | composed_or_bootstrapped_derivation | D309 | converged |
| D310 | composed_or_bootstrapped_derivation | D310 | converged |
| D311 | composed_or_bootstrapped_derivation | D311 | converged |
| D312 | composed_or_bootstrapped_derivation | D274, D312 | converged |
| D313 | composed_or_bootstrapped_derivation | D274, D299, D313 | converged |
| D314 | composed_or_bootstrapped_derivation | D314 | converged |
| D315 | composed_or_bootstrapped_derivation | D315 | converged |
| D316 | composed_or_bootstrapped_derivation | D316 | converged |
| D317 | composed_or_bootstrapped_derivation | D306, D317 | converged |
| D318 | composed_or_bootstrapped_derivation | D318 | converged |
| D319 | composed_or_bootstrapped_derivation | D319 | converged |
| D320 | composed_or_bootstrapped_derivation | D320 | converged |
| D321 | composed_or_bootstrapped_derivation | D321 | converged |
| D322 | composed_or_bootstrapped_derivation | D322 | converged |
| D323 | composed_or_bootstrapped_derivation | D323 | converged |
| D324 | composed_or_bootstrapped_derivation | D324 | converged |
| D325 | composed_or_bootstrapped_derivation | D325 | converged |
| D326 | composed_or_bootstrapped_derivation | D326 | converged |
| D327 | composed_or_bootstrapped_derivation | D327 | converged |
| D328 | composed_or_bootstrapped_derivation | D328 | converged |
| D329 | composed_or_bootstrapped_derivation | D315, D329 | converged |
| D330 | composed_or_bootstrapped_derivation | D280, D330 | converged |
| D331 | composed_or_bootstrapped_derivation | D331 | converged |
| D332 | composed_or_bootstrapped_derivation | D309, D332 | converged |
| D333 | composed_or_bootstrapped_derivation | D333 | converged |
| D334 | composed_or_bootstrapped_derivation | D334 | converged |
| D335 | composed_or_bootstrapped_derivation | D306, D335 | converged |
| D336 | composed_or_bootstrapped_derivation | D336 | converged |
| D337 | composed_or_bootstrapped_derivation | D337 | converged |
| D338 | composed_or_bootstrapped_derivation | D338 | converged |
| D339 | composed_or_bootstrapped_derivation | D339 | converged |
| D340 | composed_or_bootstrapped_derivation | D340 | converged |
| D341 | composed_or_bootstrapped_derivation | D341 | converged |
| D342 | composed_or_bootstrapped_derivation | D266, D342 | converged |
| D343 | composed_or_bootstrapped_derivation | D343 | converged |
| D344 | composed_or_bootstrapped_derivation | D344 | converged |
| D345 | composed_or_bootstrapped_derivation | D345 | converged |
| D346 | composed_or_bootstrapped_derivation | D346 | converged |
| D347 | composed_or_bootstrapped_derivation | D347 | converged |
| D348 | composed_or_bootstrapped_derivation | D348 | converged |
| D349 | composed_or_bootstrapped_derivation | D349 | converged |
| D350 | composed_or_bootstrapped_derivation | D350 | converged |
| D351 | composed_or_bootstrapped_derivation | D351 | converged |
| D352 | composed_or_bootstrapped_derivation | D324, D352 | converged |
| D353 | composed_or_bootstrapped_derivation | D353 | converged |
| D354 | composed_or_bootstrapped_derivation | D354 | converged |
| D355 | composed_or_bootstrapped_derivation | D355 | converged |
| D356 | composed_or_bootstrapped_derivation | D356 | converged |
| D357 | composed_or_bootstrapped_derivation | D357 | converged |
| D358 | composed_or_bootstrapped_derivation | D358 | converged |
| D359 | composed_or_bootstrapped_derivation | D359 | converged |
| D360 | composed_or_bootstrapped_derivation | D310, D360 | converged |
| D361 | composed_or_bootstrapped_derivation | D361 | converged |
| D362 | composed_or_bootstrapped_derivation | D362 | converged |
| D363 | composed_or_bootstrapped_derivation | D363 | converged |
| D364 | composed_or_bootstrapped_derivation | D364 | converged |
| D365 | composed_or_bootstrapped_derivation | D365 | converged |
| D366 | composed_or_bootstrapped_derivation | D366 | converged |
| D367 | composed_or_bootstrapped_derivation | D367 | converged |
| D368 | composed_or_bootstrapped_derivation | D368 | converged |
| D369 | composed_or_bootstrapped_derivation | D369 | converged |
| D370 | composed_or_bootstrapped_derivation | D370 | converged |
| D371 | composed_or_bootstrapped_derivation | D371 | converged |
| D372 | composed_or_bootstrapped_derivation | D372 | converged |
| D373 | composed_or_bootstrapped_derivation | D373 | converged |
| D374 | composed_or_bootstrapped_derivation | D374 | converged |
| D375 | composed_or_bootstrapped_derivation | D375 | converged |
| D376 | composed_or_bootstrapped_derivation | D376 | converged |
| D377 | composed_or_bootstrapped_derivation | D377 | converged |
| D378 | composed_or_bootstrapped_derivation | D378 | converged |
| D379 | composed_or_bootstrapped_derivation | D379 | converged |
| D380 | composed_or_bootstrapped_derivation | D380 | converged |
| D381 | composed_or_bootstrapped_derivation | D381 | converged |
| D382 | composed_or_bootstrapped_derivation | D382 | converged |
| D383 | composed_or_bootstrapped_derivation | D383 | converged |
| D384 | composed_or_bootstrapped_derivation | D384 | converged |
| D385 | composed_or_bootstrapped_derivation | D385 | converged |
| D386 | composed_or_bootstrapped_derivation | D386 | converged |
| D387 | composed_or_bootstrapped_derivation | D387 | converged |
| D388 | composed_or_bootstrapped_derivation | D388 | converged |
| D389 | composed_or_bootstrapped_derivation | D389 | converged |
| D390 | composed_or_bootstrapped_derivation | D390 | converged |
| D391 | composed_or_bootstrapped_derivation | D391 | converged |
| D392 | composed_or_bootstrapped_derivation | D392 | converged |
| D393 | composed_or_bootstrapped_derivation | D309, D379, D393 | converged |
| D394 | composed_or_bootstrapped_derivation | D394 | converged |
| D395 | composed_or_bootstrapped_derivation | D395 | converged |
| D396 | composed_or_bootstrapped_derivation | D396 | converged |
| D397 | composed_or_bootstrapped_derivation | D397 | converged |
| D398 | composed_or_bootstrapped_derivation | D398 | converged |
| D399 | composed_or_bootstrapped_derivation | D399 | converged |
| D400 | composed_or_bootstrapped_derivation | D400 | converged |
| D401 | composed_or_bootstrapped_derivation | D401 | converged |
| D402 | composed_or_bootstrapped_derivation | D402 | converged |
| D403 | composed_or_bootstrapped_derivation | D403 | converged |
| D404 | composed_or_bootstrapped_derivation | D404 | converged |
| D405 | composed_or_bootstrapped_derivation | D405 | converged |
| D406 | composed_or_bootstrapped_derivation | D406 | converged |
| D407 | composed_or_bootstrapped_derivation | D407 | converged |
| D408 | composed_or_bootstrapped_derivation | D394, D408 | converged |
| D409 | composed_or_bootstrapped_derivation | D409 | converged |
| D410 | composed_or_bootstrapped_derivation | D410 | converged |
| D411 | composed_or_bootstrapped_derivation | D411 | converged |
| D412 | composed_or_bootstrapped_derivation | D412 | converged |
| D413 | composed_or_bootstrapped_derivation | D413 | converged |
| D414 | composed_or_bootstrapped_derivation | D414 | converged |
| D415 | composed_or_bootstrapped_derivation | D415 | converged |
| D416 | composed_or_bootstrapped_derivation | D416 | converged |
| D417 | composed_or_bootstrapped_derivation | D417 | converged |
| D418 | composed_or_bootstrapped_derivation | D418 | converged |
| D419 | composed_or_bootstrapped_derivation | D309, D419 | converged |
| D420 | composed_or_bootstrapped_derivation | D420 | converged |
| D421 | composed_or_bootstrapped_derivation | D421 | converged |
| D422 | composed_or_bootstrapped_derivation | D422 | converged |
| D423 | composed_or_bootstrapped_derivation | D423 | converged |
| D424 | composed_or_bootstrapped_derivation | D424 | converged |
| D463 | composed_or_bootstrapped_derivation | D463 | converged |
| D464 | composed_or_bootstrapped_derivation | D464 | converged |
| D465 | composed_or_bootstrapped_derivation | D464, D465 | converged |
| D466 | composed_or_bootstrapped_derivation | D464, D466 | converged |
| D467 | composed_or_bootstrapped_derivation | D307, D467 | converged |
| D468 | composed_or_bootstrapped_derivation | D467, D468 | converged |
| D469 | composed_or_bootstrapped_derivation | D468, D469 | converged |
| D470 | composed_or_bootstrapped_derivation | D469, D470 | converged |
