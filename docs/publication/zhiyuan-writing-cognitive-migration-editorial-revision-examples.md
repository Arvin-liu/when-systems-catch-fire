# 认知迁移编辑修订：可恢复 before/after 范例

Status: `REBUILT_CANDIDATE_NOT_INTEGRATED`
Candidate: `0.1.0-candidate`

The before passages below are recoverable from current main at
`e5c6d1d0b75dae41b414474bc22747816cd00c78`. The two examples use different
text types: a historical interpretive essay and a cross-domain mechanism
essay. Neither source work is modified by this candidate.

## Example A — historical interpretive essay

Source: `docs/publication/works/when-an-emperor-manufactures-heaven.md`, current
main blob `1f190a18862b07c178d815a875cd042a6103984a`, lines 5–7.

### Before (recoverable)

> 因此，真正值得看的也许不是鹤到底从哪里来，而是鹤飞过之后发生了什么：谁有资格报告，什么算作祥瑞，哪一种画法可以保存它，哪一首诗能替它发言，又由谁把这份解释送回皇帝那里。

### After (candidate editorial variant)

> 鹤飞过宫门之后，谁先把它写进报告？谁把“看见”改成祥瑞，谁让画和题诗替它保存方向，又是谁把这份解释送回皇帝那里？问题从鹤的来处移到了它进入宫廷之后经过的那条路。

### Audit

- Carrier: recursive questioning plus a bounded return to the interface.
- Preserved: the event, reporting, naming, image, poem, and return to the
  emperor already present in the source passage.
- Changed: the original opening contrast is no longer asked to announce the
  entire migration in one sentence; the process is staged as questions before
  the local synthesis.
- Not changed: no new historical fact, causal claim, or certainty about
  whether the cranes were genuine or fabricated.
- Reversal condition: if the questions make the historical uncertainty less
  visible, retain the before version or use only the first question.

## Example B — cross-domain mechanism essay

Source: `docs/publication/works/when-an-army-believes-its-own-back.md`, current
main blob `90cafdf348a9ec32172996a12adb8713fbada26f`, lines 17–21.

### Before (recoverable)

> 行动以前，人们通常先找证据，再作判断。可在某些回路里，行动本身会产生下一步所依据的证据。士兵退了，后来的人便更相信前线已败；扩音器发出啸叫，声音又回到麦克风，替下一轮啸叫增加强度。两者一个包含恐惧和求生，一个只是物理过程，却都提示我们：反应一旦返回起点，结果就可能冒充原因。

### After (candidate editorial variant)

> 麦克风里的啸叫先让人听见一条回路：输出返回输入，下一圈因此更响。战场上的退却却把同一问题变得更重——第一个人后退，后来的人得到的不是更多敌情，而是一个已经带着代价的判断。两种回路可以放在同一张图上，但不能放进同一种经验里：声音没有家人，士兵却可能用身体支付每一次放大。

### Audit

- Carrier: perspective switching from the physical loop to the human cost,
  with a concrete anchor before the abstraction.
- Preserved: feedback, output-to-input return, the difference between acoustic
  and human systems, and the source's explicit warning against flattening them.
- Changed: the passage starts with the recoverable microphone scene and then
  moves to the soldier, so the analogy is constrained by the human cost rather
  than introduced as an abstract equivalence.
- Not changed: no claim that warfare, sound systems, banks, or power grids are
  the same system; no new historical event or quantified outcome.
- Reversal condition: if the rewritten bridge makes the analogy look causal or
  universal, reject it and keep the source wording.

## Cross-example findings

The pass can make a movement more legible, but neither before/after pair
measures reader cognition. They are editorial demonstrations with fixed source
boundaries, not validation data. The examples do not justify a style clone,
an author-similarity score, a research runtime, or a method-level acceptance.
