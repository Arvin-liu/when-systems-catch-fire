# Agent Runtime R0 非知识 pilot

给定 sandbox 中的两个文本文件，运行时先读取并校验，再把按路径排序的 SHA-256 manifest 写入唯一允许的输出路径。

- 第一个 executor：`executor-alpha`，在 `CHECKPOINTED_RESUMABLE` checkpoint 停止。
- 第二个 executor：`executor-beta`，通过 resume capsule 继续并达到 `COMPLETED_VALIDATED`。
- 网络关闭；pilot 不读取任何知识系统路径；源文件前后 SHA-256 相同；实际写集等于声明写集。
- 该结果只证明一个确定性 control-plane 闭环，不证明模型智能、现实自主性或通用 AGI。
