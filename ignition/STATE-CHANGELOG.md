# STATE-CHANGELOG

点火的 AI 优先项目状态增量日志。它记录相对于上一份正式 `main` 状态真正发生的变化，供新 Agent 先恢复最近状态；它不是[仓库首页](../.github/README.md)、`docs/project-current-state.md`、Foundation registries 或 Results Book 的第二真相源。

## 读取与写入协议

- 冷启动先读[仓库首页](../.github/README.md)，再读本日志的 baseline 和最近几条 delta；随后回到[当前项目现状](./docs/project-current-state.md)、[迭代操作法](./ITERATION.md)和对象对应的权威 registry。
- 每次正式迭代合并 `main`，必须在同一轮追加一条 delta；旧条目 append-only，不改写成“现在看来”的新状态。
- 每条 delta 至少保留：日期/任务、对应的 main 状态与基线 tip、真实 delta、权威资产变化、claim/evidence/proof/scope/provenance 变化、open obligations、失效认知和下一步阅读入口。
- 本日志只记录仓库状态与可审计变化；工程完成、叙事完成、CI 通过或 Agent 共识不能由此升级外部真值。

## 2026-08-15 — BASELINE-CURRENT — main@19658de18d1c22fff2265f94bcd8a08cdddc0609

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; baseline 是远端 `main` 在 `19658de18d1c22fff2265f94bcd8a08cdddc0609` 的状态。
- delta: 建立当前主线恢复基线；不重新解释历史，只把当前权威入口和已知残余钉回链接。
- authority_changes: [迭代操作法 1.4.0](./ITERATION.md)、[系统图 0.5.0](./data/architecture/interactive-system-map.json)、[Charter System R1](./docs/governance/charter-system-r1.md)、[REOS vNext LIGHT](./docs/architecture/reos-vnext-light.md)、[Evidence Program](./evidence-program/README.md)、[任务 112 成果出版层](./PUBLICATIONS/pointfire-results-book/README.md)、[之元写作法 0.5.0](./docs/publication/zhiyuan-writing-method.md)均以各自权威资产为准；[九状态轴](./ARCHITECTURE.md#七层关系)保持独立。
- epistemic_state: 当前总上限仍为 `CURRENT_WITH_OPEN_OBLIGATIONS`；M/E、claim ceiling、proof、evidence、scope、provenance 和 lifecycle 不互相代替。撤回、quarantine、pending 与开放问题继续保留。
- obligations: [开放问题](./RESULTS/OPEN-QUESTIONS.md)、[纠正与撤回](./RESULTS/CORRECTIONS.md)、Foundation 的证明/实证义务和 Results Book 的显式残余继续开放；独立 GitHub Pages 阅读面已退出维护，仓库 Markdown 与相对链接是持续维护的人类阅读层。
- stale_knowledge: `0.4.0` 系统图和 `0.4.0` 之元写作法不再是当前版本；它们是历史资产。不要把旧页面、旧摘要或外部笔记中的旧 current 标签覆盖当前 main 记录。
- next_read: 先读 [AI 冷启动](./AI-START-HERE.md)、[AI 交接](./AI-HANDOFF.md)，再按任务进入 [Foundation](./FOUNDATION.md) 或 [成果/结果层](./RESULTS/README.md)。

## 2026-08-15 — STATE-CHANGELOG-ASSERTION-INFLATION-GUARD — main transition from 19658de18d1c22fff2265f94bcd8a08cdddc0609

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本条是从上述 main 基线进入下一正式主线状态的第一条 delta，提交后的精确 tip 由 Git 提交回执确定。
- delta: 新增本 AI 优先状态日志；把每次正式 main 合并追加 delta 写入 Agent 冷启动、交接、迭代、版本和 GetNote 工作流；在既有认识论治理内核中纳入 `ASSERTION_INFLATION_GUARD / K13_ASSERTION_NON_ESCALATION`。
- authority_changes: [认识论治理内核](./docs/architecture/epistemic-governance-kernel-and-federated-planes.md#共享-kernel-invariants)与其[机器关系索引](./data/governance/epistemic-governance-relationships.json)新增 K13；[同步表面注册表](./data/operations/synchronization-surfaces.json)新增本日志的 canonical source 义务。
- epistemic_state: 不提升任何具体 claim 的 M/E、proof、evidence、scope、provenance、disposition 或外部真值；新增的 K13 只把已有 Claim Ceiling、九轴独立、M/E 正交、回弹阻断和 provenance/adjudication/validation 约束组合成仓库级非晋级不变量。
- obligations: 此后每次正式 main 合并必须追加一条结构完整、链接可解析的 delta；长期风险登记为“系统可能从自我克制滑向大断言”，需在研究、裁决、写作、出版和系统总结中持续检查。现有开放义务不因本轮工程完成而关闭。
- stale_knowledge: 工程、写作、成果册、跨域呼应、重复引用、模型美感、CI 通过或 Agent 共识都不是新证据；被撤回/降级/quarantine 的结论不得借改名或上层综合文档回弹。
- next_read: 读 [K13 正式定义](./docs/architecture/epistemic-governance-kernel-and-federated-planes.md#k13_assertion_non-escalation--assertion_inflation_guard)、[断言治理](./docs/foundation/claim-governance-and-function-identity.md)和[迭代操作法的 Claim Ceiling](./ITERATION.md#4-claim-ceiling)。

## 2026-08-15 — IGNITION-20260815-116-HUMAN-SURFACE-ROOT-NORMALIZATION-SEEDS-MAP — main transition from f8976749c6ddd78e11ce6572048f94c7383642c1

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本条绑定本轮改造的 main 基线，最终发布 tip 由 Git 精确回执确定。
- delta: 把仓库人类入口迁到 `.github/README.md` 并收敛为五个首页部件；根目录归一为 `.github/`、`.gitignore`、`AGENTS.md`、`LICENSE`、`ignition/` 五个条目；新增《火种》、函数资产/非函数资产人类入口、唯一完整可点击总架构图，并清理当前失效 Pages 路由。历史 Pages 证据保留历史标记，不再作为当前入口。
- authority_changes: [首页](../.github/README.md)、[火种](./PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)、[火种候选普查](./data/publication/fire-seeds/seed-census.json)、[函数资产](./docs/human/function-assets/README.md)、[非函数资产](./docs/human/nonfunction-assets/README.md)、[唯一完整总架构图](./docs/generated/ignition-system-architecture.svg)、[Human Surface 编辑契约](./docs/governance/human-surface-editorial-contract.md)、[根目录迁移审计](./data/operations/root-normalization/post-migration-root-inventory.json)和既有 [K13 认识论治理内核](./docs/architecture/epistemic-governance-kernel-and-federated-planes.md#k13_assertion_non-escalation--assertion_inflation_guard)共同记录本轮变化。
- epistemic_state: 不提升任何 claim 的 `M/E`、九状态轴、claim ceiling、semantic、logic、proof、evidence、scope、provenance、disposition 或外部真值；人类资产、成果册、整体图、写作和工程投影都只是 canonical 记录的人类导航。K13、Claim Ceiling、九轴独立和回弹阻断继续作为非晋级不变量。
- obligations: 已关闭当前入口/路径迁移、当前 Pages 引用、人类资产/整体图/火种确定性投影与仓库内链接校验；历史记录仍需保留其原始 provenance。继续开放：每次正式 main 合并追加 delta、火种按 `SEED_DELTA`/`NO_SEED_DELTA` 协议更新、外部页面验证只以发布后 live receipt 为准，以及项目既有证明/实证/开放问题义务。
- stale_knowledge: 根目录 `README.md` 不再是当前入口，`.github/README.md` 才是当前首页；函数/非函数 closure JSON 不是首要人类阅读路由；旧 Pages URL 只在带历史标记的 121Q32 记录与负向测试中存在；“工程完成即断言升级”的认知继续失效。
- next_read: 先读 [首页](../.github/README.md)、本日志最近条目，再按目的读 [火种](./PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)、[函数资产](./docs/human/function-assets/README.md)、[非函数资产](./docs/human/nonfunction-assets/README.md)、[唯一完整总架构图](./docs/generated/ignition-system-architecture.svg)和 [当前项目现状](./docs/project-current-state.md)。

## 2026-08-15 — IGNITION-20260815-117-FIRE-SEED-CONTENT-ARCHAEOLOGY — main transition from 89b005566bdfe266414c850871793b9dd10ba0af

- main_state: CURRENT_WITH_OPEN_OBLIGATIONS; 本轮正式内容考古从远端 main 基线 89b005566bdfe266414c850871793b9dd10ba0af 开始，最终发布 tip 由 Git 提交与远端回执确定。
- delta: 将《火种》从上一轮 24 条方法论入口扩展为 40 条内容火种加 24 条方法论火种；内容回到文章、案例、GetNote 主题、函数族、研究报告、写作片段、失败与负结果，source census 覆盖知识体验层 308 个 source origins 加 1489 条补充人类语料。
- authority_changes: [火种](./PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)、[火种 source census](./data/publication/fire-seeds/seed-census.json)、[火种更新协议](./data/publication/fire-seeds/UPDATE-PROTOCOL.md)、[成果册入口](./PUBLICATIONS/pointfire-results-book/README.md)和[成果册变更记录](./PUBLICATIONS/pointfire-results-book/CHANGELOG.md)记录本轮内容层增量；根目录、首页、系统图和治理结构不在本轮范围。
- epistemic_state: 本轮不改变各权威对象的既有状态轴、范围、出处、记录期限或公开边界；外部新颖性未核验，EPISTEMICALLY_ACCEPTED=0 不变。内容火种只表示内部来源链上的研究问题、重组、反例或写作入口。
- obligations: 40 条内容入口仍需各自回到所链接文件、原有状态和开放义务；GetNote 未分配、ABSTAIN、未核证和 source recovery blocked 状态不被本轮内容化关闭；历史、withdrawn、quarantine、negative result、方法与外部核证缺口继续保留。
- stale_knowledge: 旧的 24 条 seed-census 仍是历史快照，不再覆盖本轮完整内容层；seed 数量不是独立依据数量，source census 不是新的登记权威，知识体验层的 308 也不是永久计数。
- next_read: 先读[内容火种](./PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)、[机器清册](./data/publication/fire-seeds/seed-census.json)和[更新协议](./data/publication/fire-seeds/UPDATE-PROTOCOL.md)，再按主题回到[成果册](./PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](./RESULTS/LATEST.md)和[开放问题](./RESULTS/OPEN-QUESTIONS.md)。

## 2026-08-15 — IGNITION-20260815-118-HUMAN-SURFACE-SECOND-REFINEMENT — main transition from 085f7d63b2492e5ee6c95739ccb1addb5608f152

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本轮以远端 `main` 基线 `085f7d63b2492e5ee6c95739ccb1addb5608f152` 开始，最终发布 tip 由 Git 提交与远端精确回执确定。
- delta: 将人类表面二次炼化为一条关系驱动、唯一可点击的完整总架构图；退役旧双图、PNG 路由、分页浏览器和旧非函数人类目录；完成 1,431 条旧函数/案例来源的迁移审计、归档与删除；把《函数资产》《非函数资产》收敛为入口、主题、处置和人话说明四层，并固定机器清册与人类说明的分工。
- authority_changes: [Human Surface 编辑契约](./docs/governance/human-surface-editorial-contract.md)、[函数资产](./docs/human/function-assets/README.md)、[非函数资产](./docs/human/nonfunction-assets/README.md)、[唯一完整总架构图](./docs/generated/ignition-system-architecture.svg)、[旧表迁移清册](./data/foundation/migrations/legacy-table-migration.jsonl)、[系统图关系投影](./data/architecture/interactive-system-map.json)和[机器知识体验层](./KNOWLEDGE/README.md)共同记录本轮变化；首页只更新当前入口与图链接，保留人工编辑的项目说明和引文。
- epistemic_state: 不提升任何 claim 的 `M/E`、九状态轴、claim ceiling、semantic、logic、proof、evidence、scope、provenance、disposition 或外部真值；Human Surface 结构校验不判断散文质量、因果性、真值或外部新颖性。`EPISTEMICALLY_ACCEPTED=0` 保持不变，K13 与“之元写作法 0.5.0”继续作为非晋级边界。
- obligations: 旧来源的 Git 历史、原始路径、ID、blob、处置和归档内容继续由迁移清册承载；人类文字仍需回到机器记录、M/E、证据、proof、claim ceiling 与开放义务；机器专属批量记录、人工散文审校、外部证据/复制/真值和既有研究问题仍开放。
- stale_knowledge: 旧函数/案例总表目录、旧双 SVG、PNG、`page-001` 分页 IA 和旧非函数人类目录不再是当前入口；历史记录中的旧路径只作为 provenance 或迁移边界保留。人话页不是新的权威层，生成通过不等于 prose、claim 或现实命题成立。
- next_read: 先读[首页](../.github/README.md)、[Human Surface 编辑契约](./docs/governance/human-surface-editorial-contract.md)、[唯一完整总架构图](./docs/generated/ignition-system-architecture.svg)和[旧表迁移清册](./data/foundation/migrations/legacy-table-migration.jsonl)，再进入[函数资产](./docs/human/function-assets/README.md)、[非函数资产](./docs/human/nonfunction-assets/README.md)及对应机器 registry。

## 2026-08-15 — IGNITION-20260815-119-AGENTIZATION-BOUNDARY-R0 — main transition from 4f4358ef09d1871a48d7e32575a63453130b333c

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本轮从任务 118 的正式 main 基线 `4f4358ef09d1871a48d7e32575a63453130b333c` 开始，最终发布 tip 由 Git、远端和全新克隆精确回执确定。
- delta: 从知识治理系统抽出领域无关 Generic Kernel 与 Agent Runtime R0，建立 `Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop` typed loop、Agent Profile、Domain Pack Manifest、checkpoint/resume/handoff、fail-closed capability authorization 和非知识 manifest pilot；现有知识系统仅登记为第一个 Knowledge Domain Pack，未做全仓物理迁移。
- authority_changes: [Agentization Boundary manifest](./data/architecture/agentization-boundary-r0.json)由 live [component registry](./data/operations/project-components.json)确定性生成；[Generic Kernel](./agent_kernel/README.md)、[Agent Runtime](./agent_runtime/README.md)、[Knowledge Pack](./packs/knowledge/manifest.json)、[非知识 pilot 回执](./data/agent-runtime/pilots/non-knowledge-manifest-r0/pilot-receipt.json)、[Task 115 prior-art 审计](./reports/architecture/task115-runtime-prior-art-adoption-r0.md)、[唯一系统图 0.6.0](./data/architecture/interactive-system-map.json)和[Human Surface](./docs/architecture/agentization-boundary-r0.md)共同记录本轮边界。
- epistemic_state: 不提升任何 claim 的 `M/E`、proof、evidence、scope、provenance、claim ceiling、Owner acceptance 或外部真值；非知识 pilot 的 `COMPLETED_VALIDATED` 只表示声明输入、写集、checkpoint/resume lineage 和 validator 在仓库范围内通过。`EPISTEMICALLY_ACCEPTED=0` 与 K13 非晋级不变量保持不变。
- obligations: Task 115 Draft 不合并；真实 provider/API、daemon、Telegram/OpenClaw、多 agent scheduler、向量/embedding memory、Pack 物理拆分、外部 Owner acceptance 和跨领域实质效用仍开放。历史 Foundation、claims、M/E、Evidence、REOS、写作与出版路径继续由原有权威资产管理。
- stale_knowledge: 工程门禁、runtime trace、系统图可见性、仓库回执和 Agent 共识都不等于知识真值、现实因果、AGI、人格或意识；Pack 可加载不表示 Pack 获得通用权限。系统图 `0.5.0` 及更早版本降为 Historical，`0.6.0` 才是当前 registry-derived projection。
- next_read: 先读[首页](../.github/README.md)、本条与[当前项目现状](./docs/project-current-state.md)，再读[智能体化边界 R0](./docs/architecture/agentization-boundary-r0.md)、[Kernel](./agent_kernel/README.md)、[Runtime](./agent_runtime/README.md)、[pilot receipt](./data/agent-runtime/pilots/non-knowledge-manifest-r0/pilot-receipt.json)和[机器边界清单](./data/architecture/agentization-boundary-r0.json)。

## 2026-08-15 — IGNITION-20260815-120-AGENT-RUNTIME-R1 — main transition from 834fce29afdadb47adda08a95631303ad0d94fc7

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本轮从任务 119 的正式 main 基线 `834fce29afdadb47adda08a95631303ad0d94fc7` 开始，最终发布 tip 由 Git、远端和全新克隆精确回执确定。
- delta: 在 R0 typed loop 之上增加真实本地文件/命令行动层、workspace path/symlink/special-file/allowlist 边界、execution packet/source-plan digest、locked lease/idempotency、typed approval、action journal、崩溃恢复、allowlisted JSONL Reasoner transport、CLI 和 bounded local rollback；不做全仓物理拆分。
- authority_changes: [Agent Runtime R1](./docs/architecture/agent-runtime-r1.md)、[R1 action schemas](./schemas/agent-runtime/)、[R1 local pilots](./agent_runtime/pilots/r1_real_local.py)和 [R1 tests](./tests/test_agent_runtime_r1.py)记录当前执行面；R0 的 Kernel、Runtime、非知识 pilot 和 Task 115 audit 仍是历史/回归入口。
- epistemic_state: `COMPLETED_VALIDATED` 只表示一条本地 bounded run 的 typed validation 通过；`FAILED_VALIDATION_ROLLED_BACK` 只表示失败后 whole-file preimage 恢复通过。工程回执、CLI、lease、pilot 和跨 executor 恢复不提升 M/E、proof、scope、provenance、claim ceiling、Owner acceptance、外部真值或因果效果；`EPISTEMICALLY_ACCEPTED=0` 不变。
- obligations: 真实 provider/model 接入、multi-agent、vector/embedding memory、persona、scheduler/daemon、Telegram/OpenClaw/Hermes、网络/浏览、物理 Domain Pack migration、Git mutation、外部 Owner acceptance 和现实效果仍开放；unsupported rollback actions 只能进入明确 residual/stop state。
- stale_knowledge: R0 的 abstract Reasoner/Executor/Validator 只是历史边界，不应被写成已接入真实 provider；R1 的本地 pilot 也不应被改写成通用自治或生产 daemon 证明。
- next_read: 先读本条、[Agent Runtime R1](./docs/architecture/agent-runtime-r1.md)、[Runtime README](./agent_runtime/README.md)、[R1 schemas](./schemas/agent-runtime/)和 [R1 tests](./tests/test_agent_runtime_r1.py)，再回到 [R0 boundary](./docs/architecture/agentization-boundary-r0.md)；Task 119 的 1111 receipt 只在 1111 relay worktree 中读取。

## 2026-08-16 — IGNITION-20260816-121-AGENT-PLATFORM-R2-NIGHT-SHIFT-PRE-RELEASE — task-branch projection from 2becca3ffd93d6ca1e147a75c159e476f4686f5d

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; this is a task-branch pre-release projection at `983aff0b280313c79d82484f609e5a45d721fd63`, not a claim that `origin/main` has moved. Formal main lifecycle remains pending Step 12 exact fast-forward and fresh-clone verification.
- delta: Task 121 R2 connects the bounded Agent Platform spine: Pack Registry/Bus, Knowledge/Research/Writing/Maintenance manifests, Profile narrowing, Reasoner Gateway proposals, Pack-aware routing, non-vector operational memory, Supervisor multi-Run DAG, propagation contracts and a real offline fresh-clone maintenance episode.
- authority_changes: [Agent Platform R2](./docs/architecture/agent-platform-r2.md), [Agent Runtime](./agent_runtime/README.md), [Kernel](./agent_kernel/README.md), [Pack manifests](./packs/), [R2 pilot receipt](./data/agent-runtime/pilots/r2-offline-repository-maintenance/pilot-receipt.json), [R2 propagation contract](./data/operations/propagation/agent-platform-r2-propagation-contract.json), [night-shift ledger](./data/operations/iterations/121/nightshift-progress.jsonl) and [current Results](./RESULTS/LATEST.md) are synchronized as repository surfaces; canonical registries and claim/evidence assets remain authoritative.
- epistemic_state: R2 tests, validators, Pack load, checkpoint/resume, operational memory and offline pilot are repository execution evidence only. They do not upgrade M/E, the nine state axes, claim ceiling, Owner acceptance, external truth, causality, general intelligence or `EPISTEMICALLY_ACCEPTED=0`.
- obligations: Step 10 documentation synchronization is recorded on this task branch; Step 11 adversarial/full regression and Step 12 fresh-clone replay, final fast-forward, formal main delta and 1111 relay receipt remain open. Live providers, daemons, network/browser actions, vector memory, external Git mutation, physical Pack migration and external validity remain out of scope.
- stale_knowledge: Task 119/120 R0/R1-only descriptions are historical compatibility surfaces; R2 is now the current engineering projection on this branch. A successful pilot is not a production or general-intelligence result, and this pre-release entry must not be read as a main merge receipt.
- next_read: read [Agent Platform R2](./docs/architecture/agent-platform-r2.md), [R2 pilot brief](./data/agent-runtime/pilots/r2-offline-repository-maintenance/HUMAN-REPORT.md), [night-shift progress](./reports/operations/ignition-121-nightshift-progress.md), then verify Step 11 and Step 12 before treating the identity as current main.

## 2026-08-16 — IGNITION-20260816-121-AGENT-PLATFORM-R2-FINAL-CANDIDATE — transition from main@2becca3ffd93d6ca1e147a75c159e476f4686f5d

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; this append-only delta is the formal main-release candidate for Task 121. The exact final main tip is established by the ordinary fast-forward Git receipt and independent 1111 receipt after this checkpoint, not by a self-referential hash in this file.
- delta: closes the bounded Agent Platform R2 night-shift candidate across Kernel/Runtime, Pack Registry/Bus, operational Memory, Supervisor multi-Run DAG, Agent Profile, Reasoner Gateway, Pack-aware routing, propagation boundaries, Knowledge corpus admission, Human Surface and deterministic repository projections. The committed-tree correction removes one stale path-classification row exposed by the first clean-clone replay; no claim registry meaning or authority boundary changed.
- authority_changes: [Agent Platform R2](./docs/architecture/agent-platform-r2.md), [Kernel](./agent_kernel/README.md), [Runtime](./agent_runtime/README.md), [Pack manifests](./packs/), [R2 pilot receipt](./data/agent-runtime/pilots/r2-offline-repository-maintenance/pilot-receipt.json), [R2 propagation contract](./data/operations/propagation/agent-platform-r2-propagation-contract.json), [path classification manifest](./data/foundation/repository-path-classification/classification-manifest.jsonl), [Knowledge Experience](./data/governance/knowledge-experience/manifest.json), [night-shift ledger](./data/operations/iterations/121/nightshift-progress.jsonl) and [night-shift report](./reports/operations/ignition-121-nightshift-progress.md) remain the relevant repository surfaces; canonical registries and claim/evidence records remain authoritative.
- epistemic_state: `CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain unchanged. Tests, receipts, generators, fresh-clone replay, Pack load, checkpoint/resume and local fast-forward evidence are repository synchronization/engineering evidence only; they do not establish external truth, causality, production safety, Owner acceptance, general intelligence or external validity.
- obligations: the environmental `T16_SYMPY_COUNTEREXAMPLE` residual remains explicitly classified from full regression; live providers, daemons, network/browser actions, vector memory, automatic remote mutation, physical Pack migration, external validation and Owner acceptance remain out of scope. Final exact main/branch/fresh-clone equality and the independent 1111 receipt are required release evidence.
- stale_knowledge: the earlier Task 121 pre-release delta naming the Step 09 tip is historical branch-progress evidence and must not override the final Git/1111 receipt; `main` identity is current only after the no-force fast-forward and exact verification.
- next_read: read this delta, [night-shift progress](./reports/operations/ignition-121-nightshift-progress.md), [night-shift ledger](./data/operations/iterations/121/nightshift-progress.jsonl), then verify the final task-branch, `origin/main`, fresh clone and 1111 receipt SHAs.
