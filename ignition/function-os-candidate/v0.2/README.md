# Function OS v0.2

当前包版本：`0.2.1rc0`

当前地位：candidate reference implementation。

Function OS 不是 macOS、Linux 这类通用操作系统；不是万能证明器、科学真理机器、任意代码沙箱或成熟生产平台。它是点火项目里的一个候选符号函数流水线：把边界明确的函数规格转化为可执行、可追踪、可验证、可组合、可登记的工件。

## Function OS 是做什么的

一句话：Function OS 帮你把“我想让这个函数在这些输入、输出、条件和副作用边界内运行”变成一串可检查的规格、工件、执行结果、trace、验证报告和 registry 记录。

技术上，它把 FunctionSpec 解析为受限表示，编译成符号 artifact，在解释器中执行，记录 ExecutionTrace，用验证器检查规格、工件和 trace 是否一致，再把通过边界的结果登记为可审计的 revision。它执行已经被表达成函数契约的部分，不决定这个行动是否值得做，也不把一次 PASS 自动升级为科学证明。

## N1-N9 各自负责什么

| Node | 名称 | 责任 |
|---|---|---|
| N1 | FunctionSpec / 安全表达式与语义检查 | 解析函数规格，检查输入、输出、前置条件、后置条件和副作用声明；Safe Expression DSL 只允许受限 AST。 |
| N2 | Representation | 把规格编码成机器可读的中间表示，并生成可追踪哈希。 |
| N3 | Compiler | 把 FunctionSpec 与 Representation 编译成可包装的符号 payload。 |
| N4 | Artifact Packager | 生成带版本、内容哈希、规格哈希和表示哈希的 artifact。 |
| N5 | Interpreter | 用 artifact 和输入执行函数，返回 `OK`、前置条件失败、后置条件失败或错误状态。 |
| N6 | Execution Trace | 记录执行事件、输入输出摘要、状态、时间和 trace hash。 |
| N7 | Validator / Feedback | 检查规格、表示、artifact 和 trace 的一致性，并给出验证状态与修订反馈。 |
| N8 | Composer / Router | 根据任务和候选函数生成执行计划；当前主要是 sequential plan，不是自动函数发现、复杂动态规划或成熟分布式调度。 |
| N9 | Registry / revision / rollback | 登记通过边界的记录，维护 revision、更新和 rollback 审计链。 |

## 人类怎样使用

1. 选一个边界明确的问题，不要从含混愿望开始。
2. 定义输入、输出、前置条件、后置条件和副作用。
3. 审查规格是否忠实表达现实问题，尤其检查是否漏掉风险、语境或不可形式化部分。
4. 运行 N1-N7，查看规格、artifact、执行结果、trace 和验证报告。
5. 只在验证通过且结论边界明确时进入 N9 registry。
6. 后续更新必须生成 revision；发现规格错误、现实定义错误或验证失败时，必要时 rollback。

## AI 怎样使用

AI 可以承担：

- 候选规格生成；
- registry 检索；
- 输入准备；
- 执行与 trace 收集；
- N7 反馈后的修订建议；
- 审计记录整理。

AI 不得：

- 把自己的输出当外部事实证据；
- 把一次 PASS 写成科学证明；
- 因用户期待提高结论等级；
- 绕过 Charter Gate 或人类责任；
- 用“完成”替代规格、工件、输入、输出、trace 和验证记录。

## 能产出什么

Function OS 当前可产出：

- FunctionSpec；
- 中间表示及哈希；
- 编译结果；
- Artifact 及内容哈希；
- 执行结果与错误状态；
- 前置/后置条件检查；
- ExecutionTrace；
- N7 验证报告与修订反馈；
- 顺序执行计划；
- Registry 记录、revision 与 rollback 记录；
- legacy asset import 候选工件。

## 最小示例

现有集成测试使用一个加法规格作为 N1-N9 全链路示例。对应源码见 [`tests/test_integration_full_chain.py`](tests/test_integration_full_chain.py)。

