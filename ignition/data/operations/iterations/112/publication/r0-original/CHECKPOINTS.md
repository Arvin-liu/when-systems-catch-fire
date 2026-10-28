# 出版前置工程 R0 检查点

## CP-00：隔离与基线

- 时间：2026-08-02（Asia/Shanghai）
- 独立目录：`/Users/zhiyuan/WorkBuddy/Claw/ignition-publication-preproduction-r0`
- clone 类型：完整 Git clone；本地工作分支 `publication-preproduction-r0`
- 基线提交：`9b15d359c54694d851c38df6ab3c7ae42544a51b`
- 基线验证：`git rev-parse HEAD` 与指定 SHA 一致；工作树干净
- 远端写入保护：remote 名称改为 `source`，push URL 为 `DISABLED-LOCAL-ONLY`
- 禁止面核验：没有触碰任务 111 工作目录、`1111`、`relay/current` 或任何 task 112 控制文件
- 阶段结果：允许开始全仓普查

## 后续检查点格式

每个阶段提交前必须记录：

1. 阶段产物路径与数量；
2. 关键字数或条目数；
3. 所依据的基线提交与来源范围；
4. 已知缺口、冲突与 claim ceiling；
5. 本地普通提交 SHA；
6. 工作树与禁止面核验结果。

## CP-01：全仓成果普查

- 时间：2026-08-02（Asia/Shanghai）
- 固定基线：`9b15d359c54694d851c38df6ab3c7ae42544a51b`
- 产物：`01-百轮成果总台账.md`、`01-百轮成果总台账.jsonl`、`02-成果缺口与不可见性审计.md`、`03-研究问题谱系.md`、`04-纠正与撤回谱系.md`
- 结构化记录：JSONL 80 条，覆盖起源、v0.2、Foundation、MCF/PSD/ARN、Function OS、Crossref/OpenAlex、苹果案例、传播、出版、纠正、开放问题和知识资产
- 来源范围：Git 第一父级与基线祖先、`RESULTS`、`reports`、`data/foundation`、`evidence-program`、`function-os-candidate`、`docs/publication`、`data/operations/iterations/111`
- 关键发现：公开界面与机器闭合产物的函数/断言计数分别存在 5,663/7,051 与 17,333/17,626 两组快照；未擅自裁决权威口径
- 关键边界：任务 111 只按固定基线中的 bounded evidence 引用，不作正式完成声明；文件数、任务数和轮数不作为研究成果数量
- claim ceiling：阶段 1 的结论属于源恢复、分类、证据可见性审计和当前边界，不是新的外部科学结论
- 本地提交：将在本阶段验证后建立普通提交；不推送远端
- 禁止面核验：未创建 task 112 控制文件，未修改正式远端、`1111`、`relay/current` 或生命周期面

## CP-02：十章 evidence binder

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`evidence-binders/chapter-01.md` 至 `chapter-10.md`
- 文件数：10；总字符约 25,100
- 每章固定字段：章节核心问题、可支持的认识、不可支持的强说法、来源与提交、冲突版本、关键数字、反例、开放问题、claim ceiling、正文材料、附录工程信息
- 证据范围：固定基线中的动机、v0.2、Evidence Regime、Foundation、MCF/PSD/ARN、Function OS、Crossref/OpenAlex、任务 111 苹果、Q24/Q25/Q28/Q30/Q31/Q32/Q32I、出版作品与开放问题
- 关键边界：章节 binder 不新增外部事实；每章明确内部工程证据与现实领域证据的区别；任务 111 不被写成正式完成
- 本地提交：将在状态文件和结构检查后建立普通提交；不推送远端

## CP-03：第一卷初稿

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`volume/第一卷-初稿.md`、`volume/章节摘要.md`、`volume/来源与证据附录.md`、`volume/术语表.md`
- 初稿规模：39,624 总字符，30,126 个汉字，约 912 行；达到 30,000—60,000 中文字的预期范围
- 结构：序、十章、多个证据转折/中场、尾声；按问题—发现—纠正—未知组织，不按任务编号排列
- 已写入的边界：不把治理完整性写成科学正确；不把 metadata、bounded implementation、历史回忆和内部形式化升级为外部真理；保留失败、null、撤回和 target absent
- 来源/提交：来源证据附录按 S01–S33 分组，固定基线为 `9b15d359c54694d851c38df6ab3c7ae42544a51b`
- 未完成的审查：初稿尚未经过事实、反方和编辑三重独立审查；下一阶段研究笔记与全景同时作为后续校读材料
- 禁止面核验：本阶段只在独立目录写入；不创建 task 112 控制文件，不修改正式远端或 task111 控制面

