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
| [T10](../../docs/zh/functions/items/T10.md) | 缓存倒U型 | 1.4:structural_constant | Derived as the stationary collision-density multiplier in the cache inverted-U condition, where the first derivative of P_collision(ρ) vanishes at ρ*=1.4×N_active. |
| [T20](../../docs/zh/functions/items/T20.md) | σ_opt=√e解析解 | √e:math_builtin | √e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [T31](../../docs/zh/functions/items/T31.md) | 门控信息熵跃迁函数 | ln2:math_builtin, π:math_builtin, e:math_builtin, 0.415:structural_constant | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.；π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [T35](../../docs/zh/functions/items/T35.md) | σ_Planck精确值 | 6.9:structural_constant | Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary. |
| [T37](../../docs/zh/functions/items/T37.md) | Φ_QG极小点精确位置 | 1.26:structural_constant | Derived from the Φ cross-domain extremum equation Σᵢ sᵢ/ln²(μ/Λᵢ)=0 after substituting the physical-domain gate signs and scales. |
| [D32](../../docs/zh/functions/items/D32.md) | 认知-群体犹豫域统一映射函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D44](../../docs/zh/functions/items/D44.md) | 确定性误解函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D55](../../docs/zh/functions/items/D55.md) | ε_eff昼夜分时函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D106](../../docs/zh/functions/items/D106.md) | 知识更新半衰期 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D108](../../docs/zh/functions/items/D108.md) | 三域熵统一函数（推论级） | e:math_builtin, ln2:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D109](../../docs/zh/functions/items/D109.md) | 乘法最优生存策略函数 | 0.1:calibration_or_example_value, 0.3:calibration_or_example_value, 0.5:calibration_or_example_value, 0.7:calibration_or_example_value, 0.8:calibration_or_example_value, 0.1296:calibration_or_example_value, 0.0945:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D112](../../docs/zh/functions/items/D112.md) | 防守-进攻相变函数 | 0.25:structural_constant | Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25. |
| [D124](../../docs/zh/functions/items/D124.md) | 三域退化统一参数函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D127](../../docs/zh/functions/items/D127.md) | 认知路径积分函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D128](../../docs/zh/functions/items/D128.md) | 退相干-退化统一函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D129](../../docs/zh/functions/items/D129.md) | 退相干-退化等价函数 | 2.31:calibration_or_example_value, 2.34:calibration_or_example_value, 1.3:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D169](../../docs/zh/functions/items/D169.md) | 门槛碾压函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D184](../../docs/zh/functions/items/D184.md) | 熵增门槛碾压函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D203](../../docs/zh/functions/items/D203.md) | 配分函数-门控和函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D206](../../docs/zh/functions/items/D206.md) | 玻尔兹曼分布-门槛分布函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D218](../../docs/zh/functions/items/D218.md) | 物理存在必要条件 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D219](../../docs/zh/functions/items/D219.md) | Ω最优区间定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D221](../../docs/zh/functions/items/D221.md) | 热寂-完全统一同构定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D222](../../docs/zh/functions/items/D222.md) | 热力学第二定律的Φ表述 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D227](../../docs/zh/functions/items/D227.md) | 退相干-门控退化同构定理 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D230](../../docs/zh/functions/items/D230.md) | 双通道信息衰减定理 | π:math_builtin, e:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter.；e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D233](../../docs/zh/functions/items/D233.md) | Shannon-Fisher跷跷板定理 | π:math_builtin, e:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter.；e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D237](../../docs/zh/functions/items/D237.md) | 生命智能的σ压缩函数 | 6.9:structural_constant, 1.65:structural_constant | Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary.；Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed... |
| [D251](../../docs/zh/functions/items/D251.md) | 维度-容斥稳定性函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D260](../../docs/zh/functions/items/D260.md) | 偏差敏感度阈值函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| [D266](../../docs/zh/functions/items/D266.md) | 容斥偏差加速函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D276](../../docs/zh/functions/items/D276.md) | [D158](../../docs/zh/functions/items/D158.md)预测失效阈值函数 | e:math_builtin, 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| [D282](../../docs/zh/functions/items/D282.md) | Φ二阶近似函数 | 0.8:calibration_or_example_value, 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D284](../../docs/zh/functions/items/D284.md) | σ_opt跨域常数函数 | 1.65:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487. |
| [D289](../../docs/zh/functions/items/D289.md) | 良性循环逃逸速度函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D291](../../docs/zh/functions/items/D291.md) | [D158](../../docs/zh/functions/items/D158.md)案例可靠性分类函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D296](../../docs/zh/functions/items/D296.md) | Φ近似阶数选择函数 | 0.5:calibration_or_example_value, 0.8:calibration_or_example_value, 0.95:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constan... |
| [D298](../../docs/zh/functions/items/D298.md) | 鲁棒系统设计原则函数 | 1.65:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487. |
| [D302](../../docs/zh/functions/items/D302.md) | 容斥渐近发散函数 | e:math_builtin, 0.5:calibration_or_example_value, 0.95:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| [D304](../../docs/zh/functions/items/D304.md) | 弱混合角-容斥约束函数 | 0.23:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| [D307](../../docs/zh/functions/items/D307.md) | σ_opt微观起源函数 | 1.65:structural_constant, √e:math_builtin, 1.649:structural_constant | Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.；√e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D311](../../docs/zh/functions/items/D311.md) | 僵尸态函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D314](../../docs/zh/functions/items/D314.md) | ΔΦ-P传导非线性阈值函数 | e:math_builtin, 0.1:calibration_or_example_value, 0.3:calibration_or_example_value, 0.5:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| [D316](../../docs/zh/functions/items/D316.md) | 容斥时间权重演化函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| [D325](../../docs/zh/functions/items/D325.md) | 僵尸态自修复函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D327](../../docs/zh/functions/items/D327.md) | 共存震荡函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D328](../../docs/zh/functions/items/D328.md) | ΔΦ空间异质性叠加函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D348](../../docs/zh/functions/items/D348.md) | 容斥加速-时间权重联合函数 | 0.5:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| [D354](../../docs/zh/functions/items/D354.md) | 正反馈延迟函数 | π:math_builtin | π is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D356](../../docs/zh/functions/items/D356.md) | ΔΦ时空关联函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D378](../../docs/zh/functions/items/D378.md) | 实际不可逆占比函数 | e:math_builtin, 0.3:calibration_or_example_value, 0.95:calibration_or_example_value | e is a mathematical primitive used by the expression; it is not an empirical free parameter.；This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and chec... |
| [D387](../../docs/zh/functions/items/D387.md) | 容斥-耦合配分函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D392](../../docs/zh/functions/items/D392.md) | 不可逆-缓冲消失同步函数 | 0.95:calibration_or_example_value | This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant. |
| [D401](../../docs/zh/functions/items/D401.md) | 自由能-Φ等价函数 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D412](../../docs/zh/functions/items/D412.md) | 双切换同步函数 | 0.25:structural_constant | Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25. |
| [D463](../../docs/zh/functions/items/D463.md) | 完美风暴-信息量等价函数 | ln2:math_builtin | ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D467](../../docs/zh/functions/items/D467.md) | 最优性-惯性反比函数 | √e:math_builtin | √e is a mathematical primitive used by the expression; it is not an empirical free parameter. |
| [D469](../../docs/zh/functions/items/D469.md) | 振荡优化函数 | e:math_builtin | e is a mathematical primitive used by the expression; it is not an empirical free parameter. |

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
| [T1](../../docs/zh/functions/items/T1.md) | composed_or_bootstrapped_derivation | [T1](../../docs/zh/functions/items/T1.md) | converged |
| [T2](../../docs/zh/functions/items/T2.md) | composed_or_bootstrapped_derivation | [T2](../../docs/zh/functions/items/T2.md) | converged |
| [T3](../../docs/zh/functions/items/T3.md) | composed_or_bootstrapped_derivation | [T3](../../docs/zh/functions/items/T3.md) | converged |
| [T4](../../docs/zh/functions/items/T4.md) | composed_or_bootstrapped_derivation | [T4](../../docs/zh/functions/items/T4.md) | converged |
| [T5](../../docs/zh/functions/items/T5.md) | composed_or_bootstrapped_derivation | [T5](../../docs/zh/functions/items/T5.md) | converged |
| [T6](../../docs/zh/functions/items/T6.md) | composed_or_bootstrapped_derivation | [T6](../../docs/zh/functions/items/T6.md) | converged |
| [T7](../../docs/zh/functions/items/T7.md) | composed_or_bootstrapped_derivation | [T7](../../docs/zh/functions/items/T7.md) | converged |
| [T8](../../docs/zh/functions/items/T8.md) | composed_or_bootstrapped_derivation | [T8](../../docs/zh/functions/items/T8.md) | converged |
| [T9](../../docs/zh/functions/items/T9.md) | composed_or_bootstrapped_derivation | [T9](../../docs/zh/functions/items/T9.md) | converged |
| [T10](../../docs/zh/functions/items/T10.md) | composed_or_bootstrapped_derivation | [T10](../../docs/zh/functions/items/T10.md) | converged |
| [T11](../../docs/zh/functions/items/T11.md) | composed_or_bootstrapped_derivation | [T11](../../docs/zh/functions/items/T11.md) | converged |
| [T12](../../docs/zh/functions/items/T12.md) | composed_or_bootstrapped_derivation | [T12](../../docs/zh/functions/items/T12.md) | converged |
| [T13](../../docs/zh/functions/items/T13.md) | composed_or_bootstrapped_derivation | [T13](../../docs/zh/functions/items/T13.md) | converged |
| [T14](../../docs/zh/functions/items/T14.md) | composed_or_bootstrapped_derivation | [T14](../../docs/zh/functions/items/T14.md) | converged |
| [T15](../../docs/zh/functions/items/T15.md) | composed_or_bootstrapped_derivation | [T15](../../docs/zh/functions/items/T15.md) | converged |
| [T16](../../docs/zh/functions/items/T16.md) | composed_or_bootstrapped_derivation | [T16](../../docs/zh/functions/items/T16.md) | converged |
| [T17](../../docs/zh/functions/items/T17.md) | composed_or_bootstrapped_derivation | [T17](../../docs/zh/functions/items/T17.md) | converged |
| [T18](../../docs/zh/functions/items/T18.md) | composed_or_bootstrapped_derivation | [T18](../../docs/zh/functions/items/T18.md) | converged |
| [T19](../../docs/zh/functions/items/T19.md) | composed_or_bootstrapped_derivation | [T19](../../docs/zh/functions/items/T19.md) | converged |
| [T20](../../docs/zh/functions/items/T20.md) | composed_or_bootstrapped_derivation | [T20](../../docs/zh/functions/items/T20.md) | converged |
| [T21](../../docs/zh/functions/items/T21.md) | composed_or_bootstrapped_derivation | [T21](../../docs/zh/functions/items/T21.md) | converged |
| [T22](../../docs/zh/functions/items/T22.md) | composed_or_bootstrapped_derivation | [T22](../../docs/zh/functions/items/T22.md) | converged |
| [T23](../../docs/zh/functions/items/T23.md) | composed_or_bootstrapped_derivation | [T23](../../docs/zh/functions/items/T23.md) | converged |
| [T24](../../docs/zh/functions/items/T24.md) | composed_or_bootstrapped_derivation | [T24](../../docs/zh/functions/items/T24.md) | converged |
| [T25](../../docs/zh/functions/items/T25.md) | composed_or_bootstrapped_derivation | [T25](../../docs/zh/functions/items/T25.md) | converged |
| [T26](../../docs/zh/functions/items/T26.md) | composed_or_bootstrapped_derivation | [T26](../../docs/zh/functions/items/T26.md) | converged |
| [T27](../../docs/zh/functions/items/T27.md) | composed_or_bootstrapped_derivation | [T27](../../docs/zh/functions/items/T27.md) | converged |
| [T28](../../docs/zh/functions/items/T28.md) | composed_or_bootstrapped_derivation | [T28](../../docs/zh/functions/items/T28.md) | converged |
| [T29](../../docs/zh/functions/items/T29.md) | composed_or_bootstrapped_derivation | [T29](../../docs/zh/functions/items/T29.md) | converged |
| [T30](../../docs/zh/functions/items/T30.md) | composed_or_bootstrapped_derivation | [T30](../../docs/zh/functions/items/T30.md) | converged |
| [T31](../../docs/zh/functions/items/T31.md) | composed_or_bootstrapped_derivation | [T31](../../docs/zh/functions/items/T31.md) | converged |
| [T32](../../docs/zh/functions/items/T32.md) | composed_or_bootstrapped_derivation | [T32](../../docs/zh/functions/items/T32.md) | converged |
| [T33](../../docs/zh/functions/items/T33.md) | composed_or_bootstrapped_derivation | [T33](../../docs/zh/functions/items/T33.md) | converged |
| [T34](../../docs/zh/functions/items/T34.md) | composed_or_bootstrapped_derivation | [T34](../../docs/zh/functions/items/T34.md) | converged |
| [T35](../../docs/zh/functions/items/T35.md) | composed_or_bootstrapped_derivation | [T35](../../docs/zh/functions/items/T35.md) | converged |
| [T36](../../docs/zh/functions/items/T36.md) | composed_or_bootstrapped_derivation | [T36](../../docs/zh/functions/items/T36.md) | converged |
| [T37](../../docs/zh/functions/items/T37.md) | composed_or_bootstrapped_derivation | [T37](../../docs/zh/functions/items/T37.md) | converged |
| [T38](../../docs/zh/functions/items/T38.md) | composed_or_bootstrapped_derivation | [T38](../../docs/zh/functions/items/T38.md) | converged |
| [T39](../../docs/zh/functions/items/T39.md) | composed_or_bootstrapped_derivation | [T39](../../docs/zh/functions/items/T39.md) | converged |
| [D1](../../docs/zh/functions/items/D1.md) | composed_or_bootstrapped_derivation | [D1](../../docs/zh/functions/items/D1.md) | converged |
| [D2](../../docs/zh/functions/items/D2.md) | composed_or_bootstrapped_derivation | [D2](../../docs/zh/functions/items/D2.md) | converged |
| [D3](../../docs/zh/functions/items/D3.md) | composed_or_bootstrapped_derivation | [D3](../../docs/zh/functions/items/D3.md) | converged |
| [D4](../../docs/zh/functions/items/D4.md) | composed_or_bootstrapped_derivation | [D4](../../docs/zh/functions/items/D4.md) | converged |
| [D5](../../docs/zh/functions/items/D5.md) | composed_or_bootstrapped_derivation | [D5](../../docs/zh/functions/items/D5.md) | converged |
| [D6](../../docs/zh/functions/items/D6.md) | composed_or_bootstrapped_derivation | [D6](../../docs/zh/functions/items/D6.md) | converged |
| [D7](../../docs/zh/functions/items/D7.md) | composed_or_bootstrapped_derivation | [D7](../../docs/zh/functions/items/D7.md) | converged |
| [D8](../../docs/zh/functions/items/D8.md) | composed_or_bootstrapped_derivation | [D8](../../docs/zh/functions/items/D8.md) | converged |
| [D9](../../docs/zh/functions/items/D9.md) | composed_or_bootstrapped_derivation | [D9](../../docs/zh/functions/items/D9.md) | converged |
| [D10](../../docs/zh/functions/items/D10.md) | composed_or_bootstrapped_derivation | [D10](../../docs/zh/functions/items/D10.md) | converged |
| [D11](../../docs/zh/functions/items/D11.md) | composed_or_bootstrapped_derivation | [D11](../../docs/zh/functions/items/D11.md) | converged |
| [D12](../../docs/zh/functions/items/D12.md) | composed_or_bootstrapped_derivation | [D12](../../docs/zh/functions/items/D12.md) | converged |
| [D13](../../docs/zh/functions/items/D13.md) | composed_or_bootstrapped_derivation | [D13](../../docs/zh/functions/items/D13.md) | converged |
| [D14](../../docs/zh/functions/items/D14.md) | composed_or_bootstrapped_derivation | [D14](../../docs/zh/functions/items/D14.md) | converged |
| [D15](../../docs/zh/functions/items/D15.md) | composed_or_bootstrapped_derivation | [D15](../../docs/zh/functions/items/D15.md) | converged |
| [D16](../../docs/zh/functions/items/D16.md) | composed_or_bootstrapped_derivation | [D16](../../docs/zh/functions/items/D16.md) | converged |
| [D17](../../docs/zh/functions/items/D17.md) | composed_or_bootstrapped_derivation | [D17](../../docs/zh/functions/items/D17.md) | converged |
| [D18](../../docs/zh/functions/items/D18.md) | composed_or_bootstrapped_derivation | [D18](../../docs/zh/functions/items/D18.md) | converged |
| [D19](../../docs/zh/functions/items/D19.md) | composed_or_bootstrapped_derivation | [D19](../../docs/zh/functions/items/D19.md) | converged |
| [D20](../../docs/zh/functions/items/D20.md) | composed_or_bootstrapped_derivation | [D20](../../docs/zh/functions/items/D20.md) | converged |
| [D21](../../docs/zh/functions/items/D21.md) | composed_or_bootstrapped_derivation | [D21](../../docs/zh/functions/items/D21.md) | converged |
| [D22](../../docs/zh/functions/items/D22.md) | composed_or_bootstrapped_derivation | [D22](../../docs/zh/functions/items/D22.md) | converged |
| [D23](../../docs/zh/functions/items/D23.md) | composed_or_bootstrapped_derivation | [D23](../../docs/zh/functions/items/D23.md) | converged |
| [D24](../../docs/zh/functions/items/D24.md) | composed_or_bootstrapped_derivation | [D24](../../docs/zh/functions/items/D24.md) | converged |
| [D25](../../docs/zh/functions/items/D25.md) | composed_or_bootstrapped_derivation | [D25](../../docs/zh/functions/items/D25.md) | converged |
| [D26](../../docs/zh/functions/items/D26.md) | composed_or_bootstrapped_derivation | [D26](../../docs/zh/functions/items/D26.md) | converged |
| [D27](../../docs/zh/functions/items/D27.md) | composed_or_bootstrapped_derivation | [D27](../../docs/zh/functions/items/D27.md) | converged |
| [D28](../../docs/zh/functions/items/D28.md) | composed_or_bootstrapped_derivation | [D28](../../docs/zh/functions/items/D28.md) | converged |
| [D29](../../docs/zh/functions/items/D29.md) | composed_or_bootstrapped_derivation | [D29](../../docs/zh/functions/items/D29.md) | converged |
| [D30](../../docs/zh/functions/items/D30.md) | composed_or_bootstrapped_derivation | [D30](../../docs/zh/functions/items/D30.md) | converged |
| [D31](../../docs/zh/functions/items/D31.md) | composed_or_bootstrapped_derivation | [D31](../../docs/zh/functions/items/D31.md) | converged |
| [D32](../../docs/zh/functions/items/D32.md) | composed_or_bootstrapped_derivation | [D32](../../docs/zh/functions/items/D32.md) | converged |
| [D33](../../docs/zh/functions/items/D33.md) | composed_or_bootstrapped_derivation | [D33](../../docs/zh/functions/items/D33.md) | converged |
| [D34](../../docs/zh/functions/items/D34.md) | composed_or_bootstrapped_derivation | [D34](../../docs/zh/functions/items/D34.md) | converged |
| [D35](../../docs/zh/functions/items/D35.md) | composed_or_bootstrapped_derivation | [D35](../../docs/zh/functions/items/D35.md) | converged |
| [D36](../../docs/zh/functions/items/D36.md) | composed_or_bootstrapped_derivation | [D36](../../docs/zh/functions/items/D36.md) | converged |
| [D37](../../docs/zh/functions/items/D37.md) | composed_or_bootstrapped_derivation | [D37](../../docs/zh/functions/items/D37.md) | converged |
| [D38](../../docs/zh/functions/items/D38.md) | composed_or_bootstrapped_derivation | [D38](../../docs/zh/functions/items/D38.md) | converged |
| [D39](../../docs/zh/functions/items/D39.md) | composed_or_bootstrapped_derivation | [D39](../../docs/zh/functions/items/D39.md) | converged |
| [D40](../../docs/zh/functions/items/D40.md) | composed_or_bootstrapped_derivation | [D40](../../docs/zh/functions/items/D40.md) | converged |
| [D41](../../docs/zh/functions/items/D41.md) | composed_or_bootstrapped_derivation | [D41](../../docs/zh/functions/items/D41.md) | converged |
| [D42](../../docs/zh/functions/items/D42.md) | composed_or_bootstrapped_derivation | [D42](../../docs/zh/functions/items/D42.md) | converged |
| [D43](../../docs/zh/functions/items/D43.md) | composed_or_bootstrapped_derivation | [D43](../../docs/zh/functions/items/D43.md) | converged |
| [D44](../../docs/zh/functions/items/D44.md) | composed_or_bootstrapped_derivation | [D44](../../docs/zh/functions/items/D44.md) | converged |
| [D45](../../docs/zh/functions/items/D45.md) | composed_or_bootstrapped_derivation | [D45](../../docs/zh/functions/items/D45.md) | converged |
| [D46](../../docs/zh/functions/items/D46.md) | composed_or_bootstrapped_derivation | [D46](../../docs/zh/functions/items/D46.md) | converged |
| [D47](../../docs/zh/functions/items/D47.md) | composed_or_bootstrapped_derivation | [D47](../../docs/zh/functions/items/D47.md) | converged |
| [D48](../../docs/zh/functions/items/D48.md) | composed_or_bootstrapped_derivation | [D48](../../docs/zh/functions/items/D48.md) | converged |
| [D49](../../docs/zh/functions/items/D49.md) | composed_or_bootstrapped_derivation | [D49](../../docs/zh/functions/items/D49.md) | converged |
| [D50](../../docs/zh/functions/items/D50.md) | composed_or_bootstrapped_derivation | [D50](../../docs/zh/functions/items/D50.md) | converged |
| [D51](../../docs/zh/functions/items/D51.md) | composed_or_bootstrapped_derivation | [D51](../../docs/zh/functions/items/D51.md) | converged |
| [D52](../../docs/zh/functions/items/D52.md) | composed_or_bootstrapped_derivation | [D52](../../docs/zh/functions/items/D52.md) | converged |
| [D53](../../docs/zh/functions/items/D53.md) | composed_or_bootstrapped_derivation | [D53](../../docs/zh/functions/items/D53.md) | converged |
| [D54](../../docs/zh/functions/items/D54.md) | composed_or_bootstrapped_derivation | [D54](../../docs/zh/functions/items/D54.md) | converged |
| [D55](../../docs/zh/functions/items/D55.md) | composed_or_bootstrapped_derivation | [D55](../../docs/zh/functions/items/D55.md) | converged |
| [D56](../../docs/zh/functions/items/D56.md) | composed_or_bootstrapped_derivation | [D56](../../docs/zh/functions/items/D56.md) | converged |
| [D57](../../docs/zh/functions/items/D57.md) | composed_or_bootstrapped_derivation | [D57](../../docs/zh/functions/items/D57.md) | converged |
| [D58](../../docs/zh/functions/items/D58.md) | composed_or_bootstrapped_derivation | [D58](../../docs/zh/functions/items/D58.md) | converged |
| [D59](../../docs/zh/functions/items/D59.md) | composed_or_bootstrapped_derivation | [D59](../../docs/zh/functions/items/D59.md) | converged |
| [D60](../../docs/zh/functions/items/D60.md) | composed_or_bootstrapped_derivation | [D60](../../docs/zh/functions/items/D60.md) | converged |
| [D61](../../docs/zh/functions/items/D61.md) | composed_or_bootstrapped_derivation | [D61](../../docs/zh/functions/items/D61.md) | converged |
| [D62](../../docs/zh/functions/items/D62.md) | composed_or_bootstrapped_derivation | [D62](../../docs/zh/functions/items/D62.md) | converged |
| [D63](../../docs/zh/functions/items/D63.md) | composed_or_bootstrapped_derivation | [D63](../../docs/zh/functions/items/D63.md) | converged |
| [D64](../../docs/zh/functions/items/D64.md) | composed_or_bootstrapped_derivation | [D64](../../docs/zh/functions/items/D64.md) | converged |
| [D65](../../docs/zh/functions/items/D65.md) | composed_or_bootstrapped_derivation | [D65](../../docs/zh/functions/items/D65.md) | converged |
| [D66](../../docs/zh/functions/items/D66.md) | composed_or_bootstrapped_derivation | [D66](../../docs/zh/functions/items/D66.md) | converged |
| [D67](../../docs/zh/functions/items/D67.md) | composed_or_bootstrapped_derivation | [D67](../../docs/zh/functions/items/D67.md) | converged |
| [D72](../../docs/zh/functions/items/D72.md) | composed_or_bootstrapped_derivation | [D72](../../docs/zh/functions/items/D72.md) | converged |
| [D73](../../docs/zh/functions/items/D73.md) | composed_or_bootstrapped_derivation | [D73](../../docs/zh/functions/items/D73.md) | converged |
| [D74](../../docs/zh/functions/items/D74.md) | composed_or_bootstrapped_derivation | [D74](../../docs/zh/functions/items/D74.md) | converged |
| [D75](../../docs/zh/functions/items/D75.md) | composed_or_bootstrapped_derivation | [D75](../../docs/zh/functions/items/D75.md) | converged |
| [D76](../../docs/zh/functions/items/D76.md) | composed_or_bootstrapped_derivation | [D76](../../docs/zh/functions/items/D76.md) | converged |
| [D77](../../docs/zh/functions/items/D77.md) | composed_or_bootstrapped_derivation | [D77](../../docs/zh/functions/items/D77.md) | converged |
| [D84](../../docs/zh/functions/items/D84.md) | composed_or_bootstrapped_derivation | [D84](../../docs/zh/functions/items/D84.md) | converged |
| [D85](../../docs/zh/functions/items/D85.md) | composed_or_bootstrapped_derivation | [D85](../../docs/zh/functions/items/D85.md) | converged |
| [D86](../../docs/zh/functions/items/D86.md) | composed_or_bootstrapped_derivation | [D86](../../docs/zh/functions/items/D86.md) | converged |
| [D87](../../docs/zh/functions/items/D87.md) | composed_or_bootstrapped_derivation | [D87](../../docs/zh/functions/items/D87.md) | converged |
| [D88](../../docs/zh/functions/items/D88.md) | composed_or_bootstrapped_derivation | [D88](../../docs/zh/functions/items/D88.md) | converged |
| [D89](../../docs/zh/functions/items/D89.md) | composed_or_bootstrapped_derivation | [D89](../../docs/zh/functions/items/D89.md) | converged |
| [D90](../../docs/zh/functions/items/D90.md) | composed_or_bootstrapped_derivation | [D90](../../docs/zh/functions/items/D90.md) | converged |
| [D91](../../docs/zh/functions/items/D91.md) | composed_or_bootstrapped_derivation | [D91](../../docs/zh/functions/items/D91.md) | converged |
| [D92](../../docs/zh/functions/items/D92.md) | composed_or_bootstrapped_derivation | [D92](../../docs/zh/functions/items/D92.md) | converged |
| [D93](../../docs/zh/functions/items/D93.md) | composed_or_bootstrapped_derivation | [D93](../../docs/zh/functions/items/D93.md) | converged |
| [D94](../../docs/zh/functions/items/D94.md) | composed_or_bootstrapped_derivation | [D94](../../docs/zh/functions/items/D94.md) | converged |
| [D95](../../docs/zh/functions/items/D95.md) | composed_or_bootstrapped_derivation | [D95](../../docs/zh/functions/items/D95.md) | converged |
| [D96](../../docs/zh/functions/items/D96.md) | composed_or_bootstrapped_derivation | [D96](../../docs/zh/functions/items/D96.md) | converged |
| [D97](../../docs/zh/functions/items/D97.md) | composed_or_bootstrapped_derivation | [D97](../../docs/zh/functions/items/D97.md) | converged |
| [D98](../../docs/zh/functions/items/D98.md) | composed_or_bootstrapped_derivation | [D98](../../docs/zh/functions/items/D98.md) | converged |
| [D99](../../docs/zh/functions/items/D99.md) | composed_or_bootstrapped_derivation | [D99](../../docs/zh/functions/items/D99.md) | converged |
| [D100](../../docs/zh/functions/items/D100.md) | composed_or_bootstrapped_derivation | [D100](../../docs/zh/functions/items/D100.md) | converged |
| [D101](../../docs/zh/functions/items/D101.md) | composed_or_bootstrapped_derivation | [D101](../../docs/zh/functions/items/D101.md) | converged |
| [D102](../../docs/zh/functions/items/D102.md) | composed_or_bootstrapped_derivation | [D102](../../docs/zh/functions/items/D102.md) | converged |
| [D103](../../docs/zh/functions/items/D103.md) | composed_or_bootstrapped_derivation | [D103](../../docs/zh/functions/items/D103.md) | converged |
| [D104](../../docs/zh/functions/items/D104.md) | composed_or_bootstrapped_derivation | [D104](../../docs/zh/functions/items/D104.md) | converged |
| [D105](../../docs/zh/functions/items/D105.md) | composed_or_bootstrapped_derivation | [D105](../../docs/zh/functions/items/D105.md) | converged |
| [D106](../../docs/zh/functions/items/D106.md) | composed_or_bootstrapped_derivation | [D106](../../docs/zh/functions/items/D106.md) | converged |
| [D107](../../docs/zh/functions/items/D107.md) | composed_or_bootstrapped_derivation | [D107](../../docs/zh/functions/items/D107.md) | converged |
| [D108](../../docs/zh/functions/items/D108.md) | composed_or_bootstrapped_derivation | [D108](../../docs/zh/functions/items/D108.md) | converged |
| [D109](../../docs/zh/functions/items/D109.md) | composed_or_bootstrapped_derivation | [D109](../../docs/zh/functions/items/D109.md) | converged |
| [D110](../../docs/zh/functions/items/D110.md) | composed_or_bootstrapped_derivation | [D110](../../docs/zh/functions/items/D110.md) | converged |
| [D111](../../docs/zh/functions/items/D111.md) | composed_or_bootstrapped_derivation | [D111](../../docs/zh/functions/items/D111.md) | converged |
| [D112](../../docs/zh/functions/items/D112.md) | composed_or_bootstrapped_derivation | [D112](../../docs/zh/functions/items/D112.md) | converged |
| [D113](../../docs/zh/functions/items/D113.md) | composed_or_bootstrapped_derivation | [D113](../../docs/zh/functions/items/D113.md) | converged |
| [D114](../../docs/zh/functions/items/D114.md) | composed_or_bootstrapped_derivation | [D114](../../docs/zh/functions/items/D114.md) | converged |
| [D115](../../docs/zh/functions/items/D115.md) | composed_or_bootstrapped_derivation | [D115](../../docs/zh/functions/items/D115.md) | converged |
| [D116](../../docs/zh/functions/items/D116.md) | composed_or_bootstrapped_derivation | [D116](../../docs/zh/functions/items/D116.md) | converged |
| [D117](../../docs/zh/functions/items/D117.md) | composed_or_bootstrapped_derivation | [D117](../../docs/zh/functions/items/D117.md) | converged |
| [D118](../../docs/zh/functions/items/D118.md) | composed_or_bootstrapped_derivation | [D118](../../docs/zh/functions/items/D118.md) | converged |
| [D119](../../docs/zh/functions/items/D119.md) | composed_or_bootstrapped_derivation | [D119](../../docs/zh/functions/items/D119.md) | converged |
| [D120](../../docs/zh/functions/items/D120.md) | composed_or_bootstrapped_derivation | [D120](../../docs/zh/functions/items/D120.md) | converged |
| [D121](../../docs/zh/functions/items/D121.md) | composed_or_bootstrapped_derivation | [D121](../../docs/zh/functions/items/D121.md) | converged |
| [D122](../../docs/zh/functions/items/D122.md) | composed_or_bootstrapped_derivation | [D122](../../docs/zh/functions/items/D122.md) | converged |
| [D123](../../docs/zh/functions/items/D123.md) | composed_or_bootstrapped_derivation | [D123](../../docs/zh/functions/items/D123.md) | converged |
| [D124](../../docs/zh/functions/items/D124.md) | composed_or_bootstrapped_derivation | [D124](../../docs/zh/functions/items/D124.md) | converged |
| [D125](../../docs/zh/functions/items/D125.md) | composed_or_bootstrapped_derivation | [D125](../../docs/zh/functions/items/D125.md) | converged |
| [D126](../../docs/zh/functions/items/D126.md) | composed_or_bootstrapped_derivation | [D126](../../docs/zh/functions/items/D126.md) | converged |
| [D127](../../docs/zh/functions/items/D127.md) | composed_or_bootstrapped_derivation | [D127](../../docs/zh/functions/items/D127.md) | converged |
| [D128](../../docs/zh/functions/items/D128.md) | composed_or_bootstrapped_derivation | [D128](../../docs/zh/functions/items/D128.md) | converged |
| [D129](../../docs/zh/functions/items/D129.md) | composed_or_bootstrapped_derivation | [D129](../../docs/zh/functions/items/D129.md) | converged |
| [D130](../../docs/zh/functions/items/D130.md) | composed_or_bootstrapped_derivation | [D130](../../docs/zh/functions/items/D130.md) | converged |
| [D131](../../docs/zh/functions/items/D131.md) | composed_or_bootstrapped_derivation | [D131](../../docs/zh/functions/items/D131.md) | converged |
| [D132](../../docs/zh/functions/items/D132.md) | composed_or_bootstrapped_derivation | [D132](../../docs/zh/functions/items/D132.md) | converged |
| [D133](../../docs/zh/functions/items/D133.md) | composed_or_bootstrapped_derivation | [D133](../../docs/zh/functions/items/D133.md) | converged |
| [D134](../../docs/zh/functions/items/D134.md) | composed_or_bootstrapped_derivation | [D134](../../docs/zh/functions/items/D134.md) | converged |
| [D135](../../docs/zh/functions/items/D135.md) | composed_or_bootstrapped_derivation | [D135](../../docs/zh/functions/items/D135.md) | converged |
| [D136](../../docs/zh/functions/items/D136.md) | composed_or_bootstrapped_derivation | [D136](../../docs/zh/functions/items/D136.md) | converged |
| [D137](../../docs/zh/functions/items/D137.md) | composed_or_bootstrapped_derivation | [D137](../../docs/zh/functions/items/D137.md) | converged |
| [D138](../../docs/zh/functions/items/D138.md) | composed_or_bootstrapped_derivation | [D138](../../docs/zh/functions/items/D138.md) | converged |
| [D139](../../docs/zh/functions/items/D139.md) | composed_or_bootstrapped_derivation | [D139](../../docs/zh/functions/items/D139.md) | converged |
| [D140](../../docs/zh/functions/items/D140.md) | composed_or_bootstrapped_derivation | [D140](../../docs/zh/functions/items/D140.md) | converged |
| [D141](../../docs/zh/functions/items/D141.md) | composed_or_bootstrapped_derivation | [D141](../../docs/zh/functions/items/D141.md) | converged |
| [D142](../../docs/zh/functions/items/D142.md) | composed_or_bootstrapped_derivation | [D142](../../docs/zh/functions/items/D142.md) | converged |
| [D143](../../docs/zh/functions/items/D143.md) | composed_or_bootstrapped_derivation | [D143](../../docs/zh/functions/items/D143.md) | converged |
| [D144](../../docs/zh/functions/items/D144.md) | composed_or_bootstrapped_derivation | [D144](../../docs/zh/functions/items/D144.md) | converged |
| [D145](../../docs/zh/functions/items/D145.md) | composed_or_bootstrapped_derivation | [D145](../../docs/zh/functions/items/D145.md) | converged |
| [D146](../../docs/zh/functions/items/D146.md) | composed_or_bootstrapped_derivation | [D146](../../docs/zh/functions/items/D146.md) | converged |
| [D147](../../docs/zh/functions/items/D147.md) | composed_or_bootstrapped_derivation | [D147](../../docs/zh/functions/items/D147.md) | converged |
| [D148](../../docs/zh/functions/items/D148.md) | composed_or_bootstrapped_derivation | [D148](../../docs/zh/functions/items/D148.md) | converged |
| [D149](../../docs/zh/functions/items/D149.md) | composed_or_bootstrapped_derivation | [D149](../../docs/zh/functions/items/D149.md) | converged |
| [D150](../../docs/zh/functions/items/D150.md) | composed_or_bootstrapped_derivation | [D150](../../docs/zh/functions/items/D150.md) | converged |
| [D151](../../docs/zh/functions/items/D151.md) | composed_or_bootstrapped_derivation | [D151](../../docs/zh/functions/items/D151.md) | converged |
| [D152](../../docs/zh/functions/items/D152.md) | composed_or_bootstrapped_derivation | [D152](../../docs/zh/functions/items/D152.md) | converged |
| [D153](../../docs/zh/functions/items/D153.md) | composed_or_bootstrapped_derivation | [D153](../../docs/zh/functions/items/D153.md) | converged |
| [D154](../../docs/zh/functions/items/D154.md) | composed_or_bootstrapped_derivation | [D154](../../docs/zh/functions/items/D154.md) | converged |
| [D155](../../docs/zh/functions/items/D155.md) | composed_or_bootstrapped_derivation | [D155](../../docs/zh/functions/items/D155.md) | converged |
| [D156](../../docs/zh/functions/items/D156.md) | composed_or_bootstrapped_derivation | [D156](../../docs/zh/functions/items/D156.md) | converged |
| [D157](../../docs/zh/functions/items/D157.md) | composed_or_bootstrapped_derivation | [D157](../../docs/zh/functions/items/D157.md) | converged |
| [D158](../../docs/zh/functions/items/D158.md) | composed_or_bootstrapped_derivation | [D158](../../docs/zh/functions/items/D158.md) | converged |
| [D159](../../docs/zh/functions/items/D159.md) | composed_or_bootstrapped_derivation | [D159](../../docs/zh/functions/items/D159.md) | converged |
| [D160](../../docs/zh/functions/items/D160.md) | composed_or_bootstrapped_derivation | [D160](../../docs/zh/functions/items/D160.md) | converged |
| [D161](../../docs/zh/functions/items/D161.md) | composed_or_bootstrapped_derivation | [D161](../../docs/zh/functions/items/D161.md) | converged |
| [D162](../../docs/zh/functions/items/D162.md) | composed_or_bootstrapped_derivation | [D162](../../docs/zh/functions/items/D162.md) | converged |
| [D163](../../docs/zh/functions/items/D163.md) | composed_or_bootstrapped_derivation | [D163](../../docs/zh/functions/items/D163.md) | converged |
| [D164](../../docs/zh/functions/items/D164.md) | composed_or_bootstrapped_derivation | [D164](../../docs/zh/functions/items/D164.md) | converged |
| [D165](../../docs/zh/functions/items/D165.md) | composed_or_bootstrapped_derivation | [D165](../../docs/zh/functions/items/D165.md) | converged |
| [D166](../../docs/zh/functions/items/D166.md) | composed_or_bootstrapped_derivation | [D166](../../docs/zh/functions/items/D166.md) | converged |
| [D167](../../docs/zh/functions/items/D167.md) | composed_or_bootstrapped_derivation | [D167](../../docs/zh/functions/items/D167.md) | converged |
| [D168](../../docs/zh/functions/items/D168.md) | composed_or_bootstrapped_derivation | [D168](../../docs/zh/functions/items/D168.md) | converged |
| [D169](../../docs/zh/functions/items/D169.md) | composed_or_bootstrapped_derivation | [D169](../../docs/zh/functions/items/D169.md) | converged |
| [D170](../../docs/zh/functions/items/D170.md) | composed_or_bootstrapped_derivation | [D170](../../docs/zh/functions/items/D170.md) | converged |
| [D171](../../docs/zh/functions/items/D171.md) | composed_or_bootstrapped_derivation | [D171](../../docs/zh/functions/items/D171.md) | converged |
| [D172](../../docs/zh/functions/items/D172.md) | composed_or_bootstrapped_derivation | [D172](../../docs/zh/functions/items/D172.md) | converged |
| [D173](../../docs/zh/functions/items/D173.md) | composed_or_bootstrapped_derivation | [D173](../../docs/zh/functions/items/D173.md) | converged |
| [D174](../../docs/zh/functions/items/D174.md) | composed_or_bootstrapped_derivation | [D174](../../docs/zh/functions/items/D174.md) | converged |
| [D175](../../docs/zh/functions/items/D175.md) | composed_or_bootstrapped_derivation | [D175](../../docs/zh/functions/items/D175.md) | converged |
| [D176](../../docs/zh/functions/items/D176.md) | composed_or_bootstrapped_derivation | [D176](../../docs/zh/functions/items/D176.md), [D53](../../docs/zh/functions/items/D53.md), [D66](../../docs/zh/functions/items/D66.md) | converged |
| [D177](../../docs/zh/functions/items/D177.md) | composed_or_bootstrapped_derivation | [D177](../../docs/zh/functions/items/D177.md) | converged |
| [D178](../../docs/zh/functions/items/D178.md) | composed_or_bootstrapped_derivation | [D178](../../docs/zh/functions/items/D178.md) | converged |
| [D179](../../docs/zh/functions/items/D179.md) | composed_or_bootstrapped_derivation | [D179](../../docs/zh/functions/items/D179.md) | converged |
| [D180](../../docs/zh/functions/items/D180.md) | composed_or_bootstrapped_derivation | [D180](../../docs/zh/functions/items/D180.md) | converged |
| [D181](../../docs/zh/functions/items/D181.md) | composed_or_bootstrapped_derivation | [D181](../../docs/zh/functions/items/D181.md) | converged |
| [D182](../../docs/zh/functions/items/D182.md) | composed_or_bootstrapped_derivation | [D182](../../docs/zh/functions/items/D182.md) | converged |
| [D183](../../docs/zh/functions/items/D183.md) | composed_or_bootstrapped_derivation | [D183](../../docs/zh/functions/items/D183.md) | converged |
| [D184](../../docs/zh/functions/items/D184.md) | composed_or_bootstrapped_derivation | [D184](../../docs/zh/functions/items/D184.md) | converged |
| [D185](../../docs/zh/functions/items/D185.md) | composed_or_bootstrapped_derivation | [D182](../../docs/zh/functions/items/D182.md), [D185](../../docs/zh/functions/items/D185.md) | converged |
| [D186](../../docs/zh/functions/items/D186.md) | composed_or_bootstrapped_derivation | [D186](../../docs/zh/functions/items/D186.md) | converged |
| [D187](../../docs/zh/functions/items/D187.md) | composed_or_bootstrapped_derivation | [D187](../../docs/zh/functions/items/D187.md) | converged |
| [D188](../../docs/zh/functions/items/D188.md) | composed_or_bootstrapped_derivation | [D188](../../docs/zh/functions/items/D188.md) | converged |
| [D189](../../docs/zh/functions/items/D189.md) | composed_or_bootstrapped_derivation | [D189](../../docs/zh/functions/items/D189.md) | converged |
| [D190](../../docs/zh/functions/items/D190.md) | composed_or_bootstrapped_derivation | [D190](../../docs/zh/functions/items/D190.md) | converged |
| [D191](../../docs/zh/functions/items/D191.md) | composed_or_bootstrapped_derivation | [D191](../../docs/zh/functions/items/D191.md) | converged |
| [D192](../../docs/zh/functions/items/D192.md) | composed_or_bootstrapped_derivation | [D192](../../docs/zh/functions/items/D192.md) | converged |
| [D193](../../docs/zh/functions/items/D193.md) | composed_or_bootstrapped_derivation | [D193](../../docs/zh/functions/items/D193.md) | converged |
| [D194](../../docs/zh/functions/items/D194.md) | composed_or_bootstrapped_derivation | [D194](../../docs/zh/functions/items/D194.md) | converged |
| [D195](../../docs/zh/functions/items/D195.md) | composed_or_bootstrapped_derivation | [D195](../../docs/zh/functions/items/D195.md) | converged |
| [D196](../../docs/zh/functions/items/D196.md) | composed_or_bootstrapped_derivation | [D196](../../docs/zh/functions/items/D196.md) | converged |
| [D197](../../docs/zh/functions/items/D197.md) | composed_or_bootstrapped_derivation | [D197](../../docs/zh/functions/items/D197.md) | converged |
| [D198](../../docs/zh/functions/items/D198.md) | composed_or_bootstrapped_derivation | [D198](../../docs/zh/functions/items/D198.md) | converged |
| [D199](../../docs/zh/functions/items/D199.md) | composed_or_bootstrapped_derivation | [D199](../../docs/zh/functions/items/D199.md) | converged |
| [D200](../../docs/zh/functions/items/D200.md) | composed_or_bootstrapped_derivation | [D200](../../docs/zh/functions/items/D200.md) | converged |
| [D201](../../docs/zh/functions/items/D201.md) | composed_or_bootstrapped_derivation | [D201](../../docs/zh/functions/items/D201.md) | converged |
| [D202](../../docs/zh/functions/items/D202.md) | composed_or_bootstrapped_derivation | [D202](../../docs/zh/functions/items/D202.md) | converged |
| [D203](../../docs/zh/functions/items/D203.md) | composed_or_bootstrapped_derivation | [D203](../../docs/zh/functions/items/D203.md) | converged |
| [D204](../../docs/zh/functions/items/D204.md) | composed_or_bootstrapped_derivation | [D204](../../docs/zh/functions/items/D204.md) | converged |
| [D205](../../docs/zh/functions/items/D205.md) | composed_or_bootstrapped_derivation | [D205](../../docs/zh/functions/items/D205.md) | converged |
| [D206](../../docs/zh/functions/items/D206.md) | composed_or_bootstrapped_derivation | [D206](../../docs/zh/functions/items/D206.md) | converged |
| [D207](../../docs/zh/functions/items/D207.md) | composed_or_bootstrapped_derivation | [D207](../../docs/zh/functions/items/D207.md) | converged |
| [D208](../../docs/zh/functions/items/D208.md) | composed_or_bootstrapped_derivation | [D208](../../docs/zh/functions/items/D208.md) | converged |
| [D209](../../docs/zh/functions/items/D209.md) | composed_or_bootstrapped_derivation | [D209](../../docs/zh/functions/items/D209.md) | converged |
| [D210](../../docs/zh/functions/items/D210.md) | composed_or_bootstrapped_derivation | [D210](../../docs/zh/functions/items/D210.md) | converged |
| [D211](../../docs/zh/functions/items/D211.md) | composed_or_bootstrapped_derivation | [D211](../../docs/zh/functions/items/D211.md) | converged |
| [D212](../../docs/zh/functions/items/D212.md) | composed_or_bootstrapped_derivation | [D212](../../docs/zh/functions/items/D212.md) | converged |
| [D213](../../docs/zh/functions/items/D213.md) | composed_or_bootstrapped_derivation | [D213](../../docs/zh/functions/items/D213.md) | converged |
| [D214](../../docs/zh/functions/items/D214.md) | composed_or_bootstrapped_derivation | [D214](../../docs/zh/functions/items/D214.md) | converged |
| [D215](../../docs/zh/functions/items/D215.md) | composed_or_bootstrapped_derivation | [D215](../../docs/zh/functions/items/D215.md) | converged |
| [D216](../../docs/zh/functions/items/D216.md) | composed_or_bootstrapped_derivation | [D216](../../docs/zh/functions/items/D216.md) | converged |
| [D217](../../docs/zh/functions/items/D217.md) | composed_or_bootstrapped_derivation | [D217](../../docs/zh/functions/items/D217.md) | converged |
| [D218](../../docs/zh/functions/items/D218.md) | composed_or_bootstrapped_derivation | [D218](../../docs/zh/functions/items/D218.md) | converged |
| [D219](../../docs/zh/functions/items/D219.md) | composed_or_bootstrapped_derivation | [D219](../../docs/zh/functions/items/D219.md) | converged |
| [D220](../../docs/zh/functions/items/D220.md) | composed_or_bootstrapped_derivation | [D220](../../docs/zh/functions/items/D220.md) | converged |
| [D221](../../docs/zh/functions/items/D221.md) | composed_or_bootstrapped_derivation | [D221](../../docs/zh/functions/items/D221.md) | converged |
| [D222](../../docs/zh/functions/items/D222.md) | composed_or_bootstrapped_derivation | [D222](../../docs/zh/functions/items/D222.md) | converged |
| [D223](../../docs/zh/functions/items/D223.md) | composed_or_bootstrapped_derivation | [D223](../../docs/zh/functions/items/D223.md) | converged |
| [D224](../../docs/zh/functions/items/D224.md) | composed_or_bootstrapped_derivation | [D224](../../docs/zh/functions/items/D224.md) | converged |
| [D225](../../docs/zh/functions/items/D225.md) | composed_or_bootstrapped_derivation | [D225](../../docs/zh/functions/items/D225.md) | converged |
| [D226](../../docs/zh/functions/items/D226.md) | composed_or_bootstrapped_derivation | [D220](../../docs/zh/functions/items/D220.md), [D222](../../docs/zh/functions/items/D222.md), [D224](../../docs/zh/functions/items/D224.md), [D226](../../docs/zh/functions/items/D226.md) | converged |
| [D227](../../docs/zh/functions/items/D227.md) | composed_or_bootstrapped_derivation | [D198](../../docs/zh/functions/items/D198.md), [D227](../../docs/zh/functions/items/D227.md) | converged |
| [D228](../../docs/zh/functions/items/D228.md) | composed_or_bootstrapped_derivation | [D228](../../docs/zh/functions/items/D228.md) | converged |
| [D229](../../docs/zh/functions/items/D229.md) | composed_or_bootstrapped_derivation | [D220](../../docs/zh/functions/items/D220.md), [D222](../../docs/zh/functions/items/D222.md), [D224](../../docs/zh/functions/items/D224.md), [D227](../../docs/zh/functions/items/D227.md), [D229](../../docs/zh/functions/items/D229.md) | converged |
| [D230](../../docs/zh/functions/items/D230.md) | composed_or_bootstrapped_derivation | [D197](../../docs/zh/functions/items/D197.md), [D230](../../docs/zh/functions/items/D230.md) | converged |
| [D231](../../docs/zh/functions/items/D231.md) | composed_or_bootstrapped_derivation | [D222](../../docs/zh/functions/items/D222.md), [D230](../../docs/zh/functions/items/D230.md), [D231](../../docs/zh/functions/items/D231.md) | converged |
| [D232](../../docs/zh/functions/items/D232.md) | composed_or_bootstrapped_derivation | [D230](../../docs/zh/functions/items/D230.md), [D232](../../docs/zh/functions/items/D232.md) | converged |
| [D233](../../docs/zh/functions/items/D233.md) | composed_or_bootstrapped_derivation | [D233](../../docs/zh/functions/items/D233.md) | converged |
| [D234](../../docs/zh/functions/items/D234.md) | composed_or_bootstrapped_derivation | [D234](../../docs/zh/functions/items/D234.md) | converged |
| [D235](../../docs/zh/functions/items/D235.md) | composed_or_bootstrapped_derivation | [D233](../../docs/zh/functions/items/D233.md), [D235](../../docs/zh/functions/items/D235.md) | converged |
| [D236](../../docs/zh/functions/items/D236.md) | composed_or_bootstrapped_derivation | [D236](../../docs/zh/functions/items/D236.md) | converged |
| [D237](../../docs/zh/functions/items/D237.md) | composed_or_bootstrapped_derivation | [D234](../../docs/zh/functions/items/D234.md), [D237](../../docs/zh/functions/items/D237.md) | converged |
| [D238](../../docs/zh/functions/items/D238.md) | composed_or_bootstrapped_derivation | [D238](../../docs/zh/functions/items/D238.md) | converged |
| [D239](../../docs/zh/functions/items/D239.md) | composed_or_bootstrapped_derivation | [D239](../../docs/zh/functions/items/D239.md) | converged |
| [D240](../../docs/zh/functions/items/D240.md) | composed_or_bootstrapped_derivation | [D240](../../docs/zh/functions/items/D240.md) | converged |
| [D241](../../docs/zh/functions/items/D241.md) | composed_or_bootstrapped_derivation | [D241](../../docs/zh/functions/items/D241.md) | converged |
| [D242](../../docs/zh/functions/items/D242.md) | composed_or_bootstrapped_derivation | [D242](../../docs/zh/functions/items/D242.md) | converged |
| [D243](../../docs/zh/functions/items/D243.md) | composed_or_bootstrapped_derivation | [D243](../../docs/zh/functions/items/D243.md) | converged |
| [D244](../../docs/zh/functions/items/D244.md) | composed_or_bootstrapped_derivation | [D239](../../docs/zh/functions/items/D239.md), [D244](../../docs/zh/functions/items/D244.md) | converged |
| [D245](../../docs/zh/functions/items/D245.md) | composed_or_bootstrapped_derivation | [D195](../../docs/zh/functions/items/D195.md), [D245](../../docs/zh/functions/items/D245.md) | converged |
| [D246](../../docs/zh/functions/items/D246.md) | composed_or_bootstrapped_derivation | [D246](../../docs/zh/functions/items/D246.md) | converged |
| [D247](../../docs/zh/functions/items/D247.md) | composed_or_bootstrapped_derivation | [D247](../../docs/zh/functions/items/D247.md) | converged |
| [D248](../../docs/zh/functions/items/D248.md) | composed_or_bootstrapped_derivation | [D248](../../docs/zh/functions/items/D248.md) | converged |
| [D249](../../docs/zh/functions/items/D249.md) | composed_or_bootstrapped_derivation | [D249](../../docs/zh/functions/items/D249.md) | converged |
| [D250](../../docs/zh/functions/items/D250.md) | composed_or_bootstrapped_derivation | [D250](../../docs/zh/functions/items/D250.md) | converged |
| [D251](../../docs/zh/functions/items/D251.md) | composed_or_bootstrapped_derivation | [D251](../../docs/zh/functions/items/D251.md) | converged |
| [D252](../../docs/zh/functions/items/D252.md) | composed_or_bootstrapped_derivation | [D147](../../docs/zh/functions/items/D147.md), [D252](../../docs/zh/functions/items/D252.md) | converged |
| [D253](../../docs/zh/functions/items/D253.md) | composed_or_bootstrapped_derivation | [D253](../../docs/zh/functions/items/D253.md) | converged |
| [D254](../../docs/zh/functions/items/D254.md) | composed_or_bootstrapped_derivation | [D254](../../docs/zh/functions/items/D254.md) | converged |
| [D255](../../docs/zh/functions/items/D255.md) | composed_or_bootstrapped_derivation | [D255](../../docs/zh/functions/items/D255.md) | converged |
| [D256](../../docs/zh/functions/items/D256.md) | composed_or_bootstrapped_derivation | [D256](../../docs/zh/functions/items/D256.md) | converged |
| [D257](../../docs/zh/functions/items/D257.md) | composed_or_bootstrapped_derivation | [D257](../../docs/zh/functions/items/D257.md) | converged |
| [D258](../../docs/zh/functions/items/D258.md) | composed_or_bootstrapped_derivation | [D258](../../docs/zh/functions/items/D258.md) | converged |
| [D259](../../docs/zh/functions/items/D259.md) | composed_or_bootstrapped_derivation | [D258](../../docs/zh/functions/items/D258.md), [D259](../../docs/zh/functions/items/D259.md) | converged |
| [D260](../../docs/zh/functions/items/D260.md) | composed_or_bootstrapped_derivation | [D260](../../docs/zh/functions/items/D260.md) | converged |
| [D261](../../docs/zh/functions/items/D261.md) | composed_or_bootstrapped_derivation | [D261](../../docs/zh/functions/items/D261.md) | converged |
| [D262](../../docs/zh/functions/items/D262.md) | composed_or_bootstrapped_derivation | [D262](../../docs/zh/functions/items/D262.md) | converged |
| [D263](../../docs/zh/functions/items/D263.md) | composed_or_bootstrapped_derivation | [D263](../../docs/zh/functions/items/D263.md) | converged |
| [D264](../../docs/zh/functions/items/D264.md) | composed_or_bootstrapped_derivation | [D264](../../docs/zh/functions/items/D264.md) | converged |
| [D265](../../docs/zh/functions/items/D265.md) | composed_or_bootstrapped_derivation | [D265](../../docs/zh/functions/items/D265.md) | converged |
| [D266](../../docs/zh/functions/items/D266.md) | composed_or_bootstrapped_derivation | [D266](../../docs/zh/functions/items/D266.md) | converged |
| [D267](../../docs/zh/functions/items/D267.md) | composed_or_bootstrapped_derivation | [D267](../../docs/zh/functions/items/D267.md) | converged |
| [D268](../../docs/zh/functions/items/D268.md) | composed_or_bootstrapped_derivation | [D268](../../docs/zh/functions/items/D268.md) | converged |
| [D269](../../docs/zh/functions/items/D269.md) | composed_or_bootstrapped_derivation | [D269](../../docs/zh/functions/items/D269.md) | converged |
| [D270](../../docs/zh/functions/items/D270.md) | composed_or_bootstrapped_derivation | [D270](../../docs/zh/functions/items/D270.md) | converged |
| [D271](../../docs/zh/functions/items/D271.md) | composed_or_bootstrapped_derivation | [D271](../../docs/zh/functions/items/D271.md) | converged |
| [D272](../../docs/zh/functions/items/D272.md) | composed_or_bootstrapped_derivation | [D272](../../docs/zh/functions/items/D272.md) | converged |
| [D273](../../docs/zh/functions/items/D273.md) | composed_or_bootstrapped_derivation | [D253](../../docs/zh/functions/items/D253.md), [D273](../../docs/zh/functions/items/D273.md) | converged |
| [D274](../../docs/zh/functions/items/D274.md) | composed_or_bootstrapped_derivation | [D274](../../docs/zh/functions/items/D274.md) | converged |
| [D275](../../docs/zh/functions/items/D275.md) | composed_or_bootstrapped_derivation | [D275](../../docs/zh/functions/items/D275.md) | converged |
| [D276](../../docs/zh/functions/items/D276.md) | composed_or_bootstrapped_derivation | [D276](../../docs/zh/functions/items/D276.md) | converged |
| [D277](../../docs/zh/functions/items/D277.md) | composed_or_bootstrapped_derivation | [D277](../../docs/zh/functions/items/D277.md) | converged |
| [D278](../../docs/zh/functions/items/D278.md) | composed_or_bootstrapped_derivation | [D278](../../docs/zh/functions/items/D278.md) | converged |
| [D279](../../docs/zh/functions/items/D279.md) | composed_or_bootstrapped_derivation | [D279](../../docs/zh/functions/items/D279.md) | converged |
| [D280](../../docs/zh/functions/items/D280.md) | composed_or_bootstrapped_derivation | [D280](../../docs/zh/functions/items/D280.md) | converged |
| [D281](../../docs/zh/functions/items/D281.md) | composed_or_bootstrapped_derivation | [D281](../../docs/zh/functions/items/D281.md) | converged |
| [D282](../../docs/zh/functions/items/D282.md) | composed_or_bootstrapped_derivation | [D282](../../docs/zh/functions/items/D282.md) | converged |
| [D283](../../docs/zh/functions/items/D283.md) | composed_or_bootstrapped_derivation | [D283](../../docs/zh/functions/items/D283.md) | converged |
| [D284](../../docs/zh/functions/items/D284.md) | composed_or_bootstrapped_derivation | [D284](../../docs/zh/functions/items/D284.md) | converged |
| [D285](../../docs/zh/functions/items/D285.md) | composed_or_bootstrapped_derivation | [D285](../../docs/zh/functions/items/D285.md) | converged |
| [D286](../../docs/zh/functions/items/D286.md) | composed_or_bootstrapped_derivation | [D286](../../docs/zh/functions/items/D286.md) | converged |
| [D287](../../docs/zh/functions/items/D287.md) | composed_or_bootstrapped_derivation | [D287](../../docs/zh/functions/items/D287.md) | converged |
| [D288](../../docs/zh/functions/items/D288.md) | composed_or_bootstrapped_derivation | [D288](../../docs/zh/functions/items/D288.md) | converged |
| [D289](../../docs/zh/functions/items/D289.md) | composed_or_bootstrapped_derivation | [D289](../../docs/zh/functions/items/D289.md) | converged |
| [D290](../../docs/zh/functions/items/D290.md) | composed_or_bootstrapped_derivation | [D290](../../docs/zh/functions/items/D290.md) | converged |
| [D291](../../docs/zh/functions/items/D291.md) | composed_or_bootstrapped_derivation | [D291](../../docs/zh/functions/items/D291.md) | converged |
| [D292](../../docs/zh/functions/items/D292.md) | composed_or_bootstrapped_derivation | [D292](../../docs/zh/functions/items/D292.md) | converged |
| [D293](../../docs/zh/functions/items/D293.md) | composed_or_bootstrapped_derivation | [D293](../../docs/zh/functions/items/D293.md) | converged |
| [D294](../../docs/zh/functions/items/D294.md) | composed_or_bootstrapped_derivation | [D294](../../docs/zh/functions/items/D294.md) | converged |
| [D295](../../docs/zh/functions/items/D295.md) | composed_or_bootstrapped_derivation | [D295](../../docs/zh/functions/items/D295.md) | converged |
| [D296](../../docs/zh/functions/items/D296.md) | composed_or_bootstrapped_derivation | [D296](../../docs/zh/functions/items/D296.md) | converged |
| [D297](../../docs/zh/functions/items/D297.md) | composed_or_bootstrapped_derivation | [D297](../../docs/zh/functions/items/D297.md) | converged |
| [D298](../../docs/zh/functions/items/D298.md) | composed_or_bootstrapped_derivation | [D298](../../docs/zh/functions/items/D298.md) | converged |
| [D299](../../docs/zh/functions/items/D299.md) | composed_or_bootstrapped_derivation | [D299](../../docs/zh/functions/items/D299.md) | converged |
| [D300](../../docs/zh/functions/items/D300.md) | composed_or_bootstrapped_derivation | [D300](../../docs/zh/functions/items/D300.md) | converged |
| [D301](../../docs/zh/functions/items/D301.md) | composed_or_bootstrapped_derivation | [D301](../../docs/zh/functions/items/D301.md) | converged |
| [D302](../../docs/zh/functions/items/D302.md) | composed_or_bootstrapped_derivation | [D302](../../docs/zh/functions/items/D302.md) | converged |
| [D303](../../docs/zh/functions/items/D303.md) | composed_or_bootstrapped_derivation | [D303](../../docs/zh/functions/items/D303.md) | converged |
| [D304](../../docs/zh/functions/items/D304.md) | composed_or_bootstrapped_derivation | [D283](../../docs/zh/functions/items/D283.md), [D304](../../docs/zh/functions/items/D304.md) | converged |
| [D305](../../docs/zh/functions/items/D305.md) | composed_or_bootstrapped_derivation | [D305](../../docs/zh/functions/items/D305.md) | converged |
| [D306](../../docs/zh/functions/items/D306.md) | composed_or_bootstrapped_derivation | [D290](../../docs/zh/functions/items/D290.md), [D306](../../docs/zh/functions/items/D306.md) | converged |
| [D307](../../docs/zh/functions/items/D307.md) | composed_or_bootstrapped_derivation | [D307](../../docs/zh/functions/items/D307.md) | converged |
| [D308](../../docs/zh/functions/items/D308.md) | composed_or_bootstrapped_derivation | [D308](../../docs/zh/functions/items/D308.md) | converged |
| [D309](../../docs/zh/functions/items/D309.md) | composed_or_bootstrapped_derivation | [D309](../../docs/zh/functions/items/D309.md) | converged |
| [D310](../../docs/zh/functions/items/D310.md) | composed_or_bootstrapped_derivation | [D310](../../docs/zh/functions/items/D310.md) | converged |
| [D311](../../docs/zh/functions/items/D311.md) | composed_or_bootstrapped_derivation | [D311](../../docs/zh/functions/items/D311.md) | converged |
| [D312](../../docs/zh/functions/items/D312.md) | composed_or_bootstrapped_derivation | [D274](../../docs/zh/functions/items/D274.md), [D312](../../docs/zh/functions/items/D312.md) | converged |
| [D313](../../docs/zh/functions/items/D313.md) | composed_or_bootstrapped_derivation | [D274](../../docs/zh/functions/items/D274.md), [D299](../../docs/zh/functions/items/D299.md), [D313](../../docs/zh/functions/items/D313.md) | converged |
| [D314](../../docs/zh/functions/items/D314.md) | composed_or_bootstrapped_derivation | [D314](../../docs/zh/functions/items/D314.md) | converged |
| [D315](../../docs/zh/functions/items/D315.md) | composed_or_bootstrapped_derivation | [D315](../../docs/zh/functions/items/D315.md) | converged |
| [D316](../../docs/zh/functions/items/D316.md) | composed_or_bootstrapped_derivation | [D316](../../docs/zh/functions/items/D316.md) | converged |
| [D317](../../docs/zh/functions/items/D317.md) | composed_or_bootstrapped_derivation | [D306](../../docs/zh/functions/items/D306.md), [D317](../../docs/zh/functions/items/D317.md) | converged |
| [D318](../../docs/zh/functions/items/D318.md) | composed_or_bootstrapped_derivation | [D318](../../docs/zh/functions/items/D318.md) | converged |
| [D319](../../docs/zh/functions/items/D319.md) | composed_or_bootstrapped_derivation | [D319](../../docs/zh/functions/items/D319.md) | converged |
| [D320](../../docs/zh/functions/items/D320.md) | composed_or_bootstrapped_derivation | [D320](../../docs/zh/functions/items/D320.md) | converged |
| [D321](../../docs/zh/functions/items/D321.md) | composed_or_bootstrapped_derivation | [D321](../../docs/zh/functions/items/D321.md) | converged |
| [D322](../../docs/zh/functions/items/D322.md) | composed_or_bootstrapped_derivation | [D322](../../docs/zh/functions/items/D322.md) | converged |
| [D323](../../docs/zh/functions/items/D323.md) | composed_or_bootstrapped_derivation | [D323](../../docs/zh/functions/items/D323.md) | converged |
| [D324](../../docs/zh/functions/items/D324.md) | composed_or_bootstrapped_derivation | [D324](../../docs/zh/functions/items/D324.md) | converged |
| [D325](../../docs/zh/functions/items/D325.md) | composed_or_bootstrapped_derivation | [D325](../../docs/zh/functions/items/D325.md) | converged |
| [D326](../../docs/zh/functions/items/D326.md) | composed_or_bootstrapped_derivation | [D326](../../docs/zh/functions/items/D326.md) | converged |
| [D327](../../docs/zh/functions/items/D327.md) | composed_or_bootstrapped_derivation | [D327](../../docs/zh/functions/items/D327.md) | converged |
| [D328](../../docs/zh/functions/items/D328.md) | composed_or_bootstrapped_derivation | [D328](../../docs/zh/functions/items/D328.md) | converged |
| [D329](../../docs/zh/functions/items/D329.md) | composed_or_bootstrapped_derivation | [D315](../../docs/zh/functions/items/D315.md), [D329](../../docs/zh/functions/items/D329.md) | converged |
| [D330](../../docs/zh/functions/items/D330.md) | composed_or_bootstrapped_derivation | [D280](../../docs/zh/functions/items/D280.md), [D330](../../docs/zh/functions/items/D330.md) | converged |
| [D331](../../docs/zh/functions/items/D331.md) | composed_or_bootstrapped_derivation | [D331](../../docs/zh/functions/items/D331.md) | converged |
| [D332](../../docs/zh/functions/items/D332.md) | composed_or_bootstrapped_derivation | [D309](../../docs/zh/functions/items/D309.md), [D332](../../docs/zh/functions/items/D332.md) | converged |
| [D333](../../docs/zh/functions/items/D333.md) | composed_or_bootstrapped_derivation | [D333](../../docs/zh/functions/items/D333.md) | converged |
| [D334](../../docs/zh/functions/items/D334.md) | composed_or_bootstrapped_derivation | [D334](../../docs/zh/functions/items/D334.md) | converged |
| [D335](../../docs/zh/functions/items/D335.md) | composed_or_bootstrapped_derivation | [D306](../../docs/zh/functions/items/D306.md), [D335](../../docs/zh/functions/items/D335.md) | converged |
| [D336](../../docs/zh/functions/items/D336.md) | composed_or_bootstrapped_derivation | [D336](../../docs/zh/functions/items/D336.md) | converged |
| [D337](../../docs/zh/functions/items/D337.md) | composed_or_bootstrapped_derivation | [D337](../../docs/zh/functions/items/D337.md) | converged |
| [D338](../../docs/zh/functions/items/D338.md) | composed_or_bootstrapped_derivation | [D338](../../docs/zh/functions/items/D338.md) | converged |
| [D339](../../docs/zh/functions/items/D339.md) | composed_or_bootstrapped_derivation | [D339](../../docs/zh/functions/items/D339.md) | converged |
| [D340](../../docs/zh/functions/items/D340.md) | composed_or_bootstrapped_derivation | [D340](../../docs/zh/functions/items/D340.md) | converged |
| [D341](../../docs/zh/functions/items/D341.md) | composed_or_bootstrapped_derivation | [D341](../../docs/zh/functions/items/D341.md) | converged |
| [D342](../../docs/zh/functions/items/D342.md) | composed_or_bootstrapped_derivation | [D266](../../docs/zh/functions/items/D266.md), [D342](../../docs/zh/functions/items/D342.md) | converged |
| [D343](../../docs/zh/functions/items/D343.md) | composed_or_bootstrapped_derivation | [D343](../../docs/zh/functions/items/D343.md) | converged |
| [D344](../../docs/zh/functions/items/D344.md) | composed_or_bootstrapped_derivation | [D344](../../docs/zh/functions/items/D344.md) | converged |
| [D345](../../docs/zh/functions/items/D345.md) | composed_or_bootstrapped_derivation | [D345](../../docs/zh/functions/items/D345.md) | converged |
| [D346](../../docs/zh/functions/items/D346.md) | composed_or_bootstrapped_derivation | [D346](../../docs/zh/functions/items/D346.md) | converged |
| [D347](../../docs/zh/functions/items/D347.md) | composed_or_bootstrapped_derivation | [D347](../../docs/zh/functions/items/D347.md) | converged |
| [D348](../../docs/zh/functions/items/D348.md) | composed_or_bootstrapped_derivation | [D348](../../docs/zh/functions/items/D348.md) | converged |
| [D349](../../docs/zh/functions/items/D349.md) | composed_or_bootstrapped_derivation | [D349](../../docs/zh/functions/items/D349.md) | converged |
| [D350](../../docs/zh/functions/items/D350.md) | composed_or_bootstrapped_derivation | [D350](../../docs/zh/functions/items/D350.md) | converged |
| [D351](../../docs/zh/functions/items/D351.md) | composed_or_bootstrapped_derivation | [D351](../../docs/zh/functions/items/D351.md) | converged |
| [D352](../../docs/zh/functions/items/D352.md) | composed_or_bootstrapped_derivation | [D324](../../docs/zh/functions/items/D324.md), [D352](../../docs/zh/functions/items/D352.md) | converged |
| [D353](../../docs/zh/functions/items/D353.md) | composed_or_bootstrapped_derivation | [D353](../../docs/zh/functions/items/D353.md) | converged |
| [D354](../../docs/zh/functions/items/D354.md) | composed_or_bootstrapped_derivation | [D354](../../docs/zh/functions/items/D354.md) | converged |
| [D355](../../docs/zh/functions/items/D355.md) | composed_or_bootstrapped_derivation | [D355](../../docs/zh/functions/items/D355.md) | converged |
| [D356](../../docs/zh/functions/items/D356.md) | composed_or_bootstrapped_derivation | [D356](../../docs/zh/functions/items/D356.md) | converged |
| [D357](../../docs/zh/functions/items/D357.md) | composed_or_bootstrapped_derivation | [D357](../../docs/zh/functions/items/D357.md) | converged |
| [D358](../../docs/zh/functions/items/D358.md) | composed_or_bootstrapped_derivation | [D358](../../docs/zh/functions/items/D358.md) | converged |
| [D359](../../docs/zh/functions/items/D359.md) | composed_or_bootstrapped_derivation | [D359](../../docs/zh/functions/items/D359.md) | converged |
| [D360](../../docs/zh/functions/items/D360.md) | composed_or_bootstrapped_derivation | [D310](../../docs/zh/functions/items/D310.md), [D360](../../docs/zh/functions/items/D360.md) | converged |
| [D361](../../docs/zh/functions/items/D361.md) | composed_or_bootstrapped_derivation | [D361](../../docs/zh/functions/items/D361.md) | converged |
| [D362](../../docs/zh/functions/items/D362.md) | composed_or_bootstrapped_derivation | [D362](../../docs/zh/functions/items/D362.md) | converged |
| [D363](../../docs/zh/functions/items/D363.md) | composed_or_bootstrapped_derivation | [D363](../../docs/zh/functions/items/D363.md) | converged |
| [D364](../../docs/zh/functions/items/D364.md) | composed_or_bootstrapped_derivation | [D364](../../docs/zh/functions/items/D364.md) | converged |
| [D365](../../docs/zh/functions/items/D365.md) | composed_or_bootstrapped_derivation | [D365](../../docs/zh/functions/items/D365.md) | converged |
| [D366](../../docs/zh/functions/items/D366.md) | composed_or_bootstrapped_derivation | [D366](../../docs/zh/functions/items/D366.md) | converged |
| [D367](../../docs/zh/functions/items/D367.md) | composed_or_bootstrapped_derivation | [D367](../../docs/zh/functions/items/D367.md) | converged |
| [D368](../../docs/zh/functions/items/D368.md) | composed_or_bootstrapped_derivation | [D368](../../docs/zh/functions/items/D368.md) | converged |
| [D369](../../docs/zh/functions/items/D369.md) | composed_or_bootstrapped_derivation | [D369](../../docs/zh/functions/items/D369.md) | converged |
| [D370](../../docs/zh/functions/items/D370.md) | composed_or_bootstrapped_derivation | [D370](../../docs/zh/functions/items/D370.md) | converged |
| [D371](../../docs/zh/functions/items/D371.md) | composed_or_bootstrapped_derivation | [D371](../../docs/zh/functions/items/D371.md) | converged |
| [D372](../../docs/zh/functions/items/D372.md) | composed_or_bootstrapped_derivation | [D372](../../docs/zh/functions/items/D372.md) | converged |
| [D373](../../docs/zh/functions/items/D373.md) | composed_or_bootstrapped_derivation | [D373](../../docs/zh/functions/items/D373.md) | converged |
| [D374](../../docs/zh/functions/items/D374.md) | composed_or_bootstrapped_derivation | [D374](../../docs/zh/functions/items/D374.md) | converged |
| [D375](../../docs/zh/functions/items/D375.md) | composed_or_bootstrapped_derivation | [D375](../../docs/zh/functions/items/D375.md) | converged |
| [D376](../../docs/zh/functions/items/D376.md) | composed_or_bootstrapped_derivation | [D376](../../docs/zh/functions/items/D376.md) | converged |
| [D377](../../docs/zh/functions/items/D377.md) | composed_or_bootstrapped_derivation | [D377](../../docs/zh/functions/items/D377.md) | converged |
| [D378](../../docs/zh/functions/items/D378.md) | composed_or_bootstrapped_derivation | [D378](../../docs/zh/functions/items/D378.md) | converged |
| [D379](../../docs/zh/functions/items/D379.md) | composed_or_bootstrapped_derivation | [D379](../../docs/zh/functions/items/D379.md) | converged |
| [D380](../../docs/zh/functions/items/D380.md) | composed_or_bootstrapped_derivation | [D380](../../docs/zh/functions/items/D380.md) | converged |
| [D381](../../docs/zh/functions/items/D381.md) | composed_or_bootstrapped_derivation | [D381](../../docs/zh/functions/items/D381.md) | converged |
| [D382](../../docs/zh/functions/items/D382.md) | composed_or_bootstrapped_derivation | [D382](../../docs/zh/functions/items/D382.md) | converged |
| [D383](../../docs/zh/functions/items/D383.md) | composed_or_bootstrapped_derivation | [D383](../../docs/zh/functions/items/D383.md) | converged |
| [D384](../../docs/zh/functions/items/D384.md) | composed_or_bootstrapped_derivation | [D384](../../docs/zh/functions/items/D384.md) | converged |
| [D385](../../docs/zh/functions/items/D385.md) | composed_or_bootstrapped_derivation | [D385](../../docs/zh/functions/items/D385.md) | converged |
| [D386](../../docs/zh/functions/items/D386.md) | composed_or_bootstrapped_derivation | [D386](../../docs/zh/functions/items/D386.md) | converged |
| [D387](../../docs/zh/functions/items/D387.md) | composed_or_bootstrapped_derivation | [D387](../../docs/zh/functions/items/D387.md) | converged |
| [D388](../../docs/zh/functions/items/D388.md) | composed_or_bootstrapped_derivation | [D388](../../docs/zh/functions/items/D388.md) | converged |
| [D389](../../docs/zh/functions/items/D389.md) | composed_or_bootstrapped_derivation | [D389](../../docs/zh/functions/items/D389.md) | converged |
| [D390](../../docs/zh/functions/items/D390.md) | composed_or_bootstrapped_derivation | [D390](../../docs/zh/functions/items/D390.md) | converged |
| [D391](../../docs/zh/functions/items/D391.md) | composed_or_bootstrapped_derivation | [D391](../../docs/zh/functions/items/D391.md) | converged |
| [D392](../../docs/zh/functions/items/D392.md) | composed_or_bootstrapped_derivation | [D392](../../docs/zh/functions/items/D392.md) | converged |
| [D393](../../docs/zh/functions/items/D393.md) | composed_or_bootstrapped_derivation | [D309](../../docs/zh/functions/items/D309.md), [D379](../../docs/zh/functions/items/D379.md), [D393](../../docs/zh/functions/items/D393.md) | converged |
| [D394](../../docs/zh/functions/items/D394.md) | composed_or_bootstrapped_derivation | [D394](../../docs/zh/functions/items/D394.md) | converged |
| [D395](../../docs/zh/functions/items/D395.md) | composed_or_bootstrapped_derivation | [D395](../../docs/zh/functions/items/D395.md) | converged |
| [D396](../../docs/zh/functions/items/D396.md) | composed_or_bootstrapped_derivation | [D396](../../docs/zh/functions/items/D396.md) | converged |
| [D397](../../docs/zh/functions/items/D397.md) | composed_or_bootstrapped_derivation | [D397](../../docs/zh/functions/items/D397.md) | converged |
| [D398](../../docs/zh/functions/items/D398.md) | composed_or_bootstrapped_derivation | [D398](../../docs/zh/functions/items/D398.md) | converged |
| [D399](../../docs/zh/functions/items/D399.md) | composed_or_bootstrapped_derivation | [D399](../../docs/zh/functions/items/D399.md) | converged |
| [D400](../../docs/zh/functions/items/D400.md) | composed_or_bootstrapped_derivation | [D400](../../docs/zh/functions/items/D400.md) | converged |
| [D401](../../docs/zh/functions/items/D401.md) | composed_or_bootstrapped_derivation | [D401](../../docs/zh/functions/items/D401.md) | converged |
| [D402](../../docs/zh/functions/items/D402.md) | composed_or_bootstrapped_derivation | [D402](../../docs/zh/functions/items/D402.md) | converged |
| [D403](../../docs/zh/functions/items/D403.md) | composed_or_bootstrapped_derivation | [D403](../../docs/zh/functions/items/D403.md) | converged |
| [D404](../../docs/zh/functions/items/D404.md) | composed_or_bootstrapped_derivation | [D404](../../docs/zh/functions/items/D404.md) | converged |
| [D405](../../docs/zh/functions/items/D405.md) | composed_or_bootstrapped_derivation | [D405](../../docs/zh/functions/items/D405.md) | converged |
| [D406](../../docs/zh/functions/items/D406.md) | composed_or_bootstrapped_derivation | [D406](../../docs/zh/functions/items/D406.md) | converged |
| [D407](../../docs/zh/functions/items/D407.md) | composed_or_bootstrapped_derivation | [D407](../../docs/zh/functions/items/D407.md) | converged |
| [D408](../../docs/zh/functions/items/D408.md) | composed_or_bootstrapped_derivation | [D394](../../docs/zh/functions/items/D394.md), [D408](../../docs/zh/functions/items/D408.md) | converged |
| [D409](../../docs/zh/functions/items/D409.md) | composed_or_bootstrapped_derivation | [D409](../../docs/zh/functions/items/D409.md) | converged |
| [D410](../../docs/zh/functions/items/D410.md) | composed_or_bootstrapped_derivation | [D410](../../docs/zh/functions/items/D410.md) | converged |
| [D411](../../docs/zh/functions/items/D411.md) | composed_or_bootstrapped_derivation | [D411](../../docs/zh/functions/items/D411.md) | converged |
| [D412](../../docs/zh/functions/items/D412.md) | composed_or_bootstrapped_derivation | [D412](../../docs/zh/functions/items/D412.md) | converged |
| [D413](../../docs/zh/functions/items/D413.md) | composed_or_bootstrapped_derivation | [D413](../../docs/zh/functions/items/D413.md) | converged |
| [D414](../../docs/zh/functions/items/D414.md) | composed_or_bootstrapped_derivation | [D414](../../docs/zh/functions/items/D414.md) | converged |
| [D415](../../docs/zh/functions/items/D415.md) | composed_or_bootstrapped_derivation | [D415](../../docs/zh/functions/items/D415.md) | converged |
| [D416](../../docs/zh/functions/items/D416.md) | composed_or_bootstrapped_derivation | [D416](../../docs/zh/functions/items/D416.md) | converged |
| [D417](../../docs/zh/functions/items/D417.md) | composed_or_bootstrapped_derivation | [D417](../../docs/zh/functions/items/D417.md) | converged |
| [D418](../../docs/zh/functions/items/D418.md) | composed_or_bootstrapped_derivation | [D418](../../docs/zh/functions/items/D418.md) | converged |
| [D419](../../docs/zh/functions/items/D419.md) | composed_or_bootstrapped_derivation | [D309](../../docs/zh/functions/items/D309.md), [D419](../../docs/zh/functions/items/D419.md) | converged |
| [D420](../../docs/zh/functions/items/D420.md) | composed_or_bootstrapped_derivation | [D420](../../docs/zh/functions/items/D420.md) | converged |
| [D421](../../docs/zh/functions/items/D421.md) | composed_or_bootstrapped_derivation | [D421](../../docs/zh/functions/items/D421.md) | converged |
| [D422](../../docs/zh/functions/items/D422.md) | composed_or_bootstrapped_derivation | [D422](../../docs/zh/functions/items/D422.md) | converged |
| [D423](../../docs/zh/functions/items/D423.md) | composed_or_bootstrapped_derivation | [D423](../../docs/zh/functions/items/D423.md) | converged |
| [D424](../../docs/zh/functions/items/D424.md) | composed_or_bootstrapped_derivation | [D424](../../docs/zh/functions/items/D424.md) | converged |
| [D463](../../docs/zh/functions/items/D463.md) | composed_or_bootstrapped_derivation | [D463](../../docs/zh/functions/items/D463.md) | converged |
| [D464](../../docs/zh/functions/items/D464.md) | composed_or_bootstrapped_derivation | [D464](../../docs/zh/functions/items/D464.md) | converged |
| [D465](../../docs/zh/functions/items/D465.md) | composed_or_bootstrapped_derivation | [D464](../../docs/zh/functions/items/D464.md), [D465](../../docs/zh/functions/items/D465.md) | converged |
| [D466](../../docs/zh/functions/items/D466.md) | composed_or_bootstrapped_derivation | [D464](../../docs/zh/functions/items/D464.md), [D466](../../docs/zh/functions/items/D466.md) | converged |
| [D467](../../docs/zh/functions/items/D467.md) | composed_or_bootstrapped_derivation | [D307](../../docs/zh/functions/items/D307.md), [D467](../../docs/zh/functions/items/D467.md) | converged |
| [D468](../../docs/zh/functions/items/D468.md) | composed_or_bootstrapped_derivation | [D467](../../docs/zh/functions/items/D467.md), [D468](../../docs/zh/functions/items/D468.md) | converged |
| [D469](../../docs/zh/functions/items/D469.md) | composed_or_bootstrapped_derivation | [D468](../../docs/zh/functions/items/D468.md), [D469](../../docs/zh/functions/items/D469.md) | converged |
| [D470](../../docs/zh/functions/items/D470.md) | composed_or_bootstrapped_derivation | [D469](../../docs/zh/functions/items/D469.md), [D470](../../docs/zh/functions/items/D470.md) | converged |
