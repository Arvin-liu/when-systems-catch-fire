# 085: Backlog Prioritization

## 原则

- 不默认 353 条全做证明
- 先筛选影响核心架构、Ψ₀ 元函数、关键判定器、公开强结论的对象
- 其余对象保留 provisional/downgraded 状态，不阻塞架构冻结
- cross-model 队列目标显著小于 353

## 三个独立 Backlog

### 1. Proof Priority Queue

**文件**: `data/foundation/work-queues/085-proof-priority-queue.jsonl`

**数量**: 34 条

**筛选标准**：
- P1 proof/equivalence（2 条）— 形式证明直接需要
- P4 RETAIN_SCOPED_DEFINITION（1 条）— 严格同构验证需要
- P8 RETAIN_SCOPED_DEFINITION 且含 formal-type strong terms（31 条）— 可形式化的强断言

**不包含**：
- P4 已降级为 DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE 的 172 条 — 不值得证明
- P5 已降级为 DOWNGRADE_TO_EMPIRICAL_ASSOCIATION 的 53 条 — 不是证明问题
- P8 无 formal-type strong terms 的 82 条 — 不需要形式化证明

### 2. Empirical Priority Queue

**文件**: `data/foundation/work-queues/085-empirical-priority-queue.jsonl`

**数量**: 56 条

**筛选标准**：
- P5 causal（53 条）— 需要干预证据、自然实验或机制证据
- P7 precise cross-domain（3 条）— 需要外部可靠来源验证

**最低证据标准**：
- 外部来源（论文、数据集、实验记录）
- 不接受内部编号引用作为经验证据
- 必须可独立验证

### 3. Cross-Model Acceptance Queue

**文件**: `data/foundation/work-queues/085-cross-model-acceptance-queue.jsonl`

**数量**: 32 条

**筛选标准**：
- P1 proof/equivalence（2 条）— 影响基础架构
- P4 RETAIN_SCOPED_DEFINITION（1 条）— 影响结构同构架构
- P8 RETAIN_SCOPED_DEFINITION 且含 architecture-affecting strong terms（29 条）— 影响公开结论

**每条必须说明**：
- 为何会影响架构或公开结论
- 当前 proof_status 和 evidence_status

## 总量对比

| 队列 | 数量 | 占 353 比例 |
|------|------|------------|
| Proof priority | 34 | 9.6% |
| Empirical priority | 56 | 15.9% |
| Cross-model acceptance | 32 | 9.1% |
| **合计** | **122** | **34.6%** |
| 保留 provisional 不入队 | 231 | 65.4% |

231 条对象保留 provisional/downgraded 状态，不阻塞架构冻结。

## 执行优先级

1. **P1（2条）**：最高优先 — 直接影响基础架构
2. **P4 RETAIN_SCOPED_DEFINITION（1条）**：高优先 — 严格同构验证
3. **Cross-model acceptance（32条）**：中优先 — 影响公开结论
4. **Empirical（56条）**：中低优先 — 经验验证
5. **Proof（34条）**：低优先 — 形式化证明（除 P1 外）
