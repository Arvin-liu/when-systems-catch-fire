# 使用说明

> 当前版本：2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076）。

## 1. 从哪里进入

先读 [README.md](../README.md)，再读 [ARCHITECTURE.md](../ARCHITECTURE.md) 与 [FOUNDATION.md](../FOUNDATION.md)。当前机器状态见 [project-state.json](../data/foundation/project-state.json)。

## 2. 按七层处理材料

1. L0：登记来源、版本、原始材料和冲突。
2. L1：写受控语义命题，声明主体、对象、条件、量词、范围和失败条件。
3. L2：分别选择 formal_object_type 与 claim_type；不能把所有材料都包装成 FUNCTION。
4. L3：写 Premises + Declared Rules -> Conclusion，并记录隐藏前提、反模型或 NOT_ASSESSED。
5. L4：建立数学模型、proof obligation 与 proof artifact；缺失内容保持 pending。
6. L5：分别验证 formal、logic、proof、evidence、scope 和 provenance。
7. L6：写解释、故事、文章或前端，并回链 L0-L5；不得制造新的数学真实性。

无法无损形式化时，使用 NATURAL_LANGUAGE_CANDIDATE 或 ARGUMENT_SCHEMA，并写明原因。

### L6 候选写作接口：肉身锚定的心智层级跃迁

121Q28 提供一个等待独立审查的候选接口：[方法正文](./publication/embodied-cognitive-leap-writing-method.md)与[后台故事规格](../templates/publication/embodied-cognitive-leap-story-spec.md)。它不是固定段落法。使用者应定位经验锚点，在写当前层时先识别下一层正在逼问什么；只有当前层存在不可容纳残余、新层能带来信息并在返回后改变旧层意义时，才以具体作品中的双重归属铰链突然跃迁。

横向增加领域不等于纵向升层。下一层若只换词、重复同级案例或制造宏大感，应停止。后台可以用 MCF／PSD／ARN 与 Q13 审查映射、动力学、关系和信息增益；前台正文不得用这些术语替代作品。任何写作感染力、模板完成或机器检查都不能提高 L0-L5 的事实、因果、同构、证明或价值状态。

## 3. 使用 12 元协议与 64 组合

12 元协议可作规范、启发与治理坐标；64 组合可作设计与生成空间。它们不是数学公理、证明空间或现实全枚举。

- [12 个元协议](./meta-protocols/12-meta-protocols.md)
- [64 组合矩阵](./meta-protocols/meta-protocol-64-combination-matrix.md)

## 4. 查阅权威与 legacy 兼容视图

先查 data/foundation 注册表和 project-state。统一函数总表、统一案例总表及 views 仅用于历史追溯和兼容展示，不代表内容已经证明或外部验证。

## 5. 提交候选

候选首先分成对象、命题、论证、来源与证据。book candidate 保留 BC 临时 ID，不分配 C ID。pending claim 保留 PEND ID；多种文件表示按同一 ID 合并，不重复计数。

## 6. 理解状态与旧断言等级

workflow、semantic、formal、logic、proof、evidence、scope、provenance、migration 九轴独立，任何一轴不推出另一轴。

docs/claim_levels.md 中的历史 L0-L5 是 legacy claim_level / assertion_grade，不是新 architecture_layer L0-L6。引用时必须写明字段，禁止裸用 L0-L5 造成混淆。

## 7. 避免误用

- 点火不是万能证明器；只有有可检查工件的具体命题才可获得相应 proof 状态。
- 单案例不能证明普遍定理。
- 数值采样、符号化简和有限模型都有后端范围。
- 缺字段、缺来源、不可形式化和真实反例是不同状态。
- 解释与出版内容必须回指下层证据和验证。
- 抽象升层不得删除肉身成本、具体受损主体、不可映射差异或 Charter Gate 边界。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
