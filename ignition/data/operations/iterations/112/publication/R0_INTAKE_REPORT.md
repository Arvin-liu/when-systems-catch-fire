# R0 intake 报告

## 状态

`INTAKE_VERIFIED_PENDING_SUBSTANTIVE_AUDIT`

这不是对 R0 质量的接受。它只确认 112 收到了一个可复现、可哈希、可独立审读的 R0 原始材料集。

## 已核验事实

- R0 独立工作目录：`/Users/zhiyuan/WorkBuddy/Claw/ignition-publication-preproduction-r0`
- R0 本地分支：`publication-preproduction-r0`
- 固定基线：`9b15d359c54694d851c38df6ab3c7ae42544a51b`
- 阶段七提交：`68302f968f109afc4b15988b46d3c99cc8c9fa33`
- R0 最终提交：`84fdcf68f2bd3fde8ed543b0ec6b51a538ea9597`
- 最终提交由阶段七提交继承，工作树在 intake 时干净。
- R0 读取远端为正式仓库，push URL 被设置为 `DISABLED-LOCAL-ONLY`；R0 的自报写入策略声明未修改正式远端、`1111`、`relay/current` 或任务 112 控制文件。
- 本 intake 只保存 R0 相对固定基线的 32 个跟踪文件，避免把正式仓库基线重复嵌入出版分支。
- 原始文件已复制到 `r0-original/`，并保留原始文件名、文本和二进制内容；没有在该子树内做编辑。

## R0 自报产量（尚未验收）

| 材料 | R0 自报 |
| --- | ---: |
| 成果台账 JSONL | 80 条 |
| 章节证据包 | 10 章 |
| 第一卷二稿 | 30,568 个汉字 |
| 研究笔记 | 60 条 |
| 全景 | 20/20/20/10，共 70 项 |
| 三重审稿意见 | 72 条 |
| 修订清单 | 35 项 |

这些数字只用于定义审计对象，不能证明研究增量、主张有效性、笔记独立性或出版质量。

## 原始材料和修订材料的分离

- 原始材料：`data/operations/iterations/112/publication/r0-original/`
- intake 锁与文件清单：本目录下的 `R0_SOURCE_LOCK.json`、`R0_FILE_MANIFEST.json`
- 112 独立审计：同一目录下以 `R0_` 开头但不在 `r0-original/` 内的审计文件
- 112 出版作品：`PUBLICATIONS/`

后续阶段不得覆盖 `r0-original/`。如发现 R0 的事实、主张或叙事问题，修订必须通过独立文件表达，并在 revision decision 与最终修订报告中留下对应关系。
