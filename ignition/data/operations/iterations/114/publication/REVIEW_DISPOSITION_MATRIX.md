# 任务 114 四重审查处置矩阵

## 版本绑定

| 对象 | 历史接受 SHA-256／版本 | 冻结候选 SHA-256 | 审查后当前 SHA-256／版本 |
| --- | --- | --- | --- |
| 《当一支军队开始相信自己的背影》 | `c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b` | `2575c6c20922b434cde18514aed9fc3cd68a8df7514378354b2f8f46af7636f0` | `520a4b2043dacbd876b2831c257e62d126378a8e916c4beeb5365867f7f7025d` |
| 《当天意有了接口》 | `8d9fe3752e602041c8effb12f39bb2188c60a74843be4285d9181969e314a2e4` | `d397dcb1dff1da39d0340c110b4e655c32fe9b9ce58e99f6b4904ca602bcb7ac` | `d7f9df5cc8d4e1eaf4ffd906856e6e6c363d5bb8a32225f7737a62ce3147e0a5` |
| 之元写作法 | `0.4.0`（任务 113 历史版本） | `fd23ebd2cb7ad988e31a5e6c38612711fdb1bbda81718a5f74d1381c7985ebab` | `0.5.0` / `615b049dca357f4c00e3baeb38a3edd649a3bfadfa3a292928ab8d9ed8867e4d` |

历史 SHA 继续表示当时经过审查并接受的文本；当前 SHA 表示任务 114 之后公开书架所读到的修订。两者没有互相覆盖。

## 阻断项处置

| 审查 ID | 最终处置 | 证据 |
| --- | --- | --- |
| LT-114-01 | `FIXED`：日语 d09 从 `grammatically_required` 降为 `context_dependent`，增加场景、体裁与省略边界。 | `data/language-thought/profiles/ja.json` |
| LT-114-02 | `FIXED`：土耳其语 d04 降为 `strong_default`，明确不是每个命题都强制选择直接／间接证据。 | `data/language-thought/profiles/tr.json` |
| LT-114-03 / XL-114-03 | `FIXED_WITH_NEGATIVE_REGRESSION`：验证维度到 fixture 的真实引用；首次运行发现并关闭 `fx-crane-order-pass` 悬空引用。 | 验证器、26 个 fixtures、9 个单元测试 |
| XL-114-01 | `FIXED`：平面到之元写作法改为 `synchronization_requires`，不冒充治理权限。 | 传播拓扑与重新生成的地图 |
| XL-114-02 | `FIXED`：正式 CI 直接运行平面验证器与 Task 114 单元测试。 | `.github/workflows/foundation-validation.yml` |
| XL-114-04 | `FIXED_BY_GENERATOR`：地图由组件、拓扑和布局源重新生成；L0—L6 保持七层，不出现 L7。 | 当前地图 0.5.0、生成 JSON／SVG |
| ZH-114-01 | `FIXED_IN_SUBSTANTIVE_REWRITE`：先写谁退、谁站，再让战局判断进入。 | 军队篇当前 SHA |
| ZH-114-02 | `FIXED_IN_SUBSTANTIVE_REWRITE`：先写“找证据—作判断”的普通次序，再写行动生产下一轮证据。 | 军队篇当前 SHA |
| ZH-114-03 | `FIXED_IN_SUBSTANTIVE_REWRITE`：明示宫廷把解释送回皇权以及解释的用途。 | 徽宗篇当前 SHA |
| ZH-114-06 | `FIXED`：方法明确“事件先行”是诊断动作，不是固定开头、语序或短句模板。 | 之元写作法 0.5.0 当前 SHA |

## 保留项处置

| 审查 ID | 最终处置 | 边界 |
| --- | --- | --- |
| LT-114-04 | `RETAINED_LIMITATION` | 1.000 precision／recall 只适用于任务自编结构化样例。 |
| LT-114-05 | `RETAINED_LIMITATION` | `FULL` 是项目维度覆盖，不是语言本体完成；日语／土耳其语仍需语言特定出版审查。 |
| XL-114-05 | `RETAINED_LIMITATION` | 语言映射不提高来源、事实或因果权限。 |
| XL-114-06 | `RETAINED_GENERATED_AUTHORITY` | `HUMAN-READING` 与 `KNOWLEDGE` 只由正式生成器更新。 |
| ZH-114-04 / ZH-114-05 | `ALLOWED_MARKED_SYNTAX_RETAINED` | 1127 长句与军队篇结尾有可说明的思想收益，不作短句均质化。 |
| LC-114-01 至 LC-114-06 | `PASS_WITH_PRESERVATIONS` | 不建立单一自然度指标、作者克隆语料或第三方课程原文副本；两篇作品保持不同呼吸。 |

## 角色终结论

- 语言认知与类型学：`PASS_WITH_BOUNDED_CLAIMS`
- 跨层架构与认识边界：`PASS_NO_L7_NO_TRUTH_UPGRADE`
- 中文母语组织、语法与朗读：`PASS_AFTER_SUBSTANTIVE_REWRITE`
- 文学反均质化、标记句法与版权：`PASS_WITH_REQUIRED_PRESERVATIONS`

所有 required change 已有处置。语言相对论强度、日语／土耳其语具体结构分析和文学自然度仍保持开放，不被“修复”为虚假的最终答案。
