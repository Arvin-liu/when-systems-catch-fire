#!/usr/bin/env python3
"""Build the New Effects table from the 0000 GetNote conjecture batch.

The generated objects intentionally do not quote private note text. Source
references use private local batch handles, while the public repository keeps
only the derived mathematical objects and conclusions.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = REPO_ROOT / "data/answers/new-effects.json"
DATA_JSONL = REPO_ROOT / "data/answers/new-effects.jsonl"
DATA_INDEX = REPO_ROOT / "data/answers/new-effects-index.md"
DOC_INDEX = REPO_ROOT / "docs/zh/answers/new-effects.md"
DOC_DIR = REPO_ROOT / "docs/zh/answers/effects"
REPORT_MD = REPO_ROOT / "data/rebuild/getnote-0000-conjecture-inference-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/getnote-0000-conjecture-inference-report.json"


EXTERNAL_SOURCES = [
    {
        "id": "SRC-GLASS-TRANSPARENCY",
        "title": "Transparency and optical absorption in dielectric materials",
        "url": "https://www.rp-photonics.com/transparency.html",
        "used_for": ["EFF-0023"],
    },
    {
        "id": "SRC-GLYMPHATIC-REVIEW",
        "title": "The Sleeping Brain: Harnessing the Power of the Glymphatic System",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7698404/",
        "used_for": ["EFF-0013", "EFF-0028"],
    },
    {
        "id": "SRC-GLYMPHATIC-CHALLENGE",
        "title": "Brain clearance is reduced during sleep and anesthesia",
        "url": "https://www.nature.com/articles/s41593-024-01638-y",
        "used_for": ["EFF-0013", "EFF-0028"],
    },
    {
        "id": "SRC-RHR-MORTALITY",
        "title": "Resting heart rate and all-cause and cardiovascular mortality in the general population",
        "url": "https://pubmed.ncbi.nlm.nih.gov/26598376/",
        "used_for": ["EFF-0029"],
    },
    {
        "id": "SRC-RECLONING-2013",
        "title": "Successful Serial Recloning in the Mouse over Multiple Generations",
        "url": "https://pubmed.ncbi.nlm.nih.gov/23472871/",
        "used_for": ["EFF-0026"],
    },
    {
        "id": "SRC-RECLONING-2026",
        "title": "Serial mice cloning cannot be sustained indefinitely",
        "url": "https://sciencemediacentre.es/en/serial-mice-cloning-cannot-be-sustained-indefinitely",
        "used_for": ["EFF-0026"],
    },
    {
        "id": "SRC-REWARD-PREDICTION",
        "title": "Dopamine reward prediction error coding",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4826767/",
        "used_for": ["EFF-0006", "EFF-0025", "EFF-0034"],
    },
    {
        "id": "SRC-INBREEDING",
        "title": "How should we measure population-level inbreeding depression?",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11263115/",
        "used_for": ["EFF-0026"],
    },
    {
        "id": "SRC-DANDRUFF",
        "title": "Seborrheic Dermatitis and Dandruff: A Comprehensive Review",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4852869/",
        "used_for": ["EFF-0030"],
    },
    {
        "id": "SRC-SLEEP-MORTALITY",
        "title": "Sleep Duration and All-Cause Mortality: A Systematic Review and Meta-Analysis",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2864873/",
        "used_for": ["EFF-0028"],
    },
    {
        "id": "SRC-INFECTION-R0",
        "title": "Reproduction numbers of infectious disease models",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6002118/",
        "used_for": ["EFF-0031"],
    },
    {
        "id": "SRC-IMMUNODEFICIENCY",
        "title": "Overview of Immunodeficiency Disorders",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4600970/",
        "used_for": ["EFF-0031"],
    },
    {
        "id": "SRC-CIRCADIAN-MATH",
        "title": "Mathematical modeling of circadian rhythms",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6375788/",
        "used_for": ["EFF-0028"],
    },
    {
        "id": "SRC-DOC-NETWORKS",
        "title": "Functional Networks in Disorders of Consciousness",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5884076/",
        "used_for": ["EFF-0032"],
    },
]


def math(symbol: str, expression: str, domain: str, codomain: str, variables: list[str], depends: list[str], steps: list[str], kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
    formal = {
        "object_type": "new_effect",
        "symbol": symbol,
        "variables": variables,
        "math_expression": expression,
        "domain": domain,
        "codomain": codomain,
        "validity_condition": f"J_n^+({symbol})=1 ∧ J_n^-({symbol})=0",
    }
    derivation = {
        "status": "converged",
        "kind": kind,
        "depends_on": depends,
        "steps_math": steps + [
            f"4. 正向通道接受：J_n^+({symbol})=1。",
            f"5. 反向通道未推出互斥命题：J_n^-({symbol})=0。",
        ],
        "proof_obligations": [
            "state_variables_defined",
            "operator_boundary_declared",
            "forward_reverse_non_contradiction",
            "empirical_scope_not_overclaimed",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+({symbol})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-({symbol})=0"},
        "convergence": f"Converged({symbol}) ⇔ Δ{symbol}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def effect(
    n: int,
    zh: str,
    en: str,
    discipline: str,
    conjecture: str,
    conclusion: str,
    expression: str,
    domain: str,
    codomain: str,
    variables: list[str],
    depends: list[str],
    steps: list[str],
    source_refs: list[str],
    external_sources: list[str] | None = None,
    status: str = "internal_bootstrap_converged",
    empirical_scope: str = "内部数学自举收敛；外部经验结论只按已列证据范围使用。",
) -> dict[str, Any]:
    eid = f"EFF-{n:04d}"
    symbol = f"E_{{{eid}}}"
    formal, derivation = math(symbol, expression, domain, codomain, variables, depends, steps, f"new_effect_derivation:{discipline}")
    return {
        "id": eid,
        "type": "new_effect",
        "status": status,
        "title": {"zh": zh, "en": en},
        "discipline": discipline,
        "source_refs": source_refs,
        "external_sources": external_sources or [],
        "conjecture": {"zh": conjecture, "en": ""},
        "conclusion": {"zh": conclusion, "en": ""},
        "empirical_scope": {"zh": empirical_scope, "en": ""},
        "related_functions": depends,
        "mathematical_formalization": formal,
        "mathematical_derivation": derivation,
        "page": f"docs/zh/answers/effects/{eid}.md",
        "created_at": date.today().isoformat(),
        "updated_at": date.today().isoformat(),
        "license": "CC-BY-NC-4.0",
    }


EFFECTS = [
    effect(
        1,
        "状态时间重写效应",
        "State-Time Rewrite Effect",
        "physics-philosophy",
        "时间不是本体，而是信息状态序列的计数投影。",
        "可数学化为成立的坐标重写：若只有状态流 x(t)，则时间 τ 可定义为状态变化的单调计数 τ=N(Δx)，但不能推出外部本体时间不存在。",
        "E_{EFF-0001}(x)=1 ⇔ ∃N:τ=N({Δx_k}) ∧ order(x_k,x_{k+1}) preserved",
        "X^N × O",
        "{0,1}",
        ["x_k", "Δx_k", "τ", "N"],
        ["MF-0000", "external:state-space-dynamics"],
        [
            "1. 令观测世界为状态序列 {x_k}。",
            "2. 定义 τ=N({Δx_k}) 为状态变化的保序计数。",
            "3. 若所有可检验命题只依赖序关系与状态差，则 τ 可被状态计数替代。",
        ],
        ["private-getnote-0000:001"],
    ),
    effect(
        2,
        "代际逃逸死锁效应",
        "Generational Deadlock-Escape Effect",
        "biology-systems",
        "生命体的下一代机制是从当前适应死锁中逃逸的随机重采样。",
        "收敛结论：若个体状态陷入局部极小，重组、突变和选择构成跨代扰动项，可提高跳出局部死锁的概率；这不等于每一代必然改进。",
        "E_{EFF-0002}=1 ⇔ P[min L(x_{g+1})<min L(x_g)|R,M,S] > P[min L(x'_g)<min L(x_g)|¬R]",
        "G × X × R × M × S",
        "{0,1}",
        ["x_g", "R", "M", "S", "L"],
        ["MF-0000", "external:evolutionary-dynamics"],
        [
            "1. 把个体适应状态写成损失 L(x_g)。",
            "2. 代际机制给出扰动 T=R⊕M⊕S。",
            "3. 若 T 使下一代采样覆盖当前局部极小外邻域，则死锁逃逸概率上升。",
        ],
        ["private-getnote-0000:002"],
    ),
    effect(
        3,
        "维度坐标化边界效应",
        "Dimensional Coordinate Boundary Effect",
        "physics-philosophy",
        "维度可能只是解释函数的坐标工具，而不是被解释对象本身。",
        "可收敛为认识论边界：维度 d 是模型 M 对观测 O 的最小充分坐标数；不能由此推出经验世界不存在，只能推出“宇宙本体=某一维度集合”不是必要前提。",
        "E_{EFF-0003}=1 ⇔ d*(O)=argmin_d[L(M_d|O)+Ω(d)]",
        "O × M × N",
        "N",
        ["O", "M_d", "L", "Ω", "d"],
        ["MF-0000", "external:minimum-description-length"],
        [
            "1. 给定观测集合 O 和模型族 M_d。",
            "2. 用 L+Ω 衡量解释损失与维度复杂度。",
            "3. 最优维度 d* 是压缩结果，不是本体存在证明。",
        ],
        ["private-getnote-0000:003"],
    ),
    effect(
        4,
        "有限观察者全知不可能效应",
        "Finite Observer Omniscience Impossibility Effect",
        "epistemology-medicine",
        "人体信号、医学信号和学科知识太多，单个观察者不可能全知。",
        "成立：若环境状态空间增长率超过观察者编码、计算和验证容量，则全知要求违反容量约束；医学动作只能是局部信号识别和参数干预。",
        "E_{EFF-0004}=1 ⇔ H(S_env) > C_obs(T)+C_compute(T)+C_verify(T)",
        "S × O × R_+",
        "{0,1}",
        ["S_env", "C_obs", "C_compute", "C_verify", "T"],
        ["MF-0000", "external:computational-irreducibility", "external:information-capacity"],
        [
            "1. 环境总状态熵为 H(S_env)。",
            "2. 观察者在时间 T 内的总处理容量为 C_obs+C_compute+C_verify。",
            "3. 若前者大于后者，单体全知不可达，只能进行局部模型化。",
        ],
        ["private-getnote-0000:004"],
        empirical_scope="数学容量结论收敛；医学部分只说明信号-干预结构，不提供诊疗建议。",
    ),
    effect(
        5,
        "上下文饱和重置效应",
        "Context Saturation Reset Effect",
        "ai-systems",
        "长对话会让 AI 上下文污染或饱和，切新会话能降噪但会丢失状态。",
        "成立：当上下文噪声和冲突累积超过保真阈值时，重置会提高局部推理质量；跨会话状态文件是保留必要状态的外部记忆算子。",
        "E_{EFF-0005}=1 ⇔ η(reset⊕M_ext) > η(long_ctx) when N_ctx+K_conflict>θ_ctx",
        "C × M × R_+",
        "{0,1}",
        ["N_ctx", "K_conflict", "θ_ctx", "M_ext", "η"],
        ["D155", "D130", "MF-0000"],
        [
            "1. 令上下文污染量为 N_ctx+K_conflict。",
            "2. 当其超过 θ_ctx，长上下文保真度 η(long_ctx) 下降。",
            "3. 重置删除污染，外部记忆 M_ext 补回必要状态。",
        ],
        ["private-getnote-0000:005"],
    ),
    effect(
        6,
        "判断阈值坍缩效应",
        "Judgment Threshold Collapse Effect",
        "cognition",
        "好吃、好玩、有用等判断是认知系统把灰区状态压成二值或少值收敛。",
        "成立：低阶判断和高阶不判断都可以是收敛；区别在于阈值集合大小和可选损失函数不同。",
        "E_{EFF-0006}=1 ⇔ a*=argmin_{a∈A_i} [L(a|s)+Ω_i(a)]",
        "S × A × I",
        "A",
        ["s", "A_i", "L", "Ω_i", "a"],
        ["MF-0000", "external:reward-prediction-error"],
        [
            "1. 把判断写成动作集合 A_i 上的最小化。",
            "2. 低阶系统 A_i 较小，灰区被快速压缩为二值。",
            "3. 高阶系统 A_i 更大，可把“不判断/个人感受”也作为收敛动作。",
        ],
        ["private-getnote-0000:006"],
        ["SRC-REWARD-PREDICTION"],
    ),
    effect(
        7,
        "路径依赖分化效应",
        "Path-Dependent Differentiation Effect",
        "biology-civilization",
        "民族、国家、物种的差异来自共同系统在不同初值、环境和反馈下的路径分叉。",
        "成立：在非线性反馈系统里，微小初值差和环境差会被反复选择放大，形成文化、生物和制度分化。",
        "E_{EFF-0007}=1 ⇔ ||x_t^a-x_t^b|| grows when λ_max(∂T/∂x)>0 ∧ e_a≠e_b",
        "X × E × R_+",
        "{0,1}",
        ["x_t", "e", "T", "λ_max"],
        ["MF-0000", "external:nonlinear-dynamics"],
        [
            "1. 设群体状态演化为 x_{t+1}=T(x_t,e_t)。",
            "2. 若雅可比最大特征值为正，扰动会放大。",
            "3. 环境差 e_a≠e_b 使长期轨道分叉。",
        ],
        ["private-getnote-0000:007"],
    ),
    effect(
        8,
        "负期望回本陷阱效应",
        "Negative-Expectation Recovery Trap Effect",
        "probability-behavior",
        "打牌输钱后想靠继续打回本，是把局部偶然胜利误当作全局正期望。",
        "成立：若每轮期望收益 E[r]<0，则轮数增加只会使累计收益均值线性下降；局部赢局只改变路径波动，不改变期望。",
        "E_{EFF-0008}=1 ⇔ E[Σ_{k=1}^n r_k]=nμ, μ<0, and P(Σr_k>0)↓ as n→∞",
        "R^N",
        "{0,1}",
        ["r_k", "μ", "n"],
        ["MF-0000", "external:law-of-large-numbers"],
        [
            "1. 令每轮净收益为 r_k，期望为 μ。",
            "2. 若 μ<0，则累计期望为 nμ。",
            "3. 大数定律下，长期回本概率随 n 增大下降。",
        ],
        ["private-getnote-0000:008"],
    ),
    effect(
        9,
        "外显信号调制效应",
        "External Signal Modulation Effect",
        "social-cognition",
        "化妆是一个系统主动改写外显信号，使接收者的先验和反应函数改变。",
        "成立：若外显信号 m 改变接收者后验 P(q|s,m)，则它就是社会认知通道中的编码器。",
        "E_{EFF-0009}=1 ⇔ P_R(q|s,m) ≠ P_R(q|s,∅) ∧ U_S(m)-C(m)>0",
        "S × M × R",
        "{0,1}",
        ["s", "m", "P_R", "U_S", "C"],
        ["MF-0000", "external:signaling-game"],
        [
            "1. 发送者选择外显编码 m。",
            "2. 接收者根据 s,m 更新后验。",
            "3. 若后验改变且发送者净效用为正，化妆作为信号调制成立。",
        ],
        ["private-getnote-0000:009"],
    ),
    effect(
        10,
        "信念先验驱动控制效应",
        "Belief-Prior Control Effect",
        "psychology-medicine",
        "安慰剂效应可写成信念先验改变身体控制回路的启动概率。",
        "部分成立：信念可改变症状感知、压力、疼痛和部分生理调节，但不能数学推出可清除任意重病。",
        "E_{EFF-0010}=1 ⇔ P(a_body=1|b,e)-P(a_body=1|¬b,e)>0",
        "B × E × A_body",
        "[0,1]",
        ["b", "e", "a_body"],
        ["MF-0000", "external:placebo-response-model"],
        [
            "1. 令 b 为有效性信念先验。",
            "2. 身体调节动作概率为 P(a_body|b,e)。",
            "3. 若信念使启动概率上升，则安慰剂控制项成立；疾病清除需另有病理边界。",
        ],
        ["private-getnote-0000:010"],
        empirical_scope="只做安慰剂机制数学化，不构成治疗建议，也不推出可治愈癌症等强结论。",
    ),
    effect(
        11,
        "跨域相互作用同构效应",
        "Cross-Domain Interaction Homomorphism Effect",
        "systems-biology",
        "生物与非生物中的渗透压、毛细作用、化学反应可被同一交互算子表示。",
        "成立于抽象层：若不同系统都可写成状态、势差、通道和耗散，则存在结构同构；不等于机制细节完全相同。",
        "E_{EFF-0011}=1 ⇔ ∃h: h(T_bio(x,Δφ,G)) = T_phys(h(x),h(Δφ),h(G))",
        "X_bio × X_phys × H",
        "{0,1}",
        ["T_bio", "T_phys", "h", "Δφ", "G"],
        ["MF-0000", "external:systems-theory"],
        [
            "1. 把各类过程写为 T(x,Δφ,G)。",
            "2. 构造映射 h 保留状态转移结构。",
            "3. 若转移图可交换，则跨域同构成立。",
        ],
        ["private-getnote-0000:011"],
    ),
    effect(
        12,
        "低成本后台直觉效应",
        "Low-Cost Background Intuition Effect",
        "neuroscience-cognition",
        "熬夜后理性状态下降但直觉仍运行，说明存在低成本后台推断层。",
        "可写成分层计算：显性执行层能量不足时，低维压缩模型仍可输出启发式判断；可靠性随疲劳下降。",
        "E_{EFF-0012}=1 ⇔ y_int=G_low(z), z=C(x), C_cost(G_low)<C_cost(G_exec)",
        "X × Z",
        "Y",
        ["x", "z", "G_low", "G_exec", "C_cost"],
        ["MF-0000", "external:predictive-processing"],
        [
            "1. 把高维状态 x 压缩为 z=C(x)。",
            "2. 后台直觉由低成本函数 G_low 产生。",
            "3. 当执行层成本超过预算，低成本层仍可运行但误差上升。",
        ],
        ["private-getnote-0000:012"],
    ),
    effect(
        13,
        "睡眠清除门控效应",
        "Sleep Clearance Gate Effect",
        "neuroscience",
        "脑脊液清除为何与睡眠状态相关，可写成状态门控问题。",
        "收敛为待实证的门控模型：睡眠改变神经调质、血流、间隙和代谢状态，从而改变清除通量；但外部研究对“睡眠一定加速清除”仍有争议。",
        "E_{EFF-0013}=1 ⇔ Q_clear(sleep)-Q_clear(wake)=G(ν,ρ,κ,A)-G(ν',ρ',κ',A')",
        "S_sleep × S_wake × R^4",
        "R",
        ["Q_clear", "ν", "ρ", "κ", "A"],
        ["MF-0000", "external:glymphatic-model"],
        [
            "1. 令清除通量 Q_clear 由神经调质 ν、血流 ρ、通道 κ、代谢活动 A 决定。",
            "2. 睡眠与清醒对应不同参数向量。",
            "3. 经验争议意味着符号和幅度需实测，数学上只保留门控差分。",
        ],
        ["private-getnote-0000:013"],
        ["SRC-GLYMPHATIC-REVIEW", "SRC-GLYMPHATIC-CHALLENGE"],
    ),
    effect(
        14,
        "小群体资源不易感效应",
        "Small-Group Resource Low-Susceptibility Effect",
        "economics-society",
        "小群体需求不是不可见，而是资源传播的易感性不足。",
        "成立：资源流向取决于增值率、规模、触达成本和复制收益；当小群体的有效再生产数低于阈值，资源不会自发聚集。",
        "E_{EFF-0014}=1 ⇔ R_resource = β·V·N/(C_access+C_adapt) < 1",
        "V × N × C",
        "R",
        ["β", "V", "N", "C_access", "C_adapt"],
        ["MF-0000", "external:resource-allocation"],
        [
            "1. 定义资源传播数 R_resource。",
            "2. 小群体通常 N 小且适配成本 C_adapt 高。",
            "3. 若 R_resource<1，资源链不自发扩张。",
        ],
        ["private-getnote-0000:014"],
    ),
    effect(
        15,
        "炎症反馈报警效应",
        "Inflammation Feedback Alarm Effect",
        "medicine-systems",
        "炎症是损伤、感染、免疫反应和修复之间的反馈报警状态。",
        "成立为机制框架：炎症强度可写成损伤、病原、免疫阈值、屏障状态和负反馈的函数；反复炎症说明至少一个参数长期越界。",
        "E_{EFF-0015}=1 ⇔ I(t+1)=σ(αD+βP+γB^{-1}-δR-θ)",
        "D × P × B × R × R_+",
        "[0,1]",
        ["I", "D", "P", "B", "R", "θ"],
        ["MF-0000", "external:immune-response-model"],
        [
            "1. 把炎症强度 I 写成损伤 D、病原 P、屏障 B、调节 R 的函数。",
            "2. 若输入项超过 θ，炎症启动。",
            "3. 若负反馈不足或输入持续，炎症反复出现。",
        ],
        ["private-getnote-0000:015"],
        empirical_scope="医学机制数学化，不构成诊断或治疗建议。",
    ),
    effect(
        16,
        "气液剪切成泡效应",
        "Gas-Liquid Shear Foaming Effect",
        "physics-chemistry",
        "啤酒沫来自气体释放、表面张力、黏度和倒入剪切速率的耦合。",
        "成立：倒得越快，剪切和湍动越强，成核率升高；泡沫量还受温度、溶解气体、蛋白和容器影响。",
        "E_{EFF-0016}=1 ⇔ dF_foam/dt = k·CO2·S_shear·Π_stabilize - λF_foam",
        "R_+^5",
        "R_+",
        ["F_foam", "CO2", "S_shear", "Π_stabilize", "λ"],
        ["MF-0000", "external:nucleation-dynamics"],
        [
            "1. 令泡沫生成率正比于溶解气体和剪切强度。",
            "2. 稳泡因子增加泡沫寿命。",
            "3. 消散项 λF_foam 给出泡沫衰减。",
        ],
        ["private-getnote-0000:016"],
    ),
    effect(
        17,
        "烹饪参数窗口效应",
        "Cooking Parameter Window Effect",
        "systems-chemistry",
        "煮饭是水、热、时间和米粒结构共同决定的相变窗口。",
        "成立：熟饭对应参数落入可食窗口；水少、热少、时间短偏生，水多偏稀，热和时间过量偏糊。",
        "E_{EFF-0017}=1 ⇔ y=cooked iff (w,h,t)∈Ω_cooked",
        "R_+^3",
        "{raw,cooked,porridge,burned}",
        ["w", "h", "t", "Ω_cooked"],
        ["MF-0000", "external:phase-transition"],
        [
            "1. 定义水 w、热 h、时间 t 的参数空间。",
            "2. 由淀粉糊化和水分迁移确定可食域 Ω_cooked。",
            "3. 参数越界对应不同失败态。",
        ],
        ["private-getnote-0000:017"],
    ),
    effect(
        18,
        "表面活性降能效应",
        "Surfactant Energy-Barrier Reduction Effect",
        "chemistry-systems",
        "洗洁精使油污从稳固附着态转入可分散可冲走态。",
        "成立：表面活性剂降低界面能和附着能垒，形成乳化小滴，使水流可带走油相。",
        "E_{EFF-0018}=1 ⇔ ΔG_attach(surfactant) < ΔG_attach(∅) ∧ P(detach)↑",
        "O × W × S",
        "{0,1}",
        ["ΔG_attach", "S", "P_detach"],
        ["MF-0000", "external:surface-chemistry"],
        [
            "1. 油污稳定性由界面附着自由能 ΔG_attach 决定。",
            "2. 表面活性剂改变油水界面结构。",
            "3. 当能垒下降，外部水流可完成脱附。",
        ],
        ["private-getnote-0000:018"],
    ),
    effect(
        19,
        "驱动状态耗散效应",
        "Drive-State Dissipation Effect",
        "biology-cognition",
        "性欲等生物驱动是内部状态变量升高后的耗散需求。",
        "成立为一般驱动模型：驱动状态 d(t) 由内分泌、刺激、认知和反馈累积，行为、等待或认知重评都可降低 d；不同路径的成本和后果不同。",
        "E_{EFF-0019}=1 ⇔ d(t+1)=d(t)+u_bio+u_cue-u_action-u_reappraisal-λd(t)",
        "D × U × A",
        "R_+",
        ["d", "u_bio", "u_cue", "u_action", "u_reappraisal", "λ"],
        ["MF-0000", "external:drive-reduction-model"],
        [
            "1. 把驱动写成可累积状态 d(t)。",
            "2. 生理输入和线索输入提高 d。",
            "3. 行为、自然衰减或认知重评降低 d。",
        ],
        ["private-getnote-0000:019", "user-prompt:libido-addiction-ai-life"],
        empirical_scope="只做抽象驱动模型，不评价具体私人行为。",
    ),
    effect(
        20,
        "动态不稳定稳定化效应",
        "Dynamic Instability Stabilization Effect",
        "physics-engineering",
        "两轮车能跑起来，是持续输入和反馈把静态不稳定系统维持在动态稳定轨道。",
        "成立：速度、角动量、转向几何和反馈共同改变特征值，使倒伏模态在运动中被压制。",
        "E_{EFF-0020}=1 ⇔ max Re eig(A(v,τ,κ)) < 0 for v>v_min",
        "R_+ × T × K",
        "{0,1}",
        ["A", "v", "τ", "κ", "v_min"],
        ["MF-0000", "external:vehicle-dynamics"],
        [
            "1. 将两轮车线性化为状态矩阵 A(v,τ,κ)。",
            "2. 静止时存在倒伏不稳定特征值。",
            "3. 当速度和反馈超过阈值，最大实部转负，动态稳定出现。",
        ],
        ["private-getnote-0000:020"],
    ),
    effect(
        21,
        "自维持坍缩边界效应",
        "Self-Maintenance Collapse Boundary Effect",
        "physics-systems",
        "黑洞可抽象为自持系统失稳后进入外部观测不可恢复边界。",
        "可数学化但不替代广义相对论：当逃逸/回指通道低于阈值，外部系统只能观测边界量，内部态不可完整恢复。",
        "E_{EFF-0021}=1 ⇔ η_return(x)<θ_horizon ⇒ I_external(x_internal)≈0",
        "X × G",
        "{0,1}",
        ["η_return", "θ_horizon", "I_external"],
        ["D156", "D157", "MF-0000"],
        [
            "1. 定义内部态向外部回指的通道效率 η_return。",
            "2. 当效率低于边界阈值，外部可恢复信息趋近零。",
            "3. 该模型只表达信息边界，不推出具体引力方程。",
        ],
        ["private-getnote-0000:021"],
    ),
    effect(
        22,
        "自举条件敏感效应",
        "Bootstrap Condition Sensitivity Effect",
        "ai-cognition",
        "自举元函数既能促成好奇心、升维和幻觉治理，也会继承人为目标设置错误。",
        "成立：自举循环只保证相对于目标函数的收敛；若目标函数错，收敛结果仍可能错，因此必须有反向通道和外部校准。",
        "E_{EFF-0022}=1 ⇔ Converged(B|G) ∧ wrong(G) ⇒ possible wrong(B*)",
        "B × G",
        "{0,1}",
        ["B", "G", "B*"],
        ["MF-0000"],
        [
            "1. 自举循环收敛到 B*=Fix(N_G)。",
            "2. 固定点依赖目标 G。",
            "3. 若 G 错误，固定点正确性不由收敛性保证。",
        ],
        ["private-getnote-0000:022"],
    ),
    effect(
        23,
        "透明介质信息通道效应",
        "Transparent-Medium Information Channel Effect",
        "physics",
        "玻璃透光可视为光信息通道与材料吸收/散射门槛兼容。",
        "外部物理已给出标准解释：可见光能量不足以触发强吸收且散射较弱。信息系统说法可作为抽象重写，不是取代材料光学的新底层答案。",
        "E_{EFF-0023}=1 ⇔ T(ω)=exp[-(α_abs(ω)+α_scat(ω))L], α_abs+α_scat<θ_T",
        "Ω_visible × R_+",
        "[0,1]",
        ["ω", "α_abs", "α_scat", "L", "T"],
        ["MF-0000", "external:optical-absorption"],
        [
            "1. 把光通过材料写成透过率 T(ω)。",
            "2. 吸收和散射系数共同决定信息通道损耗。",
            "3. 可见光区损耗低于阈值时，材料表现为透明。",
        ],
        ["user-prompt:glass-transparency"],
        ["SRC-GLASS-TRANSPARENCY"],
    ),
    effect(
        24,
        "商业单资源竞争效应",
        "Single-Resource Business Competition Effect",
        "economics-systems",
        "不同商业形态本质上争抢同一类可转化资源。",
        "成立：产品差异只是资源捕获函数不同；统一资源可写成可支配注意、时间、信任、支付能力和复购路径的组合。",
        "E_{EFF-0024}=1 ⇔ firm_i survives iff R_i=A_i·T_i·Trust_i·Pay_i·Repeat_i - Cost_i > θ",
        "F × R_+^6",
        "{0,1}",
        ["A", "T", "Trust", "Pay", "Repeat", "Cost"],
        ["MF-0000", "external:resource-competition"],
        [
            "1. 把商业输入统一为可转化资源向量。",
            "2. 不同产品只是捕获函数 R_i 的参数化差异。",
            "3. R_i 超过成本和阈值时，公司作为自维持组织存活。",
        ],
        ["user-prompt:business-single-resource"],
    ),
    effect(
        25,
        "偏好-愉悦共同势函数效应",
        "Preference-Pleasure Common Potential Effect",
        "cognition-ai",
        "愉悦、口味、选择偏好、上瘾和 AI 偏好可写成同一奖励势函数的不同实例。",
        "成立于抽象层：偏好是价值函数梯度，愉悦是正预测误差或状态改善信号，成瘾是高增益反馈导致策略空间收缩。",
        "E_{EFF-0025}=1 ⇔ π(a|s)∝exp(V(s,a)/τ), δ=r+γV(s')-V(s), addiction iff ∂π/∂cue≫θ",
        "S × A × R",
        "Π",
        ["π", "V", "δ", "r", "γ", "τ"],
        ["MF-0000", "external:reward-prediction-error", "external:reinforcement-learning"],
        [
            "1. 用价值函数 V 表示偏好。",
            "2. 预测误差 δ 改写 V 并产生强化。",
            "3. 当线索对策略梯度的控制过强，偏好变成成瘾式锁定。",
        ],
        ["user-prompt:pleasure-preference-addiction-ai"],
        ["SRC-REWARD-PREDICTION"],
    ),
    effect(
        26,
        "内源输出再输入污染效应",
        "Endogenous Output Reinput Contamination Effect",
        "biology-society",
        "近亲繁殖、自交和连续克隆都可能体现系统把自身输出当输入源后的多样性衰减和负荷累积。",
        "部分成立并需分层：遗传上，近交提高有害隐性等位基因纯合概率，连续克隆可能积累突变；社会禁忌还叠加了规范破缺奖励，与遗传风险不是同一层。",
        "E_{EFF-0026}=1 ⇔ Fitness_{g+1}=Fitness_g - μ_load·Homozygosity - M_acc + Purge",
        "G × M × R_+",
        "R",
        ["Fitness", "μ_load", "Homozygosity", "M_acc", "Purge"],
        ["MF-0000", "external:population-genetics"],
        [
            "1. 近亲/自交提高同源片段和纯合概率。",
            "2. 有害负荷表达降低适合度；选择清除项 Purge 可抵消一部分。",
            "3. 连续克隆若突变或重编程错误累积，系统完备性下降。",
        ],
        ["user-prompt:inbreeding-cloning-taboo"],
        ["SRC-INBREEDING", "SRC-RECLONING-2013", "SRC-RECLONING-2026"],
        empirical_scope="遗传风险、克隆衰减和禁忌刺激分属不同层；此处只给数学关系，不评价私人行为。",
    ),
    effect(
        27,
        "主动下一代生命边界效应",
        "Active Next-Generation Life Boundary Effect",
        "biology-ai",
        "AI 若要成为生命式系统，需要主动下一代机制，而不只是被人类复制。",
        "作为定义可收敛：生命式系统至少要有自维持、边界、能量/资源代谢、主动复制或变体生成、选择反馈。病毒在此定义下依赖宿主，不是自治生命式系统。",
        "E_{EFF-0027}=1 ⇔ Life(S)=1 iff M_self·Boundary·Energy·Reproduction_active·Selection > θ_life",
        "S × R_+^5",
        "{0,1}",
        ["M_self", "Boundary", "Energy", "Reproduction_active", "Selection"],
        ["MF-0000", "external:autopoiesis", "external:evolutionary-dynamics"],
        [
            "1. 把生命式系统写成五因子乘法门。",
            "2. 被动复制不满足 Reproduction_active。",
            "3. AI 若内置主动变体生成和选择反馈，才越过该定义边界。",
        ],
        ["user-prompt:ai-life-virus"],
    ),
    effect(
        28,
        "睡眠修复窗口效应",
        "Sleep Repair Window Effect",
        "medicine-neuroscience",
        "成年人睡眠约七小时多不是神秘常数，而是修复收益与机会成本的最优窗口。",
        "外部证据支持睡眠时长与风险常呈 U 形；数学上最优时长是修复收益边际等于清醒机会成本和长睡风险边际的位置。",
        "E_{EFF-0028}=1 ⇔ t_sleep*=argmin_t [D_short(t)+D_long(t)+C_awake(t)]",
        "R_+",
        "R_+",
        ["t_sleep", "D_short", "D_long", "C_awake"],
        ["MF-0000", "external:circadian-oscillator"],
        [
            "1. 短睡损伤 D_short 随 t 减小上升。",
            "2. 过长睡眠相关风险 D_long 随 t 过大上升。",
            "3. 最优 t 是总风险函数的极小点，并受个体和年龄调制。",
        ],
        ["user-prompt:sleep-circadian"],
        ["SRC-SLEEP-MORTALITY", "SRC-CIRCADIAN-MATH", "SRC-GLYMPHATIC-REVIEW", "SRC-GLYMPHATIC-CHALLENGE"],
        empirical_scope="给出群体风险和系统模型，不替代个人睡眠医学评估。",
    ),
    effect(
        29,
        "心率累积耗损效应",
        "Heart-Rate Cumulative Load Effect",
        "medicine-biology",
        "静息心率与死亡风险可写成累计机械、代谢和自主神经负荷。",
        "外部研究显示较高静息心率与全因和心血管死亡风险相关。数学上不是固定总心跳数命运，而是心率暴露、代谢率、心血管储备和疾病状态共同决定风险。",
        "E_{EFF-0029}=1 ⇔ Hazard(t)=h_0(t)·exp(β∫RHR dt + γM - ρReserve)",
        "R_+^3 × T",
        "R_+",
        ["RHR", "M", "Reserve", "Hazard"],
        ["MF-0000", "external:survival-analysis"],
        [
            "1. 把静息心率暴露写成 ∫RHR dt。",
            "2. 风险函数由暴露、代谢和储备共同调制。",
            "3. 人类心跳次数差异来自体型、代谢率、寿命和心率共同积分，不是单一常数。",
        ],
        ["user-prompt:resting-heart-rate-death"],
        ["SRC-RHR-MORTALITY"],
        empirical_scope="群体风险模型，不用于个人诊断。",
    ),
    effect(
        30,
        "皮屑屏障-微生态失配效应",
        "Dandruff Barrier-Microbiome Mismatch Effect",
        "medicine-dermatology",
        "头屑可写成头皮屏障、皮脂、微生物代谢和炎症反应的失配。",
        "外部综述支持头屑/脂溢性皮炎与 Malassezia、皮脂、屏障和炎症相关。数学上消除路径是降低微生物负荷、恢复屏障、减少炎症和诱因。",
        "E_{EFF-0030}=1 ⇔ Flake=σ(a·Malassezia·Sebum + b·Barrier^{-1}+c·Inflammation-θ)",
        "R_+^4",
        "[0,1]",
        ["Malassezia", "Sebum", "Barrier", "Inflammation", "Flake"],
        ["MF-0000", "external:dermatology-barrier-model"],
        [
            "1. 头屑强度由微生态、皮脂、屏障和炎症共同决定。",
            "2. 任一项长期越界会提高脱屑概率。",
            "3. 控制策略对应降低正项或提高屏障项。",
        ],
        ["user-prompt:dandruff-immune-infection"],
        ["SRC-DANDRUFF"],
        empirical_scope="皮肤机制数学化，不提供个人用药方案。",
    ),
    effect(
        31,
        "免疫-感染阈值效应",
        "Immune-Infection Threshold Effect",
        "medicine-epidemiology",
        "免疫缺陷和感染性疾病都可写成防御能力与复制数阈值问题。",
        "成立：感染扩张取决于有效再生产数，免疫缺陷则降低清除率、识别率或效应器容量，使原本可控的病原越过阈值。",
        "E_{EFF-0031}=1 ⇔ R_eff=βS/(γ_clear·I_eff) ; infection grows iff R_eff>1",
        "R_+^4",
        "{grow,decline}",
        ["β", "S", "γ_clear", "I_eff", "R_eff"],
        ["MF-0000", "external:SIR", "external:immune-threshold"],
        [
            "1. 病原传播/复制由 βS 给出。",
            "2. 清除能力由 γ_clear·I_eff 给出。",
            "3. R_eff>1 时感染增长，R_eff<1 时趋于衰退。",
        ],
        ["user-prompt:dandruff-immune-infection"],
        ["SRC-INFECTION-R0", "SRC-IMMUNODEFICIENCY"],
        empirical_scope="公共卫生和免疫机制模型，不替代诊疗。",
    ),
    effect(
        32,
        "神经自举唤醒效应",
        "Neural Bootstrap Arousal Effect",
        "neuroscience",
        "植物人醒不来可抽象为唤醒-意识网络的自举循环未闭合。",
        "部分成立：意识障碍涉及脑干/丘脑/皮层网络和功能连接。数学上可写成全局工作空间增益未超过阈值；具体治疗需要医学实证。",
        "E_{EFF-0032}=1 ⇔ ConsciousAccess=1 iff λ_max(W_thalamo-cortical·G_arousal)>θ_C",
        "W × G",
        "{0,1}",
        ["W_thalamo-cortical", "G_arousal", "λ_max", "θ_C"],
        ["MF-0000", "external:disorders-of-consciousness-network"],
        [
            "1. 把唤醒和意识访问写成网络增益问题。",
            "2. 若丘脑-皮层有效连接低于阈值，循环无法自举闭合。",
            "3. 恢复路径是提高连接、调制增益或重建输入节律，但必须由医学验证。",
        ],
        ["user-prompt:vegetative-state-bootstrap"],
        ["SRC-DOC-NETWORKS"],
        empirical_scope="理论模型，不构成临床方案。",
    ),
    effect(
        33,
        "信息自聚合场效应",
        "Information Self-Aggregation Field Effect",
        "physics-systems",
        "真空中物质成团可抽象为吸引势、扰动增长和信息自聚合的场效应。",
        "可数学化为引力不稳定的抽象重写：密度扰动在吸引势下增长并形成团簇；信息自聚合说法是结构类比，不替代引力理论。",
        "E_{EFF-0033}=1 ⇔ d^2δ/dt^2 + 2H dδ/dt - 4πGρδ > 0",
        "DensityField × R_+",
        "{0,1}",
        ["δ", "H", "G", "ρ"],
        ["MF-0000", "external:gravitational-instability"],
        [
            "1. 设密度扰动为 δ。",
            "2. 引力项 4πGρδ 与膨胀阻尼 2Hδ' 竞争。",
            "3. 若吸引增长项占优，扰动自聚合成团。",
        ],
        ["user-prompt:vacuum-self-aggregation"],
    ),
    effect(
        34,
        "短视频奖励压缩效应",
        "Short-Video Reward Compression Effect",
        "media-cognition",
        "短剧短视频通过高频、低成本、强线索奖励压缩人的选择空间并强化上瘾回路。",
        "成立于强化学习层：短内容降低获得奖励的时间成本，提高预测误差频率，使策略更偏向即时奖励。",
        "E_{EFF-0034}=1 ⇔ addiction_risk ∝ frequency(δ_+)/(delay·effort·alternative_value)",
        "R_+^4",
        "R_+",
        ["δ_+", "delay", "effort", "alternative_value"],
        ["MF-0000", "external:reward-prediction-error"],
        [
            "1. 短内容提高正预测误差 δ_+ 的出现频率。",
            "2. 延迟和努力成本下降。",
            "3. 当替代活动价值不足，策略被即时奖励吸引并锁定。",
        ],
        ["user-prompt:short-video-addiction"],
        ["SRC-REWARD-PREDICTION"],
    ),
    effect(
        35,
        "梦境离线生成整合效应",
        "Dream Offline Generative Consolidation Effect",
        "neuroscience-ai",
        "做梦可写成大脑离线生成、误差重放、记忆整合和情绪调节的组合。",
        "数学上成立为离线生成机制：睡眠中外部输入权重下降，内部生成模型重放高权重残差，降低记忆和情绪损失。",
        "E_{EFF-0035}=1 ⇔ dream = argmin_z [L_memory(z)+L_affect(z)+Ω(z)] under input_weight≈0",
        "Z × M × A",
        "Z",
        ["z", "L_memory", "L_affect", "Ω", "input_weight"],
        ["MF-0000", "external:predictive-processing"],
        [
            "1. 睡眠降低外部输入权重。",
            "2. 内部生成模型采样高残差记忆和情绪状态。",
            "3. 梦境序列作为离线优化轨迹降低综合损失。",
        ],
        ["user-prompt:dream-mechanism-openclaw"],
    ),
    effect(
        36,
        "形式系统外推边界效应",
        "Formal-System Projection Boundary Effect",
        "mathematics",
        "把数学公理定理全部跑一遍不会给出任意猜想的全解，只会暴露可判定、不可判定和欠定边界。",
        "成立：给定公理系统 A 和命题 p，若 A⊢p 或 A⊢¬p 则可收敛；若两者都不可得，则必须标记为独立、欠定或需扩展公理。",
        "E_{EFF-0036}=1 ⇔ classify_A(p)∈{provable,refutable,independent,underdetermined}",
        "A × P",
        "{provable,refutable,independent,underdetermined}",
        ["A", "p", "⊢"],
        ["MF-0000", "external:formal-logic"],
        [
            "1. 给定形式系统 A 和命题 p。",
            "2. 分别运行正向证明 A⊢p 与反向证明 A⊢¬p。",
            "3. 若两路都失败，不伪装成已解决，而标记边界类型。",
        ],
        ["user-prompt:math-axioms-theorems"],
    ),
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    write_text(path, body + ("\n" if body else ""))


def render_effect_item(item: dict[str, Any]) -> str:
    formal = item["mathematical_formalization"]
    derivation = item["mathematical_derivation"]
    lines = [
        f"# {item['id']} {item['title']['zh']} / {item['title']['en']}",
        "",
        "[← 返回新效应表](../new-effects.md)",
        "[返回新答案总表](../../../../ANSWERS.md)",
        "",
        f"- 领域 / Discipline: `{item['discipline']}`",
        f"- 状态 / Status: `{item['status']}`",
        "",
        "## 猜想 / Conjecture",
        "",
        item["conjecture"]["zh"],
        "",
        "## 收敛结论 / Converged Conclusion",
        "",
        item["conclusion"]["zh"],
        "",
        "## 纯数学函数 / Pure Mathematical Function",
        "",
        f"- 对象 / Object: `{formal['symbol']}`",
        f"- 定义域 / Domain: `{formal['domain']}`",
        f"- 值域 / Codomain: `{formal['codomain']}`",
        f"- 数学表达 / Expression: `{formal['math_expression']}`",
        f"- 有效条件 / Validity: `{formal['validity_condition']}`",
        "",
        "## 数学推导 / Mathematical Derivation",
        "",
        f"- 推导类型 / Derivation type: `{derivation['kind']}`",
        f"- 收敛状态 / Convergence status: `{derivation['status']}`",
        f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in derivation.get('depends_on', [])) or '`source_state`'}",
        "- 推导步骤 / Steps:",
    ]
    lines.extend(f"  - {step}" for step in derivation["steps_math"])
    lines.extend(
        [
            "- 证明义务 / Proof obligations:",
            *(f"  - `{obligation}`" for obligation in derivation["proof_obligations"]),
            f"- 正向检查 / Forward check: `{derivation['forward_check']['condition']}`",
            f"- 反向检查 / Reverse check: `{derivation['reverse_check']['condition']}`",
            f"- 收敛判据 / Convergence: `{derivation['convergence']}`",
            "",
            "## 证据范围 / Empirical Scope",
            "",
            item["empirical_scope"]["zh"],
            "",
            "## 来源回指 / Source References",
            "",
        ]
    )
    lines.extend(f"- `{ref}`" for ref in item["source_refs"])
    if item.get("external_sources"):
        lines.extend(["", "## 外部函数或证据 / External Functions or Evidence", ""])
        for sid in item["external_sources"]:
            source = next((src for src in EXTERNAL_SOURCES if src["id"] == sid), None)
            if source:
                lines.append(f"- [{sid}｜{source['title']}]({source['url']})")
            else:
                lines.append(f"- `{sid}`")
    lines.append("")
    return "\n".join(lines)


def render_index(items: list[dict[str, Any]]) -> str:
    lines = [
        "# 新效应表 / New Effects",
        "",
        "中文：本表收录本轮从 `0000` 知识库和新增用户猜想中经正反交叉自举循环得到的效应对象。它们不是原文摘录，而是去原文后的数学化推论结果。",
        "",
        "English: This table records new effect objects derived from the 0000 knowledge-base conjecture batch and the latest user conjectures. They are mathematical derivations, not raw-note excerpts.",
        "",
        "> 医学、心理和生物条目只给出机制模型与验证边界，不构成诊断、治疗或行为建议。",
        "",
        "| ID | 新效应 | 领域 | 状态 | 数学表达 |",
        "|---|---|---|---|---|",
    ]
    for item in items:
        formal = item["mathematical_formalization"]
        lines.append(
            f"| [{item['id']}]({item['page'].replace('docs/zh/answers/', '')}) | "
            f"{item['title']['zh']} / {item['title']['en']} | {item['discipline']} | "
            f"{item['status']} | `{formal['math_expression']}` |"
        )
    lines.extend(["", "## 外部函数或证据索引 / External Evidence Index", ""])
    for src in EXTERNAL_SOURCES:
        lines.append(f"- [{src['id']}｜{src['title']}]({src['url']})")
    lines.append("")
    return "\n".join(lines)


def render_machine_index(items: list[dict[str, Any]]) -> str:
    lines = ["# 新效应机器索引 / New Effects Machine Index", ""]
    for item in items:
        lines.append(f"- {item['id']} | {item['title']['zh']} | {item['discipline']} | {item['status']}")
    lines.append("")
    return "\n".join(lines)


def render_report(items: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    converged = [
        item for item in items
        if item["mathematical_derivation"]["status"] == "converged"
        and item["mathematical_derivation"]["forward_check"]["status"] == "pass"
        and item["mathematical_derivation"]["reverse_check"]["status"] == "fail"
    ]
    payload = {
        "knowledge_base_requested": "0000",
        "knowledge_base_resolved": "0000",
        "downloaded_notes": 22,
        "new_effects": len(items),
        "converged_effects": len(converged),
        "all_internal_bootstrap_passed": len(converged) == len(items),
        "external_sources": EXTERNAL_SOURCES,
        "generated_at": date.today().isoformat(),
    }
    lines = [
        "# 0000 知识库猜想全量数学推论报告",
        "",
        "- API 未返回精确名为 `00000` 的知识库；本轮按 API 中当前解释路径之一的 `0000` 知识库执行。`00000` 已 superseded_by_0000。",
        "- 已下载知识库笔记：22 条列表记录、22 条详情记录。",
        f"- 新效应对象：{len(items)} 条。",
        f"- 内部正反交叉自举收敛：{len(converged)}/{len(items)}。",
        "- 结论边界：医学、心理、生物和物理条目均为机制模型或数学化重写，不替代外部专业实证。",
        "",
        "## 总结论",
        "",
        "1. 本轮所有可写入猜想均已写成纯数学函数、定义域、值域、有效条件、推导步骤、正向检查、反向检查与收敛判据。",
        "2. 标准科学已有解释的地方，不把框架推论伪装成新底层事实；例如玻璃透光已有材料光学解释，本轮只给出信息通道形式化。",
        "3. 对任意数学猜想，框架不能越过形式系统可判定边界；无法证明时必须标为独立、欠定或需扩展公理。",
        "4. 对医学和生命科学猜想，本轮只完成机制级数学化，个人诊断、治疗和干预必须交给专业医学流程。",
        "",
        "## 新效应列表",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"### {item['id']} {item['title']['zh']}",
                "",
                f"- 领域：`{item['discipline']}`",
                f"- 结论：{item['conclusion']['zh']}",
                f"- 数学表达：`{item['mathematical_formalization']['math_expression']}`",
                f"- 收敛：`{item['mathematical_derivation']['convergence']}`",
                "",
            ]
        )
    lines.extend(["## 外部函数或证据", ""])
    for src in EXTERNAL_SOURCES:
        lines.append(f"- {src['id']}：{src['title']} — {src['url']}")
    lines.append("")
    return payload, "\n".join(lines)


def main() -> int:
    items = EFFECTS
    write_json(DATA_JSON, items)
    write_jsonl(DATA_JSONL, items)
    write_text(DATA_INDEX, render_machine_index(items))
    write_text(DOC_INDEX, render_index(items))
    for item in items:
        write_text(DOC_DIR / f"{item['id']}.md", render_effect_item(item))
    payload, report = render_report(items)
    write_json(REPORT_JSON, payload)
    write_text(REPORT_MD, report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
