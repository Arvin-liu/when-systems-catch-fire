# AI-HANDOFF

这是给跨会话、跨工具、跨模型交接用的最小页面。

## 你先判断链接状态

### main 可直接访问

- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-HANDOFF.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md
- https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-PROMPT-TEMPLATES.md

### PR preview 可访问但 main 尚未上线

- 用 PR 页面中的文件预览链接读取。
- 结论必须标记为 `PR preview only`，不能假装已经进入 main。
- 不能把 preview 里的文案当成 canonical。

### 只能单文件读取

- 先读 `README.md`。
- 再读 `AI-START-HERE.md`。
- 再读 `AI-HANDOFF.md`。
- 最后只按需补 `llms.txt` 和 `docs/AI-USAGE.md`。

### 完全离线

- 只使用上传文件。
- 如果缺文件，先请求最小上传清单。
- 不要猜测 main 状态。

## 交接清单

- 当前任务编号
- 当前分支
- 已确认的 main SHA
- 需要保持 PARTIAL 的结论
- 是否存在 PR preview only 的内容
- 是否还需要更新 `llms.txt`

## 最小上传清单

- `README.md`
- `AI-START-HERE.md`
- `AI-HANDOFF.md`
- `llms.txt`
- `docs/AI-USAGE.md`
- `docs/AI-PROMPT-TEMPLATES.md`

