# Function asset authority overlay

This directory extends the existing Foundation registries; it is not a parallel truth system.

Authority order for function identity and claim scope is:

1. `corrections.jsonl` for the explicitly adjudicated task 98 records;
2. existing Foundation source-text adjudications and formal objects;
3. task-99 `identity-cards.jsonl` repository-evidence adjudications and explicit quarantine;
4. `census.jsonl` automatic discovery candidates;
5. preserved legacy source text.

`build_function_asset_census.py` discovers all tracked textual sources, consolidates explicit identifiers and implicit named candidates, emits dependency edges and a resumable queue, and marks automatic labels `AUTO_CANDIDATE`. An automatic candidate never overrides a human adjudication.

The two ratings are independent: M0–M7 measures mathematical maturity and E0–E7 measures external evidence. No inference from M to E is permitted.

Registry closure means one card and one disposition per discovery. It does not mean proof or empirical completion. `closure-summary.json` is the count authority; `proof-empirical-obligations.jsonl`, `unresolved-quarantine.jsonl`, `dependency-closure.jsonl`, `public-claim-lineage.jsonl` and `semantic-rebound-report.jsonl` preserve the open work and public boundary.
