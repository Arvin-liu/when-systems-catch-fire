# 函数资产作者指南

提交任何名为函数、模型、定理、公式、律或判定器的资产时：

1. 先选择十类权威身份，不以标题中的“函数”代替类型判断。
2. 写清输入、输出、定义域、陪域、变量类型、参数、单位、载体和运算。
3. 记录边界、奇点、连续性、可导性、单调性、可计算性和最小反例。
4. 分开模型内部解释与外部现实解释，并分别给出 M 与 E。
5. 为断言写 claim ceiling、允许用途、禁止用途和回滚条件。
6. 声称同构时提交对象、映射、逆和结构保持证明；否则标为 `STRUCTURAL_METAPHOR`。
7. 声称全称、必然、唯一、完全或不可能时提交相匹配的证明义务。
8. 列出依赖；底层资产降级后，同一变更必须更新或阻断全部上游强断言。
9. 测试结果只能写“实现符合规格”，不能写“现实命题因此为真”。
10. 历史错误必须留痕，用 `REWRITE / DOWNGRADE / SPLIT / RETIRE` 覆盖，不静默删除。

提交前执行：

```bash
python3 tools/foundation/build_function_asset_census.py
python3 tools/foundation/build_function_asset_census.py --check
python3 tools/foundation/validate_claim_governance.py
python3 -m unittest tests.foundation.test_claim_governance
```

自动扫描结果默认进入审计队列；作者自填标签也不自动成为权威审定。
