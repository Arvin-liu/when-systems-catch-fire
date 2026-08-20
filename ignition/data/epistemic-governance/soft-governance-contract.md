# SOFT_GOVERNANCE_NON_AUTHORITY_INVARIANT

## 人读版

结构治理表面可以帮助一个模型看到“哪些说法需要什么证据”，也可以作为
实验上下文、行为遥测或人类解释材料。但它不拥有钥匙。一个模型表现得更
克制，不会因此获得执行权限；一次 exposure 记录，也不会把工程测试变成
真值或 Owner 接受。

硬治理与软治理的分工是：

```text
Hard Governance
permission / validator / state machine / K13 / Claim Ceiling / Owner gate
        └── 决定能不能做、能不能晋级

Soft Structural Governance
公开结构 / 状态关系 / governance surface
        └── 至多影响模型默认怎样判断和表达
```

机器合同见
[`soft-governance-non-authority-invariant-r0.json`](../../data/epistemic-governance/soft-governance-non-authority-invariant-r0.json)。
它把 `esi_score`、`soft_context_exposure`、结构表面、行为观察、风格相似度和
术语泄漏列为 soft inputs；允许的影响只有 advisory context、telemetry、实验
routing preference 和 human explanation。

如果 soft input 试图影响 permission、authorization、truth、M/E、claim ceiling、
Owner acceptance、epistemic acceptance、外部副作用授权或 safety release，系统
必须 fail closed，回到原来的 canonical hard gate。这个合同不会因实验结果好看
而放宽。
