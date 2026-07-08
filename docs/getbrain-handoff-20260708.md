# 点火项目 · 交回得到大脑继续碰撞 · 交接说明（2026-07-08）

本文档用于把当前点火主仓库的最新状态交接给「得到大脑」，使其能够以最新仓库为唯一主源，继续做具体课题碰撞，而不必再关心底层工程收口过程。

## 一、当前状态

- `v0.2 structural infrastructure` 已完成（结构基础设施、ID 预检、P0 收口均已审计通过）。
- `P1 machine-readable data` 已完成：七类机器可读数据 + schema + 校验器齐备，`python3 tools/validate_data.py` 通过（`ALL_P1_DATA_VALID`）。
- tag `v0.2-p1-machine-readable-data` 已创建并推送到 origin（annotated，指向 `09804c6e`）。
- Codespace 两张表救援已闭环：差异审计 → 复核 → 补入 → 删除两个过期 Codespace，全部完成。
- `MF-0001~0005`（Section 0 自举元函数 5 个内部子算子）已补入正式函数表，并在 MF-0000 入口追加引用小节。
- 临时仓库 `LIANGZHANGBIAO` / `Unified-Case-Table` / `Unified-Function-Table` 仅作 Codespace 救援缓存，**不作为长期维护主线**。

## 二、主线资产（以点火主仓库内正式目录为准）

判断「两张表最新版」「机器可读数据最新版」时，一律以本仓库内正式目录为准，不再引用临时仓库。

| 资产 | 路径 | 说明 |
|---|---|---|
| 统一函数总表 | `统一函数总表/` | 当前正式函数表（拆分目录，每条一个 md；含 MF-0001~0005 内部子算子） |
| 统一案例总表 | `统一案例总表/` | 当前正式案例表（拆分目录） |
| 机器可读数据 | `data/` | P1 七类 csv+json：classic_problems_benchmark / evidence_regimes / failure_typology / function_dependency / pending_claims / publication_risk_rules / storytelling_backlog |
| 数据 schema | `data/schemas/` | 上述七类数据对应的 JSON schema |
| 校验器 | `tools/validate_data.py` | P1 数据校验入口，碰撞前必跑 |
| 审计记录 | `outputs/audit/` | 含 Codespace 救援三份审计 + v0.2/P1 既有审计 |
| 数据计划 | `docs/machine_readable_data_plan.md` | P1 机器可读化设计说明 |

> 注意：案例表经差异审计确认救援版为正式表旧子集（578/806 重叠，无增量），因此**以主仓库 `统一案例总表/` 为准**，不回灌救援版。函数表的救援独有增量（MF-0001~0005）已并入主仓库，无需再从临时仓库取。

## 三、得到大脑使用原则

1. **唯一主源**：使用最新点火主仓库 `when-systems-catch-fire` 作为唯一主源，不再从 `LIANGZHANGBIAO` / `Unified-*` 继续维护或读取主线。
2. **回填规则**：所有新增函数、案例、注释、扩展注释，必须回填到点火主仓库（新增文件进 `统一函数总表/`、`统一案例总表/`，结构化数据进 `data/` 并补 schema 校验）。
3. **碰撞前先校验**：每次碰撞前运行 `python3 tools/validate_data.py`，确认 P1 机器可读数据仍然有效。
4. **碰撞输入**：以「最新函数表 + 最新案例表 + P1 机器可读数据」为输入，不要混用旧临时仓库内容。
5. **输出区分**：碰撞输出必须明确区分五类：
   - 新增函数（new functions）
   - 新增案例（new cases）
   - 新增注释（new annotations）
   - 扩展注释（extended annotations）
   - 不采纳项（rejected / not adopted，附理由）
   其中收敛判定以「新函数 + 新案例 + 新扩展注释 + 新信息增量四项全零」为 ΔB=0 判据。

## 四、下一轮推荐任务（三选一）

### 候选 1：UNESCO 学科总表重跑碰撞
- 用最新点火元函数 + 全量函数表 + 全量案例表，重跑 UNESCO 学科总表（36 大类主干理论）。
- 产出：各学科与点火框架的函数化碰撞结论、可合并项、缺口清单。

### 候选 2：P1 机器数据接入碰撞工作流
- 把 `data/` 下七类机器可读数据真正接入碰撞工作流（读取 → 与函数/案例表碰撞 → 产出结构化增量）。
- 产出：标准化的「输入 P1 数据 → 输出新增函数/案例/注释」管线。

### 候选 3：得到笔记 / 新闻 / 具体问题增量抽取
- 从得到笔记、新闻、具体问题中继续抽取新增函数和案例，回填主仓库。
- 产出：持续增量，扩大两张表覆盖。

## 五、建议优先级

**建议优先做：候选 2 — P1 机器数据接入碰撞工作流。**

理由：
- P1 已经完成，数据、schema、校验器三者齐备，具备直接接入的条件；
- 先把机器数据接入流程打通，形成「输入 P1 数据 → 输出结构化增量」的标准管线，再大规模跑 UNESCO（候选 1）或得到笔记（候选 3）会更稳；
- 避免一上来又大规模跑内容，而是先把已结构化的资产真正用起来，性价比最高。

> 交接完成后，下一步默认执行「P1 机器数据接入碰撞工作流」；执行前应先 `git pull --ff-only` 并跑 `python3 tools/validate_data.py`。

## 六、收尾凭证（备查）

- 差异审计：`outputs/audit/codespace-rescue-two-tables-diff-audit-20260708.md`
- MF 复核：`outputs/audit/mf-0001-0005-rescue-review-20260708.md`
- MF 补入审计：`outputs/audit/mf-0001-0005-integration-audit-20260708.md`
- 关键 commit（main）：`dc6cff64`（functions: add bootstrap meta suboperators）、`d6d108c0`（docs: review rescued mf bootstrap suboperators）、`bb37b909`（docs: audit codespace rescue two tables）
- 临时仓库 rescue 分支（仅缓存，非主线）：`Arvin-liu/LIANGZHANGBIAO@codespace-rescue-liangzhangbiao-20260714`
