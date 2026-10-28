# 101 人类可读知识表面与持续自我纠错引擎

状态：`IMPLEMENTED_AWAITING_EXACT_HEAD_REVIEW_AND_ORDINARY_MERGE`

本报告记录任务 101 在正式仓库中的实现边界。PR、精确 head、CI、普通合并、Pages 仓库设置停用和全新克隆事实由 1111 最终回执在操作完成后绑定；本文件不预先声称这些外部生命周期步骤已经发生。

## 问题与基线

锁定基线为 `428ad50cf4438f027d5b8992d6e362d76037a3bd`。基线 README 底部有 4 个承载实质导航的 `<details>` 区块；独立 Pages 产品由 workflow、Jekyll 布局、样式、HTML、生成 SVG 与两组专用测试维护。仓库已有 165 份位于研究、文章、架构、Foundation 与迭代结果根目录的 Markdown 来源，但没有统一的人类结果台账。两张历史总表虽可访问，却不能代表任务 98—100 的当前身份、义务、双成熟度、依赖、处置和证据谱系。

机器审计见 [`data/governance/human-results/human-entry-audit.json`](../../data/governance/human-results/human-entry-audit.json)。

## 人类阅读层

根 README 直接显示当前结论、纠正、开放问题、研究与文章结果、函数和断言裁决、自纠链、系统图与项目入口，不再用折叠容器隐藏重要内容。`HUMAN-READING.md` 给出普通读者与技术读者路线；`RESULTS/` 提供最新结果、纠正、开放问题、裁决、研究文章、完整时间台账、Claim Delta、影响分析、证据谱系和审计结果。

结果恢复生成器逐份读取实际内容，而不是只按文件名推断。每个条目具有稳定 ID、日期、来源任务或运行、问题、方法/证据类别、来源摘要、成熟度/证据边界、变化、局限、来源和处置。自动摘要统一受 `HUMAN_INDEX_ONLY` 与 source-faithful claim ceiling 限制，不构成新裁决。

## Pages 退役

当前树删除 Pages workflow、Jekyll 配置/布局/样式、Pages HTML、Pages 路径的派生 SVG，以及两组 Pages 专用测试。系统图迁移到 `docs/generated/ignition-system-map.svg`，生成器和系统图文档改为仓库原生相对链接。Pages 相关历史清单继续由 Git 历史与时代 registry 验证，未改写或删除旧证据。

Pages 的仓库外启用状态不是本分支文件能够证明的事实；普通合并后须通过 GitHub API 停用并在 1111 回执记录前后状态。

## 自我纠错引擎

`tools/governance/run_self_correction.py` 以锁定基线发现知识资产增删改，关联现行断言注册表与依赖图，生成：

- Claim Delta；
- 依赖影响分析；
- Evidence Lineage Delta；
- 追加式历史；
- 机器整改计划与人类审计页。

当前规则覆盖证明义务、实证义务、跨域映射、量词膨胀、循环论证、类比冒充同构、单一模型失败推出普遍不可能、撤回结论改名回弹、机器结果缺人类对应物与人类结果缺机器证据。确定性规则可阻断；启发式规则只生成 `REVIEW`，不会自动作科学终局判决。

## CI 与历史兼容

Foundation workflow 运行人类结果生成器、自纠生成器、可见性验证器及其回归测试。可见性门禁检查机器—人类成对结果、结果索引、README 两步可达、断链、陈旧状态、退役 Pages 导航和隐藏的重要内容。

同步 registry 升至 `1.4.0`，以 `human.reading` 与 `human.results` 取代现行 Pages 表面。旧迭代清单继续按其声明的 era registry 解释；已从当前树退役的路径必须能在 Git 历史中证明存在，虚构路径仍会失败。这保留历史而不要求已经退役的基础设施永久留在当前树。

## 当前计算边界

迁移后重算的函数与非函数计数来自当前受治理语料，可能随本轮新增知识文档再次确定性变化。最终数字以同一 exact head 上重新生成并通过 `--check` 的 `closure-summary.json`、人类裁决总结和 1111 回执为准。

本轮只建立仓库自纠、可读性和证据边界能力；它不完成开放的数学证明、物理统一、同行评审或外部实证。
