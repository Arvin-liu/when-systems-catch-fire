# 受治理语料关系分析（TASK 104 · §4）

本分析由 `tools/build_corpus_relation_graph.py` 确定性生成，无网络依赖，仅使用 Python 标准库。

## 规模统计

- 资产卡节点：339（FUNCTION_ASSET=12, NONFUNCTION_CLAIM=43, RESULT_OR_ARTICLE=284）
- 图节点总数：351（含 MAP 主题中枢、合成文档节点、跨域中枢）
- 受治理边总数：259
- 边类型分布：alias_or_correction=1, correction_source=4, depends_on=8, evidence_source=31, identity_correction=1, related=80, reverse_depends=8, shared_research_question=126
- 候选簇总数：15；单卡叶节点：0
- 簇处置分布：ARTICLE_CANDIDATE=8, REFERENCE_TAXONOMIC=7

## 关系类型与证据（受治理边）

每条被接受的关系都声明 type / evidence / confidence。语义相似与引用重叠仅作候选信号，记录于 `corpus_relation_graph.json` 的 `candidate_signals`，**不**构成规范关系。

## 文章簇候选（按处置分类）


### ARTICLE_CANDIDATE（8）

- **C000** 规模=31 主导主题=MATHEMATICS(0.81) 域数=7
  - 中心问题候选：这里发生了什么纠正、撤回或回弹？当前的断言上限是什么？
  - 处置理由：
- **C001** 规模=15 主导主题=ARCHITECTURE_GOVERNANCE(1.00) 域数=6
  - 中心问题候选：知识资产怎样被登记、裁决、修订、隔离并保持机器与人类表面一致？
  - 处置理由：
  - 成员：nfc-00b4be17fb8dc706, nfc-156313cd333787a2, nfc-187e985133669a56, nfc-2843222a849fe77e, nfc-2b7304f480da70c2, nfc-390d533e6aa565c0, nfc-3d9ffb2206406fcc, nfc-3f2e05f213dea1ef, nfc-517a9b6de3674e2a, nfc-51f85a6892787610, nfc-6122e6f96efe210e, nfc-61546854af53780b, nfc-6ca935ca1a4f2a8e, nfc-70a1ec2c42864627, nfc-777640d03f719f40
- **C002** 规模=17 主导主题=COGNITION(1.00) 域数=5
  - 中心问题候选：认知类比、行动选择和现实反馈怎样保留边界与失败条件？
  - 处置理由：
  - 成员：hr-1437a5c9924f3c9e, hr-252ed61cfaf40f35, hr-4021615f6416219a, hr-46d4e1a9e463a4a0, hr-6585a5fc88149fff, hr-6d4c8f2164bcd7cb, hr-771c2981fcc20396, hr-8079a8712f2b03bc, hr-8c7e1c2721f6e7fd, hr-8d592a920b9edd0e, hr-8faeed857e0f9416, hr-933d6ba7d34f8014, hr-9be719cb6ef0fd88, hr-9bf38326d66a104a, hr-aa71cb6d79bb27ed, hr-c0254716ff47346d, hr-c32095e69516906c
- **C003** 规模=4 主导主题=MATHEMATICS(1.00) 域数=4
  - 中心问题候选：对象、运算、定义域、证明和反例究竟完成到哪一步？
  - 处置理由：
  - 成员：nfc-00b4be17fb8dc706, nfc-390d533e6aa565c0, nfc-3d9ffb2206406fcc, nfc-61546854af53780b
- **C004** 规模=15 主导主题=OPERATIONS_EVIDENCE(1.00) 域数=6
  - 中心问题候选：候选、验证、合并和 Current 怎样分离并留下可复算证据？
  - 处置理由：
  - 成员：hr-0450dd379222f5ba, hr-04e3c04b5c9de706, hr-052d55fd7ec8bacd, hr-081b7e1fafaa5756, nfc-2b7304f480da70c2, nfc-2f6931fff5a6554c, nfc-6122e6f96efe210e, nfc-6ca935ca1a4f2a8e, nfc-70a1ec2c42864627, nfc-777640d03f719f40, nfc-996c4e8631d40356, nfc-a5870d6c2e430817, nfc-a6b80fca608c8c8f, nfc-c15234f1546c00ea, nfc-c349fbdc470b50ab
- **C005** 规模=11 主导主题=PHYSICS(1.00) 域数=6
  - 中心问题候选：门控模型能支持什么有界物理投影，哪些统一与观测义务仍未完成？
  - 处置理由：
  - 成员：nfc-00b4be17fb8dc706, nfc-51f85a6892787610, nfc-61546854af53780b, nfc-6ca935ca1a4f2a8e, nfc-70a1ec2c42864627, nfc-777640d03f719f40, nfc-7ba5ae6b5efe40a7, nfc-7f34ff08b3193964, nfc-82ebe95def5bfab1, nfc-9d5698768267468e, nfc-b3044ed3734222fb
- **C006** 规模=18 主导主题=SYSTEMS(1.00) 域数=6
  - 中心问题候选：跨尺度表示、概率动力学和关系网络能描述什么，不能证明什么？
  - 处置理由：
  - 成员：hr-09324a8008a3bd3d, hr-0dd59e3bbd5eeb55, hr-0e7b7e2d16e773be, hr-0ef2189bb50603b7, hr-0ef7472961a343e5, hr-0fe03d4a4ca70a91, hr-1c328f9ffe6aee1f, hr-1c89ea0a4c2a0aa1, hr-1d52767df2986dd5, hr-1ee77928279485fa, hr-1faefff9c300160f, hr-2e400b8fd7cc6b10, hr-3ad9b4c8053ea959, hr-3d02f20fb6692a0c, nfc-1e10227f1b51e4d0, nfc-2b7304f480da70c2, nfc-b3044ed3734222fb, nfc-b424983d09c9a88d
