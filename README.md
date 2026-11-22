# CQ archive smoke branch

This lightweight branch qualifies source identity and archive correctness on
CQ's documented free Kaggle CPU backend. It does not access lab servers,
train a trading policy, or evaluate any market test period.

The experiment archive and research documentation are on the `main` branch.
The lab's repository-owner allowlist remains a separate prerequisite for
recovering legacy server experiments. No allowlist or provider limit is bypassed.

Envelope: 1 CPU, no GPU, 1 GiB RAM, at most 6 minutes. There are no package
installs or paid compute-unit requirements. Remote peak resource use is recorded
in `receipt.json`; the envelope is not a measurement of a training workload.

Required results: pinned-source hash receipt, five passing archive-integrity
tests and 3/3 progress. CQ's verified completion and fetched artifacts are
required before claiming the smoke succeeded.