- 输入 `x=3, y=7` 时，N5 返回 `OK`，`result=10`；随后可生成 trace，通过 N7，并进入 N9 registry。
- 输入 `x=-1, y=7` 时，前置条件 `x >= 0` 失败，返回 `PRECONDITION_FAILED`；测试明确要求它不得作为成功执行登记。

这个示例只说明受控符号函数流水线可以按规格运行；它不证明现实世界中的任意加法问题、科学命题或伦理判断已经成立。

## 限制是什么

- 当前是候选实现，缺少长期生产使用和独立安全审计。
- Safe Expression DSL 只支持受限 AST、基本算术、比较、布尔和条件表达式。
- 禁止任意函数调用、属性访问、`eval`、`exec`、`os`、`subprocess`。
- 这不是完整安全沙箱；当前没有足够证据证明可以直接执行完全不可信的恶意表达式。
- `pure`、`stateful`、`io` 标签不等于已经完整实现文件、网络、数据库或事务运行时。
- N8 当前主要是 sequential plan，不是成熟的自动函数发现、复杂动态规划或分布式调度系统。
- 不适合直接承担浏览器控制、任意 Python、网络抓取、大型数值计算、模型推理、复杂并发和分布式任务。

## 边界是什么

Function OS 执行已经被表达成函数契约的部分，不决定什么值得做。Charter Gate 决定价值边界；Foundation 与验证层决定对象、证据、证明和状态边界。

一个内部一致但现实定义错误的规格仍可能顺利执行。PASS 只说明指定检查通过，不自动证明经验真实性、因果机制、普遍正确或伦理正当。Function OS 是点火的一部分，不等于点火全部。

## 快速检查

```bash
cd function-os-candidate/v0.2
python -m pytest tests
```

## 基准与已知缺陷（任务 105）

Function OS v0.2 在 `16f64004` 上接受了任务 105 的预注册对抗基准（479 个确定性案例、3 层、7 项主张）。结论原样封存于 `function-os-candidate/v0.2/benchmark/`，并以编辑文章 `docs/editorial/articles/007-*` 叙述：

- **失败闭合边界、契约执行、制品/迹完整性、注册表修订与回滚、有界顺序组合**：原始目标即全部 `SUPPORTED`，无失败闭合（`false_accept_rate = 0.0`，`registry_contamination_count = 0`，`mutation_detection_rate = 1.0`）。
- **语义保真（A1）**：原始目标 `0.9372`（阈值 `0.99`）——缺口来自一个**真实的实现缺陷**：`N2RepresentationEncoder._extract_expressions` 对嵌套相等后条件（如 `result == (x == y)`）用 `split('==')`（全拆分）取到不完整右端，导致 25 个案例执行期 `RUNTIME_ERROR`。该缺陷已被**有界修复**（`split('==', 1)`，提交 `1314ba80`）并加回归测试；修复后 A1 = `1.0`，整体 `SUPPORTED_WITHIN_BOUNDED_DOMAIN`。原始失败结果作为独立提交 `aa803277` 原样留存，未删改、未掩盖。
- **处置边界**：本次基准只测 v0.2 **自己声明过**的有界能力。它**不改变**本页"限制是什么 / 边界是什么"——v0.2 仍是候选参考实现，不是完整安全沙箱、不是生产就绪、不是通用证明系统、不是外部真理机。发现并被修复的是一个实现缺陷，不是能力主张缺陷。

## 文档入口

- [现行架构](../../ARCHITECTURE.md) — 说明 Function OS 在点火七层架构与操作 overlay 中的位置。
- [Foundation](../../FOUNDATION.md) — 说明对象、命题、证明、验证和状态边界。
- [项目现状](../../docs/project-current-state.md) — 说明当前版本已经长成什么，以及哪些说法仍不能越界。
- [生命共同体价值宪章](../../docs/governance/life-community-value-charter.md) — 说明 Charter Gate 如何约束“什么值得做”。
- [Function OS 源码](function_os/) — 查看 N1-N9 的候选参考实现。
- [N1-N9 集成测试](tests/test_integration_full_chain.py) — 查看加法示例和 registry revision / rollback 测试。
- [Function OS CI](../../.github/workflows/function-os-ci.yml) — 查看远端测试工作流。
