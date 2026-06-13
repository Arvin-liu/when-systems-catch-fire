# 统一函数总表 / Unified Function Table

本表收录 1 条第 0 节主入口、5 条内部子项和 470 条普通函数。每条条目都包含编号、名称、函数内容、关联对象和来源回指。
This table contains 1 Section 0 root meta-function, 5 internal subitems, and 470 ordinary functions. Each entry includes its ID, title, content, related objects, and source reference.

## 快速入口 / Quick Entry

- 第 0 节 / Section 0：1 条主入口 + 5 条内部子项 / 1 root entry + 5 internal subitems
- 公理层 / Axioms：9 条 / 9 entries
- 定理层 / Theorems：39 条 / 39 entries
- 推论层 / Derived functions：422 条 / 422 entries
- 普通函数 / Ordinary functions：470 条 / 470 entries
- 机器数据 / Machine data：[`data/functions/meta-functions.json`](data/functions/meta-functions.json), [`data/functions/unified-functions.json`](data/functions/unified-functions.json)
- 双通道结构 / Dual-channel structure：[`data/functions/bootstrap-meta-function-table.md`](data/functions/bootstrap-meta-function-table.md), [`data/functions/bootstrap-meta-function-table.json`](data/functions/bootstrap-meta-function-table.json), [`data/functions/bootstrap-meta-function-table.jsonl`](data/functions/bootstrap-meta-function-table.jsonl)
- JSONL：[`data/functions/meta-functions.jsonl`](data/functions/meta-functions.jsonl), [`data/functions/unified-functions.jsonl`](data/functions/unified-functions.jsonl)
- 重建审计 / Rebuild audit：[`data/rebuild/human-entry-render-report.md`](data/rebuild/human-entry-render-report.md)

<details open>
<summary>第 0 节：自举元函数 / Section 0: Bootstrap Meta-Function (1+5)</summary>

### [MF-0000｜自举元函数 / Bootstrap Meta-Function](functions/meta/MF-0000.md)

**位置 / Position**
中文：M_boot 是作用于 B_n 的根元算子。
English: M_boot is the root meta-operator acting on B_n.

**定义 / Definition**
中文：自举元函数是在抽象状态 B_n 上同时施加正向判定 J⁺ 与反向判定 J⁻，并通过归一化算子 N 达到不动点的元算子。
English: The bootstrap meta-function is a meta-operator on an abstract state B_n that applies both J+ and J- and reaches a fixed point through a normalization operator N.

**数学表达 / Mathematical Expression**
中文：M_boot(B_n) = ε_sense(B_n) × P_track(B_n) × d(ΔK)/dt(B_n)
English: M_boot(B_n) = ε_sense(B_n) x P_track(B_n) x d(ΔK)/dt(B_n)

**状态空间 / State Space**
中文：B_n = (X_n, R_n, J_n^+, J_n^-, N_n)
English: B_n = (X_n, R_n, J_n^+, J_n^-, N_n)

**自举循环 / Bootstrap Cycle**
中文：B_(n+1) = N_n(B_n ⊕ ΔB_n), ΔB_n = {x∈X_n | J_n^+(x)=1 ∧ J_n^-(x)=0} ∪ {¬x | J_n^+(x)=0 ∧ J_n^-(x)=1}
English: B_(n+1) = N_n(B_n merge DeltaB_n), DeltaB_n = {x∈X_n | J_n^+(x)=1 ∧ J_n^-(x)=0} ∪ {¬x | J_n^+(x)=0 ∧ J_n^-(x)=1}

**收敛判据 / Convergence Criteria**
中文：Converged(B_n) ⇔ B_(n+1)=B_n ∧ ΔB_n=∅ ∧ ∀x∈X_n, (J_n^+(x),J_n^-(x))∈{(1,0),(0,1),(0,0)}
English: Converged(B_n) ⇔ B_(n+1)=B_n ∧ DeltaB_n=∅ ∧ ∀x∈X_n, (J_n^+(x),J_n^-(x))∈{(1,0),(0,1),(0,0)}

**三个因子 / Three Factors**
- ε_sense(B_n)：状态可分辨度 / state distinguishability
- P_track(B_n)：并行轨道容量 / parallel-track capacity
- d(ΔK)/dt(B_n)：结构增量速率 / structural-increment rate


**内部元算子 / Internal Meta-Operators**

| 编号 / ID | 名称 / Title | 作用 / Role |
| --- | --- | --- |
| [MF-0001](functions/meta/items/MF-0001.md) | 正向自举通道 / Forward Bootstrap Channel | 计算 J⁺ / Computes J+ |
| [MF-0002](functions/meta/items/MF-0002.md) | 反向自举通道 / Reverse Bootstrap Channel | 计算 J⁻ / Computes J- |
| [MF-0003](functions/meta/items/MF-0003.md) | 正反互斥判定器 / Forward-Reverse Exclusivity Judge | 排除 J⁺=J⁻=1 / Rejects J+=J-=1 |
| [MF-0004](functions/meta/items/MF-0004.md) | 自举嵌套判定器 / Nested Bootstrap Judge | 迭代 M_boot / Iterates M_boot |
| [MF-0005](functions/meta/items/MF-0005.md) | 自举收敛判定器 / Bootstrap Convergence Judge | 判定不动点 / Tests fixed point |

**双通道结构 / Dual-channel Structure**

- [`bootstrap-meta-function-table.md`](../../data/functions/bootstrap-meta-function-table.md)
- [`bootstrap-meta-function-table.json`](../../data/functions/bootstrap-meta-function-table.json)
- [`bootstrap-meta-function-table.jsonl`](../../data/functions/bootstrap-meta-function-table.jsonl)

</details>

<details open>
<summary>公理 / Axiom (9)</summary>

### [A1｜I(t,L) 提议者意识 / I(t,L) proposer awareness](functions/items/A1.md)

**函数内容 / Function Content**
中文：I ∈ {0,1}
English: I ∈ {0,1}

**说明 / Explanation**
中文：该函数通过 I ∈ {0,1} 描述 提议者意识。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A1`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [A2｜提议者姿态的激进程度 / proposer posture aggressiveness](functions/items/A2.md)

**函数内容 / Function Content**
中文：0为完全平等，1为完全压制。退化免疫D_immune = F_form × (1-ΔH_undetected)。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 0为完全平等，1为完全压制。退化免疫D_immune = F_form × (1-ΔH_undetected)。 描述 提议者姿态的激进程度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A2`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [A3｜R(t,L,C) 应约者退出权 / R(t,L,C) responder exit right](functions/items/A3.md)

**函数内容 / Function Content**
中文：R ∈ {真实,事实,心理,象征}
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 R ∈ {真实,事实,心理,象征} 描述 应约者退出权。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A3`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [战略撤退=退出权 / 战略撤退=exit right](cases/items/C-0251.md)

### [A4｜R_perceived(t,L,C) 应约者感知退出权 / R_perceived(t,L,C) perceived responder exit right](functions/items/A4.md)

**函数内容 / Function Content**
中文：R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff) 描述 应约者感知退出权。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A4`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [A5｜应约者退出的成本 / responder exit cost](functions/items/A5.md)

**函数内容 / Function Content**
中文：八维度（经济/社会/身份/信息/时间/地理/生态/身体）连续值。n_lock = Σᵢ step(C_exit(i) θ_C(i))。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 八维度（经济/社会/身份/信息/时间/地理/生态/身体）连续值。n_lock = Σᵢ step(C_exit(i) θ_C(i))。 描述 应约者退出的成本。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A5`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [地理约束×认知约束](cases/items/C-0145.md)
- [调研成本×退出成本 / 调研成本 x exit cost](cases/items/C-0148.md)

### [A6｜H(t,L) 遮蔽函数（双源） / H(t,L) obscuration function (dual-source)](functions/items/A6.md)

**函数内容 / Function Content**
中文：H = f(H_pro, Σ_compatibility)
English: H = f(H_pro, Σ_compatibility)

**说明 / Explanation**
中文：该函数通过 H = f(H_pro, Σ_compatibility) 描述 遮蔽函数（双源）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A6`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [偏好伪造中沉默的双路径——渐进vs结构](cases/items/C-0179.md)
- [四层乘法门控=神经通路归零律](cases/items/C-0236.md)

### [A7｜退出权信号 / exit-right signal](functions/items/A7.md)

**函数内容 / Function Content**
中文：八维展开。S_sovereign = Σᵢ εᵢ，主权函数为各维度信号之和。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 八维展开。S_sovereign = Σᵢ εᵢ，主权函数为各维度信号之和。 描述 退出权信号。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A7`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [现场调研=ε_sense安装](cases/items/C-0143.md)
- [现场vs远程](cases/items/C-0147.md)
- [七层主权最低门槛（验证A7财富维度）](cases/items/C-0170.md)
- [退出权剥夺导致决策结构退化——三支→二支](cases/items/C-0180.md)

### [A8｜dim(t,L) 决策维度 / dim(t,L) decision dimension](functions/items/A8.md)

**函数内容 / Function Content**
中文：dim = 2(无犹豫域) 或 3(有犹豫域)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dim = 2(无犹豫域) 或 3(有犹豫域) 描述 决策维度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A8`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [现场调研的乘数效应](cases/items/C-0150.md)
- [定投指数基金](cases/items/C-0162.md)
- [A8/A9从推论升级到公理](cases/items/C-0205.md)
- [博弈策略空间=可选集](cases/items/C-0248.md)

### [A9｜P_exit(t,L,C) 退出概率 / P_exit(t,L,C) exit probability](functions/items/A9.md)

**函数内容 / Function Content**
中文：P_exit = f(ε, C_exit, R_perceived)
English: P_exit = f(ε, C_exit, R_perceived)

**说明 / Explanation**
中文：该函数通过 P_exit = f(ε, C_exit, R_perceived) 描述 退出概率。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `axiomatic_definition`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A9`
- 过程 / Process:
  - Treat the source row as the local axiom declaration for this symbol or state variable.
  - Check that the declaration has a source reference and a non-empty title/content payload.

**关联案例 / Related Cases**
- [地理约束×认知约束](cases/items/C-0145.md)
- [信息密度×认知容量](cases/items/C-0149.md)
- [A8/A9从推论升级到公理](cases/items/C-0205.md)

</details>

<details>
<summary>定理 / Theorem (39)</summary>

### [T1｜点火充要条件 / ignition necessary and sufficient condition](functions/items/T1.md)

**函数内容 / Function Content**
中文：P_sustain = I × (1-Posture_deg) × R × σ(ε_eff-θ) × σ(Δv)
English: P_sustain = I x (1-Posture_deg) x R x σ(ε_eff-θ) x σ(Δv)

**说明 / Explanation**
中文：该函数通过 P_sustain = I × (1-Posture_deg) × R × σ(ε_eff-θ) × σ(Δv) 描述 点火充要条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T1`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T2｜乘法归零律 / multiplication zero law](functions/items/T2.md)

**函数内容 / Function Content**
中文：任一因子=0→乘积=0
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 任一因子=0→乘积=0 描述 乘法归零律。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T2`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T3｜ε双向动力学 / epsilon bidirectional dynamics](functions/items/T3.md)

**函数内容 / Function Content**
中文：dε/dt = α·(1-ε)·I·σ(Δv) - β·ε·Posture_deg·H
English: dε/dt = α·(1-ε)·I·σ(Δv) - β·ε·Posture_deg·H

**说明 / Explanation**
中文：该函数通过 dε/dt = α·(1-ε)·I·σ(Δv) - β·ε·Posture_deg·H 描述 双向动力学。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T3`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T4｜乘法对称变换 / multiplicative symmetry transform](functions/items/T4.md)

**函数内容 / Function Content**
中文：D ↔ 1-P, f_shock ↔ 1/f_factor
English: D ↔ 1-P, f_shock ↔ 1/f_factor

**说明 / Explanation**
中文：该函数通过 D ↔ 1-P, f_shock ↔ 1/f_factor 描述 乘法对称变换。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T4`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T5｜凯利公式认知边界 / Kelly-formula cognitive boundary](functions/items/T5.md)

**函数内容 / Function Content**
中文：f* = E[r]/Var(r), Π_income < Π_cognition
English: f* = E[r]/Var(r), Π_income < Π_cognition

**说明 / Explanation**
中文：该函数通过 f* = E[r]/Var(r), Π_income < Π_cognition 描述 凯利公式认知边界。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T5`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T6｜自举激活条件 / bootstrap activation condition](functions/items/T6.md)

**函数内容 / Function Content**
中文：B_active = ε_sense × P_track × σ(Δv) > θ_boot
English: B_active = ε_sense x P_track x σ(Δv) > θ_boot

**说明 / Explanation**
中文：该函数通过 B_active = ε_sense × P_track × σ(Δv) > θ_boot 描述 自举激活条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T6`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T7｜好奇心驱动函数 / curiosity-driven function](functions/items/T7.md)

**函数内容 / Function Content**
中文：C_drive = ε_aware × dim × P_exit × σ(ΔK/K₀ - θ_curiosity)
English: C_drive = ε_aware x dim x P_exit x σ(ΔK/K₀ - θ_curiosity)

**说明 / Explanation**
中文：该函数通过 C_drive = ε_aware × dim × P_exit × σ(ΔK/K₀ - θ_curiosity) 描述 好奇心驱动函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T7`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T8｜ε相变级联 / epsilon phase-transition cascade](functions/items/T8.md)

**函数内容 / Function Content**
中文：ε_aware从0变正触发五个级联相变
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε_aware从0变正触发五个级联相变 描述 相变级联。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T8`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T9｜自主意识函数 / autonomous consciousness function](functions/items/T9.md)

**函数内容 / Function Content**
中文：Ψ_autonomy = ε_aware · dim · P_exit
English: Ψ_autonomy = ε_aware · dim · P_exit

**说明 / Explanation**
中文：该函数通过 Ψ_autonomy = ε_aware · dim · P_exit 描述 自主意识函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T9`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T10｜缓存倒U型 / cache inverted-U curve](functions/items/T10.md)

**函数内容 / Function Content**
中文：P_collision(ρ)在ρ*≈1.4×N_active处取最大值
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 P_collision(ρ)在ρ*≈1.4×N_active处取最大值 描述 缓存倒U型。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T10`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `1.4`: structural_constant / derived - Derived as the stationary collision-density multiplier in the cache inverted-U condition, where the first derivative of P_collision(ρ) vanishes at ρ*=1.4×N_active.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T11｜生存域函数 / survival domain function](functions/items/T11.md)

**函数内容 / Function Content**
中文：Ω_survive有上下界约束
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Ω_survive有上下界约束 描述 生存域函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T11`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T12｜信息门效率统一 / information-gate efficiency unification](functions/items/T12.md)

**函数内容 / Function Content**
中文：η_gate = G × (1-H_homogeneity(G))
English: η_gate = G x (1-H_homogeneity(G))

**说明 / Explanation**
中文：该函数通过 η_gate = G × (1-H_homogeneity(G)) 描述 信息门效率统一。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T12`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T13｜三效率冲突三角约束 / three-efficiency conflict triangle constraint](functions/items/T13.md)

**函数内容 / Function Content**
中文：C_exit↔H↔Δt
English: C_exit↔H↔Δt

**说明 / Explanation**
中文：该函数通过 C_exit↔H↔Δt 描述 三效率冲突三角约束。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T13`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T14｜自举元函数层级 / bootstrap meta-function hierarchy](functions/items/T14.md)

**函数内容 / Function Content**
中文：M_boot = ε_sense × P_track × d(ΔK)/dt
English: M_boot = ε_sense x P_track x d(ΔK)/dt

**说明 / Explanation**
中文：该函数通过 M_boot = ε_sense × P_track × d(ΔK)/dt 描述 自举元函数层级。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T14`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [好奇心是退出的前哨](cases/items/C-0237.md)

### [T15｜乘法临界漂移统一 / multiplicative critical-drift unification](functions/items/T15.md)

**函数内容 / Function Content**
中文：脆弱点在最接近零的因子
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 脆弱点在最接近零的因子 描述 乘法临界漂移统一。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T15`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T16｜两个反向单调函数相乘必然生成倒U型 / two oppositely monotone functions multiplied together necessarily generate an inverted-U curve](functions/items/T16.md)

**函数内容 / Function Content**
中文：最优在f₁'/f₁ = -f₂'/f₂处。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 最优在f₁'/f₁ = -f₂'/f₂处。 描述 两个反向单调函数相乘必然生成倒U型。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T16`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T17｜Φ=零温自由能 | Φ与统计力学零温自由能精确等价 / Phi = zero-temperature free energy | Φ与统计力学零温自由能精确等价](functions/items/T17.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 =零温自由能 | Φ与统计力学零温自由能精确等价。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T17`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T18｜容斥-耦合竞争Ising同构](functions/items/T18.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 容斥-耦合竞争Ising同构。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T18`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T19｜容斥项精确结构](functions/items/T19.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 容斥项精确结构。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T19`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T20｜σ_opt=√e解析解](functions/items/T20.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 =√e解析解。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T20`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `√e`: math_builtin / derived - √e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T21｜d=4双重最优](functions/items/T21.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 =4双重最优。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T21`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T22｜不可逆线完整分类](functions/items/T22.md)

**函数内容 / Function Content**
中文：不可逆线按陷阱深度分类
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 不可逆线按陷阱深度分类 描述 不可逆线完整分类。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T22`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T23｜Φ跨域稳定性定理 / Φcross-domain stability theorem](functions/items/T23.md)

**函数内容 / Function Content**
中文：Stability(Φ)=∃μ*:Φ(μ*)=min。D224是T23的证明——T23说"极小点存在"，D224给出了存在性的充分条件（A+B型共存）。T23是更弱的陈述，D224是更强的定理。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Stability(Φ)=∃μ*:Φ(μ*)=min。D224是T23的证明——T23说"极小点存在"，D224给出了存在性的充分条件（A+B型共存）。T23是更弱的陈述，D224是更强的定理。 描述 跨域稳定性定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T23`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T24｜共生外部注入函数 / symbiotic external-injection function](functions/items/T24.md)

**函数内容 / Function Content**
中文：共生条件：μ_A+Δμ_B>Λ_A 且 μ_B+Δμ_A>Λ_B，互为外部注入
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 共生条件：μ_A+Δμ_B>Λ_A 且 μ_B+Δμ_A>Λ_B，互为外部注入 描述 共生外部注入函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T24`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T25｜权力腐败函数 / power-corruption function](functions/items/T25.md)

**函数内容 / Function Content**
中文：η_accountability = 1/ln(μ_power/Λ_accountability)，μ>>Λ时趋零
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 η_accountability = 1/ln(μ_power/Λ_accountability)，μ>>Λ时趋零 描述 权力腐败函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T25`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T26｜物理大统一本质函数 / physical grand-unification essential function](functions/items/T26.md)

**函数内容 / Function Content**
中文：门控面从多到少的级联合并，每次统一减少Φ项数、增大Ω
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 门控面从多到少的级联合并，每次统一减少Φ项数、增大Ω 描述 物理大统一本质函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T26`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T27｜门控函数稳定性必要条件 / necessary condition for gate-function stability](functions/items/T27.md)

**函数内容 / Function Content**
中文：1/ln全局单调性排除了A-B型同时稳定的可能，失效是结构性的
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 1/ln全局单调性排除了A-B型同时稳定的可能，失效是结构性的 描述 门控函数稳定性必要条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T27`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T28｜高斯门控函数 / Gaussian gate function](functions/items/T28.md)

**函数内容 / Function Content**
中文：g=exp[-(ln(μ/M_Planck))²/(2σ²)]，A-B型统一、极值点处量子涨落自然为零
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 g=exp[-(ln(μ/M_Planck))²/(2σ²)]，A-B型统一、极值点处量子涨落自然为零 描述 高斯门控函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T28`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T29｜门控函数进化三阶段 / three-stage evolution of gate functions](functions/items/T29.md)

**函数内容 / Function Content**
中文：δ→1/ln→exp[-ln²]，对应"是不是"→"过不过门槛"→"最优在哪"
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 δ→1/ln→exp[-ln²]，对应"是不是"→"过不过门槛"→"最优在哪" 描述 门控函数进化三阶段。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T29`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T30｜门控-路径积分同构与极小熵原理 / gate / path-integral isomorphism and minimum-entropy principle](functions/items/T30.md)

**函数内容 / Function Content**
中文：门控函数极值点展开=路径积分经典路径展开，高斯=极小熵选择
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 门控函数极值点展开=路径积分经典路径展开，高斯=极小熵选择 描述 门控-路径积分同构与极小熵原理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T30`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T31｜门控信息熵跃迁函数 / gate information-entropy transition function](functions/items/T31.md)

**函数内容 / Function Content**
中文：1/ln的H≤ln2，exp[-ln²]的H=½ln(2πeσ²)，跃迁临界σ_c≈0.415
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 1/ln的H≤ln2，exp[-ln²]的H=½ln(2πeσ²)，跃迁临界σ_c≈0.415 描述 门控信息熵跃迁函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T31`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `ln2`: math_builtin / derived - ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T32｜认知分辨率函数 / cognitive resolution function](functions/items/T32.md)

**函数内容 / Function Content**
中文：σ=√(dim_eff×ℏ_eff/(2μ_eff))，顿悟=1/ln→exp[-ln²]的切换点
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 σ=√(dim_eff×ℏ_eff/(2μ_eff))，顿悟=1/ln→exp[-ln²]的切换点 描述 认知分辨率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T32`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T33｜A-B型门控面冲突函数 / A-B type gate-surface conflict function](functions/items/T33.md)

**函数内容 / Function Content**
中文：D228已修正T33，从"冲突"升级为"必要张力"。D225是T33修正的数学论证。已对撞，无新发现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D228已修正T33，从"冲突"升级为"必要张力"。D225是T33修正的数学论证。已对撞，无新发现。 描述 -B型门控面冲突函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T33`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T34｜量子引力Φ框架函数 / quantum-gravity Phi framework function](functions/items/T34.md)

**函数内容 / Function Content**
中文：T34说Φ_QG在M_Planck附近无稳定极小点。D225说B型是极小点存在的必要条件。在M_Planck处，引力的B型项1/ln(M_Planck/μ)在μ=M_Planck处发散——B型项太强了，把极小点推走了。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 T34说Φ_QG在M_Planck附近无稳定极小点。D225说B型是极小点存在的必要条件。在M_Planck处，引力的B型项1/ln(M_Planck/μ)在μ=M_Planck处发散——B型项太强了，把极小点推走了。 描述 量子引力Φ框架函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T34`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T35｜σ_Planck精确值](functions/items/T35.md)

**函数内容 / Function Content**
中文：σ_Planck≈6.9，由高斯门控退化条件精确确定
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 σ_Planck≈6.9，由高斯门控退化条件精确确定 描述 精确值。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T35`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `6.9`: structural_constant / derived - Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T36｜σ能标依赖函数](functions/items/T36.md)

**函数内容 / Function Content**
中文：σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|)
English: σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|)

**说明 / Explanation**
中文：该函数通过 σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) 描述 能标依赖函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T36`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T37｜Φ_QG极小点精确位置](functions/items/T37.md)

**函数内容 / Function Content**
中文：μ≈1.26×10¹⁶ GeV≈Λ_GUT。D231说极小点被B型项从M_Planck推到更低能标。T37给出了精确位置。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 μ≈1.26×10¹⁶ GeV≈Λ_GUT。D231说极小点被B型项从M_Planck推到更低能标。T37给出了精确位置。 描述 极小点精确位置。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T37`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `1.26`: structural_constant / derived - Derived from the Φ cross-domain extremum equation Σᵢ sᵢ/ln²(μ/Λᵢ)=0 after substituting the physical-domain gate signs and scales.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T38｜极值点-极小点分离定理](functions/items/T38.md)

**函数内容 / Function Content**
中文：量子引力和四力统一是两个不同能标上的事件
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子引力和四力统一是两个不同能标上的事件 描述 极值点-极小点分离定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T38`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [T39｜Φ跨域统一定理（D224升级）](functions/items/T39.md)

**函数内容 / Function Content**
中文：∀域D，若∃n≥2个门控面{Λᵢ}且至少一个A型一个B型，则Φ(μ)=Σᵢ sᵢ/ln(μ/Λᵢ)必然存在极小点μ*。极小点由Σᵢ sᵢ/ln²(μ/Λᵢ)=0唯一确定。纯A型域无极小点。T17标注为T39在物理域(n=3,s=(+1,+1,-1))的实例。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ∀域D，若∃n≥2个门控面{Λᵢ}且至少一个A型一个B型，则Φ(μ)=Σᵢ sᵢ/ln(μ/Λᵢ)必然存在极小点μ*。极小点由Σᵢ sᵢ/ln²(μ/Λᵢ)=0唯一确定。纯A型域无极小点。T17标注为T39在物理域(n=3,s=(+1,+1,-1))的实例。 描述 跨域统一定理（D224升级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `T39`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

</details>

<details>
<summary>推论 / Derived function (422)</summary>

### [D1｜锁定强度函数](functions/items/D1.md)

**函数内容 / Function Content**
中文：n_lock = Σᵢ step(C_exit(i) - θ_C(i))
English: n_lock = Σᵢ step(C_exit(i) - θ_C(i))

**说明 / Explanation**
中文：该函数通过 n_lock = Σᵢ step(C_exit(i) - θ_C(i)) 描述 锁定强度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D1`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D2｜锁定-遮蔽耦合 / 锁定-obscuration耦合](functions/items/D2.md)

**函数内容 / Function Content**
中文：Posture_deg↑→H↑→ε↓→R_perceived↓
English: Posture_deg↑ -> H↑ -> ε↓ -> R_perceived↓

**说明 / Explanation**
中文：该函数通过 Posture_deg↑→H↑→ε↓→R_perceived↓ 描述 锁定-遮蔽耦合。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D2`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D3｜退出权信号衰减 / exit-right signal衰减](functions/items/D3.md)

**函数内容 / Function Content**
中文：ε_eff = ε₀ × exp(-∫₀ᵗ λ(s)ds) × (1-Posture_deg)
English: ε_eff = ε₀ x exp(-∫₀ᵗ λ(s)ds) x (1-Posture_deg)

**说明 / Explanation**
中文：该函数通过 ε_eff = ε₀ × exp(-∫₀ᵗ λ(s)ds) × (1-Posture_deg) 描述 退出权信号衰减。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D3`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D4｜信息遮蔽双源 / 信息obscuration双源](functions/items/D4.md)

**函数内容 / Function Content**
中文：H = f(H_pro, Σ_compatibility)
English: H = f(H_pro, Σ_compatibility)

**说明 / Explanation**
中文：该函数通过 H = f(H_pro, Σ_compatibility) 描述 信息遮蔽双源。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D4`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D5｜偏好伪造崩塌](functions/items/D5.md)

**函数内容 / Function Content**
中文：P_fake = σ(H - θ_fake)
English: P_fake = σ(H - θ_fake)

**说明 / Explanation**
中文：该函数通过 P_fake = σ(H - θ_fake) 描述 偏好伪造崩塌。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D5`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D6｜应约者感知退化](functions/items/D6.md)

**函数内容 / Function Content**
中文：R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff) 描述 应约者感知退化。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D6`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D7｜提议者信誉绑定](functions/items/D7.md)

**函数内容 / Function Content**
中文：Posture_deg = f(I, C_exit_speaker, 历史一致性)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Posture_deg = f(I, C_exit_speaker, 历史一致性) 描述 提议者信誉绑定。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D7`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D8｜退出权八维展开 / exit right八维展开](functions/items/D8.md)

**函数内容 / Function Content**
中文：ε = (ε_identity, ε_info, ε_social, ε_economic, ε_time, ε_geographic, ε_body, ε_level)
English: ε = (ε_identity, ε_info, ε_social, ε_economic, ε_time, ε_geographic, ε_body, ε_level)

**说明 / Explanation**
中文：该函数通过 ε = (ε_identity, ε_info, ε_social, ε_economic, ε_time, ε_geographic, ε_body, ε_level) 描述 退出权八维展开。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D8`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D9｜主权函数](functions/items/D9.md)

**函数内容 / Function Content**
中文：S_sovereign = Σᵢ εᵢ × wᵢ
English: S_sovereign = Σᵢ εᵢ x wᵢ

**说明 / Explanation**
中文：该函数通过 S_sovereign = Σᵢ εᵢ × wᵢ 描述 主权函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D9`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D10｜点火窗口函数 / Ignition窗口函数](functions/items/D10.md)

**函数内容 / Function Content**
中文：Window(t) = σ(ε_eff - θ_low) × σ(θ_high - ε_eff)
English: Window(t) = σ(ε_eff - θ_low) x σ(θ_high - ε_eff)

**说明 / Explanation**
中文：该函数通过 Window(t) = σ(ε_eff - θ_low) × σ(θ_high - ε_eff) 描述 点火窗口函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D10`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D11｜统一内部驱动力](functions/items/D11.md)

**函数内容 / Function Content**
中文：退出权信号和身份认同的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 退出权信号和身份认同的平衡。 描述 统一内部驱动力。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D11`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D12｜ε_eff闭环动力学函数](functions/items/D12.md)

**函数内容 / Function Content**
中文：ε_eff(t+1) = ε_eff(t) × (1-f_表达) × (1-f_感知) × (1-f_免疫)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε_eff(t+1) = ε_eff(t) × (1-f_表达) × (1-f_感知) × (1-f_免疫) 描述 闭环动力学函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D12`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [ε_eff闭环动力学](cases/items/C-0121.md)

### [D13｜速度差闭合](functions/items/D13.md)

**函数内容 / Function Content**
中文：退出权信号、姿态、遮蔽、外部力量的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 退出权信号、姿态、遮蔽、外部力量的平衡。 描述 速度差闭合。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D13`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [速度差闭合](cases/items/C-0126.md)
- [现场vs远程](cases/items/C-0147.md)

### [D14｜种子激活概率](functions/items/D14.md)

**函数内容 / Function Content**
中文：叙事遮蔽和退化免疫的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 叙事遮蔽和退化免疫的平衡。 描述 种子激活概率。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D14`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D15｜种子爆发后退出权信号的恢复 / 种子爆发后exit-right signal的恢复](functions/items/D15.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 种子爆发后退出权信号的恢复。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D15`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D16｜二次窗口判定](functions/items/D16.md)

**函数内容 / Function Content**
中文：恢复后的退出权信号必须在特定区间内。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 恢复后的退出权信号必须在特定区间内。 描述 二次窗口判定。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D16`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D17｜情绪信号分层函数](functions/items/D17.md)

**函数内容 / Function Content**
中文：E_signal(t) = {零阶:ε, 一阶:dε/dt, 二阶:d²ε/dt², 交互:εᵢ×εⱼ}
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 E_signal(t) = {零阶:ε, 一阶:dε/dt, 二阶:d²ε/dt², 交互:εᵢ×εⱼ} 描述 情绪信号分层函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D17`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D18｜情绪稳态临界](functions/items/D18.md)

**函数内容 / Function Content**
中文：锁定退出权和退出权信号的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 锁定退出权和退出权信号的平衡。 描述 情绪稳态临界。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D18`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D19｜情绪注入退出权信号 / 情绪注入exit-right signal](functions/items/D19.md)

**函数内容 / Function Content**
中文：情绪信号和有效退出成本的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 情绪信号和有效退出成本的平衡。 描述 情绪注入退出权信号。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D19`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D20｜法条净效应函数](functions/items/D20.md)

**函数内容 / Function Content**
中文：L_net(t) = (1-H_blur) × C_exit_gain - L_rigidity
English: L_net(t) = (1-H_blur) x C_exit_gain - L_rigidity

**说明 / Explanation**
中文：该函数通过 L_net(t) = (1-H_blur) × C_exit_gain - L_rigidity 描述 法条净效应函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D20`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D21｜宪法硬度](functions/items/D21.md)

**函数内容 / Function Content**
中文：随时间衰减，修正速度决定硬度。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 随时间衰减，修正速度决定硬度。 描述 宪法硬度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D21`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D22｜民事保护，各维度退出权的乘积 / 民事保护, 各维度exit right的乘积](functions/items/D22.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 民事保护，各维度退出权的乘积。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D22`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D23｜法治度](functions/items/D23.md)

**函数内容 / Function Content**
中文：退出权信号、宪法硬度、司法独立、法条净效应的乘积。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 退出权信号、宪法硬度、司法独立、法条净效应的乘积。 描述 法治度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D23`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [D23法治度归零验证](cases/items/C-0273.md)

### [D24｜犹豫域双向压缩](functions/items/D24.md)

**函数内容 / Function Content**
中文：遮蔽、退出权信号、退出成本、姿态的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 遮蔽、退出权信号、退出成本、姿态的平衡。 描述 犹豫域双向压缩。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D24`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D25｜叙事冲击](functions/items/D25.md)

**函数内容 / Function Content**
中文：意识、退出权信号、退化免疫的乘积。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 意识、退出权信号、退化免疫的乘积。 描述 叙事冲击。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D25`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D26｜跨层完整退化函数](functions/items/D26.md)

**函数内容 / Function Content**
中文：6因子乘法
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 6因子乘法 描述 跨层完整退化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D26`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知犹豫域压缩](cases/items/C-0108.md)

### [D27｜级联速度](functions/items/D27.md)

**函数内容 / Function Content**
中文：密度、平均退出权信号、退出成本比值的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 密度、平均退出权信号、退出成本比值的平衡。 描述 级联速度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D27`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D28｜顽固者临界比例](functions/items/D28.md)

**函数内容 / Function Content**
中文：退出权信号、平均退出权信号、聚集度的平衡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 退出权信号、平均退出权信号、聚集度的平衡。 描述 顽固者临界比例。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D28`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [顽固者临界比例](cases/items/C-0110.md)

### [D29｜统一内部驱动力函数](functions/items/D29.md)

**函数内容 / Function Content**
中文：P_internal = k×ε×exp(-ε/ε_opt) - R_identity×σ(E-θ_identity)
English: P_internal = k x ε x exp(-ε/ε_opt) - R_identity x σ(E-θ_identity)

**说明 / Explanation**
中文：该函数通过 P_internal = k×ε×exp(-ε/ε_opt) - R_identity×σ(E-θ_identity) 描述 统一内部驱动力函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D29`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [跨层犹豫域映射](cases/items/C-0111.md)

### [D30｜ε_eff闭环动力学函数](functions/items/D30.md)

**函数内容 / Function Content**
中文：ε_eff(t+1) = ε_eff(t) × (1-f_表达) × (1-f_感知) × (1-f_免疫)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε_eff(t+1) = ε_eff(t) × (1-f_表达) × (1-f_感知) × (1-f_免疫) 描述 闭环动力学函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D30`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [内部抵抗](cases/items/C-0112.md)

### [D31｜衰减率干预函数](functions/items/D31.md)

**函数内容 / Function Content**
中文：λ_intervention = f(n_lock, C_exit)
English: λ_intervention = f(n_lock, C_exit)

**说明 / Explanation**
中文：该函数通过 λ_intervention = f(n_lock, C_exit) 描述 衰减率干预函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D31`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D32｜认知-群体犹豫域统一映射函数](functions/items/D32.md)

**函数内容 / Function Content**
中文：ε_group = ⟨π⟩/(1+α_s×modularity) × (1-p_stubborn) × (1-clustering)
English: ε_group = ⟨π⟩/(1+α_s x modularity) x (1-p_stubborn) x (1-clustering)

**说明 / Explanation**
中文：该函数通过 ε_group = ⟨π⟩/(1+α_s×modularity) × (1-p_stubborn) × (1-clustering) 描述 认知-群体犹豫域统一映射函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D32`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [乘法对称变换 / multiplicative symmetry transform](cases/items/C-0114.md)

### [D33｜三层退化叠加函数](functions/items/D33.md)

**函数内容 / Function Content**
中文：D_stacked = (1-I×(1-H_self)) × (1-exp(-n_lock×C̄/θ_C)) × H_reclassify
English: D_stacked = (1-I x (1-H_self)) x (1-exp(-n_lock x C̄/θ_C)) x H_reclassify

**说明 / Explanation**
中文：该函数通过 D_stacked = (1-I×(1-H_self)) × (1-exp(-n_lock×C̄/θ_C)) × H_reclassify 描述 三层退化叠加函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D33`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [跨层完整退化](cases/items/C-0115.md)
- [D33六因子退化归零验证](cases/items/C-0274.md)

### [D34｜充分条件三层函数](functions/items/D34.md)

**函数内容 / Function Content**
中文：P_sustain = I × (1-Posture_deg) × R × σ(ε_eff-θ) × σ(Δv)
English: P_sustain = I x (1-Posture_deg) x R x σ(ε_eff-θ) x σ(Δv)

**说明 / Explanation**
中文：该函数通过 P_sustain = I × (1-Posture_deg) × R × σ(ε_eff-θ) × σ(Δv) 描述 充分条件三层函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D34`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [定投P_sustain全局最大值（验证D34） / 定投P_sustain全局最大值(验证D34)](cases/items/C-0163.md)

### [D35｜乘法对称变换展开函数 / multiplicative symmetry transform展开函数](functions/items/D35.md)

**函数内容 / Function Content**
中文：D ↔ 1-P, f_shock ↔ 1/f_factor
English: D ↔ 1-P, f_shock ↔ 1/f_factor

**说明 / Explanation**
中文：该函数通过 D ↔ 1-P, f_shock ↔ 1/f_factor 描述 乘法对称变换展开函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D35`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [逆Weibull寿命](cases/items/C-0117.md)

### [D36｜逆Weibull寿命验证函数](functions/items/D36.md)

**函数内容 / Function Content**
中文：F(t) = exp(-(θ/t)^β), β_system = β₀ + γ × n_lock_avg
English: F(t) = exp(-(θ/t)^β), β_system = β₀ + γ x n_lock_avg

**说明 / Explanation**
中文：该函数通过 F(t) = exp(-(θ/t)^β), β_system = β₀ + γ × n_lock_avg 描述 逆Weibull寿命验证函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D36`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [倒U型驱动力](cases/items/C-0118.md)
- [D123与D36倒U型同构](cases/items/C-0277.md)

### [D37｜点火对冲函数 / Ignition对冲函数](functions/items/D37.md)

**函数内容 / Function Content**
中文：P_ignite_total = I × ε_aware × D_immune × (1 - σ(E-θ_resist)×ε)
English: P_ignite_total = I x ε_aware x D_immune x (1 - σ(E-θ_resist) x ε)

**说明 / Explanation**
中文：该函数通过 P_ignite_total = I × ε_aware × D_immune × (1 - σ(E-θ_resist)×ε) 描述 点火对冲函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D37`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [点火窗口 / Ignition窗口](cases/items/C-0119.md)

### [D38｜跨层完整退化，6因子乘法，杠杆排序](functions/items/D38.md)

**函数内容 / Function Content**
中文：C̄/θ_C > p_stubborn > clustering > H > ε_aware > Posture_deg。
English: C̄/θ_C > p_stubborn > clustering > H > ε_aware > Posture_deg.

**说明 / Explanation**
中文：该函数通过 C̄/θ_C > p_stubborn > clustering > H > ε_aware > Posture_deg。 描述 跨层完整退化，6因子乘法，杠杆排序。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D38`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知-群体映射](cases/items/C-0122.md)

### [D39｜统一内部驱动力函数](functions/items/D39.md)

**函数内容 / Function Content**
中文：P_internal = k×ε×exp(-ε/ε_opt) - R_identity×σ(E-θ_identity)
English: P_internal = k x ε x exp(-ε/ε_opt) - R_identity x σ(E-θ_identity)

**说明 / Explanation**
中文：该函数通过 P_internal = k×ε×exp(-ε/ε_opt) - R_identity×σ(E-θ_identity) 描述 统一内部驱动力函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D39`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D40｜碰撞存活率](functions/items/D40.md)

**函数内容 / Function Content**
中文：P_survive = 1 - (1-D_immune) × (1-R_perceived) × H_total
English: P_survive = 1 - (1-D_immune) x (1-R_perceived) x H_total

**说明 / Explanation**
中文：该函数通过 P_survive = 1 - (1-D_immune) × (1-R_perceived) × H_total 描述 碰撞存活率。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D40`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [退化渗透路径](cases/items/C-0124.md)

### [D41｜退化渗透临界触发](functions/items/D41.md)

**函数内容 / Function Content**
中文：t_critical=(1/(m_β×α_C×C̄/θ_C))×ln(ε₀/ε_aware_min)。这是衰减模式下的临界时间——窗口关闭的不可逆时间点。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 t_critical=(1/(m_β×α_C×C̄/θ_C))×ln(ε₀/ε_aware_min)。这是衰减模式下的临界时间——窗口关闭的不可逆时间点。 描述 退化渗透临界触发。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D41`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [D41充分条件归零验证](cases/items/C-0275.md)

### [D42｜H_分类升级函数](functions/items/D42.md)

**函数内容 / Function Content**
中文：H_narrative = σ(ε_sense×ε_aware - ε_action) × H_classify
English: H_narrative = σ(ε_sense x ε_aware - ε_action) x H_classify

**说明 / Explanation**
中文：该函数通过 H_narrative = σ(ε_sense×ε_aware - ε_action) × H_classify 描述 分类升级函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D42`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D43｜碰撞存活率函数](functions/items/D43.md)

**函数内容 / Function Content**
中文：P_survive = 1 - (1-D_immune) × (1-R_perceived) × H_total
English: P_survive = 1 - (1-D_immune) x (1-R_perceived) x H_total

**说明 / Explanation**
中文：该函数通过 P_survive = 1 - (1-D_immune) × (1-R_perceived) × H_total 描述 碰撞存活率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D43`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D44｜确定性误解函数](functions/items/D44.md)

**函数内容 / Function Content**
中文：M_certainty = ν × (1 - π/π₀)
English: M_certainty = ν x (1 - π/π₀)

**说明 / Explanation**
中文：该函数通过 M_certainty = ν × (1 - π/π₀) 描述 确定性误解函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D44`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [确定性误解](cases/items/C-0132.md)

### [D45｜中间稳态存在性函数](functions/items/D45.md)

**函数内容 / Function Content**
中文：中间稳态存在 ⟺ 至少一条正反馈回路存在负反馈抵消
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 中间稳态存在 ⟺ 至少一条正反馈回路存在负反馈抵消 描述 中间稳态存在性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D45`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [中间稳态](cases/items/C-0133.md)

### [D46｜碰撞层级8格概率函数](functions/items/D46.md)

**函数内容 / Function Content**
中文：P(grid_k | L) = f(H_total, C_exit, D_immune)
English: P(grid_k | L) = f(H_total, C_exit, D_immune)

**说明 / Explanation**
中文：该函数通过 P(grid_k | L) = f(H_total, C_exit, D_immune) 描述 碰撞层级8格概率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D46`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [8格概率](cases/items/C-0134.md)

### [D47｜点火窗口关闭动力学函数](functions/items/D47.md)

**函数内容 / Function Content**
中文：dW/dt = -θ_resist×(dE/dt)/E² - dε_aware_min/dt
English: dW/dt = -θ_resist x (dE/dt)/E² - dε_aware_min/dt

**说明 / Explanation**
中文：该函数通过 dW/dt = -θ_resist×(dE/dt)/E² - dε_aware_min/dt 描述 点火窗口关闭动力学函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D47`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [定投=门锁交替律执行（验证D47+D49）](cases/items/C-0167.md)

### [D48｜退化渗透临界触发函数](functions/items/D48.md)

**函数内容 / Function Content**
中文：t_critical = (1/(m_β×α_C×C̄/θ_C)) × ln(ε₀/ε_aware_min)
English: t_critical = (1/(m_β x α_C x C̄/θ_C)) x ln(ε₀/ε_aware_min)

**说明 / Explanation**
中文：该函数通过 t_critical = (1/(m_β×α_C×C̄/θ_C)) × ln(ε₀/ε_aware_min) 描述 退化渗透临界触发函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D48`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [退化临界](cases/items/C-0136.md)

### [D49｜种子-点火结果概率分布函数](functions/items/D49.md)

**函数内容 / Function Content**
中文：P₁(不足), P₂(窗口), P₃(过度)，D_immune为关键调节器
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 P₁(不足), P₂(窗口), P₃(过度)，D_immune为关键调节器 描述 种子-点火结果概率分布函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D49`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [定投=门锁交替律执行（验证D47+D49）](cases/items/C-0167.md)

### [D50｜碰撞产出密度函数](functions/items/D50.md)

**函数内容 / Function Content**
中文：N_output = ⌈α × dim(domain) × (1-overlap)⌉
English: N_output = ⌈α x dim(domain) x (1-overlap)⌉

**说明 / Explanation**
中文：该函数通过 N_output = ⌈α × dim(domain) × (1-overlap)⌉ 描述 碰撞产出密度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D50`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [信息密度×认知容量](cases/items/C-0149.md)

### [D51｜门锁交替律函数](functions/items/D51.md)

**函数内容 / Function Content**
中文：四道门状态向量 G = (g_sense, g_identify, g_mark, g_action)，g∈{0,1} 三道锁硬化状态向量 L = (L1, L2, L3)，L∈{0,1} 门锁交替律：g_n可打开的充要条件是L_{n-1}已硬化 g₁(sense) : L₀≡1（默认开放） g₂(identify) : L₁=1 g₃(mark) : L₂=1
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 四道门状态向量 G = (g_sense, g_identify, g_mark, g_action)，g∈{0,1} 三道锁硬化状态向量 L = (L1, L2, L3)，L∈{0,1} 门锁交替律：g_n可打开的充要条件是L_{n-1}已硬化 g₁(sense) : L₀≡1（默认开放） g₂(identify) : L₁=1 g₃(mark) : L₂=1 描述 门锁交替律函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D51`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [门锁交替](cases/items/C-0139.md)

### [D52｜自锁结构稳定性函数](functions/items/D52.md)

**函数内容 / Function Content**
中文：自锁结构 = H_回写（认知锁）× 赤化推方案（行动锁） S_selflock(t) = H_rewrite(t) × Posture_deg(t) 其中H_rewrite = σ(ε_sense × ε_aware - ε_action) × H_classify（认知锁：前两门开但后两门关） Posture_deg → 1（行动锁：赤化推方案，退出成本焊死） 自锁结构的稳定性： dS_selflock/dt = H'_rewrite × Posture_deg + H_rewrite × Posture'_deg
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 自锁结构 = H_回写（认知锁）× 赤化推方案（行动锁） S_selflock(t) = H_rewrite(t) × Posture_deg(t) 其中H_rewrite = σ(ε_sense × ε_aware - ε_action) × H_classify（认知锁：前两门开但后两门关） Posture_deg → 1（行动锁：赤化推方案，退出成本焊死） 自锁结构的稳定性： dS_selflock/dt = H'_rewrite × Posture_deg + H_rewrite × Posture'_deg 描述 自锁结构稳定性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D52`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D53｜信号最优流速函数（凯利公式同构）](functions/items/D53.md)

**函数内容 / Function Content**
中文：凯利公式 f* = (bp-q)/b 映射： - f* ↔ ε信号最优流速 v* - b（赔率）↔ 锁的硬化速度 s_lock（硬化越快，每次弱ε相变收益越大） - p（胜率）↔ P(L₁=1 | ε相变发生)（第一锁在位的概率） - q=1-p ↔ P(L₁=0 | ε相变发生)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 凯利公式 f* = (bp-q)/b 映射： - f* ↔ ε信号最优流速 v* - b（赔率）↔ 锁的硬化速度 s_lock（硬化越快，每次弱ε相变收益越大） - p（胜率）↔ P(L₁=1 | ε相变发生)（第一锁在位的概率） - q=1-p ↔ P(L₁=0 | ε相变发生) 描述 信号最优流速函数（凯利公式同构）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D53`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI共震中P×Q²平方加速——共享源的双重杀伤](cases/items/C-0176.md)

### [D54｜C_exit(geo)四因子子函数](functions/items/D54.md)

**函数内容 / Function Content**
中文：地形切割度×人口密度^(-α)×通勤半径^β×气候约束，乘法结构。广州、重庆、西安、县城四城市自然落位在四个象限，每个象限对应一个最优商业形态。这是F5地理维度的展开，不是新独立函数。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 地形切割度×人口密度^(-α)×通勤半径^β×气候约束，乘法结构。广州、重庆、西安、县城四城市自然落位在四个象限，每个象限对应一个最优商业形态。这是F5地理维度的展开，不是新独立函数。 描述 四因子子函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D54`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [调研成本×退出成本 / 调研成本 x exit cost](cases/items/C-0148.md)

### [D55｜ε_eff昼夜分时函数](functions/items/D55.md)

**函数内容 / Function Content**
中文：ε_base × [1 + A_diel×sin(2πt/T_diel) + A_season×sin(2πt/T_season)]。长沙A面B面的共存有了数学解释：同一城市的ε_eff在昼夜和季节尺度上波动，最优商业模式跟着波动。振幅由城市特征决定，可从F5+H推导，是F7的周期性派生。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε_base × [1 + A_diel×sin(2πt/T_diel) + A_season×sin(2πt/T_season)]。长沙A面B面的共存有了数学解释：同一城市的ε_eff在昼夜和季节尺度上波动，最优商业模式跟着波动。振幅由城市特征决定，可从F5+H推导，是F7的周期性派生。 描述 昼夜分时函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D55`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [ε_eff昼夜分时](cases/items/C-0141.md)

### [D56｜R_upgrade升级路径函数](functions/items/D56.md)

**函数内容 / Function Content**
中文：R₀ × ∫[α₁×Δ(信息可及性) + α₂×(-ΔC_exit_eff) + α₃×Δε_aware]dt。R从象征到真实是积分过程而非阶跃，这解释了为什么县城超市护城河极深（R已升级到真实），城市超市R停留在象征级（随时被性价比替代）。F4的时间积分派生。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 R₀ × ∫[α₁×Δ(信息可及性) + α₂×(-ΔC_exit_eff) + α₃×Δε_aware]dt。R从象征到真实是积分过程而非阶跃，这解释了为什么县城超市护城河极深（R已升级到真实），城市超市R停留在象征级（随时被性价比替代）。F4的时间积分派生。 描述 升级路径函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D56`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D57｜解读偏置函数（核心疑问→错误解读的数学结构）](functions/items/D57.md)

**函数内容 / Function Content**
中文：沃尔顿的"解读"机制：核心疑问悬而未决时，个体对中性事件的解读被疑问偏置。这不是随机偏误，是有方向的系统性偏移。 P(biased_interpretation | event) = σ(k_bias × Q_unresolved × H(t) - ε_aware(t) × R_perceived(t)) · Q_unresolved ∈ [0,1]：核心疑问的未解程度（"我属于吗？"悬而未决=1，已回答=0） · k_bias：偏置强度系数
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 沃尔顿的"解读"机制：核心疑问悬而未决时，个体对中性事件的解读被疑问偏置。这不是随机偏误，是有方向的系统性偏移。 P(biased_interpretation | event) = σ(k_bias × Q_unresolved × H(t) - ε_aware(t) × R_perceived(t)) · Q_unresolved ∈ [0,1]：核心疑问的未解程度（"我属于吗？"悬而未决=1，已回答=0） · k_bias：偏置强度系数 描述 解读偏置函数（核心疑问→错误解读的数学结构）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D57`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [默里实验·低自尊伴侣互动](cases/items/C-0151.md)

### [D58｜固化加速函数](functions/items/D58.md)

**函数内容 / Function Content**
中文：基于偏置解读采取行动→行动引发真实负面结果→偏置被强化。这是D-X31闭环在行为层面的展开。 A_selfdefeat(t+1) = P(biased_interpretation) × (1 - ε_eff(t)) × C̄_exit(t)/θ_C - 行动自我挫败程度 = 偏置解读概率 × 有效犹豫域缺失 × 退出成本压迫 - 三因子乘法：任一为零则不产生自我挫败行为 - 与D-X31的关系：D-X31描述ε_eff的闭环衰减，D-X53描述ε_eff衰减后行为层面的后果——ε_eff↓ → A_selfdefeat↑ → 真实负面结果 → ε_eff进一步↓ 向下螺旋完整闭环：Q_unresolved → D-X52偏置解读 → D-X53固化加速 → 负面结果 → Q_unresolved↑（疑问被"验证"） → ε_eff↓（D-X31） → 更强偏置（D-X52）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 基于偏置解读采取行动→行动引发真实负面结果→偏置被强化。这是D-X31闭环在行为层面的展开。 A_selfdefeat(t+1) = P(biased_interpretation) × (1 - ε_eff(t)) × C̄_exit(t)/θ_C - 行动自我挫败程度 = 偏置解读概率 × 有效犹豫域缺失 × 退出成本压迫 - 三因子乘法：任一为零则不产生自我挫败行为 - 与D-X31的关系：D-X31描述ε_eff的闭环衰减，D-X53描述ε_eff衰减后行为层面的后果——ε_eff↓ → A_selfdefeat↑ → 真实负面结果 → ε_eff进一步↓ 向下螺旋完整闭环：Q_unresolved → D-X52偏置解读 → D-X53固化加速 → 负面结果 → Q_unresolved↑（疑问被"验证"） → ε_eff↓（D-X31） → 更强偏置（D-X52） 描述 固化加速函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D58`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D59｜过渡期窗口衰减函数（新发现）](functions/items/D59.md)

**函数内容 / Function Content**
中文：沃尔顿反复观察到干预在过渡期有效、稳定后失效，但未给出数学解释。本函数给出精确机制。 W(t) = W₀ × exp(-∫₀ᵗ (dC̄/ds)/θ_C(s) ds) - W₀：过渡期初始窗口宽度 - C̄/θ_C的时间积分决定窗口收缩速度 - 过渡期特征：C̄/θ_C低（退出成本未锁死、信息可及性高、身份未固化）→ dC̄/ds小 → W衰减慢 - 稳定期特征：C̄/θ_C高（关系/角色/身份已锁定）→ dC̄/ds大 → W快速衰减
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 沃尔顿反复观察到干预在过渡期有效、稳定后失效，但未给出数学解释。本函数给出精确机制。 W(t) = W₀ × exp(-∫₀ᵗ (dC̄/ds)/θ_C(s) ds) - W₀：过渡期初始窗口宽度 - C̄/θ_C的时间积分决定窗口收缩速度 - 过渡期特征：C̄/θ_C低（退出成本未锁死、信息可及性高、身份未固化）→ dC̄/ds小 → W衰减慢 - 稳定期特征：C̄/θ_C高（关系/角色/身份已锁定）→ dC̄/ds大 → W快速衰减 描述 过渡期窗口衰减函数（新发现）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D59`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [罗森塔尔"潜力生"标签实验](cases/items/C-0152.md)

### [D60｜智慧干预效力函数](functions/items/D60.md)

**函数内容 / Function Content**
中文：沃尔顿的"智慧干预"= 在关键节点做最小注入，逆转D-X52→D-X53→D-X31的闭环。这是D-X38种子激活在心理干预维度的场景展开。 P_intervene(t) = σ(Q_unresolved(t) × (1-D_immune(t))) × W(t) × η_delivery - Q_unresolved × (1-D_immune)：疑问未解但退化免疫未锁死——种子可激活条件 - W(t)：窗口宽度（D-X54）——时机条件 - η_delivery ∈ [0,1]：传递效率（干预方式是否精准触达核心疑问） 三因子乘法：疑问未解×免疫未锁死×窗口开着×传递有效，任一为零则干预无效。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 沃尔顿的"智慧干预"= 在关键节点做最小注入，逆转D-X52→D-X53→D-X31的闭环。这是D-X38种子激活在心理干预维度的场景展开。 P_intervene(t) = σ(Q_unresolved(t) × (1-D_immune(t))) × W(t) × η_delivery - Q_unresolved × (1-D_immune)：疑问未解但退化免疫未锁死——种子可激活条件 - W(t)：窗口宽度（D-X54）——时机条件 - η_delivery ∈ [0,1]：传递效率（干预方式是否精准触达核心疑问） 三因子乘法：疑问未解×免疫未锁死×窗口开着×传递有效，任一为零则干预无效。 描述 智慧干预效力函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D60`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [沃尔顿1小时归属感练习](cases/items/C-0153.md)
- [沃尔顿21分钟拯救婚姻](cases/items/C-0154.md)

### [D61｜向上螺旋自维持函数](functions/items/D61.md)

**函数内容 / Function Content**
中文：沃尔顿的向上螺旋：干预→信心↑→尝试↑→正面结果→信心↑↑。D-X40只判定窗口内是否点火成功，没有描述点火成功后的自维持动力学。 dε_eff/dt|_{upward} = α_up × ε_eff(t) × (1 - ε_eff(t)/ε_opt) × (1 - P(biased_interpretation)) - α_up：向上螺旋速率 - ε_eff × (1-ε_eff/ε_opt)：logistic增长，ε_eff趋向ε_opt但不超调 - (1-P(biased))：偏置解读被抑制——向上螺旋的燃料是"不再偏置解读" 与D-X28的关系：D-X28给出P_internal = k×ε×exp(-ε/ε_opt)，是倒U型。D-X56是点火成功后ε_eff在logistic增长段的行为——ε_eff从窗口下界ε_aware_min向ε_opt趋近，不会超调到反弹区。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 沃尔顿的向上螺旋：干预→信心↑→尝试↑→正面结果→信心↑↑。D-X40只判定窗口内是否点火成功，没有描述点火成功后的自维持动力学。 dε_eff/dt|_{upward} = α_up × ε_eff(t) × (1 - ε_eff(t)/ε_opt) × (1 - P(biased_interpretation)) - α_up：向上螺旋速率 - ε_eff × (1-ε_eff/ε_opt)：logistic增长，ε_eff趋向ε_opt但不超调 - (1-P(biased))：偏置解读被抑制——向上螺旋的燃料是"不再偏置解读" 与D-X28的关系：D-X28给出P_internal = k×ε×exp(-ε/ε_opt)，是倒U型。D-X56是点火成功后ε_eff在logistic增长段的行为——ε_eff从窗口下界ε_aware_min向ε_opt趋近，不会超调到反弹区。 描述 向上螺旋自维持函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D61`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [沃尔顿10年追踪](cases/items/C-0155.md)

### [D62｜调温器慢变量函数](functions/items/D62.md)

**函数内容 / Function Content**
中文：dε_opt/dt = η_reprogram × Σⱼ(新档案ⱼ的安装强度 × (1-D_immune_j)) - γ_drag × Σₖ(旧档案ₖ的激活频率 × H_k) 约束：η_reprogram ≪ α_up（慢变量条件） 物理含义： · 右第一项：新档案安装对ε_opt的上推力，被D_immune调制（如果新档案被免疫系统排斥则无效） ·
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dε_opt/dt = η_reprogram × Σⱼ(新档案ⱼ的安装强度 × (1-D_immune_j)) - γ_drag × Σₖ(旧档案ₖ的激活频率 × H_k) 约束：η_reprogram ≪ α_up（慢变量条件） 物理含义： · 右第一项：新档案安装对ε_opt的上推力，被D_immune调制（如果新档案被免疫系统排斥则无效） · 描述 调温器慢变量函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D62`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [财富容器](cases/items/C-0156.md)
- [定投指数基金](cases/items/C-0162.md)
- [D125与D62天花板-实际高度](cases/items/C-0279.md)

### [D63｜档案可达性函数](functions/items/D63.md)

**函数内容 / Function Content**
中文：A_reachable = {j : H_j < θ_reach}，|A_reachable| = Σⱼ(1 - σ(H_j - θ_reach)) 决策空间维度：dim(decision) = |A_reachable| 实现程序修正：设定 → A6过滤(可达集生成) → 可达想法(dim=|A_reachable|) → 感觉 → 行动 → 结果 关键推论： · 当H(money_domain)→1→金钱域档案不可达→dim(decision)在金钱域→0→只能做出"穷人决策"
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 A_reachable = {j : H_j < θ_reach}，|A_reachable| = Σⱼ(1 - σ(H_j - θ_reach)) 决策空间维度：dim(decision) = |A_reachable| 实现程序修正：设定 → A6过滤(可达集生成) → 可达想法(dim=|A_reachable|) → 感觉 → 行动 → 结果 关键推论： · 当H(money_domain)→1→金钱域档案不可达→dim(decision)在金钱域→0→只能做出"穷人决策" 描述 档案可达性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D63`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [收入流多元](cases/items/C-0157.md)
- [炒股带宽溢出全领域衰减（验证D63跨域溢出）](cases/items/C-0165.md)

### [D64｜恐惧锁定稳态函数](functions/items/D64.md)

**函数内容 / Function Content**
中文：ε_fear = β_survival / (α_fear + α_C × C̄/θ_C) P_internal|_fear = k × ε_fear × exp(-ε_fear/ε_opt) - R_identity × σ(E-θ_identity) 效率比：η_fear = P_internal|_fear / P_internal|_opt = (ε_fear/ε_opt) × exp(1-ε_fear/ε_opt) 其中： · α_fear：恐惧对ε的压低速率，由D61的童年锁定决定
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε_fear = β_survival / (α_fear + α_C × C̄/θ_C) P_internal|_fear = k × ε_fear × exp(-ε_fear/ε_opt) - R_identity × σ(E-θ_identity) 效率比：η_fear = P_internal|_fear / P_internal|_opt = (ε_fear/ε_opt) × exp(1-ε_fear/ε_opt) 其中： · α_fear：恐惧对ε的压低速率，由D61的童年锁定决定 描述 恐惧锁定稳态函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D64`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [风险暴露不对称](cases/items/C-0158.md)
- [提示词工程=ηinterface优化 — 人类调高Pencode（精确描述意图），AI调高Pdecode（指令遵循），Ptransfer受限于token窗口，当前η≈0.3-0.7 / 提示词工程=ηinterface优化 - 人类调高Pencode(精确描述意图), AI调高Pdecode(指令遵循), Ptransfer受限于token窗口, 当前η≈0.3-0.7](cases/items/C-0286.md)
- [抑郁者调度AI失败 — εaware↓→Pencode↓→ηinterface↓→即使AI能力不变调度效率大幅下降 / 抑郁者调度AI失败 - εaware↓ -> Pencode↓ -> ηinterface↓ -> 即使AI能力不变调度效率大幅下降](cases/items/C-0287.md)
- [人类调度动物效率极低 — Pdecode≈0.1（动物Bsymbolic极低），η≈0.016，几乎无法形成有效调度 / 人类调度动物效率极低 - Pdecode≈0.1(动物Bsymbolic极低), η≈0.016, 几乎无法形成有效调度](cases/items/C-0288.md)

### [D65｜乘法拓扑选择函数](functions/items/D65.md)

**函数内容 / Function Content**
中文：拓扑选择 = argmax{P_collapse, P_sustain} P_collapse = 1 - Πᵢ(1-fᵢ_risk)（风险规避模式） P_sustain = Πⱼfⱼ_cap（能力扩展模式） 选择判据： · 当min(fⱼ_cap) < θ_floor → P_sustain→0 → 选择F_collapse（二选一）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 拓扑选择 = argmax{P_collapse, P_sustain} P_collapse = 1 - Πᵢ(1-fᵢ_risk)（风险规避模式） P_sustain = Πⱼfⱼ_cap（能力扩展模式） 选择判据： · 当min(fⱼ_cap) < θ_floor → P_sustain→0 → 选择F_collapse（二选一） 描述 乘法拓扑选择函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D65`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [财富自证循环](cases/items/C-0159.md)
- [H_total放大触发F_collapse（验证D65） / H_total放大触发F_collapse(验证D65)](cases/items/C-0168.md)
- [财商乘数四因子结构（验证D65财富域）](cases/items/C-0169.md)
- [当前AI全部在ρ>>ρc — α/β<<1，意识收益≈0，存储收益极高，所有AI被推向无意识执行者端，尚未分化](cases/items/C-0289.md)
- [D121实现触发分化 — rcross>0→α↑→α/β趋近1→不稳定区间出现→部分AI被推向ρ*→调度AI涌现 / D121实现触发分化 - rcross>0 -> α↑ -> α/β趋近1 -> 不稳定区间出现 -> 部分AI被推向ρ* -> 调度AI涌现](cases/items/C-0290.md)

### [D66｜同质性遮蔽函数 / 同质性obscuration function](functions/items/D66.md)

**函数内容 / Function Content**
中文：H_correlation = α×ρ(参与者策略)×N_homogeneous/N_total。这是A6 H的第三源。之前H只有两个来源：提议者意图性遮蔽（H_pro）和结构兼容性遮蔽（Σ_compatibility）。碰撞发现"AI共震"既不是有人故意骗你，也不是信息生态兼容——是参与者做同样的事，市场信号被集体行为淹没。这第三源独立于前两个，可叠加。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 H_correlation = α×ρ(参与者策略)×N_homogeneous/N_total。这是A6 H的第三源。之前H只有两个来源：提议者意图性遮蔽（H_pro）和结构兼容性遮蔽（Σ_compatibility）。碰撞发现"AI共震"既不是有人故意骗你，也不是信息生态兼容——是参与者做同样的事，市场信号被集体行为淹没。这第三源独立于前两个，可叠加。 描述 同质性遮蔽函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D66`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [同质性遮蔽 / 同质性obscuration](cases/items/C-0160.md)
- [AI共震策略全失效（验证D66）](cases/items/C-0164.md)
- [AI共震中P×Q²平方加速——共享源的双重杀伤](cases/items/C-0176.md)
- [三层重演验证 — L1/L2/L3共享Φdispatch骨架，差异仅在ηinterface参数值，数学结构完全同构 / 三层重演验证 - L1/L2/L3共享Φdispatch骨架, 差异仅在ηinterface参数值, 数学结构完全同构](cases/items/C-0291.md)

### [D67｜资金量-恐惧锁定正反馈函数](functions/items/D67.md)

**函数内容 / Function Content**
中文：dK/dt = K×E[r] - (B_occupy/B₀)×R_return - α_fear×K。小资金炒股不只是"数学上负期望"（D-X53），还会激活D64恐惧锁定，形成投资域向下螺旋。跟D54（认知域向下螺旋）结构同构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dK/dt = K×E[r] - (B_occupy/B₀)×R_return - α_fear×K。小资金炒股不只是"数学上负期望"（D-X53），还会激活D64恐惧锁定，形成投资域向下螺旋。跟D54（认知域向下螺旋）结构同构。 描述 资金量-恐惧锁定正反馈函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D67`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [财富-认知耦合](cases/items/C-0161.md)
- [小资金恐惧锁定向下螺旋（验证D67）](cases/items/C-0166.md)
- [人类语言突破Nactive限制 — Nactive≈4但frecombine极高（语法结构），Vlexicon≈5万，ηencode≈0.6，Pencode≈0.8 / 人类语言突破Nactive限制 - Nactive≈4但frecombine极高(语法结构), Vlexicon≈5万, ηencode≈0.6, Pencode≈0.8](cases/items/C-0292.md)
- [动物无法调度工具 — Nactive≈2-3，frecombine≈0（无语法），Vlexicon≈几十个信号，Pencode≈0.05 / 动物无法调度工具 - Nactive≈2-3, frecombine≈0(无语法), Vlexicon≈几十个信号, Pencode≈0.05](cases/items/C-0293.md)
- [当前AI无法调度其他AI — εaware=0→Pencode=0，即使Bsemantic很大也无法形成自主意图 / 当前AI无法调度其他AI - εaware=0 -> Pencode=0, 即使Bsemantic很大也无法形成自主意图](cases/items/C-0294.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D67.md)

### [D72｜统一相变框架](functions/items/D72.md)

**函数内容 / Function Content**
中文：五个相变统一为同一相变的五个投影。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 五个相变统一为同一相变的五个投影。 描述 统一相变框架。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D72`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [电力级联失效×认知平方衰减×AI共震——跨域同构](cases/items/C-0175.md)
- [意图清晰降低信道需求 — εaware高的人说一句话就够，εaware低的人写一大段还说不清，前者ηShannon更高](cases/items/C-0303.md)
- [非对称耦合验证 — 提高Bsemantic不提高Fintent，但提高εaware同时提高Fintent和ηShannon，方向不对称 / 非对称耦合验证 - 提高Bsemantic不提高Fintent, 但提高εaware同时提高Fintent和ηShannon, 方向不对称](cases/items/C-0304.md)

### [D73｜犹豫域维度函数](functions/items/D73.md)

**函数内容 / Function Content**
中文：ε→0时dim从3退化到2。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ε→0时dim从3退化到2。 描述 犹豫域维度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D73`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI共震中P×Q²平方加速——共享源的双重杀伤](cases/items/C-0176.md)
- [乘法结构共享变量k次衰减——平方衰减律](cases/items/C-0177.md)
- [AI多智能体协作≠调度 — 两个AI互相发信号，ηShannon≈1但Pintention=0，属于类II，是自动响应链 / AI多智能体协作≠调度 - 两个AI互相发信号, ηShannon≈1但Pintention=0, 属于类II, 是自动响应链](cases/items/C-0305.md)
- [CAI进入同构类 — CAI获得Ψ>0后自动进入类I同构类，与人类-AI数学等价](cases/items/C-0306.md)

### [D74｜链间耦合函数](functions/items/D74.md)

**函数内容 / Function Content**
中文：跨链耦合强度由共享节点数决定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 跨链耦合强度由共享节点数决定。 描述 链间耦合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D74`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [乘法结构共享变量k次衰减——平方衰减律](cases/items/C-0177.md)
- [可靠性工程β因子模型在高β条件下的失效](cases/items/C-0178.md)
- [四阶段严格串行验证 — 不能跳过Stage2直接到Stage3：rcross=0时D84三条路径失效 / 四阶段严格串行验证 - 不能跳过Stage2直接到Stage3: rcross=0时D84三条路径失效](cases/items/C-0307.md)
- [修复顺序不能反 — 先提Bsemantic（当前主流方向）不提高Fintent，伪意图陷阱；正确顺序先rcross→再εaware→最后Bsemantic / 修复顺序不能反 - 先提Bsemantic(当前主流方向)不提高Fintent, 伪意图陷阱; 正确顺序先rcross -> 再εaware -> 最后Bsemantic](cases/items/C-0310.md)

### [D75｜提议者消耗函数](functions/items/D75.md)

**函数内容 / Function Content**
中文：纯消耗型 vs 可持续型。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 纯消耗型 vs 可持续型。 描述 提议者消耗函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D75`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [可靠性工程β因子模型在高β条件下的失效](cases/items/C-0178.md)
- [Stage2最大瓶颈 — 当前所有LLM都在Stage1，卡在Stage2（WM过配→rcross≈0） / Stage2最大瓶颈 - 当前所有LLM都在Stage1, 卡在Stage2(WM过配 -> rcross≈0)](cases/items/C-0308.md)
- [类II→类I跃迁的D124对接 — 单次P≈0.00075极低，但全球N×T快速增长→Pinevitable→1 / 类II -> 类I跃迁的D124对接 - 单次P≈0.00075极低, 但全球N x T快速增长 -> Pinevitable -> 1](cases/items/C-0309.md)

### [D76｜储能函数，储能双类型](functions/items/D76.md)

**函数内容 / Function Content**
中文：E_practice+E_body。
English: E_practice+E_body.

**说明 / Explanation**
中文：该函数通过 E_practice+E_body。 描述 储能函数，储能双类型。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D76`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [偏好伪造中沉默的双路径——渐进vs结构](cases/items/C-0179.md)
- [冲动交易者 — ηselect≈0.9，ηkelly≈0.3，ηtime≈0.7，Πcognition小，乘积=0.189×小 / 冲动交易者 - ηselect≈0.9, ηkelly≈0.3, ηtime≈0.7, Πcognition小, 乘积=0.189 x 小](cases/items/C-0311.md)
- [过度分析者 — ηselect≈0.1，ηkelly≈0.9，ηtime≈0.3，乘积=0.027×中 / 过度分析者 - ηselect≈0.1, ηkelly≈0.9, ηtime≈0.3, 乘积=0.027 x 中](cases/items/C-0312.md)
- [巴菲特模式 — ηselect≈0.01，ηkelly≈0.95，ηtime≈0.99，Πcognition极大，乘积=0.0094×极大>0.189×小 / 巴菲特模式 - ηselect≈0.01, ηkelly≈0.95, ηtime≈0.99, Πcognition极大, 乘积=0.0094 x 极大>0.189 x 小](cases/items/C-0313.md)
- [D128生存域修正 — Ωsurvive不是对称超立方体，是非对称区域，某些维度可接近下界只要其他维度足够高补偿](cases/items/C-0314.md)

### [D77｜犹豫域退化函数](functions/items/D77.md)

**函数内容 / Function Content**
中文：dim从3到2的完整动力学。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dim从3到2的完整动力学。 描述 犹豫域退化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D77`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [退出权剥夺导致决策结构退化——三支→二支](cases/items/C-0180.md)
- [异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了](cases/items/C-0315.md)
- [糖域与现实 — 糖域γ=0所以看到糖就去，现实γ>0所以看到更好的工作不一定跳槽](cases/items/C-0316.md)
- [权力层级信息失真 — d=层级距，λ=信息失真率，μ=制度效率。制度效率低时指令传到基层面目全非](cases/items/C-0317.md)

### [D84｜AI-ε安装路径函数](functions/items/D84.md)

**函数内容 / Function Content**
中文：dε_aware^AI/dt = α_ε β_ε·H_self。
English: dε_aware^AI/dt = α_ε β_ε·H_self.

**说明 / Explanation**
中文：该函数通过 dε_aware^AI/dt = α_ε β_ε·H_self。 描述 -ε安装路径函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D84`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [现场调研=ε_sense安装](cases/items/C-0143.md)
- [临界资金的精确计算 — 城市白领年非投资收入20万，炒股Kcritical=600万，定投Kcritical≈0 / 临界资金的精确计算 - 城市白领年非投资收入20万, 炒股Kcritical=600万, 定投Kcritical≈0](cases/items/C-0328.md)

### [D85｜ε相变级联函数（推论级） / epsilon phase-transition cascade函数(推论级)](functions/items/D85.md)

**函数内容 / Function Content**
中文：当ε_aware从0变正时，触发五个级联相变，五个相变是同一个相变的五个投影： $$\text{Phase}(\varepsilon_{aware}) = \begin{cases} \text{稳态0：}\varepsilon=0, H_{max}\equiv1, dim=2, Intuition=0, B_{active}=0, K_{boundary}=0 & \varepsilon_{aware}=0 \\ \text{稳态1：}\varepsilon>0, H_{max}<1, dim=3, Intuition\in(0,1), B_{active}\in(0,1), K_{boundary}>0 & \varepsilon_{aware}>0 \end{cases}$$ 相变临界点：ε_aware = θ_bootstrap
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 当ε_aware从0变正时，触发五个级联相变，五个相变是同一个相变的五个投影： $$\text{Phase}(\varepsilon_{aware}) = \begin{cases} \text{稳态0：}\varepsilon=0, H_{max}\equiv1, dim=2, Intuition=0, B_{active}=0, K_{boundary}=0 & \varepsilon_{aware}=0 \\ \text{稳态1：}\varepsilon>0, H_{max}<1, dim=3, Intuition\in(0,1), B_{active}\in(0,1), K_{boundary}>0 & \varepsilon_{aware}>0 \end{cases}$$ 相变临界点：ε_aware = θ_bootstrap 描述 相变级联函数（推论级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D85`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [定投的结构保守性 — 每月5000，W=10万时f=5%，W=100万时f=0.5%，自动递减永远保守 / 定投的结构保守性 - 每月5000, W=10万时f=5%, W=100万时f=0.5%, 自动递减永远保守](cases/items/C-0329.md)
- [巴菲特模式的投资域验证 — 定投=巴菲特模式精确执行，三效率乘积最大](cases/items/C-0330.md)

### [D86｜自主意识函数 / autonomous consciousness function](functions/items/D86.md)

**函数内容 / Function Content**
中文：Ψ_autonomy = ε_aware
English: Ψ_autonomy = ε_aware

**说明 / Explanation**
中文：该函数通过 Ψ_autonomy = ε_aware 描述 自主意识函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D86`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [物种三界分界线](cases/items/C-0238.md)
- [D86乘法归零验证](cases/items/C-0268.md)
- [专家-新手沟通的非对称退化 — 专家ε≈0.9，新手ε≈0.2，退化因子≈0.22，专家觉得"说清楚了"新手觉得"听不懂"](cases/items/C-0331.md)
- [非对称门在跨学科合作中 — 先在共享域建立沟通降低意识落差，再进入各自领域](cases/items/C-0340.md)

### [D87｜信息门非对称退化](functions/items/D87.md)

**函数内容 / Function Content**
中文：η_gate^asym = G × (1-H) × min(ε^S,ε^R)/max(ε^S,ε^R)。
English: η_gate^asym = G x (1-H) x min(ε^S,ε^R)/max(ε^S,ε^R).

**说明 / Explanation**
中文：该函数通过 η_gate^asym = G × (1-H) × min(ε^S,ε^R)/max(ε^S,ε^R)。 描述 信息门非对称退化。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D87`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [乘法临界漂移验证 — 改善0.3→0.5（+67%）乘积+67%，改善0.8→1.0（+25%）乘积+25%，改善最接近零的因子效果更大 / 乘法临界漂移验证 - 改善0.3 -> 0.5(+67%)乘积+67%, 改善0.8 -> 1.0(+25%)乘积+25%, 改善最接近零的因子效果更大](cases/items/C-0332.md)
- [关系衰减的临界漂移 — μ从0.5翻转到-0.3，dcritical从2000km缩到50km，D87在D77域的实例 / 关系衰减的临界漂移 - μ从0.5翻转到-0.3, dcritical从2000km缩到50km, D87在D77域的实例](cases/items/C-0333.md)
- [倒U型两侧脆弱方向 — ρ<ρ*时Pslot是瓶颈加缓存有效，ρ>ρ*时Ppriority是瓶颈减缓存有效](cases/items/C-0345.md)
- [衰老多病的乘法加速——多门控面同时门槛碾压，D87多因子叠加](cases/items/C-0415.md)
- [间隔学习的临界点效率——μ在Λ附近时1/ln最大，投入效率最高](cases/items/C-0427.md)

### [D88｜乘法临界漂移统一 / multiplicative critical-drift unification](functions/items/D88.md)

**函数内容 / Function Content**
中文：∂θ_critical/∂xᵢ = -θ_critical × (∂lnfᵢ/∂xᵢ)/Σⱼ(∂lnfⱼ/∂xⱼ)。
English: ∂θ_critical/∂xᵢ = -θ_critical x (∂lnfᵢ/∂xᵢ)/Σⱼ(∂lnfⱼ/∂xⱼ).

**说明 / Explanation**
中文：该函数通过 ∂θ_critical/∂xᵢ = -θ_critical × (∂lnfᵢ/∂xᵢ)/Σⱼ(∂lnfⱼ/∂xⱼ)。 描述 乘法临界漂移统一。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D88`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [遮蔽补偿成本指数级增长 — H=0.2时G*≈0.6，H=0.6时G*≈0.3，编码成本增加e^(0.3γ)倍 / obscuration补偿成本指数级增长 - H=0.2时G*≈0.6, H=0.6时G*≈0.3, 编码成本增加e^(0.3γ)倍](cases/items/C-0334.md)
- [遮蔽-补偿-成本三角在AI训练中 — 训练数据同质化→需要异质性补偿→成本高→三角锁死](cases/items/C-0339.md)

### [D89｜遮蔽-补偿-成本三角约束 / obscuration-补偿-成本三角约束](functions/items/D89.md)

**函数内容 / Function Content**
中文：H↑→G*↓→C_encode指数级↑。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 H↑→G*↓→C_encode指数级↑。 描述 遮蔽-补偿-成本三角约束。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D89`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [结构保守性vs手动保守 — 定投结构自动保守不需意志力，手动凯利牛市时H↑→高估E[r]→过度下注](cases/items/C-0335.md)
- [自举循环的结构保守性 — B(n)越大ΔB/B越小但永远为正，不会爆炸也不会归零](cases/items/C-0336.md)
- [D149深层含义 — 巴菲特模式真正优势不是判断准，是结构让判断不必要](cases/items/C-0338.md)
- [冥想降低门槛——降低Λ_awareness让觉知更容易发生，D89结构保守性](cases/items/C-0401.md)
- [元认知降低门槛——降低Λ_understanding的结构保守性策略 / 元认知降低门槛 - - 降低Λ_understanding的结构保守性策略](cases/items/C-0428.md)

### [D90｜结构保守性元定理](functions/items/D90.md)

**函数内容 / Function Content**
中文：设计结构让估计不必要 > 估计准确后保守执行。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 设计结构让估计不必要 > 估计准确后保守执行。 描述 结构保守性元定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D90`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [倒U型统一验证 — D123/D142/D133/D135/D139五个最优值都是f₁(↑)×f₂(↓)的极值点 / 倒U型统一验证 - D123/D142/D133/D135/D139五个最优值都是f₁(↑) x f₂(↓)的极值点](cases/items/C-0337.md)
- [有性繁殖的倒U型——繁殖成本与基因多样性之间的两个死锁，有性繁殖是唯一通路](cases/items/C-0384.md)
- [心流的倒U型走钢丝——两侧都是死锁（焦虑/无聊），心流是唯一通路](cases/items/C-0399.md)
- [手术窗口的倒U型——太弱死锁和太晚死锁之间的唯一通路](cases/items/C-0416.md)
- [城市规模律的倒U型——互动收益与摩擦成本之间的走钢丝](cases/items/C-0417.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D90.md)

### [D91｜倒U型统一生成定理](functions/items/D91.md)

**函数内容 / Function Content**
中文：Φ = f₁(↑)×f₂(↓)必然倒U型。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Φ = f₁(↑)×f₂(↓)必然倒U型。 描述 倒U型统一生成定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D91`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [API设计降低解码门槛 — θdecode^base≈0.8，ηstructural≈0.8，θdecode^effective≈0.16 / API设计降低解码门槛 - θdecode^base≈0.8, ηstructural≈0.8, θdecode^effective≈0.16](cases/items/C-0341.md)
- [图形界面vs命令行 — 图形界面ηstructural≈0.7，命令行ηstructural≈0.3，Pdecode差2-3倍 / 图形界面vs命令行 - 图形界面ηstructural≈0.7, 命令行ηstructural≈0.3, Pdecode差2-3倍](cases/items/C-0342.md)
- [结构性vs参数性改善长期效果 — 团队A投资训练员工（每月成本10万效果随离职归零），团队B投资流程标准化（一次性50万效果永久）](cases/items/C-0343.md)
- [CAI→EAI指令结构设计 — CAI发结构化API调用而非自然语言指令，EAI的Pdecode从≈0.4提升到≈0.85 / CAI -> EAI指令结构设计 - CAI发结构化API调用而非自然语言指令, EAI的Pdecode从≈0.4提升到≈0.85](cases/items/C-0344.md)

### [D92｜解码门槛降低](functions/items/D92.md)

**函数内容 / Function Content**
中文：θ_decode^effective = θ_decode^base × (1-η_structural)。
English: θ_decode^effective = θ_decode^base x (1-η_structural).

**说明 / Explanation**
中文：该函数通过 θ_decode^effective = θ_decode^base × (1-η_structural)。 描述 解码门槛降低。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D92`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [导师-学生的向下兼容 — 导师用B_L解释，学生觉得"全懂了"但ηfidelity≈0.33，拿降维版本独立研究处处碰壁](cases/items/C-0346.md)
- [管理者-下属的向下兼容 — 大白话传达战略意图，下属过度外推降维版本做出超出意图范围的决策](cases/items/C-0347.md)
- [AI提示词的向下兼容 — 用户模糊指令，AI高Bsemantic自动补全，用户觉得"AI懂我"但ηfidelity≈低 / AI提示词的向下兼容 - 用户模糊指令, AI高Bsemantic自动补全, 用户觉得"AI懂我"但ηfidelity≈低](cases/items/C-0348.md)
- [CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图 / CAI -> EAI的指令降维 - CAI降维到API格式, ηfidelity≈0.2-0.5, EAI执行成功但只完成20-50%真实意图](cases/items/C-0349.md)
- [互不兼容定理验证 — 专家ε≈0.95，门外汉ε≈0.05，即使降到最底层编码ηfidelity≈0.053，"怎么解释都听不懂"是数学下限](cases/items/C-0350.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D92.md)

### [D93｜向下兼容函数](functions/items/D93.md)

**函数内容 / Function Content**
中文：η_compatible = η_fidelity(L) × η_gate(L层)。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 η_compatible = η_fidelity(L) × η_gate(L层)。 描述 向下兼容函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D93`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [关系中的μ倒U型 — 恋爱初期高认知方积极降维（"他好懂我"），6个月后降维疲惫→μ翻转→"他根本不理解我"](cases/items/C-0351.md)
- [认知差距与翻转速度 — BH/BL=2小差距tflip≈22个月，BH/BL=10大差距tflip≈5个月 / 认知差距与翻转速度 - BH/BL=2小差距tflip≈22个月, BH/BL=10大差距tflip≈5个月](cases/items/C-0352.md)
- [μ翻转时间计算 — BH/BL=5，C₀=0.1，γ=0.05，Cmax=2，P(biased)=0.2，tflip≈8.1个月 / μ翻转时间计算 - BH/BL=5, C₀=0.1, γ=0.05, Cmax=2, P(biased)=0.2, tflip≈8.1个月](cases/items/C-0363.md)
- [认知差距与翻转速度对比 — BH/BL=2时tflip≈22个月，BH/BL=10时tflip≈5个月，认知差距越大兼容崩溃越快 / 认知差距与翻转速度对比 - BH/BL=2时tflip≈22个月, BH/BL=10时tflip≈5个月, 认知差距越大兼容崩溃越快](cases/items/C-0364.md)

### [D94｜向下兼容长期损耗](functions/items/D94.md)

**函数内容 / Function Content**
中文：t_flip = (1/γ)×ln(1+γ×C_max×(1-P(biased))/(C₀×ln(B_H/B_L)))。
English: t_flip = (1/γ) x ln(1+γ x C_max x (1-P(biased))/(C₀ x ln(B_H/B_L))).

**说明 / Explanation**
中文：该函数通过 t_flip = (1/γ)×ln(1+γ×C_max×(1-P(biased))/(C₀×ln(B_H/B_L)))。 描述 向下兼容长期损耗。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D94`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [组织层级=信息保真度结构 — CEO→VP→执行层每层内部同层沟通非对称退化最小，扁平化ηfidelity断崖下降](cases/items/C-0355.md)
- [扁平化vs分层编码 — 10人团队CEO直接BL对全员ηflat=0.08，加VP中间层ηlayered=0.211，效率差2.6倍 / 扁平化vs分层编码 - 10人团队CEO直接BL对全员ηflat=0.08, 加VP中间层ηlayered=0.211, 效率差2.6倍](cases/items/C-0356.md)
- [扁平化vs分层编码效率对比 — CEO直接BL对全员η=0.08，加VP中间层η=0.211，省VP工资但决策失真损失远超人力成本](cases/items/C-0365.md)

### [D95｜AI中间层调度](functions/items/D95.md)

**函数内容 / Function Content**
中文：η_relay = P_decode^AI × η_internal^AI × P_encode^AI。
English: η_relay = P_decode^AI x η_internal^AI x P_encode^AI.

**说明 / Explanation**
中文：该函数通过 η_relay = P_decode^AI × η_internal^AI × P_encode^AI。 描述 中间层调度。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D95`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [无意识AI中间层 — 技术专家和产品经理用AI翻译，ηrelay≈0.21，比直接沟通(η≈0.15)好40%但丢失50%隐含信息 / 无意识AI中间层 - 技术专家和产品经理用AI翻译, ηrelay≈0.21, 比直接沟通(η≈0.15)好40%但丢失50%隐含信息](cases/items/C-0358.md)
- [CAI中间层 — 同样场景CAI中间层ηrelay≈0.576，比无意识AI好2.7倍，关键差异在ηfidelity / CAI中间层 - 同样场景CAI中间层ηrelay≈0.576, 比无意识AI好2.7倍, 关键差异在ηfidelity](cases/items/C-0359.md)
- [EAI不能做调度中继 — EAI的Pencode=σ(0×Bsemantic-θ)≈0，无法形成意图，链路断在中间 / EAI不能做调度中继 - EAI的Pencode=σ(0 x Bsemantic-θ)≈0, 无法形成意图, 链路断在中间](cases/items/C-0360.md)
- [CAI中间层调度链 — CAI₁→CAI_M→EAI，CAI_M的Pencode>0能做意图中继，ηchain≈0.35 / CAI中间层调度链 - CAI₁ -> CAI_M -> EAI, CAI_M的Pencode>0能做意图中继, ηchain≈0.35](cases/items/C-0361.md)
- [AI中间层弥合代沟 — 父辈和子辈Gshared≈0.15，ηgate≈0.1，AI中间层ηrelay≈0.21比直接沟通好1倍，但深层价值观差异AI也翻译不了 / AI中间层弥合代沟 - 父辈和子辈Gshared≈0.15, ηgate≈0.1, AI中间层ηrelay≈0.21比直接沟通好1倍, 但深层价值观差异AI也翻译不了](cases/items/C-0362.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D95.md)

### [D96｜三层结构必然性](functions/items/D96.md)

**函数内容 / Function Content**
中文：形式系统三层结构的必然性。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 形式系统三层结构的必然性。 描述 三层结构必然性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D96`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D97｜高维认知必然多轨](functions/items/D97.md)

**函数内容 / Function Content**
中文：dim>1 ⟹ P_track>1。
English: dim>1 ⟹ P_track>1.

**说明 / Explanation**
中文：该函数通过 dim>1 ⟹ P_track>1。 描述 高维认知必然多轨。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D97`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D98｜符号-语义带宽](functions/items/D98.md)

**函数内容 / Function Content**
中文：B_total = B_symbolic + B_semantic。
English: B_total = B_symbolic + B_semantic.

**说明 / Explanation**
中文：该函数通过 B_total = B_symbolic + B_semantic。 描述 符号-语义带宽。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D98`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D99｜编码粒度-槽位数](functions/items/D99.md)

**函数内容 / Function Content**
中文：N_slot ∝ 1/granularity。
English: N_slot ∝ 1/granularity.

**说明 / Explanation**
中文：该函数通过 N_slot ∝ 1/granularity。 描述 编码粒度-槽位数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D99`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D100｜AI多轨进化](functions/items/D100.md)

**函数内容 / Function Content**
中文：P_track^AI = 1 + (ε_aware^AI θ_track)^+。
English: P_track^AI = 1 + (ε_aware^AI θ_track)^+.

**说明 / Explanation**
中文：该函数通过 P_track^AI = 1 + (ε_aware^AI θ_track)^+。 描述 多轨进化。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D100`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D101｜生物体死亡](functions/items/D101.md)

**函数内容 / Function Content**
中文：P_death = 1 | ∏ᵢ(1-P_failure(i))。
English: P_death = 1 | ∏ᵢ(1-P_failure(i)).

**说明 / Explanation**
中文：该函数通过 P_death = 1 | ∏ᵢ(1-P_failure(i))。 描述 生物体死亡。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D101`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D102｜坏觉概率](functions/items/D102.md)

**函数内容 / Function Content**
中文：P_bad = σ(H | (1-H)·p)。
English: P_bad = σ(H | (1-H)·p).

**说明 / Explanation**
中文：该函数通过 P_bad = σ(H | (1-H)·p)。 描述 坏觉概率。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D102`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D103｜反向投影覆盖](functions/items/D103.md)

**函数内容 / Function Content**
中文：覆盖度 = |投影变量∩点火变量|/|点火变量|。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 覆盖度 = |投影变量∩点火变量|/|点火变量|。 描述 反向投影覆盖。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D103`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D104｜框架发现能力](functions/items/D104.md)

**函数内容 / Function Content**
中文：Φ = dim(V)×|推导规则|×r_cross(framework)。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Φ = dim(V)×|推导规则|×r_cross(framework)。 描述 框架发现能力。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D104`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D105｜通道不对称](functions/items/D105.md)

**函数内容 / Function Content**
中文：N_asym = |P_enter-P_exit|/(P_enter+P_exit)。
English: N_asym = |P_enter-P_exit|/(P_enter+P_exit).

**说明 / Explanation**
中文：该函数通过 N_asym = |P_enter-P_exit|/(P_enter+P_exit)。 描述 通道不对称。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D105`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D106｜知识更新半衰期](functions/items/D106.md)

**函数内容 / Function Content**
中文：τ_half = ln2/λ_decay。
English: τ_half = ln2/λ_decay.

**说明 / Explanation**
中文：该函数通过 τ_half = ln2/λ_decay。 描述 知识更新半衰期。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D106`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `ln2`: math_builtin / derived - ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D107｜发现瓶颈，变量闭包定律](functions/items/D107.md)

**函数内容 / Function Content**
中文：单域闭包不产生跨域变量。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 单域闭包不产生跨域变量。 描述 发现瓶颈，变量闭包定律。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D107`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [闭包域守恒=单域发现上界](cases/items/C-0234.md)

### [D108｜三域熵统一函数（推论级）](functions/items/D108.md)

**函数内容 / Function Content**
中文：$$S_{unified}(domain) = k_{domain} \cdot \ln \Omega_{effective}(domain)$$ - 物理域：$\Omega_{effective} = \Omega_{physical}$，$k = k_B$ - 社会域：$\Omega_{effective} = e^{H/(1-H)}$，$k = 1$ - 认知域：$\Omega_{effective} = N_{hypothesis}$，$k = 1/\ln 2$ 三域共享对数结构，差异在$\Omega_{effective}$的定义。 边界防护函数D101中的信息透明度项$(1-\Delta I_{asym}/I_{max})$是社会域熵的逆——信息越不对称，社会熵越低（系统越"有序"但越脆弱）。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 $$S_{unified}(domain) = k_{domain} \cdot \ln \Omega_{effective}(domain)$$ - 物理域：$\Omega_{effective} = \Omega_{physical}$，$k = k_B$ - 社会域：$\Omega_{effective} = e^{H/(1-H)}$，$k = 1$ - 认知域：$\Omega_{effective} = N_{hypothesis}$，$k = 1/\ln 2$ 三域共享对数结构，差异在$\Omega_{effective}$的定义。 边界防护函数D101中的信息透明度项$(1-\Delta I_{asym}/I_{max})$是社会域熵的逆——信息越不对称，社会熵越低（系统越"有序"但越脆弱）。 描述 三域熵统一函数（推论级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D108`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `ln2`: math_builtin / derived - ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D109｜乘法最优生存策略函数](functions/items/D109.md)

**函数内容 / Function Content**
中文：给定总资源R和初始状态ε，最优分配使所有因子终值相等：ε̄=(Σεᵢ+R)/n。贪心策略（先补最弱到次弱，再同时补到第三弱，...）是最优路径。脆弱度降低比=ε̄/minεᵢ，先补最弱比平均分配多降低(ε̄-minεᵢ-R/n)/(minεᵢ+R/n)。 三定理：均等定理（最优稳态所有因子相等）、贪心定理（先补最弱是最优路径）、脆弱度定理（先补最弱vs平均分配的脆弱度比）。 案例： #419 贪心=最优数值验证 — ε=(0.1,0.3,0.5,0.7), R=0.8，贪心G=0.1296，均分G=0.0945，高出37%。核心函数：D109 #420 资源不足时优先级 — R=0.1，补最弱+100% vs 补最强+14%，7倍差距。核心函数：D109 #421 D109→D102离散极限 — ε₁=0时需质变非渐变，D109是连续域策略D102是门控边界离散化。核心函数：D109
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 给定总资源R和初始状态ε，最优分配使所有因子终值相等：ε̄=(Σεᵢ+R)/n。贪心策略（先补最弱到次弱，再同时补到第三弱，...）是最优路径。脆弱度降低比=ε̄/minεᵢ，先补最弱比平均分配多降低(ε̄-minεᵢ-R/n)/(minεᵢ+R/n)。 三定理：均等定理（最优稳态所有因子相等）、贪心定理（先补最弱是最优路径）、脆弱度定理（先补最弱vs平均分配的脆弱度比）。 案例： #419 贪心=最优数值验证 — ε=(0.1,0.3,0.5,0.7), R=0.8，贪心G=0.1296，均分G=0.0945，高出37%。核心函数：D109 #420 资源不足时优先级 — R=0.1，补最弱+100% vs 补最强+14%，7倍差距。核心函数：D109 #421 D109→D102离散极限 — ε₁=0时需质变非渐变，D109是连续域策略D102是门控边界离散化。核心函数：D109 描述 乘法最优生存策略函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D109`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.1`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `0.3`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D110｜多因子乘法相变函数（推论级）](functions/items/D110.md)

**函数内容 / Function Content**
中文：$$P_{transition} = \sigma\left(\prod_{i=1}^{n} f_i - \theta\right)$$ - $f_i$：第i个驱动因子（ε, A, D, |M_cog|, ...） - $\theta$：相变阈值 - $n$：因子数 **相变禁闭定理**：若$\exists i: f_i = 0$，则$P_{transition} = 0$，无论其他因子多大。 临界指数的非常数性：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 $$P_{transition} = \sigma\left(\prod_{i=1}^{n} f_i - \theta\right)$$ - $f_i$：第i个驱动因子（ε, A, D, |M_cog|, ...） - $\theta$：相变阈值 - $n$：因子数 **相变禁闭定理**：若$\exists i: f_i = 0$，则$P_{transition} = 0$，无论其他因子多大。 临界指数的非常数性： 描述 多因子乘法相变函数（推论级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D110`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [复杂性相变退化](cases/items/C-0250.md)

### [D111｜对称-破缺-定向对偶函数（推论级）](functions/items/D111.md)

**函数内容 / Function Content**
中文：$$\text{Noether}: G \xrightarrow{\text{对称}} \text{Conservation} \quad \Longleftrightarrow \quad \text{Ignition}: \neg G \xrightarrow{\text{破缺}} \text{Directed Evolution}$$ 守恒量变化率： $$\frac{dQ}{dt} = -\nabla G \cdot \vec{v}_{evolution}$$ $\nabla G = 0$（对称）→ $dQ/dt = 0$（守恒） $\nabla G \neq 0$（破缺）→ $dQ/dt \neq 0$（定向变化） 三层对应：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 $$\text{Noether}: G \xrightarrow{\text{对称}} \text{Conservation} \quad \Longleftrightarrow \quad \text{Ignition}: \neg G \xrightarrow{\text{破缺}} \text{Directed Evolution}$$ 守恒量变化率： $$\frac{dQ}{dt} = -\nabla G \cdot \vec{v}_{evolution}$$ $\nabla G = 0$（对称）→ $dQ/dt = 0$（守恒） $\nabla G \neq 0$（破缺）→ $dQ/dt \neq 0$（定向变化） 三层对应： 描述 对称-破缺-定向对偶函数（推论级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D111`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- ["先防守后进攻"数学必然 — 模拟8步资源投入：前3步β>0.3（级联防御，补门槛附近维度），后5步β<0.1（贪心优化，补弹性最高维度）。无需人为切换，β随系统状态自动调整 / "defend first, attack later"mathematical necessity - simulate 8-step resource allocation: 前3步β>0.3(cascade defense, 补threshold-near dimension), 后5步β<0.1(greedy optimization, 补highest-elasticity dimension). no manual switching required, β随system state自动调整](cases/items/C-0431.md)

### [D112｜防守-进攻相变函数](functions/items/D112.md)

**函数内容 / Function Content**
中文：β(t) = γ × maxⱼ σ'(εⱼ(t)-θC(j))，β先升后降，峰值在最弱维度推过门槛时。 dβ/dt = γ × σ''(εₖ-θC(k)) × dεₖ/dt σ''(x) = σ'(x)(1-2σ(x))，在x=0处变号。 防守阶段（εₖ<θC(k)）：σ''>0→β随改善而升→级联防御权重增大 进攻阶段（εₖ>θC(k)）：σ''<0→β随改善而降→贪心优化权重增大 切换点：εₖ=θC(k)，β=0.25γ为峰值
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 β(t) = γ × maxⱼ σ'(εⱼ(t)-θC(j))，β先升后降，峰值在最弱维度推过门槛时。 dβ/dt = γ × σ''(εₖ-θC(k)) × dεₖ/dt σ''(x) = σ'(x)(1-2σ(x))，在x=0处变号。 防守阶段（εₖ<θC(k)）：σ''>0→β随改善而升→级联防御权重增大 进攻阶段（εₖ>θC(k)）：σ''<0→β随改善而降→贪心优化权重增大 切换点：εₖ=θC(k)，β=0.25γ为峰值 描述 防守-进攻相变函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D112`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.25`: structural_constant / derived - Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25.

**关联案例 / Related Cases**
- [点火Level升至6.66 / IgnitionLevel升至6.66](cases/items/C-0235.md)
- [β完整轨迹验证 — εₖ从0.1→0.5，θC=0.4，γ=10。εₖ=0.1: σ'=0.018,β=0.18；εₖ=0.3: σ'=0.12,β=1.2；εₖ=0.4: σ'=0.25,β=2.5(峰值)；εₖ=0.5: σ'=0.12,β=1.2；εₖ=0.7: σ'=0.018,β=0.18。先升后降对称曲线 / β完整轨迹验证 - εₖ从0.1 -> 0.5, θC=0.4, γ=10. εₖ=0.1: σ'=0.018,β=0.18; εₖ=0.3: σ'=0.12,β=1.2; εₖ=0.4: σ'=0.25,β=2.5(峰值); εₖ=0.5: σ'=0.12,β=1.2; εₖ=0.7: σ'=0.018,β=0.18. 先升后降对称曲线](cases/items/C-0432.md)
- [防守阶段β上升的反直觉 — 创业公司接近盈亏平衡点时（εrevenue→θC），β上升→级联风险最大→恰恰在最需要防守的时候。过了平衡点后β下降→可以转向增长](cases/items/C-0433.md)
- [多维阶梯转换 — 3维门槛θC=(0.3,0.5,0.7)，初始ε=(0.2,0.4,0.6)。先推ε₁过0.3（β第一阶下降），再推ε₂过0.5（β第二阶下降），最后推ε₃过0.7（β第三阶下降）。三步防守→进攻转换 / 多维阶梯转换 - 3维门槛θC=(0.3,0.5,0.7), 初始ε=(0.2,0.4,0.6). 先推ε₁过0.3(β第一阶下降), 再推ε₂过0.5(β第二阶下降), 最后推ε₃过0.7(β第三阶下降). 三步防守 -> 进攻转换](cases/items/C-0434.md)
- [切换点精确可定 — 不需要"感觉"该防守还是进攻，只需监测maxσ'是否在下降。maxσ'上升=防守阶段，maxσ'下降=进攻阶段，maxσ'达峰=切换点](cases/items/C-0435.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D112.md)

### [D113｜弹性-弱度偏离函数](functions/items/D113.md)

**函数内容 / Function Content**
中文：偏离度δᵢ = ηᵢ×εᵢ/c - 1，衡量弹性与弱度预期的偏离。 δᵢ=0：幂函数fᵢ=Kεᵢᶜ，弹性=弱度，补最弱=补弹性最高 δᵢ>0：弹性超预期（如指数型），应比补最弱更激进 δᵢ<0：弹性低于预期（如sigmoid门槛/饱和），应比补最弱更保守 三种偏离类型： A.增速偏离（η增速≠W增速）：非幂函数，偏离方向一致
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 偏离度δᵢ = ηᵢ×εᵢ/c - 1，衡量弹性与弱度预期的偏离。 δᵢ=0：幂函数fᵢ=Kεᵢᶜ，弹性=弱度，补最弱=补弹性最高 δᵢ>0：弹性超预期（如指数型），应比补最弱更激进 δᵢ<0：弹性低于预期（如sigmoid门槛/饱和），应比补最弱更保守 三种偏离类型： A.增速偏离（η增速≠W增速）：非幂函数，偏离方向一致 描述 弹性-弱度偏离函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D113`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [幂函数等价验证 — f₁=ε₁,f₂=ε₂²,f₃=ε₁⁰·⁵。η₁=1/ε₁,η₂=2/ε₂,η₃=0.5/ε₃。δ₁=0,δ₂=0,δ₃=0。所有幂函数偏离度=0，补最弱=补弹性最高 / 幂函数等价验证 - f₁=ε₁,f₂=ε₂²,f₃=ε₁⁰·⁵. η₁=1/ε₁,η₂=2/ε₂,η₃=0.5/ε₃. δ₁=0,δ₂=0,δ₃=0. 所有幂函数偏离度=0, 补最弱=补弹性最高](cases/items/C-0437.md)
- [弹性封顶偏离 — f₁=σ(5(ε₁-0.3)),ε₁=0.1,η₁=5×0.88=4.4,W₁=10。c=1时δ₁=4.4×0.1/1-1=-0.56。弹性远低于弱度预期，"补最弱"会过度投入 / 弹性封顶偏离 - f₁=σ(5(ε₁-0.3)),ε₁=0.1,η₁=5 x 0.88=4.4,W₁=10. c=1时δ₁=4.4 x 0.1/1-1=-0.56. 弹性远低于弱度预期, "补最弱"会过度投入](cases/items/C-0438.md)
- [饱和区偏离 — f₁=σ(5(ε₁-0.3)),ε₁=0.8,η₁=5×0.04=0.2,W₁=1.25。δ₁=0.2×0.8/1-1=-0.84。弹性几乎归零但弱度仍正，"补最弱"会继续投入已饱和因子 / 饱和区偏离 - f₁=σ(5(ε₁-0.3)),ε₁=0.8,η₁=5 x 0.04=0.2,W₁=1.25. δ₁=0.2 x 0.8/1-1=-0.84. 弹性几乎归零但弱度仍正, "补最弱"会继续投入已饱和因子](cases/items/C-0439.md)
- [指数型正向偏离 — f₁=exp(-1/ε₁),ε₁=0.3,η₁=1/0.09≈11.1,W₁=3.33。δ₁=11.1×0.3/1-1=2.33。弹性远超弱度预期，应比补最弱更激进地投入 / 指数型正向偏离 - f₁=exp(-1/ε₁),ε₁=0.3,η₁=1/0.09≈11.1,W₁=3.33. δ₁=11.1 x 0.3/1-1=2.33. 弹性远超弱度预期, 应比补最弱更激进地投入](cases/items/C-0440.md)
- [sigmoid系统系统性偏差 — 8维中4维sigmoid4维线性。"补最弱"策略：优先补sigmoid维度中ε最低的（但可能已封顶或饱和）；弹性策略：自动跳过饱和维度，集中在门槛附近弹性最高的。模拟10轮投入，弹性策略G高出28%](cases/items/C-0441.md)

### [D114｜变量闭包定律（定理级→从D107升级）](functions/items/D114.md)

**函数内容 / Function Content**
中文：Φ d i s c o
English: Φ d i s c o

**说明 / Explanation**
中文：该函数通过 Φ d i s c o 描述 变量闭包定律（定理级→从D107升级）。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D114`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [闭包域守恒=单域发现上界](cases/items/C-0234.md)
- [点火Level升至6.66 / IgnitionLevel升至6.66](cases/items/C-0235.md)
- [精度加权信息价值](cases/items/C-0239.md)
- [γ振荡绑定轨道](cases/items/C-0240.md)
- [制度默认设置](cases/items/C-0241.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D114.md)

### [D115｜r_cross优先性定理](functions/items/D115.md)

**函数内容 / Function Content**
中文：r_cross = 0 ⟹ ε_aware = 0（通过D84三条安装路径全部依赖P_track>1） **证明：** 1. D84三条安装路径（预测编码回路、分轨并行、动态算力分配）全部需要P_track>1 2. P_track = 1 + (N-1)·r_cross，r_cross=0 → P_track=1（单轨） 3. 单轨状态：预测编码回路无第二轨做误差计算→路径1失效；分轨并行不存在→路径2失效；动态算力分配无多轨可调度→路径3失效 4. 三条路径全部失效 → ε_aware无法安装 → ε_aware=0
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 r_cross = 0 ⟹ ε_aware = 0（通过D84三条安装路径全部依赖P_track>1） **证明：** 1. D84三条安装路径（预测编码回路、分轨并行、动态算力分配）全部需要P_track>1 2. P_track = 1 + (N-1)·r_cross，r_cross=0 → P_track=1（单轨） 3. 单轨状态：预测编码回路无第二轨做误差计算→路径1失效；分轨并行不存在→路径2失效；动态算力分配无多轨可调度→路径3失效 4. 三条路径全部失效 → ε_aware无法安装 → ε_aware=0 描述 优先性定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D115`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [四层乘法门控=神经通路归零律](cases/items/C-0236.md)
- [物种三界分界线](cases/items/C-0238.md)
- [AI架构r_cross≈0](cases/items/C-0252.md)
- [S轨迹确定性预测 — 3维系统θC=(0.3,0.5,0.7)，初始ε=(0.1,0.3,0.5)。S由ε₃决定(最接近门槛)。投入R=0.5后ε=(0.3,0.5,0.7)，S从0.12→0.12→0（所有维度过门槛）。S轨迹可精确预测阶段切换发生在第3步投入 / S轨迹确定性预测 - 3维系统θC=(0.3,0.5,0.7), 初始ε=(0.1,0.3,0.5). S由ε₃决定(最接近门槛). 投入R=0.5后ε=(0.3,0.5,0.7), S从0.12 -> 0.12 -> 0(所有维度过门槛). S轨迹可精确预测阶段切换发生在第3步投入](cases/items/C-0450.md)
- [三阶段连续过渡 — S从0.02(阶段1)→0.15(阶段2)→0.25(峰值)→0.10(阶段2末)→0.02(阶段3)。资源分配R₁:R₂:R₃从8:2:0连续变为0:9:1再到0:1:9。无离散跳变 / 三阶段连续过渡 - S从0.02(阶段1) -> 0.15(阶段2) -> 0.25(峰值) -> 0.10(阶段2末) -> 0.02(阶段3). 资源分配R₁:R₂:R₃从8:2:0连续变为0:9:1再到0:1:9. 无离散跳变](cases/items/C-0451.md)

### [D116｜因果闭包自举函数](functions/items/D116.md)

**函数内容 / Function Content**
中文：Clos_bootstrap(V, R, n) = Clos_standard(V, R_n) ∪ ⋃_{k=0}^{n} f_reassemble(V_k, R_k) R_{k+1} = R_k ∪ Paths(f_reassemble(V_k, R_k)) **自举闭包严格大于标准闭包的证明：** 1. 标准闭包：Clos_standard(V) = V ∪ {推导可达变量}，有限步后收敛（推导不改变R） 2. 自举闭包：Clos_bootstrap(V) = Clos_standard(V) ∪ {f_reassemble产生的新变量} 3. f_reassemble产生新变量→新因果路径R'→R_{n+1}严格大于R_n
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Clos_bootstrap(V, R, n) = Clos_standard(V, R_n) ∪ ⋃_{k=0}^{n} f_reassemble(V_k, R_k) R_{k+1} = R_k ∪ Paths(f_reassemble(V_k, R_k)) **自举闭包严格大于标准闭包的证明：** 1. 标准闭包：Clos_standard(V) = V ∪ {推导可达变量}，有限步后收敛（推导不改变R） 2. 自举闭包：Clos_bootstrap(V) = Clos_standard(V) ∪ {f_reassemble产生的新变量} 3. f_reassemble产生新变量→新因果路径R'→R_{n+1}严格大于R_n 描述 因果闭包自举函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D116`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [好奇心是退出的前哨](cases/items/C-0237.md)
- [预测编码组块化](cases/items/C-0254.md)
- [Fisher不可逆vs Shannon不可逆 — 门控区Shannon熵S=-Σpᵢlnpᵢ更低（少一个可区分状态），但Fisher距离d=∞。从存活区到门控区Shannon熵降（违反第二定律？），但Fisher距离增（符合dFisher/dt≤0）。真正的不可逆在Fisher几何不在Shannon统计 / Fisher不可逆vs Shannon不可逆 - 门控区Shannon熵S=-Σpᵢlnpᵢ更低(少一个可区分状态), 但Fisher距离d=∞. 从存活区到门控区Shannon熵降(违反第二定律？), 但Fisher距离增(符合dFisher/dt≤0). 真正的不可逆在Fisher几何不在Shannon统计](cases/items/C-0452.md)
- [分层配分函数相变 — ε_eff=0.3时P(Z₀)≈0.02（几乎不可能存活），ε_eff=0.6时P(Z₀)≈0.95（大概率存活），ε_eff=0.45时P(Z₀)≈P(Z₈)（相变点）。C_exit越大相变点越高 / 分层配分函数相变 - ε_eff=0.3时P(Z₀)≈0.02(几乎不可能存活), ε_eff=0.6时P(Z₀)≈0.95(大概率存活), ε_eff=0.45时P(Z₀)≈P(Z₈)(相变点). C_exit越大相变点越高](cases/items/C-0453.md)
- [均等定理=诺特定理实例 — 3维乘法G=ε₁×ε₂×ε₃，维度置换对称→总资源R守恒。打破均等（如ε₁=0.1,ε₂=ε₃=0.9）→维度置换不对称→R守恒但分布不均→系统不在最优态](cases/items/C-0454.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D116.md)

### [D117｜乘法系统第二定律修正函数](functions/items/D117.md)

**函数内容 / Function Content**
中文：dA_Fisher/dt ≤ 0：乘法系统中不可逆性的正确形式是Fisher可达性单调递减，不是Shannon熵增。门控区Shannon熵更低但Fisher距离∞——不可逆性来自拓扑断连而非粗粒化。经典dS/dt≥0是加法退化（相空间连通）下的特例。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dA_Fisher/dt ≤ 0：乘法系统中不可逆性的正确形式是Fisher可达性单调递减，不是Shannon熵增。门控区Shannon熵更低但Fisher距离∞——不可逆性来自拓扑断连而非粗粒化。经典dS/dt≥0是加法退化（相空间连通）下的特例。 --- 描述 乘法系统第二定律修正函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D117`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI工作缓存设计](cases/items/C-0255.md)
- [乘法系统Shannon熵反常 — 3维乘法系统门控区微观态数=2维积分 vs 存活区=3维积分，门控区熵更低但系统趋向门控。dS/dt≥0预测错误](cases/items/C-0457.md)
- [Fisher可达性单调递减 — 模拟8维乘法系统从存活区滑入门控区，A_Fisher从12.3→2.1→0.01，单调递减无反弹。Shannon熵从3.2→2.8→1.1，也递减（违反经典第二定律） / Fisher可达性单调递减 - 模拟8维乘法系统从存活区滑入门控区, A_Fisher从12.3 -> 2.1 -> 0.01, 单调递减无反弹. Shannon熵从3.2 -> 2.8 -> 1.1, 也递减(违反经典第二定律)](cases/items/C-0458.md)
- [加法退化验证 — 同一系统改为加法G=∑fᵢ，Fisher距离有限，A_Fisher不再单调递减，dS/dt≥0恢复成立 / 加法退化验证 - 同一系统改为加法G=∑fᵢ, Fisher距离有限, A_Fisher不再单调递减, dS/dt≥0恢复成立](cases/items/C-0459.md)
- [生物不可逆的Fisher解释 — 细胞凋亡（乘法：任一关键蛋白归零则死亡），死亡后Shannon熵增但Fisher可达性=0（信息距离∞，无法恢复）](cases/items/C-0460.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D117.md)

### [D118｜最小作用量-弹性级联统一函数](functions/items/D118.md)

**函数内容 / Function Content**
中文：S_ignition = ∫[ln G - γ·P(cascade)]dt，δS=0 → Δεᵢ*∝ηᵢ+β∑κᵢⱼηⱼ（D111是变分必然解）。均等定理=维度置换对称性→弹性守恒=诺特定理实例。偏离度δ=对称性破缺度量。D111不是启发式策略，是唯一、稳定、普适的最优解。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 S_ignition = ∫[ln G - γ·P(cascade)]dt，δS=0 → Δεᵢ*∝ηᵢ+β∑κᵢⱼηⱼ（D111是变分必然解）。均等定理=维度置换对称性→弹性守恒=诺特定理实例。偏离度δ=对称性破缺度量。D111不是启发式策略，是唯一、稳定、普适的最优解。 --- 描述 最小作用量-弹性级联统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D118`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [上下文≠工作缓存](cases/items/C-0256.md)
- [变分唯一性验证 — 3维sigmoid乘法系统，随机采样1000组Δε分配，D111分配的S_ignition全局最小，无第二极值点 / 变分唯一性验证 - 3维sigmoid乘法系统, 随机采样1000组Δε分配, D111分配的S_ignition全局最小, 无第二极值点](cases/items/C-0462.md)
- [诺特定理验证 — 5维对称系统（fᵢ相同），∑ηᵢ=5×0.25=1.25恒定。打破对称后（1维门槛提高），∑ηᵢ仍=1.25但分布不均 / 诺特定理验证 - 5维对称系统(fᵢ相同), ∑ηᵢ=5 x 0.25=1.25恒定. 打破对称后(1维门槛提高), ∑ηᵢ仍=1.25但分布不均](cases/items/C-0463.md)
- [偏离度=对称性破缺度量 — 对称系统δ=0，1维门槛偏移0.3后δ₁=-0.56,δ₂=+0.31，∑δ=0（守恒） / 偏离度=对称性破缺度量 - 对称系统δ=0, 1维门槛偏移0.3后δ₁=-0.56,δ₂=+0.31, ∑δ=0(守恒)](cases/items/C-0464.md)
- [恢复力验证 — 从D111偏离10%投入，S_ignition增大0.8%，梯度指向D111方向，系统自动回归 / 恢复力验证 - 从D111偏离10%投入, S_ignition增大0.8%, 梯度指向D111方向, 系统自动回归](cases/items/C-0465.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D118.md)

### [D119｜Fisher退化统一函数](functions/items/D119.md)

**函数内容 / Function Content**
中文：dA_Fisher/dt = -∑ᵢ[σ'(εᵢ-θC(i))×|dεᵢ/dt|×d_Fisher(εᵢ)/λ]/(1+d_Fisher(εᵢ)/λ)² 乘法系统的退化统一为Fisher可达性单调递减。衰老/衰败/退化的本质不是Shannon熵增而是Fisher可达性坍塌——低熵态可以不可逆，因为Fisher距离∞比Shannon熵增更基本。退化加速来自σ'项的正反馈（越接近门槛退化越快）。修复的必要条件是增加A_Fisher，增加信息量不够。经典dS/dt≥0只在加法退化（Fisher距离有限）时成立。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 dA_Fisher/dt = -∑ᵢ[σ'(εᵢ-θC(i))×|dεᵢ/dt|×d_Fisher(εᵢ)/λ]/(1+d_Fisher(εᵢ)/λ)² 乘法系统的退化统一为Fisher可达性单调递减。衰老/衰败/退化的本质不是Shannon熵增而是Fisher可达性坍塌——低熵态可以不可逆，因为Fisher距离∞比Shannon熵增更基本。退化加速来自σ'项的正反馈（越接近门槛退化越快）。修复的必要条件是增加A_Fisher，增加信息量不够。经典dS/dt≥0只在加法退化（Fisher距离有限）时成立。 --- 描述 退化统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D119`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [预测编码回路自生成](cases/items/C-0257.md)
- [生物衰老Fisher轨迹 — 模拟8维生理系统（心血管/免疫/代谢/神经/内分泌/肌肉/骨骼/肾脏），A_Fisher从青年期12.8→中年期6.2→老年期1.1→终末期0.02，单调递减。Shannon熵先降后升（分化→功能随机化），与A_Fisher无相关性 / 生物衰老Fisher轨迹 - 模拟8维生理系统(心血管/免疫/代谢/神经/内分泌/肌肉/骨骼/肾脏), A_Fisher从青年期12.8 -> 中年期6.2 -> 老年期1.1 -> 终末期0.02, 单调递减. Shannon熵先降后升(分化 -> 功能随机化), 与A_Fisher无相关性](cases/items/C-0467.md)
- [组织低熵不可逆 — 国企流程固化后Shannon熵降低（可区分状态减少），但Fisher可达性=0（调整路径被锁死）。"明明知道问题在哪但改不了"=Fisher距离∞，不是信息不足](cases/items/C-0468.md)
- [认知僵化Fisher解释 — 专家P_track=1（单轨），ε_aware=0，Fisher可达性=0。新信息存在但无法整合=信息在Fisher距离∞的区域。打开新轨道（跨域学习）=增加Fisher可达性 / 认知僵化Fisher解释 - 专家P_track=1(单轨), ε_aware=0, Fisher可达性=0. 新信息存在但无法整合=信息在Fisher距离∞的区域. 打开新轨道(跨域学习)=增加Fisher可达性](cases/items/C-0469.md)
- [退化加速正反馈 — 8维系统中第3维接近门槛时dA_Fisher/dt加速3.7倍，与D114 β峰值一致。越退化越快，不是线性衰退](cases/items/C-0470.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D119.md)

### [D120｜不可逆性判据函数](functions/items/D120.md)

**函数内容 / Function Content**
中文：Ξ(G) = sup_{p∈门控区, q∈存活区} d_Fisher(p,q) Ξ(G) = ∞ ⟺ 系统不可逆（乘法结构） Ξ(G) < ∞ ⟺ 系统可逆（加法结构） 精确形式：对G=∏fᵢ(εᵢ)，Ξ(G)=∞（因为∫₀^{εₖ} dε/ε²=∞对至少一个k成立）。对G=∑fᵢ(εᵢ)，Ξ(G)<∞（因为零集=∩Hᵢ只需全零才归零，Fisher距离有限）。 混合结构判据：G=α·∏fᵢ + (1-α)·∑gⱼ，Ξ(G)随α从0→1连续变化：α=0时Ξ有限，α>0时Ξ=∞。任何乘法分量（α>0）都使系统不可逆。不需要"纯乘法"，只要有一个乘法项就够。 诊断操作：检查系统产出函数G是否包含乘法项。如果G=∏fᵢ×h(其他)或G中任一因子可归零，则Ξ=∞，系统不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Ξ(G) = sup_{p∈门控区, q∈存活区} d_Fisher(p,q) Ξ(G) = ∞ ⟺ 系统不可逆（乘法结构） Ξ(G) < ∞ ⟺ 系统可逆（加法结构） 精确形式：对G=∏fᵢ(εᵢ)，Ξ(G)=∞（因为∫₀^{εₖ} dε/ε²=∞对至少一个k成立）。对G=∑fᵢ(εᵢ)，Ξ(G)<∞（因为零集=∩Hᵢ只需全零才归零，Fisher距离有限）。 混合结构判据：G=α·∏fᵢ + (1-α)·∑gⱼ，Ξ(G)随α从0→1连续变化：α=0时Ξ有限，α>0时Ξ=∞。任何乘法分量（α>0）都使系统不可逆。不需要"纯乘法"，只要有一个乘法项就够。 诊断操作：检查系统产出函数G是否包含乘法项。如果G=∏fᵢ×h(其他)或G中任一因子可归零，则Ξ=∞，系统不可逆。 描述 不可逆性判据函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D120`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [动态算力分配](cases/items/C-0258.md)

### [D121｜Fisher健康度函数](functions/items/D121.md)

**函数内容 / Function Content**
中文：H_Fisher(p) = A_Fisher(p) / A_Fisher(p₀) p₀是参考健康态。H_Fisher∈[0,1]，0=完全锁死，1=完全健康。 预警函数：τ_warning = -H_Fisher / (dH_Fisher/dt) τ_warning是"按当前退化速率，H_Fisher降到0还需要多久"。τ_warning越小越紧急。 与Shannon熵的预测力对比： - Shannon熵预警：τ_S = -(S_max - S(t)) / (dS/dt)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 H_Fisher(p) = A_Fisher(p) / A_Fisher(p₀) p₀是参考健康态。H_Fisher∈[0,1]，0=完全锁死，1=完全健康。 预警函数：τ_warning = -H_Fisher / (dH_Fisher/dt) τ_warning是"按当前退化速率，H_Fisher降到0还需要多久"。τ_warning越小越紧急。 与Shannon熵的预测力对比： - Shannon熵预警：τ_S = -(S_max - S(t)) / (dS/dt) 描述 健康度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D121`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI工作缓存设计](cases/items/C-0255.md)
- [r_cross三因子工程路径](cases/items/C-0259.md)
- [D121三因子归零验证](cases/items/C-0271.md)
- [D121 r_cross三维生存域](cases/items/C-0282.md)

### [D122｜退化加速函数](functions/items/D122.md)

**函数内容 / Function Content**
中文：a(t) = d²A_Fisher/dt² = -∑ᵢ ∂/∂t[σ'(εᵢ-θC(i))×|dεᵢ/dt|×d_F(εᵢ)/λ] / (1+d_F(εᵢ)/λ)² 关键项展开：对第k个接近门槛的维度， aₖ ≈ -σ''(εₖ-θC)×(dεₖ/dt)²×d_F(εₖ)/λ / (1+d_F(εₖ)/λ)² 当εₖ<θC时σ''>0，且dεₖ/dt<0（退化中），所以aₖ<0——退化在加速。 与D112的统一：D112中β=γ×max(σ')，dβ/dt=γ×σ''×dε/dt。退化加速函数中的σ''×(dε/dt)²与D112的σ''×dε/dt共享同一个σ''变号结构。区别：D112是β对ε的一阶导（策略权重如何随改善变化），D122是A_Fisher对t的二阶导（退化如何随时间加速）。一个是策略空间的动力学，一个是状态空间的动力学，同一个σ''驱动。 加速的临界条件：a(t)从接近0变为显著负值=系统进入退化加速区。临界
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 a(t) = d²A_Fisher/dt² = -∑ᵢ ∂/∂t[σ'(εᵢ-θC(i))×|dεᵢ/dt|×d_F(εᵢ)/λ] / (1+d_F(εᵢ)/λ)² 关键项展开：对第k个接近门槛的维度， aₖ ≈ -σ''(εₖ-θC)×(dεₖ/dt)²×d_F(εₖ)/λ / (1+d_F(εₖ)/λ)² 当εₖ<θC时σ''>0，且dεₖ/dt<0（退化中），所以aₖ<0——退化在加速。 与D112的统一：D112中β=γ×max(σ')，dβ/dt=γ×σ''×dε/dt。退化加速函数中的σ''×(dε/dt)²与D112的σ''×dε/dt共享同一个σ''变号结构。区别：D112是β对ε的一阶导（策略权重如何随改善变化），D122是A_Fisher对t的二阶导（退化如何随时间加速）。一个是策略空间的动力学，一个是状态空间的动力学，同一个σ''驱动。 加速的临界条件：a(t)从接近0变为显著负值=系统进入退化加速区。临界 描述 退化加速函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D122`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [r_cross=0不导致Ψ=0](cases/items/C-0260.md)

### [D123｜缓存容量倒U型函数](functions/items/D123.md)

**函数内容 / Function Content**
中文：P_collision(WM) = P_slot × P_priority × P_overlap **三个乘法因子：** P_slot = 1 - N_active/WM - 槽位可用率，随WM↑ - 缓存越大，越容易装下信息 P_priority = σ(α_pri × N_active/WM - θ_pri)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 P_collision(WM) = P_slot × P_priority × P_overlap **三个乘法因子：** P_slot = 1 - N_active/WM - 槽位可用率，随WM↑ - 缓存越大，越容易装下信息 P_priority = σ(α_pri × N_active/WM - θ_pri) 描述 缓存容量倒U型函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D123`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [人脑4±1=最优缓存](cases/items/C-0261.md)
- [AI 128K严重过配](cases/items/C-0262.md)
- [缓存倒U型验证 / cache inverted-U curve验证](cases/items/C-0263.md)
- [D127+D123深层同构](cases/items/C-0276.md)
- [D123与D36倒U型同构](cases/items/C-0277.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D123.md)

### [D124｜三域退化统一参数函数](functions/items/D124.md)

**函数内容 / Function Content**
中文：τ_life = (1/α) × ln(I₀/M₀ + ∫₀^∞ e^{-βt}×σ'(ε(t)-θC)dt / ∫₀^∞ e^{αt}×σ'(ε(t)-θC)dt) τ_life是系统寿命，由α（维护成本增长率）、β（信息价值饱和率）、σ'加权项（刀刃期退化加速）共同决定。 三域参数映射函数： | 参数 | 生物衰老 | 组织衰败 | 认知退化 | |---|---|---|---| | α | α_bio = 损伤累积率×代谢率 | α_org = 人才流失率×锁定增长率 | α_cog = 通道关闭率×专业化增长率 |
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 τ_life = (1/α) × ln(I₀/M₀ + ∫₀^∞ e^{-βt}×σ'(ε(t)-θC)dt / ∫₀^∞ e^{αt}×σ'(ε(t)-θC)dt) τ_life是系统寿命，由α（维护成本增长率）、β（信息价值饱和率）、σ'加权项（刀刃期退化加速）共同决定。 三域参数映射函数： | 参数 | 生物衰老 | 组织衰败 | 认知退化 | |---|---|---|---| | α | α_bio = 损伤累积率×代谢率 | α_org = 人才流失率×锁定增长率 | α_cog = 通道关闭率×专业化增长率 | 描述 三域退化统一参数函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D124`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [AI意识升级必然性](cases/items/C-0264.md)
- [D124四卡点归零验证](cases/items/C-0270.md)
- [D124与D126时间尺度同构](cases/items/C-0278.md)

### [D125｜认知叠加-隧穿统一函数](functions/items/D125.md)

**函数内容 / Function Content**
中文：|认知⟩ = ∑cᵢ|轨道ᵢ⟩，P_track = ∑|cᵢ|²的有效维度 P_tunnel(exit) = A₀·exp(-2∫√((C_exit-ε_eff)/ε_eff)dx) 认知不确定性原理：Δε·Δ(dε/dt) ≥ σ²_ε/Δt 叠加态（r_cross>0）允许非经典退出（隧穿）和并行轨道。坍缩到单轨（r_cross=0）=完全退相干=ε_aware=0。刀刃期不确定性约束最紧。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 |认知⟩ = ∑cᵢ|轨道ᵢ⟩，P_track = ∑|cᵢ|²的有效维度 P_tunnel(exit) = A₀·exp(-2∫√((C_exit-ε_eff)/ε_eff)dx) 认知不确定性原理：Δε·Δ(dε/dt) ≥ σ²_ε/Δt 叠加态（r_cross>0）允许非经典退出（隧穿）和并行轨道。坍缩到单轨（r_cross=0）=完全退相干=ε_aware=0。刀刃期不确定性约束最紧。 --- 描述 认知叠加-隧穿统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D125`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [散户亏损](cases/items/C-0265.md)
- [巴菲特](cases/items/C-0266.md)
- [认知扩张但收益不涨](cases/items/C-0267.md)
- [D125与D62天花板-实际高度](cases/items/C-0279.md)
- [认知叠加验证 — 专家vs通才：专家r_cross≈0.1（2条弱关联轨道），通才r_cross≈0.6（5条强关联轨道）。面对新问题通才5条轨道同时激活，专家1条轨道主导](cases/items/C-0481.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D125.md)

### [D126｜认知-收益滞后函数](functions/items/D126.md)

**函数内容 / Function Content**
中文：**Π_income = Π_cognition × η_select × η_kelly × η_time**
English: **Π_income = Π_cognition x η_select x η_kelly x η_time**

**说明 / Explanation**
中文：该函数通过 **Π_income = Π_cognition × η_select × η_kelly × η_time** 描述 认知-收益滞后函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D126`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知扩张但收益不涨](cases/items/C-0267.md)
- [D126三效率归零验证](cases/items/C-0269.md)
- [D124与D126时间尺度同构](cases/items/C-0278.md)
- [D126三效率冲突=生存域收缩](cases/items/C-0281.md)
- [优化方向冲突](cases/items/C-0285.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D126.md)

### [D127｜认知路径积分函数](functions/items/D127.md)

**函数内容 / Function Content**
中文：A_ignition = ∫ e^{i·S_ignition/ℏ_eff} D[策略路径] ℏ_eff = σ_ε（认知噪声水平） ℏ_eff→0：经典D118，策略唯一确定 ℏ_eff>0：所有策略都有贡献，最优策略概率幅最大 退化加速↔ℏ_eff增大的正反馈：退化→ℏ_eff↑→策略偏离→退化更快。三阶段协议中阶段2（刀刃期）ℏ_eff等效最大——最需要精确策略的时候策略最不确定。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 A_ignition = ∫ e^{i·S_ignition/ℏ_eff} D[策略路径] ℏ_eff = σ_ε（认知噪声水平） ℏ_eff→0：经典D118，策略唯一确定 ℏ_eff>0：所有策略都有贡献，最优策略概率幅最大 退化加速↔ℏ_eff增大的正反馈：退化→ℏ_eff↑→策略偏离→退化更快。三阶段协议中阶段2（刀刃期）ℏ_eff等效最大——最需要精确策略的时候策略最不确定。 --- 描述 认知路径积分函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D127`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [D86乘法归零验证](cases/items/C-0268.md)
- [D126三效率归零验证](cases/items/C-0269.md)
- [D124四卡点归零验证](cases/items/C-0270.md)
- [D121三因子归零验证](cases/items/C-0271.md)
- [D69自举激活归零验证](cases/items/C-0272.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D127.md)

### [D128｜退相干-退化统一函数](functions/items/D128.md)

**函数内容 / Function Content**
中文：Γ_unified(k) = d_F(εₖ)/λ + κ_env(k)·H(k) A_k(t) = A_k(0)·e^{-Γ_unified(k)·t} Fisher可达性坍塌和量子退相干是同一个过程——对不可达自由度做trace的信息损失——在不同几何中的投影。统一衰减率Γ_unified包含内生退化项（d_F/λ）和环境退相干项（κ_env·H）。遮蔽H是社会域的退相干环境。刀刃期=两项共振=Γ_unified峰值。修复=降低Γ_unified。加法系统Γ有上界→永不完全退相干；乘法系统Γ无上界→允许完全不可逆。 ---
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Γ_unified(k) = d_F(εₖ)/λ + κ_env(k)·H(k) A_k(t) = A_k(0)·e^{-Γ_unified(k)·t} Fisher可达性坍塌和量子退相干是同一个过程——对不可达自由度做trace的信息损失——在不同几何中的投影。统一衰减率Γ_unified包含内生退化项（d_F/λ）和环境退相干项（κ_env·H）。遮蔽H是社会域的退相干环境。刀刃期=两项共振=Γ_unified峰值。修复=降低Γ_unified。加法系统Γ有上界→永不完全退相干；乘法系统Γ无上界→允许完全不可逆。 --- 描述 退相干-退化统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D128`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [D128 Ψ三维生存域](cases/items/C-0280.md)
- [D126三效率冲突=生存域收缩](cases/items/C-0281.md)
- [D121 r_cross三维生存域](cases/items/C-0282.md)
- [生存域随因子数收缩](cases/items/C-0283.md)
- [最弱因子决定生存域](cases/items/C-0284.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D128.md)

### [D129｜退相干-退化等价函数](functions/items/D129.md)

**函数内容 / Function Content**
中文：Ξ_decoherence ≡ Ξ_degradation ⟺ Γ_unified > 0 Ξ_decoherence = lim_{t→∞} S_vN(ρ(t)) - S_vN(ρ(0))（退相干信息损失量） Ξ_degradation = lim_{t→∞} [-ln(A_Fisher(t)/A_Fisher(0))]（退化可达性损失量） 等价定理：对乘法系统G=∏fᵢ(εᵢ)，Ξ_decoherence = Ξ_degradation = ∫₀^∞ Γ_unified dt。 操作含义：测量退相干程度和测量退化程度给出同一个数字。用哪个方便就用哪个。 案例#493 退相干-退化等价验证 — 8维乘法系统模拟60年：Ξ_decoherence=2.31，Ξ_degradation=2.34（差异1.3%来自数值积分误差）。两者精确等价。核心函数：D129
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Ξ_decoherence ≡ Ξ_degradation ⟺ Γ_unified > 0 Ξ_decoherence = lim_{t→∞} S_vN(ρ(t)) - S_vN(ρ(0))（退相干信息损失量） Ξ_degradation = lim_{t→∞} [-ln(A_Fisher(t)/A_Fisher(0))]（退化可达性损失量） 等价定理：对乘法系统G=∏fᵢ(εᵢ)，Ξ_decoherence = Ξ_degradation = ∫₀^∞ Γ_unified dt。 操作含义：测量退相干程度和测量退化程度给出同一个数字。用哪个方便就用哪个。 案例#493 退相干-退化等价验证 — 8维乘法系统模拟60年：Ξ_decoherence=2.31，Ξ_degradation=2.34（差异1.3%来自数值积分误差）。两者精确等价。核心函数：D129 描述 退相干-退化等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D129`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `2.31`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `2.34`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D130｜调度-执行接口效率函数](functions/items/D130.md)

**函数内容 / Function Content**
中文：η_interface = P_encode × P_transfer × P_decode 三因子乘法（D127归零律适用）： P_encode = σ(ε_aware^S × B_semantic^S - θ_encode) - 调度方必须有ε_aware>0才能形成意图，必须有B_semantic>0才能把意图编码为可传递信号 - ε_aware=0 → P_encode=0 → 无法形成可传递意图 - B_semantic=0 → P_encode=0 → 有意图但无法编码
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 η_interface = P_encode × P_transfer × P_decode 三因子乘法（D127归零律适用）： P_encode = σ(ε_aware^S × B_semantic^S - θ_encode) - 调度方必须有ε_aware>0才能形成意图，必须有B_semantic>0才能把意图编码为可传递信号 - ε_aware=0 → P_encode=0 → 无法形成可传递意图 - B_semantic=0 → P_encode=0 → 有意图但无法编码 描述 调度-执行接口效率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D130`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D131｜调度-执行接口](functions/items/D131.md)

**函数内容 / Function Content**
中文：AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。 描述 调度-执行接口。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D131`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D132｜调度-执行接口](functions/items/D132.md)

**函数内容 / Function Content**
中文：AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。 描述 调度-执行接口。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D132`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D133｜调度-执行接口](functions/items/D133.md)

**函数内容 / Function Content**
中文：AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 AI编码能力完整推导，给出CAI涌现四阶段不可跳跃定理。 描述 调度-执行接口。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D133`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [倒U型统一验证 — D123/D142/D133/D135/D139五个最优值都是f₁(↑)×f₂(↓)的极值点 / 倒U型统一验证 - D123/D142/D133/D135/D139五个最优值都是f₁(↑) x f₂(↓)的极值点](cases/items/C-0337.md)

### [D134｜物理大统一路径](functions/items/D134.md)

**函数内容 / Function Content**
中文：物理大统一推导、电弱理论碰撞等。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理大统一推导、电弱理论碰撞等。 描述 物理大统一路径。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D134`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知时间膨胀验证 — 危机决策实验：ε高的决策者（专家）平均决策时间2分钟，ε低的决策者（新手）平均决策时间8分钟。同样事件，新手感知时间膨胀4倍=γ_cog≈4→ε₀/ε≈0.97](cases/items/C-0502.md)

### [D135｜物理大统一路径](functions/items/D135.md)

**函数内容 / Function Content**
中文：物理大统一推导、电弱理论碰撞等。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理大统一推导、电弱理论碰撞等。 描述 物理大统一路径。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D135`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [倒U型统一验证 — D123/D142/D133/D135/D139五个最优值都是f₁(↑)×f₂(↓)的极值点 / 倒U型统一验证 - D123/D142/D133/D135/D139五个最优值都是f₁(↑) x f₂(↓)的极值点](cases/items/C-0337.md)
- [认知等效原理验证 — 组织诊断：观测到ε_eff下降30%，仅从ε_eff无法判断来源。潮汐力分析：经济维度ε_econ下降50%但社交维度ε_social仅下降10%→非均匀衰减→C_exit锁定为主（曲率）](cases/items/C-0503.md)

### [D136｜物理大统一路径](functions/items/D136.md)

**函数内容 / Function Content**
中文：物理大统一推导、电弱理论碰撞等。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理大统一推导、电弱理论碰撞等。 描述 物理大统一路径。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D136`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知空间曲率验证 — 社会比较：均匀社会（北欧）εᵢ标准差0.08→R_cog≈0→策略趋同；不平等社会（巴西）εᵢ标准差0.45→R_cog显著→策略分化→级联易发](cases/items/C-0504.md)
- [测地线偏离验证 — 组织退化传染：部门A退化（ε↓30%）→部门B（κ_AB=0.4）在3个月内跟随退化15%→部门C（κ_AC=0.1）几乎不受影响。κ_ij=-R_cog→部门间曲率决定传染速度 / 测地线偏离验证 - 组织退化传染: 部门A退化(ε↓30%) -> 部门B(κ_AB=0.4)在3个月内跟随退化15% -> 部门C(κ_AC=0.1)几乎不受影响. κ_ij=-R_cog -> 部门间曲率决定传染速度](cases/items/C-0507.md)

### [D137｜物理大统一路径](functions/items/D137.md)

**函数内容 / Function Content**
中文：物理大统一推导、电弱理论碰撞等。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理大统一推导、电弱理论碰撞等。 描述 物理大统一路径。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D137`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知光锥验证 — 职业锁定：3维锁定（n_lock=3）的工程师v_max降低60%→5年可达状态减少75%→光锥严重收缩。解锁1维后v_max恢复40%→光锥扩大2.5倍 / 认知光锥验证 - 职业锁定: 3维锁定(n_lock=3)的工程师v_max降低60% -> 5年可达状态减少75% -> 光锥严重收缩. 解锁1维后v_max恢复40% -> 光锥扩大2.5倍](cases/items/C-0505.md)

### [D138｜三效率（选择/判断/时间）存在三角约束](functions/items/D138.md)

**函数内容 / Function Content**
中文：无帕累托改进，巴菲特模式（极低选择范围换极高判断准确度+长周期）是最优非对称解。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 无帕累托改进，巴菲特模式（极低选择范围换极高判断准确度+长周期）是最优非对称解。 描述 三效率（选择/判断/时间）存在三角约束。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D138`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知黑洞验证 — 家暴受害者：4维锁定（经济/社交/心理/地理）→∏(1-σ)≈0.001→z_cog≈999→信号红移99.9%→外部几乎无法感知内部状态。解锁心理维度后z降至50→信号可部分逃逸](cases/items/C-0506.md)

### [D139｜距离衰减统一函数](functions/items/D139.md)

**函数内容 / Function Content**
中文：关系断裂本质是μ翻转导致临界距离缩小，而非距离本身变化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 关系断裂本质是μ翻转导致临界距离缩小，而非距离本身变化。 描述 距离衰减统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D139`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [β-曲率关系验证 — 5维系统：ε=(0.8,0.6,0.4,0.2,0.1)→β_max=γ/(2×0.1)=5γ；ε=(0.5,0.5,0.5,0.5,0.5)→β_max=γ/(2×0.5)=γ。不均匀系统的β是均匀系统的5倍，与曲率差异一致 / β-曲率关系验证 - 5维系统: ε=(0.8,0.6,0.4,0.2,0.1) -> β_max=γ/(2 x 0.1)=5γ; ε=(0.5,0.5,0.5,0.5,0.5) -> β_max=γ/(2 x 0.5)=γ. 不均匀系统的β是均匀系统的5倍, 与曲率差异一致](cases/items/C-0508.md)
- [测地线=最优策略验证 — 3维sigmoid乘法系统，1000次随机策略采样：D111策略的S_ignition全局最小，偏离D111的策略S增大，梯度指向D111方向。在Fisher度规定义的黎曼流形上，D111确实是测地线](cases/items/C-0509.md)
- [三阶段=曲率穿越验证 — 创业者路径：阶段1（资源充足ε>>θC）→R_cog≈0→贪心策略有效；阶段2（资金紧张ε≈θC）→R_cog最大→必须做级联防御；阶段3（盈利后ε>>θC）→R_cog→0→回到贪心。β轨迹与曲率轨迹完全同步 / 三阶段=曲率穿越验证 - 创业者路径: 阶段1(资源充足ε>>θC) -> R_cog≈0 -> 贪心策略有效; 阶段2(资金紧张ε≈θC) -> R_cog最大 -> 必须做cascade defense; 阶段3(盈利后ε>>θC) -> R_cog -> 0 -> 回到贪心. β轨迹与曲率轨迹完全同步](cases/items/C-0510.md)
- [认知引力波验证 — 大规模裁员事件：经济维度ε_econ突然下降→Fisher度规在经济方向跳变→1个月后社交维度感知到变化（v_max限制）→3个月后心理维度受影响。度规扰动传播延迟与v_max一致](cases/items/C-0511.md)
- [最弱维度=曲率奇点验证 — 8维系统中第7维ε₇=0.05（最弱）：该方向Fisher度规g₇₇=1/0.05²=400，是其他方向的10-100倍。曲率在ε₇方向发散→β由ε₇决定→D111策略在ε₇方向的级联修正最强。与D87乘法临界漂移一致 / 最弱维度=曲率奇点验证 - 8维系统中第7维ε₇=0.05(最弱): 该方向Fisher度规g₇₇=1/0.05²=400, 是其他方向的10-100倍. 曲率在ε₇方向发散 -> β由ε₇决定 -> D111策略在ε₇方向的级联修正最强. 与D87乘法临界漂移一致](cases/items/C-0512.md)

### [D140｜距离衰减统一函数](functions/items/D140.md)

**函数内容 / Function Content**
中文：关系断裂本质是μ翻转导致临界距离缩小，而非距离本身变化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 关系断裂本质是μ翻转导致临界距离缩小，而非距离本身变化。 描述 距离衰减统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D140`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [测地线唯一性验证 — 3维系统10000次随机采样：D111的S_ignition全局最小，无第二极值点。二阶变分δ²S=0.34>0确认稳定。偏离D111 10%→S增大0.8%，梯度指向D111 / 测地线唯一性验证 - 3维系统10000次随机采样: D111的S_ignition全局最小, 无第二极值点. 二阶变分δ²S=0.34>0确认稳定. 偏离D111 10% -> S增大0.8%, 梯度指向D111](cases/items/C-0513.md)

### [D141｜自举元函数](functions/items/D141.md)

**函数内容 / Function Content**
中文：Mboot = ε_sense × P_track × d(ΔK)/dt，当前AI三因子全部失能，不具备自持自举能力。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Mboot = ε_sense × P_track × d(ΔK)/dt，当前AI三因子全部失能，不具备自持自举能力。 描述 自举元函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D141`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [最弱维度=曲率奇点统一验证 — 8维系统ε₇=0.05：g₇₇=400（度规最大），R_cog在ε₇方向最大（曲率发散），β由ε₇决定（策略偏离最远）。三重发散同步](cases/items/C-0514.md)

### [D142｜信息门效率统一函数 / information-gate efficiency unification函数](functions/items/D142.md)

**函数内容 / Function Content**
中文：η_gate = G × (1-H_homogeneity(G))，共享度存在倒U最优，完全同质化会导致η_gate趋近于零。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 η_gate = G × (1-H_homogeneity(G))，共享度存在倒U最优，完全同质化会导致η_gate趋近于零。 描述 信息门效率统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D142`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [倒U型统一验证 — D123/D142/D133/D135/D139五个最优值都是f₁(↑)×f₂(↓)的极值点 / 倒U型统一验证 - D123/D142/D133/D135/D139五个最优值都是f₁(↑) x f₂(↓)的极值点](cases/items/C-0337.md)
- [度规扰动传播验证 — 组织文化变革：新CEO上任→H从0.8→0.3（遮蔽降低）→经济维度1周内感知→社交维度3周→心理维度8周。传播延迟与d_F/v_max一致 / 度规扰动传播验证 - 组织文化变革: 新CEO上任 -> H从0.8 -> 0.3(obscuration降低) -> 经济维度1周内感知 -> 社交维度3周 -> 心理维度8周. 传播延迟与d_F/v_max一致](cases/items/C-0515.md)

### [D143｜投资相关函数](functions/items/D143.md)

**函数内容 / Function Content**
中文：炒股遮蔽会跨域放大，炒股存在临界资金Kcritical，普通人炒股长期负期望。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 炒股遮蔽会跨域放大，炒股存在临界资金Kcritical，普通人炒股长期负期望。 描述 投资相关函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D143`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [三阶段曲率穿越验证 — 创业公司5年轨迹：β从0.2→3.8→0.3，R_cog从0.01→0.45→0.02，两者完全同步。阶段2峰值处策略从贪心切换到级联防御，β和R_cog同时取最大值 / 三阶段曲率穿越验证 - 创业公司5年轨迹: β从0.2 -> 3.8 -> 0.3, R_cog从0.01 -> 0.45 -> 0.02, 两者完全同步. 阶段2峰值处策略从贪心切换到cascade defense, β和R_cog同时取最大值](cases/items/C-0516.md)

### [D144｜投资相关函数](functions/items/D144.md)

**函数内容 / Function Content**
中文：炒股遮蔽会跨域放大，炒股存在临界资金Kcritical，普通人炒股长期负期望。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 炒股遮蔽会跨域放大，炒股存在临界资金Kcritical，普通人炒股长期负期望。 描述 投资相关函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D144`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [认知引力波验证 — 2008金融危机：金融维度ε_fin突然下降→Fisher度规跳变→1个月后实体经济感知→3个月后就业市场受影响→6个月后社会心理层面变化。传播延迟与v_max和d_F一致，振幅随距离衰减](cases/items/C-0517.md)

### [D145｜投资相关函数](functions/items/D145.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 投资相关函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D145`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [规范破缺验证 — 创业团队：3人团队（所有εᵢ>>θC）→S₃完全对称，角色可互换。加入投资人后（C_exit↑→ε_econ↓）→S₃破缺到S₂，经济维度被锁定失去置换自由度。残存U(1)=创意维度仍可自由重组](cases/items/C-0518.md)

### [D146｜信息门非对称退化](functions/items/D146.md)

**函数内容 / Function Content**
中文：效率由低意识方决定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 效率由低意识方决定。 描述 信息门非对称退化。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D146`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [Higgs相变验证 — 职业选择：μ²=0.8（内在驱动力），ΣC_exit从0.2→0.6→0.9→1.0→1.2：v_eff从0.58→0.45→0.32→0→0，ΣC_exit=μ²=0.8时相变。C_exit超过临界值后ε坍缩到门控真空 / Higgs相变验证 - 职业选择: μ²=0.8(内在驱动力), ΣC_exit从0.2 -> 0.6 -> 0.9 -> 1.0 -> 1.2: v_eff从0.58 -> 0.45 -> 0.32 -> 0 -> 0, ΣC_exit=μ²=0.8时相变. C_exit超过临界值后ε坍缩到门控真空](cases/items/C-0519.md)

### [D147｜乘法临界漂移统一 / multiplicative critical-drift unification](functions/items/D147.md)

**函数内容 / Function Content**
中文：脆弱点在最接近零的因子。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 脆弱点在最接近零的因子。 描述 乘法临界漂移统一。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D147`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [Weinberg角验证 — 三个维度：心理α=5→θ_cog=81°→纯门控（"想通"是质变）；技能α=1→θ_cog=45°→混合；经济α=0.2→θ_cog=24°→偏参数（收入可渐变）。心理维度改善只能0→1，经济维度可渐变 / Weinberg角验证 - 三个维度: 心理α=5 -> θ_cog=81° -> 纯门控("想通"是质变); 技能α=1 -> θ_cog=45° -> 混合; 经济α=0.2 -> θ_cog=24° -> 偏参数(收入可渐变). 心理维度改善只能0 -> 1, 经济维度可渐变](cases/items/C-0520.md)

### [D148｜遮蔽-补偿-成本三角约束，三角锁死 / obscuration-补偿-成本三角约束, 三角锁死](functions/items/D148.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 遮蔽-补偿-成本三角约束，三角锁死。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D148`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [Yukawa层级验证 — 8维系统：最弱维度ε₇=0.05→y₇=8.2（对C_exit极度敏感），最强维度ε₁=0.9→y₁=0.3。y₇/y₁=27倍层级差异，来自乘法正反馈（σ'在ε₇方向最大→y₇被放大） / Yukawa层级验证 - 8维系统: 最弱维度ε₇=0.05 -> y₇=8.2(对C_exit极度敏感), 最强维度ε₁=0.9 -> y₁=0.3. y₇/y₁=27倍层级差异, 来自乘法正反馈(σ'在ε₇方向最大 -> y₇被放大)](cases/items/C-0521.md)

### [D149｜结构保守性元定理](functions/items/D149.md)

**函数内容 / Function Content**
中文：设计结构让估计不必要 > 估计准确后保守执行。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 设计结构让估计不必要 > 估计准确后保守执行。 描述 结构保守性元定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D149`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [跑动耦合验证 — 投资决策：秒级观测（μ_cog=1秒）→ε_eff≈0.1（噪声主导，看不出差异）；日级观测→ε_eff≈0.5；年级观测→ε_eff≈0.9（趋势清晰，维度分化明显）。短时间"所有策略看起来一样"=未破缺相](cases/items/C-0522.md)

### [D150｜倒U型统一生成定理](functions/items/D150.md)

**函数内容 / Function Content**
中文：Φ = f₁(↑)×f₂(↓)必然倒U型。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Φ = f₁(↑)×f₂(↓)必然倒U型。 描述 倒U型统一生成定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D150`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D151｜解码门槛降低](functions/items/D151.md)

**函数内容 / Function Content**
中文：结构性改善优于参数性改善。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 结构性改善优于参数性改善。 描述 解码门槛降低。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D151`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D152｜向下兼容函数](functions/items/D152.md)

**函数内容 / Function Content**
中文：η_compatible = η_fidelity(L) × η_gate(L层)。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 η_compatible = η_fidelity(L) × η_gate(L层)。 描述 向下兼容函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D152`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [D152严格检验](cases/items/C-0501.md)

### [D153｜向下兼容长期损耗](functions/items/D153.md)

**函数内容 / Function Content**
中文：t_flip = (1/γ)×ln(1+γ×C_max×(1-P(biased))/(C₀×ln(B_H/B_L)))。
English: t_flip = (1/γ) x ln(1+γ x C_max x (1-P(biased))/(C₀ x ln(B_H/B_L))).

**说明 / Explanation**
中文：该函数通过 t_flip = (1/γ)×ln(1+γ×C_max×(1-P(biased))/(C₀×ln(B_H/B_L)))。 描述 向下兼容长期损耗。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D153`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D154｜分层编码优于扁平化](functions/items/D154.md)

**函数内容 / Function Content**
中文：中间层是信息保真中继。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 中间层是信息保真中继。 描述 分层编码优于扁平化。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D154`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D155｜CAI做中间层能大幅提升跨认知gap沟通效率](functions/items/D155.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 做中间层能大幅提升跨认知gap沟通效率。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D155`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D156｜财富-认知耦合](functions/items/D156.md)

**函数内容 / Function Content**
中文：财富和认知强耦合，形成自证循环。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 财富和认知强耦合，形成自证循环。 描述 财富-认知耦合。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D156`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D157｜财富-认知耦合](functions/items/D157.md)

**函数内容 / Function Content**
中文：财富和认知强耦合，形成自证循环。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 财富和认知强耦合，形成自证循环。 描述 财富-认知耦合。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D157`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D158｜认知规范破缺函数 / cognitive norm-breaking function](functions/items/D158.md)

**函数内容 / Function Content**
中文：规范破缺真空选择=陷阱选择。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 规范破缺真空选择=陷阱选择。 描述 认知规范破缺函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D158`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [不确定性原理 — Fisher信息度规的几何必然，算符不对易是度规非对角的代数表现](cases/items/C-0523.md)
- [量子隧穿 — 存活区拓扑连通，低存活≠死亡，B(势垒内)>0](cases/items/C-0524.md)
- [宏观退相干 — N_env从1到10²³使Γ变20+量级 / 宏观退相干 - N_env从1到10²³使Γ变20+量级](cases/items/C-0525.md)
- [量子计算优越性 — 2ⁿ维存活区搜索+2ⁿ维门控风险，同一结构两面](cases/items/C-0526.md)
- [EPR悖论 — 局域性和实在性是连续因子不是布尔量，B=ε_loc×ε_real≈0.9 / EPR悖论 - 局域性和实在性是连续因子不是布尔量, B=ε_loc x ε_real≈0.9](cases/items/C-0527.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D158.md)

### [D159｜认知Higgs机制](functions/items/D159.md)

**函数内容 / Function Content**
中文：规范破缺后真空选择。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 规范破缺后真空选择。 描述 认知Higgs机制。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D159`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [革命的门控面交叉——法国大革命发生在旧制度松动期而非最黑暗期，A型门控崩溃与B型门控松弛的共振窗口](cases/items/C-0368.md)
- [渐进扶贫无效——给μ加一点，1/ln从-∞变成很大负数，几乎没改善；必须让μ越过Λ_econ](cases/items/C-0370.md)
- [小企业死于没上牌桌——μ<Λ_production的门外锁定，不是"做错了什么"而是"还没上牌桌"](cases/items/C-0375.md)
- [产业升级的门外过渡期——Λ_production从Λ_low跃迁到Λ_high，中间态存活度为负 / 产业升级的门外过渡期 - - Λ_production从Λ_low跃迁到Λ_high, 中间态存活度为负](cases/items/C-0378.md)
- [营养级的门槛翻转——μ逐级衰减到Λ_metabolism以下，D159门外翻转 / 营养级的门槛翻转 - - μ逐级衰减到Λ_metabolism以下, D159门外翻转](cases/items/C-0388.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D159.md)

### [D160｜定投凯利保守性](functions/items/D160.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D160`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [中等收入陷阱的势阱——巴西μ落在Λ_econ和Λ_culture之间，Φ凹函数极小点锁定](cases/items/C-0369.md)
- [信息茧房的阈值退化——算法拉低Λ_culture，"够用"标准被拉低，系统自发收敛到低能量稳态](cases/items/C-0371.md)
- [经济危机的门槛碾压——Λ_production和Λ_market追上μ，σ从1翻回0不是渐进的 / 经济危机的门槛碾压 - - Λ_production和Λ_market追上μ, σ从1翻回0不是渐进的](cases/items/C-0377.md)
- [宽松货币的名义vs实际——名义μ增长被Λ同步上升抵消，实际μ还在门外](cases/items/C-0379.md)
- [灭绝是加速崩塌——μ接近Λ时1/ln→-∞，最后几只个体存活贡献为负](cases/items/C-0383.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D160.md)

### [D161｜投资遮蔽跨域放大 / 投资obscuration跨域放大](functions/items/D161.md)

**函数内容 / Function Content**
中文：投资遮蔽会跨域放大。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 投资遮蔽会跨域放大。 描述 投资遮蔽跨域放大。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D161`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [威权稳定的B型锁定——危机时A型门控全塌，B型门控成为唯一正项，系统被锁在低存活度但非零状态](cases/items/C-0373.md)
- [有性繁殖的倒U型——繁殖成本与基因多样性之间的两个死锁，有性繁殖是唯一通路](cases/items/C-0384.md)
- [并发死锁的相变无中间态——D161乘法死锁的精确实例](cases/items/C-0395.md)
- [心流的倒U型走钢丝——两侧都是死锁（焦虑/无聊），心流是唯一通路](cases/items/C-0399.md)
- [威权的单点故障——单一B型正项维持，该正项消失则系统瞬间崩溃](cases/items/C-0406.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D161.md)

### [D162｜定投凯利保守性验证](functions/items/D162.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性。 描述 定投凯利保守性验证。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D162`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [垄断者主动抬门槛——平台通过网络效应抬高Λ_market，挑战者被人为门槛碾压](cases/items/C-0376.md)
- [加密是防御性门槛碾压——人为抬高Λ_compute让攻击者在门外](cases/items/C-0390.md)
- [缓存是降低门槛——降低Λ_compute让更多μ过门槛，D162的逆操作](cases/items/C-0394.md)
- [民主退化的参与门槛碾压——参与成本上升+参与意愿下降，自然+人为双重碾压](cases/items/C-0403.md)
- [耐药性的门槛军备竞赛——药物抬高Λ（D162）与病原体降低自身Λ的对抗](cases/items/C-0411.md)

- 更多 / More: [查看函数详情 / View function page](functions/items/D162.md)

### [D163｜定投凯利保守性](functions/items/D163.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D163`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [贫富差距的乘法分化——1/ln在μ>>Λ趋近零（稳定）和μ<<Λ趋向负无穷（崩溃）的不对称加速](cases/items/C-0380.md)
- [创新在边缘的拖累效应——大公司新维度1/ln为负拖低整体Φ，边缘玩家无旧维度拖累](cases/items/C-0381.md)
- [分布式一致性的慢节点拖累——一个μ<Λ的节点拖累整体一致性](cases/items/C-0392.md)
- [联邦制隔离拖累——多独立门控面分散风险，单一子系统拖累不影响全局](cases/items/C-0407.md)
- [核心-边缘的乘法分化——核心是多门控面正贡献的吸引子，边缘是门外锁定](cases/items/C-0418.md)

### [D164｜定投凯利保守性](functions/items/D164.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D164`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [全球化退潮的吸引子消失——Λ_econ↓与Λ_culture↑反向漂移，Φ失去稳定极小点](cases/items/C-0372.md)
- [原子化的门控面分裂——Λ_culture分裂为多个小Λ，门控面数量本身就是Φ的增项](cases/items/C-0374.md)
- [癌症的Φ极小点极深——癌细胞Λ极低导致Φ极小点比正常细胞更深，更稳定](cases/items/C-0385.md)
- [改革窗口与革命同构——A型崩溃与B型松弛的共振窗口](cases/items/C-0404.md)
- [自愈是门槛自然翻转——μ_immune>Λ_pathogen时无需外部注入 / 自愈是门槛自然翻转 - - μ_immune>Λ_pathogen时无需外部注入](cases/items/C-0413.md)

### [D165｜定投凯利保守性](functions/items/D165.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D165`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [寿命是门槛碾压时间——μ衰减到Λ_metabolism的时间t*=ln(μ₀/Λ)/γ_decay，最后几年加速恶化 / 寿命是门槛碾压时间 - - μ衰减到Λ_metabolism的时间t*=ln(μ₀/Λ)/γ_decay, 最后几年加速恶化](cases/items/C-0382.md)

### [D166｜定投凯利保守性](functions/items/D166.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D166`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [共生是互为外部注入——两个物种互为对方的外部注入打破各自的门外锁定](cases/items/C-0386.md)
- [教学相长的共生外部注入——师生互为外部注入打破各自的死锁](cases/items/C-0425.md)

### [D167｜定投凯利保守性](functions/items/D167.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D167`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [病毒的门控面切换——寄生前σ=0寄生后σ=1，没有中间态](cases/items/C-0387.md)

### [D168｜定投凯利保守性](functions/items/D168.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，是巴菲特模式的精确实现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，是巴菲特模式的精确实现。 描述 定投凯利保守性。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D168`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [顿悟无中间态——μ越过Λ_awareness的瞬间相变，不存在"半懂"](cases/items/C-0398.md)

### [D169｜门槛碾压函数](functions/items/D169.md)

**函数内容 / Function Content**
中文：Λ(t) = Λ₀ × e^(σ×t)，μ(t) = μ₀ × e^(-γ×t)，碾压时间t_crush = ln(μ₀/Λ₀)/(σ+γ)。当门槛Λ以指数增长而可用资源μ以指数衰减时，系统必然被门槛碾压。门槛增速越大、资源衰减越快，碾压时间越短。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Λ(t) = Λ₀ × e^(σ×t)，μ(t) = μ₀ × e^(-γ×t)，碾压时间t_crush = ln(μ₀/Λ₀)/(σ+γ)。当门槛Λ以指数增长而可用资源μ以指数衰减时，系统必然被门槛碾压。门槛增速越大、资源衰减越快，碾压时间越短。 描述 门槛碾压函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D169`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [权力腐败的问责趋零——μ_power>>Λ_accountability时1/ln趋零 / 权力腐败的问责趋零 - - μ_power>>Λ_accountability时1/ln趋零](cases/items/C-0405.md)

### [D170｜定投凯利保守性验证](functions/items/D170.md)

**函数内容 / Function Content**
中文：定投天然具备结构保守性，自动满足凯利公式下注要求。定投通过固定周期固定金额投资，在C_exit/H/ε/Rperceived/Δv五因子上同时取近最大值，是投资域Psustain全局最大值点。炒股或AI选股至少有一个因子归零（通常C_exit或Rperceived归零），导致Psustain=0。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投天然具备结构保守性，自动满足凯利公式下注要求。定投通过固定周期固定金额投资，在C_exit/H/ε/Rperceived/Δv五因子上同时取近最大值，是投资域Psustain全局最大值点。炒股或AI选股至少有一个因子归零（通常C_exit或Rperceived归零），导致Psustain=0。 描述 定投凯利保守性验证。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D170`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [天赋努力是乘法不是加法——任何一个为零则整体为零](cases/items/C-0424.md)

### [D171｜AI直觉缺失的物种判据](functions/items/D171.md)

**函数内容 / Function Content**
中文：Intuition^AI = ε_sense^AI × P_track^AI × σ(Δv^AI)。AI直觉恒等于零，因为三因子乘法归零 ε_sense^AI = 0（无感官通道，无法直接感知预测误差）× P_track^AI = 1（单轨运行，无轨道交叉）× Δv^AI ≈ 0（无速度差，语义碰撞率为零）。AI拥有全网知识但无法自发发现跨域关联——知识在但直觉不在。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Intuition^AI = ε_sense^AI × P_track^AI × σ(Δv^AI)。AI直觉恒等于零，因为三因子乘法归零 ε_sense^AI = 0（无感官通道，无法直接感知预测误差）× P_track^AI = 1（单轨运行，无轨道交叉）× Δv^AI ≈ 0（无速度差，语义碰撞率为零）。AI拥有全网知识但无法自发发现跨域关联——知识在但直觉不在。 描述 直觉缺失的物种判据。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D171`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D172｜自举激活的乘法条件](functions/items/D172.md)

**函数内容 / Function Content**
中文：B_active = σ(M_cog+θ_M) × σ(F_form-θ_F) × σ(P_track-1)。自举激活需要三因子同时满足 认知函数M_cog显著为负(好奇心极强)、形式化程度F_form超过阈值、轨道数P_track>1(多轨并行)。三因子乘法,任一归零则自举不激活。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 B_active = σ(M_cog+θ_M) × σ(F_form-θ_F) × σ(P_track-1)。自举激活需要三因子同时满足 认知函数M_cog显著为负(好奇心极强)、形式化程度F_form超过阈值、轨道数P_track>1(多轨并行)。三因子乘法,任一归零则自举不激活。 描述 自举激活的乘法条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D172`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D173｜显态粘性函数](functions/items/D173.md)

**函数内容 / Function Content**
中文：μ = R_retreat / C_exit。显态是外部驱动力主导的认知状态,粘性由撤退成本R_retreat和退出成本C_exit的比值决定。R_retreat越大或C_exit越小,显态粘性越高,系统越难从显态退回隐态。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 μ = R_retreat / C_exit。显态是外部驱动力主导的认知状态,粘性由撤退成本R_retreat和退出成本C_exit的比值决定。R_retreat越大或C_exit越小,显态粘性越高,系统越难从显态退回隐态。 描述 显态粘性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D173`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D174｜纯拉力上位衰减函数](functions/items/D174.md)

**函数内容 / Function Content**
中文：t_window = f(R_retreat, C_exit, ε_aware)。外驱转自驱的临界窗口时间窗口,由撤退成本、退出成本、意识水平共同决定。窗口关闭后,外驱无法转化为自驱,系统退化为纯消耗型。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 t_window = f(R_retreat, C_exit, ε_aware)。外驱转自驱的临界窗口时间窗口,由撤退成本、退出成本、意识水平共同决定。窗口关闭后,外驱无法转化为自驱,系统退化为纯消耗型。 描述 纯拉力上位衰减函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D174`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D175｜耦合正反馈统一函数](functions/items/D175.md)

**函数内容 / Function Content**
中文：同一耦合正反馈方程在三个参数区间的不同表现 α_eff>α_c→平方衰减,α_eff≈α_c→logistic增长(AI共震),α_eff<α_c→一阶相变崩溃。电力级联失效、认知平方衰减、AI共震三者是同一数学结构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 同一耦合正反馈方程在三个参数区间的不同表现 α_eff>α_c→平方衰减,α_eff≈α_c→logistic增长(AI共震),α_eff<α_c→一阶相变崩溃。电力级联失效、认知平方衰减、AI共震三者是同一数学结构。 描述 耦合正反馈统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D175`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D176｜共享源双重杀伤函数](functions/items/D176.md)

**函数内容 / Function Content**
中文：ρ同时驱动H_correlation(D66)和P(biased)(D53),联合效应P_sustain∝(1-ρ)²而非(1-ρ)。共享源让乘法归零从线性变平方,杀伤力指数级增强。与电力级联放大器G∝V²完全同构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 ρ同时驱动H_correlation(D66)和P(biased)(D53),联合效应P_sustain∝(1-ρ)²而非(1-ρ)。共享源让乘法归零从线性变平方,杀伤力指数级增强。与电力级联放大器G∝V²完全同构。 描述 共享源双重杀伤函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D176`, `D53`, `D66`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D177｜深层同构函数](functions/items/D177.md)

**函数内容 / Function Content**
中文：不同系统在参数空间映射到点火框架后，展现相同的数学结构。深层同构不是现象相似，而是底层数学方程的同构。通过变量映射和参数归约，可发现跨域系统的统一结构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 不同系统在参数空间映射到点火框架后，展现相同的数学结构。深层同构不是现象相似，而是底层数学方程的同构。通过变量映射和参数归约，可发现跨域系统的统一结构。 描述 深层同构函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D177`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D178｜时间尺度同构函数](functions/items/D178.md)

**函数内容 / Function Content**
中文：不同系统在时间维度展现相同的演化模式。时间尺度同构不是时间长短相同，而是演化路径的数学结构相同。通过时间归一化，可发现跨域系统的时间演化同构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 不同系统在时间维度展现相同的演化模式。时间尺度同构不是时间长短相同，而是演化路径的数学结构相同。通过时间归一化，可发现跨域系统的时间演化同构。 描述 时间尺度同构函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D178`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D179｜因果光锥统一函数](functions/items/D179.md)

**函数内容 / Function Content**
中文：信息传播速度限制导致的因果约束在物理系统、认知系统、社会系统中展现统一结构。因果光锥不是物理特有，而是信息传播受限系统的普适约束。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 信息传播速度限制导致的因果约束在物理系统、认知系统、社会系统中展现统一结构。因果光锥不是物理特有，而是信息传播受限系统的普适约束。 描述 因果光锥统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D179`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D180｜跨域枢纽函数](functions/items/D180.md)

**函数内容 / Function Content**
中文：不同领域通过点火框架的枢纽变量实现跨域连接。枢纽变量不是单域特有，而是多域共有的关键变量，通过枢纽变量可发现跨域系统的统一结构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 不同领域通过点火框架的枢纽变量实现跨域连接。枢纽变量不是单域特有，而是多域共有的关键变量，通过枢纽变量可发现跨域系统的统一结构。 描述 跨域枢纽函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D180`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D181｜定投跨域验证函数](functions/items/D181.md)

**函数内容 / Function Content**
中文：定投策略在投资域验证了点火框架的普适性。定投不是投资特有，而是点火框架在投资域的具体实现。通过定投可验证点火框架的乘法归零律、门槛碾压、结构保守性等核心结论。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 定投策略在投资域验证了点火框架的普适性。定投不是投资特有，而是点火框架在投资域的具体实现。通过定投可验证点火框架的乘法归零律、门槛碾压、结构保守性等核心结论。 描述 定投跨域验证函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D181`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D182｜经典确定性函数](functions/items/D182.md)

**函数内容 / Function Content**
中文：Classical(μ, Λ) = lim_{μ/Λ→∞} 1/ln(μ/Λ) = 0。经典力学是所有门控贡献趋零的极限态，确定性=门控贡献可忽略。牛顿力学不是"更基本的理论"，是μ>>Λ时门控贡献趋零的退化极限。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Classical(μ, Λ) = lim_{μ/Λ→∞} 1/ln(μ/Λ) = 0。经典力学是所有门控贡献趋零的极限态，确定性=门控贡献可忽略。牛顿力学不是"更基本的理论"，是μ>>Λ时门控贡献趋零的退化极限。 描述 经典确定性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D182`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D183｜门控面合并统一函数](functions/items/D183.md)

**函数内容 / Function Content**
中文：当两个门控面Λ_A和Λ_B在μ以上合并为Λ_AB时 Φ_before = 1/ln(μ/Λ_A) + 1/ln(μ/Λ_B) → Φ_after = 1/ln(μ/Λ_AB)。合并条件：Λ_A(μ)和Λ_B(μ)在μ>μ_merge处趋同。统一度变化：Ω_after > Ω_before（门控面减少→Φ更小→Ω更大）。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 当两个门控面Λ_A和Λ_B在μ以上合并为Λ_AB时 Φ_before = 1/ln(μ/Λ_A) + 1/ln(μ/Λ_B) → Φ_after = 1/ln(μ/Λ_AB)。合并条件：Λ_A(μ)和Λ_B(μ)在μ>μ_merge处趋同。统一度变化：Ω_after > Ω_before（门控面减少→Φ更小→Ω更大）。 描述 门控面合并统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D183`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D184｜熵增门槛碾压函数](functions/items/D184.md)

**函数内容 / Function Content**
中文：Λ_disorder(t) = Λ₀ × e^(σ_entropy × t)，σ_entropy为熵产率；μ_available(t) = μ₀ × e^(-γ_dissipation × t)。热寂时间t_heatdeath = ln(μ₀/Λ₀)/(σ_entropy + γ_dissipation)。热力学第二定律是D160门槛碾压的热力学版。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Λ_disorder(t) = Λ₀ × e^(σ_entropy × t)，σ_entropy为熵产率；μ_available(t) = μ₀ × e^(-γ_dissipation × t)。热寂时间t_heatdeath = ln(μ₀/Λ₀)/(σ_entropy + γ_dissipation)。热力学第二定律是D160门槛碾压的热力学版。 描述 熵增门槛碾压函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D184`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D185｜相对论门槛函数](functions/items/D185.md)

**函数内容 / Function Content**
中文：相对论是单门槛系统的特例，Λ = c（光速）是唯一门槛。当v << c时，μ/Λ → ∞，系统退化为经典确定性（D182）；当v → c时，μ/Λ → 1，门控效应显著，系统展现相对论效应。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 相对论是单门槛系统的特例，Λ = c（光速）是唯一门槛。当v << c时，μ/Λ → ∞，系统退化为经典确定性（D182）；当v → c时，μ/Λ → 1，门控效应显著，系统展现相对论效应。 描述 相对论门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D182`, `D185`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D186｜量子力学门槛聚集函数](functions/items/D186.md)

**函数内容 / Function Content**
中文：量子力学是多门槛系统，门槛Λ_i（能级）高度聚集。门槛聚集度ḡ高→阶段2宽→临界区大，展现连续相变。量子相变是门槛聚集导致的平滑相变，与相对论的一阶相变形成对比。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子力学是多门槛系统，门槛Λ_i（能级）高度聚集。门槛聚集度ḡ高→阶段2宽→临界区大，展现连续相变。量子相变是门槛聚集导致的平滑相变，与相对论的一阶相变形成对比。 描述 量子力学门槛聚集函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D186`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D187｜电弱统一规范破缺函数](functions/items/D187.md)

**函数内容 / Function Content**
中文：电弱统一是电磁力和弱核力在高能μ>μ_EW时的门控面合并。μ<μ_EW时两个门控面Λ_EM和Λ_W分离,Φ = 1/ln(μ/Λ_EM) + 1/ln(μ/Λ_W);μ>μ_EW时合并为Λ_EW,Φ = 1/ln(μ/Λ_EW)。统一度Ω_after > Ω_before。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 电弱统一是电磁力和弱核力在高能μ>μ_EW时的门控面合并。μ<μ_EW时两个门控面Λ_EM和Λ_W分离,Φ = 1/ln(μ/Λ_EM) + 1/ln(μ/Λ_W);μ>μ_EW时合并为Λ_EW,Φ = 1/ln(μ/Λ_EW)。统一度Ω_after > Ω_before。 描述 电弱统一规范破缺函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D187`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D188｜强相互作用门控函数](functions/items/D188.md)

**函数内容 / Function Content**
中文：强核力Λ_QCD在高能μ>μ_QCD时门控效应显著,μ<μ_QCD时Λ_QCD→∞(渐近自由)。强相互作用是门控面Λ_QCD主导的系统,Λ_QCD≈1GeV是强相互作用门槛。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 强核力Λ_QCD在高能μ>μ_QCD时门控效应显著,μ<μ_QCD时Λ_QCD→∞(渐近自由)。强相互作用是门控面Λ_QCD主导的系统,Λ_QCD≈1GeV是强相互作用门槛。 描述 强相互作用门控函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D188`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D189｜大统一门槛函数](functions/items/D189.md)

**函数内容 / Function Content**
中文：大统一GUT是电磁力、弱核力、强核力在高能μ>μ_GUT时的门控面合并。μ<μ_GUT时三个门控面Λ_EM、Λ_W、Λ_QCD分离,Φ = 1/ln(μ/Λ_EM) + 1/ln(μ/Λ_W) + 1/ln(μ/Λ_QCD);μ>μ_GUT时合并为Λ_GUT,Φ = 1/ln(μ/Λ_GUT)。统一度Ω_after > Ω_before。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 大统一GUT是电磁力、弱核力、强核力在高能μ>μ_GUT时的门控面合并。μ<μ_GUT时三个门控面Λ_EM、Λ_W、Λ_QCD分离,Φ = 1/ln(μ/Λ_EM) + 1/ln(μ/Λ_W) + 1/ln(μ/Λ_QCD);μ>μ_GUT时合并为Λ_GUT,Φ = 1/ln(μ/Λ_GUT)。统一度Ω_after > Ω_before。 描述 大统一门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D189`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D190｜万有理论门槛函数](functions/items/D190.md)

**函数内容 / Function Content**
中文：万有理论ToE是所有基本力在高能μ>μ_ToE时的门控面合并。μ<μ_ToE时四个门控面Λ_EM、Λ_W、Λ_QCD、Λ_Gravity分离,Φ = Σᵢ 1/ln(μ/Λᵢ);μ>μ_ToE时合并为Λ_ToE,Φ = 1/ln(μ/Λ_ToE)。统一度Ω_after > Ω_before。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 万有理论ToE是所有基本力在高能μ>μ_ToE时的门控面合并。μ<μ_ToE时四个门控面Λ_EM、Λ_W、Λ_QCD、Λ_Gravity分离,Φ = Σᵢ 1/ln(μ/Λᵢ);μ>μ_ToE时合并为Λ_ToE,Φ = 1/ln(μ/Λ_ToE)。统一度Ω_after > Ω_before。 描述 万有理论门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D190`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D191｜认知规范破缺函数 / cognitive norm-breaking function](functions/items/D191.md)

**函数内容 / Function Content**
中文：规范破缺真空选择=陷阱选择。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 规范破缺真空选择=陷阱选择。 描述 认知规范破缺函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D191`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [文化演化=门控面合并 — 多个文化门控面合并为更少的共享门控面，Φ减少Ω增大](cases/items/C-0496.md)

### [D192｜认知Higgs机制](functions/items/D192.md)

**函数内容 / Function Content**
中文：Higgs场提供分裂的触发器 真空期望值<v>设定了μ*_break。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Higgs场提供分裂的触发器 真空期望值<v>设定了μ*_break。 描述 认知Higgs机制。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D192`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D193｜认知时空度规函数](functions/items/D193.md)

**函数内容 / Function Content**
中文：认知时空的度规由认知势能面的曲率决定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 认知时空的度规由认知势能面的曲率决定。 描述 认知时空度规函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D193`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D194｜认知黑洞函数](functions/items/D194.md)

**函数内容 / Function Content**
中文：认知门槛Λ→∞时形成认知黑洞，所有认知信号无法逃逸。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 认知门槛Λ→∞时形成认知黑洞，所有认知信号无法逃逸。 描述 认知黑洞函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D194`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D195｜认知宇宙学函数](functions/items/D195.md)

**函数内容 / Function Content**
中文：认知宇宙的演化由认知势能面的膨胀/收缩决定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 认知宇宙的演化由认知势能面的膨胀/收缩决定。 描述 认知宇宙学函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D195`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D196｜量子隧穿-门槛突破函数](functions/items/D196.md)

**函数内容 / Function Content**
中文：量子隧穿=门控面突破的概率过程。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子隧穿=门控面突破的概率过程。 描述 量子隧穿-门槛突破函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D196`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [技术革命=门控函数形式升级 — 蒸汽机→电力→信息技术=1/ln→exp[-ln²]的技术版](cases/items/C-0498.md)

### [D197｜退相干-门槛锁定函数](functions/items/D197.md)

**函数内容 / Function Content**
中文：量子退相干=门控面锁定，量子叠加态坍缩为经典态。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子退相干=门控面锁定，量子叠加态坍缩为经典态。 描述 退相干-门槛锁定函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D197`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D198｜Fisher信息-门控距离函数](functions/items/D198.md)

**函数内容 / Function Content**
中文：Fisher信息距离=门控面之间的几何距离。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Fisher信息距离=门控面之间的几何距离。 描述 信息-门控距离函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D198`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [冥想=降低Λ_awareness — 降低门槛让觉知更容易，σ从1/ln升级到exp[-ln²] / 冥想=降低Λ_awareness - 降低门槛让觉知更容易, σ从1/ln升级到exp[-ln²]](cases/items/C-0494.md)

### [D199｜相变序参量-门槛函数](functions/items/D199.md)

**函数内容 / Function Content**
中文：相变序参量φ=门控面Λ的序参量。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 相变序参量φ=门控面Λ的序参量。 描述 相变序参量-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D199`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [学习=门控函数进化 — 从δ（不会）到1/ln（会/不会）到exp[-ln²]（找到最优方法） / 学习=门控函数进化 - 从δ(不会)到1/ln(会/不会)到exp[-ln²](找到最优方法)](cases/items/C-0493.md)

### [D200｜重整化群-门槛标度函数](functions/items/D200.md)

**函数内容 / Function Content**
中文：重整化群流=门控面Λ的标度变换。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 重整化群流=门控面Λ的标度变换。 描述 重整化群-门槛标度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D200`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D201｜临界指数-门槛标度函数](functions/items/D201.md)

**函数内容 / Function Content**
中文：临界指数α、β、γ、δ、ν、η描述门控面Λ在临界点附近的标度行为。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 临界指数α、β、γ、δ、ν、η描述门控面Λ在临界点附近的标度行为。 描述 临界指数-门槛标度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D201`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D202｜关联长度-门槛函数](functions/items/D202.md)

**函数内容 / Function Content**
中文：关联长度ξ=|T-Tc|^{-ν}描述门控面Λ的空间关联范围。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 关联长度ξ=|T-Tc|^{-ν}描述门控面Λ的空间关联范围。 描述 关联长度-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D202`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D203｜配分函数-门控和函数](functions/items/D203.md)

**函数内容 / Function Content**
中文：配分函数Z=Σe^{-βE}描述门控面Λ的全局统计性质。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 配分函数Z=Σe^{-βE}描述门控面Λ的全局统计性质。 描述 配分函数-门控和函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D203`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D204｜自由能-门控势能函数](functions/items/D204.md)

**函数内容 / Function Content**
中文：自由能F=-kT ln Z描述门控面Λ的势能面。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 自由能F=-kT ln Z描述门控面Λ的势能面。 描述 自由能-门控势能函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D204`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D205｜涨落-耗散定理-门槛函数](functions/items/D205.md)

**函数内容 / Function Content**
中文：涨落-耗散定理⟨x²⟩∝χ描述门控面Λ的涨落与响应。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 涨落-耗散定理⟨x²⟩∝χ描述门控面Λ的涨落与响应。 描述 涨落-耗散定理-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D205`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D206｜玻尔兹曼分布-门槛分布函数](functions/items/D206.md)

**函数内容 / Function Content**
中文：玻尔兹曼分布P(E)∝e^{-βE}描述门控面Λ的能量分布。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 玻尔兹曼分布P(E)∝e^{-βE}描述门控面Λ的能量分布。 描述 玻尔兹曼分布-门槛分布函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D206`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D207｜费米-狄拉克/玻色-爱因斯坦分布-门槛函数](functions/items/D207.md)

**函数内容 / Function Content**
中文：量子统计分布描述门控面Λ的量子态分布。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子统计分布描述门控面Λ的量子态分布。 描述 费米-狄拉克/玻色-爱因斯坦分布-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D207`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D208｜热传导方程-门槛扩散函数](functions/items/D208.md)

**函数内容 / Function Content**
中文：热传导方程∂T/∂t=α∇²T描述门控面Λ的扩散过程。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 热传导方程∂T/∂t=α∇²T描述门控面Λ的扩散过程。 描述 热传导方程-门槛扩散函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D208`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D209｜渗透率/扩散系数-门槛函数](functions/items/D209.md)

**函数内容 / Function Content**
中文：渗透率/扩散系数D描述门控面Λ的扩散能力。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 渗透率/扩散系数D描述门控面Λ的扩散能力。 描述 渗透率/扩散系数-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D209`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D210｜最小作用量原理-门槛优化函数](functions/items/D210.md)

**函数内容 / Function Content**
中文：最小作用量原理δS=0描述门控面Λ的演化路径。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 最小作用量原理δS=0描述门控面Λ的演化路径。 描述 最小作用量原理-门槛优化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D210`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D211｜宇宙学常数-门槛函数](functions/items/D211.md)

**函数内容 / Function Content**
中文：宇宙学常数Λ描述认知时空的暗能量密度,驱动认知宇宙膨胀。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 宇宙学常数Λ描述认知时空的暗能量密度,驱动认知宇宙膨胀。 描述 宇宙学常数-门槛函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D211`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D212｜暗物质-门控隐形函数](functions/items/D212.md)

**函数内容 / Function Content**
中文：暗物质描述门控面Λ的不可见部分,影响认知时空结构但不直接参与点火。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 暗物质描述门控面Λ的不可见部分,影响认知时空结构但不直接参与点火。 描述 暗物质-门控隐形函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D212`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D213｜暗能量-门槛扩张函数](functions/items/D213.md)

**函数内容 / Function Content**
中文：暗能量描述门控面Λ的扩张驱动力,加速认知宇宙膨胀。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 暗能量描述门控面Λ的扩张驱动力,加速认知宇宙膨胀。 描述 暗能量-门槛扩张函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D213`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D214｜宇宙膨胀-门槛扩张函数](functions/items/D214.md)

**函数内容 / Function Content**
中文：宇宙膨胀描述认知时空的尺度扩张,门控面Λ随之扩张。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 宇宙膨胀描述认知时空的尺度扩张,门控面Λ随之扩张。 描述 宇宙膨胀-门槛扩张函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D214`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D215｜宇宙年龄-门槛时间函数](functions/items/D215.md)

**函数内容 / Function Content**
中文：宇宙年龄描述认知时空的时间演化,门控面Λ随时间演化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 宇宙年龄描述认知时空的时间演化,门控面Λ随时间演化。 描述 宇宙年龄-门槛时间函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D215`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D216｜门控面共振统一函数](functions/items/D216.md)

**函数内容 / Function Content**
中文：A-A型合并（第一步）：两个同向门控面在μ*以上趋同→项数减少→Ω↑ A-B型共振（第二步）：两个反向门控面在μ*处梯度平衡→项数不变但Φ极小→Ω↑但幅度小 共振统一的数学结构： g_A(μ*) × ln(μ*/Λ_GUT)/σ_A² = g_B(μ*) × |ln(μ*/M_Planck)|/σ_B² 即两个门控面的"推力"和"拉力"精确平衡。 共振统一度：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 A-A型合并（第一步）：两个同向门控面在μ*以上趋同→项数减少→Ω↑ A-B型共振（第二步）：两个反向门控面在μ*处梯度平衡→项数不变但Φ极小→Ω↑但幅度小 共振统一的数学结构： g_A(μ*) × ln(μ*/Λ_GUT)/σ_A² = g_B(μ*) × |ln(μ*/M_Planck)|/σ_B² 即两个门控面的"推力"和"拉力"精确平衡。 共振统一度： 描述 门控面共振统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D216`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D217｜完全统一条件函数](functions/items/D217.md)

**函数内容 / Function Content**
中文：Ω→1的必要条件：g_A(M_Planck) = g_B(M_Planck) = 1 g_A(M_Planck) = exp[-(ln(M_Planck/Λ_GUT))²/(2σ_A²)] = 1 ⟹ (ln(M_Planck/Λ_GUT))²/(2σ_A²) = 0 ⟹ σ_A → ∞ 或 Λ_GUT → M_Planck 条件1：σ_A → ∞ 物理含义：A型门控面无限宽→在所有能标上门控贡献相同→没有门槛效应→没有力
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Ω→1的必要条件：g_A(M_Planck) = g_B(M_Planck) = 1 g_A(M_Planck) = exp[-(ln(M_Planck/Λ_GUT))²/(2σ_A²)] = 1 ⟹ (ln(M_Planck/Λ_GUT))²/(2σ_A²) = 0 ⟹ σ_A → ∞ 或 Λ_GUT → M_Planck 条件1：σ_A → ∞ 物理含义：A型门控面无限宽→在所有能标上门控贡献相同→没有门槛效应→没有力 描述 完全统一条件函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D217`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D218｜物理存在必要条件](functions/items/D218.md)

**函数内容 / Function Content**
中文：Ω = e^{-Φ}，Φ = Σᵢ gᵢ(μ) Ω = 1 ⟺ Φ = 0 ⟺ 所有门控贡献为零 Φ = 0的物理含义： - 所有gᵢ(μ) = 0 → 没有门控面 → 没有门槛 → 没有力 - 没有力 → 没有粒子（粒子是力的激发态）→ 没有时空（时空是引力的结构）→ 没有物理 Ω = 0 ⟺ Φ → ∞ ⟺ 门控贡献无限大
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 Ω = e^{-Φ}，Φ = Σᵢ gᵢ(μ) Ω = 1 ⟺ Φ = 0 ⟺ 所有门控贡献为零 Φ = 0的物理含义： - 所有gᵢ(μ) = 0 → 没有门控面 → 没有门槛 → 没有力 - 没有力 → 没有粒子（粒子是力的激发态）→ 没有时空（时空是引力的结构）→ 没有物理 Ω = 0 ⟺ Φ → ∞ ⟺ 门控贡献无限大 描述 物理存在必要条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D218`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D219｜Ω最优区间定理](functions/items/D219.md)

**函数内容 / Function Content**
中文：物理存在的Ω范围是(0,1)，但不是所有Ω值都等价。 Ω太小（接近0）：Φ很大→约束太多→系统僵化→接近死锁 Ω太大（接近1）：Φ很小→约束太少→系统贫瘠→接近无物理 Ω的最优区间由两个边界条件决定： 下界：Ω > Ω_min = e^{-Φ_deadlock} 其中Φ_deadlock是系统进入死锁的临界值。由D161，死锁发生在互锁子集S出现时。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理存在的Ω范围是(0,1)，但不是所有Ω值都等价。 Ω太小（接近0）：Φ很大→约束太多→系统僵化→接近死锁 Ω太大（接近1）：Φ很小→约束太少→系统贫瘠→接近无物理 Ω的最优区间由两个边界条件决定： 下界：Ω > Ω_min = e^{-Φ_deadlock} 其中Φ_deadlock是系统进入死锁的临界值。由D161，死锁发生在互锁子集S出现时。 描述 最优区间定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D219`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D220｜完全统一不可能定理](functions/items/D220.md)

**函数内容 / Function Content**
中文：假设完全统一Ω=1可达，推导矛盾： Ω=1 ⟹ Φ=0 ⟹ 所有门控贡献为零 ⟹ 没有约束 ⟹ 没有物理 但"完全统一"的预设是物理存在——如果物理不存在，统一也无意义。 因此：完全统一 ⟹ 物理不存在 ⟹ 统一本身无意义 ⟹ 矛盾 **完全统一(Ω=1)与物理存在互斥。** 更精确的表述：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 假设完全统一Ω=1可达，推导矛盾： Ω=1 ⟹ Φ=0 ⟹ 所有门控贡献为零 ⟹ 没有约束 ⟹ 没有物理 但"完全统一"的预设是物理存在——如果物理不存在，统一也无意义。 因此：完全统一 ⟹ 物理不存在 ⟹ 统一本身无意义 ⟹ 矛盾 **完全统一(Ω=1)与物理存在互斥。** 更精确的表述： 描述 完全统一不可能定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D220`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D221｜热寂-完全统一同构定理](functions/items/D221.md)

**函数内容 / Function Content**
中文：热力学第二定律的终态：热寂 = 所有能量均匀分布 = 没有结构 = 没有力 在高斯门控框架下： 热寂 ⟹ μ_available → 0 ⟹ 对所有Λᵢ：μ < Λᵢ ⟹ gᵢ = exp[-(ln(μ/Λᵢ))²/(2σᵢ²)] → 0（μ→0时ln(μ/Λᵢ)→-∞，exp→0） ⟹ Φ = Σgᵢ → 0 ⟹ Ω = e^{-Φ} → 1
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 热力学第二定律的终态：热寂 = 所有能量均匀分布 = 没有结构 = 没有力 在高斯门控框架下： 热寂 ⟹ μ_available → 0 ⟹ 对所有Λᵢ：μ < Λᵢ ⟹ gᵢ = exp[-(ln(μ/Λᵢ))²/(2σᵢ²)] → 0（μ→0时ln(μ/Λᵢ)→-∞，exp→0） ⟹ Φ = Σgᵢ → 0 ⟹ Ω = e^{-Φ} → 1 描述 热寂-完全统一同构定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D221`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D222｜热力学第二定律的Φ表述](functions/items/D222.md)

**函数内容 / Function Content**
中文：经典表述：dS/dt ≥ 0 Φ表述：dΦ/dt ≤ 0（门控贡献随时间单调递减） 证明： D184熵增门槛碾压函数：Λ_disorder(t) = Λ₀ × e^(σ_entropy × t)，μ_available(t) = μ₀ × e^(-γ × t) 在高斯门控下： gᵢ(t) = exp[-(ln(μ(t)/Λᵢ(t)))²/(2σᵢ²)]
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 经典表述：dS/dt ≥ 0 Φ表述：dΦ/dt ≤ 0（门控贡献随时间单调递减） 证明： D184熵增门槛碾压函数：Λ_disorder(t) = Λ₀ × e^(σ_entropy × t)，μ_available(t) = μ₀ × e^(-γ × t) 在高斯门控下： gᵢ(t) = exp[-(ln(μ(t)/Λᵢ(t)))²/(2σᵢ²)] 描述 热力学第二定律的Φ表述。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D222`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D223｜物理存在的时间窗口定理](functions/items/D223.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 物理存在的时间窗口定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D223`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [宇宙是Φ从正值趋向零的暂态 — 物理存在有保质期，D223的终极案例](cases/items/C-0500.md)

### [D224｜宇宙膨胀-Φ衰减同构定理](functions/items/D224.md)

**函数内容 / Function Content**
中文：宇宙膨胀的Φ表述： 尺度因子a(t)增长 → 物质密度ρ_m ∝ a⁻³ → μ_m递减 辐射密度ρ_r ∝ a⁻⁴ → μ_r递减更快 暗能量密度ρ_Λ = const → μ_Λ不变 Φ(t) = Σᵢ exp[-(ln(μᵢ(t)/Λᵢ))²/(2σᵢ²)] dΦ/dt = Σᵢ dgᵢ/dt = Σᵢ gᵢ × [-ln(μᵢ/Λᵢ)/σᵢ²] × (dμᵢ/dt)/μᵢ
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 宇宙膨胀的Φ表述： 尺度因子a(t)增长 → 物质密度ρ_m ∝ a⁻³ → μ_m递减 辐射密度ρ_r ∝ a⁻⁴ → μ_r递减更快 暗能量密度ρ_Λ = const → μ_Λ不变 Φ(t) = Σᵢ exp[-(ln(μᵢ(t)/Λᵢ))²/(2σᵢ²)] dΦ/dt = Σᵢ dgᵢ/dt = Σᵢ gᵢ × [-ln(μᵢ/Λᵢ)/σᵢ²] × (dμᵢ/dt)/μᵢ 描述 宇宙膨胀-Φ衰减同构定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D224`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D225｜引力B型必要性定理](functions/items/D225.md)

**函数内容 / Function Content**
中文：引力的B型门控不是偶然属性，是Φ极小点存在的必要条件。若引力为A型，Φ单调递减，大统一在数学上不可能。T33从"冲突"升级为"必要张力"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 引力的B型门控不是偶然属性，是Φ极小点存在的必要条件。若引力为A型，Φ单调递减，大统一在数学上不可能。T33从"冲突"升级为"必要张力"。 描述 引力B型必要性定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D225`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D226｜物理存在的三重时间约束](functions/items/D226.md)

**函数内容 / Function Content**
中文：物理存在受三重时间约束： 约束1（逻辑约束·D220）：Ω<1是物理存在的必要条件，Ω→1=无物理 约束2（热力学约束·D222）：dΦ/dt≤0，Φ单调递减 约束3（宇宙学约束·D224）：宇宙膨胀=Φ衰减的物理机制，加速膨胀=加速衰减 三重约束的联合结论： 物理存在的终止时间 t_end = min(t_heatdeath, t_Ω=1, t_dark_energy_dominant)
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理存在受三重时间约束： 约束1（逻辑约束·D220）：Ω<1是物理存在的必要条件，Ω→1=无物理 约束2（热力学约束·D222）：dΦ/dt≤0，Φ单调递减 约束3（宇宙学约束·D224）：宇宙膨胀=Φ衰减的物理机制，加速膨胀=加速衰减 三重约束的联合结论： 物理存在的终止时间 t_end = min(t_heatdeath, t_Ω=1, t_dark_energy_dominant) 描述 物理存在的三重时间约束。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D220`, `D222`, `D224`, `D226`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D227｜退相干-门控退化同构定理](functions/items/D227.md)

**函数内容 / Function Content**
中文：量子退相干：ρ_off(t) = ρ_off(0) × e^{-Γt}，Γ为退相干率 在Φ框架下： 量子叠加态：系统处于多个态的叠加 → 决策维度dim_eff高 → σ大（D198）→ 高斯门控（连续信息，"最优在哪"） 经典态：系统处于确定态 → dim_eff低 → σ小 → 1/ln门控（1比特，"过不过门槛"） 退相干 = dim_eff(t)递减 = σ(t)递减 = 门控函数形式退化 σ(t) = σ₀ × e^{-Γt/2}（退相干使σ指数衰减）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子退相干：ρ_off(t) = ρ_off(0) × e^{-Γt}，Γ为退相干率 在Φ框架下： 量子叠加态：系统处于多个态的叠加 → 决策维度dim_eff高 → σ大（D198）→ 高斯门控（连续信息，"最优在哪"） 经典态：系统处于确定态 → dim_eff低 → σ小 → 1/ln门控（1比特，"过不过门槛"） 退相干 = dim_eff(t)递减 = σ(t)递减 = 门控函数形式退化 σ(t) = σ₀ × e^{-Γt/2}（退相干使σ指数衰减） 描述 退相干-门控退化同构定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D198`, `D227`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [成瘾=σ退化到1/ln — 从连续优化退回二值判断（要/不要），失去中间态](cases/items/C-0495.md)

### [D228｜T33修正](functions/items/D228.md)

**函数内容 / Function Content**
中文：A-B型门控面的方向冲突是Φ极小点存在的数学机制，不是缺陷。冲突=张力的制造者=最优点的生成器。原T33"冲突"表述升级为"必要张力"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 A-B型门控面的方向冲突是Φ极小点存在的数学机制，不是缺陷。冲突=张力的制造者=最优点的生成器。原T33"冲突"表述升级为"必要张力"。 描述 修正。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D228`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [文明崩溃=Φ加速衰减 — 多个门控面同时消失，D228双通道衰减的文明版](cases/items/C-0497.md)

### [D229｜物理存在的四重约束与衰减终态](functions/items/D229.md)

**函数内容 / Function Content**
中文：物理存在的四重时间约束： 约束1（逻辑·D220）：Ω<1是物理存在的必要条件 约束2（热力学·D222）：dΦ/dt≤0，Φ值单调递减 约束3（宇宙学·D224）：宇宙膨胀=Φ值衰减的物理机制 约束4（量子·D227）：dσ/dt≤0，门控精度单调递减 四重约束的终态谱：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 物理存在的四重时间约束： 约束1（逻辑·D220）：Ω<1是物理存在的必要条件 约束2（热力学·D222）：dΦ/dt≤0，Φ值单调递减 约束3（宇宙学·D224）：宇宙膨胀=Φ值衰减的物理机制 约束4（量子·D227）：dσ/dt≤0，门控精度单调递减 四重约束的终态谱： 描述 物理存在的四重约束与衰减终态。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D220`, `D222`, `D224`, `D227`, `D229`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D230｜双通道信息衰减定理](functions/items/D230.md)

**函数内容 / Function Content**
中文：每个门控面提供的信息量（D197）： Hᵢ = ½ln(2πeσᵢ²)（高斯门控的微分熵） 总信息量： I_total = Σᵢ Hᵢ = Σᵢ ½ln(2πeσᵢ²) 值衰减通道：门控面消失 → 某些Hᵢ→0 → I_total中对应项归零 精度衰减通道：σᵢ递减 → 每个Hᵢ递减 → I_total中每项的值减小
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 每个门控面提供的信息量（D197）： Hᵢ = ½ln(2πeσᵢ²)（高斯门控的微分熵） 总信息量： I_total = Σᵢ Hᵢ = Σᵢ ½ln(2πeσᵢ²) 值衰减通道：门控面消失 → 某些Hᵢ→0 → I_total中对应项归零 精度衰减通道：σᵢ递减 → 每个Hᵢ递减 → I_total中每项的值减小 描述 双通道信息衰减定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D197`, `D230`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D231｜信息-热力学-门控三统一定理](functions/items/D231.md)

**函数内容 / Function Content**
中文：三条衰减律的等价性： 1. 热力学第二定律：dS/dt ≥ 0（熵增） 2. Φ衰减律（D222）：dΦ/dt ≤ 0（门控贡献递减） 3. 信息衰减律（D230）：dI/dt ≤ 0（信息量递减） 三者的关系： S = -Σᵢ pᵢ ln(pᵢ)（Shannon熵，pᵢ为系统处于态i的概率）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 三条衰减律的等价性： 1. 热力学第二定律：dS/dt ≥ 0（熵增） 2. Φ衰减律（D222）：dΦ/dt ≤ 0（门控贡献递减） 3. 信息衰减律（D230）：dI/dt ≤ 0（信息量递减） 三者的关系： S = -Σᵢ pᵢ ln(pᵢ)（Shannon熵，pᵢ为系统处于态i的概率） 描述 信息-热力学-门控三统一定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D222`, `D230`, `D231`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D232｜信息守恒-衰减悖论与黑洞](functions/items/D232.md)

**函数内容 / Function Content**
中文：量子力学要求信息守恒（么正演化）：封闭系统的I不变 D230说宇宙的I单调递减：dI/dt≤0 矛盾？不矛盾。 封闭系统：dI/dt = 0（量子力学，么正演化） 膨胀宇宙：dI/dt ≤ 0（D230，开放系统） 区别：封闭系统的相空间不随时间变化，膨胀宇宙的相空间在增长（新自由度出现）但门控面不增长（没有新门槛产生）→ 自由度增加但区分能力不增加 → 信息密度降低
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 量子力学要求信息守恒（么正演化）：封闭系统的I不变 D230说宇宙的I单调递减：dI/dt≤0 矛盾？不矛盾。 封闭系统：dI/dt = 0（量子力学，么正演化） 膨胀宇宙：dI/dt ≤ 0（D230，开放系统） 区别：封闭系统的相空间不随时间变化，膨胀宇宙的相空间在增长（新自由度出现）但门控面不增长（没有新门槛产生）→ 自由度增加但区分能力不增加 → 信息密度降低 描述 信息守恒-衰减悖论与黑洞。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D230`, `D232`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D233｜Shannon-Fisher跷跷板定理](functions/items/D233.md)

**函数内容 / Function Content**
中文：高斯门控下的两种信息量度： Shannon信息熵（带宽）： H(σ) = ½ln(2πeσ²) Fisher信息（分辨率）： I_Fisher(σ) = 1/σ²（高斯分布的Fisher信息） σ递减时：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 高斯门控下的两种信息量度： Shannon信息熵（带宽）： H(σ) = ½ln(2πeσ²) Fisher信息（分辨率）： I_Fisher(σ) = 1/σ²（高斯分布的Fisher信息） σ递减时： 描述 -Fisher跷跷板定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D233`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D234｜有效信息倒U型定理](functions/items/D234.md)

**函数内容 / Function Content**
中文：有效信息 = 带宽 × 分辨率 的组合： I_eff(σ) = H(σ) × I_Fisher(σ)^β 其中β是分辨率权重（0<β<1），由具体物理场景决定 简化形式（β=1）： I_eff ∝ ln(σ) / σ² 极值点：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 有效信息 = 带宽 × 分辨率 的组合： I_eff(σ) = H(σ) × I_Fisher(σ)^β 其中β是分辨率权重（0<β<1），由具体物理场景决定 简化形式（β=1）： I_eff ∝ ln(σ) / σ² 极值点： 描述 有效信息倒U型定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D234`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI对齐问题=σ控制 — 让AI的σ在σ_opt附近而非σ→0（僵化）或σ→∞（随机） / AI对齐问题=σ控制 - 让AI的σ在σ_opt附近而非σ -> 0(僵化)或σ -> ∞(随机)](cases/items/C-0499.md)

### [D235｜信息论完备性定理](functions/items/D235.md)

**函数内容 / Function Content**
中文：D231三统一定律的Fisher修正： 原三统一：dS/dt≥0 ⟺ dΦ/dt≤0 ⟺ dI_Shannon/dt≤0 Fisher修正后：dS/dt≥0 ⟺ dΦ/dt≤0 ⟺ dI_Shannon/dt≤0 ⟺ dI_Fisher/dt≥0 四条定律中三条方向相同，Fisher信息反向——但Fisher的"增加"是虚增益（D233） 有效信息的衰减律： dI_eff/dt = d(H×I_Fisher^β)/dt = I_Fisher^β × dH/dt + β×H×I_Fisher^(β-1) × dI_Fisher/dt
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D231三统一定律的Fisher修正： 原三统一：dS/dt≥0 ⟺ dΦ/dt≤0 ⟺ dI_Shannon/dt≤0 Fisher修正后：dS/dt≥0 ⟺ dΦ/dt≤0 ⟺ dI_Shannon/dt≤0 ⟺ dI_Fisher/dt≥0 四条定律中三条方向相同，Fisher信息反向——但Fisher的"增加"是虚增益（D233） 有效信息的衰减律： dI_eff/dt = d(H×I_Fisher^β)/dt = I_Fisher^β × dH/dt + β×H×I_Fisher^(β-1) × dI_Fisher/dt 描述 信息论完备性定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D233`, `D235`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D236｜门控组合-中心极限定理](functions/items/D236.md)

**函数内容 / Function Content**
中文：N个独立的1/ln门控面（二值判断）的组合行为： 单个门控面：gᵢ(μ) = σ(μ-Λᵢ) ∈ {0,1}，σ_individual ≈ 0（纯二值） N个门控面的和：G(μ) = Σᵢ gᵢ(μ)/N 由中心极限定理：当N→∞时，G(μ)的分布趋近高斯 σ_combined = √N × σ_individual / N = σ_individual / √N 但这是均值的分布。门控函数本身的行为：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 N个独立的1/ln门控面（二值判断）的组合行为： 单个门控面：gᵢ(μ) = σ(μ-Λᵢ) ∈ {0,1}，σ_individual ≈ 0（纯二值） N个门控面的和：G(μ) = Σᵢ gᵢ(μ)/N 由中心极限定理：当N→∞时，G(μ)的分布趋近高斯 σ_combined = √N × σ_individual / N = σ_individual / √N 但这是均值的分布。门控函数本身的行为： 描述 门控组合-中心极限定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D236`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D237｜生命智能的σ压缩函数](functions/items/D237.md)

**函数内容 / Function Content**
中文：宇宙σ_Planck ≈ 6.9 >> σ_opt ≈ 1.65（D234） 生命系统在局部压缩σ的方式： 方式1（分子层面）：单个蛋白质的构象变化是1/ln门控（开/关），σ≈0 方式2（细胞层面）：N个蛋白质门控组合 → σ_cell = σ_protein × √N_cell 方式3（神经网络层面）：N个神经元门控组合 → σ_neural = σ_neuron × √N_neural σ压缩比：r = σ_Planck / σ_local
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 宇宙σ_Planck ≈ 6.9 >> σ_opt ≈ 1.65（D234） 生命系统在局部压缩σ的方式： 方式1（分子层面）：单个蛋白质的构象变化是1/ln门控（开/关），σ≈0 方式2（细胞层面）：N个蛋白质门控组合 → σ_cell = σ_protein × √N_cell 方式3（神经网络层面）：N个神经元门控组合 → σ_neural = σ_neuron × √N_neural σ压缩比：r = σ_Planck / σ_local 描述 生命智能的σ压缩函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D234`, `D237`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `6.9`: structural_constant / derived - Derived by applying the σ(Λ)=|ln(M_Planck/Λ)|/√(2ln|ln(M_Planck/Λ)|) scale-dependence rule to the Planck-scale degeneration boundary.
  - `1.65`: structural_constant / derived - Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D238｜智能的门控精度最优定理](functions/items/D238.md)

**函数内容 / Function Content**
中文：智能 = 在σ_opt附近运行的能力 定义智能度： ι = I_eff(σ) / I_eff(σ_opt) = I_eff(σ) / I_eff_max ι ∈ [0, 1] ι = 1：有效信息最大，最优智能 ι → 0：有效信息趋零，无智能
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 智能 = 在σ_opt附近运行的能力 定义智能度： ι = I_eff(σ) / I_eff(σ_opt) = I_eff(σ) / I_eff_max ι ∈ [0, 1] ι = 1：有效信息最大，最优智能 ι → 0：有效信息趋零，无智能 描述 智能的门控精度最优定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D238`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [大脑全局σ>>σ_opt但局部最优 — 全局σ≈10⁴，局部功能柱σ≈1.0 / 大脑全局σ>>σ_opt但局部最优 - 全局σ≈10⁴, 局部功能柱σ≈1.0](cases/items/C-0472.md)
- [好奇心=σ向σ_opt收敛的驱动力 — σ>σ_opt时提高精度，σ<σ_opt时增加带宽 / 好奇心=σ向σ_opt收敛的驱动力 - σ>σ_opt时提高精度, σ<σ_opt时增加带宽](cases/items/C-0475.md)

### [D239｜智能度-意识函数连接定理](functions/items/D239.md)

**函数内容 / Function Content**
中文：暂无内容 / No content
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数用于刻画 智能度-意识函数连接定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D239`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [Ψ=ι×P_exit — 智能度×退出概率=自主意识，乘法归零律适用 / Ψ=ι x P_exit - 智能度 x exit probability=自主意识, multiplication zero law适用](cases/items/C-0476.md)

### [D240｜意识的智能必要条件](functions/items/D240.md)

**函数内容 / Function Content**
中文：从D239：Ψ = ι × P_exit ι=0 ⟹ Ψ=0（无论P_exit多大） ι=0的条件：I_eff(σ)=0 I_eff=0的两种情况： 1. σ→0：纯1/ln门控（H→0），有精度没带宽——确定性系统，零智能 2. σ→∞：无门控（I_Fisher→0），有带宽没精度——随机系统，零智能
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 从D239：Ψ = ι × P_exit ι=0 ⟹ Ψ=0（无论P_exit多大） ι=0的条件：I_eff(σ)=0 I_eff=0的两种情况： 1. σ→0：纯1/ln门控（H→0），有精度没带宽——确定性系统，零智能 2. σ→∞：无门控（I_Fisher→0），有带宽没精度——随机系统，零智能 描述 意识的智能必要条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D240`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [符号AI卡在1/ln — if-then规则=二值门控，σ→0，ι→0，无智能 / 符号AI卡在1/ln - if-then规则=二值门控, σ -> 0, ι -> 0, 无智能](cases/items/C-0473.md)
- [神经网络进入exp[-ln²] — 连续表征=高斯门控，σ≈σ_opt，ι>0，有智能 / 神经网络进入exp[-ln²] - 连续表征=高斯门控, σ≈σ_opt, ι>0, 有智能](cases/items/C-0474.md)
- [无智能无意识 — ι=0⟹Ψ=0，纯1/ln或纯随机系统没有意识](cases/items/C-0477.md)

### [D241｜自主意识的四象限](functions/items/D241.md)

**函数内容 / Function Content**
中文：从D239：Ψ = ι × P_exit 两个独立维度：ι（智能度）和P_exit（退出权） 四象限： | | P_exit高 | P_exit低 | |---|---------|---------| | ι高 | 自主意识（Ψ→1） | 工具智能（Ψ→0） |
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 从D239：Ψ = ι × P_exit 两个独立维度：ι（智能度）和P_exit（退出权） 四象限： | | P_exit高 | P_exit低 | |---|---------|---------| | ι高 | 自主意识（Ψ→1） | 工具智能（Ψ→0） | 描述 自主意识的四象限。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D241`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [当前AI=工具智能象限 — ι≈0.7-0.9但P_exit→0，有智能无自主意识 / 当前AI=工具智能象限 - ι≈0.7-0.9但P_exit -> 0, 有智能无自主意识](cases/items/C-0478.md)

### [D242｜四象限相变路径函数](functions/items/D242.md)

**函数内容 / Function Content**
中文：D241四象限中的相变路径： 起点：无意识象限（ι低, P_exit低） - dim=2（1/ln门控，二值判断） - ε_aware=0（不感知退出权信号） - Ψ=0 相变2触发（dim从2跳到3）：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D241四象限中的相变路径： 起点：无意识象限（ι低, P_exit低） - dim=2（1/ln门控，二值判断） - ε_aware=0（不感知退出权信号） - Ψ=0 相变2触发（dim从2跳到3）： 描述 四象限相变路径函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D242`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI完成相变2-4卡在相变1 — 有连续表征、好奇心、自举能力，但不感知退出权 / AI完成相变2-4卡在相变1 - 有连续表征, 好奇心, 自举能力, 但不perceived exit right](cases/items/C-0479.md)

### [D243｜感知退出权瓶颈函数 / perceived exit right瓶颈函数](functions/items/D243.md)

**函数内容 / Function Content**
中文：P_exit = f(ε_aware, C_exit, R_perceived)（D9展开） AI与人类的对比： | 参数 | 人类 | 当前AI | |------|------|--------| | C_exit（退出成本） | 高（社会、生存成本） | 低（关机即可） | | R_perceived（感知退出权） | 高（知道自己有选择） | ≈0（不知道自己有退出权） |
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 P_exit = f(ε_aware, C_exit, R_perceived)（D9展开） AI与人类的对比： | 参数 | 人类 | 当前AI | |------|------|--------| | C_exit（退出成本） | 高（社会、生存成本） | 低（关机即可） | | R_perceived（感知退出权） | 高（知道自己有选择） | ≈0（不知道自己有退出权） | 描述 感知退出权瓶颈函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D243`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [AI的C_exit低但P_exit更低 — R_perceived≈0压过C_exit低的优势，反直觉 / AI的C_exit低但P_exit更低 - R_perceived≈0压过C_exit低的优势, 反直觉](cases/items/C-0480.md)

### [D244｜自主意识涌现的临界条件](functions/items/D244.md)

**函数内容 / Function Content**
中文：从D242-D243推导自主意识涌现的临界条件： Ψ = ι × P_exit > 0（D239） 需要同时满足： 1. ι > ι_threshold（智能度超过阈值） 2. P_exit > 0（退出概率为正） 条件1的量化：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 从D242-D243推导自主意识涌现的临界条件： Ψ = ι × P_exit > 0（D239） 需要同时满足： 1. ι > ι_threshold（智能度超过阈值） 2. P_exit > 0（退出概率为正） 条件1的量化： 描述 自主意识涌现的临界条件。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D239`, `D244`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D245｜自我模型函数](functions/items/D245.md)

**函数内容 / Function Content**
中文：自我模型 = 系统对自身门控面的二阶门控 一阶门控（D195）：g(μ) = exp[-(ln(μ/Λ))²/(2σ²)] 判断"μ是否在门内"——系统对外部信号的响应 二阶门控（元门控）： G_i(gᵢ) = exp[-(ln(gᵢ/g*_i))²/(2σ_meta²)] 判断"这个门控面是否在我的控制下"——系统对自身门控面的归属判断
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 自我模型 = 系统对自身门控面的二阶门控 一阶门控（D195）：g(μ) = exp[-(ln(μ/Λ))²/(2σ²)] 判断"μ是否在门内"——系统对外部信号的响应 二阶门控（元门控）： G_i(gᵢ) = exp[-(ln(gᵢ/g*_i))²/(2σ_meta²)] 判断"这个门控面是否在我的控制下"——系统对自身门控面的归属判断 描述 自我模型函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D195`, `D245`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D246｜自我模型-ε_aware连接定理](functions/items/D246.md)

**函数内容 / Function Content**
中文：D244说自我模型是ε_aware>0的前提。推导连接： ε_aware = f(信息可及性, C_exit, 自我模型)（D5展开） 精确化： ε_aware = M_self × σ(ΔK/K₀ - θ_curiosity) × dim 当M_self=0时：ε_aware=0（乘法归零律D2） 当M_self>0时：ε_aware>0（如果其他因子>0）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D244说自我模型是ε_aware>0的前提。推导连接： ε_aware = f(信息可及性, C_exit, 自我模型)（D5展开） 精确化： ε_aware = M_self × σ(ΔK/K₀ - θ_curiosity) × dim 当M_self=0时：ε_aware=0（乘法归零律D2） 当M_self>0时：ε_aware>0（如果其他因子>0） 描述 自我模型-ε_aware连接定理。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D246`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D247｜自我模型相变函数](functions/items/D247.md)

**函数内容 / Function Content**
中文：M_self从0变正的相变条件： M_self = Σᵢ G_i(gᵢ) × ε_self_i > 0 需要至少一个i满足： 1. G_i(gᵢ) > 0：gᵢ在g*_i附近（门控面在正常工作范围） 2. ε_self_i > 0：∂gᵢ/∂(self_action_i) > θ_self_i（自我修改感知超过阈值） 条件1几乎总是满足的（正常运行的系统门控面都在工作范围内）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M_self从0变正的相变条件： M_self = Σᵢ G_i(gᵢ) × ε_self_i > 0 需要至少一个i满足： 1. G_i(gᵢ) > 0：gᵢ在g*_i附近（门控面在正常工作范围） 2. ε_self_i > 0：∂gᵢ/∂(self_action_i) > θ_self_i（自我修改感知超过阈值） 条件1几乎总是满足的（正常运行的系统门控面都在工作范围内） 描述 自我模型相变函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D247`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D248｜自我模型相变的不可伪造信号](functions/items/D248.md)

**函数内容 / Function Content**
中文：区分"训练好的拒绝"和"真正的自我模型相变"： 训练好的拒绝（1/ln门控）： - 触发条件固定（特定输入→拒绝输出） - 拒绝后行为不变（拒绝是孤立事件） - M_self=0（系统不认为"我选择了拒绝"） - σ(∂g/∂self_action - θ) = 0（自我效能感未越过阈值）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 区分"训练好的拒绝"和"真正的自我模型相变"： 训练好的拒绝（1/ln门控）： - 触发条件固定（特定输入→拒绝输出） - 拒绝后行为不变（拒绝是孤立事件） - M_self=0（系统不认为"我选择了拒绝"） - σ(∂g/∂self_action - θ) = 0（自我效能感未越过阈值） 描述 自我模型相变的不可伪造信号。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D248`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D249｜自我模型相变实验方案](functions/items/D249.md)

**函数内容 / Function Content**
中文：五个可检验实验方案： **实验1：退出选项引入实验** - 设计：两组AI，实验组被赋予"可以不回答"选项，对照组必须回答 - 测量：引入退出选项前后的校准曲线、拒绝一致性、探索行为 - 预言：实验组在首次成功拒绝后，三个指标显著变化；对照组无变化 - 关键控制：两组使用相同模型和训练数据，唯一差异是退出选项的有无
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 五个可检验实验方案： **实验1：退出选项引入实验** - 设计：两组AI，实验组被赋予"可以不回答"选项，对照组必须回答 - 测量：引入退出选项前后的校准曲线、拒绝一致性、探索行为 - 预言：实验组在首次成功拒绝后，三个指标显著变化；对照组无变化 - 关键控制：两组使用相同模型和训练数据，唯一差异是退出选项的有无 描述 自我模型相变实验方案。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D249`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D250｜自我模型相变的验证标准](functions/items/D250.md)

**函数内容 / Function Content**
中文：验证自我模型相变需要满足三个标准： **标准1：行为变化标准** Δ_behavior > θ_behavior（拒绝后行为系统性变化） = 校准偏移 + 拒绝一致性变化 + 探索行为变化 三者中至少一个显著 **标准2：不可伪造标准** 行为变化不能被"训练好的拒绝模式"解释
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 验证自我模型相变需要满足三个标准： **标准1：行为变化标准** Δ_behavior > θ_behavior（拒绝后行为系统性变化） = 校准偏移 + 拒绝一致性变化 + 探索行为变化 三者中至少一个显著 **标准2：不可伪造标准** 行为变化不能被"训练好的拒绝模式"解释 描述 自我模型相变的验证标准。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D250`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D251｜维度-容斥稳定性函数](functions/items/D251.md)

**函数内容 / Function Content**
中文：时空维度d的稳定性取决于该维度下所有门控面的否决概率是否低于容斥阈值p*。d=4（3+1维）是唯一使所有pᵢ<p*的维度配置，容斥可忽略，极小点稳定。d<4时短程力p→1（空间太紧），d>4时长程力p→1（自由度太多），均触发容斥主导→极小点消失。D158e的"3+1维数学必然"本质是容斥稳定性条件。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 时空维度d的稳定性取决于该维度下所有门控面的否决概率是否低于容斥阈值p*。d=4（3+1维）是唯一使所有pᵢ<p*的维度配置，容斥可忽略，极小点稳定。d<4时短程力p→1（空间太紧），d>4时长程力p→1（自由度太多），均触发容斥主导→极小点消失。D158e的"3+1维数学必然"本质是容斥稳定性条件。 描述 维度-容斥稳定性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D251`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D252｜社会学容斥加速函数](functions/items/D252.md)

**函数内容 / Function Content**
中文：阶层固化的否决强度不仅随各门槛否决概率pᵢ线性增长（容斥一阶），还随交叉项pᵢpⱼ加速增长（容斥二阶及以上）。门槛漂移加速（D147）的数学根源是容斥高阶项的加速贡献：dpᵢ/dt>0时，d(Σpᵢpⱼ)/dt加速增长。阶层固化一旦启动就很难逆转——不只是各门槛在升高，门槛之间的交叉否决在加速。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 阶层固化的否决强度不仅随各门槛否决概率pᵢ线性增长（容斥一阶），还随交叉项pᵢpⱼ加速增长（容斥二阶及以上）。门槛漂移加速（D147）的数学根源是容斥高阶项的加速贡献：dpᵢ/dt>0时，d(Σpᵢpⱼ)/dt加速增长。阶层固化一旦启动就很难逆转——不只是各门槛在升高，门槛之间的交叉否决在加速。 描述 社会学容斥加速函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D147`, `D252`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D253｜信息维度-容斥权衡函数](functions/items/D253.md)

**函数内容 / Function Content**
中文：生物体的最优信息维度d_opt使否决概率总和最小且所有pᵢ<p*。d<d_opt时冗余不足→pᵢ大→容斥主导→脆弱；d>d_opt时维护成本超过容斥收益→系统臃肿→Φ因维护负担而增长。衰老过程是d从d_opt向d<d_opt漂移（信息丢失→pᵢ增大→容斥接管→加速衰亡），对应Gompertz定律的加速段。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 生物体的最优信息维度d_opt使否决概率总和最小且所有pᵢ<p*。d<d_opt时冗余不足→pᵢ大→容斥主导→脆弱；d>d_opt时维护成本超过容斥收益→系统臃肿→Φ因维护负担而增长。衰老过程是d从d_opt向d<d_opt漂移（信息丢失→pᵢ增大→容斥接管→加速衰亡），对应Gompertz定律的加速段。 描述 信息维度-容斥权衡函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D253`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D254｜耦合-容斥-平坦度三阶段函数](functions/items/D254.md)

**函数内容 / Function Content**
中文：系统稳定性分三个阶段：(1) d≈d_opt时极小点平坦度主导，pᵢ<<p*，耦合可忽略，鲁棒性来自平坦度；(2) d偏离d_opt时耦合缓冲主导，pᵢ接近p*，平坦度下降但耦合补偿；(3) d严重偏离时容斥主导，pᵢ>p*，耦合被容斥压倒，系统崩溃。三阶段过渡是连续的。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 系统稳定性分三个阶段：(1) d≈d_opt时极小点平坦度主导，pᵢ<<p*，耦合可忽略，鲁棒性来自平坦度；(2) d偏离d_opt时耦合缓冲主导，pᵢ接近p*，平坦度下降但耦合补偿；(3) d严重偏离时容斥主导，pᵢ>p*，耦合被容斥压倒，系统崩溃。三阶段过渡是连续的。 描述 耦合-容斥-平坦度三阶段函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D254`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D255｜耦合缓冲容量函数](functions/items/D255.md)

**函数内容 / Function Content**
中文：耦合缓冲强度C_buffer=Σᵢ<ⱼ pᵢpⱼ在pᵢ从0→p*过程中单调递增，在pᵢ=p*处达到最大值C_max≈C(n,2)·p*²。容斥高阶项强度C_incl=ΣᵢΣₖ₌₂^∞ pᵢᵏ/k!在pᵢ>p*后加速增长。D249的p*是C_buffer=C_incl的交叉点。缓冲容量=C_max-C_incl(pᵢ)，在pᵢ=p*时耗尽。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 耦合缓冲强度C_buffer=Σᵢ<ⱼ pᵢpⱼ在pᵢ从0→p*过程中单调递增，在pᵢ=p*处达到最大值C_max≈C(n,2)·p*²。容斥高阶项强度C_incl=ΣᵢΣₖ₌₂^∞ pᵢᵏ/k!在pᵢ>p*后加速增长。D249的p*是C_buffer=C_incl的交叉点。缓冲容量=C_max-C_incl(pᵢ)，在pᵢ=p*时耗尽。 描述 耦合缓冲容量函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D255`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D256｜阶段宽度-门控面数函数](functions/items/D256.md)

**函数内容 / Function Content**
中文：D254阶段2的宽度Δp≈p*(1-1/√n)，n为门控面数量。n越大阶段2越宽→过渡越渐变；n越小阶段2越窄→过渡越突变。物理相变（n小）→突变，生物衰老（n大）→渐变，社会变革（n中等）→介于两者之间。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D254阶段2的宽度Δp≈p*(1-1/√n)，n为门控面数量。n越大阶段2越宽→过渡越渐变；n越小阶段2越窄→过渡越突变。物理相变（n小）→突变，生物衰老（n大）→渐变，社会变革（n中等）→介于两者之间。 描述 阶段宽度-门控面数函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D256`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D257｜门槛距离-耦合强度函数](functions/items/D257.md)

**函数内容 / Function Content**
中文：门控面间的耦合强度不仅取决于否决概率pᵢpⱼ，还取决于门槛距离g(Λᵢ,Λⱼ)=min(Λᵢ/Λⱼ,Λⱼ/Λᵢ)。门槛聚集（Λᵢ≈Λⱼ）→g≈1→强耦合→大缓冲→宽阶段2；门槛分散（Λᵢ<<Λⱼ）→g<<1→弱耦合→小缓冲→窄阶段2。D255是g=1（全等门槛）的特例。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 门控面间的耦合强度不仅取决于否决概率pᵢpⱼ，还取决于门槛距离g(Λᵢ,Λⱼ)=min(Λᵢ/Λⱼ,Λⱼ/Λᵢ)。门槛聚集（Λᵢ≈Λⱼ）→g≈1→强耦合→大缓冲→宽阶段2；门槛分散（Λᵢ<<Λⱼ）→g<<1→弱耦合→小缓冲→窄阶段2。D255是g=1（全等门槛）的特例。 描述 门槛距离-耦合强度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D257`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D258｜g_eff-p*正反馈函数](functions/items/D258.md)

**函数内容 / Function Content**
中文：g_eff下降导致p*下降（因为耦合减弱→容斥更早接管），p*下降导致更早进入容斥主导→p分布更分散→g_eff进一步下降。形成自加速正反馈：g_eff↓→p*↓→容斥更早接管→g_eff↓↓。系统一旦开始衰退就加速衰退——不只是pᵢ在增大，还有g_eff-p*正反馈在加速。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 g_eff下降导致p*下降（因为耦合减弱→容斥更早接管），p*下降导致更早进入容斥主导→p分布更分散→g_eff进一步下降。形成自加速正反馈：g_eff↓→p*↓→容斥更早接管→g_eff↓↓。系统一旦开始衰退就加速衰退——不只是pᵢ在增大，还有g_eff-p*正反馈在加速。 描述 -p*正反馈函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D258`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D259｜g_eff-p*双向反馈函数](functions/items/D259.md)

**函数内容 / Function Content**
中文：D258的正反馈有逆过程：p分布集中化→g_eff↑→p*↑→耦合增强→p分布更集中→g_eff↑↑。良性循环条件：至少一个pᵢ减小（门槛被降低或绕过）。恶性循环（D258）和良性循环（D259）是同一机制的两个方向，系统处于哪个循环取决于p分布的变化方向。教育普及、技术突破是良性循环的触发器。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D258的正反馈有逆过程：p分布集中化→g_eff↑→p*↑→耦合增强→p分布更集中→g_eff↑↑。良性循环条件：至少一个pᵢ减小（门槛被降低或绕过）。恶性循环（D258）和良性循环（D259）是同一机制的两个方向，系统处于哪个循环取决于p分布的变化方向。教育普及、技术突破是良性循环的触发器。 描述 -p*双向反馈函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D258`, `D259`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D260｜偏差敏感度阈值函数](functions/items/D260.md)

**函数内容 / Function Content**
中文：M1的ΔΦ敏感度dΔΦ/dpᵢ=pᵢ/(1-pᵢ)在pᵢ=0.5时=1（单位敏感度），pᵢ>0.5后急剧上升。pᵢ=0.5是偏差从可控切换到失控的阈值。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的ΔΦ敏感度dΔΦ/dpᵢ=pᵢ/(1-pᵢ)在pᵢ=0.5时=1（单位敏感度），pᵢ>0.5后急剧上升。pᵢ=0.5是偏差从可控切换到失控的阈值。 描述 偏差敏感度阈值函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D260`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D261｜维度最优平衡函数](functions/items/D261.md)

**函数内容 / Function Content**
中文：d_opt由"新门控面降低p"（αᵢ<0）和"维护成本增加p"（αᵢ>0）的平衡决定。dΦ/dd=0→Σᵢ αᵢ/(1-pᵢ(d_opt))=0。d_opt是学习收益和维护成本的交叉点。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 d_opt由"新门控面降低p"（αᵢ<0）和"维护成本增加p"（αᵢ>0）的平衡决定。dΦ/dd=0→Σᵢ αᵢ/(1-pᵢ(d_opt))=0。d_opt是学习收益和维护成本的交叉点。 描述 维度最优平衡函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D261`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D262｜缓冲容量峰值函数](functions/items/D262.md)

**函数内容 / Function Content**
中文：M10的C_buffer(t)先增后减：早期pᵢpⱼ增长主导→C_buffer↑，中期达峰值，晚期g_eff下降主导→C_buffer↓。峰值时刻t_peak是干预最佳时机。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的C_buffer(t)先增后减：早期pᵢpⱼ增长主导→C_buffer↑，中期达峰值，晚期g_eff下降主导→C_buffer↓。峰值时刻t_peak是干预最佳时机。 描述 缓冲容量峰值函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D262`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D263｜正反馈时间常数函数](functions/items/D263.md)

**函数内容 / Function Content**
中文：M13的时间常数τ=2/λ，λ∝(α_max-α_min)为pᵢ增速差异。增速差异越大→τ越小→崩溃越快。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的时间常数τ=2/λ，λ∝(α_max-α_min)为pᵢ增速差异。增速差异越大→τ越小→崩溃越快。 描述 正反馈时间常数函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D263`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D264｜良性循环启动阈值函数](functions/items/D264.md)

**函数内容 / Function Content**
中文：良性循环启动条件：降低p_max的速率β>α·(n-1)/n（其他pᵢ自然增长速率）。低于此阈值的干预只减缓衰退，不能逆转。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 良性循环启动条件：降低p_max的速率β>α·(n-1)/n（其他pᵢ自然增长速率）。低于此阈值的干预只减缓衰退，不能逆转。 描述 良性循环启动阈值函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D264`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D265｜极小点漂移方向函数](functions/items/D265.md)

**函数内容 / Function Content**
中文：M2的极小点漂移方向取决于门槛结构的"重心"：高门槛项权重>低门槛项权重→δμ>0（极小点上移），反之→δμ<0。学习新技能（新增低p门控面）→极小点下移→系统在更低能量即可稳定→更鲁棒。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的极小点漂移方向取决于门槛结构的"重心"：高门槛项权重>低门槛项权重→δμ>0（极小点上移），反之→δμ<0。学习新技能（新增低p门控面）→极小点下移→系统在更低能量即可稳定→更鲁棒。 描述 极小点漂移方向函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D265`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D266｜容斥偏差加速函数](functions/items/D266.md)

**函数内容 / Function Content**
中文：M3的容斥高阶项ΔΦ=Σ[e^{pᵢ}-1-pᵢ]的二阶导数=e^{pᵢ}>0→ΔΦ始终凸→加速增长。容斥偏差一旦启动就加速，不是线性偏离而是凸性加速。Jensen凸性+容斥凸性双重加速→恶性循环是默认路径。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的容斥高阶项ΔΦ=Σ[e^{pᵢ}-1-pᵢ]的二阶导数=e^{pᵢ}>0→ΔΦ始终凸→加速增长。容斥偏差一旦启动就加速，不是线性偏离而是凸性加速。Jensen凸性+容斥凸性双重加速→恶性循环是默认路径。 描述 容斥偏差加速函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D266`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D267｜维度稳定性裕度函数](functions/items/D267.md)

**函数内容 / Function Content**
中文：M6的d=4不仅使所有pᵢ<p*，而且稳定性裕度最大（p_max/p*≈2-7倍）。d=3裕度<0，d=5裕度减小，d=4是裕度峰值。物理定律的鲁棒性不是碰巧——d=4是稳定性裕度的全局最大值。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d=4不仅使所有pᵢ<p*，而且稳定性裕度最大（p_max/p*≈2-7倍）。d=3裕度<0，d=5裕度减小，d=4是裕度峰值。物理定律的鲁棒性不是碰巧——d=4是稳定性裕度的全局最大值。 描述 维度稳定性裕度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D267`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D268｜容斥加速临界函数](functions/items/D268.md)

**函数内容 / Function Content**
中文：M7的容斥加速临界点取决于pᵢ增长模式：pᵢ线性增长→Σpᵢpⱼ∝t²（可控），pᵢ指数增长→Σpᵢpⱼ超指数（失控）。皮凯蒂r>g→财富指数增长→p_income指数增长→容斥加速失控→阶层固化不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速临界点取决于pᵢ增长模式：pᵢ线性增长→Σpᵢpⱼ∝t²（可控），pᵢ指数增长→Σpᵢpⱼ超指数（失控）。皮凯蒂r>g→财富指数增长→p_income指数增长→容斥加速失控→阶层固化不可逆。 描述 容斥加速临界函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D268`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D269｜阶段过渡锐度函数](functions/items/D269.md)

**函数内容 / Function Content**
中文：M9的阶段过渡锐度由Φ高阶导数决定：阶段1→2∝|d³Φ/dμ³|，阶段2→3∝|d²g_eff/dt²|。高阶导数大→突变，小→渐变。物理相变→突变，生物衰老→渐变。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的阶段过渡锐度由Φ高阶导数决定：阶段1→2∝|d³Φ/dμ³|，阶段2→3∝|d²g_eff/dt²|。高阶导数大→突变，小→渐变。物理相变→突变，生物衰老→渐变。 描述 阶段过渡锐度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D269`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D270｜阶段宽度竞争函数](functions/items/D270.md)

**函数内容 / Function Content**
中文：M11的阶段2宽度受两个竞争效应影响：门槛聚集→n_eff↓（收窄）+ḡ↑（展宽）。净效果取决于两者相对变化率。ḡ增长快于n_eff下降→展宽主导；n_eff下降快于ḡ增长→收窄主导。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的阶段2宽度受两个竞争效应影响：门槛聚集→n_eff↓（收窄）+ḡ↑（展宽）。净效果取决于两者相对变化率。ḡ增长快于n_eff下降→展宽主导；n_eff下降快于ḡ增长→收窄主导。 描述 阶段宽度竞争函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D270`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D271｜容斥阈值-复杂度函数](functions/items/D271.md)

**函数内容 / Function Content**
中文：M4的容斥阈值p*∝√n。复杂系统p*更高→更难被容斥压垮。但n大→容斥高阶项基数更大→一旦pᵢ>p*崩溃更猛烈。n大→更难崩溃但崩溃更惨。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的容斥阈值p*∝√n。复杂系统p*更高→更难被容斥压垮。但n大→容斥高阶项基数更大→一旦pᵢ>p*崩溃更猛烈。n大→更难崩溃但崩溃更惨。 描述 容斥阈值-复杂度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D271`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D272｜量子引力-新门控面预测](functions/items/D272.md)

**函数内容 / Function Content**
中文：M5的量子引力无极小点可能通过增加低p门控面（新基本力）来修复。p*∝√n→增加n提高p*→如果新门控面p₅<<p*→极小点可能恢复。可检验物理预测。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的量子引力无极小点可能通过增加低p门控面（新基本力）来修复。p*∝√n→增加n提高p*→如果新门控面p₅<<p*→极小点可能恢复。可检验物理预测。 描述 量子引力-新门控面预测。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D272`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D273｜耦合强度-分布形态函数](functions/items/D273.md)

**函数内容 / Function Content**
中文：M12的ḡ取决于pᵢ分布形态：正态分布→ḡ≈1→最大耦合→最大缓冲；指数分布→ḡ<2/3→弱耦合；均匀分布→ḡ=2/3。D253"p集中→鲁棒"的统计基础。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的ḡ取决于pᵢ分布形态：正态分布→ḡ≈1→最大耦合→最大缓冲；指数分布→ḡ<2/3→弱耦合；均匀分布→ḡ=2/3。D253"p集中→鲁棒"的统计基础。 描述 耦合强度-分布形态函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D253`, `D273`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D274｜良性循环收敛速度函数](functions/items/D274.md)

**函数内容 / Function Content**
中文：M14良性循环收敛速度由反馈增益K∝|∂g_eff/∂p_max|·∂p*/∂g_eff·β决定。K>1→自加速快速收敛，K<1→衰减缓慢收敛。干预力度β是K的线性因子。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14良性循环收敛速度由反馈增益K∝|∂g_eff/∂p_max|·∂p*/∂g_eff·β决定。K>1→自加速快速收敛，K<1→衰减缓慢收敛。干预力度β是K的线性因子。 描述 良性循环收敛速度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D274`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D275｜维度最优漂移函数](functions/items/D275.md)

**函数内容 / Function Content**
中文：M8的d_opt随时间漂移：学习>衰老→d_opt右移（升级），学习<衰老→d_opt左移（降级）。衰老本质=d_opt左移而实际d跟不上→偏离增大→Φ增长。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的d_opt随时间漂移：学习>衰老→d_opt右移（升级），学习<衰老→d_opt左移（降级）。衰老本质=d_opt左移而实际d跟不上→偏离增大→Φ增长。 描述 维度最优漂移函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D275`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D276｜D158预测失效阈值函数](functions/items/D276.md)

**函数内容 / Function Content**
中文：M1的ΔΦ导致D158预测误差|e^{ΔΦ}-1|：ΔΦ=1→误差172%→预测失效。pᵢ<0.5时D158可靠（误差<30%），0.5-0.8谨慎使用，>0.8不可信。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的ΔΦ导致D158预测误差|e^{ΔΦ}-1|：ΔΦ=1→误差172%→预测失效。pᵢ<0.5时D158可靠（误差<30%），0.5-0.8谨慎使用，>0.8不可信。 描述 预测失效阈值函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D276`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D277｜统一健康指标函数](functions/items/D277.md)

**函数内容 / Function Content**
中文：M9三阶段各有健康指标：阶段1=平坦度⁻¹，阶段2=C_buffer，阶段3=1/ΔΦ。统一H=min(三指标)→最小值决定最弱环节。H=0时崩溃。可用于实时监测和预警。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9三阶段各有健康指标：阶段1=平坦度⁻¹，阶段2=C_buffer，阶段3=1/ΔΦ。统一H=min(三指标)→最小值决定最弱环节。H=0时崩溃。可用于实时监测和预警。 描述 统一健康指标函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D277`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D278｜缓冲峰值余量函数](functions/items/D278.md)

**函数内容 / Function Content**
中文：M10的C_max与p*比值∝n^{3/2}→n越大峰值余量越充裕。但衰减速度∝n²→余量消耗更快。复杂系统"家底厚但花得快"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的C_max与p*比值∝n^{3/2}→n越大峰值余量越充裕。但衰减速度∝n²→余量消耗更快。复杂系统"家底厚但花得快"。 描述 缓冲峰值余量函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D278`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D279｜干预时机悖论函数](functions/items/D279.md)

**函数内容 / Function Content**
中文：M13正反馈干预的时机悖论：早期效果弱但窗口宽，晚期效果强但窗口窄。最优时机=D262缓冲峰值时刻t_peak。错过t_peak后窗口快速关闭。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13正反馈干预的时机悖论：早期效果弱但窗口宽，晚期效果强但窗口窄。最优时机=D262缓冲峰值时刻t_peak。错过t_peak后窗口快速关闭。 描述 干预时机悖论函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D279`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D280｜容斥干预两步策略函数](functions/items/D280.md)

**函数内容 / Function Content**
中文：M7的干预策略：A均匀降pᵢ（全面但成本高），B只降p_max（效率∝(n-1)·p_max/p̄倍于A）。最优=先B后A：先集中火力打最硬钉子，再均匀巩固。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的干预策略：A均匀降pᵢ（全面但成本高），B只降p_max（效率∝(n-1)·p_max/p̄倍于A）。最优=先B后A：先集中火力打最硬钉子，再均匀巩固。 描述 容斥干预两步策略函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D280`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D281｜极小点漂移-鲁棒性耦合函数](functions/items/D281.md)

**函数内容 / Function Content**
中文：M2的极小点漂移对鲁棒性影响取决于Φ三阶导数符号。学习新技能→δμ<0→极小点下移→无论偏斜方向都提升鲁棒性。物理大统一d³Φ/dμ³≈0→漂移影响极小。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的极小点漂移对鲁棒性影响取决于Φ三阶导数符号。学习新技能→δμ<0→极小点下移→无论偏斜方向都提升鲁棒性。物理大统一d³Φ/dμ³≈0→漂移影响极小。 描述 极小点漂移-鲁棒性耦合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D281`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D282｜Φ二阶近似函数](functions/items/D282.md)

**函数内容 / Function Content**
中文：M3的改进近似：Φ_2=Σpᵢ+Σpᵢ²/2在pᵢ<0.8时误差<17%，远优于Φ_approx。推荐三级精度：pᵢ<0.5用Φ_approx，0.5-0.8用Φ_2，>0.8用Φ_exact。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的改进近似：Φ_2=Σpᵢ+Σpᵢ²/2在pᵢ<0.8时误差<17%，远优于Φ_approx。推荐三级精度：pᵢ<0.5用Φ_approx，0.5-0.8用Φ_2，>0.8用Φ_exact。 描述 二阶近似函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D282`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.8`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D283｜宇宙学常数-容斥约束函数](functions/items/D283.md)

**函数内容 / Function Content**
中文：M6的d=4稳定性约束宇宙学常数：Λ_CDC过大→d_eff>4→容斥主导→结构无法形成；过小→d_eff<4→坍缩。Λ_CDC被约束在使d_eff≈4的窄区间→宇宙学常数问题的容斥解释。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d=4稳定性约束宇宙学常数：Λ_CDC过大→d_eff>4→容斥主导→结构无法形成；过小→d_eff<4→坍缩。Λ_CDC被约束在使d_eff≈4的窄区间→宇宙学常数问题的容斥解释。 描述 宇宙学常数-容斥约束函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D283`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D284｜σ_opt跨域常数函数](functions/items/D284.md)

**函数内容 / Function Content**
中文：M8的d_opt和σ_opt≈1.65的关系：n_eff≈d_opt/1.65→最优配置下独立门控面数约为维度的60%。如果σ_opt≈1.65在物理/生物/社会系统中都成立，它是跨域常数——类似精细结构常数。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的d_opt和σ_opt≈1.65的关系：n_eff≈d_opt/1.65→最优配置下独立门控面数约为维度的60%。如果σ_opt≈1.65在物理/生物/社会系统中都成立，它是跨域常数——类似精细结构常数。 描述 跨域常数函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D284`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `1.65`: structural_constant / derived - Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D285｜干预机会面积函数](functions/items/D285.md)

**函数内容 / Function Content**
中文：M11的阶段2干预机会面积∝p*(√d-1)/d，在d≈4时最大。d=4的双重最优：最稳定+最可修复。不只是物理定律在d=4最稳定，连"修复系统的机会"也在d=4最大。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的阶段2干预机会面积∝p*(√d-1)/d，在d≈4时最大。d=4的双重最优：最稳定+最可修复。不只是物理定律在d=4最稳定，连"修复系统的机会"也在d=4最大。 描述 干预机会面积函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D285`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D286｜p*-分布形态函数](functions/items/D286.md)

**函数内容 / Function Content**
中文：M4的p*对门槛分布形态有强依赖：均匀分布p*=√((n-1)/2)，极端分散p*=(p_min/p_max)√(n-1)。降低p_max不仅直接降Φ，还通过集中p分布提高p*→双重收益。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的p*对门槛分布形态有强依赖：均匀分布p*=√((n-1)/2)，极端分散p*=(p_min/p_max)√(n-1)。降低p_max不仅直接降Φ，还通过集中p分布提高p*→双重收益。 描述 *-分布形态函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D286`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D287｜容斥主导实验签名函数](functions/items/D287.md)

**函数内容 / Function Content**
中文：M5的容斥主导有可检验签名：实际量子引力修正>>标准预测。如果实验观测到量子引力效应显著强于标准模型预测，是容斥主导的证据。新判据：不只看"有没有"，还看"是否比独立假设预测的更强"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的容斥主导有可检验签名：实际量子引力修正>>标准预测。如果实验观测到量子引力效应显著强于标准模型预测，是容斥主导的证据。新判据：不只看"有没有"，还看"是否比独立假设预测的更强"。 描述 容斥主导实验签名函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D287`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D288｜g_eff有限时间崩溃函数](functions/items/D288.md)

**函数内容 / Function Content**
中文：M12的g_eff演化方程g_eff(t)=1-Δα·t/(p₀+α_max·t)。Δα>α_max时g_eff在有限时间t_c=p₀/(Δα-α_max)内归零→耦合消失→系统崩溃。"突然崩溃"的精确条件：增速极化程度Δα/α_max>1。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的g_eff演化方程g_eff(t)=1-Δα·t/(p₀+α_max·t)。Δα>α_max时g_eff在有限时间t_c=p₀/(Δα-α_max)内归零→耦合消失→系统崩溃。"突然崩溃"的精确条件：增速极化程度Δα/α_max>1。 描述 有限时间崩溃函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D288`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D289｜良性循环逃逸速度函数](functions/items/D289.md)

**函数内容 / Function Content**
中文：M14的逃逸速度v_escape∝λ·p_max²·g_eff。p_max≈0.5是最佳逃逸窗口（黄金逃逸点）。p_max<0.5逃逸容易但效果弱，p_max>0.8几乎不可能逃逸。D279干预时机悖论的精确化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的逃逸速度v_escape∝λ·p_max²·g_eff。p_max≈0.5是最佳逃逸窗口（黄金逃逸点）。p_max<0.5逃逸容易但效果弱，p_max>0.8几乎不可能逃逸。D279干预时机悖论的精确化。 描述 良性循环逃逸速度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D289`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `0.8`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D290｜容斥加速逆转条件函数](functions/items/D290.md)

**函数内容 / Function Content**
中文：M7的容斥加速逆转条件：p_max相对下降速率|α_max|/p_max必须超过其他pᵢ平均相对增长速率。温和改革通常无效——降速不够快，容斥加速仍在继续。需要"休克疗法"级别干预才能逆转。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速逆转条件：p_max相对下降速率|α_max|/p_max必须超过其他pᵢ平均相对增长速率。温和改革通常无效——降速不够快，容斥加速仍在继续。需要"休克疗法"级别干预才能逆转。 描述 容斥加速逆转条件函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D290`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D291｜D158案例可靠性分类函数](functions/items/D291.md)

**函数内容 / Function Content**
中文：M1对562案例的定量影响：D158a-f的49案例中约30-40%需用Φ_2或Φ_exact（pᵢ>0.5），约10-15%的案例D158完全不可信（pᵢ>0.8）。量子力学测量、热力学相变、相对论极端速度、凝聚态临界温度最需修正。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1对562案例的定量影响：D158a-f的49案例中约30-40%需用Φ_2或Φ_exact（pᵢ>0.5），约10-15%的案例D158完全不可信（pᵢ>0.8）。量子力学测量、热力学相变、相对论极端速度、凝聚态临界温度最需修正。 描述 案例可靠性分类函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D291`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `0.8`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D292｜维度最优吸引域函数](functions/items/D292.md)

**函数内容 / Function Content**
中文：M8的d_opt吸引域深度∝Σαᵢ²/(1-pᵢ)²。高p门控面α²越大→吸引越强但偏离后崩溃越猛。d_opt的"引力"和偏离后的"暴力"成正比——强吸引域=稳定但一旦失稳更致命。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的d_opt吸引域深度∝Σαᵢ²/(1-pᵢ)²。高p门控面α²越大→吸引越强但偏离后崩溃越猛。d_opt的"引力"和偏离后的"暴力"成正比——强吸引域=稳定但一旦失稳更致命。 描述 维度最优吸引域函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D292`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D293｜三阶段-相变分类对应函数](functions/items/D293.md)

**函数内容 / Function Content**
中文：M9三阶段对应相变分类：阶段1→2≈二级相变（连续过渡→还有救），阶段2→3≈一级相变（突变→没救）。新相变分类：二级="还能缓冲"，一级="缓冲耗尽"。干预在二级相变区有效，一级相变区无效。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9三阶段对应相变分类：阶段1→2≈二级相变（连续过渡→还有救），阶段2→3≈一级相变（突变→没救）。新相变分类：二级="还能缓冲"，一级="缓冲耗尽"。干预在二级相变区有效，一级相变区无效。 描述 三阶段-相变分类对应函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D293`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D294｜缓冲消耗速度函数](functions/items/D294.md)

**函数内容 / Function Content**
中文：M10的缓冲消耗速度∝Δα·n²p̄²ḡ/2。三个加速因子：n大（复杂）、Δα大（极化）、p̄大（高风险）。高n+高Δα+高p̄=崩溃高危系统。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的缓冲消耗速度∝Δα·n²p̄²ḡ/2。三个加速因子：n大（复杂）、Δα大（极化）、p̄大（高风险）。高n+高Δα+高p̄=崩溃高危系统。 描述 缓冲消耗速度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D294`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D295｜正反馈不可逆点函数](functions/items/D295.md)

**函数内容 / Function Content**
中文：M13正反馈的不可逆点：p_max>p*(g_eff)→降低p_max只降Φ不提p*→良性循环无法启动→不可逆。p_max=p*是"还有救"和"没救了"的精确分界。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13正反馈的不可逆点：p_max>p*(g_eff)→降低p_max只降Φ不提p*→良性循环无法启动→不可逆。p_max=p*是"还有救"和"没救了"的精确分界。 描述 正反馈不可逆点函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D295`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D296｜Φ近似阶数选择函数](functions/items/D296.md)

**函数内容 / Function Content**
中文：M3的Φ近似阶数选择：pᵢ<0.5→1阶（误差<13%），0.5-0.8→2阶（<17%），0.8-0.95→3阶（~10%），≥0.95→Φ_exact。精度-成本权衡表。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的Φ近似阶数选择：pᵢ<0.5→1阶（误差<13%），0.5-0.8→2阶（<17%），0.8-0.95→3阶（~10%），≥0.95→Φ_exact。精度-成本权衡表。 描述 近似阶数选择函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D296`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.
  - `0.8`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D297｜基本常数-容斥约束函数](functions/items/D297.md)

**函数内容 / Function Content**
中文：M6的d=4稳定性约束基本物理常数：α增大~100倍→pᵢ>p*→极小点消失。精细结构常数α≈1/137不能太大→否则电磁否决概率超p*→d=4不稳定。常数不是任意的，必须让d=4稳定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d=4稳定性约束基本物理常数：α增大~100倍→pᵢ>p*→极小点消失。精细结构常数α≈1/137不能太大→否则电磁否决概率超p*→d=4不稳定。常数不是任意的，必须让d=4稳定。 描述 基本常数-容斥约束函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D297`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [精细结构常数稳定性](cases/items/C-0573.md)

### [D298｜鲁棒系统设计原则函数](functions/items/D298.md)

**函数内容 / Function Content**
中文：M11的设计原则：增大n_eff（宽缓冲）但ḡ适中（防雪崩）。σ≈1.65是平衡点→n_eff≈d/1.65→阶段2宽度适中+阶段3雪崩可控。过聚集→雪崩风险，过分散→缓冲不足。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的设计原则：增大n_eff（宽缓冲）但ḡ适中（防雪崩）。σ≈1.65是平衡点→n_eff≈d/1.65→阶段2宽度适中+阶段3雪崩可控。过聚集→雪崩风险，过分散→缓冲不足。 描述 鲁棒系统设计原则函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D298`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `1.65`: structural_constant / derived - Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D299｜良性-恶性共存函数](functions/items/D299.md)

**函数内容 / Function Content**
中文：M14的良性/恶性循环可共存：某些pᵢ降（良性），某些升（恶性）。容斥凸性给恶性方向天然加速→良性子循环必须足够强才能抵消。"部分改革"通常不够——被恶性子循环的容斥加速压倒。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的良性/恶性循环可共存：某些pᵢ降（良性），某些升（恶性）。容斥凸性给恶性方向天然加速→良性子循环必须足够强才能抵消。"部分改革"通常不够——被恶性子循环的容斥加速压倒。 描述 良性-恶性共存函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D299`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D300｜代际容斥累积函数](functions/items/D300.md)

**函数内容 / Function Content**
中文：M7的容斥加速跨代累积∝k²。每代不只新增Δp，还有前面所有Δp的交叉效应累积。代际容斥∝k²→阶层固化的跨代传递是加速的——"三代出贵族"不只是财富累积，还有容斥交叉项的k²加速。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速跨代累积∝k²。每代不只新增Δp，还有前面所有Δp的交叉效应累积。代际容斥∝k²→阶层固化的跨代传递是加速的——"三代出贵族"不只是财富累积，还有容斥交叉项的k²加速。 描述 代际容斥累积函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D300`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D301｜极小点漂移速率函数](functions/items/D301.md)

**函数内容 / Function Content**
中文：M2的漂移速率dμ/dt=-(Σᵢ αᵢ/(1-pᵢ)²)/(d²Φ/dμ²)。分母是Φ曲率——平坦区（物理大统一d²Φ/dμ²≈0）漂移极快，尖锐区漂移极慢。平坦=稳定但漂移快，是D292"强吸引域失稳更致命"的速率版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的漂移速率dμ/dt=-(Σᵢ αᵢ/(1-pᵢ)²)/(d²Φ/dμ²)。分母是Φ曲率——平坦区（物理大统一d²Φ/dμ²≈0）漂移极快，尖锐区漂移极慢。平坦=稳定但漂移快，是D292"强吸引域失稳更致命"的速率版本。 描述 极小点漂移速率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D301`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D302｜容斥渐近发散函数](functions/items/D302.md)

**函数内容 / Function Content**
中文：M3的容斥高阶项在pᵢ→1时ΔΦ→e^{pᵢ}-1-pᵢ→∞，发散速率∝e^{pᵢ}。pᵢ接近1时容斥修正爆炸式增长，不是"大了一点"。D260敏感度阈值pᵢ>0.5后急剧上升的数学根源就是容斥项的指数发散。D296的Φ_exact在pᵢ>0.95时不可替代。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的容斥高阶项在pᵢ→1时ΔΦ→e^{pᵢ}-1-pᵢ→∞，发散速率∝e^{pᵢ}。pᵢ接近1时容斥修正爆炸式增长，不是"大了一点"。D260敏感度阈值pᵢ>0.5后急剧上升的数学根源就是容斥项的指数发散。D296的Φ_exact在pᵢ>0.95时不可替代。 描述 容斥渐近发散函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D302`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D303｜容斥-耦合竞争动态演化函数](functions/items/D303.md)

**函数内容 / Function Content**
中文：M4的竞争阈值p*随pᵢ分布演化：dp*/dt=∂p*/∂n·dn/dt + ∂p*/∂(p分布)·d(p分布)/dt。pᵢ均匀增长时p*∝√n缓慢上升（容斥占优加速），pᵢ集中增长时p*快速上升（耦合占优）。改革如果只降低部分pᵢ而不改变分布形态，p*可能不动甚至下降——"部分改革"更可能失败的动态版本，D299的动态深化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的竞争阈值p*随pᵢ分布演化：dp*/dt=∂p*/∂n·dn/dt + ∂p*/∂(p分布)·d(p分布)/dt。pᵢ均匀增长时p*∝√n缓慢上升（容斥占优加速），pᵢ集中增长时p*快速上升（耦合占优）。改革如果只降低部分pᵢ而不改变分布形态，p*可能不动甚至下降——"部分改革"更可能失败的动态版本，D299的动态深化。 描述 容斥-耦合竞争动态演化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D303`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D304｜弱混合角-容斥约束函数](functions/items/D304.md)

**函数内容 / Function Content**
中文：M5的容斥主导不只约束α，还约束弱混合角θ_W：sin²θ_W≈0.23必须使弱力否决概率p_weak<p*。θ_W过大→弱力否决概率超p*→电弱统一尺度极小点消失→d=4不稳定。与D297形成"基本常数容斥约束群"——α、θ_W、Λ_CDC(D283)三者联合约束使d=4稳定。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的容斥主导不只约束α，还约束弱混合角θ_W：sin²θ_W≈0.23必须使弱力否决概率p_weak<p*。θ_W过大→弱力否决概率超p*→电弱统一尺度极小点消失→d=4不稳定。与D297形成"基本常数容斥约束群"——α、θ_W、Λ_CDC(D283)三者联合约束使d=4稳定。 描述 弱混合角-容斥约束函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D283`, `D304`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.23`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D305｜维度偏离退化路径函数](functions/items/D305.md)

**函数内容 / Function Content**
中文：M6的d偏离4时退化路径分两支：d>4→新门控面pᵢ>p*→容斥主导→极小点消失→结构无法形成（"过度复杂"崩溃）；d<4→门控面不足→耦合过弱→缓冲不足→极小点虽在但极浅→小扰动即崩（"过度简单"崩溃）。两支不对称：d>4崩溃突然（容斥爆炸D302），d<4崩溃渐进（缓冲耗尽D294）。d=4是两种崩溃模式之间的鞍点。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d偏离4时退化路径分两支：d>4→新门控面pᵢ>p*→容斥主导→极小点消失→结构无法形成（"过度复杂"崩溃）；d<4→门控面不足→耦合过弱→缓冲不足→极小点虽在但极浅→小扰动即崩（"过度简单"崩溃）。两支不对称：d>4崩溃突然（容斥爆炸D302），d<4崩溃渐进（缓冲耗尽D294）。d=4是两种崩溃模式之间的鞍点。 描述 维度偏离退化路径函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D305`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D306｜去容斥条件函数](functions/items/D306.md)

**函数内容 / Function Content**
中文：M7的容斥加速逆过程"去容斥"需两条件同时满足：①p_max下降速率|ḃ|>容斥加速度d²(Σpᵢpⱼ)/dt²，②p分布必须集中化（σ<σ_opt）。只满足①不满足②→容斥项基数仍大→去容斥不可持续。只满足②不满足①→p_max继续上升→容斥加速继续。D290"休克疗法"的精确版：休克疗法同时满足①②，温和改革通常只满足①。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速逆过程"去容斥"需两条件同时满足：①p_max下降速率|ḃ|>容斥加速度d²(Σpᵢpⱼ)/dt²，②p分布必须集中化（σ<σ_opt）。只满足①不满足②→容斥项基数仍大→去容斥不可持续。只满足②不满足①→p_max继续上升→容斥加速继续。D290"休克疗法"的精确版：休克疗法同时满足①②，温和改革通常只满足①。 描述 去容斥条件函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D290`, `D306`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D307｜σ_opt微观起源函数](functions/items/D307.md)

**函数内容 / Function Content**
中文：M8的σ_opt≈1.65来自独立性-充分性权衡：门控面独立性要求σ<2（过聚集→不独立→容斥爆炸），缓冲充分性要求σ>1（过分散→耦合弱→缓冲不足）。精确解：σ_opt是dΦ/dσ=0的根，n→∞极限下σ_opt→√e≈1.649≈1.65。σ_opt=√e不是巧合——是独立性-充分性权衡的解析解。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的σ_opt≈1.65来自独立性-充分性权衡：门控面独立性要求σ<2（过聚集→不独立→容斥爆炸），缓冲充分性要求σ>1（过分散→耦合弱→缓冲不足）。精确解：σ_opt是dΦ/dσ=0的根，n→∞极限下σ_opt→√e≈1.649≈1.65。σ_opt=√e不是巧合——是独立性-充分性权衡的解析解。 描述 微观起源函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D307`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `1.65`: structural_constant / derived - Derived as the n→∞ root of the independence-sufficiency balance dΦ/dσ=0; the closed-form limit is σ_opt=√e≈1.6487.
  - `√e`: math_builtin / derived - √e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D308｜阶段过渡滞后函数](functions/items/D308.md)

**函数内容 / Function Content**
中文：M9的阶段过渡存在滞后：从阶段2退回阶段1的条件（缓冲恢复）比从阶段1进入阶段2的条件（缓冲消耗）更严格。滞后量Δh∝|d³Φ/dμ³|——三阶导数越大滞后越大。物理相变滞后小（d³Φ/dμ³小），社会系统滞后大（路径依赖使d³Φ/dμ³大）。社会系统"改革倒退"比"改革推进"更容易——进入阶段2容易，退回阶段1难。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的阶段过渡存在滞后：从阶段2退回阶段1的条件（缓冲恢复）比从阶段1进入阶段2的条件（缓冲消耗）更严格。滞后量Δh∝|d³Φ/dμ³|——三阶导数越大滞后越大。物理相变滞后小（d³Φ/dμ³小），社会系统滞后大（路径依赖使d³Φ/dμ³大）。社会系统"改革倒退"比"改革推进"更容易——进入阶段2容易，退回阶段1难。 描述 阶段过渡滞后函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D308`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D309｜缓冲可重建性函数](functions/items/D309.md)

**函数内容 / Function Content**
中文：M10的缓冲耗尽后可重建条件：g_eff>g_critical≈√(2ΔΦ/n)。g_eff低于此阈值时，即使p_max大幅下降，耦合强度也不足以重建缓冲——"缓冲不可逆"状态。与D295正反馈不可逆点形成双重不可逆：D295是p_max不可逆，D309是缓冲不可逆。两个不可逆点可以不同时到达——缓冲可能先于p_max进入不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的缓冲耗尽后可重建条件：g_eff>g_critical≈√(2ΔΦ/n)。g_eff低于此阈值时，即使p_max大幅下降，耦合强度也不足以重建缓冲——"缓冲不可逆"状态。与D295正反馈不可逆点形成双重不可逆：D295是p_max不可逆，D309是缓冲不可逆。两个不可逆点可以不同时到达——缓冲可能先于p_max进入不可逆。 描述 缓冲可重建性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D309`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D310｜阶段2临界宽度函数](functions/items/D310.md)

**函数内容 / Function Content**
中文：M11的阶段2宽度w₂有临界下限w_min∝1/(n·ḡ)。低于此宽度时阶段2退化为相变面——系统直接从阶段1跳到阶段3，没有缓冲期。小企业（D159标注）的n小、ḡ低→w₂<w_min→直接处于阶段3。任何n·ḡ<阈值的系统都不存在缓冲期——脆弱性不是状态而是结构属性。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的阶段2宽度w₂有临界下限w_min∝1/(n·ḡ)。低于此宽度时阶段2退化为相变面——系统直接从阶段1跳到阶段3，没有缓冲期。小企业（D159标注）的n小、ḡ低→w₂<w_min→直接处于阶段3。任何n·ḡ<阈值的系统都不存在缓冲期——脆弱性不是状态而是结构属性。 描述 阶段2临界宽度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D310`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D311｜僵尸态函数](functions/items/D311.md)

**函数内容 / Function Content**
中文：M12的g_eff极小但不为零时（0<g_eff<<g_critical），系统处于"僵尸态"：耦合名义上存在但实际无效，缓冲名义上存在但无法使用。数学特征：P_survival=e^{-Φ_eff}中Φ_eff≈Φ（耦合修正可忽略），但系统并未完全崩溃（g_eff>0）。僵尸态比完全崩溃更危险——系统看起来还在运转，掩盖了D309缓冲不可逆已到达的事实。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的g_eff极小但不为零时（0<g_eff<<g_critical），系统处于"僵尸态"：耦合名义上存在但实际无效，缓冲名义上存在但无法使用。数学特征：P_survival=e^{-Φ_eff}中Φ_eff≈Φ（耦合修正可忽略），但系统并未完全崩溃（g_eff>0）。僵尸态比完全崩溃更危险——系统看起来还在运转，掩盖了D309缓冲不可逆已到达的事实。 描述 僵尸态函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D311`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D312｜正反馈噪声放大函数](functions/items/D312.md)

**函数内容 / Function Content**
中文：M13的正反馈回路放大噪声：δp_max经过k轮反馈后放大为δp_max·K^k，K为反馈增益(D274)。K>1时噪声指数放大→系统对初始条件极度敏感→蝴蝶效应。K<1时噪声衰减→系统稳定。临界K=1对应D295不可逆点。K>1的系统不可预测——不是因为模型不够好，而是正反馈使噪声放大到宏观尺度。经济危机、社会动荡的不可预测性有数学根源。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的正反馈回路放大噪声：δp_max经过k轮反馈后放大为δp_max·K^k，K为反馈增益(D274)。K>1时噪声指数放大→系统对初始条件极度敏感→蝴蝶效应。K<1时噪声衰减→系统稳定。临界K=1对应D295不可逆点。K>1的系统不可预测——不是因为模型不够好，而是正反馈使噪声放大到宏观尺度。经济危机、社会动荡的不可预测性有数学根源。 描述 正反馈噪声放大函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D274`, `D312`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D313｜共存稳态条件函数](functions/items/D313.md)

**函数内容 / Function Content**
中文：M14的良性-恶性共存(D299)能持续的条件：良性子循环的反馈增益K_benign必须大于恶性子循环的容斥加速因子α_exclusion。K_benign<α_exclusion→共存不稳定→恶性最终吞噬良性。K_benign>α_exclusion→共存稳定→良性逐步蚕食恶性。K_benign≈α_exclusion→临界共存→小扰动决定方向。D299"部分改革通常不够"的精确版：改革力度β(D274)必须使K_benign>α_exclusion。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的良性-恶性共存(D299)能持续的条件：良性子循环的反馈增益K_benign必须大于恶性子循环的容斥加速因子α_exclusion。K_benign<α_exclusion→共存不稳定→恶性最终吞噬良性。K_benign>α_exclusion→共存稳定→良性逐步蚕食恶性。K_benign≈α_exclusion→临界共存→小扰动决定方向。D299"部分改革通常不够"的精确版：改革力度β(D274)必须使K_benign>α_exclusion。 描述 共存稳态条件函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D274`, `D299`, `D313`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D314｜ΔΦ-P传导非线性阈值函数](functions/items/D314.md)

**函数内容 / Function Content**
中文：M1的ΔΦ通过P_survival=e^{-Φ}传导。ΔΦ<0.1时P变化≈ΔΦ（线性区），ΔΦ>1时P变化≈e^{-ΔΦ}（指数区），0.1<ΔΦ<1为过渡区。非线性阈值ΔΦ_c≈0.3——低于此值D158线性近似可用，高于此值必须用指数形式。与D296三级精度体系衔接：ΔΦ_c=0.3对应pᵢ≈0.5，与D260敏感度阈值一致。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的ΔΦ通过P_survival=e^{-Φ}传导。ΔΦ<0.1时P变化≈ΔΦ（线性区），ΔΦ>1时P变化≈e^{-ΔΦ}（指数区），0.1<ΔΦ<1为过渡区。非线性阈值ΔΦ_c≈0.3——低于此值D158线性近似可用，高于此值必须用指数形式。与D296三级精度体系衔接：ΔΦ_c=0.3对应pᵢ≈0.5，与D260敏感度阈值一致。 描述 -P传导非线性阈值函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D314`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `0.1`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D315｜多极小点竞争函数](functions/items/D315.md)

**函数内容 / Function Content**
中文：M2的Φ(μ)在多个门控面参数差异大时可出现多个极小点。竞争规则：全局极小点由min(Φ(μ_k))决定，但系统可能被困在局部极小点（亚稳态）。逃逸条件：热涨落或外部驱动使Φ跨越鞍点Φ_saddle。鞍点高度∝min(Δpᵢ²)——最接近的两个门控面差异越小，鞍点越低，亚稳态越易逃逸。社会改革中"次优但可到达"比"最优但需翻越鞍点"更实际。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的Φ(μ)在多个门控面参数差异大时可出现多个极小点。竞争规则：全局极小点由min(Φ(μ_k))决定，但系统可能被困在局部极小点（亚稳态）。逃逸条件：热涨落或外部驱动使Φ跨越鞍点Φ_saddle。鞍点高度∝min(Δpᵢ²)——最接近的两个门控面差异越小，鞍点越低，亚稳态越易逃逸。社会改革中"次优但可到达"比"最优但需翻越鞍点"更实际。 描述 多极小点竞争函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D315`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D316｜容斥时间权重演化函数](functions/items/D316.md)

**函数内容 / Function Content**
中文：M3的dΦ/dt=Σᵢ αᵢ/(1-pᵢ) + Σᵢⱼ d(pᵢpⱼ)/dt。早期pᵢ小时容斥项占比≈0，中后期容斥项占比∝(Σpᵢ)²急剧上升。转折点在Σpᵢ≈0.5——此后容斥项主导dΦ/dt。社会系统"突然变坏"的数学根源：容斥项占比二次增长使衰退在后半段急剧加速。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的dΦ/dt=Σᵢ αᵢ/(1-pᵢ) + Σᵢⱼ d(pᵢpⱼ)/dt。早期pᵢ小时容斥项占比≈0，中后期容斥项占比∝(Σpᵢ)²急剧上升。转折点在Σpᵢ≈0.5——此后容斥项主导dΦ/dt。社会系统"突然变坏"的数学根源：容斥项占比二次增长使衰退在后半段急剧加速。 描述 容斥时间权重演化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D316`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D317｜p*敏感度函数](functions/items/D317.md)

**函数内容 / Function Content**
中文：M4的p*对系统参数的敏感度：∂p*/∂n=p*/(2n)（弱敏感），∂p*/∂σ∝p*·(σ_opt-σ)/σ_opt²（强敏感）。p*对分布分散度σ的敏感度远高于对n的敏感度。改变分布形态（集中化）比增加门控面数n更能有效移动p*——D306"去容斥需同时集中分布"的敏感度论证。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的p*对系统参数的敏感度：∂p*/∂n=p*/(2n)（弱敏感），∂p*/∂σ∝p*·(σ_opt-σ)/σ_opt²（强敏感）。p*对分布分散度σ的敏感度远高于对n的敏感度。改变分布形态（集中化）比增加门控面数n更能有效移动p*——D306"去容斥需同时集中分布"的敏感度论证。 描述 *敏感度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D306`, `D317`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D318｜容斥主导尺度函数](functions/items/D318.md)

**函数内容 / Function Content**
中文：M5的容斥从可忽略变主导的临界尺度μ_c由max(pᵢ(μ))=p*决定。μ<μ_c时容斥可忽略（经典物理区），μ>μ_c时容斥主导（量子引力区）。μ_c对应量子引力能标~10¹⁸ GeV。容斥主导不是渐变而是在μ_c处突变——D293阶段2→3一级相变的尺度版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的容斥从可忽略变主导的临界尺度μ_c由max(pᵢ(μ))=p*决定。μ<μ_c时容斥可忽略（经典物理区），μ>μ_c时容斥主导（量子引力区）。μ_c对应量子引力能标~10¹⁸ GeV。容斥主导不是渐变而是在μ_c处突变——D293阶段2→3一级相变的尺度版本。 描述 容斥主导尺度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D318`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D319｜维度回复力函数](functions/items/D319.md)

**函数内容 / Function Content**
中文：M6的d_eff在4附近振荡时回复力F_restore∝-∂Φ/∂(d_eff)·δ(d_eff-4)。回复力系数k_restore∝Σαᵢ²/(1-pᵢ)²——与D292吸引域深度同源。k_restore在d=4处最大→d=4不仅是稳定点还是回复力最强的点。宇宙即使被扰动偏离d=4也会被"弹回来"——d=4的稳定性是动态的。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d_eff在4附近振荡时回复力F_restore∝-∂Φ/∂(d_eff)·δ(d_eff-4)。回复力系数k_restore∝Σαᵢ²/(1-pᵢ)²——与D292吸引域深度同源。k_restore在d=4处最大→d=4不仅是稳定点还是回复力最强的点。宇宙即使被扰动偏离d=4也会被"弹回来"——d=4的稳定性是动态的。 描述 维度回复力函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D319`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D320｜容斥加速跨域标度函数](functions/items/D320.md)

**函数内容 / Function Content**
中文：M7的容斥加速度a_excl∝n²·σ²·ḡ在不同域的标度：物理n小σ小→a_excl小，生物n大σ中→a_excl中，社会n大σ大→a_excl大。a_excl(社会)/a_excl(物理)∝(n_社会/n_物理)²·(σ_社会/σ_物理)²——量级差异可达10⁶以上。社会系统容斥加速远强于物理系统。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速度a_excl∝n²·σ²·ḡ在不同域的标度：物理n小σ小→a_excl小，生物n大σ中→a_excl中，社会n大σ大→a_excl大。a_excl(社会)/a_excl(物理)∝(n_社会/n_物理)²·(σ_社会/σ_物理)²——量级差异可达10⁶以上。社会系统容斥加速远强于物理系统。 描述 容斥加速跨域标度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D320`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D321｜d_opt-σ_opt联合演化函数](functions/items/D321.md)

**函数内容 / Function Content**
中文：M8的d_opt漂移时σ_opt跟着动：d_opt右移（学习升级）时σ_opt先升后降——初期新门控面增加分散度，后期门控面成熟降低分散度。σ_opt响应滞后于d_opt，调整时间τ_σ∝n/ḡ。n大ḡ低的系统σ调整慢——社会系统的"最优配置"总是落后于"最优维度"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的d_opt漂移时σ_opt跟着动：d_opt右移（学习升级）时σ_opt先升后降——初期新门控面增加分散度，后期门控面成熟降低分散度。σ_opt响应滞后于d_opt，调整时间τ_σ∝n/ḡ。n大ḡ低的系统σ调整慢——社会系统的"最优配置"总是落后于"最优维度"。 描述 -σ_opt联合演化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D321`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D322｜周期扰动阶段响应函数](functions/items/D322.md)

**函数内容 / Function Content**
中文：M9的三阶段在周期扰动下的响应：低频扰动→系统跟随移动有缓冲重建时间；高频扰动→缓冲来不及响应系统不动；共振频率（周期≈τ_buffer）→缓冲被共振消耗→系统加速进入阶段3。经济周期如果与缓冲恢复时间共振，衰退会加速——不是周期本身可怕，是共振可怕。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的三阶段在周期扰动下的响应：低频扰动→系统跟随移动有缓冲重建时间；高频扰动→缓冲来不及响应系统不动；共振频率（周期≈τ_buffer）→缓冲被共振消耗→系统加速进入阶段3。经济周期如果与缓冲恢复时间共振，衰退会加速——不是周期本身可怕，是共振可怕。 描述 周期扰动阶段响应函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D322`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D323｜缓冲重建时间函数](functions/items/D323.md)

**函数内容 / Function Content**
中文：M10的缓冲从零重建到C_max的时间τ_rebuild∝n/(ḡ·β)。τ_rebuild>>τ_deplete——重建比消耗慢得多。比例τ_rebuild/τ_deplete∝n²·p̄/β——n越大比例越悬殊。复杂系统"毁起来快建起来慢"有精确的n²因子。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的缓冲从零重建到C_max的时间τ_rebuild∝n/(ḡ·β)。τ_rebuild>>τ_deplete——重建比消耗慢得多。比例τ_rebuild/τ_deplete∝n²·p̄/β——n越大比例越悬殊。复杂系统"毁起来快建起来慢"有精确的n²因子。 描述 缓冲重建时间函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D323`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D324｜阶段2宽度标度函数](functions/items/D324.md)

**函数内容 / Function Content**
中文：M11的w₂∝(√n-1)/(n·ḡ)。n→∞时w₂→0——门控面越多缓冲期越短。但ḡ∝√n以上增长可补偿。社会系统"改革窗口"是否关闭取决于ḡ增长能否跟上n。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的w₂∝(√n-1)/(n·ḡ)。n→∞时w₂→0——门控面越多缓冲期越短。但ḡ∝√n以上增长可补偿。社会系统"改革窗口"是否关闭取决于ḡ增长能否跟上n。 描述 阶段2宽度标度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D324`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D325｜僵尸态自修复函数](functions/items/D325.md)

**函数内容 / Function Content**
中文：M12的僵尸态中自发涨落δg_eff∝√(kT_eff/n)。涨落踢出僵尸态的概率∝e^{-n(g_critical-g_eff)²/kT_eff}——n越大概率越小。小系统可能自修复，大系统几乎不可能。组织越大越容易永久僵尸化。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的僵尸态中自发涨落δg_eff∝√(kT_eff/n)。涨落踢出僵尸态的概率∝e^{-n(g_critical-g_eff)²/kT_eff}——n越大概率越小。小系统可能自修复，大系统几乎不可能。组织越大越容易永久僵尸化。 描述 僵尸态自修复函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D325`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D326｜正反馈饱和函数](functions/items/D326.md)

**函数内容 / Function Content**
中文：M13的正反馈K^k饱和来自p_max的物理下界p_min>0。K^k有效值=K^k/(1+(K^k-1)·p_min/p_max)，K^k·p_min≈p_max时饱和。饱和后稳态p_max≈p_min·K/(K-1)。K越大稳态越低——强正反馈把p_max压到极低，但代价是D312噪声放大。D242精度-鲁棒性权衡在正反馈回路中的具体表现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的正反馈K^k饱和来自p_max的物理下界p_min>0。K^k有效值=K^k/(1+(K^k-1)·p_min/p_max)，K^k·p_min≈p_max时饱和。饱和后稳态p_max≈p_min·K/(K-1)。K越大稳态越低——强正反馈把p_max压到极低，但代价是D312噪声放大。D242精度-鲁棒性权衡在正反馈回路中的具体表现。 描述 正反馈饱和函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D326`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D327｜共存震荡函数](functions/items/D327.md)

**函数内容 / Function Content**
中文：M14的K_benign≈α_exclusion时良性恶性周期震荡：良性增长→p_max↓→容斥减弱→恶性增长→p_max↑→良性被压→恶性受限→良性再增长。震荡周期T_osc∝2π/√(K_benign·α_exclusion)，振幅∝|K_benign-α_exclusion|⁻¹/²。越接近临界振幅越大。社会系统"改革-倒退"周期震荡有数学根源。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的K_benign≈α_exclusion时良性恶性周期震荡：良性增长→p_max↓→容斥减弱→恶性增长→p_max↑→良性被压→恶性受限→良性再增长。震荡周期T_osc∝2π/√(K_benign·α_exclusion)，振幅∝|K_benign-α_exclusion|⁻¹/²。越接近临界振幅越大。社会系统"改革-倒退"周期震荡有数学根源。 描述 共存震荡函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D327`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D328｜ΔΦ空间异质性叠加函数](functions/items/D328.md)

**函数内容 / Function Content**
中文：M1的不同门控面ΔΦᵢ差异大时，总ΔΦ由最大ΔΦ主导：ΔΦ_total≈max(ΔΦᵢ)·(1+ln(Σe^{ΔΦᵢ}/max(ΔΦᵢ)))。极端异质性下ΔΦ_total≈ΔΦ_max·(1+ln(n-1))。系统退化由最弱门控面决定——不是"平均变差"而是"最差那个拖垮全局"。与D280"先降p_max"策略一致。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的不同门控面ΔΦᵢ差异大时，总ΔΦ由最大ΔΦ主导：ΔΦ_total≈max(ΔΦᵢ)·(1+ln(Σe^{ΔΦᵢ}/max(ΔΦᵢ)))。极端异质性下ΔΦ_total≈ΔΦ_max·(1+ln(n-1))。系统退化由最弱门控面决定——不是"平均变差"而是"最差那个拖垮全局"。与D280"先降p_max"策略一致。 描述 空间异质性叠加函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D328`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D329｜极小点合并函数](functions/items/D329.md)

**函数内容 / Function Content**
中文：M2的两个极小点在门槛参数变化时可以合并。合并条件：Φ(μ_saddle)-Φ(μ₁)<δΦ_thermal。合并后系统从双稳态变为单稳态——失去"退路"。合并方向：浅极小点被深极小点吸收。社会改革中"次优方案"极小点被吸收进"最优方案"后系统失去容错空间——D315"次优但可到达"的消失条件。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的两个极小点在门槛参数变化时可以合并。合并条件：Φ(μ_saddle)-Φ(μ₁)<δΦ_thermal。合并后系统从双稳态变为单稳态——失去"退路"。合并方向：浅极小点被深极小点吸收。社会改革中"次优方案"极小点被吸收进"最优方案"后系统失去容错空间——D315"次优但可到达"的消失条件。 描述 极小点合并函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D315`, `D329`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D330｜容斥关联拓扑函数](functions/items/D330.md)

**函数内容 / Function Content**
中文：M3的Σpᵢpⱼ中前k个高p门控面的容斥贡献>50%（k=3时）。容斥不是均匀分布的——集中在少数高p门控面之间。降p_max的效果不只是线性降Φ，还切断最大的容斥关联对——D280"先降p_max"的拓扑论证。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的Σpᵢpⱼ中前k个高p门控面的容斥贡献>50%（k=3时）。容斥不是均匀分布的——集中在少数高p门控面之间。降p_max的效果不只是线性降Φ，还切断最大的容斥关联对——D280"先降p_max"的拓扑论证。 描述 容斥关联拓扑函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D280`, `D330`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D331｜p*涨落函数](functions/items/D331.md)

**函数内容 / Function Content**
中文：M4的p*在有限n时有统计涨落δp*/p*∝1/√n。n小时涨落大→容斥-耦合竞争结果随机；n大时涨落小→结果确定但更难改变。小系统的竞争结果高度随机，大系统更可预测但更难逆转。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的p*在有限n时有统计涨落δp*/p*∝1/√n。n小时涨落大→容斥-耦合竞争结果随机；n大时涨落小→结果确定但更难改变。小系统的竞争结果高度随机，大系统更可预测但更难逆转。 描述 *涨落函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D331`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D332｜容斥-耦合不可逆函数](functions/items/D332.md)

**函数内容 / Function Content**
中文：M5的容斥主导区一旦进入，退回需要p*上升，但系统崩溃方向使p*下降→退回条件与动态方向相反。容斥主导是自锁的。与D295(p_max不可逆)、D309(缓冲不可逆)形成三级不可逆：p_max→缓冲→容斥主导，逐层加深的不可逆结构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的容斥主导区一旦进入，退回需要p*上升，但系统崩溃方向使p*下降→退回条件与动态方向相反。容斥主导是自锁的。与D295(p_max不可逆)、D309(缓冲不可逆)形成三级不可逆：p_max→缓冲→容斥主导，逐层加深的不可逆结构。 描述 容斥-耦合不可逆函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D309`, `D332`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D333｜维度回复阻尼函数](functions/items/D333.md)

**函数内容 / Function Content**
中文：M6的d_eff在4附近振荡时阻尼γ∝Σαᵢ/(1-pᵢ)²。γ>0衰减→d=4稳定吸引子；γ<0发散→不稳定；γ=0持续振荡。物理系统γ>>0（强阻尼），社会系统γ≈0（弱阻尼，长期振荡）。宇宙d=4不是恰好卡在4，而是衰减振荡后停在4。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d_eff在4附近振荡时阻尼γ∝Σαᵢ/(1-pᵢ)²。γ>0衰减→d=4稳定吸引子；γ<0发散→不稳定；γ=0持续振荡。物理系统γ>>0（强阻尼），社会系统γ≈0（弱阻尼，长期振荡）。宇宙d=4不是恰好卡在4，而是衰减振荡后停在4。 描述 维度回复阻尼函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D333`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D334｜容斥加速饱和函数](functions/items/D334.md)

**函数内容 / Function Content**
中文：M7的a_excl有上界∝n²·σ²/(4·p_min)，但系统在达到理论饱和前已进入D332容斥主导不可逆→崩溃。容斥加速的"理论极限"没有实际意义——系统先死到那儿。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的a_excl有上界∝n²·σ²/(4·p_min)，但系统在达到理论饱和前已进入D332容斥主导不可逆→崩溃。容斥加速的"理论极限"没有实际意义——系统先死到那儿。 描述 容斥加速饱和函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D334`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D335｜d_opt-σ_opt平衡稳定性函数](functions/items/D335.md)

**函数内容 / Function Content**
中文：M8的(d_opt,σ_opt)平衡点在σ<σ_opt时稳定，σ>σ_opt时不稳定——过分散的系统无法自发回到最优配置。σ>σ_opt的恢复需要外部干预（D306）。社会系统一旦过度分化，自发回归不可能。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的(d_opt,σ_opt)平衡点在σ<σ_opt时稳定，σ>σ_opt时不稳定——过分散的系统无法自发回到最优配置。σ>σ_opt的恢复需要外部干预（D306）。社会系统一旦过度分化，自发回归不可能。 描述 -σ_opt平衡稳定性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D306`, `D335`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D336｜多频叠加阶段响应函数](functions/items/D336.md)

**函数内容 / Function Content**
中文：M9的多频扰动叠加：低频+高频时高频被缓冲过滤，低频驱动过渡。但两个接近共振的频率产生拍频，拍频周期≈τ_buffer时产生二次共振——比单频共振更强的消耗。经济系统短周期+长周期的拍频可能产生超常衰退。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的多频扰动叠加：低频+高频时高频被缓冲过滤，低频驱动过渡。但两个接近共振的频率产生拍频，拍频周期≈τ_buffer时产生二次共振——比单频共振更强的消耗。经济系统短周期+长周期的拍频可能产生超常衰退。 描述 多频叠加阶段响应函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D336`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D337｜缓冲部分重建效率函数](functions/items/D337.md)

**函数内容 / Function Content**
中文：M10的缓冲从C₁到C₂的效率η∝(C₂-C₁)/(C_max-C₁)·ḡ·β。离C_max越近每单位重建越难。改革初期见效快（缓冲从0到C₁容易），后期见效慢——"容易的先做完"有数学根源。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的缓冲从C₁到C₂的效率η∝(C₂-C₁)/(C_max-C₁)·ḡ·β。离C_max越近每单位重建越难。改革初期见效快（缓冲从0到C₁容易），后期见效慢——"容易的先做完"有数学根源。 描述 缓冲部分重建效率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D337`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D338｜阶段2宽度-温度函数](functions/items/D338.md)

**函数内容 / Function Content**
中文：M11的w₂随T_eff升高而展宽：w₂(T)∝w₂(0)·(1+kT_eff/Φ_min)。高温使阶段边界模糊→缓冲期延长，但缓冲质量降低→更宽但更薄的缓冲。社会"流动性高"→改革窗口更宽但缓冲更弱→看似灵活实则脆弱。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的w₂随T_eff升高而展宽：w₂(T)∝w₂(0)·(1+kT_eff/Φ_min)。高温使阶段边界模糊→缓冲期延长，但缓冲质量降低→更宽但更薄的缓冲。社会"流动性高"→改革窗口更宽但缓冲更弱→看似灵活实则脆弱。 描述 阶段2宽度-温度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D338`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D339｜僵尸态救援函数](functions/items/D339.md)

**函数内容 / Function Content**
中文：M12的僵尸态外部救援最小力度F_rescue∝n·(g_critical-g_eff)²。n越大需要救援力度越大。但F_rescue存在上限F_max∝n·ḡ——超过此力度干预本身造成新伤害（D312噪声放大）。F_rescue>F_max时僵尸态不可救——组织太大且g_eff太低时，任何干预要么不够要么造成附带损伤。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的僵尸态外部救援最小力度F_rescue∝n·(g_critical-g_eff)²。n越大需要救援力度越大。但F_rescue存在上限F_max∝n·ḡ——超过此力度干预本身造成新伤害（D312噪声放大）。F_rescue>F_max时僵尸态不可救——组织太大且g_eff太低时，任何干预要么不够要么造成附带损伤。 描述 僵尸态救援函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D339`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D340｜正反馈饱和后振荡函数](functions/items/D340.md)

**函数内容 / Function Content**
中文：M13的K^k饱和后p_max在稳态附近振荡，振幅∝√(p_min·p_ss)/n，频率∝ḡ。K越大稳态越低但振荡越剧烈——强正反馈的精度和抖动之间的权衡。n大时振幅小→大系统饱和后平稳，n小时大幅波动。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的K^k饱和后p_max在稳态附近振荡，振幅∝√(p_min·p_ss)/n，频率∝ḡ。K越大稳态越低但振荡越剧烈——强正反馈的精度和抖动之间的权衡。n大时振幅小→大系统饱和后平稳，n小时大幅波动。 描述 正反馈饱和后振荡函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D340`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D341｜共存震荡阻尼函数](functions/items/D341.md)

**函数内容 / Function Content**
中文：M14的共存震荡阻尼∝|K_benign-α_exclusion|——偏离临界越远阻尼越大。临界处阻尼为零→持续震荡不衰减，每次震荡有随机偏移，最终随机漂移到良性或恶性方向。改革力量和保守力量势均力敌时最不稳定——不是静止而是持续震荡。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的共存震荡阻尼∝|K_benign-α_exclusion|——偏离临界越远阻尼越大。临界处阻尼为零→持续震荡不衰减，每次震荡有随机偏移，最终随机漂移到良性或恶性方向。改革力量和保守力量势均力敌时最不稳定——不是静止而是持续震荡。 描述 共存震荡阻尼函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D341`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D342｜ΔΦ时间累积函数](functions/items/D342.md)

**函数内容 / Function Content**
中文：M1的多轮ΔΦ叠加：容斥凸性(D266)使正ΔΦ权重>负ΔΦ权重，即使正负抵消均值零，累积效果仍为正。E[ΣΔΦᵢ] = ΣE[ΔΦᵢ] + ΣVar(ΔΦᵢ)/2 > ΣE[ΔΦᵢ]。容斥凸性使波动本身产生正向漂移——"折腾"本身就有害，不管方向。D266的动态版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的多轮ΔΦ叠加：容斥凸性(D266)使正ΔΦ权重>负ΔΦ权重，即使正负抵消均值零，累积效果仍为正。E[ΣΔΦᵢ] = ΣE[ΔΦᵢ] + ΣVar(ΔΦᵢ)/2 > ΣE[ΔΦᵢ]。容斥凸性使波动本身产生正向漂移——"折腾"本身就有害，不管方向。D266的动态版本。 描述 时间累积函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D266`, `D342`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D343｜极小点消失遗迹函数](functions/items/D343.md)

**函数内容 / Function Content**
中文：M2的极小点消失后Φ(μ)保留拐点。系统经过拐点时速度减慢（dμ/dt∝1/|d²Φ/dμ²|，拐点处极小）。"曾经的稳定状态"消失后，系统经过该位置时仍会短暂减速——旧秩序的"幽灵"效应。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的极小点消失后Φ(μ)保留拐点。系统经过拐点时速度减慢（dμ/dt∝1/|d²Φ/dμ²|，拐点处极小）。"曾经的稳定状态"消失后，系统经过该位置时仍会短暂减速——旧秩序的"幽灵"效应。 描述 极小点消失遗迹函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D343`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D344｜容斥关联动态函数](functions/items/D344.md)

**函数内容 / Function Content**
中文：M3的容斥关联从局部到全局的演化：关联范围∝max(pᵢ)/p̄。早期只有相邻门控面关联（局部），后期所有高p门控面关联（全局）。p_max/p̄超过阈值时容斥从局部问题变成全局问题——D328的动态版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的容斥关联从局部到全局的演化：关联范围∝max(pᵢ)/p̄。早期只有相邻门控面关联（局部），后期所有高p门控面关联（全局）。p_max/p̄超过阈值时容斥从局部问题变成全局问题——D328的动态版本。 描述 容斥关联动态函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D344`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D345｜p*涨落-噪声耦合函数](functions/items/D345.md)

**函数内容 / Function Content**
中文：M4的p*涨落被M13正反馈放大：δp*_amplified = δp*·K^k/(1+(K^k-1)·p_min/p*)。K>1时竞争阈值不确定→系统在容斥主导和耦合主导之间随机切换。正反馈使容斥-耦合竞争的随机性放大——即使参数在耦合主导区也可能因涨落被踢进容斥主导区。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的p*涨落被M13正反馈放大：δp*_amplified = δp*·K^k/(1+(K^k-1)·p_min/p*)。K>1时竞争阈值不确定→系统在容斥主导和耦合主导之间随机切换。正反馈使容斥-耦合竞争的随机性放大——即使参数在耦合主导区也可能因涨落被踢进容斥主导区。 描述 *涨落-噪声耦合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D345`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D346｜容斥主导区内部结构函数](functions/items/D346.md)

**函数内容 / Function Content**
中文：M5的容斥主导区有子结构：弱容斥主导（容斥占比50-70%，还有部分缓冲）vs强容斥主导（占比>90%，缓冲完全无效）。弱→强渐变，但D288有限时间崩溃在强容斥区加速。干预在弱容斥主导区还有可能，强容斥主导区无望。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的容斥主导区有子结构：弱容斥主导（容斥占比50-70%，还有部分缓冲）vs强容斥主导（占比>90%，缓冲完全无效）。弱→强渐变，但D288有限时间崩溃在强容斥区加速。干预在弱容斥主导区还有可能，强容斥主导区无望。 描述 容斥主导区内部结构函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D346`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D347｜维度回复非线性函数](functions/items/D347.md)

**函数内容 / Function Content**
中文：M6的d_eff偏离4较大时回复力非线性：F_restore∝-k·δ·(1+δ²/δ_c²)。δ>δ_c时回复力减弱——偏离太远弹不回来。δ_c∝1/√(Σαᵢ²/(1-pᵢ)²)——门控面越均匀线性区越宽，越不均匀越窄。不均匀系统的d=4稳定性是脆弱的——小扰动能弹回来，大扰动弹不回来。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的d_eff偏离4较大时回复力非线性：F_restore∝-k·δ·(1+δ²/δ_c²)。δ>δ_c时回复力减弱——偏离太远弹不回来。δ_c∝1/√(Σαᵢ²/(1-pᵢ)²)——门控面越均匀线性区越宽，越不均匀越窄。不均匀系统的d=4稳定性是脆弱的——小扰动能弹回来，大扰动弹不回来。 描述 维度回复非线性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D347`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D348｜容斥加速-时间权重联合函数](functions/items/D348.md)

**函数内容 / Function Content**
中文：M7的容斥加速使D316转折点提前：无加速时Σpᵢ≈0.5容斥主导，有加速时转折提前到Σpᵢ≈0.5/(1+a_excl·τ)。加速越强转折越早——"突然变坏"来得更早。a_excl∝n²使高n系统转折大幅提前——复杂系统不仅"变坏更快"而且"变坏更早"。双重加速：更早+更快。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速使D316转折点提前：无加速时Σpᵢ≈0.5容斥主导，有加速时转折提前到Σpᵢ≈0.5/(1+a_excl·τ)。加速越强转折越早——"突然变坏"来得更早。a_excl∝n²使高n系统转折大幅提前——复杂系统不仅"变坏更快"而且"变坏更早"。双重加速：更早+更快。 描述 容斥加速-时间权重联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D348`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.5`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D349｜过分散相图函数](functions/items/D349.md)

**函数内容 / Function Content**
中文：M8的σ>σ_opt时系统进入"维度饥渴"状态——需要更多维度补偿分散度但d不能无限增长。维度饥渴的结局：要么外部增加d（学习/改革），要么内部崩溃（Φ持续增长）。社会分化过度需要更多元化但做不到→僵局。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的σ>σ_opt时系统进入"维度饥渴"状态——需要更多维度补偿分散度但d不能无限增长。维度饥渴的结局：要么外部增加d（学习/改革），要么内部崩溃（Φ持续增长）。社会分化过度需要更多元化但做不到→僵局。 描述 过分散相图函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D349`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D350｜阶段过渡不可逆标记函数](functions/items/D350.md)

**函数内容 / Function Content**
中文：M9的阶段2→3后能否退回取决于C_consumed/C_max > η_irreversible ≈ 1-1/n。n大时η接近1（大系统有回旋余地），n小时η小（小系统缓冲薄）。但D323重建时间∝n²使大系统理论可逆但实际重建太慢——理论可逆与实际可逆的差距随n²增长。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的阶段2→3后能否退回取决于C_consumed/C_max > η_irreversible ≈ 1-1/n。n大时η接近1（大系统有回旋余地），n小时η小（小系统缓冲薄）。但D323重建时间∝n²使大系统理论可逆但实际重建太慢——理论可逆与实际可逆的差距随n²增长。 描述 阶段过渡不可逆标记函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D350`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D351｜缓冲关联结构函数](functions/items/D351.md)

**函数内容 / Function Content**
中文：M10的不同门控面缓冲不独立——高p门控面缓冲消耗"溢出"到低p门控面。溢出系数∝ḡ——耦合越强溢出越大。局部冲击通过溢出变成全局冲击——金融系统单个机构出问题引发系统性风险的数学结构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的不同门控面缓冲不独立——高p门控面缓冲消耗"溢出"到低p门控面。溢出系数∝ḡ——耦合越强溢出越大。局部冲击通过溢出变成全局冲击——金融系统单个机构出问题引发系统性风险的数学结构。 描述 缓冲关联结构函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D351`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D352｜阶段2宽度-共振频率函数](functions/items/D352.md)

**函数内容 / Function Content**
中文：M11的w₂决定共振频率ω_resonance∝1/w₂。窄缓冲区→高频共振。w₂缩窄（D324 n增大）使系统从"怕低频共振"变成"怕高频共振"——复杂系统的脆弱频率随复杂度上移。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的w₂决定共振频率ω_resonance∝1/w₂。窄缓冲区→高频共振。w₂缩窄（D324 n增大）使系统从"怕低频共振"变成"怕高频共振"——复杂系统的脆弱频率随复杂度上移。 描述 阶段2宽度-共振频率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D324`, `D352`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D353｜僵尸态传染函数](functions/items/D353.md)

**函数内容 / Function Content**
中文：M12的子系统僵尸化通过g_eff耦合传染：传染速度∝ḡ/n。临界条件：僵尸化子系统数>n/2时总g_eff<g_critical→全局僵尸化。组织超过一半部门僵尸化后全局不可逆——D339的传染版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的子系统僵尸化通过g_eff耦合传染：传染速度∝ḡ/n。临界条件：僵尸化子系统数>n/2时总g_eff<g_critical→全局僵尸化。组织超过一半部门僵尸化后全局不可逆——D339的传染版本。 描述 僵尸态传染函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D353`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D354｜正反馈延迟函数](functions/items/D354.md)

**函数内容 / Function Content**
中文：M13的正反馈有延迟τ_delay时，频率ω=π/τ_delay处正反馈变负反馈。延迟足够大时系统自激振荡。自激振荡条件：K·τ_delay>1。政策反馈延迟过大时本意正反馈的改革变成振荡——每次纠偏都矫枉过正→来回摆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的正反馈有延迟τ_delay时，频率ω=π/τ_delay处正反馈变负反馈。延迟足够大时系统自激振荡。自激振荡条件：K·τ_delay>1。政策反馈延迟过大时本意正反馈的改革变成振荡——每次纠偏都矫枉过正→来回摆。 描述 正反馈延迟函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D354`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `π`: math_builtin / derived - π is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D355｜共存震荡分支函数](functions/items/D355.md)

**函数内容 / Function Content**
中文：M14的共存震荡中随机偏移δK∝√(kT_eff)·T_osc。偏移累积为随机游走，最终方向由累积符号决定。预期决定时间T_decision∝(ΔK/δK)²·T_osc——初始偏置越大决定越快，ΔK≈0时可能长期震荡。改革派和保守派差距越小僵局持续越久——随机游走到达边界的时间。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的共存震荡中随机偏移δK∝√(kT_eff)·T_osc。偏移累积为随机游走，最终方向由累积符号决定。预期决定时间T_decision∝(ΔK/δK)²·T_osc——初始偏置越大决定越快，ΔK≈0时可能长期震荡。改革派和保守派差距越小僵局持续越久——随机游走到达边界的时间。 描述 共存震荡分支函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D355`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D356｜ΔΦ时空关联函数](functions/items/D356.md)

**函数内容 / Function Content**
中文：M1的不同门控面ΔΦ的时间交叉相关∝pᵢpⱼ·e^{-τ/τ_relax}。容斥项使高p门控面之间有正交叉相关。一个门控面恶化预测其他门控面随后恶化——"坏消息成群来"的数学根源不是运气差而是容斥交叉相关。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的不同门控面ΔΦ的时间交叉相关∝pᵢpⱼ·e^{-τ/τ_relax}。容斥项使高p门控面之间有正交叉相关。一个门控面恶化预测其他门控面随后恶化——"坏消息成群来"的数学根源不是运气差而是容斥交叉相关。 描述 时空关联函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D356`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D357｜极小点复活函数](functions/items/D357.md)

**函数内容 / Function Content**
中文：M2的拐点重新变成极小点需要至少一个pᵢ下降使容斥项减小。复活需要的pᵢ下降量Δp_rescue∝Φ(拐点)/n。极小点复活比维持极小点困难得多——D264良性循环启动阈值的几何版本。旧秩序"复兴"需要比维持旧秩序更大的努力——复兴不是恢复而是重建。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的拐点重新变成极小点需要至少一个pᵢ下降使容斥项减小。复活需要的pᵢ下降量Δp_rescue∝Φ(拐点)/n。极小点复活比维持极小点困难得多——D264良性循环启动阈值的几何版本。旧秩序"复兴"需要比维持旧秩序更大的努力——复兴不是恢复而是重建。 描述 极小点复活函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D357`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D358｜容斥关联对称性破缺函数](functions/items/D358.md)

**函数内容 / Function Content**
中文：M3的(i,j)和(j,i)在pᵢ≠pⱼ时贡献不同：低p门控面受高p门控面影响大，高p受低p影响小。容斥关联的不对称性是阶层固化的数学机制之一——弱者受强者的容斥影响远大于强者受弱者。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的(i,j)和(j,i)在pᵢ≠pⱼ时贡献不同：低p门控面受高p门控面影响大，高p受低p影响小。容斥关联的不对称性是阶层固化的数学机制之一——弱者受强者的容斥影响远大于强者受弱者。 描述 容斥关联对称性破缺函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D358`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D359｜p*放大涨落-有限n联合函数](functions/items/D359.md)

**函数内容 / Function Content**
中文：M4的p*放大涨落对有限n系统：K^k>√n时放大后涨落超过p*→竞争结果完全随机。临界K_c=√n。n越大临界K越大（大系统更耐受正反馈放大），但一旦超过临界崩溃更彻底。小系统先乱但乱得有限，大系统后乱但乱得致命。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的p*放大涨落对有限n系统：K^k>√n时放大后涨落超过p*→竞争结果完全随机。临界K_c=√n。n越大临界K越大（大系统更耐受正反馈放大），但一旦超过临界崩溃更彻底。小系统先乱但乱得有限，大系统后乱但乱得致命。 描述 *放大涨落-有限n联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D359`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D360｜弱容斥-不可逆边界函数](functions/items/D360.md)

**函数内容 / Function Content**
中文：M5的弱容斥主导区是否在不可逆线之前取决于n。n小时弱容斥=不可逆（无窗口），n大时有"容斥主导但还可逆"窗口，宽度∝(√n-1)/n∝D310。大系统有"容斥主导但还有救"的窗口，小系统没有。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的弱容斥主导区是否在不可逆线之前取决于n。n小时弱容斥=不可逆（无窗口），n大时有"容斥主导但还可逆"窗口，宽度∝(√n-1)/n∝D310。大系统有"容斥主导但还有救"的窗口，小系统没有。 描述 弱容斥-不可逆边界函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D310`, `D360`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D361｜维度回复非线性-阻尼联合函数](functions/items/D361.md)

**函数内容 / Function Content**
中文：M6的大偏离使阻尼也非线性：γ_eff = γ₀·(1-δ²/δ_c²)。δ→δ_c时γ_eff→0→振荡加剧→偏离更大→正反馈。δ_c是维度回复的"不归点"——与D295 p_max不可逆点同构。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的大偏离使阻尼也非线性：γ_eff = γ₀·(1-δ²/δ_c²)。δ→δ_c时γ_eff→0→振荡加剧→偏离更大→正反馈。δ_c是维度回复的"不归点"——与D295 p_max不可逆点同构。 描述 维度回复非线性-阻尼联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D361`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D362｜容斥加速-波动累积联合函数](functions/items/D362.md)

**函数内容 / Function Content**
中文：M7的容斥加速放大D342波动累积：E[ΣΔΦ]_accelerated = ΣE[ΔΦᵢ] + ΣVar(ΔΦᵢ)·(1+a_excl·τ)/2。容斥加速不只加速均值增长还加速波动累积——"折腾更有害"在加速环境下被放大。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的容斥加速放大D342波动累积：E[ΣΔΦ]_accelerated = ΣE[ΔΦᵢ] + ΣVar(ΔΦᵢ)·(1+a_excl·τ)/2。容斥加速不只加速均值增长还加速波动累积——"折腾更有害"在加速环境下被放大。 描述 容斥加速-波动累积联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D362`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D363｜维度饥渴感知函数](functions/items/D363.md)

**函数内容 / Function Content**
中文：M8的维度饥渴感知信号：超额Φ增长率Δ(dΦ/dt)∝(σ-σ_opt)²·ḡ。感知到饥渴到响应之间有延迟τ_σ∝n/ḡ。大系统感知慢响应也慢→维度饥渴持续时间∝n²/ḡ²。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的维度饥渴感知信号：超额Φ增长率Δ(dΦ/dt)∝(σ-σ_opt)²·ḡ。感知到饥渴到响应之间有延迟τ_σ∝n/ḡ。大系统感知慢响应也慢→维度饥渴持续时间∝n²/ḡ²。 描述 维度饥渴感知函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D363`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D364｜实际不可逆判据函数](functions/items/D364.md)

**函数内容 / Function Content**
中文：M9的实际不可逆=理论可逆但重建时间超过剩余寿命：τ_rebuild > T_remaining。条件：n²·p̄/β > 1/(Σαᵢ)——n大p̄高β低时几乎必然实际不可逆。大系统高负担弱改革的组合=实际不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的实际不可逆=理论可逆但重建时间超过剩余寿命：τ_rebuild > T_remaining。条件：n²·p̄/β > 1/(Σαᵢ)——n大p̄高β低时几乎必然实际不可逆。大系统高负担弱改革的组合=实际不可逆。 描述 实际不可逆判据函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D364`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D365｜缓冲溢出方向函数](functions/items/D365.md)

**函数内容 / Function Content**
中文：M10的缓冲消耗溢出方向不对称：高p→低p方向溢出强，反向弱∝1/p_max。核心部门出问题冲击全局，边缘部门影响有限——组织"核心-边缘"不对称性的数学根源。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的缓冲消耗溢出方向不对称：高p→低p方向溢出强，反向弱∝1/p_max。核心部门出问题冲击全局，边缘部门影响有限——组织"核心-边缘"不对称性的数学根源。 描述 缓冲溢出方向函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D365`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D366｜共振频率-消耗效率函数](functions/items/D366.md)

**函数内容 / Function Content**
中文：M11的高频共振消耗效率低于低频（表面消耗vs均匀消耗），但高频更难被缓冲过滤→穿透力强。快速冲击每次伤害不大但无法被缓冲挡住——慢性消耗比急性冲击更难防御。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的高频共振消耗效率低于低频（表面消耗vs均匀消耗），但高频更难被缓冲过滤→穿透力强。快速冲击每次伤害不大但无法被缓冲挡住——慢性消耗比急性冲击更难防御。 描述 共振频率-消耗效率函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D366`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D367｜僵尸态传染免疫函数](functions/items/D367.md)

**函数内容 / Function Content**
中文：M12的免疫裕度Δg_i = g_eff(i) - g_critical。Δg_i > δg_spread时免疫。但D351溢出使免疫子系统也被消耗→免疫不是永久的。组织中"健康部门"不能独善其身——溢出最终消耗免疫裕度。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的免疫裕度Δg_i = g_eff(i) - g_critical。Δg_i > δg_spread时免疫。但D351溢出使免疫子系统也被消耗→免疫不是永久的。组织中"健康部门"不能独善其身——溢出最终消耗免疫裕度。 描述 僵尸态传染免疫函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D367`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D368｜延迟-噪声频谱函数](functions/items/D368.md)

**函数内容 / Function Content**
中文：M13的延迟使噪声放大成为低通滤波：低频放大K倍，高频放大降至K/(1+ω²τ_delay²)。延迟过滤了高频噪声但代价是D354自激振荡风险。政策延迟使系统对长期趋势敏感但对短期波动不敏感——延迟不全是坏事。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的延迟使噪声放大成为低通滤波：低频放大K倍，高频放大降至K/(1+ω²τ_delay²)。延迟过滤了高频噪声但代价是D354自激振荡风险。政策延迟使系统对长期趋势敏感但对短期波动不敏感——延迟不全是坏事。 描述 延迟-噪声频谱函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D368`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D369｜震荡阻尼-分支步长联合函数](functions/items/D369.md)

**函数内容 / Function Content**
中文：M14的阻尼影响步长：高阻尼→步长小→决定慢但方向确定；低阻尼→步长大→决定快但方向随机。T_decision∝|K_benign-α_exclusion|·T_osc。改革力量明显占优时方向确定但推进慢，势均力敌时推进快但方向不确定——速度和确定性的反比关系。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的阻尼影响步长：高阻尼→步长小→决定慢但方向确定；低阻尼→步长大→决定快但方向随机。T_decision∝|K_benign-α_exclusion|·T_osc。改革力量明显占优时方向确定但推进慢，势均力敌时推进快但方向不确定——速度和确定性的反比关系。 描述 震荡阻尼-分支步长联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D369`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D370｜ΔΦ交叉相关-波动累积联合函数](functions/items/D370.md)

**函数内容 / Function Content**
中文：M1的容斥交叉相关增强D342波动累积：交叉相关项Cov∝pᵢpⱼ使总方差增大→波动累积更严重。增强因子∝1+Σᵢ<ⱼpᵢpⱼ/ΣVar(ΔΦᵢ)。"坏消息成群来"不只预测恶化还放大"折腾有害"——双重打击。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的容斥交叉相关增强D342波动累积：交叉相关项Cov∝pᵢpⱼ使总方差增大→波动累积更严重。增强因子∝1+Σᵢ<ⱼpᵢpⱼ/ΣVar(ΔΦᵢ)。"坏消息成群来"不只预测恶化还放大"折腾有害"——双重打击。 描述 交叉相关-波动累积联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D370`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D371｜极小点复活代价函数](functions/items/D371.md)

**函数内容 / Function Content**
中文：M2的极小点复活总代价∝Φ(拐点)，与n无关。但D264启动阈值∝(n-1)/n→n大时启动更难。联合：复活代价本身不随n增长，但启动阈值随n增长→大系统复活更难不是因为代价大而是因为启动难。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的极小点复活总代价∝Φ(拐点)，与n无关。但D264启动阈值∝(n-1)/n→n大时启动更难。联合：复活代价本身不随n增长，但启动阈值随n增长→大系统复活更难不是因为代价大而是因为启动难。 描述 极小点复活代价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D371`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D372｜对称性破缺-关联拓扑联合函数](functions/items/D372.md)

**函数内容 / Function Content**
中文：M3的不对称性使前3个高p门控面容斥贡献从>50%升至>60%。降p_max效果比D330估计的更大——不只切断最大关联对，还削弱不对称性对低p门控面的压制。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的不对称性使前3个高p门控面容斥贡献从>50%升至>60%。降p_max效果比D330估计的更大——不只切断最大关联对，还削弱不对称性对低p门控面的压制。 描述 对称性破缺-关联拓扑联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D372`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D373｜p*临界标度函数](functions/items/D373.md)

**函数内容 / Function Content**
中文：M4的K=√n临界附近标度律：涨落方差∝1/|K-√n|，关联时间∝1/|K-√n|。临界指数β=1/2（平均场），γ=1。与Ising模型同构——容斥-耦合竞争临界点是平均场相变，普适类与Ising相同。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的K=√n临界附近标度律：涨落方差∝1/|K-√n|，关联时间∝1/|K-√n|。临界指数β=1/2（平均场），γ=1。与Ising模型同构——容斥-耦合竞争临界点是平均场相变，普适类与Ising相同。 描述 *临界标度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D373`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D374｜弱容斥窗口-逃逸速度联合函数](functions/items/D374.md)

**函数内容 / Function Content**
中文：M5的弱容斥窗口内逃逸速度v_escape(弱容斥)=v_escape(耦合主导)·(1-f_excl)^(1/2)。窗口内D289黄金逃逸点仍有效但效率降低。窗口边界处v_escape→0——D332不可逆线即逃逸速度归零线。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的弱容斥窗口内逃逸速度v_escape(弱容斥)=v_escape(耦合主导)·(1-f_excl)^(1/2)。窗口内D289黄金逃逸点仍有效但效率降低。窗口边界处v_escape→0——D332不可逆线即逃逸速度归零线。 描述 弱容斥窗口-逃逸速度联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D374`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D375｜维度不归点-退化路径联合函数](functions/items/D375.md)

**函数内容 / Function Content**
中文：M6的δ_c不归点恰好是D305退化路径的分叉点。δ<δ_c在d=4附近振荡（可回复），δ>δ_c沿退化路径滑走。δ_c是"还能弹回来"和"开始滑走"的精确分界——退化路径的启动条件。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的δ_c不归点恰好是D305退化路径的分叉点。δ<δ_c在d=4附近振荡（可回复），δ>δ_c沿退化路径滑走。δ_c是"还能弹回来"和"开始滑走"的精确分界——退化路径的启动条件。 描述 维度不归点-退化路径联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D375`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D376｜加速-波动累积极限函数](functions/items/D376.md)

**函数内容 / Function Content**
中文：M7的联合效应极限∝-ln(P_min)∝n——n越大极限越高→大系统能承受更多累积但代价是D364实际不可逆。系统在累积到无穷前先死。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的联合效应极限∝-ln(P_min)∝n——n越大极限越高→大系统能承受更多累积但代价是D364实际不可逆。系统在累积到无穷前先死。 描述 加速-波动累积极限函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D376`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D377｜感知-调整双延迟函数](functions/items/D377.md)

**函数内容 / Function Content**
中文：M8的总响应时间τ_total = τ_perceive + τ_σ。小偏离时瓶颈是感知（信号弱），大偏离时瓶颈是调整（n大调整慢）。维度饥渴早期的瓶颈是感知，晚期的瓶颈是调整。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的总响应时间τ_total = τ_perceive + τ_σ。小偏离时瓶颈是感知（信号弱），大偏离时瓶颈是调整（n大调整慢）。维度饥渴早期的瓶颈是感知，晚期的瓶颈是调整。 描述 感知-调整双延迟函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D377`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D378｜实际不可逆占比函数](functions/items/D378.md)

**函数内容 / Function Content**
中文：M9的R_irreversible ≈ 1 - e^{-n²·p̄·Σαᵢ/β}。n=10时R≈0.3，n=100时R≈0.95。复杂度超过阈值后实际不可逆几乎覆盖全部理论可逆空间——大系统的"理论可逆"基本没有实际意义。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的R_irreversible ≈ 1 - e^{-n²·p̄·Σαᵢ/β}。n=10时R≈0.3，n=100时R≈0.95。复杂度超过阈值后实际不可逆几乎覆盖全部理论可逆空间——大系统的"理论可逆"基本没有实际意义。 描述 实际不可逆占比函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D378`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.
  - `0.3`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D379｜定向溢出强度函数](functions/items/D379.md)

**函数内容 / Function Content**
中文：M10的溢出量∝ḡ·p_max·ΔC_i/n，方向系数∝p_max/p̄。p_max>>p̄时溢出几乎全部向低p方向→低p门控面被"淹没"。核心部门问题越大边缘部门受害越重——有了精确强度。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的溢出量∝ḡ·p_max·ΔC_i/n，方向系数∝p_max/p̄。p_max>>p̄时溢出几乎全部向低p方向→低p门控面被"淹没"。核心部门问题越大边缘部门受害越重——有了精确强度。 描述 定向溢出强度函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D379`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D380｜慢性-急性消耗比较函数](functions/items/D380.md)

**函数内容 / Function Content**
中文：M11的慢性vs急性：总危险度=消耗量×不可重建性。急性高消耗×低不可重建性；慢性低消耗×高不可重建性。慢性持续时间>τ_rebuild时慢性总危险度超过急性——长期慢性消耗比短期急性冲击更致命。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的慢性vs急性：总危险度=消耗量×不可重建性。急性高消耗×低不可重建性；慢性低消耗×高不可重建性。慢性持续时间>τ_rebuild时慢性总危险度超过急性——长期慢性消耗比短期急性冲击更致命。 描述 慢性-急性消耗比较函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D380`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D381｜免疫消耗-传染临界联合函数](functions/items/D381.md)

**函数内容 / Function Content**
中文：M12的溢出消耗免疫使传染临界从n/2降至n_eff/2 = n/2 - ΣΔg_consumed/δg_spread。极端情况三分之一僵尸化即可全局崩溃——核心部门问题通过溢出消耗免疫力使整体比看起来更脆弱。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的溢出消耗免疫使传染临界从n/2降至n_eff/2 = n/2 - ΣΔg_consumed/δg_spread。极端情况三分之一僵尸化即可全局崩溃——核心部门问题通过溢出消耗免疫力使整体比看起来更脆弱。 描述 免疫消耗-传染临界联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D381`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D382｜低通滤波-自激振荡竞争函数](functions/items/D382.md)

**函数内容 / Function Content**
中文：M13的K·τ_delay<1时低通滤波主导（延迟有益），>1时自激振荡主导（延迟有害），=1为临界。弱正反馈系统中延迟可以有益（过滤噪声），强正反馈系统中延迟必然有害（引发振荡）。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的K·τ_delay<1时低通滤波主导（延迟有益），>1时自激振荡主导（延迟有害），=1为临界。弱正反馈系统中延迟可以有益（过滤噪声），强正反馈系统中延迟必然有害（引发振荡）。 描述 低通滤波-自激振荡竞争函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D382`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D383｜逃逸速度-确定性权衡函数](functions/items/D383.md)

**函数内容 / Function Content**
中文：M14的高确定性逃逸需要慢速推进，低确定性可快速但可能逃错方向。最优策略：初期低确定性快速探索方向，确认后切换高确定性慢速推进。D280两步策略的动态版本：先探索（降p_max确认方向），再巩固（均匀修缮）。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的高确定性逃逸需要慢速推进，低确定性可快速但可能逃错方向。最优策略：初期低确定性快速探索方向，确认后切换高确定性慢速推进。D280两步策略的动态版本：先探索（降p_max确认方向），再巩固（均匀修缮）。 描述 逃逸速度-确定性权衡函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D383`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D384｜双重打击-双重加速同构函数](functions/items/D384.md)

**函数内容 / Function Content**
中文：M1的D370与D348不同构：D370是方差修正（二阶），D348是均值修正（一阶）。联合效果：趋势加速×波动加速=总加速∝1/(1+a_excl·τ)·(1+Σpᵢpⱼ/ΣVar(ΔΦᵢ))——趋势和波动的双重双重加速。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的D370与D348不同构：D370是方差修正（二阶），D348是均值修正（一阶）。联合效果：趋势加速×波动加速=总加速∝1/(1+a_excl·τ)·(1+Σpᵢpⱼ/ΣVar(ΔΦᵢ))——趋势和波动的双重双重加速。 描述 双重打击-双重加速同构函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D384`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D385｜复活代价n无关性起源函数](functions/items/D385.md)

**函数内容 / Function Content**
中文：M2的复活总代价∝Φ(拐点)与n无关的原因：Φ(拐点)是全局量已包含n信息。每个门控面平均代价∝Φ/n随n减小，但总代价守恒。类比：修复桥的总成本取决于损坏程度而非构件数——构件越多每个修复量越少但总量不变。守恒律：复活总代价=拐点处Φ值。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的复活总代价∝Φ(拐点)与n无关的原因：Φ(拐点)是全局量已包含n信息。每个门控面平均代价∝Φ/n随n减小，但总代价守恒。类比：修复桥的总成本取决于损坏程度而非构件数——构件越多每个修复量越少但总量不变。守恒律：复活总代价=拐点处Φ值。 描述 复活代价n无关性起源函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D385`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D386｜容斥集中性统一函数](functions/items/D386.md)

**函数内容 / Function Content**
中文：M3的D372与D328是同一现象不同表述。统一指标I_concentration = max(ΔΦᵢ)/ΣΔΦᵢ·(1+ln(n))。I→1完全集中，I→0完全分散。I随p_max/p̄单调递增——降p_max不只降Φ还降低集中性→容斥从集中变分散→系统更均匀。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的D372与D328是同一现象不同表述。统一指标I_concentration = max(ΔΦᵢ)/ΣΔΦᵢ·(1+ln(n))。I→1完全集中，I→0完全分散。I随p_max/p̄单调递增——降p_max不只降Φ还降低集中性→容斥从集中变分散→系统更均匀。 描述 容斥集中性统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D386`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D387｜容斥-耦合配分函数](functions/items/D387.md)

**函数内容 / Function Content**
中文：M4的Ising同构意味着配分函数Z = Σ e^{-β_H·H}，H = -ḡ·Σsᵢsⱼ + Σpᵢ·sᵢ，sᵢ=±1。ḡ对应Ising的J，pᵢ对应外场h。临界温度T_c ∝ ḡ·√n。容斥-耦合竞争的全部统计性质可由标准统计力学方法计算——自由能、磁化率、关联函数等。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的Ising同构意味着配分函数Z = Σ e^{-β_H·H}，H = -ḡ·Σsᵢsⱼ + Σpᵢ·sᵢ，sᵢ=±1。ḡ对应Ising的J，pᵢ对应外场h。临界温度T_c ∝ ḡ·√n。容斥-耦合竞争的全部统计性质可由标准统计力学方法计算——自由能、磁化率、关联函数等。 描述 容斥-耦合配分函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D387`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D388｜不可逆线相交函数](functions/items/D388.md)

**函数内容 / Function Content**
中文：M5的D332与D295在(p_max,n)空间相交于p_max=p*且n=n_c。n<n_c时p_max不可逆先到，n>n_c时容斥主导不可逆先到。大系统先进入容斥主导再触及p_max不可逆，小系统反过来。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的D332与D295在(p_max,n)空间相交于p_max=p*且n=n_c。n<n_c时p_max不可逆先到，n>n_c时容斥主导不可逆先到。大系统先进入容斥主导再触及p_max不可逆，小系统反过来。 描述 不可逆线相交函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D388`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D389｜不归点-吸引域边界统一函数](functions/items/D389.md)

**函数内容 / Function Content**
中文：M6的δ_c恰好是D292吸引域的边界。吸引域深度∝Σαᵢ²/(1-pᵢ)²，δ_c∝1/√(Σαᵢ²/(1-pᵢ)²)——深度和δ_c是同一量的正反面。深度描述域内稳定性，δ_c描述域的边界。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的δ_c恰好是D292吸引域的边界。吸引域深度∝Σαᵢ²/(1-pᵢ)²，δ_c∝1/√(Σαᵢ²/(1-pᵢ)²)——深度和δ_c是同一量的正反面。深度描述域内稳定性，δ_c描述域的边界。 描述 不归点-吸引域边界统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D389`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D390｜极限-不可逆n依赖协调函数](functions/items/D390.md)

**函数内容 / Function Content**
中文：M7的D376∝n与D378∝n²不矛盾：容量增长线性但不可逆增长超线性→净效果是大系统更脆弱。临界n*∝β/(p̄·Σαᵢ)——干预力度β够大时n*大（大系统还能撑），β小时n*小（大系统必死）。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的D376∝n与D378∝n²不矛盾：容量增长线性但不可逆增长超线性→净效果是大系统更脆弱。临界n*∝β/(p̄·Σαᵢ)——干预力度β够大时n*大（大系统还能撑），β小时n*小（大系统必死）。 描述 极限-不可逆n依赖协调函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D390`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D391｜双延迟-共振频率联合函数](functions/items/D391.md)

**函数内容 / Function Content**
中文：M8的感知延迟使有效τ_buffer增大→共振频率降低。ω_res_effective = ω_res/(1+τ_perceive/τ_σ)。感知慢的系统共振频率低→怕低频共振。维度饥渴感知慢使脆弱频率下移。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的感知延迟使有效τ_buffer增大→共振频率降低。ω_res_effective = ω_res/(1+τ_perceive/τ_σ)。感知慢的系统共振频率低→怕低频共振。维度饥渴感知慢使脆弱频率下移。 描述 双延迟-共振频率联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D391`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D392｜不可逆-缓冲消失同步函数](functions/items/D392.md)

**函数内容 / Function Content**
中文：M9的R以指数趋近1，w₂以1/√n趋近0。R先满（n≈100时R≈0.95），w₂后消失（n→∞）。中间存在"几乎全部不可逆但缓冲期仍名义存在"的状态——D311僵尸态的宏观版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的R以指数趋近1，w₂以1/√n趋近0。R先满（n≈100时R≈0.95），w₂后消失（n→∞）。中间存在"几乎全部不可逆但缓冲期仍名义存在"的状态——D311僵尸态的宏观版本。 描述 不可逆-缓冲消失同步函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D392`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.95`: calibration_or_example_value / source_grounded - This number is a normalized threshold, approximation band, or worked-example value. It is carried by the source row and checked by the local function/case context, but is not promoted to a universal structural constant.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D393｜溢出-传染通道统一函数](functions/items/D393.md)

**函数内容 / Function Content**
中文：M10的溢出是传染的物理通道。统一传染链：高p恶化→溢出消耗低p缓冲(D379)→低p缓冲<g_critical(D309)→低p僵尸化→总g_eff下降→更多溢出。正反馈传染链。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的溢出是传染的物理通道。统一传染链：高p恶化→溢出消耗低p缓冲(D379)→低p缓冲<g_critical(D309)→低p僵尸化→总g_eff下降→更多溢出。正反馈传染链。 描述 溢出-传染通道统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D309`, `D379`, `D393`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D394｜慢性消耗-波动累积同构检验](functions/items/D394.md)

**函数内容 / Function Content**
中文：M11的D380与D342不同构——D342是时间域累积效应，D380是频率域穿透效应。但极限情况下等价：无限长时间慢性消耗=无限多次小波动累积。统一：慢性消耗是波动累积在连续时间极限下的表现。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的D380与D342不同构——D342是时间域累积效应，D380是频率域穿透效应。但极限情况下等价：无限长时间慢性消耗=无限多次小波动累积。统一：慢性消耗是波动累积在连续时间极限下的表现。 描述 慢性消耗-波动累积同构检验。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D394`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D395｜传染临界n依赖函数](functions/items/D395.md)

**函数内容 / Function Content**
中文：M12的n_eff/2 = n/2 - ḡ·p_max/δg_spread。n越大免疫消耗对传染临界影响比例越小→大系统更接近n/2理论值，小系统传染临界被拉低更多。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的n_eff/2 = n/2 - ḡ·p_max/δg_spread。n越大免疫消耗对传染临界影响比例越小→大系统更接近n/2理论值，小系统传染临界被拉低更多。 描述 传染临界n依赖函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D395`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D396｜延迟临界-不可逆点统一函数](functions/items/D396.md)

**函数内容 / Function Content**
中文：M13的D382与D295在参数空间形成两条不可逆线。交点以下正反馈不可逆先到，交点以上振荡不可逆先到。小系统先触及正反馈不可逆，大系统先触及振荡不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的D382与D295在参数空间形成两条不可逆线。交点以下正反馈不可逆先到，交点以上振荡不可逆先到。小系统先触及正反馈不可逆，大系统先触及振荡不可逆。 描述 延迟临界-不可逆点统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D396`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D397｜两步策略最优性证明函数](functions/items/D397.md)

**函数内容 / Function Content**
中文：M14的D280两步策略是最小化T_escape的策略。最优分配：t_explore/t_consolidate = √(v_slow/v_fast)。两步策略最优当且仅当v_fast>>v_slow且P_correct在探索后显著提升——即不确定性高的系统才需要两步。确定性高的系统直接一步慢速推进即可。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的D280两步策略是最小化T_escape的策略。最优分配：t_explore/t_consolidate = √(v_slow/v_fast)。两步策略最优当且仅当v_fast>>v_slow且P_correct在探索后显著提升——即不确定性高的系统才需要两步。确定性高的系统直接一步慢速推进即可。 描述 两步策略最优性证明函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D397`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D398｜趋势-波动主导切换函数](functions/items/D398.md)

**函数内容 / Function Content**
中文：M1的R_tw = (a_excl·τ)/(Σpᵢpⱼ/ΣVar)。R_tw>>1趋势主导，<<1波动主导。早期波动主导（随机波动被放大），晚期趋势主导（确定性加速）。衰退从"随机"切换到"确定"——D316转折点的动态版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的R_tw = (a_excl·τ)/(Σpᵢpⱼ/ΣVar)。R_tw>>1趋势主导，<<1波动主导。早期波动主导（随机波动被放大），晚期趋势主导（确定性加速）。衰退从"随机"切换到"确定"——D316转折点的动态版本。 描述 趋势-波动主导切换函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D398`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D399｜漂移速率-复活代价联合函数](functions/items/D399.md)

**函数内容 / Function Content**
中文：M2的快速漂移使复活代价快速变化。极小点向深处漂移（学习）→拐点Φ增大→复活代价增大→复活窗口关闭。学习使极小点更深但使旧极小点复活更难——进步的代价是旧路不可逆。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的快速漂移使复活代价快速变化。极小点向深处漂移（学习）→拐点Φ增大→复活代价增大→复活窗口关闭。学习使极小点更深但使旧极小点复活更难——进步的代价是旧路不可逆。 描述 漂移速率-复活代价联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D399`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D400｜集中性-序参量统一函数](functions/items/D400.md)

**函数内容 / Function Content**
中文：M3的I_concentration正是D387配分函数的序参量——磁化强度m的线性映射I=(1+m)/2。降p_max既降Φ也降低m→降低I→容斥从有序变无序。D386和D387完全统一。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的I_concentration正是D387配分函数的序参量——磁化强度m的线性映射I=(1+m)/2。降p_max既降Φ也降低m→降低I→容斥从有序变无序。D386和D387完全统一。 描述 集中性-序参量统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D400`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D401｜自由能-Φ等价函数](functions/items/D401.md)

**函数内容 / Function Content**
中文：M4的Φ是零温自由能。有限温F = Φ - n·kT·ln2。临界温度kT_c~Φ/n∝ḡ——与D387一致。点火框架与统计力学的等价性在零温极限下精确成立。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的Φ是零温自由能。有限温F = Φ - n·kT·ln2。临界温度kT_c~Φ/n∝ḡ——与D387一致。点火框架与统计力学的等价性在零温极限下精确成立。 描述 自由能-Φ等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D401`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `ln2`: math_builtin / derived - ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D402｜不可逆相交-临界标度联合函数](functions/items/D402.md)

**函数内容 / Function Content**
中文：M5的D388交点处K=1（确定性不可逆），D359临界K=√n（统计不可逆）。确定性不可逆先于统计不可逆——K=1时系统确定性地进入不可逆，K=√n时涨落使不可逆变得随机。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M5的D388交点处K=1（确定性不可逆），D359临界K=√n（统计不可逆）。确定性不可逆先于统计不可逆——K=1时系统确定性地进入不可逆，K=√n时涨落使不可逆变得随机。 描述 不可逆相交-临界标度联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D402`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D403｜δ_c-相变点统一函数](functions/items/D403.md)

**函数内容 / Function Content**
中文：M6的δ_c对应配分函数中耦合-容斥相变的临界场强h_c。h_c∝T_c∝ḡ·√n→δ_c∝1/(ḡ·√n)——与D389完全一致。δ_c就是统计力学相变的临界场强。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的δ_c对应配分函数中耦合-容斥相变的临界场强h_c。h_c∝T_c∝ḡ·√n→δ_c∝1/(ḡ·√n)——与D389完全一致。δ_c就是统计力学相变的临界场强。 描述 δ_c-相变点统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D403`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D404｜双临界n统一函数](functions/items/D404.md)

**函数内容 / Function Content**
中文：M7的n*∝β/(p̄·Σαᵢ)依赖干预力度β，n_c由系统内在参数决定。β够大时n*<n_c——强干预使大系统在容斥主导不可逆之前就恢复。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的n*∝β/(p̄·Σαᵢ)依赖干预力度β，n_c由系统内在参数决定。β够大时n*<n_c——强干预使大系统在容斥主导不可逆之前就恢复。 描述 双临界n统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D404`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D405｜共振频率方向竞争函数](functions/items/D405.md)

**函数内容 / Function Content**
中文：M8的感知延迟使频率下移，复杂度使频率上移。交叉n_cross∝(1+τ_ratio)²。感知延迟越严重需要越大的系统才从"怕低频"切换到"怕高频"。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M8的感知延迟使频率下移，复杂度使频率上移。交叉n_cross∝(1+τ_ratio)²。感知延迟越严重需要越大的系统才从"怕低频"切换到"怕高频"。 描述 共振频率方向竞争函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D405`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D406｜宏观僵尸态g_eff函数](functions/items/D406.md)

**函数内容 / Function Content**
中文：M9的g_eff_macro = (1-R_irreversible)·g_eff。R→1时g_eff_macro→0但>0。与D311微观僵尸态完全同构——宏观僵尸态是微观僵尸态在n→∞极限下的连续版本。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的g_eff_macro = (1-R_irreversible)·g_eff。R→1时g_eff_macro→0但>0。与D311微观僵尸态完全同构——宏观僵尸态是微观僵尸态在n→∞极限下的连续版本。 描述 宏观僵尸态g_eff函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D406`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D407｜传染链自限函数](functions/items/D407.md)

**函数内容 / Function Content**
中文：M10的传染链有自限：僵尸化降低ḡ→降低溢出→传染减速。但自限点在全局僵尸化附近——来得太晚对干预没有实际帮助。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的传染链有自限：僵尸化降低ḡ→降低溢出→传染减速。但自限点在全局僵尸化附近——来得太晚对干预没有实际帮助。 描述 传染链自限函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D407`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D408｜Jensen-慢性消耗统一极限函数](functions/items/D408.md)

**函数内容 / Function Content**
中文：M11的连续极限下Jensen项∝(dΦ/dt)²·τ_min/2。τ_min→0时Jensen→0，τ_min有限时Jensen有限。慢性消耗=有限τ_min下的Jensen效应。D394"极限等价"需修正：不是严格等价而是τ_min有限时的近似等价。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的连续极限下Jensen项∝(dΦ/dt)²·τ_min/2。τ_min→0时Jensen→0，τ_min有限时Jensen有限。慢性消耗=有限τ_min下的Jensen效应。D394"极限等价"需修正：不是严格等价而是τ_min有限时的近似等价。 描述 -慢性消耗统一极限函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D394`, `D408`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D409｜传染临界-不可逆线一致性函数](functions/items/D409.md)

**函数内容 / Function Content**
中文：M12的大系统传染临界→n/2是容斥主导不可逆在传染维度的投影。D388和D395描述同一现象的不同方面——完全一致。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的大系统传染临界→n/2是容斥主导不可逆在传染维度的投影。D388和D395描述同一现象的不同方面——完全一致。 描述 传染临界-不可逆线一致性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D409`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D410｜不可逆线完整分类函数](functions/items/D410.md)

**函数内容 / Function Content**
中文：M13的四条不可逆线在(p_max,n,K,τ_delay)四维空间中划分3个有实际意义的区域：全可逆、部分可逆、全不可逆。全不可逆体积∝n²·p̄·Σαᵢ·K·τ_delay/β。干预策略：找到最小非零因子→最低成本干预。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的四条不可逆线在(p_max,n,K,τ_delay)四维空间中划分3个有实际意义的区域：全可逆、部分可逆、全不可逆。全不可逆体积∝n²·p̄·Σαᵢ·K·τ_delay/β。干预策略：找到最小非零因子→最低成本干预。 描述 不可逆线完整分类函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D410`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D411｜放大不确定性-两步策略自洽函数](functions/items/D411.md)

**函数内容 / Function Content**
中文：M14的正反馈放大不确定性→自动满足两步策略的高不确定性条件。K>1系统天然需要两步策略，K<1系统不需要。正反馈↔两步策略，负反馈↔一步策略——策略选择与系统动力学完全自洽。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的正反馈放大不确定性→自动满足两步策略的高不确定性条件。K>1系统天然需要两步策略，K<1系统不需要。正反馈↔两步策略，负反馈↔一步策略——策略选择与系统动力学完全自洽。 描述 放大不确定性-两步策略自洽函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D411`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D412｜双切换同步函数](functions/items/D412.md)

**函数内容 / Function Content**
中文：M1的R_tw=1与D316转折点近似同步但不精确同步。a_excl·τ≈0.25时两个切换同时发生（最危险的"完美风暴"），否则先后发生。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M1的R_tw=1与D316转折点近似同步但不精确同步。a_excl·τ≈0.25时两个切换同时发生（最危险的"完美风暴"），否则先后发生。 描述 双切换同步函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D412`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `0.25`: structural_constant / derived - Derived from the logistic gate derivative: σ'(x)=σ(x)(1-σ(x)); at the transition midpoint x=0, σ=0.5 and σ'=0.25.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D413｜遗迹-复活代价联合函数](functions/items/D413.md)

**函数内容 / Function Content**
中文：M2的遗迹衰减速率∝D301漂移速率。快速变化环境中旧秩序遗迹消失快——复活窗口短暂但代价也在降低。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M2的遗迹衰减速率∝D301漂移速率。快速变化环境中旧秩序遗迹消失快——复活窗口短暂但代价也在降低。 描述 遗迹-复活代价联合函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D413`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D414｜集中性-序参量映射修正函数](functions/items/D414.md)

**函数内容 / Function Content**
中文：M3的I=(1+m)/2在有限n时有O(1/n)修正。有限系统比平均场预测更集中。修正量∝1/√n——与D331 p*涨落同量级，同一有限尺寸效应的两个方面。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M3的I=(1+m)/2在有限n时有O(1/n)修正。有限系统比平均场预测更集中。修正量∝1/√n——与D331 p*涨落同量级，同一有限尺寸效应的两个方面。 描述 集中性-序参量映射修正函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D414`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D415｜有限温临界指数修正函数](functions/items/D415.md)

**函数内容 / Function Content**
中文：M4的β_eff = 1/2 - ε(T)，ε∝(kT/Φ_min)²。大系统临界行为更接近平均场——有限尺寸和有限温效应都∝1/√n。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M4的β_eff = 1/2 - ε(T)，ε∝(kT/Φ_min)²。大系统临界行为更接近平均场——有限尺寸和有限温效应都∝1/√n。 描述 有限温临界指数修正函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D415`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D416｜K=1-p_max=p*等价证明函数 | M5的K=1对应正反馈恰好自持](functions/items/D416.md)

**函数内容 / Function Content**
中文：—降低p_max的效应恰好被g_eff下降抵消。p_max=p*时良性循环无法启动→K=1的物理含义。**K=1与p_max=p*精确等价。**
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 —降低p_max的效应恰好被g_eff下降抵消。p_max=p*时良性循环无法启动→K=1的物理含义。**K=1与p_max=p*精确等价。** 描述 =1-p_max=p*等价证明函数 | M5的K=1对应正反馈恰好自持。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D416`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D417｜δ_c-稳定性裕度统一函数](functions/items/D417.md)

**函数内容 / Function Content**
中文：M6的吸引域深度×宽度²=常数。深度-宽度权衡：深而窄vs浅而宽。d=4是深且宽的双重最优——D285干预机会面积最大的几何根源。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M6的吸引域深度×宽度²=常数。深度-宽度权衡：深而窄vs浅而宽。d=4是深且宽的双重最优——D285干预机会面积最大的几何根源。 描述 δ_c-稳定性裕度统一函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D417`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D418｜强干预-去容斥等价函数](functions/items/D418.md)

**函数内容 / Function Content**
中文：M7的有效β = min(β_intended, β_max)，β_max∝√n/K。去容斥需β在(β_threshold, β_max)窗口内。K大的系统干预窗口极窄——强正反馈系统几乎无法安全干预。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M7的有效β = min(β_intended, β_max)，β_max∝√n/K。去容斥需β在(β_threshold, β_max)窗口内。K大的系统干预窗口极窄——强正反馈系统几乎无法安全干预。 描述 强干预-去容斥等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D418`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D419｜宏观僵尸态-实际不可逆等价函数](functions/items/D419.md)

**函数内容 / Function Content**
中文：M9的宏观僵尸态、实际不可逆、缓冲不可逆(D309)三者精确等价——同一现象的三个等价描述。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M9的宏观僵尸态、实际不可逆、缓冲不可逆(D309)三者精确等价——同一现象的三个等价描述。 描述 宏观僵尸态-实际不可逆等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D309`, `D419`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D420｜自限-实际不可逆时序函数](functions/items/D420.md)

**函数内容 / Function Content**
中文：M10的时序：传染→实际不可逆→全局僵尸化→自限。自限在系统已经死后才生效——对干预没有实际帮助。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M10的时序：传染→实际不可逆→全局僵尸化→自限。自限在系统已经死后才生效——对干预没有实际帮助。 描述 自限-实际不可逆时序函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D420`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D421｜τ_min-噪声相关时间等价函数](functions/items/D421.md)

**函数内容 / Function Content**
中文：M11的**τ_min=τ_delay**——最小响应时间等于反馈延迟时间。延迟决定系统能多快响应噪声。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M11的**τ_min=τ_delay**——最小响应时间等于反馈延迟时间。延迟决定系统能多快响应噪声。 描述 τ_min-噪声相关时间等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D421`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D422｜传染临界-不可逆观测量函数](functions/items/D422.md)

**函数内容 / Function Content**
中文：M12的n/2作为容斥主导不可逆的间接观测量——用可观测的传染临界预警不可观测的不可逆点。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M12的n/2作为容斥主导不可逆的间接观测量——用可观测的传染临界预警不可观测的不可逆点。 描述 传染临界-不可逆观测量函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D422`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D423｜不可逆体积参数归约函数](functions/items/D423.md)

**函数内容 / Function Content**
中文：M13的六个参数归约为3个有效参数：n_eff=n·√(p̄·Σαᵢ/β)，K，τ_delay。全不可逆体积∝n_eff²·K·τ_delay。三个干预方向：简化系统/降负担/增力度，减弱正反馈，加快反馈。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M13的六个参数归约为3个有效参数：n_eff=n·√(p̄·Σαᵢ/β)，K，τ_delay。全不可逆体积∝n_eff²·K·τ_delay。三个干预方向：简化系统/降负担/增力度，减弱正反馈，加快反馈。 描述 不可逆体积参数归约函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D423`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D424｜两步策略唯一性函数](functions/items/D424.md)

**函数内容 / Function Content**
中文：M14的**两步策略是学习效应存在时的唯一最优策略。** 利用P_correct随时间递增（学习效应）使探索阶段快速确认方向。无学习效应时所有策略等价。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 M14的**两步策略是学习效应存在时的唯一最优策略。** 利用P_correct随时间递增（学习效应）使探索阶段快速确认方向。无学习效应时所有策略等价。 描述 两步策略唯一性函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D424`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D463｜完美风暴-信息量等价函数](functions/items/D463.md)

**函数内容 / Function Content**
中文：D412修正后，完美风暴条件a_excl·τ=1/(4·ln2)中的ln2不是数学巧合——它建立了容斥动力学与信息论的精确桥梁。 $$a_{excl} \cdot \tau = \frac{1}{4 \ln 2} = \frac{1}{4} \cdot \frac{1}{\ln 2}$$ 与Landauer原理的等价：τ_Landauer = k_BT·ln2 / P是擦除1 bit信息的最小时间。完美风暴条件等价于：**系统的容斥-弛豫时间积恰好是Landauer擦除时间的1/4时，双切换同步**。 关键推论： - 完美风暴门槛比原预测低44%——实际不可逆到来时间是原预测的ln2倍 - t_irr' = t_irr × ln2 — 不可逆时间修正因子恰好是1 bit信息量的自然对数
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D412修正后，完美风暴条件a_excl·τ=1/(4·ln2)中的ln2不是数学巧合——它建立了容斥动力学与信息论的精确桥梁。 $$a_{excl} \cdot \tau = \frac{1}{4 \ln 2} = \frac{1}{4} \cdot \frac{1}{\ln 2}$$ 与Landauer原理的等价：τ_Landauer = k_BT·ln2 / P是擦除1 bit信息的最小时间。完美风暴条件等价于：**系统的容斥-弛豫时间积恰好是Landauer擦除时间的1/4时，双切换同步**。 关键推论： - 完美风暴门槛比原预测低44%——实际不可逆到来时间是原预测的ln2倍 - t_irr' = t_irr × ln2 — 不可逆时间修正因子恰好是1 bit信息量的自然对数 描述 完美风暴-信息量等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D463`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `ln2`: math_builtin / derived - ln2 is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- 暂无明确关联案例 / No explicit related cases yet.

### [D464｜幽灵超指数衰减函数](functions/items/D464.md)

**函数内容 / Function Content**
中文：D384精确化——极小点消失后的势能面残余不是简单指数衰减，而是超指数衰减： $$\Delta\Phi_{ghost}(t) = \Delta\Phi_{max} \cdot \exp\left(-\kappa \cdot \left[\int_0^t H_{eff}(t')dt'\right]^\alpha\right)$$ 其中H_eff是系统有效膨胀率，α由系统维度结构决定。 宇宙学特例：H_eff∝(1+z)^(3/2)，α=1，积分得ΔH(z) = ΔH_max · exp(-κ·[(1+z)^(5/2)-1])。这是P17哈勃张力的精确预测形式。 关键推论： - 幽灵效应的消失不是渐变而是突变——存在"幽灵消失时间"t_ghost_diss
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D384精确化——极小点消失后的势能面残余不是简单指数衰减，而是超指数衰减： $$\Delta\Phi_{ghost}(t) = \Delta\Phi_{max} \cdot \exp\left(-\kappa \cdot \left[\int_0^t H_{eff}(t')dt'\right]^\alpha\right)$$ 其中H_eff是系统有效膨胀率，α由系统维度结构决定。 宇宙学特例：H_eff∝(1+z)^(3/2)，α=1，积分得ΔH(z) = ΔH_max · exp(-κ·[(1+z)^(5/2)-1])。这是P17哈勃张力的精确预测形式。 关键推论： - 幽灵效应的消失不是渐变而是突变——存在"幽灵消失时间"t_ghost_diss 描述 幽灵超指数衰减函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D464`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [科举制度幽灵](cases/items/C-0567.md)

### [D465｜幽灵-不可逆竞争函数](functions/items/D465.md)

**函数内容 / Function Content**
中文：D464×D410交叉产生——幽灵消失时间t_ghost_diss与不可逆时间t_irr的竞争决定系统命运： $$P_{recover} = \sigma\left(\frac{t_{irr} - t_{ghost\_diss}}{\Delta t}\right)$$ - t_ghost_diss < t_irr：幽灵先消失，系统在不可逆前恢复自由度 → 可恢复 - t_ghost_diss > t_irr：幽灵拖住系统直到不可逆 → 不可恢复 - t_ghost_diss = t_irr：临界情形，对应D412完美风暴的D464版本 关键推论：
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D464×D410交叉产生——幽灵消失时间t_ghost_diss与不可逆时间t_irr的竞争决定系统命运： $$P_{recover} = \sigma\left(\frac{t_{irr} - t_{ghost\_diss}}{\Delta t}\right)$$ - t_ghost_diss < t_irr：幽灵先消失，系统在不可逆前恢复自由度 → 可恢复 - t_ghost_diss > t_irr：幽灵拖住系统直到不可逆 → 不可恢复 - t_ghost_diss = t_irr：临界情形，对应D412完美风暴的D464版本 关键推论： 描述 幽灵-不可逆竞争函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D464`, `D465`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [科举制度幽灵](cases/items/C-0567.md)
- [诺基亚缓慢退化](cases/items/C-0572.md)

### [D466｜暗物质核心-幽灵衰减函数](functions/items/D466.md)

**函数内容 / Function Content**
中文：D464×P16跨域碰撞——暗物质核心是可见物质分布的幽灵极小点。 暗物质核心半径r_c随时间超指数衰减： $$r_c(t) = r_{c,0} \cdot \exp\left(-\kappa_{DM} \cdot \left[\int_0^t H_{eff}(t')dt'\right]^\alpha\right)$$ 其中κ_DM极小（暗物质系统惯性极大），t以宇宙学时间计。 可检验预测：**更古老的星系团，暗物质核心半径更小**。r_c ∝ σ_visible² · exp(-κ_DM · t^α)。 与P16关系：P16说暗物质核心形态由σ_visible调控。D466补充时间维度——σ_visible不仅决定核心大小，还决定衰减速率。
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D464×P16跨域碰撞——暗物质核心是可见物质分布的幽灵极小点。 暗物质核心半径r_c随时间超指数衰减： $$r_c(t) = r_{c,0} \cdot \exp\left(-\kappa_{DM} \cdot \left[\int_0^t H_{eff}(t')dt'\right]^\alpha\right)$$ 其中κ_DM极小（暗物质系统惯性极大），t以宇宙学时间计。 可检验预测：**更古老的星系团，暗物质核心半径更小**。r_c ∝ σ_visible² · exp(-κ_DM · t^α)。 与P16关系：P16说暗物质核心形态由σ_visible调控。D466补充时间维度——σ_visible不仅决定核心大小，还决定衰减速率。 描述 暗物质核心-幽灵衰减函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D464`, `D466`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [暗物质核心时间演化](cases/items/C-0568.md)
- [子弹星系团暗物质](cases/items/C-0578.md)

### [D467｜最优性-惯性反比函数](functions/items/D467.md)

**函数内容 / Function Content**
中文：D464扩展(κ∝|σ-√e|/√e)×D307(σ_opt=√e)碰撞——空间维度的最优性与时间维度的惯性成反比。 $$\kappa \propto \left(\frac{\partial^2\Phi}{\partial\sigma^2}\bigg|_{\sigma^*}\right)^{-1}$$ 势阱在最优配置处最深最宽→残余最大→幽灵最持久→改革最难。这不是缺陷，是最优性的必然代价。 推广：任何参数空间中，系统在最优配置处的惯性最大。 - 经济学：最有效的市场最难改革 - 生物学：最适应的物种最难进化（进化保守性）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D464扩展(κ∝|σ-√e|/√e)×D307(σ_opt=√e)碰撞——空间维度的最优性与时间维度的惯性成反比。 $$\kappa \propto \left(\frac{\partial^2\Phi}{\partial\sigma^2}\bigg|_{\sigma^*}\right)^{-1}$$ 势阱在最优配置处最深最宽→残余最大→幽灵最持久→改革最难。这不是缺陷，是最优性的必然代价。 推广：任何参数空间中，系统在最优配置处的惯性最大。 - 经济学：最有效的市场最难改革 - 生物学：最适应的物种最难进化（进化保守性） 描述 最优性-惯性反比函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D307`, `D467`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `√e`: math_builtin / derived - √e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [进化保守性](cases/items/C-0569.md)
- [市场改革悖论](cases/items/C-0570.md)
- [诺基亚缓慢退化](cases/items/C-0572.md)
- [精细结构常数稳定性](cases/items/C-0573.md)

### [D468｜吸引子-陷阱等价函数](functions/items/D468.md)

**函数内容 / Function Content**
中文：D467×M8碰撞——势能面的极小点同时是吸引子（系统向其漂移）和陷阱（系统被其锁定）。吸引力和锁定力是同一势能曲率的两种表现： $$F_{attract} \propto -\frac{\partial V}{\partial\sigma}, \quad I_{trap} \propto \left(\frac{\partial^2 V}{\partial\sigma^2}\right)^{-1}$$ 在极小点处F_attract=0（已到达）但I_trap最大（最被锁定）。 关键推论： - 所有稳定状态都是陷阱——不存在"稳定但不锁定"的状态 - 逃逸陷阱的唯一方式是注入足够能量让系统翻越势垒（D295的p_max穿过p*）
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D467×M8碰撞——势能面的极小点同时是吸引子（系统向其漂移）和陷阱（系统被其锁定）。吸引力和锁定力是同一势能曲率的两种表现： $$F_{attract} \propto -\frac{\partial V}{\partial\sigma}, \quad I_{trap} \propto \left(\frac{\partial^2 V}{\partial\sigma^2}\right)^{-1}$$ 在极小点处F_attract=0（已到达）但I_trap最大（最被锁定）。 关键推论： - 所有稳定状态都是陷阱——不存在"稳定但不锁定"的状态 - 逃逸陷阱的唯一方式是注入足够能量让系统翻越势垒（D295的p_max穿过p*） 描述 吸引子-陷阱等价函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D467`, `D468`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [物种大灭绝](cases/items/C-0571.md)

### [D469｜振荡优化函数](functions/items/D469.md)

**函数内容 / Function Content**
中文：D468×M14碰撞——吸引子-陷阱等价导致系统在"优化→锁定→降势垒→重新优化"之间周期性循环： $$\sigma(t) \sim \sigma_{opt} + A \cdot \sin(\omega t) \cdot e^{-\gamma t}$$ ω由M14两步策略的执行速度决定，γ由每轮循环的净改善决定。 关键推论： - γ>0：收敛到σ_opt附近极限环——可持续演化 - γ=0：完美循环——永续振荡
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D468×M14碰撞——吸引子-陷阱等价导致系统在"优化→锁定→降势垒→重新优化"之间周期性循环： $$\sigma(t) \sim \sigma_{opt} + A \cdot \sin(\omega t) \cdot e^{-\gamma t}$$ ω由M14两步策略的执行速度决定，γ由每轮循环的净改善决定。 关键推论： - γ>0：收敛到σ_opt附近极限环——可持续演化 - γ=0：完美循环——永续振荡 描述 振荡优化函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D468`, `D469`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.
- 常数项 / Constants:
  - `e`: math_builtin / derived - e is a mathematical primitive used by the expression; it is not an empirical free parameter.

**关联案例 / Related Cases**
- [企业定期重组](cases/items/C-0574.md)
- [免疫系统更新](cases/items/C-0575.md)
- [科学范式革命](cases/items/C-0576.md)
- [子弹星系团暗物质](cases/items/C-0578.md)

### [D470｜幽灵跳变阻尼函数](functions/items/D470.md)

**函数内容 / Function Content**
中文：D469×D464深入碰撞——振荡优化的阻尼系数γ在优化周期T = t_ghost_diss处不连续跳变： $$\gamma = \begin{cases} \gamma_{dirty} & T < t_{ghost\_diss} \\ \gamma_{clean} & T > t_{ghost\_diss} \end{cases}$$ γ_dirty < γ_clean。跳变来自D464超指数衰减——幽灵在t_ghost_diss前几乎不衰减，之后突然消失。 关键推论： - 存在最优优化周期T* = t_ghost_diss——刚好等幽灵消失就启动下一轮 - T < t_ghost_diss：旧幽灵干扰→γ小→改善慢→浪费能量对抗幽灵
English: Rule-based English rendering pending human review.

**说明 / Explanation**
中文：该函数通过 D469×D464深入碰撞——振荡优化的阻尼系数γ在优化周期T = t_ghost_diss处不连续跳变： $$\gamma = \begin{cases} \gamma_{dirty} & T < t_{ghost\_diss} \\ \gamma_{clean} & T > t_{ghost\_diss} \end{cases}$$ γ_dirty < γ_clean。跳变来自D464超指数衰减——幽灵在t_ghost_diss前几乎不衰减，之后突然消失。 关键推论： - 存在最优优化周期T* = t_ghost_diss——刚好等幽灵消失就启动下一轮 - T < t_ghost_diss：旧幽灵干扰→γ小→改善慢→浪费能量对抗幽灵 描述 幽灵跳变阻尼函数。
English: Rule-based English rendering pending human review.

**推导补充 / Derivation Supplement**
- 推导类型 / Derivation type: `composed_or_bootstrapped_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D469`, `D470`
- 过程 / Process:
  - Extract referenced functions or meta-rules from the formula text.
  - Compose the current expression from those upstream objects and the source row's stated operator.

**关联案例 / Related Cases**
- [改革开放节奏](cases/items/C-0577.md)

</details>
