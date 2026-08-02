# FINAL CAMPAIGN REPORT

## Closeout

- Campaign: `POINTFIRE-OVERNIGHT-PUBLIC-EVIDENCE-RESEARCH-CAMPAIGN-20260803-R1`
- Actual start: `2026-08-03T02:29:24+08:00` (Asia/Shanghai)
- Actual closeout preparation: `2026-08-03T03:12:26+08:00` (Asia/Shanghai)
- New-round deadline: `2026-08-03T10:00:00+08:00`; no new round was started after closeout preparation.
- Startup control tip: `551d1bf51eb8e69f2421ebf78526c323c159c796`
- Research baseline: `61510ed26a1285e1746777c9eacd568cb3038a50`
- Ending remote `main`: `61510ed26a1285e1746777c9eacd568cb3038a50` (unchanged from baseline)
- Completed rounds: `8`
- Final research-results tip before this closeout metadata commit: `279913c31b33897f179b35176a30f70a4eb90ae4`
- Final branch: `research/overnight-public-evidence-20260803-r1`
- Final state: `COMPLETE_AWAITING_GPT_OWNER_ADJUDICATION`

## Round ledger

| Round | Domain and question | Sources | Verdict |
|---|---|---:|---|
| 001 | AI weather models versus physical models for record-breaking extremes | 4 | `PARTIALLY_SUPPORTED` |
| 002 | Handwriting versus typing and university learning | 6 | `CONTESTED` |
| 003 | European heat-health action plans and mortality | 7 | `SUPPORTED_WITH_SCOPE` |
| 004 | 2025 low-carbon electricity growth and fossil generation | 6 | `SUPPORTED_WITH_SCOPE` |
| 005 | GLP-1 cardiovascular outcomes in obesity without diabetes | 7 | `SUPPORTED_WITH_SCOPE` |
| 006 | Generative AI and software developer productivity | 7 | `CONTESTED` |
| 007 | EV versus internal-combustion vehicle fire frequency | 5 | `SUPPORTED_WITH_SCOPE` |
| 008 | Microplastics in arterial plaque and cardiovascular events | 5 | `INSUFFICIENT_EVIDENCE` |

Every round contains the required minimal packet: `REPORT.md`, `SOURCES.jsonl`, and `ROUND.json`. Reports are generally 1,769–2,515 Chinese characters. Each round recorded a first-hand or official source, an independent or edited source, opened scope, limitations, selection scores, and a competing explanation.

## Three most valuable findings

1. Measurement context changes the AI productivity answer. A simple Copilot task and three enterprise field experiments showed faster completion or more completed tasks, while METR’s randomized study of experienced developers maintaining familiar large repositories showed a roughly 19% slowdown. The defensible candidate is task- and workflow-dependent productivity, not a universal percentage.

2. A global electricity turning point is real only at a bounded accounting level. Ember and IEA evidence supports low-carbon generation covering 2025 global electricity-demand growth and a small decline in aggregate fossil generation, while gas generation still rose and whole-energy demand and emissions did not fall. Annual power balance is not whole-system decarbonisation or hour-by-hour reliability.

3. Human-health signals repeatedly narrowed under causal scrutiny. Heat plans were associated with lower mortality but implementation and confounding remain; semaglutide has strong secondary-prevention evidence for a defined high-risk population but not all GLP-1 drugs or healthy weight-loss users; microplastics in plaques are a strong observational signal whose contamination and method limits prevent causal proof.

## Contested, insufficient, and unverified items

- `CONTESTED`: Round 002 on handwriting and learning; Round 006 on AI coding productivity.
- `INSUFFICIENT_EVIDENCE`: Round 008 on microplastics causing cardiovascular events.
- No round was left null or incomplete. Round 001 was `PARTIALLY_SUPPORTED`; Rounds 003, 004, 005, and 007 were `SUPPORTED_WITH_SCOPE`.
- Some primary pages were inaccessible behind ordinary access controls. Those rounds recorded the restriction and used only accessible abstracts, official summaries, mirrors, or independent reporting for the affected claim; no paywall or access control was bypassed.
- No raw individual-level dataset was reanalysed. The packets are evidence candidates, not completed systematic reviews, meta-analyses, or regulatory assessments.

## Minimal next verification candidates

- Re-run AI coding experiments across simple tasks, familiar repositories, developer experience levels, tool generations, quality, review, and maintenance outcomes.
- Replicate the microplastic plaque finding in contamination-controlled laboratories and prospective populations outside carotid-surgery cohorts.
- Test the electricity and heat findings with regional, hourly, implementation-level, and final-energy data before making causal or whole-system claims.

## Safety and acceptance declaration

This campaign remained on the dedicated research branch and baseline. It did not modify `Arvin-liu/1111` `relay/current`, Task 114, `main`, pull requests, tags, lifecycle events, Foundation projections, planners, project state, or whole-repository derived surfaces. No PR, merge, rebase, amend, squash, reset replacement, or force push was used. All results remain candidate research packets and have not been accepted by GPT or the owner as Pointfire knowledge or a formal project conclusion.

The final branch tip must be read from the remote branch ref and the final `STATUS.json` after the ordinary closeout push; the last research-results commit immediately before this report is `279913c31b33897f179b35176a30f70a4eb90ae4`.
