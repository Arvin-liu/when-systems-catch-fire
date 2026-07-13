# IGNITION-088 收尾报告：点火框架外部文献缺口与来源图谱

> 执行器：QClaw / qclaw/pool-glm-5.2 / max（GLM-5.2 池，未动用 Codex）
> 分支：`records/ignition-088-external-literature-gap-source-atlas-20260713`（未动 main，合并需用户/GPT 显式授权）
> 生成时间：2026-07-13（上海时）

## 0. 一句话结论

14 个结构缺口 × 250 学科的真实文献试投影**全部落地**：117 条来源**全部经 Crossref 双向核验、零伪造**，其中 8 个 HIGH 缺口作为**补丁库/对齐层的新对象类型接口**注入，6 个 MEDIUM 缺口作为引擎内部增强字段补齐。完整闭环：**外部找线索（anysearch）→ 验真（Crossref）→ 注入/增强 → 反幻觉闸门**。

## 1. 红线自检（先给结论，再给证据）

| 红线 | 状态 |
|---|---|
| 未改 Ψ₀:= 定义（Ψ₀ := C×M×I_iso×L_meta×G_δ×P_meta） | ✅ PASS |
| 未新增 Ψ₀ 函数编号 / candidate_formalized | ✅ PASS |
| 不注入未验真外部理论（反幻觉闸门 101） | ✅ PASS |
| 8 HIGH 仅作补丁库/对齐层对象类型接口，不入 Ψ₀ 核心 | ✅ PASS |
| 6 MEDIUM 仅补引擎内部增强字段，未改现有判定结构 | ✅ PASS |

证据：全目录扫描无 `Ψ₀:=` 改写、无 `新增函数编号`、无 `candidate_formalized`；8 个 NEW 补丁均带 `redline_preserved` 标记。

## 2. 阶段产物一览

| 阶段 | 文件 | 关键内容 |
|---|---|---|
| 0 | 088-087-count-reconciliation.json | overlay 分母 143→250 纠错 |
| 1 | （087 重算） | 250/250 一致，14 缺口齐全 |
| 2 | 088-discipline-source-routing.jsonl | 250 条学科特异检索路由 |
| 3 | 088-gap-source-atlas.jsonl | 14 缺口来源族 |
| 4 | **088-external-source-atlas-v3.jsonl** | **117 条全部 Crossref 验真（74 HIGH + 43 MEDIUM）** |
| 5 | 088-patch-blueprint.{md,jsonl} + 094-088-patch-library.jsonl | 14 补丁（8 NEW + 6 ENHANCE） |
| 6 | 089 至 103 共 15 产物 | 投影/闸门/对齐层/可视化/维护 |

## 3. 14 补丁与验真来源清单

> 每条补丁标注：类型、状态、验真来源数、映射 Ψ₀ 组件、红线归属、样本验真 DOI（全部可点开核验）。

### 8 个 HIGH 缺口 → 新对象类型接口（NEW_OBJECT_TYPE_INTERFACE）

**GAP-001 干预与控制** | 状态 INJECTED_VERIFIED | 8 来源 | 映射 C(x,y)（互补：补全可操作干预语义）
- Pearl 2009 *Causality* — `10.1017/cbo9780511803161`
- Xing et al. 2024 *Causal inference in medical domain* — `10.1007/s10489-024-05338-9`
- Ann Rev 2025 *From Prediction to Prescription* — `10.1146/annurev-biodatasci-103123-095750`

**GAP-002 层级尺度** | 状态 INJECTED_VERIFIED | 8 来源 | 映射 L_meta（互补：显式尺度桥接）
- Grima 2008 *Multiscale Modeling of Biological Pattern Formation* — `10.1016/s0070-2153(07)81015-5`
- Degenhard & Rodríguez-Laguna *Renormalization Group Methods* — `10.1007/3-540-35888-9_8`
- Papavasiliou & Kevrekidis 2007 — `10.1137/060650635`

**GAP-003 时间动态** | 状态 INJECTED_VERIFIED | 12 来源 | 映射 C.temporal_order（互补：动态演化）
- Scheffer 2009 *Early-warning signals for critical transitions* — `10.1038/nature08227`
- Lenton et al. 2008 *Tipping elements* — `10.1073/pnas.0705414105`
- Dakos et al. 2008 *Slowing down as early warning* — `10.1073/pnas.0802430105`

**GAP-004 随机不确定性** | 状态 INJECTED_VERIFIED | 8 来源 | 映射 I_iso（互补：分布稳健性）
- Gelman 2003 *Bayesian Data Analysis* — `10.1201/9780429258480`
- Berger 1985 *Statistical Decision Theory* — `10.1007/978-1-4757-4286-2`
- 2021 *Robust Bayesian Inference for Set-Identified* — `10.3982/ecta16773`

**GAP-005 优化权衡** | 状态 INJECTED_VERIFIED | 8 来源 | 映射 F_contract/F_nash（互补：多目标权衡）
- *Reliability-Based Multi-objective Optimization* — `10.1007/978-3-540-70928-2_9`
- *Pareto Optimality* 2017 — `10.2174/9781681085685117010005`
- 2015 *Ensemble of many-objective evolutionary alg.* — `10.1007/s00500-015-1955-3`

