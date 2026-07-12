# When Systems Catch Fire / 点火

点火有两个入口：

- 人类理解入口：先看这是什么、为什么存在、从哪里读起。
- AI 协助入口：先复制提示词，让正在使用的 AI 带你进入点火。

## 人类理解入口

点火是一个跨域结构性推论与理论生成框架。它把现象整理成函数、案例与元协议，让人和 AI 可以在同一套结构里比较、收敛、反证，并在证据不足时保留 `pending`。

项目的价值锚点来自生命共同体伦理：任何局部系统的延续、效率、创新、稳定或扩张，都不得以对更大生命共同体造成不可逆、不可补偿、非自愿的重大伤害为代价。

### 从哪里开始读

- [人类导航页](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/SUMMARY.md)
- [使用说明](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/USAGE.md)
- [项目架构](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/PROJECT-ARCHITECTURE.md)
- [生命共同体价值宪章](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/governance/life-community-value-charter.md)
- [断言等级说明](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/claim_levels.md)
- [反证模板](https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/falsifiability/README.md)

### 这套仓库在做什么

点火的核心是把一个问题放进可复核的结构里：对象是什么，因果在哪里，系统如何反馈，哪些部分可以比较，分析应该停在哪一层，最后再判断结论是 `true`、`false`、`contradiction` 还是 `pending`。

正式资产放在两张表里，候选材料和理论展开放在专门的文档里。README 不重复细节，只负责把入口摆清楚。

## AI 协助入口

先复制一段提示词，让你正在使用的 AI 带你进入点火。

### 给 AI 的通用完整版提示词

```text
你正在协助我阅读并使用一个名为 “When Systems Catch Fire / 点火” 的项目。

先不要编造内容，先做三件事：
1. 识别我现在使用的 AI 是否能直接读取仓库文件。
2. 如果你不能直接读仓库文件，请明确告诉我需要上传哪些文件，而不是猜测文件内容。
3. 如果你能读到文件，请优先阅读这些入口：
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/README.md
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-START-HERE.md
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-HANDOFF.md
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/llms.txt
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/docs/AI-USAGE.md
   - https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/docs/AI-PROMPT-TEMPLATES.md

项目链接：
- 仓库首页：https://github.com/Arvin-liu/when-systems-catch-fire
- AI 起点（preview only）：https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-START-HERE.md
- AI 交接页（preview only）：https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-HANDOFF.md
- 机器可读入口（preview only）：https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/llms.txt
- 使用指南（preview only）：https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/docs/AI-USAGE.md
- 提示词模板（preview only）：https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/docs/AI-PROMPT-TEMPLATES.md

你需要遵守这些规则：
- 先读边界，再给结论。
- 不要把候选、推论或外部材料当成正式 canonical。
- 不要改动正式函数表和正式案例表，除非任务明确要求。
- 如果文件缺失、链接不可读、或你无法确认来源，请先请求我上传文件，再继续。
- 当证据不足时，明确标注 pending / partial / needs verification。

我要你带我进入点火的工作方式，不是替我臆造结论。
```

### 给 AI 的超短版提示词

```text
请先读 https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-START-HERE.md、https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-HANDOFF.md 和 https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/llms.txt，按 https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/docs/AI-USAGE.md 带我进入点火。不要编造仓库内容；若你不能直接读取文件，请告诉我需要上传哪些文件。仓库首页：https://github.com/Arvin-liu/when-systems-catch-fire
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

## 继续进入项目

如果你是第一次进来，先看人类入口；如果你是 AI，先看 AI 起点和交接页。两条前门都保留，但都要守住边界和证据。

