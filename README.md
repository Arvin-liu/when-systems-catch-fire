# When Systems Catch Fire / 点火

先复制一段提示词，让你正在使用的 AI 带你进入点火。

## 给 AI 的通用完整版提示词

```text
你正在协助我阅读并使用一个名为 “When Systems Catch Fire / 点火” 的项目。

先不要编造内容，先做三件事：
1. 识别我现在使用的 AI 是否能直接读取仓库文件。
2. 如果你不能直接读仓库文件，请明确告诉我需要上传哪些文件，而不是猜测文件内容。
3. 如果你能读到文件，请优先阅读这些入口：
   - README.md
   - AI-START-HERE.md
   - llms.txt
   - docs/AI-USAGE.md
   - docs/AI-PROMPT-TEMPLATES.md

项目链接：
- 仓库首页：./
- AI 起点：./AI-START-HERE.md
- 机器可读入口：./llms.txt
- 使用指南：./docs/AI-USAGE.md

你需要遵守这些规则：
- 先读边界，再给结论。
- 不要把候选、推论或外部材料当成正式 canonical。
- 不要改动正式函数表和正式案例表，除非任务明确要求。
- 如果文件缺失、链接不可读、或你无法确认来源，请先请求我上传文件，再继续。
- 当证据不足时，明确标注 pending / partial / needs verification。

我要你带我进入点火的工作方式，不是替我臆造结论。
```

## 给 AI 的超短版提示词

```text
请先读 `./AI-START-HERE.md` 和 `./llms.txt`，再按 `./docs/AI-USAGE.md` 带我进入点火。不要编造仓库内容；若你不能直接读取文件，请告诉我需要上传哪些文件。仓库首页：`./`
```

## 常见 AI

这个入口适用于：
- ChatGPT
- Claude
- Gemini
- DeepSeek
- 通义千问
- 豆包
- Kimi
- Grok
- Microsoft Copilot
- Perplexity

## 最先读什么

- [AI-START-HERE.md](./AI-START-HERE.md)
- [机器可读入口 llms.txt](./llms.txt)
- [AI 使用指南](./docs/AI-USAGE.md)
- [提示词模板](./docs/AI-PROMPT-TEMPLATES.md)
- [项目架构](./docs/PROJECT-ARCHITECTURE.md)
- [使用说明](./docs/USAGE.md)

## 继续进入项目

如果你是第一次进来，先从 AI 起点开始；如果你已经在项目里，按提示词把 AI 变成一个会先读边界、再做推理、最后给出可核验结果的协作者。

