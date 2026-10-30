# 五材料收讫 / Five-Material Receipt

Draft production-layer receipt for the five control materials processed by
`tools/ignition_runtime` (branch `production/ignition-run-promote-evolve-r1`).
This is a build artifact, not a merged/current result, and embeds no live HEAD.

## Control set

The runtime ingests five materials via `FixtureProvider` (deterministic) and,
when control inputs are present, `FileSystemProvider` (real `.md` files). The
original upload digest is a fixed external attestation and is reproduced verbatim
from the control `INPUT_INDEX.md`; the runtime never recomputes or claims it as
its own final head.

- original upload SHA-256:
  `e50e847056e5089a3f1fb3c9d58309db677b61c2267a66f63574484b93df94f7`

## M1 — M4 (PRIMARY / mixed; deterministic 7/8/5)

Curated so RUN yields exactly 7 ACTIVE candidates, 8 UNKNOWNs, 5 engineering
signals (verified by `test_s39`):

| Material | Tier | Candidates | UNKNOWNs | Signals |
|----------|------|-----------|----------|---------|
| M1 | `PRIMARY_REPORT` | 2 (alpha, beta) | 2 | 1 |
| M2 | `PRIMARY_REPORT` | 2 (gamma, delta) | 2 | 1 |
| M3 | `PRIMARY_REPORT` | 2 (epsilon, zeta) | 2 | 1 |
| M4 | `SECONDARY_ACADEMIC_INTERPRETATION` | 1 (eta) | 2 | 2 |
| **Total** | — | **7** | **8** | **5** |

Source binding: every ACTIVE candidate binds to its material `source_sha256`;
`semantic_id = sha256(source_sha | normalized_claim)` is stable across provider
reorder (`test_s20`). Source change tombstones the stale `semantic_id`
(`REPLACED`); a revert reactivates it (`ACTIVE`) exactly once (`test_s21`,
`test_s22`).

## M5 — SECONDARY source / temporal calibration

M5 is a QC-MHM temporal KGQA reprint held as a **normalized transcript copy** (not
byte-identical). The runtime classifies it and never changes the production
architecture:

- `source_tier`: `SECONDARY_ACADEMIC_INTERPRETATION`
- `verdict`: `NORMALIZED_TRANSCRIPT_COPY`
- `normalized_transcript_copy`: `true`
- `temporal_calibration`: `R_TQ_01..R_TQ_06` all `true`
- A SOTA / originality / root-cure claim is **downgraded to UNKNOWN** (not
  primary-verified) — verified by `test_s40`.

## Epistemic ceiling discipline

Claim ceilings are bounded to `PRIMARY_VERIFIED` / `SECONDARY` / `UNKNOWN`. Any
arbitrary ceiling (e.g. `ROOT_CURE_ABSOLUTE`) is rejected (`test_s19`). No
`run` auto-promotes to formal knowledge and no `run` auto-triggers EVOLVE
(`test_s36`, `test_s37`, `test_s39` assert `formal_promotions == 0` and
`auto_evolve == 0`).

## Receipt identity

Every committed generation carries a `receipt.json` with
`self_final_sha_claimed=false` and `live_refetch_required=true`; the live tip is
never embedded as a final head in any committed file (`test_s45`). Recovery is
strict: a corrupt current generation yields the last closed-manifest-valid
generation, never a silent empty ledger.

## Build provenance (one-time fix, agent F)

- Previous HEAD: `c9253154b36af1ded3f973bd13b44a99f23984b9`
- New HEAD: the tip of `production/ignition-run-promote-evolve-r1` (this fix
  commit). Exact 40-char sha is verifiable via `git rev-parse HEAD` and is
  recorded in `/tmp/agent-work/F_fix_report.md`.

### Fixes applied in this commit

- **G2b / G3 / G8 (load-path binding).** A generation directory name and its
  manifest `generation_id` must both equal the content-derived `gen_id`
  recomputed on every load with the same function used at publish
  (`parent + op + materials + results + ledgers digests`); a mismatch raises
  `GenerationIntegrityError`. This guarantees crash consistency, complete-set
  validation, and fail-closed behavior against accidental corruption and
  non-coordinated tampering. It does **NOT** claim resistance against an attacker
  holding full local store write permission; cross-trust-boundary authenticity is
  borne by external Git commit, remote refetch, and evidence anchors.
- **H B1 (provider-identity).** Provider-identity incoherence now fails closed for
  **all** schemes (including `fixture://`), not only `upload://`. Provider
  identity/tier remain self-asserted; the runtime does NOT claim to authenticate
  providers — provenance authenticity requires out-of-band trust (external
  refetch / evidence anchors).
- **H W2 (beyond-ceiling).** The beyond-ceiling guard normalizes claim text
  (unicode NFKC, lowercase, strip whitespace/punctuation separators) before
  substring matching. It is a HEURISTIC guard, not a semantic classifier; leetspeak
  / synonym over-claims from SECONDARY sources still downgrade to UNKNOWN via the
  tier check.

### Foundation status (unchanged from #118 base)

The inherited `validate_iteration_sync.py` exit-1 / `tests.test_iteration_sync`
36-failure debt (frozen `data/operations/iterations/121Q25B.json` &
`121Q25C.json`) REMAINS and is unchanged from base `833c3e5f…`. This fix
introduces **NO new** foundation failure; foundation validation is **NOT claimed
green**.
