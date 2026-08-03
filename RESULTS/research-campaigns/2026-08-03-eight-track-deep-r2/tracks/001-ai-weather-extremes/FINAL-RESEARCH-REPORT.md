# 001 AI天气极端事件：基准与方法审计

## 结论

最终裁定：`SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`。

跨 benchmark 裁定：`CONTEXT_DEPENDENT_COMPETING_BENCHMARKS`。

Zhang 等人的承重论文支持一个明确而有价值、但边界很窄的结论：在其指定的模型版本、ERA5 真值、1979–2017 训练史、2018/2020 测试期、逐网格逐月严格历史纪录超越定义，以及相应的 lead/event 评分下，ECMWF HRES 在极端纪录子集上通常优于所比较的纯数据驱动模型。论文同时报告 AI 预测对纪录强度的负偏差、纪录发生率/召回不足，以及平均 RMSE 与纪录 RMSE 方向相反的现象。这一结果可以保留为“特定 reanalysis-record benchmark 的支持性结果”。

它不能升级为“AI 天气模型普遍不如物理模型”。独立的 Olivetti–Messori 研究使用 top-1%/top-5% 分位数极端、1.5° 公共网格和不同的模型/区域/lead 组合，发现数据驱动模型在平均误差上常有优势、在不少极端设置中具有竞争力，但区域和事件类型依赖明显。Pasche 等人的三个事件也呈现混合结果：太平洋西北热浪局部可比，北美冬季风暴和南亚湿热复合指标暴露出明显短板。两组研究不是对 Zhang 的同一文件做重复计算，而是证明“极端”存在不同 estimand；它们足以否定普遍排名，却不足以抹掉承重论文自身的 benchmark 结果。

## 可复算检查

我从 WeatherBench2 官方公开 Zarr 读取了 ERA5、HRES 和 Pangu 数据，在 64×32 网格上重建了 Zhang 风格的逐网格逐月 1979–2017 最大值，并对 2020 严格超越事件应用 `land_sea_mask > 0.5` 与纬度 > −60° 的掩膜。阈值规则给出 349 个掩膜后的 land-grid exceedances；不加掩膜为 2,674 个 gridpoint exceedances。随后对公开 2020 HRES/Pangu 预测计算 2-m temperature record-subset RMSE：

| 提前期 | HRES | Pangu |
| --- | ---: | ---: |
| 24 h | 1.438 K | 0.676 K |
| 48 h | 1.564 K | 1.060 K |
| 120 h | 2.626 K | 2.635 K |

这个公开粗网格检查与 Zhang 的 headline ordering 不同，正是为什么不能把一个 benchmark 的结果推广成普遍规律。它也不是原论文 0.25° 结果的复现：公开数据的网格、模型 release、初始化/字段对齐、事件聚合和可复现代码表均不完全相同。因此它的正确用途是验证规则可执行、暴露 ranking 对 benchmark 设计的敏感性，而不是宣布 Pangu 普遍胜出。

## 方法判断

“纪录”在主论文中是相对于 ERA5 训练历史的严格超越，不等于站点观测意义上的全球物理纪录。网格点之间还会重复表示同一热浪、寒潮或风暴；论文提供 bootstrap 和替代窗口检查，但不能把 gridpoint 数当成独立灾害数。ERA5、HRES 和各 AI 模型的训练材料、分辨率、初值、版本和后处理也不能被该设计完全拆分识别。因此可以报告经验排序，不能把它解释成“物理约束本身导致胜出”。

FastNet 的物理引导损失提供了合理的下一步方法方向，并在技术论文的 holdout/案例中改善物理或谱一致性，但仍是 proof-of-principle、非运营系统、非独立前瞻预警试验。ECMWF review、RealBench 方法设计和公开 WeatherBench2 数据都指向同一个尚未闭合的缺口：reanalysis/grid benchmark 与站点、运营输入、决策阈值和真实漏报代价之间仍有一层验证。

## 允许与不允许的表述

允许：

> 在 Zhang 等人的严格 ERA5 历史纪录 benchmark 中，HRES 在所比较的纯 AI 模型之上表现更好；跨研究证据表明该优势依赖极端定义、区域、lead、变量、真值与模型版本。

不允许：

- “AI 天气模型在极端天气上普遍失败”；
- “物理模型已经被证明普遍优于 AI”；
- “FastNet 或任何本轮来源已经证明 AI 可以/不能替代 NWP”；
- “reanalysis record-gridpoint 的分数等于真实站点预警能力”。

本报告仍是待 GPT 逐项审定的研究候选，不进入正式知识或项目状态。
