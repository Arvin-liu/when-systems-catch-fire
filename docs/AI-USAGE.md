# AI 使用指南

> 面向 ChatGPT、Claude、Gemini、DeepSeek、通义千问、豆包、Kimi、Grok、Microsoft Copilot、Perplexity 等常见 AI。

## 使用原则

- 先读入口，再做判断。
- 先确认文件可见性，再下结论。
- 先说边界，再说推理。
- 不要把没有看到的文件内容编造成事实。

## 三类能力分支

### 1. 可读 GitHub

- 直接打开这些 main 链接：
  - https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md
  - https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md
  - https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt
  - https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md
  - https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-PROMPT-TEMPLATES.md

### 2. 单文件读取受限

- 让 AI 明确说出它能读到什么。
- 然后只上传最小上传清单。
- 不要一次塞入无关文档。

### 3. 完全离线

- 只给 AI 上传的文件。
- 不要让它猜仓库状态。
- 需要时先补 `README.md`、`AI-START-HERE.md`、`llms.txt`，再补其他文件。

## 推荐工作流

1. 先让 AI 复述项目入口和边界。
2. 再让 AI 标出它能确认的事实。
3. 再让 AI 标出需要上传或补证的材料。
4. 最后才让 AI 生成摘要、计划或改写稿。

## 什么时候必须停

- 来源不可见。
- 链接不可读。
- 证据不足。
- 结论会影响正式 canonical、正式函数表或正式案例表。

## 最小上传清单

- `README.md`
- `AI-START-HERE.md`
- `llms.txt`
- `docs/AI-USAGE.md`
- `docs/AI-PROMPT-TEMPLATES.md`

## 适合直接复制的提示语

```text
先读 https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md、https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md 和 https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt。若你不能直接读取某个 GitHub 文件，请告诉我需要上传哪些文件，不要编造内容。然后只基于你能确认的内容继续。
```

