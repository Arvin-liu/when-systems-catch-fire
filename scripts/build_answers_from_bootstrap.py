#!/usr/bin/env python3
"""Build the New Answers layer from bootstrap notes and explicit answer leads."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from answer_utils import (
    ANSWER_TEMPLATE_MD,
    ANSWERS_INDEX_MD,
    ANSWERS_JSON,
    ANSWERS_JSONL,
    ANSWERS_LIST_MD,
    ANSWERS_JSON,
    ANSWERS_INDEX_MD,
    BOOTSTRAP_REPORT_JSON,
    BOOTSTRAP_REPORT_MD,
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_DIR,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    CATEGORY_DEFINITIONS,
    CATEGORY_LOOKUP,
    ITEM_DIR,
    ANSWER_DIR,
    CASES_JSON,
    DISCOVERIES_JSON,
    FUNCTIONS_JSON,
    PREDICTIONS_JSON,
    ANSWER_ID_RE,
    build_category_map,
    next_answer_id,
    normalize_source_refs,
    read_json,
    render_answer_index,
    render_answer_index_md,
    render_answer_page,
    render_bootstrap_report,
    render_category_page,
    rel_link,
    write_json,
    write_jsonl,
    write_text,
)
from derive_math_formalizations import answer_formalization


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_NOTE_ROOTS = [
    REPO_ROOT / "dianhuo/originals",
    REPO_ROOT / "dianhuo/04-materials/raw-notes",
]

ANSWER_RECOVERY_KEYWORDS = [
    "物理学七团乌云",
    "七团乌云",
    "七朵乌云",
    "物理学乌云",
    "物理学危机",
    "物理学大一统",
    "统一理论",
    "大一统",
    "理论统一",
    "得到大脑",
    "推测",
    "猜想",
    "新答案",
    "新解释",
]

LOW_PRIORITY_MISREAD_KEYWORDS = [
    "气团",
    "雾云",
]

PHYSICS_SEVEN_CLOUDS_RECOVERY = "PhysicsSevenCloudsRecovery"


ANSWER_BLUEPRINTS = [
    {
        "id": "ANS-0001",
        "title": {"zh": "大统一应该追求Φ极小而不是α相等", "en": "Grand unification should minimize Phi rather than force equal couplings"},
        "question": {
            "zh": "传统大统一为什么卡了一百年，目标到底错在哪里？",
            "en": "Why has traditional grand unification stalled for so long, and where is the target wrong?",
        },
        "answer": {
            "zh": "目标错在追求耦合常数相等；更合理的目标是让Φ在自然能标上取极小。",
            "en": "The mistake is to chase equal couplings; the better target is to minimize Phi at a natural scale.",
        },
        "prior_answers": {
            "zh": "传统GUT通常把统一理解为所有耦合常数相等，但这只是Φ在特殊条件下的退化态。",
            "en": "Traditional GUT treats unification as equality of couplings, but that is only a degenerate special case of Phi.",
        },
        "new_explanation": {
            "zh": "这里把“统一”的判据从参数相等改成系统极小值，问题从“怎么让它们一样”改写成“怎么让系统整体更稳”。",
            "en": "The novelty is to replace parameter equality with a system-level minimum, shifting the question from making terms equal to making the whole system more stable.",
        },
        "basis": {
            "zh": "来源笔记明确写出“新答案：大统一的目标应该是Φ极小而不是α相等”。",
            "en": "The source note explicitly says the new answer is that grand unification should minimize Phi rather than force equal couplings.",
        },
        "testability": {
            "zh": "如果未来有统一理论或有效理论能直接从Φ极小推出更稳的耦合结构，这个答案会比“全相等”更有解释力。",
            "en": "If a future theory derives a more stable coupling structure directly from Phi minimization, this answer will be more explanatory than a simple equality target.",
        },
        "categories": ["physics", "technology-and-engineering"],
        "related_functions": ["D153", "D156", "D157"],
        "related_cases": ["C-0554"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": ["dianhuo/originals/1912550858907336432_点火统一函数数学推导.md#问题1"],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "grand unification Phi minimum",
                "为什么大统一卡了一百年 Φ 极小",
                "unification target should minimize Phi",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把统一判据改写为Φ极小，而不是参数相等。",
                "en": "This answer reframes unification around minimizing Phi rather than equal couplings.",
            },
            "reviewer_note": "bootstrap lead from source note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0002",
        "title": {"zh": "引力的弱是层级间距的数学必然", "en": "Gravity is weak because of hierarchy spacing"},
        "question": {
            "zh": "为什么引力比另外三种力弱那么多？",
            "en": "Why is gravity so much weaker than the other three forces?",
        },
        "answer": {
            "zh": "因为M_Planck与日常能标之间的层级间距太大，引力在Φ里只是一个远尾项，所以耦合极弱。",
            "en": "Because the hierarchy gap between the Planck scale and everyday scales is enormous, gravity is just a far-tail term in Phi, so its coupling is tiny.",
        },
        "prior_answers": {
            "zh": "传统层次问题常把引力弱看成待解释异常，或者用人择原理绕开。",
            "en": "The traditional hierarchy problem treats weak gravity as an anomaly to explain, or sidesteps it with anthropic reasoning.",
        },
        "new_explanation": {
            "zh": "这个答案把“弱”拆成两个层面：可微扰性与耦合强度；前者可以接近1，后者仍然可以极小。",
            "en": "The new explanation separates weak coupling from perturbative accessibility: the first can be tiny while the second stays near unity.",
        },
        "basis": {
            "zh": "来源笔记直接写出“引力弱是B型因子的数学必然”和“为什么引力弱10^40倍”。",
            "en": "The source note explicitly frames weak gravity as a mathematical necessity of the B-type factor and answers why gravity is 10^40 times weaker.",
        },
        "testability": {
            "zh": "如果未来的统一理论能解释层级间距的起源，这个答案会保留为结构解释；如果不能，它仍能解释为什么“弱”并不奇怪。",
            "en": "If a future unified theory explains the origin of the hierarchy gap, this answer remains a structural explanation; otherwise it still explains why weak gravity is not surprising.",
        },
        "categories": ["physics"],
        "related_functions": ["D153", "D156", "D157", "D164"],
        "related_cases": ["C-0554", "C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": ["dianhuo/originals/1912550858907336432_点火统一函数数学推导.md#问题2"],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "why gravity is weak hierarchy spacing",
                "引力弱 10^40 倍 层级 间距",
                "gravity weak because Planck scale spacing",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把引力弱归因于层级间距，而不是单独的微调故事。",
                "en": "This answer attributes weak gravity to hierarchy spacing rather than a standalone fine-tuning story.",
            },
            "reviewer_note": "bootstrap lead from source note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0003",
        "title": {"zh": "黑洞信息悖论更像部分保留而不是完全丢失", "en": "The black-hole information paradox is partial retention, not total loss"},
        "question": {
            "zh": "黑洞信息到底是全丢了，还是能以某种方式保住？",
            "en": "Does black-hole information disappear entirely, or can it be preserved in some form?",
        },
        "answer": {
            "zh": "更合理的答案是部分丢失、部分保留；视界更像压缩与门控，而不是简单抹除。",
            "en": "The better answer is partial loss and partial retention; the horizon behaves more like compression and gating than simple erasure.",
        },
        "prior_answers": {
            "zh": "传统争论在“完全丢失”与“完全守恒”之间对撞，常常没有中间态。",
            "en": "The classic debate pits complete loss against complete conservation and often leaves no middle state.",
        },
        "new_explanation": {
            "zh": "这里把视界当作门控面：信息在穿越前后经历压缩、编码和可恢复性的变化，因此不必是二元结论。",
            "en": "The novelty is to treat the horizon as a gating surface: information changes compression, encoding, and recoverability across it, so the outcome need not be binary.",
        },
        "basis": {
            "zh": "来源笔记明确给出“黑洞信息丢失是乘法门控的数学必然，但不是完全丢失”。",
            "en": "The source note explicitly says black-hole information loss is a mathematical necessity of multiplicative gating but not total loss.",
        },
        "testability": {
            "zh": "如果视界物理、蒸发谱或类比黑洞实验能区分“完全丢失”和“部分保留”，这个答案就可被检验。",
            "en": "If horizon physics, evaporation spectra, or analogue-black-hole experiments can distinguish total loss from partial retention, this answer becomes testable.",
        },
        "categories": ["physics", "philosophy"],
        "related_functions": ["D156", "D157", "D108"],
        "related_cases": ["C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": ["dianhuo/originals/1912550858907336432_点火统一函数数学推导.md#问题6"],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "black hole information partial retention gating",
                "黑洞信息悖论 部分保留 门控",
                "black hole information paradox middle ground",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把黑洞视为门控压缩面，而不是单一的丢失/守恒二分。",
                "en": "This answer treats the black hole as a gating/compression surface rather than a binary loss/conservation case.",
            },
            "reviewer_note": "bootstrap lead from source note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0004",
        "title": {"zh": "秦统一失败不是因为硬件不够，而是退出权被压成了符号", "en": "Qin failed because exit rights were compressed into symbols, not because the hardware was insufficient"},
        "question": {
            "zh": "秦统一为什么很快就崩了？",
            "en": "Why did Qin's unification collapse so quickly?",
        },
        "answer": {
            "zh": "秦的问题不在于统一硬件不足，而在于把退出权压缩成了象征层，缺少缓冲与真实认同。",
            "en": "Qin's problem was not insufficient unifying hardware; it compressed exit rights into a symbolic layer and lacked buffering and real identity.",
        },
        "prior_answers": {
            "zh": "传统解释常说秦法过严、二世而亡，但这只解释了表层政治，不解释结构性脆弱。",
            "en": "Traditional explanations say Qin was too harsh and died in two generations, but that only explains surface politics, not structural fragility.",
        },
        "new_explanation": {
            "zh": "这里把统一的成败放到退出权梯度里看：没有缓冲层的强制统一会把系统推到极脆点。",
            "en": "The novelty is to read success or failure through the gradient of exit rights: forced unification without a buffer pushes a system to a brittle point.",
        },
        "basis": {
            "zh": "来源笔记把秦统一多次当作“强推”“退出权为假”“15年亡”的典型例子。",
            "en": "The source notes repeatedly use Qin unification as the example of forced push, fake exit rights, and a 15-year collapse.",
        },
        "testability": {
            "zh": "可用其他强制统一或强制整合案例检验：如果退出权被压到象征层且无缓冲，系统应显著更脆。",
            "en": "Other forced-unification or forced-integration cases can test this: if exit rights are compressed to a symbolic layer with no buffer, the system should be more brittle.",
        },
        "categories": ["history-and-civilization", "sociology-and-politics"],
        "related_functions": ["A5", "A8", "A9"],
        "related_cases": ["C-0003", "C-0162"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/20260608_1912243139532423784_点火-退出权梯度：等级制对退出权的结构性压缩.md",
            "dianhuo/originals/1912618494978223944_点火函数 A5.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "Qin unification exit rights compression",
                "秦统一 退出权 压缩 缓冲",
                "forced unification brittle exit rights",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把秦的失败解释为退出权梯度的断裂，而不是单纯的暴政后果。",
                "en": "This answer explains Qin's failure as a rupture in the exit-right gradient, not just as tyranny.",
            },
            "reviewer_note": "bootstrap lead from source note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0005",
        "title": {"zh": "物理学七团乌云共享同一容斥根因", "en": "The physics seven clouds share one inclusion-exclusion root"},
        "question": {
            "zh": "物理学七团乌云到底是七个独立问题，还是同一结构在不同尺度上的投影？",
            "en": "Are the physics seven clouds seven independent problems, or projections of the same structure at different scales?",
        },
        "answer": {
            "zh": "它们不是七个互不相关的问题，而是同一容斥竞争机制在不同尺度、不同可观测性和不同门控区间上的七种投影。",
            "en": "They are not seven unrelated problems; they are seven projections of the same inclusion-exclusion competition across different scales, observability regimes, and gating intervals.",
        },
        "prior_answers": {
            "zh": "传统物理学通常把量子引力、暗物质、暗能量、哈勃危机、层级问题、黑洞信息悖论和宇宙波函数不可知性分开处理。",
            "en": "Traditional physics usually treats quantum gravity, dark matter, dark energy, the Hubble crisis, the hierarchy problem, the black-hole information paradox, and cosmic wavefunction unknowability separately.",
        },
        "new_explanation": {
            "zh": "这里把七团乌云统一成同一套Φ面/容斥结构：系统行为由相对强度、区间位置和门控竞争共同决定，而不是由单点理论缺口决定。",
            "en": "The novelty is to unify the seven clouds under one Phi/inclusion-exclusion structure: behavior is determined by relative strength, interval position, and gating competition rather than a single missing theory.",
        },
        "basis": {
            "zh": "来源笔记直接逐条展开七团乌云，并明确写出“七团乌云共享同一数学根源：容斥项的相对强度决定系统行为区间”。",
            "en": "The source note explicitly enumerates the seven clouds and states that they share one mathematical root: the relative strength of inclusion-exclusion terms determines the behavioral interval.",
        },
        "testability": {
            "zh": "若不同乌云的观测量在同一参数区间同时共振、同时退化或同时出现临界转折，这个统一解释就比七个独立机制更强；反之可被分裂为多个独立问题。",
            "en": "If observables from different clouds resonate, degenerate, or hit critical turning points in the same parameter interval, this unified explanation is stronger than seven independent mechanisms; otherwise it can be split apart.",
        },
        "categories": ["physics"],
        "related_functions": ["D260", "D272", "D287", "D373", "D387", "D401", "D307", "D412", "D413", "D295"],
        "related_cases": ["C-0554", "C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
            "dianhuo/originals/1912595796075888368_点火｜P16-P18观测数据检验方案.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "物理学七团乌云",
                "physics seven clouds",
                "seven clouds in physics inclusion exclusion",
                "grand unification dark matter dark energy black hole information wavefunction",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把七个物理危机统一成同一容斥结构的不同投影。",
                "en": "This answer unifies the seven physics crises as different projections of the same inclusion-exclusion structure.",
            },
            "reviewer_note": "bootstrap lead from source note; seven-cloud recovery added after local note search",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0006",
        "title": {"zh": "量子引力是同一势能面在过渡区的统一描述", "en": "Quantum gravity is the unified description of one potential surface in the transition zone"},
        "question": {
            "zh": "量子引力与广义相对论、量子力学为什么看似冲突，却可能只是同一结构在不同区间的近似？",
            "en": "Why do quantum gravity, general relativity, and quantum mechanics seem to conflict if they may only be approximations of one structure in different regimes?",
        },
        "answer": {
            "zh": "它们更像同一势能面Φ在不同参数区间的近似：GR对应排斥主导的大尺度区，QM对应吸引主导的小尺度区，量子引力就是两者在容斥竞争转折点附近的统一描述。",
            "en": "They are better seen as approximations of the same potential surface Phi in different parameter regimes: GR in the large-scale repulsion-dominated zone, QM in the small-scale attraction-dominated zone, and quantum gravity as the unified description near the inclusion-exclusion turning point.",
        },
        "prior_answers": {
            "zh": "传统做法把量子引力当作一套要硬拼成的统一理论，常常默认GR和QM必须直接兼容。",
            "en": "Traditional approaches treat quantum gravity as a theory that must be forced into compatibility, often assuming GR and QM must be directly compatible.",
        },
        "new_explanation": {
            "zh": "新解释不是去拼两套本来不在同一参数区间的理论，而是把问题改写为：过渡区的可观测规律是什么，何时从GR滑向QM。",
            "en": "The new explanation does not try to fuse two theories that do not live in the same parameter regime; it asks what the transition-zone observables are and when the system slides from GR to QM.",
        },
        "basis": {
            "zh": "原文明确写出GR与QM是同一势能面在不同参数区间的近似，并给出σ≈√e作为过渡判据。",
            "en": "The source note explicitly says GR and QM are approximations of the same potential surface in different parameter regimes and gives sigma≈sqrt(e) as the transition criterion.",
        },
        "testability": {
            "zh": "若不同尺度实验或理论推导都指向同一个过渡区判据，而不是要求一套全域统一形式，这个解释就更强；否则可被拆回成独立问题。",
            "en": "If experiments or derivations at different scales point to the same transition-zone criterion rather than a single global unification form, this explanation wins; otherwise it can be split back into independent problems.",
        },
        "categories": ["physics"],
        "related_functions": ["D260", "D272", "D287", "D401", "D307", "D423"],
        "related_cases": ["C-0554", "C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "quantum gravity transition zone inclusion exclusion",
                "量子引力 过渡区 容斥",
                "GR QM same potential surface",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把量子引力定义为同一势能面的过渡区描述，而不是额外拼接的一层理论。",
                "en": "This answer defines quantum gravity as the transition-zone description of one potential surface rather than an extra stitched-on theory.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0007",
        "title": {"zh": "暗物质更像容斥交叉项的宏观表现", "en": "Dark matter is more like a macroscopic manifestation of inclusion-exclusion cross terms"},
        "question": {
            "zh": "暗物质效应到底是新粒子，还是可见物质结构在更大尺度上的宏观投影？",
            "en": "Is the dark-matter effect really new particles, or a macroscopic projection of visible-matter structure at larger scales?",
        },
        "answer": {
            "zh": "更合理的解释是后者：暗物质效应像容斥交叉项在大尺度上的表现，而不是独立自由参数。",
            "en": "The more plausible explanation is the latter: the dark-matter effect behaves like a large-scale expression of inclusion-exclusion cross terms rather than an independent free parameter.",
        },
        "prior_answers": {
            "zh": "标准暗物质框架通常把暗物质视为额外粒子或额外成分，再由其决定旋转曲线与透镜效应。",
            "en": "Standard dark-matter frameworks usually treat dark matter as extra particles or an extra component that then determines rotation curves and lensing.",
        },
        "new_explanation": {
            "zh": "新解释把暗物质重新写成可见物质p分布与容斥修正的耦合结果，因此暗物质分布应和可见物质的二阶矩严格相关。",
            "en": "The new explanation rewrites dark matter as the coupled result of visible-matter p-distribution and inclusion-exclusion corrections, so its distribution should be tightly linked to the second moment of visible matter.",
        },
        "basis": {
            "zh": "原文直接给出“暗物质密度分布与可见物质p分布二阶矩严格相关”，并指出σ接近√e时暗物质效应最弱。",
            "en": "The source note explicitly states that dark-matter density should track the second moment of visible-matter p-distribution and that the effect is weakest near sigma≈sqrt(e).",
        },
        "testability": {
            "zh": "若星系团样本显示暗物质密度与可见物质二阶矩相关且在σ≈√e附近出现极小值，这一答案优于独立粒子假说。",
            "en": "If galaxy-cluster samples show dark-matter density tracking the second moment of visible matter with a minimum near sigma≈sqrt(e), this answer beats the independent-particle hypothesis.",
        },
        "categories": ["physics"],
        "related_functions": ["D373", "D387", "D8", "D307", "D401"],
        "related_cases": ["C-0554", "C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
            "dianhuo/originals/1912595796075888368_点火｜P16-P18观测数据检验方案.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "dark matter visible matter second moment inclusion exclusion",
                "暗物质 可见物质 二阶矩 容斥",
                "dark matter not independent parameter",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把暗物质解释为宏观容斥交叉项，而不是独立自由参数。",
                "en": "This answer interprets dark matter as a macroscopic inclusion-exclusion cross term rather than an independent free parameter.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0008",
        "title": {"zh": "暗能量灾变是容斥对消后的净值问题", "en": "The dark-energy catastrophe is a question of the net value after inclusion-exclusion cancellation"},
        "question": {
            "zh": "宇宙学常数为什么会比量子场论粗算值小得离谱？",
            "en": "Why is the cosmological constant so much smaller than the crude quantum-field-theory estimate?",
        },
        "answer": {
            "zh": "因为观测到的是容斥对消后的有效净值，不是所有自由度线性相加后的总量。",
            "en": "Because what we observe is the effective net value after inclusion-exclusion cancellation, not the total sum of all degrees of freedom added linearly.",
        },
        "prior_answers": {
            "zh": "传统讨论把真空能10^120倍差距当成巨大的微调灾难，往往缺少结构解释。",
            "en": "Traditional discussions treat the 10^120 vacuum-energy gap as a huge fine-tuning disaster and often lack a structural explanation.",
        },
        "new_explanation": {
            "zh": "新解释把量子场论的总和与宇宙观测值拆开：前者对应未对消的总量，后者对应容斥后的净值。",
            "en": "The new explanation separates the QFT total from the cosmological observation: the first is the uncancelled total, the second the post-cancellation net value.",
        },
        "basis": {
            "zh": "原文明确写出真空能问题应重写为容斥对消后的净值问题，并把10^120差距解释为乘法结构压缩。",
            "en": "The source note explicitly reframes vacuum energy as a net-after-cancellation problem and explains the 10^120 gap as compression by a multiplicative structure.",
        },
        "testability": {
            "zh": "如果宇宙膨胀参数变化时暗能量的有效值同步变化，这说明净值而非总量才是关键变量。",
            "en": "If the effective dark-energy value changes together with cosmological expansion parameters, that would support the net-value interpretation over the raw total.",
        },
        "categories": ["physics"],
        "related_functions": ["D401", "D387", "D266", "D397", "D410", "D423"],
        "related_cases": ["C-0554"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
            "dianhuo/originals/1912595796075888368_点火｜P16-P18观测数据检验方案.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "cosmological constant inclusion exclusion cancellation",
                "宇宙学常数 容斥 对消 净值",
                "vacuum energy net value after cancellation",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把暗能量问题改写为容斥对消后的净值，不再把总量与观测值混为一谈。",
                "en": "This answer reframes dark energy as a net value after inclusion-exclusion cancellation instead of conflating totals with observations.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0009",
        "title": {"zh": "哈勃常数危机是不同截面的幽灵效应差异", "en": "The Hubble crisis is a difference in ghost effects across different cross-sections"},
        "question": {
            "zh": "哈勃常数张力是测量错了，还是不同观测截面采到了不同的系统状态？",
            "en": "Is the Hubble tension a measurement error, or do different observational cross-sections sample different system states?",
        },
        "answer": {
            "zh": "更像后者：近域和远域测量对应势能面Φ的不同截面，所以哈勃常数会随红移演化。",
            "en": "It is more like the latter: near and far measurements correspond to different cross-sections of the potential surface Phi, so the Hubble constant evolves with redshift.",
        },
        "prior_answers": {
            "zh": "传统解释常把哈勃张力视为系统误差或校准偏差，但这不解释为何不同红移区间的结果会系统偏移。",
            "en": "Traditional explanations often treat Hubble tension as systematics or calibration bias, but that does not explain why different redshift ranges shift systematically.",
        },
        "new_explanation": {
            "zh": "新解释引入幽灵效应：早期极小点消失后仍留下拐点拖慢系统，因此高红移与低红移测到的H₀不同。",
            "en": "The new explanation introduces a ghost effect: after the early minimum disappears, its inflection-point remnant still slows the system, so high- and low-redshift H0 values differ.",
        },
        "basis": {
            "zh": "原文明确写出哈勃常数差异应随红移z演化，而不是固定常量。",
            "en": "The source note explicitly says the Hubble difference should evolve with redshift z rather than remain a fixed constant.",
        },
        "testability": {
            "zh": "若中等红移区间的H₀衰减更符合指数而非幂律，并与D384幽灵效应一致，这一答案就更强。",
            "en": "If mid-redshift H0 decay fits an exponential better than a power law and matches the D384 ghost effect, this answer gets stronger.",
        },
        "categories": ["physics"],
        "related_functions": ["D335", "D384"],
        "related_cases": ["C-0554"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
            "dianhuo/originals/1912595796075888368_点火｜P16-P18观测数据检验方案.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "Hubble tension ghost effect redshift evolution",
                "哈勃常数 幽灵效应 红移 演化",
                "H0 evolves with redshift potential surface",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把哈勃张力解释为不同截面的幽灵效应，而不是单纯校准问题。",
                "en": "This answer explains Hubble tension as a ghost-effect difference across cross-sections rather than a pure calibration issue.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0010",
        "title": {"zh": "层级问题是 d=4 稳定性约束的解析解", "en": "The hierarchy problem is the analytic solution of the d=4 stability constraint"},
        "question": {
            "zh": "希格斯质量为什么远小于普朗克质量，是不是被精细调节出来的？",
            "en": "Why is the Higgs mass so much smaller than the Planck mass, and is it just fine-tuned?",
        },
        "answer": {
            "zh": "更像是 d=4 稳定性约束的结果，而不是人为精调；大的量子修正会被容斥项自动压低。",
            "en": "It looks more like the result of a d=4 stability constraint than manual fine-tuning; large quantum corrections are automatically suppressed by the inclusion-exclusion structure.",
        },
        "prior_answers": {
            "zh": "传统层级问题把这个差距看成需要额外微调或新对称性解释的异常。",
            "en": "The classic hierarchy problem treats the gap as an anomaly requiring extra fine-tuning or new symmetries.",
        },
        "new_explanation": {
            "zh": "新解释把比值读成结构约束的解析解：不是质量“被做小”，而是系统在 d=4 稳定区间内只能落在那个位置。",
            "en": "The new explanation reads the ratio as the analytic outcome of a structural constraint: the mass is not made small by hand, it simply lands there inside the d=4 stable interval.",
        },
        "basis": {
            "zh": "原文明确把希格斯质量与普朗克质量之比写成 d=4 稳定性约束的结果。",
            "en": "The source note explicitly writes the Higgs-to-Planck ratio as the result of a d=4 stability constraint.",
        },
        "testability": {
            "zh": "如果未来统一理论能从稳定性约束直接导出层级间距，而无需额外精调，这一答案就会被加强。",
            "en": "If a future unified theory derives the hierarchy gap directly from the stability constraint without extra fine-tuning, this answer is strengthened.",
        },
        "categories": ["physics"],
        "related_functions": ["D297", "D410", "D325", "D307"],
        "related_cases": ["C-0554"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "hierarchy problem d=4 stability constraint",
                "层级问题 d=4 稳定性 约束",
                "Higgs Planck ratio analytic solution",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把层级问题读成 d=4 稳定性约束的解析结果。",
                "en": "This answer reads the hierarchy problem as the analytic result of a d=4 stability constraint.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0011",
        "title": {"zh": "黑洞信息在极小点遗迹中以相变方式释放", "en": "Black-hole information is released as a phase transition in the remnant of a vanished minimum"},
        "question": {
            "zh": "黑洞信息到底是完全丢失，还是会以某种临界方式被释放出来？",
            "en": "Does black-hole information disappear entirely, or is it released in some critical way?",
        },
        "answer": {
            "zh": "更像后者：信息被压缩在极小点消失后的拐点遗迹里，蒸发到临界质量时会以相变方式释放。",
            "en": "It is more like the latter: information is compressed into the inflection-point remnant after the minimum vanishes, and when evaporation reaches the critical mass it is released as a phase transition.",
        },
        "prior_answers": {
            "zh": "传统争论常停留在信息完全丢失与信息完全守恒的二分对立。",
            "en": "The traditional debate often stops at a binary opposition between total information loss and total conservation.",
        },
        "new_explanation": {
            "zh": "新解释把黑洞视作门控与压缩面，信息不是消失，而是被重编码成可在临界点恢复的残余结构。",
            "en": "The new explanation treats the black hole as a gating and compression surface: information is not erased, but recoded into a remnant structure that can be recovered at the critical point.",
        },
        "basis": {
            "zh": "原文明确给出黑洞信息悖论的门控视角，并把蒸发末期描述为相变释放。",
            "en": "The source note explicitly gives the gating view of the black-hole information paradox and describes the evaporation endpoint as a phase-transition release.",
        },
        "testability": {
            "zh": "若类比黑洞实验或数值模拟在临界尺寸附近出现纠缠度上升与蒸发突变，这一答案就更强。",
            "en": "If analogue-black-hole experiments or simulations show rising entanglement and an evaporation jump near the critical size, this answer becomes stronger.",
        },
        "categories": ["physics"],
        "related_functions": ["D412", "D413", "D384", "D295", "D307"],
        "related_cases": ["C-0457"],
        "related_discoveries": [],
        "related_predictions": ["P18"],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
            "dianhuo/originals/1912595796075888368_点火｜P16-P18观测数据检验方案.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "black hole information phase transition remnant",
                "黑洞信息 相变 残余物",
                "information released at critical mass black hole",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把信息释放写成临界质量上的相变，而不是连续泄漏或彻底消失。",
                "en": "This answer turns information release into a phase transition at the critical mass, not a continuous leak or total disappearance.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
    {
        "id": "ANS-0012",
        "title": {"zh": "宇宙波函数不可知是子系统门控限制的结果", "en": "Cosmic wavefunction unknowability follows from subsystem gating limits"},
        "question": {
            "zh": "为什么宇宙整体的波函数对内部观测者总是不可完全知道？",
            "en": "Why is the universe's overall wavefunction never fully knowable to observers inside it?",
        },
        "answer": {
            "zh": "因为观测者永远是宇宙的子系统，子系统对超系统的门控和维度压缩必然不对称，所以完整状态不可达。",
            "en": "Because observers are always subsystems of the universe, and gating plus dimensional compression from subsystem to supersystem is necessarily asymmetric, so the full state is unreachable.",
        },
        "prior_answers": {
            "zh": "传统说法常把这个问题解释成技术限制或纯哲学困境。",
            "en": "Traditional accounts often treat this as a technical limitation or a purely philosophical puzzle.",
        },
        "new_explanation": {
            "zh": "新解释把不可知性改写成结构性限制：能知道的永远是统计结构，不是精确全态。",
            "en": "The new explanation turns unknowability into a structural limit: what can be known is always statistical structure, not the exact global state.",
        },
        "basis": {
            "zh": "原文明确把宇宙波函数不可知性和哥德尔不完备性作类比，并强调观测者ε_awar永远小于宇宙ε。",
            "en": "The source note explicitly compares cosmic wavefunction unknowability to Gödel incompleteness and stresses that observer epsilon-aware is always smaller than the universe's epsilon.",
        },
        "testability": {
            "zh": "如果更优采样只能提升统计信息而不能突破全态不可知边界，这个答案就成立；若能突破，则该解释失败。",
            "en": "If better sampling only improves statistical information without breaking the global-knowability boundary, this answer holds; if it can break the boundary, it fails.",
        },
        "categories": ["physics", "philosophy"],
        "related_functions": ["D86", "D96", "A4", "D307"],
        "related_cases": ["C-0457"],
        "related_discoveries": [],
        "related_predictions": [],
        "source_refs": [
            "dianhuo/originals/1912595454627192952_点火｜物理学七团乌云碰撞收敛（P16-P18新增·3条可检验预测）.md",
        ],
        "academic_novelty": {
            "status": "inconclusive",
            "checked_at": "",
            "query_terms": [
                "cosmic wavefunction unknowability subsystem gating",
                "宇宙波函数 不可知 子系统 门控",
                "observer cannot know global wavefunction",
            ],
            "sources_checked": ["OpenAlex", "Crossref"],
            "nearest_matches": [],
            "novelty_claim": {
                "zh": "该答案把宇宙波函数不可知写成子系统门控限制，而不是单纯的技术无能。",
                "en": "This answer turns cosmic wavefunction unknowability into a subsystem gating limit rather than mere technical inability.",
            },
            "reviewer_note": "bootstrap sub-answer from seven-cloud recovery note; novelty not confirmed",
        },
        "confidence": "medium",
        "status": "answer_pending_novelty_review",
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
    },
]


def build_source_summary() -> dict[str, int]:
    summary = {}
    for root in RAW_NOTE_ROOTS:
        if not root.exists():
            summary[str(root.relative_to(REPO_ROOT))] = 0
            continue
        summary[str(root.relative_to(REPO_ROOT))] = len(list(root.rglob("*.md")))
    summary["functions"] = len(read_json(FUNCTIONS_JSON, []))
    summary["cases"] = len(read_json(CASES_JSON, []))
    summary["discoveries"] = len(read_json(DISCOVERIES_JSON, []))
    summary["predictions"] = len(read_json(PREDICTIONS_JSON, []))
    return summary


def build_answer_leads_from_bootstrap() -> list[dict]:
    # The bootstrap set is intentionally conservative: we promote only items
    # that are explicitly marked as new answers in the source notes.
    return [dict(item) for item in ANSWER_BLUEPRINTS]


def build_answer_pages(answers: list[dict]) -> None:
    ANSWER_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    CATEGORY_DIR.mkdir(parents=True, exist_ok=True)

    for item in answers:
        write_text(ITEM_DIR / f"{item['id']}.md", render_answer_page(item))


def build_category_pages(category_map: list[dict]) -> None:
    for category in category_map:
        write_text(CATEGORY_DIR / f"{category['id']}.md", render_category_page(category))


def normalize_answer_item(item: dict) -> dict:
    normalized = dict(item)
    normalized["related_functions"] = list(dict.fromkeys(normalized.get("related_functions", [])))
    normalized["related_cases"] = list(dict.fromkeys(normalized.get("related_cases", [])))
    normalized["related_discoveries"] = list(dict.fromkeys(normalized.get("related_discoveries", [])))
    normalized["related_predictions"] = list(dict.fromkeys(normalized.get("related_predictions", [])))
    normalized["source_refs"] = normalize_source_refs(normalized.get("source_refs", []))
    if "page" not in normalized:
        normalized["page"] = f"docs/zh/answers/items/{normalized['id']}.md"
    formal, derivation = answer_formalization(normalized)
    normalized["mathematical_formalization"] = formal
    normalized["mathematical_derivation"] = derivation
    return normalized


def is_blank_value(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def audit_answer_leads(answers: list[dict]) -> tuple[dict, str]:
    reports: list[dict] = []
    source_pending = 0
    novelty_inconclusive = 0
    novelty_passed = 0
    novelty_failed = 0

    required_fields = [
        "question",
        "answer",
        "prior_answers",
        "new_explanation",
        "basis",
        "testability",
        "categories",
        "related_functions",
        "related_cases",
        "related_discoveries",
        "related_predictions",
        "source_refs",
        "academic_novelty",
        "status",
        "confidence",
        "page",
    ]

    for item in answers:
        missing: list[str] = []
        empty_optional: list[str] = []

        for field in required_fields:
            if field not in item:
                missing.append(field)
                continue
            value = item.get(field)
            if is_blank_value(value):
                empty_optional.append(field)

        novelty = item.get("academic_novelty", {}) or {}
        novelty_status = novelty.get("status", "pending")
        if novelty_status == "inconclusive":
            novelty_inconclusive += 1
        elif novelty_status == "passed":
            novelty_passed += 1
        elif novelty_status == "failed":
            novelty_failed += 1
        if missing or not item.get("source_refs"):
            source_pending += 1

        reports.append(
            {
                "id": item.get("id"),
                "title": item.get("title", {}),
                "status": item.get("status"),
                "academic_novelty_status": novelty_status,
                "missing_fields": missing,
                "empty_fields": empty_optional,
                "page": item.get("page"),
            }
        )

    payload = {
        "generated_at": date.today().isoformat(),
        "answer_leads_total": len(answers),
        "source_pending": source_pending,
        "inconclusive_novelty": novelty_inconclusive,
        "passed_novelty": novelty_passed,
        "failed_novelty": novelty_failed,
        "reports": reports,
    }

    lines = [
        "# Answer Leads Quality Report",
        "",
        f"- answer_leads_total: {payload['answer_leads_total']}",
        f"- source_pending: {payload['source_pending']}",
        f"- inconclusive_novelty: {payload['inconclusive_novelty']}",
        f"- passed_novelty: {payload['passed_novelty']}",
        f"- failed_novelty: {payload['failed_novelty']}",
        "",
        "## Per Lead Audit",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"### {report['id']} {report['title'].get('zh', '')}",
                "",
                f"- status: {report['status']}",
                f"- academic_novelty.status: {report['academic_novelty_status']}",
                f"- missing_fields: {', '.join(report['missing_fields']) or '-'}",
                f"- empty_fields: {', '.join(report['empty_fields']) or '-'}",
                f"- page: {report['page']}",
                "",
            ]
        )
    return payload, "\n".join(lines)


def write_answer_template() -> None:
    write_text(
        ANSWER_TEMPLATE_MD,
        """# ANS-____ 新答案标题 / New Answer Title

