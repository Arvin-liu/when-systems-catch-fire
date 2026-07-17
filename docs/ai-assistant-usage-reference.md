# AI 助手使用参考

这页给第一次接触点火项目的人使用。你不必先读完整仓库，可以先把下面的提示词复制给自己常用的 AI 助手，让它帮你做第一轮阅读。

可任选一款你日常使用的 AI 助手：

- [ChatGPT](https://chatgpt.com/)
- [Claude](https://claude.ai/)
- [Gemini](https://gemini.google.com/)
- [Microsoft Copilot](https://copilot.microsoft.com/)
- [Perplexity](https://www.perplexity.ai/)
- [Grok](https://grok.com/)
- [DeepSeek](https://chat.deepseek.com/)
- [Kimi](https://www.kimi.com/)
- [豆包](https://www.doubao.com/)
- [千问](https://www.qianwen.com/qianwen/)

这些助手不一定具备相同的浏览能力、地区可用性或回答质量。如果它无法打开 GitHub 链接，必须明确说无法读取，不应只凭项目名称猜测。你可以改用具备联网阅读能力的助手，或把仓库文件内容粘贴给它。

## 可直接复制的提示词

```text
请阅读并分析点火项目：
https://github.com/Arvin-liu/when-systems-catch-fire

我是第一次接触这个项目。请不要只根据项目名称、README 的宣传性句子
或作者愿景作结论，也不要把候选能力、测试通过或未来计划当成
已经被现实证明的结果。

请优先阅读以下文件：
README.md
docs/project-current-state.md
docs/governance/life-community-value-charter.md
ITERATION.md
ARCHITECTURE.md
docs/architecture/interactive-system-map.md
FOUNDATION.md
function-os-candidate/v0.2/README.md
docs/architecture/multiscale-causal-fabric.md
docs/architecture/probabilistic-system-dynamics.md
docs/architecture/adaptive-relational-network.md
docs/USAGE.md
AI-START-HERE.md
llms.txt

然后用普通人能理解的中文回答：

1. 当前版本的点火是一个什么样的项目？它明确不是什么？
   请把“当前现状”与“永久定位”区分开。
2. 它由哪些核心部分组成？项目现状、生命共同体价值宪章、Foundation、
   Ψ₀、Function OS、效果推理与机制判断、注意力与分布控制、
   地图集、MCF、PSD、ARN、点火迭代操作法和现实反馈分别负责什么？
   请解释 MCF、PSD 与 ARN 怎样分工、连接，以及 ARN 为什么把因果主张
   委托给 MCF。
3. 它对普通人的工作、学习、生活判断和长期项目有什么实际作用
   或方法启发？请给出至少 3 个具体场景，并区分哪些是仓库
   已实现能力，哪些只是可借鉴的方法。
4. 一个第一次使用点火的人，应从哪里开始？请给出一个不超过 7 步
   的最小使用流程。
5. Function OS 是什么？人类和 AI 应怎样使用它？它能产出什么？
   它当前的限制、风险、适用边界和不能证明的事情分别是什么？
6. 项目当前有哪些结论仍只能标记为 candidate、pending、
   需要外部验证或等待现实反馈？
   请明确区分“当前仓库能力”“候选派生表示”和“已证明的科学理论”。
   MCF、PSD 和 ARN 不是新的真值层，请不要把表示能力写成事实证明。
7. 点火怎样处理证据、反例、错误、失败、外部反馈和结论降级？
8. 点火的生命共同体价值宪章怎样约束“什么值得做”，
   而不冒充事实证据或数学证明？
9. 请把重要判断链接到仓库中的具体文件；遇到文件冲突时，
   以当前 main 的正式资产、测试、CI 和明确状态字段为准，
   不要自动选择更宏大的说法。
10. 最后请根据我的实际工作、学习或生活，向我提出最多 5 个
    真正必要的问题，然后给我一份个性化的首次使用建议。

如果你无法访问这个 GitHub 仓库，请直接说明无法读取，
不要编造项目内容。
```

[打开点火项目 GitHub 首页](https://github.com/Arvin-liu/when-systems-catch-fire)

这个链接打开的就是项目首页。你可以复制上面的提示词，再把这个链接交给自己常用的 AI。

当前状态与架构直达入口：[项目现状](./project-current-state.md) / [点火迭代操作法](../ITERATION.md) / [MCF](./architecture/multiscale-causal-fabric.md) / [PSD](./architecture/probabilistic-system-dynamics.md) / [ARN](./architecture/adaptive-relational-network.md)。本页是完整的人类 AI 使用指南；根 README 中的提示词是同一份受验证的前门投影，两者不得独立漂移。当前迭代方法把状态改变视为全项目同步传播：实现完成、仓库同步、逐外部表面证明和项目整体完成必须分开报告，局部通过不能替代整体闭环。

121Q32 的迭代方法 1.2.0 与系统图 0.2.0 只是 Draft candidate；Current 仍为 1.1.0 / 0.1.0。AI 试用 candidate 时必须从构件 registry、传播 topology 和同步 registry 重算 fixpoint，核对逐构件／逐表面决定、map delta、residue 和 closure hash。三个 relation domain 的权限不得混合：现实／理论 causal candidate 不自动驱动仓库变更，Git diff、文件依赖、遍历或可视连线也不能被写成因果证明。

L6 公共写作的当前接口是之元写作法 [`0.4.0`](./publication/zhiyuan-writing-method.md)及其[后台规格](../templates/publication/zhiyuan-writing-spec.md)所定义的双来源素材池；`0.3.0` 保留为历史版本。AI 必须区分 `external_input` 与 `ignition_increment`：后者可包括 claim、argument、mechanism、map、gap、residue、Q12—Q14、MCF／PSD／ARN 投影、分析报告和 provenance-gated 返回项，但必须保存 canonical 路径、版本、生成任务、claim ceiling 与原始来源回链。点火派生产物不能被算作新的独立证据。试读／发布反馈仍须登记主体、渠道、时间、原文范围和解释限制，才可返回适用流程。

若任务需要全项目导航，读取[完整可点击系统图说明](./architecture/interactive-system-map.md)及机器 spec。图中节点和连线是当前导航或受约束信息流，不是 L7、因果图、严格同构或理论完整性证明。

当前成果从[人类索引](./publication/zhiyuan-writing-showcase.md)与 `data/publication/zhiyuan-writing-showcase.json` 读取。AI 不得只抓取作品标题：必须同时核对案例来源链、点火分析、方法版本、review provenance 与 claim ceiling；registry 是展示与追踪接口，不是事实或文学质量注册表。

## 使用边界

- AI 的解释是一次有条件的阅读样本，不是点火项目的最终权威。
- AI 应引用仓库文件，不应只复述口号、标题或作者愿景。
- AI 无法浏览仓库时必须承认，不能编造项目内容。
- 你可以比较不同 AI 的回答，但多个 AI 给出一致答案，也不自动构成独立事实证据。
- 最终判断仍应回到 [项目现状](./project-current-state.md)、[生命共同体价值宪章](./governance/life-community-value-charter.md)、[现行架构](../ARCHITECTURE.md)、[Foundation](../FOUNDATION.md) 和相关限制说明。
- L6 写作的感染力、跨域收敛或多模型一致不能提高事实、因果、同构或价值主张；高层表达必须保留肉身成本和受损主体。
