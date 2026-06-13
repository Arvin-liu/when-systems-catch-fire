# Sync Dry Run Report

- generated_at: 2026-06-13T15:15:27.443281+00:00
- dry_run: True

## python3 scripts/build_answers_from_function_projection.py --check
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 0.282

## python3 scripts/normalize_bilingual_labels.py --check
- returncode: 1
- ok: False
- timed_out: False
- duration_s: 7.304

## python3 scripts/validate_ignition_repository.py --quick
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 0.368

## python3 scripts/render_answer_index.py --check
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 0.193

## python3 scripts/render_repository_overview.py --check
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 0.125

## python3 scripts/merge_redundant_entry_links.py --check
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 1.742

## python3 scripts/normalize_attribution_display_name.py --check
- returncode: 0
- ok: True
- timed_out: False
- duration_s: 0.122