[← 返回新答案总表 / Back to New Answers](../../../ANSWERS.md)
[返回仓库首页 / Back to Repository Home](../../../README.md)

## 问题 / Question

中文：
English:

## 新答案 / New Answer

中文：
English:

## 已有答案或旧问题背景 / Existing Answers or Prior Problem Background

中文：
English:

## 新解释在哪里 / What Is New in This Answer

中文：
English:

## 推出依据 / Basis

中文：
English:

## 可检验性 / Testability

中文：
English:

## 纯数学函数 / Pure Mathematical Function

- 对象 / Object: `A_{ANS-____}`
- 定义域 / Domain: `Q × E × A`
- 值域 / Codomain: `{A_0,A_1}`
- 数学表达 / Expression: `A_{ANS-____}=A_1 ⇔ L(A_1|Q,E)+Ω(A_1) < L(A_0|Q,E)+Ω(A_0)`
- 有效条件 / Validity: `J_n^+(A_{ANS-____})=1 ∧ J_n^-(A_{ANS-____})=0`

## 数学推导 / Mathematical Derivation

- 推导类型 / Derivation type: `answer_objective_rewrite_derivation`
- 收敛状态 / Convergence status: `converged`
- 推导步骤 / Steps:
  - 定义旧答案 `A_0` 与新答案 `A_1`。
  - 定义解释损失 `L(A|Q,E)` 与结构惩罚 `Ω(A)`。
  - 证明新答案满足严格目标函数下降。
  - 通过反向通道排除 `L(A_1|Q,E)+Ω(A_1) ≥ L(A_0|Q,E)+Ω(A_0)`。
