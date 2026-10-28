# Get Brain Latest Status Protocol

## Purpose

This repository keeps exactly one current entry for the latest state that Get Brain should read first.

## Files

- `GET-BRAIN-LATEST.md`
- `data/get-brain/latest-status.json`

## Rules

1. The Markdown file is the reader entry.
2. The JSON file is the machine-readable mirror.
3. The latest entry is overwritten in place, not duplicated by timestamped filename.
4. The entry must never convert open PR content or candidate notes into formal authority.
5. The entry must not contain secrets, tokens, cookies, or Authorization headers.
6. Review status must stay `PENDING_GPT_REVIEW` until GPT explicitly approves it.