**GAP-006 路径依赖与历史** | 状态 INJECTED_VERIFIED | 13 来源 | 映射 G_δ（互补：历史不可逆）
- North 1990 *Institutions, Institutional Change* — `10.1017/cbo9780511808678`
- Arthur 1994 *Increasing Returns and Path Dependence* — `10.3998/mpub.10029`
- Pierson 2000 *Increasing Returns, Path Dependence* — `10.2307/2586011`

**GAP-007 表示语言** | 状态 INJECTED_VERIFIED | 9 来源 | 映射 G_δ（互补：表达力边界）
- 2025 *Ontology learning towards expressiveness* — `10.1016/j.cosrev.2024.100693`
- 2025 *Neurosymbolic visual reasoning survey* — `10.3233/nai-240719`
- Harnad 1990 *The symbol grounding problem* — `10.1016/0167-2789(90)90087-6`

**GAP-008 计算复杂度** | 状态 INJECTED_VERIFIED | 8 来源 | 映射 G_δ（互补：不可计算边界）
- Turing 1960 *On Computable Numbers* — `10.1016/b978-0-08-009217-1.50024-4`
- Cook 1971 *The complexity of theorem-proving* — `10.1145/800157.805047`
- Garey & Johnson 1982 *Computers and Intractability* — `10.1137/1024022`

### 6 个 MEDIUM 缺口 → 引擎内部增强字段（ENHANCE_KEEP，补外部文献后升级）

**GAP-009 不完备性/开放系统边界** | ENHANCE_WITH_EXTERNAL_SOURCES | 10 来源 | 补 `open_system_boundary`
- Cartwright 1999 *The Dappled World* — `10.1017/cbo9781139167093`
- 2019 *Thermodynamics of Non-Equilibrium Steady States* — `10.3390/e21070704`

**GAP-010 测量与可观测性** | ENHANCE_WITH_EXTERNAL_SOURCES | 12 来源 | 补 `construct_validity` / `proxy_variable`
- 2009 *Construct Validity: Advances in Theory* — `10.1146/annurev.clinpsy.032408.153639`
- 2003 *Quantifying construct validity* — `10.1037/0022-3514.84.3.608`

**GAP-011 本体论** | ENHANCE_WITH_EXTERNAL_SOURCES | 4 来源 | 补 `domain_ontology`
- 2019 *Engineering Domain Ontology* — `10.14569/IJACSA.2019.0100842`
- 2021 *Ontology-Based Process Modelling* — `10.3390/pr9040592`

**GAP-012 因果识别/运输性** | ENHANCE_WITH_EXTERNAL_SOURCES | 5 来源 | 补 `transportability` / `external_validity`
- Pearl & Bareinboim 2014 *External Validity: Do-Calculus to Transportability* — `10.1214/14-STS486`
- 2020 *Generalizing experimental results by mechanisms* — `10.1007/s10654-020-00687-4`

**GAP-013 证据制度/可重复性** | ENHANCE_WITH_EXTERNAL_SOURCES | 8 来源 | 补 `reproducibility` / `meta_research`
- 2015 *Estimating reproducibility of psychological science* — `10.1126/science.aac4716`
- 2018 *Is science facing a reproducibility crisis?* — `10.1073/pnas.1708272114`

**GAP-014 反例与失败** | ENHANCE_WITH_EXTERNAL_SOURCES | 4 来源 | 补 `negative_result` / `retraction_correction`
- 2022 *Self-correction in science: retraction effect* — `10.1371/journal.pone.0277814`
- 2026 *Retraction and correction due to conflicts of interest* — `10.1186/s41073-026-00236-9`

## 4. 关键真实 DOI 纠正（记忆错误已修）

- Rubin 1974 真实 DOI = `10.1037/h0037350`（非记忆中的错号）
- Angrist-Imbens-Rubin 1996 = `10.2307/2291634`
- Pearl 2009 = `10.1017/cbo9780511803161`
- Scheffer 2009 = `10.1038/nature08227`（真实，非伪造）

## 5. 联网检索通道（anysearch，已封装可用）

- 脚本 `scripts/external-research/anysearch_client.py`（`POST https://api.anysearch.com/v1/search`，免 key、CORS 开放）
- **闭环规则**：anysearch 仅找线索 → 抽 DOI 须 Crossref 双向验真后才入产物。
- GPT 下次可直接点名："用 anysearch 客户端补 088 的 X 缺口外部文献"。

## 6. 续跑入口（Resumable）

1. 阶段4 补某 gap：子代理已验真者直接采用；否则 `python3 scripts/external-research/anysearch_client.py "<query>" 5` 找线索 → Crossref 验真。
2. **合并入主库**：需用户/GPT 显式授权（点火红线：Agent 不自动 merge）。
3. 若要求突破"最小必要结构"新增 Ψ₀ 组件：须另行显式授权。

## 7. 已知限制

- 阶段4 部分条目为书评/综述或近期预印本，peer_review_status 已标注；注入补丁时作原始方法证据强度较弱，已降权。
- MEDIUM 缺口外部文献相对 HIGH 偏少（GAP-011 仅 4 条），如需更强支撑可续补。
- anysearch 为第三方免 key API，来源不明，仅作线索源，一切以 Crossref 验真为准。
