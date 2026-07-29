# 持续自我纠错引擎

## 目的

本引擎把任务 98—100 的断言治理、函数注册表与证据谱系接到每次知识资产变化上。它自动建立“变化 → 关联断言 → 依赖影响 → 证据链 → 风险规则 → 整改计划 → 人类结果”，但不把自动检测当成数学证明、专家裁决或外部真理。

## 输入与输出

输入基线由 `data/governance/self-correction/config.json` 锁定。生成器读取当前工作树、任务 100 claim registry/dependency graph/evidence lineage，以及人类结果配对合同。

机器输出：

- `claim-delta.jsonl`：路径状态、前后摘要、关联断言和人类结果义务；
- `impact-analysis.jsonl`：直接和传递影响；
- `evidence-lineage-delta.jsonl`：受变更触发的证据谱系复核；
- `audit-findings.jsonl`：十类规则的 PASS/REVIEW/BLOCK；
- `remediation-plan.json`：所有 BLOCK 的失败关闭整改动作；
- `history.jsonl`：本轮追加式变更事件；
- `summary.json`：计数和 claim ceiling。

人类对应物：`RESULTS/CLAIM-DELTA.md`、`IMPACT-ANALYSIS.md`、`EVIDENCE-LINEAGE.md` 与 `SELF-CORRECTION-AUDIT.md`。

## 自动审计规则

1. 证明义务：强数学词是否缺对象、假设或证明边界；
2. 实证义务：经验/因果结论是否缺数据、基线或复现边界；
3. 跨域映射：是否把结构相似直接升级；
4. 量词膨胀：局部结果是否被写成所有、任何、必然、唯一；
5. 循环论证：结论是否被自身重述支持；
6. 类比冒充同构：是否缺对象、映射、双射/同态与结构保持；
7. 模型失败推出普遍不可能；
8. 撤回结论回弹，包括改名、改编号或换“结构性”包装；
9. 默认隐藏重要人类内容；
10. 退役阅读站重新进入当前表面。

启发式命中默认进入 REVIEW；已知结构阻断进入 BLOCK。纠正、撤回、否定和开放问题中的有边界提及保留为历史/治理引用，不被误判为回弹。

## 人类可见性门禁

`tools/governance/validate_human_visibility.py` 检查：

- 当前核心页面存在且没有 `<details>` 隐藏；
- 本地链接存在，重要结果在 README 两次点击内可达；
- 退役站点文件、workflow、URL 与当前 registry 身份不再出现；
- 每个声明的机器结果都有现存的人类对应物；
- 历史结果 census 与 ledger 一致；
- README 和项目现状含现行结论与任务 101 状态。

## 运行

```bash
python3 tools/governance/build_human_results.py
python3 tools/governance/run_self_correction.py
python3 tools/governance/build_human_results.py --check
python3 tools/governance/run_self_correction.py --check
python3 tools/governance/validate_human_visibility.py
python3 -m unittest tests.test_human_visibility_gate tests.test_self_correction_engine -v
```

CI 在 Foundation workflow 中按这个顺序运行。任何机器记录缺人类结果、生成漂移、断链、默认隐藏或 BLOCK 规则都会使合并失败。

## 历史与边界

Git 是历史权威；引擎不删除旧证据、不改写提交。撤回、降级、隔离和修订继续使用现行 supersession lineage，`history.jsonl` 只提供当前引擎的追加投影。图传播只表示仓库复核范围，不是现实因果。
