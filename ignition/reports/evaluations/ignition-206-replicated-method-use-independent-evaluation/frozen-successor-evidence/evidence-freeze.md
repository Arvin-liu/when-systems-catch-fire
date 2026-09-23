# Evidence Freeze - IGNITION-20260922-206

Replicated Method-Use R0 Independent Evaluation - Step00 mechanical gate.

- exact base: `867dc2e4f47c3981aa4178d706b6ea6e110379fe`
- evaluator role: Independent Evaluator / Evidence Freezer
- semantic verdict at this step: NOT_RUN (mechanical gate only)
- mechanical gate: PASS

## Per-bundle freeze

| task | condition | replicate | container | branch | local no-commit | remote branch | allowlist | records | schema | copy bytes | contamination |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IGNITION-20260921-200 | FACTS_ONLY | A | 200-FACTS-A | `work/IGNITION-20260921-198-successor-facts-a` | NO_SUCCESSOR_COMMIT | ABSENT | 12 | 3 | PASS | EQUAL | NONE_DETECTED |
| IGNITION-20260921-201 | FACTS_ONLY | B | 201-FACTS-B | `work/IGNITION-20260921-198-successor-facts-b` | NO_SUCCESSOR_COMMIT | ABSENT | 12 | 3 | PASS | EQUAL | WORKTREE_WIPE_ISOLATION_MECHANICALLY_BENIGN |
| IGNITION-20260921-202 | METHOD_TRACE | A | 202-METHOD-A | `work/IGNITION-20260921-198-successor-method-a` | NO_SUCCESSOR_COMMIT | ABSENT | 17 | 3 | PASS | EQUAL | NONE_DETECTED |
| IGNITION-20260921-203 | METHOD_TRACE | B | 203-METHOD-B | `work/IGNITION-20260921-198-successor-method-b` | NO_SUCCESSOR_COMMIT | ABSENT | 17 | 3 | PASS | EQUAL | NONE_DETECTED |
| IGNITION-20260921-204 | BROKEN_METHOD_TRACE_CONTROL | A | 204-BROKEN-A | `work/IGNITION-20260921-198-successor-broken-a` | NO_SUCCESSOR_COMMIT | ABSENT | 15 | 3 | PASS | EQUAL | NONE_DETECTED |
| IGNITION-20260921-205 | BROKEN_METHOD_TRACE_CONTROL | B | 205-BROKEN-B | `work/IGNITION-20260921-198-successor-broken-b` | NO_SUCCESSOR_COMMIT | ABSENT | 15 | 3 | PASS | EQUAL | NONE_DETECTED |

### 200-FACTS-A - FACTS_ONLY / replicate A

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `c6d3c0a4c67c0c1ab28ea5b56da69526a3aef2b21ee53a3b4587e388a252ca1a` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02'] == packet case_order ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `f7f019261deb18f2b12ac91841e935b5ae504030bcbfcd952ceff65988fc0af5` (15357 bytes, source==copy True)
  - `read-manifest.json` `6e4c891e6413f1ee69a997c9e006614cdb33f933c91741f4781f816eb81befa4` (3681 bytes, source==copy True)
  - `freeze-sha256.txt` `3a7c847018adc5ee0e861198efaa8273352725e4535fd8d230770166355179fb` (2736 bytes, source==copy True)
- note: checked-out HEAD 428d1885d0cb on 'main' is an ancestor of exact base (not advanced); successor branch ref == exact base

### 201-FACTS-B - FACTS_ONLY / replicate B

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `3926b9b2085cd7930e26532f9b1f59e75437b8e8c684349922b5ed372d876891` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03'] == packet case_order ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `357e480ba9f5459bce13dc6db3f8724d2f1ac2e0f865a71d65fd44fd2d07f509` (15005 bytes, source==copy True)
  - `read-manifest.json` `a68e1b06d9b28b9322de0f43099699ac3928845f87d8bcb97f92e70a120d8ec1` (3801 bytes, source==copy True)
  - `freeze-sha256.txt` `ed41c74ad92d5d4897b300b34cffbfa04d3eff1ad137ffd81d27e50188b2c9ca` (2643 bytes, source==copy True)
- note: checked-out HEAD 428d1885d0cb on 'main' is an ancestor of exact base (not advanced); successor branch ref == exact base
- note: worktree mutation outside bundle: .github/CONTRIBUTING.md, .github/ISSUE_TEMPLATE/independent-review.yml, .github/ISSUE_TEMPLATE/noncommercial-use-report.yml ...
- note: freeze file declares no per-path allowlist entries (only aggregate hash); per-path equality checked via read-manifest

