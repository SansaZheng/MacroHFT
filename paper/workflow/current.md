# Authorized compute fork recovery

Prompt 008/008b; executor Codex/CQ; configuration revision 7.
Canonical code/data/result archive: SansaZheng/MacroHFT.
Authorized compute fork: SuuTTT/MacroHFT (existing fork, reused without replacing
history). Main synchronized at 1dfae1699e62b57f4647eac7bf6751caf63c7cd6; new
runtime qualification branch mirrored at 1664b7af1fa2708a096491827eaaab3f4750ec25.

The repository-owner barrier is resolved by the user-authorized fork. Current jobs:

- j-1123-c9445b: queued; waiting: no feasible host (CPU only) — pc4070: GPU jobs only · excluded by placement.never: c203, c219, c220, c221, c222, c223, c225, c227, c237 · c224: last 8 CPUs kept for GPU jobs (8 of 16 booked) · c226: monitor only (windows)

- j-1123-ef9890: queued; waiting: no feasible host (CPU only) — pc4070: GPU jobs only · excluded by placement.never: c203, c219, c220, c221, c222, c223, c224, c227, c237 · c225: last 96 GB RAM kept for GPU jobs (96 GB free for us) · c226: monitor only (windows)

- j-1123-c20ec0: assigned; Kaggle notebook submitted; waiting for provider RUNNING status

The c224 and c225 inventories are host-specific reads and cannot be moved to
arbitrary free servers. Their normal CQ CPU/RAM reservations currently block
placement. No other jobs or scheduling policies were modified. The independent
Kaggle qualification uses ten existing numerical tests and synthetic data only;
it is not training, real-data evaluation or a lab-runtime certification.

Large artifacts stay on authorized server storage. Local free disk is below
2 GiB, so further bulk hydration/retrieval is deferred; only small receipts are
collected. Legacy final results, scientific gains and submission readiness
remain unverified. The preserved validation-selected protocol is unchanged.


Update: runtime job j-1123-c20ec0 failed during output collection (unsafe archive member); its test outcome is unknown. Bootstrap cleanup is corrected and two local failure-path tests pass. Replacement j-1123-7ed893 uses source commit 3034b9b3c35ffc6a49042b9a5c81f8e60c40e12f, mirrored to both repositories. Lab host reservations still require scheduler capacity; a specific administrator assistance request names the two 1-CPU/1-GB inventories. No shared policy was altered.
