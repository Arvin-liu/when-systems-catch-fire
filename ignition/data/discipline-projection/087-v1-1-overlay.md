# IGNITION-087 v1.1 Overlay: Architecture Gap Closure

## 概述
基于 UNESCO 250 个四位学科投影到点火 085 冻结架构的压力测试，识别出 14 个架构级缺口。本 overlay 提出可补齐的接口扩展方案。

## 缺口优先级分布
- HIGH: 8 个（干预控制、层级尺度、时间动态、随机不确定性、优化权衡、路径依赖、表示语言、计算复杂度）
- MEDIUM: 6 个（不完备性、测量可观测性、本体论、因果识别、证据制度、反例失败）

## v1.1 新增接口

### 1. InterventionControlInterface (补齐 GAP-001)
- **缺口**: 143/143 学科缺失干预控制接口
- **新增**: `intervention_control` 对象类型，记录干预操作、对照实验设计、因果效应估计
- **schema**: { intervention_type, control_design, effect_estimate, confounders, external_validity }

### 2. LevelScaleInterface (补齐 GAP-002)
- **缺口**: 124/143 学科缺失层级尺度接口
- **新增**: `level_scale` 对象类型，记录跨尺度映射、涌现边界、尺度转换规则
- **schema**: { level_type, scale_range, emergence_boundary, cross_scale_mapping, reduction_limit }

### 3. TemporalDynamicsInterface (补齐 GAP-003)
- **缺口**: 123/143 学科缺失时间动态接口
- **新增**: `temporal_dynamics` 对象类型，记录时间演化、稳态转换、滞后效应
- **schema**: { dynamics_type, timescale, equilibrium, transient_behavior, hysteresis }

### 4. StochasticUncertaintyInterface (补齐 GAP-004)
- **缺口**: 115/143 学科缺失随机不确定性接口
- **新增**: `stochastic_uncertainty` 对象类型，记录不确定性来源、概率模型、敏感性分析
- **schema**: { uncertainty_source, probability_model, sensitivity, confidence_interval, bayesian_prior }

### 5. OptimizationTradeoffInterface (补齐 GAP-005)
- **缺口**: 135/143 学科缺失优化权衡接口
- **新增**: `optimization_tradeoff` 对象类型，记录多目标优化、Pareto 前沿、约束条件
- **schema**: { objectives, constraints, pareto_frontier, tradeoff_quantification, optimality_condition }

### 6. PathDependenceInterface (补齐 GAP-006)
- **缺口**: 135/143 学科缺失路径依赖接口
- **新增**: `path_dependence` 对象类型，记录历史依赖、锁定效应、临界点
- **schema**: { history_dependency, lock_in_effect, tipping_point, irreversibility, contingency }

### 7. RepresentationLanguageInterface (补齐 GAP-007)
- **缺口**: 91/143 学科缺失表示语言接口
- **新增**: `representation_language` 对象类型，记录形式化语言、语义映射、表达力边界
- **schema**: { language_type, expressiveness, semantic_mapping, syntax_rules, undecidable_problems }

### 8. ComputationalComplexityInterface (补齐 GAP-008)
- **缺口**: 108/143 学科缺失计算复杂度接口
- **新增**: `computational_complexity` 对象类型，记录算法复杂度、可计算性边界、近似策略
- **schema**: { complexity_class, computability_boundary, approximation_scheme, hardness_proof, reduction }

## 保持 pending 的缺口（不补齐）
- GAP-009 不完备性与不可判定: 102/143 已 PARTIAL，保持现有 G_δ 组件
- GAP-010 测量与可观测性: 83/143 已 PARTIAL，保持现有 evidence obligation interface
- GAP-011~014: 全部 PARTIAL，保持现有组件，不做 v1.1 扩展

## 禁止事项
- 不修改 085 frozen v1 文件
- 不修改统一函数总表和统一案例总表
- 不合并或关闭任何 PR
- 不将投影称为同构或真值证明
