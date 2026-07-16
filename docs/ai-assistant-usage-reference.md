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
ARCHITECTURE.md
FOUNDATION.md
function-os-candidate/v0.2/README.md
docs/USAGE.md
AI-START-HERE.md
llms.txt

然后用普通人能理解的中文回答：

1. 当前版本的点火是一个什么样的项目？它明确不是什么？
   请把“当前现状”与“永久定位”区分开。
2. 它由哪些核心部分组成？项目现状、生命共同体价值宪章、Foundation、
   Ψ₀、Function OS、效果推理与机制判断、注意力与分布控制、
   地图集、现实反馈分别负责什么？
3. 它对普通人的工作、学习、生活判断和长期项目有什么实际作用
   或方法启发？请给出至少 3 个具体场景，并区分哪些是仓库
   已实现能力，哪些只是可借鉴的方法。
4. 一个第一次使用点火的人，应从哪里开始？请给出一个不超过 7 步
   的最小使用流程。
5. Function OS 是什么？人类和 AI 应怎样使用它？它能产出什么？
   它当前的限制、风险、适用边界和不能证明的事情分别是什么？
6. 项目当前有哪些结论仍只能标记为 candidate、pending、
   需要外部验证或等待现实反馈？
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

## 使用边界

- AI 的解释是一次有条件的阅读样本，不是点火项目的最终权威。
- AI 应引用仓库文件，不应只复述口号、标题或作者愿景。
- AI 无法浏览仓库时必须承认，不能编造项目内容。
- 你可以比较不同 AI 的回答，但多个 AI 给出一致答案，也不自动构成独立事实证据。
- 最终判断仍应回到 [项目现状](./project-current-state.md)、[生命共同体价值宪章](./governance/life-community-value-charter.md)、[现行架构](../ARCHITECTURE.md)、[Foundation](../FOUNDATION.md) 和相关限制说明。
