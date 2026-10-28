# 《火种》更新协议

《火种》是出版层的人类阅读资产，不是新的 claim registry。每次更新先读取知识体验层的全部 source origins，再回到文章、案例、GetNote 主题、函数族、研究报告、写作片段、失败、撤回和开放问题的来源。机器清册记录扫描覆盖和来源处置，人类正文只保留可继续阅读的问题入口。

## 每轮必须做的事

1. 读取 data/governance/knowledge-experience/layered-reading.jsonl 的全部当前 source origins，并读取其 canonical_source，不把 308 这个当前快照数写成永久常数。
2. 补读成果册、editorial/articles、publication works/cases/method-sources、research/publication/architecture reports、KNOWLEDGE 人类页、结果页、函数/案例表和碰撞材料。
3. 对每个实质性来源写入四种处置之一：SEED_CREATED、MERGED_INTO_SEED、NO_SEED_DELTA、EXCLUDED_NONCONTENT。来源不因没有新入口而删除，历史、withdrawn、quarantine 和负结果仍然可回到原处。
4. 每个正文火种必须有稳定 ID、自然语言段落、为什么值得追、当前边界和 2 至 5 个相对来源链接。内容火种与关于点火自身的方法论火种分区，不能把 24 条方法条目重新换名当作内容增量。
5. 每个机器 seed 的 external_novelty_status 固定为 NOT_CHECKED。本页不得写原创发现、首次发现或外部学术原创性；内部推导、重组、问题化和写作增量仍然要保留其边界。
6. 显式登记冲突与互斥解释，例如退出权与退出后生活、支持与路径控制、表示与统一、修复与原始失败、收据与现实。冲突不是错误，也不是由清册自动裁决的真值。

## 确定性构建与校验

从 ignition 目录执行：

    python3 tools/publication/build_fire_seed_census.py
    python3 tools/publication/validate_fire_seeds.py --check

构建器从人类 canonical 页面解析 seed registry，从 knowledge-experience layered reading 和补充人类语料生成 source census、sha256、处置分布、冲突索引和 coverage summary。更新时连续运行两次并比较输出；若有差异，先修复排序、路径或生成逻辑。

有新的内部内容入口时，在 CHANGELOG.jsonl 追加 SEED_DELTA，并记录内容火种数、方法火种数、knowledge source origins 和 source snapshot；本轮没有新的出版层增量时追加 NO_SEED_DELTA。数量不是质量指标，也不是独立证据数量。

## 权威边界

人类 canonical 页面是 PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md。机器收据是 data/publication/fire-seeds/seed-census.json。两者都不能覆盖原始 registry、evidence、proof、M/E、scope、provenance、lifecycle、withdrawal 或 claim ceiling。仓库校验、提交、回执和 Owner/Review 状态都不等于外部真值或 EPISTEMICALLY_ACCEPTED。
