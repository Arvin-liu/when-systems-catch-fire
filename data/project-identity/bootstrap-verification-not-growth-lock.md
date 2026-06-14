# Bootstrap Verification Is Not a Growth Lock

The dual-channel bootstrap verification loop is for validation, not for blocking growth. An object that has not passed full verification must not enter `active` status, but may enter `candidate`, `lead`, `pending`, `needs_evidence`, `needs_human_review`, `existing_reference` or other non-active statuses.

Dual-channel bootstrap prevents hallucinated active conclusions, not new questions, curiosities, or leads entering the repository.

Status machine:
  new curiosity / user question -> candidate -> lead -> academic_search_pending -> academic_search_passed / existing_reference / inconclusive / pending -> dual_channel_pending -> active / needs_evidence / contradiction / underdetermined

Key rules:
1. Must pass academic search before becoming active.
2. Must pass dual-channel bootstrap before becoming active.
3. Failure to pass does NOT mean deletion.
4. Failed items may be kept as lead / candidate / pending.
5. Contradiction entries go to blocker, do NOT stop project growth.
6. Bootstrap prevents "finalized" conclusions, not "candidate pool" entries.

自举验证循环的作用是验证，不是阻止增长。一个新对象没有通过完整验证时，不得进入 active 状态，但可以进入 candidate、lead、pending、needs_evidence、needs_human_review、existing_reference 等非 active 状态。
状态机：
  new curiosity / user question -> candidate -> lead -> academic_search_pending -> academic_search_passed / existing_reference / inconclusive / pending -> dual_channel_pending -> active / needs_evidence / contradiction / underdetermined
关键规则：
1. 未通过学术搜索，不得 active。
2. 未通过正反自举，不得 active。
3. 未通过不等于删除。
4. 未通过可以保留为 lead / candidate / pending。
5. contradiction 进入 blocker，不代表整个项目停止增长。
6. 自举循环可以阻止"定稿"，不能阻止"进入候选池"。
