# Agent Runtime R1：真实行动层

本页记录任务 120 的当前工程边界。R0 的 generic kernel、typed loop、checkpoint/resume 和非知识 pilot 继续保留为历史与回归基线；R1 只增加一个受声明 workspace policy 约束的本地执行面。

## 运行边界

```text
Reasoner (typed frame/plan)
        |
        v
ExecutionPacket -- source plan hash --> Authorize + ApprovalStore
        |                                  |
        |                                  v
        +--> LeaseStore --> ActionJournal --> LocalWorkspaceExecutor
                                      |              |
                                      v              v
                                Validator       bounded preimages
                                      |              |
                                      +-------> Continue / Stop
```

`WorkspacePolicy` 是一次 run 的边界。路径只能是 workspace 内的 canonical relative path；symlink component、special file、parent traversal、越过读写根的路径和未 allowlist 的 executable 都 fail closed。命令使用 literal argv、`shell=False`、stdin 关闭、显式超时和 bounded stdout/stderr；R1 没有删除、远程 Git mutation、package install、sudo、network automation 或 system settings action。

## Durable action protocol

每个 action 先由完整 packet digest 和 source plan hash 固定，再产生 approval request（若 action class 需要），然后取得 execution lease。journal 在副作用前写入 `PREPARED`，在执行前写入 `EXECUTING`，只有获得 typed result 后才写入 `COMPLETED`。重启时：

- 已记录 postimage 且当前 workspace 匹配时，写入 `RECONCILED`，不重跑；
- 文件 preimage 仍匹配时，允许安全重试；
- 两者都不能证明，进入 `REQUIRES_RECONCILIATION`，不猜测；
- 通过 validator 后才推进 action index；验证失败的 rollbackable file action 只有在 whole-file preimage 验证相等时才进入 `FAILED_VALIDATION_ROLLED_BACK`，否则进入 `ROLLBACK_FAILED`。

Lease 与 approval store 使用持久锁和 atomic replace。相同 idempotency key 绑定不同 packet digest 会被拒绝；active action/lease 冲突不会通过重新启动绕过。

## Reasoner 与 CLI

`run-spec` 必须同时声明 profile、goal、workspace policy、capability scope、reasoner adapter、`local_workspace` executor adapter 和 validator；缺字段不会从聊天上下文补齐。Reasoner 只看到 bounded goal/environment/capability 摘要，不接收或持久化隐藏推理。`JsonlReasonerTransport` 是一请求一响应的 stdio 协议；它不选择 provider、不保存凭据，也不改变 executor 的权限边界。

```text
python3 -m agent_runtime run --spec RUN_SPEC.json --run-dir RUN_DIR --json
python3 -m agent_runtime pending-approval --run-dir RUN_DIR --json
python3 -m agent_runtime approve --run-dir RUN_DIR --request-id approval-ACTION --decision allow --authority human-id --json
python3 -m agent_runtime resume --run-dir RUN_DIR --json
```

## 证据与残余

`tests/test_agent_runtime_r1.py` 覆盖 path/symlink/special-file、executable/argv、timeout/output bound、packet expansion、stale approval、digest mismatch、lease/idempotency、四种 deterministic crash point、rollback failure、JSONL transport、CLI 和 real local pilots。Pilot A 的 terminal 是 `COMPLETED_VALIDATED`；Pilot B 的 terminal 是 `FAILED_VALIDATION_ROLLED_BACK`，这是受控负面验证，不是外部效果结论。

R1 不包含 multi-agent、vector/embedding memory、persona、scheduler/daemon、Telegram/OpenClaw/Hermes、网络浏览、真实 provider/model pilot、物理 Domain Pack migration、Git branch/commit/push 或现实 Owner acceptance。它把“安全地碰本地工作区”做成可审计边界，但仍不等于自治、真值、因果效果或 `EPISTEMICALLY_ACCEPTED`。
