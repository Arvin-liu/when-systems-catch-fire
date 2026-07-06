# 反证模板

点火不是为了把所有问题都解释通，而是为了让解释可以被检验、被推翻、被修正。每个核心函数都应该能在真实或假设场景里接受测试，例如 `C(x,y)`、`M(B_n)`、`I_iso(A,B)`、`L_meta`、`G_δ`、`P_meta`。

当你用这个仓库分析新问题时，建议顺手新增一条测试记录。只要发现新的反例、冲突结论或不稳定映射，就值得写进来。

## 模板

```md
## Test Title
**Hypothesis / Function**: Ψ component being tested (e.g. C(x,y))
**Scenario**: Description of the real or hypothetical case.
**Prediction**: What the system predicts (true/false/contradiction/pending).
**Method**: How to evaluate it (data source, logical derivation, etc.).
**Outcome**: Did the prediction hold? If not, what failed?
**Notes**: Observations or interpretation.
```

## 使用建议

- 先写问题，再选函数。
- 优先用真实数据；没有数据时，也可以先写清楚可检验的假设场景。
- 如果结果不稳，直接标 `pending`。
- 只要出现反例，就把它记下来，而不是忽略掉。

