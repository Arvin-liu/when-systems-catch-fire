# Foundation documentation

076 将“来源、命题、对象、论证、证明、验证、出版”拆开管理。先读根目录 `FOUNDATION.md`，再按数学、逻辑、注册表、状态、门禁和迁移文档工作。旧 L0-L5 声明等级如仍在历史文档出现，只是 legacy assertion grade，不等于本架构七层。

函数、模型、定理、公式、律或判定器还必须读取：

- [断言治理与函数身份](./claim-governance-and-function-identity.md)
- [历史函数资产登记](./historical-function-census.md)
- [函数资产作者指南](./function-asset-authoring-guide.md)
- [首批物理资产纠偏](./physics-asset-correction-20260729.md)
- [历史纠偏日志](./historical-correction-log.md)
- [后续深审路线图](./function-audit-roadmap.md)
- [历史函数资产深度裁决与注册表闭合](./historical-function-deep-adjudication-20260729.md)
- [公共断言上限指南](./public-claim-ceiling-guidance.md)
- [函数资产注册表迁移 R2](./function-asset-registry-migration-r2.md)
- [全语料非函数断言裁决索引](./nonfunction-claim-adjudication-index.md)
- [未来断言准入协议](./future-claim-admission-protocol.md)

旧表是不可变来源；`data/foundation/function-assets/corrections.jsonl` 是 task 98 首批纠偏权威覆盖。task 99 的 `identity-cards.jsonl` 为每个发现项提供现行处置；自动 census 仍只是候选，quarantine 也不因登记、编号或测试而获得真值。

task 100 的 `data/foundation/nonfunction-claims/claim-registry.jsonl` 覆盖非函数型断言，并保留函数身份卡作为依赖权威。其 closure 只表示发现项已有处置或显式 quarantine，不表示证明、外部证据、原创性、同行评审或复现完成。
