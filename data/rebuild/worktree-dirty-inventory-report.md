# 工作区脏文件清单报告 / Worktree Dirty Inventory Report

- HEAD: `fbb8a54`
- Branch: `main`
- total_dirty_items: 27
- unrelated_dirty_items: 7
- unknown_items: 2
- prior_dirty_commit: None
- unknown_items_left_unstaged: 2
- unrelated_dirty_files_left_unstaged: 7

## 条目 / Items

| status | category | path | appeared_before_current_run | safe_to_commit_now | recommended_action |
|---|---|---|---:|---:|---|
| M | normalized_jsonl_related | `AGENT_ENTRY.md` | true | true | include_in_current_commit |
| M | normalized_jsonl_related | `data/normalized-jsonl/README.md` | true | true | include_in_current_commit |
| M | get_note_dirty | `data/rebuild/get-note-0000-sync-report.json` | true | false | leave_unstaged |
| M | link_entry_dirty | `data/rebuild/link-entry-merge-report.json` | true | false | leave_unstaged |
| M | link_entry_dirty | `data/rebuild/link-entry-merge-report.md` | true | false | leave_unstaged |
| M | entailment_dirty | `data/rebuild/no-function-case-entailment-scan-report.json` | true | false | leave_unstaged |
| M | entailment_dirty | `data/rebuild/no-function-case-entailment-scan-report.md` | true | false | leave_unstaged |
| M | normalized_jsonl_related | `llms.txt` | true | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/normalized-jsonl/baseline.json` | false | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/rebuild/normalized-jsonl-final-audit-report.json` | false | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/rebuild/normalized-jsonl-final-audit-report.md` | false | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/rebuild/normalized-jsonl-final-validation-report.json` | false | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/rebuild/normalized-jsonl-final-validation-report.md` | false | true | include_in_current_commit |
| ?? | unknown | `data/rebuild/pre-eff-identity-audit-dirty-worktree-status.txt` | true | false | needs_user_review |
| ?? | unknown | `data/rebuild/pre-eff-identity-audit-dirty-worktree.patch` | true | false | needs_user_review |
| ?? | current_inventory_artifact | `data/rebuild/recovery/dirty-inventory-diff-stat.txt` | true | true | include_in_current_commit |
| ?? | current_inventory_artifact | `data/rebuild/recovery/dirty-inventory-head.txt` | true | true | include_in_current_commit |
| ?? | current_inventory_artifact | `data/rebuild/recovery/dirty-inventory-status.txt` | true | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `data/rebuild/recovery/pre-normalized-jsonl-phase-b-diff-stat.txt` | true | false | leave_unstaged |
| ?? | normalized_jsonl_related | `data/rebuild/recovery/pre-normalized-jsonl-phase-b-status.txt` | true | false | leave_unstaged |
| ?? | normalized_jsonl_related | `data/rebuild/recovery/pre-normalized-jsonl-recovery.patch` | true | false | leave_unstaged |
| ?? | current_inventory_artifact | `data/rebuild/worktree-dirty-inventory-report.json` | true | true | include_in_current_commit |
| ?? | current_inventory_artifact | `data/rebuild/worktree-dirty-inventory-report.md` | true | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `scripts/check_normalized_jsonl_baseline.py` | true | true | include_in_current_commit |
| ?? | current_inventory_artifact | `scripts/inventory_dirty_worktree.py` | true | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `scripts/validate_normalized_jsonl_all.py` | true | true | include_in_current_commit |
| ?? | normalized_jsonl_related | `scripts/validate_project_identity_lock.py` | true | true | include_in_current_commit |

## 安全边界 / Safety

- 未删除文件 / No files discarded
- 未暂存文件 / No files staged by this script
- 未提交 / No commit executed by this script
- 未推送 / No push executed by this script
- 未写入完整 diff / No full diff written
- 未读取敏感环境文件内容 / No sensitive env file content read
