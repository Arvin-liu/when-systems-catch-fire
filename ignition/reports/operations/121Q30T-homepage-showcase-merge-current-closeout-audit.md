# 121Q30T｜首页与之元写作法成果展示合并收口审计

PR #59 的 accepted HEAD `fb550c50dc5ebc385dcebb3b9aa8c768458c6d8c` 经 review `4715686225` 接受，并以 merge commit `0dfebc661668555a2636f9f59267fd7905368dca` 合入 main。合并前重新核验了 PR HEAD/base/mergeability、三条精确 HEAD CI、Q29R 正文 SHA-256 与受限来源边界；accepted HEAD 是 merge commit 和 post-merge main 的祖先。

本收口只改变 121Q30 的生命周期表述：README、ARCHITECTURE、项目现状、导航、使用、AI/Agent/机器入口、版本记录和机器 registry 将成果展示描述为当前 L6 presentation/provenance interface。`candidate` 作为结构对应、表示或历史认识地位的词继续保留，不被误删。首页仍按“项目现状 → 之元写作法成果 → 生命共同体价值宪章 → 使用指南”排列；详细现状与完整 AI 提示词默认折叠，README 最多投影 registry 最近三项。

五类职责继续分离：人类索引、机器 registry、正式作品、案例 provenance、点火分析。Q29R 正文仍绑定 `c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b`，不修改一个字节；原始 Get 笔记全文未公开；之元写作法保持 0.3.0；没有增加架构层、真值层或普遍有效性主张。

首次生产实况核验发现旧 Pages 流程只复制 README，导致首页成果链指向的仓库 Markdown 在站点返回 404。121Q30T 因而对 Pages source 做最小修复：只把首条成果链所需的成果索引、方法、作品、案例 provenance 和分析报告加入站点构建，不复制受限原始笔记。Q26 分析带有 Jekyll 元数据，构建会只生成 `.html`；构建产物因此额外保留同内容 `.md`，使 GitHub 与 Pages 共用的仓库相对链接都可访问。最终 main 的本地检查、Foundation、Function OS、Pages 生产部署和公开首页无缓存实况证据由 GitHub Actions 与 1111 结果回执承载。121Q30 候选记录保持原样，121Q30T 追加记录 Current/Closed 事实。
