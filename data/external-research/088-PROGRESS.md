# 088 点火框架外部文献缺口与来源图谱 — 阶段进度（全阶段完成）

执行器：QClaw / qclaw/pool-glm-5.2 / max（GLM-5.2 池，非 Codex）
红线守住：未改 Ψ₀:= 定义、未新增函数编号；8 HIGH 缺口仅作为补丁库/对齐层“新对象类型接口”落地，6 MEDIUM 纯增强。

## 完成状态（阶段 0-6 全闭环）
| 阶段 | 产物 | 状态 |
|---|---|---|
| 0 计数审计 | 087 reconciliation | ✅ |
| 1 087 纠偏 | 250/250 一致 | ✅ |
| 2 250 学科路由 | 088-discipline-source-routing.jsonl | ✅ |
| 3 14 缺口图谱 | 088-gap-source-atlas.jsonl | ✅ |
| 4 真实文献试投影 | 088-external-source-atlas-v2.jsonl（74 条全部 Crossref 验真） | ✅ |
| 5 补丁候选蓝图→注入 | 088-patch-blueprint + 094-088-patch-library | ✅ 8 NEW 接口 + 6 ENHANCE |
| 6 089–103 编排 | 089 至 103 共 15 个产物 | ✅ 全生成 |

## 阶段4 来源（74 条，全部 crossref_verified=true，零伪造）
- GAP-001:8 / 002:8 / 003:12 / 004:8 / 005:8 / 006:13 / 007:9 / 008:8
- 角色：CURRENT_REVIEW 19 / FOUNDATIONAL 20 / METHOD 18 / FAILURE 7 / BENCHMARK 10

## 阶段5/6 关键产出文件
- 089 外部来源图谱（精炼阶段3）
- 090 学科特异来源映射 + 学科覆盖统计（19 学科覆盖，TIER_A 18 / TIER_B 1）
- 091 来源可信度等级
- 092 缺口→补丁投影（证据门槛全部达标）
- 093 引入拒绝协议（scope guard，反幻觉前置）
- 094 088 补丁库（8 NEW_OBJECT_TYPE_INTERFACE INJECTED_VERIFIED + 6 ENHANCE_KEEP）
- 095 补丁→Ψ₀ 映射
- 096 CLM 对齐层 v2（声明未改 Ψ₀）
- 097 250 学科证据分层
- 098 外部基准测试（fail-first 定义）
- 099 回填缺口映射（8 HIGH GROUNDED）
- 100 覆盖可视化 v2
- 101 反幻觉证据闸门（硬标准：cite≥1 验真源）
- 102 提示层与检索路由
- 103 固化与可维护（续跑入口 + 红线）

## 红线自检结论
- [PASS] 全目录扫描：无 Ψ₀:= 改写、无新增函数编号、无 candidate_formalized。
- [PASS] 8 个 NEW 补丁均带 redline_preserved 标记（仅对象类型接口，未入 Ψ₀ 核心）。
- [PASS] 6 个 MEDIUM 仅补引擎内部字段，未改现有判定结构。
- 分支：records/ignition-088-...-20260713；未动 main，合并需用户授权。

## 可用联网检索通道（anysearch，已实测可用）
- 脚本：scripts/external-research/anysearch_client.py
- 端点：POST https://api.anysearch.com/v1/search，body {"query","limit"}，免 key、CORS 开放
- 闭环规则：anysearch 仅找线索 → 抽取 DOI 须 Crossref 双向验真后才入产物（反幻觉）
- 用途：解决 web_fetch 受限；扩补 6 MEDIUM 缺口外部文献；任何「找线索→验真」文献任务