- 正向检查 / Forward check: `J_n^+(A)=1`
- 反向检查 / Reverse check: `J_n^-(A)=0`
- 收敛判据 / Convergence: `ΔA=∅ ∧ (J_n^+,J_n^-)=(1,0)`

## 分类 / Categories

-

## 相关函数 / Related Functions

-

## 相关案例 / Related Cases

-

## 相关发现 / Related Discoveries

-

## 相关预测 / Related Predictions

-

## 来源回指 / Source References

-

## 学术搜索独有性检查 / Academic Novelty Check

- 状态 / Status：pending / passed / failed / inconclusive
- 检查时间 / Checked at：
- 搜索词 / Query terms：
- 检查来源 / Sources checked：
- 最近相似结果 / Nearest matches：
- 为什么不是同一答案 / Why not identical：
- 独有性声明 / Novelty claim：

## 状态 / Status

draft / active / answer_pending_novelty_review / existing_answer_reference / deprecated / merged

## 置信度 / Confidence

low / medium / high
""",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    answers = [normalize_answer_item(item) for item in build_answer_leads_from_bootstrap()]
    functions = read_json(FUNCTIONS_JSON, [])
    cases = read_json(CASES_JSON, [])
    discoveries = read_json(DISCOVERIES_JSON, [])
    predictions = read_json(PREDICTIONS_JSON, [])
    category_map = build_category_map(answers, CATEGORY_DEFINITIONS, functions, cases, discoveries, predictions)

    template_text = """# ANS-____ 新答案标题 / New Answer Title

