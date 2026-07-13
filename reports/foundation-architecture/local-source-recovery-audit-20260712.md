# Local source and recovery audit

## Scope and boundary

This was a read-only L0 source inspection. No Get 笔记 API was called, no
mathematical or logical decision was delegated to Get 笔记, and no source file
was edited or copied into the authority registries.

## Local note roots

| path | exists | file count | use |
|---|---|---:|---|
| /Users/zhiyuan/我的笔记/getnote-notes | yes | 117986 | direct-source locator recovery only |
| /Users/zhiyuan/我的笔记/得到大脑 | no | 0 | absent; not treated as a blocker for architecture migration |
| /Users/zhiyuan/我的笔记/2026-07-09 1735 | yes | 141 | historical export batch |
| /Users/zhiyuan/我的笔记/2026-07-09 1902 | yes | 41 | historical export batch |

This corrects the 075 report that said getnote-notes was absent. Existence does
not by itself prove provenance: each locator still needs an identity, content
hash or stable anchor and conflict review.

## Codespace Rescue and old-table sources

- recovery function table: /Users/zhiyuan/Agent 工作区/Codespace-Rescue/Unified-Case-Table/统一函数总表_Codespace救援.md
  - size: 1298353 bytes
  - sha256: ec3f131d1e8eb9014ac4a85922ca010c1bfbe17bbb3fd334e4f69de9e002c9d1
- recovery case table: /Users/zhiyuan/Agent 工作区/Codespace-Rescue/Unified-Case-Table/统一案例总表_Codespace救援.md
  - size: 1142593 bytes
  - sha256: b380574d20b0fd1c908b39f78641f4ecb78d64ddda0adca3e010bcc35c91fb7d

Existing audits show the rescue case table is an old subset and the only
function-side rescue increment was MF-0001 through MF-0005, already integrated.
The recovery files remain L0 source versions, not current object authority.

## Git history anchors

- aa307e61: historical 617 / 804 index-title snapshot
- dc6cff64: rescued MF suboperators integrated
- b6afd2fe: D600-D602 and C-0810-C-0811 material collision
- a20bac8b: D603/D604 promotion and M8 pending decision

Git history, source versions, registry identity and current status are separate
records. A historical path or commit is evidence of lineage, not proof of a
claim.
