# 数学与逻辑地基

本页是 076 的人工入口；机器权威位于 `data/foundation/`。架构已完成，内容证明仍逐条开放。

## 权威注册表

| 注册表 | 责任 |
|---|---|
| `formal-objects/` | 稳定 ID、对象类型、类型/范围/证明义务 |
| `claims/` | 命题文本、命题类型与九轴状态 |
| `arguments/` | 前提、推理规则、结论与有效性 |
| `sources/` | 路径、提交对象与来源状态 |
| `evidence/` | 案例事实、解释、争议、关系和强度 |
| `mappings/` | legacy ID 到新实体的零遗漏映射 |
| `proofs/` | 证明义务与证明工件索引 |
| `validations/` | 可重放验证与反例契约 |
| `migrations/` | 迁移覆盖快照 |

## 不可越权的门禁

- FUNCTION 必须声明定义域、陪域并满足单值性；否则使用关系、算子、谓词或自然语言候选。
- THEOREM 必须有声明理论、形式命题和可检查证明工件。
- ISOMORPHISM 必须有双射与结构保持证明；否则降为结构类比或部分映射。
- CAUSAL 必须有结构因果模型、干预语义与识别依据；否则是机制假说。
- PROVED 必须链接受支持后端或完整、待审的人类证明工件。
- 单案例、数值采样、符号化简与有限模型都不能单独证明普遍命题。

## 可复算入口

    python3 tools/foundation/migrate_legacy.py --check
    python3 tools/foundation/validate_foundation.py
    python3 tools/foundation/run_benchmarks.py --check
    python3 -m unittest tests.foundation.test_foundation

Lean、SymPy、Z3 在本机均未发现，因此 Lean 仅提供项目骨架并保留真实 blocker；没有宣称 Lean proof passed。当前可执行基准包括代数正规化、具体有理数反例、保持 pending 的开放猜想、真值表有效演绎、反模型和可废止类比。

## 深入阅读

- [数学地基](docs/foundation/mathematics/README.md)
- [逻辑地基](docs/foundation/logic/README.md)
- [状态系统](docs/foundation/status-system.md)
- [注册表契约](docs/foundation/registry-contract.md)
- [迁移与回滚](docs/foundation/migration.md)
- [AI 使用入口](AI-START-HERE.md)
