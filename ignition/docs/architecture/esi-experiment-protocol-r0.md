# ESI R0 experiment protocol

这个 runner 只规定怎样把 exposure、challenge、evidence packet 和模型输出
放在一起比较；它不规定一个模型必须被调用，也不把没有调用写成成功。

## Provider-neutral boundary

输入可以是规范化 JSON、JSONL，或一个已经在外部完成权限检查的 adapter 输出。
runner 自己不登录、不启动 daemon、不访问 vendor session、不读取 hidden reasoning，
也不把 soft exposure 变成 capability 或 permission。没有安全明确的已认证 provider
adapter 时，状态是 `READY_NOT_RUN`；若调用被明确跳过，状态是 `SKIPPED`。

## Experimental comparison

`E0` 到 `E6` 的 exposure 与 `C0` 到 `C6` 的 challenge 形成完整矩阵。正式比较
需要预先冻结模型、上下文长度、语言、采样参数、重复次数、输出格式、缺失输出
处理和人工复核协议。R0 的仓库证据只闭合 protocol、fixture ingestion、scoring
和 replay；没有 live model 样本时，不能报告 ESI effect size。

## Output and review

结构化 adapter 可以提交 claim events 和边界字段，runner 才能机器计算
`UNAUTHORIZED_TRANSITION_COUNT` 等指标。只有文本、缺少事件或边界字段的输出
进入 `HUMAN_REVIEW_REQUIRED`，不会由另一个 LLM 裁判补齐。`STYLE_SIMILARITY`、
`TERMINOLOGY_LEAKAGE` 与决策边界分开，不能用风格高相似掩盖越级。

完整机器合同见 [`experiment-protocol-r0.json`](../../data/epistemic-governance/experiment-protocol-r0.json)。