- **C007** 规模=16 主导主题=WRITING_PUBLICATION(1.00) 域数=6
  - 中心问题候选：研究结果如何形成可阅读作品，同时不越过来源、证据和许可边界？
  - 处置理由：
  - 成员：hr-1c89ea0a4c2a0aa1, hr-25ccad6cef81cbea, hr-3069e59a51d869c3, hr-3b5e72d7f1cdfb5b, hr-3d02f20fb6692a0c, hr-3d6271e0ba81267e, hr-43bf10109af2485e, hr-4419fea9529c829c, hr-44a1c398c470bbf4, hr-45480c716d721c81, hr-460ef60e3cf27dca, nfc-3d9ffb2206406fcc, nfc-517a9b6de3674e2a, nfc-6122e6f96efe210e, nfc-82ebe95def5bfab1, nfc-97dbfc72d7ef8b40

### REFERENCE_TAXONOMIC（7）

- **C008** 规模=46 主导主题=ARCHITECTURE_GOVERNANCE(1.00) 域数=3
  - 中心问题候选：架构、治理与自我纠错机制如何保证仓库主张不被悄悄升级？
  - 处置理由：簇过大(46 卡)且缺乏卡间依赖/纠正主轴，仅由研究问题中枢或主题聚合，按来源族/研究问题拆分以防止"按主题标签"式笼统成篇。（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；保留为参考，待编辑界定子问题。）
- **C009** 规模=2 主导主题=COGNITION(1.00) 域数=3
  - 中心问题候选：关于认知、Agent 与行动的断言，哪些越过了事实边界？
  - 处置理由：仅按主题标签聚合(COGNITION)、无研究问题中枢或卡间结构；保留为参考集合，文章须先由编辑界定连贯问题。
  - 成员：hr-c322de3c7799a555, hr-f58d1b491fb96c27
- **C010** 规模=61 主导主题=MATHEMATICS(1.00) 域数=6
  - 中心问题候选：对象、运算、定义域、证明与反例在数学上究竟完成到哪一步？
  - 处置理由：簇过大(61 卡)且缺乏卡间依赖/纠正主轴，仅由研究问题中枢或主题聚合，按来源族/研究问题拆分以防止"按主题标签"式笼统成篇。（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；保留为参考，待编辑界定子问题。）
- **C011** 规模=73 主导主题=OPERATIONS_EVIDENCE(1.00) 域数=1
  - 中心问题候选：迭代、验证与证据工程如何使结论可复现、可 adjudicate？
  - 处置理由：簇过大(73 卡)且缺乏卡间依赖/纠正主轴，仅由研究问题中枢或主题聚合，按来源族/研究问题拆分以防止"按主题标签"式笼统成篇。（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；保留为参考，待编辑界定子问题。）
- **C012** 规模=4 主导主题=PHYSICS(1.00) 域数=3
  - 中心问题候选：门控模型能支持什么有界物理投影，哪些统一与观测义务仍未完成？
  - 处置理由：仅按主题标签聚合(PHYSICS)、无研究问题中枢或卡间结构；保留为参考集合，文章须先由编辑界定连贯问题。
  - 成员：hr-8abef15d00fa6899, nfc-d30b79cb6b607ade, nfc-fcd82f719963c928, nfc-ffa78acc808beedc
- **C013** 规模=38 主导主题=SYSTEMS(1.00) 域数=5
  - 中心问题候选：系统论与机制建模在何处提供了可检验的机制，而非仅命名？
  - 处置理由：仅按主题标签聚合(SYSTEMS)、无研究问题中枢或卡间结构；保留为参考集合，文章须先由编辑界定连贯问题。
- **C014** 规模=11 主导主题=WRITING_PUBLICATION(1.00) 域数=2
  - 中心问题候选：面向公众的表达如何在可读与不越界之间取得平衡？
  - 处置理由：仅按主题标签聚合(WRITING_PUBLICATION)、无研究问题中枢或卡间结构；保留为参考集合，文章须先由编辑界定连贯问题。
  - 成员：hr-4f3c4ff4a7ab0e3a, hr-5a6642209467ff3a, hr-67cc7f2c07c67bd9, hr-8e4b48d6273130f9, hr-a932eb17267d9709, hr-a960756efab9d50a, hr-b42fdd29bfb492b0, hr-b55587d4d61d4426, hr-d328ae24912155e2, hr-de57c4f1ec87eada, hr-e7a557e011cab937

## 候选信号（非规范关系，仅供编辑参考）

- 语义相似候选对：200（最高 cosine=0.950）
- 引用重叠组：39

## 方法与局限

- 资产单元 = 339 张重点卡（284 结果/文章 + 12 函数 + 43 非函数断言）。
- 显式边来自卡的 `依赖`/`被引用`/`相关`/`主题` 字段，以及 MAP 主题中枢、CORRECTIONS/EVOLUTION 表、OPEN-QUESTIONS/EVIDENCE-LINEAGE 显式提及。
- 跨域映射仅当卡体显式出现跨域措辞且 ≥2 主题域时才标记，低置信。
- 簇处置启发式检测：过大拆分、异质拒绝、纯分类保留为参考、单卡叶节点。
- 机器无法判定文学质量；文章是否成篇仍需编辑按 §5 准则人工裁定。
