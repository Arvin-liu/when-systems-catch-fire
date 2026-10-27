# 104 双 088 归并与外部证据层定版报告

> 执行器：QClaw / qclaw/pool-glm-5.2 / max
> 生成时间：2026-07-13（上海时）
> 分支：`records/ignition-104-dual-088-reconciliation-external-evidence-layer-20260713`

## 0. 状态

`PARTIAL_EXTERNAL_EVIDENCE_LAYER_WITH_EXPLICIT_BLOCKERS`

部分完成：双 088 已发现并归并；外部证据状态阶梯已建立；117 条来源已重新评定；anysearch 已审计；14 补丁已重新评级；105+ 深挖队列已生成。Blocker：088-A 和 088-C 未执行（仅有任务文件），全文审阅未进行，Retraction Watch 未检查。

## 1. 双 088 全发现

### 执行实例清单

| 实例 | 任务文件 | 分支 | HEAD | 推送 | 产物 |
|------|---------|------|------|------|------|
| 088-A | `IGNITION-20260709-088-external-frontier-evidence-atlas-and-gap-applicability-audit.md` | 无 | 无 | 否 | 无（未执行） |
| 088-B | `IGNITION-20260709-088-external-literature-gap-source-atlas-and-campaign-router.md` | `records/ignition-088-external-literature-gap-source-atlas-20260713` | `f3ed0e81` | 是 | 28 个文件 |
| 088-C | `agent-instructions/IGNITION-20260713-088.md` | 无 | 无 | 否 | 无（未执行） |

### 088-B 提交链

```
f3ed0e81 IGNITION-088 FINAL REPORT
3b920735 medium gaps 009-014: 43 Crossref-verified sources
90b3c0a2 stage5-6 + anysearch retrieval client
371885d0 stage5-6: 089-103 all artifacts
e7d0d0da stage4-v2: 74 Crossref-verified sources
1858da41 stage0-4: 65 Crossref-verified sources
496f4257 IGNITION-087 FINAL (parent)
```

- 085 基线 `434e0983` 是 088-B 的祖先 ✅
- 088-B 父提交：`496f4257`（087 FINAL）

### 权威选择

088-B 是唯一有执行产物的 088 实例，作为权威基线。088-A 和 088-C 保留为未执行任务文件。

## 2. 双 088 差异

### 文件比较

- 088-A 预期 17 个文件，实际 0 个
- 088-C 预期 10 个文件，实际 0 个
- 088-B 产出 28 个文件（含 089-103 的 15 个产物）

### 冲突清单

| 冲突ID | 类型 | 严重度 | 描述 |
|--------|------|--------|------|
| C001 | DOI重复 | MINOR | GAP002-01 和 GAP002-08 共享同一 DOI |
| C002 | 来源类型不一致 | MINOR | 9 种不同的 source_type 值需标准化 |
| C003 | 同行评审状态不一致 | MINOR | 4 种不同大小写形式 |
| C004 | Atlas版本增殖 | INFO | v1/v2/v3/medium 4个版本 |
| C005 | 无Draft PR | MEDIUM | 088-B 分支已推送但未确认 Draft PR |
| C006 | 元数据vs内容混淆 | HIGH | "Crossref-verified" 被暗示为内容支持 |
| C007 | 088-A未执行 | HIGH | 任务文件存在但无产物 |
| C008 | 088-C未执行 | HIGH | 任务文件存在但无产物 |

## 3. 外部证据状态阶梯

### 状态分布（117 条来源）

| 状态 | 数量 |
|------|------|
| METADATA_VERIFIED | 117 |
| ABSTRACT_REVIEWED | 0 (待验证摘要来源) |
| FULLTEXT_REVIEWED | 0 |
| CLAIM_SUPPORT_CONFIRMED | 0 |
| CLAIM_SUPPORT_PARTIAL | 0 |
| CONTRADICTORY_EVIDENCE | 0 |
| RETRACTED_OR_CORRECTED | 0 |
| UNAVAILABLE_FOR_CONTENT_REVIEW | 0 |

### 关键纠正

088-FINAL-REPORT 使用 "INJECTED_VERIFIED" 暗示内容支持已验证。实际上所有验证仅为 Crossref 元数据匹配（DOI 存在 + 标题/年份匹配）。104 将此降级为 `METADATA_SUPPORTED_ONLY`。

## 4. 来源审计