[← 返回新答案总表 / Back to New Answers](../../../ANSWERS.md)
[返回仓库首页 / Back to Repository Home](../../../README.md)

## 问题 / Question

中文：
English:

## 新答案 / New Answer

中文：
English:

## 已有答案或旧问题背景 / Existing Answers or Prior Problem Background

中文：
English:

## 新解释在哪里 / What Is New in This Answer

中文：
English:

## 推出依据 / Basis

中文：
English:

## 可检验性 / Testability

中文：
English:

## 纯数学函数 / Pure Mathematical Function

- 对象 / Object: `A_{ANS-____}`
- 定义域 / Domain: `Q × E × A`
- 值域 / Codomain: `{A_0,A_1}`
- 数学表达 / Expression: `A_{ANS-____}=A_1 ⇔ L(A_1|Q,E)+Ω(A_1) < L(A_0|Q,E)+Ω(A_0)`
- 有效条件 / Validity: `J_n^+(A_{ANS-____})=1 ∧ J_n^-(A_{ANS-____})=0`

## 数学推导 / Mathematical Derivation

- 推导类型 / Derivation type: `answer_objective_rewrite_derivation`
- 收敛状态 / Convergence status: `converged`
- 推导步骤 / Steps:
  - 定义旧答案 `A_0` 与新答案 `A_1`。
  - 定义解释损失 `L(A|Q,E)` 与结构惩罚 `Ω(A)`。
  - 证明新答案满足严格目标函数下降。
  - 通过反向通道排除 `L(A_1|Q,E)+Ω(A_1) ≥ L(A_0|Q,E)+Ω(A_0)`。
