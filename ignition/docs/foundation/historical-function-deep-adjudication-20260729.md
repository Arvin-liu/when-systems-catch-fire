# 历史函数资产深度裁决与注册表闭合 R1

本轮把任务 98 的候选 census 推进为第一轮全量、逐项、可重放的注册表闭合。闭合的严格含义是：每个发现项都有唯一 canonical card、一个主身份、M/E 双轴、来源行锚、证明与实证义务、依赖、十门结果、claim ceiling 和一种最终处置；缺少定义或证据的项进入显式 quarantine。闭合不等于所有资产已被证明、验证或外部复现。

当前精确计数和分布以 [`closure-summary.json`](../../data/foundation/function-assets/closure-summary.json) 为准。扫描器 v2 覆盖稳定编号、命名标题与字段、Python/Lean/JavaScript 函数声明和可检索的独立公式候选；公式图片没有可检索文本时仍不能恢复数学语义。

## 十二类主身份

任务 99 使用：严格数学函数、参数化数学模型、评分/指标函数、门/分类器、算子/变换、关系/约束、算法/工作流、启发式、结构隐喻、猜想/研究候选、无效/伪函数、身份未决。每项只能有一个主身份；同名不自动合并，精确同名只生成可审 alias candidate。

## 六层裁决

每张身份卡记录语法与映射、代数与分析、类型与量纲、逻辑、数值与计算、领域解释六层结果。适用资产使用 SymPy/Python 固定种子重放；T2、D182、D183、D260 另由 SageMath 独立实现复核。数学检查只支持卡片中的受限命题，不支持任何外部物理结论。

## 处置与 quarantine

`KEEP` 只保留其身份卡允许的用途。代码函数可以作为仓库范围算法保留，但测试通过不证明现实真实性。未声明定义域、值域、类型、量纲、表达或领域桥接的资产进入 `QUARANTINE_UNTIL_DEFINED`；开放命题进入 `DOWNGRADE_TO_CONJECTURE/PENDING`。quarantine 是明确的治理处置，不是验证通过。

## 机器入口

- `identity-cards.jsonl`：全量 canonical 身份卡；
- `adjudication-ledger.jsonl` / `asset-inventory.csv`：逐项处置索引；
- `proof-empirical-obligations.jsonl`：证明与实证义务；
- `counterexample-registry.jsonl`：反例；
- `dependency-closure.jsonl`：直接与传递依赖；
- `unresolved-quarantine.jsonl`：未决与隔离队列；
- `public-claim-lineage.jsonl` / `semantic-rebound-report.jsonl`：公共强断言和回弹候选；
- `withdrawn-historical-claims.jsonl`：撤回历史；
- `discovery-coverage.json` / `closure-summary.json`：覆盖与闭合证明。

## 复现

```bash
python3 tools/foundation/build_function_asset_census.py --check
python3 tools/foundation/adjudicate_function_assets.py --check
python3 tools/foundation/validate_function_asset_closure.py
python3 tools/foundation/run_function_asset_math_checks.py --check
python3 -m unittest tests.foundation.test_function_asset_closure
```

SageMath 在可用环境中运行：`sage formal/sage/function_asset_task99_checks.sage --check`。
