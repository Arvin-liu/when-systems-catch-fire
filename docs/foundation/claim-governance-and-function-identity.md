# 断言治理与函数身份规范

本规范是 Foundation 的现行认识论边界。它管理项目如何命名、计算、测试、展示和撤回断言；它不把治理规则本身伪装成外部科学结论。

## 不可跨越的边界

- 形式化不等于证实；可计算不等于真实；内部自洽不等于外部成立。
- AI 生成的编号、名称、公式或通过的内部测试不赋予真值。
- 数学事实、模型定义、算法规则、结构隐喻和经验断言必须分层。
- 局部模型失败不能推广为全称不可能；必要条件不能冒充充分条件。
- 定义不能预埋待证明结论；内部指标不能未经表示映射直接解释为现实对象。
- 结构相似不是严格同构。同构声明必须给出对象、双射、逆映射与结构保持证明。
- 现实或跨学科强断言必须有 claim ceiling、证据边界、依赖传播和回滚条件。

## 十类函数身份

历史名称中的“函数”不具有分类权威。每条资产最终只能由审定记录赋予下列身份之一：

| 类型 | 判定边界 |
|---|---|
| `STRICT_MATHEMATICAL_FUNCTION` | 明确集合意义的定义域、陪域、单值性和求值规则 |
| `PARAMETRIC_MODEL` | 由明确参数索引的一族模型；拟合与现实解释另行审计 |
| `SCORE_OR_INDEX` | 用于排序或汇总的标量；阈值和校准不是公式自动给出的 |
| `GATE_OR_DECISION_RULE` | 谓词、阈值门或路由判定器 |
| `ALGORITHM_OR_WORKFLOW` | 有步骤、状态或终止条件的执行过程 |
| `RELATION_OR_CONSTRAINT` | 方程、约束或可多值关系，不强装成单值函数 |
| `HEURISTIC` | 可失败的经验规则，不具有演绎必然性 |
| `STRUCTURAL_METAPHOR` | 未给出结构保持映射的跨域类比 |
| `CONJECTURE_OR_PENDING_CLAIM` | 尚有开放证明义务的命题 |
| `INVALID_OR_PSEUDO_FUNCTION` | 未良定义、循环、类型冲突或已被反例击穿的伪函数 |

自动扫描只能写入 `AUTO_CANDIDATE`。只有受审记录可以写入 `HUMAN_ADJUDICATED_*`，候选不得覆盖人工权威。

## 数学成熟度 M0—M7

| 级别 | 含义 |
|---|---|
| M0 | 只有名称或自然语言 |
| M1 | 存在符号表达 |
| M2 | 定义域、值域和变量类型完整，数学上良定义 |
| M3 | 符号或形式验算通过 |
| M4 | 数值实现、边界和反例测试通过 |
| M5 | 跨实现或干净环境复算通过 |
| M6 | 证明义务或误差界完成 |
| M7 | 外部独立数学复核通过 |

## 外部证据 E0—E7

| 级别 | 含义 |
|---|---|
| E0 | 无现实映射 |
| E1 | 仅结构隐喻 |
| E2 | 变量与现实对象有操作性定义 |
| E3 | 已有数据可检验 |
| E4 | 内部数据拟合或回测 |
| E5 | 外部数据复现 |
| E6 | 领域同行审查 |
| E7 | 多方独立经验确认 |

M 与 E 正交。M6/E0 完全可能：一个已证明的抽象命题仍可能没有现实映射。

## 十个审计门

1. `definition_gate`：输入、输出、定义域、陪域和求值规则。
2. `dimension_and_type_gate`：单位、抽象类型、代数载体和运算一致。
3. `counterexample_gate`：最小反例或反例搜索状态明确。
4. `circular_reasoning_gate`：结论没有被偷偷写进定义或前提。
5. `claim_layer_gate`：数学、模型内部和现实断言分离。
6. `claim_ceiling_gate`：结论不超过证据允许层级。
7. `cross_domain_isomorphism_gate`：同构有对象、映射、逆与保持证明；否则降为类比。
8. `universal_quantifier_gate`：全称、必然、唯一、完全和不可能具有对应证明义务。
9. `internal_test_truth_gate`：测试只证明实现符合规格，不证明规格描述现实。
10. `dependency_impact_gate`：底层降级时，上游强断言必须同步修正或阻断。

机器无法可靠判断时，唯一允许的结果是 `REQUIRES_HUMAN_REVIEW`。不确定性不得伪装成 `PASS`。

## 处置与防回弹

最终处置为 `KEEP / REWRITE / DOWNGRADE / SPLIT / RETIRE`。强断言撤回后，不得只把“物理定理”改成“结构性定理”、把“证明”改成“框架判定”或用内部定义重新制造原结论。降级必须同时改变结论文本、适用范围、允许推理方向、依赖传播、公开展示和测试期望。

机器入口：`data/foundation/function-assets/`；验证入口：

```bash
python3 tools/foundation/build_function_asset_census.py --check
python3 tools/foundation/validate_claim_governance.py
python3 -m unittest tests.foundation.test_claim_governance
```