## CP-04：研究笔记第一辑

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`notes/点火研究笔记-第一辑.md`、`notes/index.jsonl`
- 数量：60 条，六个问题主题；不是从第一卷机械切段，也不按任务编号排列
- 字段检查：每条包含一个明确问题、核心认识、证据/来源、边界和未决问题；正文长度 300—481 字
- 索引检查：JSONL 60 行、60 个唯一 note_id、每条可回到正文标题和来源路径
- claim ceiling：笔记是独立的主题入口和局部判断，不自动升级成新的外部实验或正式论文
- 已知边界：部分笔记同时引用内部工程、历史来源和出版资产，必须按每条 claim ceiling 阅读
- 禁止面核验：未创建 task 112 控制文件，未修改正式远端、`1111`、`relay/current` 或生命周期面

## CP-05：一页全景

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`点火目前真正知道什么.md`
- 结构检查：20 项当前能够支持的认识、20 项已纠正/撤回/降级的认识、20 项尚未解决的问题、10 项后续研究方向
- 边界检查：70 项均以“结论 + 边界”紧邻写出；不要求读者点击链接或 JSON 才能获得全局判断
- 关键冲突：并列写出 Foundation 公开/机器计数、Crossref/OpenAlex metadata-only、Function OS bounded scope 和苹果 target absent
- claim ceiling：全景是出版层压缩入口，不替代固定基线、原始来源、正式远端状态或外部领域裁决
- 本地提交：将在状态文件和内容检查后建立普通提交；不推送远端

## CP-06：三重独立审稿

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`reviews/事实审查.md`、`reviews/反方审查.md`、`reviews/编辑审查.md`、`reviews/逐项修订清单.md`
- 结构检查：事实、反方、编辑三种角色各提出 24 条具体意见；修订清单另列 35 条 P0/P1/P2 项目
- 关键事实风险：Foundation 两组计数、Function OS 版本链、Crossref/OpenAlex metadata-only、苹果 target absent、Q32/Q32I 局部边界、任务 111 生命周期边界
- 关键主张风险：不得把治理能力写成系统自知，不得把内部工程验证写成现实领域知识，不得把出版层综合写成仓库自动发现
- 编辑方向：减少任务号和内部数字在正文中的密度；提前解释普通读者所需概念；合并“撤回/未知/研究不是”重复段落；保留失败、null 和不确定性
- claim ceiling：审稿意见是对初稿的证据、反方和可读性审计，不是新的研究发现；第二稿必须逐项处理或标记有理由的延期
- 本地提交：本检查点与审稿文件一起建立普通本地提交；不推送远端
- 禁止面核验：未创建 task 112 控制文件，未修改正式远端、`1111`、`relay/current` 或生命周期面

## CP-07：第二稿与最终验收（提交前）

- 时间：2026-08-02（Asia/Shanghai）
- 产物：`volume/第一卷-第二稿.md`、`volume/修订说明.md`、更新后的 `volume/来源与证据附录.md`、已回填状态的 `reviews/逐项修订清单.md`
- 第二稿规模：38,994 总字符、30,568 个汉字、977 行；十章顺序重新组织，含开场、尾声、读者后记和证据阅读约定
- 实质重写检查：第二稿与初稿 SHA-256 不同；删除重复中场结构，增加非仓库生活锚点、nested equality 直觉例子、target/oracle/repeat 边界、五类未知地形、方向分组和读者复核路径
- 修订状态：R-001 至 R-035 均为 `DONE`；最终只读核验确认独立 clone、禁用 push URL、无 task 112 控制文件、无 `relay/current` 文件和无正式远端写入
- 关键事实边界：Foundation 两组数字并存；Function OS 保留原始失败与修复；Crossref/OpenAlex 保持 metadata-only；苹果案例保持 target absent；任务 111 只按固定基线有界证据引用
- claim ceiling：第二稿是既有证据的可读综合，不新增外部事实、正式任务状态或远端生命周期事件
- 本地提交：`68302f968f109afc4b15988b46d3c99cc8c9fa33`；普通本地提交，不推送远端
