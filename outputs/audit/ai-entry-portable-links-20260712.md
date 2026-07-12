# 072 可复制 AI 入口审计

## 目标

把 071 的 AI 入口改成仓库外可直接复制的稳定 GitHub main 绝对链接，并补齐三类能力分支。

## 核验结果

- 可读 GitHub 场景：通过
- 单文件读取受限场景：通过
- 完全离线场景：通过
- 所有可复制提示词：未发现 `./` 相对路径残留

## 说明

- `README.md`、`AI-START-HERE.md`、`docs/AI-USAGE.md`、`docs/AI-PROMPT-TEMPLATES.md`、`llms.txt` 都使用了稳定的 GitHub main 绝对链接。
- 新人任务菜单、最小上传清单、不同用途模板已补齐。
- 070 结论仍保持 `PARTIAL`，未回写成全仓 100% 覆盖。

