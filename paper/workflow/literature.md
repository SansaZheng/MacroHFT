# Literature and novelty audit

Verified 2026-10-14. Recent-search window: 2025-10-14 through 2026-10-14. Older work is marked foundational or predecessor. Abstract-level evidence supports scope only, not implementation equivalence. This audit was performed by Codex; no Gemini/Claude consultation occurred.

| Work / primary source | Date / status | Verified relevance | Consequence for this project |
| --- | --- | --- | --- |
| [MacroHFT](https://arxiv.org/abs/2406.14537) | 2024; predecessor, KDD paper separately archived | Context-aware expert mixing and memory for minute trading | Must compare the original system and matched compute; minor fee repairs are not sufficient novelty. |
| [EarnHFT](https://ojs.aaai.org/index.php/AAAI/article/download/29384/30614) | AAAI 2024; predecessor | Hierarchical trading with second-level agents and minute router | Time granularity and input availability must be matched; minute-OHLCV adaptation must not be called exact reproduction. |
| [Successor Features](https://proceedings.neurips.cc/paper/2017/hash/350db081a661525235354dd3e19b8c05-Abstract.html) | NeurIPS 2017; foundational | Separates dynamics-dependent successor statistics from reward weights | Gross/turnover decomposition is an application of known linear reward transfer, not an original theorem. |
| [Risk-Aware Transfer using Successor Features](https://proceedings.neurips.cc/paper/2021/hash/90610aa0e24f63ec6d2637e06f9b9af2-Abstract.html) | NeurIPS 2021; foundational, within six calendar years | Risk-sensitive policy transfer using successor-feature statistics | Adding return variance or a risk penalty alone is not a defensible novelty claim. |
| [FORL](https://proceedings.neurips.cc/paper_files/paper/2025/hash/0bc91addac6b72fb970c678a936dacf0-Abstract-Conference.html) | NeurIPS 2025; exact first-online date not verified | Diffusion candidate states plus forecasting for nonstationary offline RL | Must distinguish market memory reliability from generic forecasting-based adaptation. |
| [MetaTrader](https://ojs.aaai.org/index.php/AAAI/article/view/40027) | AAAI 2026, published 2026-03-14 | Bilevel training on transformed stock data and conservative TD targets | Relevant modern trading baseline; not the older, similarly named MetaTrader cited in MacroHFT. Code/protocol compatibility remains to audit. |
| [MACE](https://arxiv.org/abs/2603.29086) | Preprint submitted 2026-03-30, revised 2026-04-04 | Trading simulators with nonlinear market impact and detailed costs | “More realistic costs” alone is insufficient novelty. A stress simulator cannot substitute for calibrated execution evidence. |
| [SF2](https://proceedings.iclr.cc/paper_files/paper/2026/hash/48acf4b231771e693f42305b4c9b4c9f-Abstract-Conference.html) | ICLR 2026; exact publication day unverified | Flow-based successor representations and online policy learning | Related representation method; not directly a trading baseline without an explicit adaptation. |
| [Robust Successor Features](https://arxiv.org/html/2609.31016v1) | Preprint 2026-09-25 | Linear-MDP reward/dynamics transfer with a GPI mismatch bound; grid experiments | Direct novelty collision with a generic “cost plus regime transfer” proposal. Financial applicability does not by itself establish new methodology. |
| [Distributional SF/GPI](https://www.sciencedirect.com/science/article/pii/S1568494626002620) | Applied Soft Computing 193, May 2026; publisher abstract inspected | Distributional extension addressing value-estimation bias | Must distinguish any pessimistic memory estimator from existing distributional successor features. Full-code comparison pending. |
| [JaxMARL-HFT](https://arxiv.org/abs/2511.02136) | Preprint 2025-11-03; arXiv identifies ICAIF 2025 | GPU-oriented multi-agent market-by-order environment | Relevant execution/systems reference; not interchangeable with minute-bar directional trading. Data access and hardware compatibility unresolved. |
| [Group-aware order-book RL](https://arxiv.org/abs/2605.25527) | Preprint 2026-05-25 | PPO-family methods on stock order-book directional trading | Input/task mismatch prevents direct numerical comparison with this OHLCV pilot. |

## Bounded conclusion

Cost-transported nearest-neighbor memory is useful as a diagnostic, but the present construction is not independently novel enough for a CCF A claim. A possible research question is selective reuse of delayed, partially observed trading experience under changing execution costs and conditional return laws. That question still needs a mechanism, a precise comparison against the above work, and discriminating evidence. Covariate distance and an uncalibrated standard-error penalty cannot certify robustness to arbitrary concept drift.

中文：已明确排除“改手续费”“加入风险惩罚”“重新加权历史回报”等作为单独创新。现阶段只验证可解释的成本迁移组件，新的方法贡献仍待建立。

Additional prior work: [Trading Confidence](https://arxiv.org/abs/2607.02864), uploaded 2026-07-03, reports PACIS 2025 acceptance. Do not count the upload year as a new 2026 conference method or claim uncertainty-aware trading is new.
