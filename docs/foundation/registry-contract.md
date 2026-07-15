# 注册表契约

稳定实体去重键为 asset_kind、normalized_namespace、normalized_id；文件表示键为 entity_key、path、git_blob_sha。所有引用使用 entity_key。对象与命题分离；命题与论证分离；案例只进入 evidence；proof artifact 与 validation record 不混用。

每个 legacy 正式对象必须至少有对象、命题、论证、来源、映射和证明义务记录。每个正式案例必须有 evidence 记录。迁移器 `--check` 证明生成结果与已提交快照一致。

每个对象还必须有 `classification_status`、`classification_basis`、`classification_confidence`、`semantic_justification`、`source_excerpt_refs`、`adjudication_date`、`adjudicator`、`review_required`、`legacy_label` 与 `adjudicated_label`。仅由 ID/标题产生的记录必须是 `PROVISIONAL` + `TITLE_HEURISTIC`；只有独立 adjudication/override 记录可以升级为 `ADJUDICATED`。迁移器不得覆盖已审定记录。
