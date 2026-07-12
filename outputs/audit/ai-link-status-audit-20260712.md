# 074 链接状态审计

## 结论

- `README.md` 的人类入口保持 `main` 可访问。
- `AI-START-HERE.md`、`AI-HANDOFF.md`、`llms.txt`、`docs/AI-USAGE.md`、`docs/AI-PROMPT-TEMPLATES.md` 当前都属于 `PR preview only`。
- 默认可复制提示词已改为 preview branch 绝对链接，不再把 404 的 main URL 伪装成可用入口。

## 逐 URL 状态

- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/README.md` -> `main`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-START-HERE.md` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/AI-HANDOFF.md` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/llms.txt` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-USAGE.md` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/docs/AI-PROMPT-TEMPLATES.md` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-START-HERE.md` -> `pr_preview_only`
- `https://github.com/Arvin-liu/when-systems-catch-fire/blob/records/ignition-074-preview-link-truth-20260712/AI-HANDOFF.md` -> `pr_preview_only`

## 说明

- 073 相关口径回正为 PARTIAL。
- 070、072、073 保持真实 PARTIAL。
- 没有修改正式函数表、正式案例表或 canonical。

