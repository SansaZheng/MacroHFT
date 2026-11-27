# Claim map

| Claim | Evidence | Status / limits |
|---|---|---|
| Paper reports ETH 39.28% vs EarnHFT 18.02% | Paper Table 1 | Verified literature claim; not measured locally |
| Official ETH data matches reported dates | results/data-audit.json | Verified dates and split separation; feature causality not fully auditable |
| Six official experts load | results/tests.log | Verified |
| Runtime repairs and accelerated operations pass checks | results/tests.log; smoke JSON files | Verified within checked cases; not bitwise trajectory equivalence |
| Action-conditioned memory improves trading | Registered full experiments | Pending |
| Aligned demonstration fee improves trading | Registered full experiments | Pending |
| Full MacroHFT ETH return reproduced | Full reference experiment | Pending |
| Method exceeds 39.28% on matching test | Sealed test and cross-seed report | Pending; no positive claim yet |
| All four markets / all baselines reproduced | Missing artifacts | Unsupported |


## Research route v1, 2026-10-14

| Claim | Evidence | Status |
| --- | --- | --- |
| Causal prefix and maturity guards pass six tests | research/cost-transport-memory-v1/results/tests.log | Verified within checked cases |
| Exact linear-fee accounting | research route src/memory.py and tests/test_core.py | Verified identity; known SF special case, not new theory |
| Three-market component pilot completed | research route results/pilot.json | 84 validation settings, not full RL |
| Robust predictive improvement | pilot.json and activity-control.json | Unsupported; sparse trading without compelling matched-control advantage |
| Original remote tests completed | final-summary.json unavailable | UNKNOWN on October 14 |
| CCF A submission-ready original paper | research completion gates | Not achieved |


## 2026-11-27 update (supersedes historical pending rows above)

| Claim | Evidence | Status / limitation |
|---|---|---|
| ETH reference seed 12345 rounds to 39.28% | recovered final-summary.json; summary-verification.json | Summary/arithmetic and six trial artifacts reconciled; ETH hyper-agent scope only |
| Combined outperforms reference | same six paired rows | Rejected on this period: -38.177387 pp mean difference |
| Nine causal diagnostic tests pass | v2 results/screen-001/tests.log | Engineering property only |
| Conditional delayed weighting improves trading | v2 synthetic diagnostic | Unsupported; only constructed MSE effects, not RL or trading |
| Full CCF A manuscript readiness | research gates | Not achieved |
