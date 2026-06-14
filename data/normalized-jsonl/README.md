# 项目级规范化 JSONL 数据层 / Project-level Normalized JSONL Data Layer

中文：本目录是《点火》仓库的正式机器可读数据层，不是单独为得到大脑创建的适配层。得到大脑只是揭示了 JSONL 对机器逐行读取和批量碰撞分析更友好。
English: This directory is the formal machine-readable data layer of the Ignition repository. It is not an adapter created only for Get Brain; Get Brain merely revealed that JSONL is friendlier for machine line-by-line reading and batch collision analysis.

中文：数据结构不是目的，一致性才是目的。
English: Data structure is not the goal; consistency is the goal.

## 内容 / Contents

- `functions.jsonl` — 函数 / Functions
- `cases.jsonl` — 案例 / Cases
- `effect-leads.jsonl` — 效果线索 / Effect Leads
- `manifest.json` — 清单 / Manifest
- `schema/` — JSON Schema 定义

## 生成 / Generation

所有 JSONL 由脚本从 canonical 数据生成：

```bash
python3 scripts/build_normalized_jsonl_layer_minimal.py --all
```

## 校验 / Validation

```bash
python3 scripts/validate_normalized_jsonl_layer_minimal.py --check
python3 scripts/check_jsonl_canonical_consistency_minimal.py --check
```

## 规则 / Rules

1. 不修改 canonical 数据。
2. 不写死数量。
3. 每行一个完整 JSON 对象。
4. 每行必须包含 `canonical_source`, `schema_version`, `generated_at`, `source_commit`, `source_sha`, `inference_not_conclusion`。
