# 004 分析方法

## 输入锁定

分析使用两个不混合的输入集：

1. Ember 当前公开全球 CSV 的 `Area=World`、`Year=2024/2025` 行。直接使用 `Generation (TWh)`，并分别计算 2025 减 2024；对 `Clean`、`Renewables`、`Fossil` 等 aggregate row 做一致性检查。
2. IEA 公开图表 HTML 中的 CC BY 4.0 `data-chart-csv`：一个是 2015—2025 的五类 generation 表，一个是 2024—2025 source-change 表。先按图表自己的类别求和，再计算差值；不把 IEA 图表的“generation”替换成 Ember 的 “demand”。

运行入口是 `reproducibility/recompute_004.py`，只依赖 Python 标准库。它重新下载输入、保存小型提取表、写 `recomputed_metrics.json` 和下载哈希。报告全文不进入仓库；完整本地文件的哈希在 `ACCESS-AND-HASH-MANIFEST.json`。

## 估计量

对每个数据集计算：

`Δsource = value(2025) - value(2024)`

`coverage_margin = Δclean_or_low_emissions - Δdemand_or_total_generation`

`Δfossil = Σ(Δcoal, Δgas, Δoil_or_other_fossil)`

Ember 的 `Clean` 与 `Fossil` aggregate row 作为数据集提供的审计结果，同时用 Renewables + Nuclear、Coal + Gas + Other fossil 复算；当前公开 CSV 没有独立 Oil 行，所以不把 `Other fossil` 全部重命名为 Oil。IEA 只报告 chart precision（一位小数），所有跨来源差异保留为版本／定义差异而不是假设精确等同。

## 口径边界

`annual_global_power` 是唯一主估计层。`regional_or_hourly_matching`、`capacity_reliability` 和 `whole_energy_system` 只作为外部推断检查，不从本分析中生成数值结论。IEA 报告的全能源需求和 CO2 只用于证明电力年度平衡不能外推成全能源化石下降。

## 验证检查

- Ember current CSV 的 `Clean` 增量与 `Renewables + Nuclear` 相差仅为显示精度内的 0.001 TWh；`Fossil` 增量与 `Coal + Gas + Other fossil` 一致。
- IEA source-change table 的 renewable sum、low-emissions sum 和 fossil sum由脚本直接生成，且与 source-level rows 一致。
- 计算结果不使用搜索摘要、新闻或 R1 数字作为输入；OWID/AP 只作为依赖链和传播误差的审计对象。
