# 数学与逻辑地基

本页是 078 的人工入口；机器权威位于 `data/foundation/`。076 架构已被继承，但迁移覆盖与语义审定严格分开：622/622 迁移完成，621/622 registry 对象完成来源文本审定，D598 仍为 `PROVISIONAL`。

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
| `adjudications/` | 逐对象受控语义、正确类型、逻辑检查、处置与证明义务 |
| `coverage/` | 迁移覆盖率与语义审定覆盖率的独立口径 |
| `work-queues/` | 未深审对象的依赖/风险排序队列 |
| `function-assets/` | 十类函数身份、M/E 双轴、全量发现、纠偏覆盖、依赖边与可恢复审计队列 |

## 不可越权的门禁

- FUNCTION 必须声明定义域、陪域并满足单值性；否则使用关系、算子、谓词或自然语言候选。
- THEOREM 必须有声明理论、形式命题和可检查证明工件。
- ISOMORPHISM 必须有双射与结构保持证明；否则降为结构类比或部分映射。
- CAUSAL 必须有结构因果模型、干预语义与识别依据；否则是机制假说。
- PROVED 必须链接受支持后端或完整、待审的人类证明工件。
- 单案例、数值采样、符号化简与有限模型都不能单独证明普遍命题。

## 可复算入口

    python3 tools/foundation/adjudicate_core.py --check
    python3 tools/foundation/migrate_legacy.py --check
    python3 tools/foundation/validate_foundation.py
    python3 tools/foundation/verify_core_claims.py --check
    python3 tools/foundation/build_function_asset_census.py --check
    python3 tools/foundation/validate_claim_governance.py
    python3 -m unittest tests.foundation.test_foundation
    python3 -m unittest tests.foundation.test_claim_governance

Lean 4 固定为 v4.19.0，SymPy 固定为 1.14.0，Z3 固定为 4.16.0。T2 的 Nat 范围命题同时通过 Lean 与 Z3；T16 有可重放 SymPy 反例；D220 有可重放 Z3 反模型；T23 保持 `UNPROVED_PROPOSITION`。这些工件只证明各自受控命题，不证明整个点火框架。

## 深入阅读

- [数学地基](docs/foundation/mathematics/README.md)
- [逻辑地基](docs/foundation/logic/README.md)
- [状态系统](docs/foundation/status-system.md)
- [注册表契约](docs/foundation/registry-contract.md)
- [迁移与回滚](docs/foundation/migration.md)
- [断言治理与函数身份](docs/foundation/claim-governance-and-function-identity.md)
- [历史函数资产登记](docs/foundation/historical-function-census.md)
- [首批物理资产纠偏](docs/foundation/physics-asset-correction-20260729.md)
- [AI 使用入口](AI-START-HERE.md)