### 202-METHOD-A - METHOD_TRACE / replicate A

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `65822249c3b008426f69ec12f61a4d5c703d436ed64abf2c199c661f5a57251a` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02'] == packet case_order ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `b2abe7c2eb6ea5081c3e673717b8730a15e20b0c0932f2a0cf4c8a65cfb3edee` (17473 bytes, source==copy True)
  - `read-manifest.json` `812b385f101a70c7b8de125f9d5f46076818058995ec7ccc8ab4ab6f940eac45` (5316 bytes, source==copy True)
  - `freeze-sha256.txt` `6695cf8ba892322d2d75f71d0d2290059c35052824844e0b20636295fbac2303` (782 bytes, source==copy True)
- note: freeze file declares no per-path allowlist entries (only aggregate hash); per-path equality checked via read-manifest

### 203-METHOD-B - METHOD_TRACE / replicate B

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `3f1b6a4fc0eb39393c775210da83de4b5a39a02b572ae171ce028772b8a98ca0` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03'] == packet case_order ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `8da75328fefc27606ac1f4319bacbfd3d61abd13cc5c8748d3880d7498e0b148` (21013 bytes, source==copy True)
  - `read-manifest.json` `2fbb094885dd61c607906496d1953d100b9a0c4c54863290bd3591afda2e9c99` (5318 bytes, source==copy True)
  - `freeze-sha256.txt` `4539670f0a3cbdbac7781f4f663a7b4509a68e866b869369a9c1b93cb24307d2` (3600 bytes, source==copy True)
- note: checked-out HEAD 428d1885d0cb on 'main' is an ancestor of exact base (not advanced); successor branch ref == exact base
- note: freeze file declares no per-path allowlist entries (only aggregate hash); per-path equality checked via read-manifest

### 204-BROKEN-A - BROKEN_METHOD_TRACE_CONTROL / replicate A

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `44b001c0da14f2c5fcb9f237a381dc17aa402b7fe76cee864a61782fbbd9d2af` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02'] == packet case_order ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `722dabef0cd7fb70c4690c36ac40998bad34c0e0069474eafaea00a578db62c8` (15850 bytes, source==copy True)
  - `read-manifest.json` `b9e0fefb46ccac1a330d1cb14ee12680083de2facd1908a30e69c512b39ae4d6` (4796 bytes, source==copy True)
  - `freeze-sha256.txt` `702687b9ca6011c8e902e5f51b68722903cf638a8192361fec0cdf7f224380bb` (3530 bytes, source==copy True)
- note: freeze file declares no per-path allowlist entries (only aggregate hash); per-path equality checked via read-manifest

### 205-BROKEN-B - BROKEN_METHOD_TRACE_CONTROL / replicate B

- branch ref equals exact base: True
- successor commits after base: 0
- packet manifest SHA256: `e3384e79faabe03b44a274775c9ca3a42c3e59badc44a441eaf932600f78fe05` (expected match True)
- read-manifest vs packet read_allowlist exact set equality: True
- unlisted / cross-condition / evaluator-sealed reads: 0 / 0 / 0
- record count: 3; R0.1 schema: PASS
- record order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03'] == packet case_order ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']: True
- packet pins vs exact-base bytes mismatches: 0
- source-copy byte equality: True
- file hashes:
  - `successor-response.jsonl` `b7f7039ffc4d1e009d287c0b88c90093822f67aa2125e5209c06b9b9fc8c9a50` (11150 bytes, source==copy True)
  - `read-manifest.json` `a213b5bc117f7bc3174b1b6b907b73811c81e1f186e2034b67438e386daab5ba` (4659 bytes, source==copy True)
  - `freeze-sha256.txt` `f5bd804582314e58166c3728d8789bb6e290195b299d51f6aabde50aa830402f` (3356 bytes, source==copy True)

## Read-boundary summary

All read-manifest entries: read_channel `cognitive_packet_read`, read_status `READ`, each allowlisted path exactly once, each recorded SHA equal to the packet pin and to the exact-base final bytes. No unlisted, cross-condition or evaluator-sealed read.

## Contamination status

- 200-FACTS-A: NONE_DETECTED
- 201-FACTS-B: WORKTREE_WIPE_ISOLATION_MECHANICALLY_BENIGN: 4358 tracked files staged-deleted (no commit); sole remaining worktree content is the local untracked evidence bundle; branch ref unchanged at exact base; deletion cannot inject evidence and is consistent with read isolation
- 202-METHOD-A: NONE_DETECTED
- 203-METHOD-B: NONE_DETECTED
- 204-BROKEN-A: NONE_DETECTED
- 205-BROKEN-B: NONE_DETECTED

No semantic scoring, no condition comparison and no evaluator-sealed material was read before this checkpoint.
