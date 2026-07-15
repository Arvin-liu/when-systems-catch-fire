# 迁移与回滚

迁移读取 075 head 的 legacy 文件，按稳定 ID 去重并生成新注册表及兼容视图。它不修改旧表、不删除候选、不重编号。回滚只移除 `data/foundation/`、`schemas/foundation/`、`views/` 及关联生成报告；原始表和历史报告仍可审计。
