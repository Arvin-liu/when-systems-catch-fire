# 历史创造性不连续性回放 — IGNITION-20260908-165

命令：Arvin-liu/1111/agent-commands/IGNITION-20260908-165.md@b3b128f46a625f728870ded1a975f3c2f0db53ce
命令 blob：065f02e04e3a0c8e55c398954a761c66901f74b5；内容 SHA-256：dcd123b9ae487f54dd7afcc921f9f1fd691147c463634e33e8d3f1f136b2d22a
Formal 基线：work/IGNITION-20260907-164@ba6641d200000ad4ebaa764e4ed94d79f32fb2df
边界：研究只、Draft 只；不改变 Current、canonical、生产运行时、validator 或 Owner/认识论接受状态。


Stage A 为 UNDERDETERMINED：可数的四个精确正例中 C3 能力等价命中 0/4，holdout 命中 0/3；P00 保留为 HISTORICAL_BOUNDARY_GAP，没有被补造边界。

Stage A 失败或未定并不停止本任务；按照命令继续执行了 Stage B。没有把同一运行产生的 proposer、packet 和 answer key 解释成认知独立性。

失败门槛：three_of_five_scoreable_positive_hits, two_of_three_holdout_positive_hits, c3_beats_c0_c1_c2_by_net_two, no_l3_false_positive_n02_n03_n09, all_strong_negative_l3_fp_le_one, random_collision_not_equivalent, p00_boundary_scoreable。

强负例 L3 假阳性：3；C3 相对 C0/C1/C2 的配对净差：{'C0': 12, 'C1': 0, 'C2': 0}；C3-C4 结构分数差：0.5。这些数字是本地结构代理结果，不是外部验证。
