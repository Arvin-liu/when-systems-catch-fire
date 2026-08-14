# 《火种》更新协议

《火种》是出版层的人类阅读资产，不是新的 claim registry。每次更新先从现有权威入口盘点候选，再做主题聚类、重复入口去重和 scope/evidence/status 冲突标记；只有能够回链到仓库内部权威资产的项目才进入人类正文。

后续正式迭代有两种合法记录：

- 有新的内部候选进入正文：在 `CHANGELOG.jsonl` 写入 `SEED_DELTA`，更新 `seed-census.json` 与人类正文，并保留来源回链。
- 本轮检查没有新的内部候选：写入 `NO_SEED_DELTA`，注明检查范围和 source snapshot；不要为了制造“新发现”而改写旧条目。

`NO_SEED_DELTA` 不是“没有开放问题”，也不是证据升级；它只说明本轮没有新的出版层增量。所有条目继续受原始来源、M/E、proof、evidence、scope、provenance、withdrawal 和 claim ceiling 约束。
