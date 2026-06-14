# 正反双通道自举元结构 / Forward-Reverse Bootstrap Meta-Structure

[MF-0000](../../docs/zh/functions/meta/MF-0000.md) 展开为正向判定、反向判定、互斥判定、嵌套迭代与不动点收敛五个抽象算子。
[MF-0000](../../docs/zh/functions/meta/MF-0000.md) expands into five abstract operators: forward judgment, reverse judgment, exclusivity judgment, nested iteration, and fixed-point convergence.

| 编号 / ID | 名称 / Title | 数学表达 / Expression | 作用 / Role | 状态 / Status |
| --- | --- | --- | --- | --- |
| [MF-0000](../../docs/zh/functions/meta/MF-0000.md) | 自举元函数 / Bootstrap Meta-Function | M_boot(B_n) = ε_sense(B_n) × P_track(B_n) × d(ΔK)/dt(B_n) | 根元算子 / Root meta-operator | active |
| [MF-0001](../../docs/zh/functions/meta/items/MF-0001.md) | 正向自举通道 / Forward Bootstrap Channel | J_n^+(x)=1 ⇔ Π_n^+(x\|B_n) ≥ θ_n^+ | 计算 J⁺ / Computes J+ | active |
| [MF-0002](../../docs/zh/functions/meta/items/MF-0002.md) | 反向自举通道 / Reverse Bootstrap Channel | J_n^-(x)=1 ⇔ Π_n^-(x\|B_n) ≥ θ_n^- | 计算 J⁻ / Computes J- | active |
| [MF-0003](../../docs/zh/functions/meta/items/MF-0003.md) | 正反互斥判定器 / Forward-Reverse Exclusivity Judge | ∀x∈X_n, ¬(J_n^+(x)=1 ∧ J_n^-(x)=1) | 排除 J⁺=J⁻=1 / Rejects J+=J-=1 | active |
| [MF-0004](../../docs/zh/functions/meta/items/MF-0004.md) | 自举嵌套判定器 / Nested Bootstrap Judge | M_boot^(k+1)(B_n)=M_boot(M_boot^k(B_n)) | 迭代 M_boot / Iterates M_boot | active |
| [MF-0005](../../docs/zh/functions/meta/items/MF-0005.md) | 自举收敛判定器 / Bootstrap Convergence Judge | Converged(B_n) ⇔ B_(n+1)=B_n ∧ ΔB_n=∅ ∧ ∀x∈X_n, (J_n^+(x),J_n^-(x))≠(1,1) | 判定不动点 / Tests fixed point | active |

## 规则 / Rule

- 设 B_n=(X_n,R_n,J_n^+,J_n^-,N_n)。
- 对任意 x∈X_n，同时计算 J_n^+(x) 与 J_n^-(x)。
- (J_n^+(x),J_n^-(x))=(1,0) 时接受 x。
- (J_n^+(x),J_n^-(x))=(0,1) 时接受 ¬x。
- (J_n^+(x),J_n^-(x))=(1,1) 时判定为 contradiction。
- (J_n^+(x),J_n^-(x))=(0,0) 时判定为 underdetermined。
- 当 B_(n+1)=B_n 且 ΔB_n=∅ 且不存在 (1,1) 时收敛。
