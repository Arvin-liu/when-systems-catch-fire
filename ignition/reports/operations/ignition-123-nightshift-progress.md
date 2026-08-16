# IGNITION-20260816-123 架构真相同步 R1 夜班进度

任务分支：`codex/ignition-123-current-state-sync-compact-map-federation-r2-20260816`  
正式基线：`d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`  
控制面：`1111 origin/relay/current = 7a1cfff8`

本报告是机器 ledger 的紧凑人读入口；逐步命令、哈希、schema 和回归输出以同目录
`nightshift-progress.jsonl`、本迭代 artifacts 与最终 machine receipt 为准。所有结果
都是仓库工程证据，不是外部真值、Owner acceptance、生产安全或
`EPISTEMICALLY_ACCEPTED`。

## Step 00 — COMPLETE

从 live `origin/main` 建立隔离工作树并完成只读基线审计。确认 Current State 旧数量、
首页重复 identity、map 版本/历史语义和 row-max 布局残余；建立 current-state drift
与 geometry baseline fixtures。未读 secret、未改外部配置、未做 live external invocation。

## Step 01 — COMPLETE

建立 `CURRENT_STATE_SYNC_INVARIANT`、current-system-identity、receipt/schema、validator、
CI gate 与正负 fixture。身份固定为 Ignition OS/orchestration-governance layer 与 driver，
外部 Agent 为可替换 executor，本地执行层为 `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR /
FALLBACK_MINIMAL`；当前仍 `CURRENT_WITH_OPEN_OBLIGATIONS`、`EPISTEMICALLY_ACCEPTED=0`。

## Step 02 — COMPLETE

生成唯一 `current-facts.json` 与窄范围 Markdown projection。当前 registry 为 82 components、
70 visible nodes、12 hidden components、77 visible edges、4 Packs；function/nonfunction
closure 为 `5,603 / 15,899`，Fire Seeds 为 `64 / 371`（后续派生回归会更新 source count）。
JSON/schema/generator 连续生成 byte-identical。

## Step 03 — COMPLETE

同步 `project-current-state.md`、首页和 AI/hand-off surfaces：旧数量只保留在历史语境，
Current 指向 canonical facts；OpenClaw、Hermes、Codex 仍是 replaceable executors，外部
完成不自动成为 OS validation。Human front door、visibility、state changelog 与 sync gate PASS。

## Step 04 — COMPLETE

将系统图从 row-max 改为 deterministic SCC-ranked column packing；唯一可点击总图的 map
version/layout projection 继续由 registry/topology 生成。canvas 从 `1800×3988` 收敛到
`1800×2978`，没有改变节点身份或 typed edges。

## Step 05 — COMPLETE

建立 `os_spine`、`federation`、`domain_packs` 三个语义投影和六段 bounded reading path；
地图升至 `0.8.0 Current`，外部执行器不被误读为 Kernel 或 OS 真相源。

## Step 06 — COMPLETE

加入 geometry quality gate 与旧 row-max/overlap negative fixtures。当前结果：height `2470`,
blank reduction `0.8741007194`, crossing proxy `160`, group occupancy `0.784957265`,
visible/clickable `70/70`，移动端 fit、无孤立 bottom module、无 overlap/clip/越界；全部
geometry/map/current-state tests PASS。

## Step 07 — COMPLETE

以同一 identity contract 收敛 Human/AI、Architecture、Federation、Results 与 map guide；
正式 `STATE-CHANGELOG` architecture delta 留到 Step 12。当前边界和 claim ceiling 未升级。

## Step 08 — COMPLETE

冻结 Reference/Conformance/Fallback 产品边界，禁止 browser、network、messaging、provider、
daemon、subagent、MCP ecosystem 和 remote Git 扩张；ownership validator、CI 与 5 个负向
fixture PASS。没有安装/升级或外部 auth/config mutation。

## Step 09 — COMPLETE

Fresh public probe：OpenClaw `2026.7.1-2`、Hermes `v0.20.0`、Codex `0.144.4` 均 healthy。
OpenClaw 因 unsafe/unbound surface 为 `SKIPPED`；Hermes/Codex 各一次 bounded read-only
尝试均 timeout，记录 `SKIPPED_UNSAFE_OR_UNAVAILABLE`。OS validator 对 disposable fixture
独立 PASS；不保留 prompt、token、credential、private session 或 provider telemetry。

## Step 10 — COMPLETE

Ignition driver 先路由 `external.hermes`，按 Step 09 结果 failover 到 `reference.executor`，
审批为 `APPROVED`，handoff 至 `reference.executor.recovery`。独立 validator 在两次观察中均
发现同样 2 个 fixture issues，只有 OS 生成的 `COMPLETED_VALIDATED` receipt 进入 convergence。
对抗性伪造 issue count 被判 `REJECTED_FAILED_VALIDATION`、`UNVERIFIED`、
`REQUIRES_RECONCILIATION`；未升级为 OS acceptance。详见
`cross-executor-driver-pilot-r1.json` 及其 tool/schema/test。

## Step 11 — COMPLETED_WITH_CLASSIFIED_RESIDUALS

最终派生快照已按 canonical generators 串行重建：function `5,604`、nonfunction `15,992`、
Human Results `333`、Knowledge `404 cards / 333 layers / 21,929 search / 853 aliases`、
Fire Seeds `64`（source census `393`）、Self-Correction `464 deltas / 10 rules`。Knowledge
Experience audit、two-pass determinism、Human Surface contract/front door、current-facts、
compact-map geometry、Federation ownership/routing、repository path classification、blast-radius
report、Foundation math/core、operational memory 和 phase-D 均 PASS。分层阅读页为 `423,962`
bytes，低于 500KB render budget。

本步修复并重新验证了两个 projection 层缺陷：Knowledge map 的截断 source preview 不再生成
假链接；分层阅读改为保留全部提取内容的紧凑记录。另同步修复了 blast-radius report 的
canonical source hash 和 repository path-classification manifest 的 tracked-path 覆盖。Human
materiality fingerprints 已由 canonical refresh 更新。Foundation 的 `sympy==1.14.0`、
`z3-solver==4.16.0.0`、`jsonschema==4.26.0` 只安装到一次性隔离 venv；没有安装/升级
OpenClaw、Hermes、Codex，没有改外部 auth/config，没有重复 Step 09 invocation。

隔离 venv 的完整命令为 `PYTHONPATH=. python3 -m unittest discover -s tests -v`，结果为
`Ran 750 tests`、`0 errors`、`1 skipped`、`4 failures`。其中 3 个 failure 是历史
reconciliation records 104–106 的旧 `NO_IMPACT_JUSTIFIED` 与当前派生路径不一致；第 4 个是
full-suite 顺序下 `current-facts` 的一次 stale 观察。后者在 isolated current-state module
（7 tests）及 refresh 后 validator 中 PASS，且回归结束后无 canonical source drift。两类现象
都被保留为机器 residual：`PROPAGATION-104-106`、`PHASE-E-CWD-WARNINGS` 和
`CURRENT-FACTS-ORDER-DRIFT`；没有放宽 current-state validator，也没有重写历史记录。

机器证据见 `data/operations/iterations/123/full-regression-r1.json`、其 schema、current-state
receipt 与本目录 JSONL ledger。正式 `main` 在 Step 12 前保持
`d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`。