- 唯一来源总数：117（去重后 116，因 1 个 DOI 重复）
- DOI 错误：0
- DOI 重复：1（GAP002-01/GAP002-08）
- 版本冲突：0
- 撤稿/更正警报：0（但未主动查询 Retraction Watch，标记为 NOT_CHECKED）

## 5. anysearch 审计

- 端点：`POST https://api.anysearch.com/v1/search`
- 免 key：是（CORS 开放）
- Smoke test：通过（2026-07-13 20:50 CST，返回 10 条真实结果）
- API key 模式：支持但不必要（key 通过环境变量配置，不写入 Git）
- 角色定位：仅线索发现（LEAD_DISCOVERED），不能作为权威
- API key 泄漏：0

## 6. 14 补丁证据就绪状态

| 补丁 | 类型 | 088状态 | 104状态 | 来源数 | 全文审阅 |
|------|------|---------|---------|--------|---------|
| GAP-001 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-002 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-003 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 12 | 否 |
| GAP-004 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-005 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-006 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 13 | 否 |
| GAP-007 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 9 | 否 |
| GAP-008 | NEW_OBJECT | INJECTED_VERIFIED | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-009 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 10 | 否 |
| GAP-010 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 12 | 否 |
| GAP-011 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 4 | 否 |
| GAP-012 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 5 | 否 |
| GAP-013 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 8 | 否 |
| GAP-014 | ENHANCE | ENHANCE_WITH_EXT | METADATA_SUPPORTED_ONLY | 4 | 否 |

8 个 HIGH 补丁均为 INTERFACE_CANDIDATE（不自动进入 Ψ₀）。6 个 MEDIUM 补丁均为内部增强字段。8 个 HIGH 补丁已进入宪法审查队列（constitutional review queue），因可能需要未来对 Ψ₀ 组件边界做正式非重叠证明。

## 7. 105+ 深挖队列

从 105 开始共 14 个任务：

| 任务号 | 缺口 | 优先级 | 最低来源 | 估计批次 |
|--------|------|--------|---------|---------|
| 105 | GAP-001 干预与控制 | HIGH | 12 | 3 |
| 106 | GAP-002 层级尺度 | HIGH | 10 | 3 |
| 107 | GAP-003 时间动态 | HIGH | 12 | 3 |
| 108 | GAP-004 随机不确定性 | HIGH | 10 | 2 |
| 109 | GAP-005 优化权衡 | HIGH | 10 | 2 |
| 110 | GAP-006 路径依赖 | HIGH | 10 | 2 |
| 111 | GAP-007 表示语言 | HIGH | 10 | 2 |
| 112 | GAP-008 计算复杂度 | HIGH | 10 | 2 |
| 113 | GAP-009 不完备性 | MEDIUM | 8 | 2 |
| 114 | GAP-010 测量可观测性 | MEDIUM | 8 | 2 |
| 115 | GAP-011 本体论 | MEDIUM | 8 | 3 |
| 116 | GAP-012 因果识别 | MEDIUM | 8 | 2 |
| 117 | GAP-013 证据制度 | MEDIUM | 8 | 2 |
| 118 | GAP-014 反例与失败 | MEDIUM | 8 | 3 |

不得自动执行 105 以后任务。

## 8. 红线验证

| 检查项 | 状态 |
|--------|------|
| 085 frozen v1 未修改 | ✅ PASS |
| Ψ₀ 定义未修改 | ✅ PASS |
| 统一函数总表未修改 | ✅ PASS |
| 统一案例总表未修改 | ✅ PASS |
| 旧 PR 未合并/关闭 | ✅ PASS |
| 新 PR 未合并（Draft only） | ✅ PASS |
| API key 未泄漏 | ✅ PASS |
| 088 原始记录未删除 | ✅ PASS |

## 9. Blocker

1. 088-A 和 088-C 无执行产物——若未来发现产物需触发 104-amendment
2. 全文审阅未进行——所有 117 条来源停在 METADATA_VERIFIED
3. Retraction Watch 未检查——所有来源 retraction_status = NOT_CHECKED
4. 摘要来源未验证——088-B 的 abstract 字段可能为模型生成而非出版商摘要
5. Content Retriever provider 未配置——无法自动获取全文
6. Draft PR 状态未确认——088-B 分支已推送但未确认是否已创建 PR

## 10. 待 GPT 查验
