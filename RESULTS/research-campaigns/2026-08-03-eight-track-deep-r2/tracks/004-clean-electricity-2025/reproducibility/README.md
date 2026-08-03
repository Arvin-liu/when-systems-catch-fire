# 004 重算说明

`recompute_004.py` 只使用标准库：它重新下载 Ember 全球年度 CSV，并从 IEA 两个公开 CC BY 4.0 图表页面提取嵌入的年度表；随后把 Ember 的 World 行与 IEA 的图表值分别计算成增量。完整 Ember 下载文件和 IEA HTML 保留在本地运行环境中并以 SHA-256 记录，仓库只提交可再生成的 2024/2025 小型提取表和结果，避免把整份报告或不必要的全文复制进成果包。

运行：

```text
python3 recompute_004.py
```

输出 `output/recomputed_metrics.json` 和 `output/download-manifest.json`。结果以 TWh 表示；Ember 当前 CSV 的 `Other fossil` 是其公开数据的合并行，不能被错误地写成单独油电数字。
