# 注册表契约

稳定实体去重键为 asset_kind、normalized_namespace、normalized_id；文件表示键为 entity_key、path、git_blob_sha。所有引用使用 entity_key。对象与命题分离；命题与论证分离；案例只进入 evidence；proof artifact 与 validation record 不混用。

每个 legacy 正式对象必须至少有对象、命题、论证、来源、映射和证明义务记录。每个正式案例必须有 evidence 记录。迁移器 `--check` 证明生成结果与已提交快照一致。
