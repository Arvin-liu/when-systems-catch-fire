# 项目级规范化 JSONL 数据层 / Project-level Normalized JSONL Data Layer

中文：本目录是《点火》仓库的正式机器可读数据层。
English: This directory is the formal machine-readable data layer of the Ignition repository.

中文：数据结构不是目的，一致性才是目的。
English: Data structure is not the goal; consistency is the goal.

## 内容 / Contents

- `functions.jsonl` — 函数 / Functions
- `cases.jsonl` — 案例 / Cases
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

## 维护规则 / Maintenance Rules

中文：任何对象层的新增、改写、删除，都必须触发 normalized-jsonl 重建与一致性检查。
English: Any addition, rewrite, or deletion in an object layer must trigger normalized-jsonl rebuild and consistency checks.

中文：JSONL 不是外部适配，而是项目正式机器数据层。
English: JSONL is not an external adapter; it is the formal machine-readable data layer of the project.

中文：数据结构不是目的，一致性才是目的。
English: Data structure is not the goal; consistency is the goal.

- `function-case-relations.jsonl` 为 0 行时，必须由诊断报告支持，不得伪造关系。
- `lead` 不等于 `active`，不得把 lead 默认晋级为 active。
