# 提示词模板

## 新人任务菜单

如果你刚进入点火，先让 AI 选一个任务：

1. 只读导航
2. 目录理解
3. 文件上传受限排查
4. 离线复核
5. 任务改写或总结

## 可读 GitHub 场景

```text
请先读以下 GitHub main 链接：
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-HANDOFF.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-PROMPT-TEMPLATES.md
然后只基于你确认过的内容继续，不要编造仓库里看不到的东西。
```

## 单文件读取受限场景

```text
我正在使用的 AI 只能稳定读取少量文件。请告诉我理解点火项目的最小上传清单，并说明每个文件的用途。不要猜测未上传文件的内容。
```

## 完全离线场景

```text
我现在只能给你本地上传文件，不能让你直接读 GitHub。请先说明需要上传哪几个最小文件，分成“必须”和“可选”，并在没有看到文件前不要推断仓库状态。
```

## 通用完整版

```text
你正在协助我进入 When Systems Catch Fire / 点火 项目。

先读这些文件：
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-HANDOFF.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md

然后按下面规则工作：
- 先确认你能直接读取哪些仓库文件。
- 不能读取的文件，请明确告诉我需要上传，不要编造。
- 先给出你确认到的边界和事实。
- 如果涉及正式函数表、正式案例表或 canonical，请先停下来说明风险。

项目主页：https://github.com/Arvin-liu/when-systems-catch-fire
```

## 超短版

```text
请先读 https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md、https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-HANDOFF.md 和 https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt，按 https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md 带我进入点火。不能直接读文件就请我上传，不要编造。
```

