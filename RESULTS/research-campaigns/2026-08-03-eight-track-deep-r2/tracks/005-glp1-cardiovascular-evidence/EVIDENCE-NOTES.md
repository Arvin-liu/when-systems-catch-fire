# 005 证据阶段记录：GLP-1 心血管结局

## 阶段边界

本文件只记录来源阅读、页码／章节／表格定位和可复算数字。R1 身份为 `UNVERIFIED_RAPID_EVIDENCE_SCANS`；R1 报告不能直接升级为正式知识。SELECT 的多篇二次分析共享同一随机队列，不能计作彼此独立的复制。

证据阶段于 2026-08-03 11:25 Asia/Shanghai 开始，至本检查点已完成原始试验、注册结果、FDA、NICE、独立系统综述和反方／机制边界材料的阅读。论文 PDF 的页码以下指下载文件页码；SELECT 主论文下载文件含 University of Groningen 存档封面 1 页，期刊正文为 PDF pp.2–13。

## SELECT：原始随机试验

主论文：[Semaglutide and Cardiovascular Outcomes in Obesity without Diabetes](https://doi.org/10.1056/NEJMoa2307563)，NEJM 2023;389:2221–2232。可复核 publisher PDF 通过 University of Groningen repository 下载，13 页，SHA-256 `e592caf24b51c7093933f8ad09b90f3acf09bea1eb980154dc1c0047c389cb43`。

- PDF p.2（摘要）：17,604 人；8,803 司美格鲁肽、8,801 安慰剂；平均暴露 34.2±13.7 月；平均随访 39.8±9.4 月；MACE 569/8803（6.5%）对 701/8801（8.0%）；HR 0.80，95% CI 0.72–0.90；永久停药相关不良事件 16.6% 对 8.2%。
- PDF pp.3–4（Methods，Trial Design、Trial Population、Intervention、Endpoints、Statistical Analysis）：804 个中心、41 个国家；年龄至少 45 岁、BMI 至少 27 kg/m²、既往 MI／卒中／有症状 PAD；排除糖尿病、筛查 HbA1c ≥6.5%、近 90 日降糖药或 GLP-1、NYHA IV 心衰、终末期肾病；1:1 中央随机、双盲、每周皮下注射，0.24→0.5→1.0→1.7→2.4 mg，16 周递增；主要终点是时间到首次 CV 死亡、非致死 MI 或非致死卒中。
- PDF p.4（Statistical Analysis）：主要分析为 full analysis／意向治疗，不因依从性、停药或背景药调整而排除随机者；Cox 比例风险模型；事件驱动，计划至少 1,225 个主要事件；预设中期优效分析并按序贯设计校正。
- PDF pp.5–6（Randomization、Follow-up、Table 1）：平均年龄 61.6 岁；72.3% 男性；平均 BMI 33.3；71.5% BMI≥30；66.4% 有前糖尿病；超过四分之三既往 MI，约四分之一有慢性心衰；大多数接受降脂药和抗血小板药。平均随访 39.8±9.4 月；永久提前停药 26.7% 对 23.6%；平均实际暴露 33.3 对 35.1 月；104 周约 77% 在 2.4 mg；96.9% 完成试验，生命状态 99.4% 可得。
- PDF p.7（Table 2、Table 4）：MACE 569（6.5%）对 701（8.0%）；CV 死亡 223（2.5%）对 262（3.0%），HR 0.85（0.71–1.01），P=0.07，序贯检验未确认；心衰复合 300（3.4%）对 361（4.1%），HR 0.82（0.71–0.96），但层级检验未继续；全因死亡 375（4.3%）对 458（5.2%），HR 0.81（0.71–0.93），同样不应写成已确认的层级优效。非致死 MI HR 0.72（0.61–0.85），非致死卒中 HR 0.93（0.74–1.15）。
- PDF p.7（Table 4，targeted safety collection）：严重不良事件 33.4% 对 36.4%；永久停药相关不良事件 16.6% 对 8.2%，其中胃肠道事件 10.0% 对 2.0%；胆囊相关事件 2.8% 对 2.3%。论文明确安全数据是定向收集，只系统记录严重不良事件、导致停药事件和预设特殊关注事件，不等于所有轻微不良事件的完整比较。
- PDF pp.8–12（Discussion）：作者承认这是高风险既往 CVD 人群，且结果来自特定剂量、特定人群和标准治疗背景；讨论了体重、血压、脂质和炎症等可能通路，但试验不是机制试验。论文不能证明“独立于减重的直接护心”这一强命题。
- Supplementary Appendix：NEJM 页面列出正式 appendix 和 protocol；NEJM 站点和直接 PDF 在本机与网页访问均返回 HTTP 403。本轮没有把未能取得的 appendix 当作已读全文；其已得信息以主论文、FDA 标签、ClinicalTrials.gov 和 NICE 公开证据包交叉核对，并在 manifest 记录阻断。

## ClinicalTrials.gov：注册和结果入口

[NCT03574597](https://clinicaltrials.gov/study/NCT03574597) API JSON 下载 SHA-256 `382f8e74a9c1f777c3472281baa46d64960f6a758b0343df1a320665b05ef229`。

- `protocolSection.statusModule`：2018-10-24 开始，2023-06-29 完成；结果于 2024-08-30 发布；登记机构 Novo Nordisk A/S。
- `designModule`：Phase 3、随机平行、四重盲法、实际入组 17,604。
- `eligibilityModule`：年龄、BMI、既往 MI／卒中／有症状 PAD 和糖尿病排除条件与论文一致。
- `outcomesModule`：主要终点时间窗登记为随机化至 240 周，定义为 in-trial observation；full analysis set 按随机分配分析；主要结果记录 569 对 701，Cox HR 0.80。
- 注册结果仍不能替代论文 appendix：它提供了登记分母、终点定义和主要计数，但没有解决所有事件判定、停药原因和安全定向收集的完整上下文。

## FDA：监管原文

FDA 现行 [Wegovy 处方信息](https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/215256s029lbl.pdf)，67 页，修订 2026-03，SHA-256 `d1c4cdb753e295a682505203bf470882161d5d23735ca1e30ff28470cca9cc6e`。

- PDF pp.1–4，Sections 1–2：注射剂适应证为配合低热量饮食和增加活动，降低已有 CVD 且肥胖或超重成人的 CV 死亡、非致死 MI 或非致死卒中风险；心血管风险降低的注射维持剂量为 2.4 mg（推荐）或 1.7 mg 每周一次；不得与其他含司美格鲁肽产品或其他 GLP-1 受体激动剂联用。现行标签还包含口服剂型的新内容，本研究的 SELECT 证据只支持注射剂路线，不能把口服剂型的新剂量混入 SELECT。
- PDF p.26，Section 14.1：FDA 将 Study 1 明确标为多国、多中心、安慰剂对照、双盲、加标准治疗的 CV 试验；16 周递增至 2.4 mg；排除 1/2 型糖尿病。标准治疗包括风险因素管理和个体化生活方式咨询。
- PDF pp.27–28，Section 14.1、Table 6：平均年龄 62 岁，72% 男性，84% White，4% Black，8% Asian，10% Hispanic；既往 MI 76%、卒中 23%、PAD 9%、心衰 24%；96.9% 完成，生命状态 99.4% 可得；中位随访 41.8 月；永久停药 31% 对 27%；1 年在治疗者 76% 达 2.4 mg，2 年 77% 达 2.4 mg。表 6 重现 MACE 701/8801 对 569/8803，HR 0.80；并注明 CV 死亡的层级优效未确认，心衰作用尚未建立。
- PDF p.28，Table 7：104 周体重变化约 −0.93% 对 −9.43%，血压 −0.5 对 −3.8 mmHg，心率 +0.7 对 +3.8 bpm；这些是支持性代谢结果，不是 MACE 机制分解。
- PDF pp.1、8–11、49：标签警告包括甲状腺 C 细胞肿瘤黑框、胰腺炎、胆囊病、容量耗竭导致的急性肾损伤、严重胃肠道反应、过敏、糖尿病视网膜病变、心率增加和麻醉／深度镇静时肺吸入。成人减重试验的严重胃肠道不良反应为 4.1% 对 0.9%；这不是 SELECT 的同一观察集，不能直接代入 SELECT 风险。
- FDA [2024-03-08 批准公告](https://www.fda.gov/news-events/press-announcements/fda-approves-first-treatment-reduce-risk-serious-heart-problems-specifically-adults-obesity-or)：网页明确写出适应证只针对已有 CVD 且超重／肥胖成人，并复述 6.5% 对 8.0% 与风险警告；公告是监管来源链，标签是具体剂量和安全细节的承重原文。

## NICE：正式 HTA 与证据包

正式 [TA1152 guidance](https://www.nice.org.uk/guidance/ta1152)，从 NCBI Bookshelf 下载 19 页 PDF，SHA-256 `e3db155290d907c77887d595b0e668903f4215dbfa017ecd5d8d9dc3138cf54e`。

- 正式 guidance PDF p.4，Recommendation 1.1：NICE 限定为已有 CVD（既往 MI、缺血性或出血性卒中、或符合定义的有症状 PAD）且 BMI≥27 kg/m² 成人；配合低热量饮食和增加活动，最高维持 2.4 mg 每周一次。它是“secondary prevention”定位，不是无既往 CVD 人群的一级预防推荐。
- p.5，Why this recommendation：NICE 的临床理由是 SELECT 中司美格鲁肽+标准治疗相对于安慰剂+标准治疗降低 MACE；经济理由是成本效果在可接受范围。NICE 不把这个推荐写成整个 GLP-1 类的类效应。
- pp.8–10，Discussion 3.1–3.4：NICE 明确主要证据是 SELECT；STEP-HFpEF／STEP-HFpEF DM 没有直接相关 MACE 结果；SELECT 排除糖尿病，但 NICE 依据 4 个不同剂量／路线／人群的糖尿病 CVOT 认为对糖尿病人群可能可推广，同时承认这些证据存在局限。这里是正式 HTA 的外推判断，不是 SELECT 的直接随机结果。
- p.10，Discussion 3.4：糖尿病外推来自不同剂量、给药路线和没有相同既往 CVD／BMI 入口标准的试验，因而不能写成 SELECT 在糖尿病人群中已直接复制。
- pp.10–11，Discussion 3.5：SELECT 排除筛查前 60 日内 MI、卒中、TIA 或不稳定心绞痛住院者；NICE 认为早期曲线分离使近期事件人群外推“plausible”，但这仍是外推，不是试验内证据。
- pp.12–14，Discussion 3.6–3.9：经济模型包括部分未达统计显著的终点；EAG 对治疗停止率恒定外推和试验后事件风险调整提出不确定性；NICE 认为这些不确定性不改变成本效果决定，但它们确实限制了长期净获益的精确度。

公开 [NICE committee papers](https://www.nice.org.uk/guidance/ta1152/evidence/committee-papers-pdf-15676237117) 8.24 MB、466 页，SHA-256 `6c115d25d14ced7079b6f634e181d1fad2eea0c8c79af80d861e5ecad9efc624`。它含公司提交、外部评估和有 `xxxxx` 保密遮盖的材料，不能把公司叙述当作独立来源；本轮用其公开页码作方法和模型审计：PDF pp.52–56（SELECT 设计、估计量、资格）、pp.64–72（统计和 MACE）、pp.110–115（安全、解释和局限）、pp.166–170（长期经济情景）。

## 安全性与机制边界：同一 SELECT 队列的二次分析

1. [Safety profile of semaglutide versus placebo in SELECT](https://pmc.ncbi.nlm.nih.gov/articles/PMC11897845/)，通过 Europe PMC FullText XML 获取，SHA-256 `ff1e14d02725e1c73ad1348028a9e65038548cce1eadfaae7df6112270f2c6f4`。摘要和 Results／Discussion：SAE 33.4% 对 36.4%；停药 16.6% 对 8.2%；胃肠道停药 10.0% 对 2.0%；严重不良事件导致停药 3.6% 对 4.1%；胆囊相关 2.8% 对 2.3%，主要为胆石 1.4% 对 1.1%；自杀／自伤 SAE 0.11% 对 0.11%。作者明确警告，SELECT 排除了慢性胰腺炎、近五年恶性肿瘤和严重精神障碍，因此不能把安全性无条件外推到这些人群；跨 STEP／SUSTAIN-6 的百分比还受随访时长和人群差异影响。
2. [Semaglutide and cardiovascular outcomes by baseline HbA1c and change in HbA1c](https://pmc.ncbi.nlm.nih.gov/articles/PMC11282385/)，通过 Europe PMC FullText XML 获取，SHA-256 `079e53096b49c535354d3f75eb7b50f3477fb6bc98d73364ced6f3788a164b4e`。Results／Statistical Methods：17,604 人按基线 HbA1c `<5.7%`、`5.7–<6.0%`、`6.0–<6.5%` 分层，基线 HbA1c 和到第 20 周变化的交互没有显示 MACE 效果差异；但变化分层是随机化后的变量、事件只在第 20 周后计入，探索性分析的 CI 未作多重性校正。Discussion 的明确限制是结果只适用于既往 CVD、超重／肥胖、无糖尿病人群，不能外推到无既往 CVD 的人。

## 主动反方／机制挑战

[Semaglutide and cardiovascular outcomes by baseline and changes in adiposity measurements](https://www.sciencedirect.com/science/article/pii/S0140673625013753)，The Lancet 2025;406:2257–2268，摘要和公开 repository record 已读；期刊正文／repository PDF 下载尝试返回 HTTP 403，因而没有声称完成逐页全文阅读。可得摘要定位：随机 17,604 人，基线体重每低 5 kg 的 MACE HR 0.96，基线腰围每低 5 cm HR 0.96；司美格鲁肽组第 20 周减重幅度与之后 MACE 无线性趋势；腰围变化约解释观察到的效应 33%，调整时变腰围后 HR 0.86（0.77–0.97）。公开 PDF 搜索摘录的限制段指出：按随机后体重／腰围变化分层存在混杂，不能证明因果或定义机制；样本以白人和男性为主，外推受限。该研究支持“体重以外可能有通路”的候选解释，但不能证明直接药理作用。

[Efficacy of GLP-1 Receptor Agonist-Based Therapies on Cardiovascular Events and Cardiometabolic Parameters in Obese Individuals Without Diabetes](https://pmc.ncbi.nlm.nih.gov/articles/PMC11982705/)，通过 Europe PMC FullText XML 获取，SHA-256 `dd1d42b08ca506b2295cc9a5714ba384f55b8b1b020c45775e1db73a6cb6cf05`。Methods／Results／Risk of Bias／Limitations：截至 2024-06-18 纳入 29 个 RCT、9 种 GLP-1 类药物、37,348 人；总 CV 事件 RR 0.81、MACE RR 0.80、MI RR 0.72、全因死亡 RR 0.81，但 CV 死亡和卒中无显著差异；CV 事件 I²=59%，移除 SELECT 后降到 29%；作者明确说肥胖无糖尿病人群的专门 CVOT 很少，SELECT 是 MI 和全因死亡结果的主要贡献者，代谢指标不能替代硬结局，需更多专门 CVOT。它是独立于 SELECT 主论文的研究综合，但纳入的多个试验并非独立于 SELECT 的新随机证据，所以用于限定而非“复制证明”。

## 绝对风险和近似 NNT 的边界

原始分母和事件数为 `semaglutide 569/8803`、`placebo 701/8801`。本轮独立脚本计算：粗事件比例分别为 0.0646371 和 0.0796500；粗绝对风险差（安慰剂减司美格鲁肽）为 0.0150130（约 1.50 个百分点）；`1/ARR = 66.609`，向上取整为约 67。该值只代表 SELECT 的 in-trial 观察窗中从随机化到末次随访的粗比例差的近似 NNT，不能替代 Aalen–Johansen 在某个固定月数的累积发生率，也不能外推成 5 年、终身或个人 NNT。由于主要终点包含 CV 死亡、非致死 MI、非致死卒中，不能把 1.50 个百分点解释为每个组成部分的同幅度获益。

## 本阶段证据上限

1. SELECT 的随机证据支持窄命题：在无糖尿病、年龄至少 45 岁、BMI≥27 kg/m²、既往 MI／卒中／有症状 PAD 的成人中，司美格鲁肽注射剂 2.4 mg 每周一次加标准治疗，在试验内观察窗降低首次三点 MACE。
2. 绝对获益约 1.50 个百分点、粗近似 NNT 约 67，但随访不是固定时点风险，且停药和剂量达成率使“持续 2.4 mg 治疗”的口语化解释不准确。
3. CV 死亡和卒中单项 CI 跨 1；层级检验在 CV 死亡处停止，不能把 MACE 的显著性传播为所有组成部分或所有次要终点均已确认。
4. FDA 和 NICE 都把适应证／推荐限定在已有 CVD 和 BMI≥27；NICE 对糖尿病和近期事件的扩展是有条件的 HTA 外推，不是 SELECT 的直接复制。无既往 CVD 的一级预防、正常 BMI 人群、所有 GLP-1RA、替尔泊肽或其他双／三重激动剂均不能由本轮直接随机证据推出同等相对或绝对获益。
5. “独立于减重”只能作为关联和机制候选；SELECT 不是机制试验，随机后减重／腰围分层有混杂，不能升级为已证明的直接心血管药理效应。
