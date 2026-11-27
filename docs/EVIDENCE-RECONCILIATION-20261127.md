# Recovered ETH final results — 2026-11-27

CQ inventories j-1123-c9445b and j-1123-ef9890 finished after the prior session.
Their actual outputs have now been fetched. The c225 final summary reports
completion at 2026-10-03 04:02:27 +08:00. Its full original bytes were recovered
from the inventory JSON: reserialization matches the source SHA-256 and size
exactly. The six unique trial rows, profit/capital return arithmetic, means and
sample standard deviations have been independently recomputed from that summary.
Underlying per-trial files and model identity are being checked separately by
CQ j-1127-458f37; this summary audit is not a new policy evaluation.

| Seed | Reference return (%) | Combined return (%) | Difference (percentage points) |
|---|---:|---:|---:|
| 12345 | 39.280827 | 0.811625 | -38.469203 |
| 2024 | 39.687667 | 0.666378 | -39.021289 |
| 42 | 34.089106 | -2.952562 | -37.041668 |

Reference mean: **37.685867%**, sample SD **3.121521** percentage points.
Combined mean: **−0.491520%**, sample SD **2.132562** percentage points.
Mean paired difference: **−38.177387 percentage points**. All three differences
are negative. Three seeds on the same market period are not three independent
market replications; no population-level significance claim is made.

The reference seed 12345 result, 39.280827%, rounds to the reported 39.28%.
Scope is ETH hyper-agent retraining with the authors' six released experts,
not all four markets or expert learning from scratch. This corrects the earlier
“final result unknown” status. The combined modification failed on this period;
its stronger validation score did not transfer. Do not rerun this test to search
for a more favorable seed, checkpoint or modification.

The combined model traded more (35–49 buys versus 19–20), unlike the separate
cash-like cost-transport pilot. These are distinct experiments; their failure
mechanisms cannot be conflated. The two simultaneous modifications and model
selection prevent attribution to either component from this comparison alone.

Remaining limits: upstream ex-post capital denominator and no terminal
liquidation fee; original expert provenance/feature causality not fully rebuilt;
individual checkpoint/source reconciliation pending. No full-paper reproduction,
robust trading improvement, or CCF A readiness is established.

中文：历史实验实际已完成，原方法 seed 12345 的收益与论文四舍五入后一致。
combined 三个种子均明显落后。现已取回并核验汇总字节与统计计算，正在核对单次
结果及模型哈希；未重新训练，也未重新运行最终测试。该负结果必须保留。

## Post-hoc accounting diagnostic

Recorded extra fees are only 1.73%–2.96% of the per-seed absolute profit gap.
Using the reference capital denominator for the combined profit gives returns
of 0.920%, 0.782%, -3.326%, so the denominator change alone cannot explain the collapse. This is
descriptive arithmetic on an already observed test, not causal attribution or
a new selection metric. Gross path profit, policy exposure and attribution to
either modification require validation-only follow-up.
