# IGNITION-20260827-143 Step 15 — 跨出版成果一致性审计

## 结论

Step 15 通过。三篇完整文章、Book Project R1 和两篇成熟样章已经形成一个可继续人工编辑的出版组合；它们共享必要的证据边界，但没有把同一段论证拆成多个标题。

本步确认的成果关系如下：

| 成果 | 独立读者问题 | 主要材料 | 与其他成果的边界 |
| --- | --- | --- | --- |
| Article 011 | 任务怎样在开放义务仍存在时诚实 terminal | Task142 生命周期与 obligation registry | 讲生命周期分离，不承担支持模型或树冠 replay |
| Article 012 | 资源支持什么时候开始收窄行动路径 | D600/M3 内部候选模型与五类反例 | 讲关系机制与研究问题，不冒充普遍因果定律 |
| Article 013 | 树冠、温度和因果为什么不能互换 | 七组公开来源与 bounded replay | 讲测量对象和因果范围，不恢复人体热应激结论 |
| 样章 01 | 为什么不能急着宣布完成 | 书稿开篇的房屋、天气与 Task142 场景 | 以书籍叙事打开问题，不复制 Article 011 的完整论证 |
| 样章 03 | 退出为什么不只是一个按钮 | 三扇门与正式/感知/事后退出 | 以书稿中段推进退出主题，不把 D600/M3 变成书稿主轴 |

Book Project R1 已链接两篇样章，且素材—章节映射、四层证据策略和与既有十二章成果册的重复审计都已写入[书籍项目](../../PUBLICATIONS/pointfire-results-book/14-书籍项目-R1-还没有被证明的世界.md)。本步没有新增平行成果系统，也没有把样章或文章提升为外部真值、生产就绪、Owner 接受或 `EPISTEMICALLY_ACCEPTED`。

## 机器与编辑检查

- 三篇文章的 `check_editorial_quality.py` 单文件检查均为 `PASS`：正文行数分别为 46、45、48；列表/表格比为 0、0、0.125；ID 主导段均为 0；均有来源与边界附录及来源链接。
- `validate_fire_seeds.py` 通过：64 entries、64 clusters、40 条内容火种、24 条方法火种、393 个来源。
- `validate_human_visibility.py` 通过：25 个 Human Surface、14 个 machine/human pairs、20 个 two-click destinations。
- 新增六份出版正文通过 `git diff --check` 与私有路径、凭据模式扫描；扫描无命中。
- 交叉审校确认没有重复轶事、重复 thesis 段落或私有 note body 泄露；共同出现的“来源—边界—claim ceiling”是出版所需的最小共同语汇。

## 保留的基线残余

`validate_human_surface_contract.py` 与 `validate_human_front_door.py` 仍报告 10 个既有 Human Surface source-hash drift。它们不属于本轮新出版正文，且从 Task142 基线 `b359580fe31866bc04eeb24911011e0baba9b66d` 到当前候选的逐路径 diff 为空，因此记录为 `PRE_EXISTING_BASELINE_DRIFT`，不在 Step 15 越权修复或改写 materiality manifest：

- `docs/human/function-assets/entries/d127.md`
- `docs/human/function-assets/entries/d182.md`
- `docs/human/function-assets/entries/d190.md`
- `docs/human/function-assets/entries/d260.md`
- `docs/human/function-assets/entries/t2.md`
- `docs/human/nonfunction-assets/entries/nfc-015cfd6ba387c9b1.md`
- `docs/human/nonfunction-assets/entries/nfc-01d7757c148ee0cc.md`
- `docs/human/nonfunction-assets/entries/nfc-0331afe8d84f2538.md`
- `docs/human/nonfunction-assets/entries/nfc-14866124cc1a2cae.md`
- `docs/human/nonfunction-assets/entries/nfc-154bdc1ff37c47f6.md`

该残余不改变本步出版组合的一致性结论，也不应在后续报告中被写成“全仓 Human Surface 门禁已绿”。Step 16 继续把本组合接回既有 canonical Results Book 入口；Step 18 将分别报告出版门禁与完整自然回归的真实结果。

## 证据

- [Publication Portfolio R1](../../data/operations/iterations/143/publication-portfolio-r1.json)
- [Article 011](../../docs/editorial/articles/011-terminal-task-open-obligation.md) · [Article 012](../../docs/editorial/articles/012-support-becomes-path-control.md) · [Article 013](../../docs/editorial/articles/013-tree-canopy-temperature-causality.md)
- [Book Project R1](../../PUBLICATIONS/pointfire-results-book/14-书籍项目-R1-还没有被证明的世界.md)
- [样章 01](../../PUBLICATIONS/pointfire-results-book/book-project-r1/01-第一章-先别急着宣布完成.md) · [样章 03](../../PUBLICATIONS/pointfire-results-book/book-project-r1/03-第三章-退出不是按钮.md)
- [Step 11 cross-publication editorial review](ignition-143-step11-cross-publication-editorial-review.md)

