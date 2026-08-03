# 004 证据笔记

## 访问和版本

本项 evidence 阶段实际打开了 Ember 2026 报告（镜像 PDF，仅为直链 403 时的同一报告公开副本）、Ember 当前年度 CSV 与数据页面、IEA 2026 报告、IEA 两个公开图表页面、OWID 数据解读和 AP 编辑报道。报告和网页的阅读时间分散在 10:36—10:46 Asia/Shanghai；具体访问级别、定位和哈希见 `SOURCE-AUDIT.jsonl` 与 `ACCESS-AND-HASH-MANIFEST.json`。

IEA 的 Global Energy Review Dataset 产品页确实声明含 2023—2025 的世界聚合数据，但下载链接要求登录／账户会话；本次没有绕过该门槛。IEA 公开的 CC BY 4.0 图表页把所需生成分类以 `data-chart-csv` 嵌入 HTML，因此可合法提取并重算发电源项；精确需求字段仍只使用公开报告的“around 800 TWh”表述，不能伪装成已取得 IEA XLSX。

## Ember 原始报告与当前数据

Ember 报告 PDF p. 9 明确写出 April release 的 `low-carbon +887 TWh`、需求 `+849 TWh`、化石 `-38 TWh`；p. 13 分解为太阳能 `+636`、风能 `+205`、合计 `+841`，并称其他低碳源再增 `46`；p. 17 写煤 `-63`、其他化石 `-12`、气 `+36`。p. 113—114 说明 2025 年是由月度发电估算、需求是发电加净进口且不含输配损耗，并警告数据可能修订；同时把 clean/low-carbon 定义为可再生加核电。

重新下载的 Ember 当前全球 CSV（页面标明 2026 年 7 月格式更新）给出 World 行：

| 口径 | 2024 | 2025 | 增量 |
|---|---:|---:|---:|
| Total generation / Demand | 30,906.114 | 31,739.347 | +833.233 |
| Renewables | 9,873.924 | 10,719.014 | +845.090 |
| Nuclear | 2,777.400 | 2,810.802 | +33.402 |
| Clean (= renewables + nuclear) | 12,651.324 | 13,529.815 | +878.491 |
| Coal | 10,536.025 | 10,493.817 | -42.208 |
| Gas | 6,880.140 | 6,908.601 | +28.461 |
| Other fossil | 838.625 | 807.113 | -31.512 |
| Fossil | 18,254.790 | 18,209.532 | -45.258 |

因此当前 CSV 仍支持年度全球 `clean > demand`，但不是把 R1 的 887/849 原样搬运：当前差额为 `878.491 - 833.233 = +45.258 TWh`。当前下载没有独立 `Oil` 行；只能说 `Other fossil` 下降，不能把整行精确改名为油。

## IEA 原始图表与报告

IEA 报告 p. 5 和 Electricity supply 页面写：2025 全球发电增加超过 850 TWh；太阳能增加约 600 TWh；可再生加核电超过总发电增量；煤约 -0.5%、气约 +0.5%、油约 -1.5%。公开生成图表的 2024→2025 行相加为：

- 2024 generation = 10,906.7 + 6,783.1 + 755.4 + 9,946.8 + 2,824.2 = 31,216.2 TWh；
- 2025 generation = 10,857.9 + 6,821.8 + 742.4 + 10,807.8 + 2,858.5 = 32,088.4 TWh；
- chart-based total increment = +872.2 TWh；
- renewable increment = 600.2 + 198.9 + 9.9 + 51.9 = +860.9 TWh；
- nuclear increment = +34.2 TWh；low-emissions = +895.1 TWh；
- fossil increment = -48.8 + 38.8 - 13.0 = -23.0 TWh.

图表数值为一位小数，故合计存在 0.1 TWh 级的显示误差。IEA 这套公开图表与 Ember 当前 CSV 的方向相同，但绝对变化不同；这不是“同一数字被二次确认”。IEA 报告 p. 5 还写全能源需求增长 1.3%、能源相关 CO2 增长约 0.4%，构成对“整个能源系统已脱离化石”的直接边界约束。

## 口径 crosswalk

Ember：`Clean/low-carbon = Renewables + Nuclear`；`Renewables = Solar + Wind + Hydro + Bioenergy + Other renewables`；`Fossil = Coal + Gas + Other fossil`。报告说 `Other fossil` mostly oil，但当前 CSV 不给独立油列。

IEA：`Low-emissions = Renewables + Nuclear`；其 renewables 注释含太阳能、风、水电、地热、生物能源／废物、CSP 和海洋能源；公开年变图表另列 Oil。两者的名称可建立语义近似 crosswalk，但底层估算、更新日和分类细节不同，不能强行逐项相减。

## R1 → R2 数字变化

R1 把 Ember April 报告的 887/849 当作当前值，并没有发现 July CSV 的 878.491/833.233。R2 证明了 R1 方向判断在当前 Ember 表中仍成立，但数字和煤／气／其他化石分解已经改变。这个变化可由版本／估算修订解释为可能原因，但本项没有审计 Ember 内部修订历史，所以不把原因写成已证明的因果。
