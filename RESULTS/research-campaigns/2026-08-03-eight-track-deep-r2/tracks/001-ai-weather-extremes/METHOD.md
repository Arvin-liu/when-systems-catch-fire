# 001 方法与复算边界

将主论文的纪录定义、ERA5 训练期/测试期、模型版本、网格、提前期、真值和极端评分拆成可比较字段；把 Zhang 的 record-exceedance benchmark、Olivetti–Messori 的 percentile-tail benchmark、Pasche 的事件案例和 WeatherBench2 粗复算作为不同 estimand。公开粗复算只用于检验规则可执行和排名敏感性，不冒充论文原网格复现。完整输入哈希、脚本和输出在 `recalc_weather_001.py` 及 `reproducibility/`；核心分析见 `ANALYSIS.md`。