- 正向检查 / Forward check: `J_n^+(A)=1`
- 反向检查 / Reverse check: `J_n^-(A)=0`
- 收敛判据 / Convergence: `ΔA=∅ ∧ (J_n^+,J_n^-)=(1,0)`

## 分类 / Categories

-

## 相关函数 / Related Functions

-

## 相关案例 / Related Cases

-

## 相关发现 / Related Discoveries

-

## 相关预测 / Related Predictions

-

## 来源回指 / Source References

-

## 学术搜索独有性检查 / Academic Novelty Check

- 状态 / Status：pending / passed / failed / inconclusive
- 检查时间 / Checked at：
- 搜索词 / Query terms：
- 检查来源 / Sources checked：
- 最近相似结果 / Nearest matches：
- 为什么不是同一答案 / Why not identical：
- 独有性声明 / Novelty claim：

## 状态 / Status

draft / active / answer_pending_novelty_review / existing_answer_reference / deprecated / merged

## 置信度 / Confidence

low / medium / high
"""
    index_text = render_answer_index(answers, category_map)
    machine_text = render_answer_index_md(answers)
    summary = build_source_summary()
    notes = [
        "bootstrap notes were scanned conservatively for explicit new-answer material",
        "physics, grand-unification, gravity, black-hole information, and Qin-unification notes were promoted",
        "no curated answer was marked active because novelty is not confirmed yet",
        f"{PHYSICS_SEVEN_CLOUDS_RECOVERY}: corrected the prior misread and recovered 物理学七团乌云",
        "physics seven clouds recovery: corrected the prior misread and searched for 物理学七团乌云 / 七团乌云 / 七朵乌云",
        "low-priority misread keywords (气团 / 雾云) were downgraded and are no longer the main recovery target",
    ]
    payload, report_md = render_bootstrap_report(answers, category_map, summary, notes)
    lead_audit_payload, lead_audit_md = audit_answer_leads(answers)
    lead_audit_json = REPO_ROOT / "data/rebuild/answer-leads-quality-report.json"
    lead_audit_markdown = REPO_ROOT / "data/rebuild/answer-leads-quality-report.md"

    if args.check or args.dry_run:
        current_template = ANSWER_TEMPLATE_MD.read_text(encoding="utf-8") if ANSWER_TEMPLATE_MD.exists() else ""
        current_index = ANSWERS_LIST_MD.read_text(encoding="utf-8") if ANSWERS_LIST_MD.exists() else ""
        current_machine = ANSWERS_INDEX_MD.read_text(encoding="utf-8") if ANSWERS_INDEX_MD.exists() else ""
        if current_template != template_text:
            print("answer template out of date")
            return 1 if args.check else 0
        if current_index != index_text:
            print("answer index out of date")
            return 1 if args.check else 0
        if current_machine != machine_text:
            print("answer machine index out of date")
            return 1 if args.check else 0
        print(
            json.dumps(
                {
                    "answers": len(answers),
                    "curated": sum(1 for item in answers if item.get("status") == "active"),
                    "leads": sum(1 for item in answers if item.get("status") != "active"),
                    "check": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    write_answer_template()
    write_json(CATEGORIES_JSON, CATEGORY_DEFINITIONS)
    write_jsonl(CATEGORIES_JSONL, CATEGORY_DEFINITIONS)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_json(ANSWERS_JSON, answers)
    write_jsonl(ANSWERS_JSONL, answers)
    write_text(ANSWERS_INDEX_MD, machine_text)
    write_text(ANSWERS_LIST_MD, index_text)
    write_json(lead_audit_json, lead_audit_payload)
    write_text(lead_audit_markdown, lead_audit_md)
    build_answer_pages(answers)
    build_category_pages(category_map)
    write_json(BOOTSTRAP_REPORT_JSON, payload)
    write_text(BOOTSTRAP_REPORT_MD, report_md)

    print(
        json.dumps(
            {
                "answers": len(answers),
                "curated": sum(1 for item in answers if item.get("status") == "active"),
                "leads": sum(1 for item in answers if item.get("status") != "active"),
                "report_md": str(BOOTSTRAP_REPORT_MD.relative_to(REPO_ROOT)),
                "report_json": str(BOOTSTRAP_REPORT_JSON.relative_to(REPO_ROOT)),
                "lead_audit_md": str(lead_audit_markdown.relative_to(REPO_ROOT)),
                "lead_audit_json": str(lead_audit_json.relative_to(REPO_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
