# Task172 Step11 — three-input A/B replay

The three provenance-locked input bytes were available by their recorded SHA-256 values. A is the frozen Step01 relay baseline; B is the current read-only routing overlay plus compact index and exact canonical validation.

## A/B boundary

The old relay baseline has candidate counts of 5 (`《我播种黄金》`), 3 (`《叙旧》`), and 3 (`《大脑高效休息法》`). Its source reports did not execute a full current-registry retrieval or record comparable timing, memory, fallback, or exact-ID metrics. Those values are therefore `NOT_MEASURED`.

B executed the frozen Step07 facet queries against 6,158 function rows, 18,003 nonfunction rows, and a 24,161-row compact index. The scholarly metadata corpus is intentionally separate from this routing index.

| Input | B candidate universe | selected | exact IDs | invalid/orphan | fallback | duplicate rate | exact validation | time | disposition |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| 我播种黄金 / structural analogy | 194 | 50 | 50 | 0 | false | 0 | 100% | 943.108 ms | `INCONCLUSIVE` |
| 叙旧 / literary context | 223 | 50 | 50 | 0 | false | 0 | 100% | 924.076 ms | `INCONCLUSIVE` |
| 大脑高效休息法 / evidence boundary | 801 | 50 | 50 | 0 | false | 0 | 100% | 939.995 ms | `INCONCLUSIVE` |

Fresh child-process peak memory was approximately 985,088,000 / 985,350,144 / 986,054,656 bytes on macOS Python. It is recorded as an observation, not an A/B improvement claim. False “repo lacks this” incidence is `NOT_MEASURED`; the old path has no comparable executable metric. The two Step01 known duplicate/already-covered candidates remain dispositions, and B selected no duplicate canonical IDs. No literary or scholarly metadata was promoted to empirical truth.

The machine record is `data/operations/iterations/172/step11-ab-replay.json`. The bounded B engineering run passed its exact-ID and fallback gates; comparative performance is deliberately `INCONCLUSIVE` rather than overstated.
