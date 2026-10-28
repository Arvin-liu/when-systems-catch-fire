# Gate Semantics (022 frozen)

generated_at: 2026-07-10T21:45:00+08:00

门槛注册表见 `canonical/data/gate-registry.json`。

## 重点复核门槛
- G07 触发条件：semi_automatic → 需人工确认候选触发条件。
- G10 排除/失效：semi_automatic → 需人工确认。
- G13 冲突/优先级：semi_automatic → 需人工确认。
- G20 与函数表相似性：semi_automatic → 需对照函数表。
- G22 边界/反例：semi_automatic → 需边界案例或证据。
- G23 案例关系类型：manual → 必须人工标注 support/limit/falsify/boundary/illustrate/pending。
- G33 人工复核：governance（按 020 §5）→ 不阻断 content_machine_eligible，阻断 ratification_ready。

## 不得伪装
完全需要人工判断的门槛（G07/G10/G13/G20/G22/G23/G33）一律输出 PENDING / MANUAL_REVIEW_REQUIRED，不得标为自动 PASS。
