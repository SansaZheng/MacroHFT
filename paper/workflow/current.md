# Authorized compute fork recovery

Prompt 008/008b; executor Codex/CQ; configuration revision 7.
Canonical archive: https://github.com/SansaZheng/MacroHFT .
Compute fork: https://github.com/SuuTTT/MacroHFT .
The owner allowlist barrier is resolved. Both main branches were verified at
`6c88b87be654014b9b27e32d5cb51df8021093e0` before this status update.
Both runtime branches are at `f3c7d1c44b3acaae94a1c3cf7df192425fefbdf5`.

## Job snapshot

Checked: 2026-11-23T07:31:30.371495+00:00

- j-1123-c9445b: queued; waiting: no feasible host (CPU only) — pc4070: GPU jobs only · excluded by placement.never: c203, c219, c220, c221, c222, c223, c225, c227, c237 · c224: last 8 CPUs kept for GPU jobs (8 of 16 booked) · c226: monitor only (windows)
- j-1123-ef9890: queued; waiting: no feasible host (CPU only) — pc4070: GPU jobs only · excluded by placement.never: c203, c219, c220, c221, c222, c223, c224, c227, c237 · c225: last 96 GB RAM kept for GPU jobs (96 GB free for us) · c226: monitor only (windows)
- j-1123-124e9b: done; outputs verified (Kaggle, 0.04 h); results in /Users/sudingli/.local/share/cq/kaggle/results/j-1123-124e9b/out; copied to /Users/sudingli/.local/share/cq/kaggle/results/macrohft-runtime-qualification-20261123/pip-bootstrap-fix

The two lab inventories read host-specific legacy locations. Their normal CQ
CPU/RAM reservations block placement; physical availability does not override
scheduler policy. An administrator assistance request names these two jobs.
No other jobs or shared policy were modified. No training was launched.

The first numerical qualification failed output collection with an unsafe
archive member; its numerical result is unknown. The second failed private
venv creation. Cleanup was fixed and two local failure-path tests pass. The
third uses --without-pip plus a hash-verified immutable official bootstrap
inside the private job environment. No system Python modification is performed.
The third job completed: all 10 numerical tests passed (8.740 s test-suite time;
11.743 s wrapper-measured time; 656,183,296-byte test-child peak RSS). Fetched
source manifest matches the published branch and both synthetic fixture hashes
verify. Receipt, package versions, logs and fixtures are archived under
results/compute-mirror-20261123/j-1123-124e9b. The original simulator emitted
divide-by-zero warnings in synthetic zero-required-capital cases; these logs
are preserved. No market-performance result is claimed.

GitHub briefly refused to resolve the newest canonical commit in the fork.
Draft PR #1 made the cross-repository change reviewable; the connector then
fast-forwarded with expected-head protection. GitHub marked it merged by that
fast-forward, with no extra merge commit. SSH push to the fork was rejected;
canonical SSH and the SuuTTT connector remain the respective write routes.

Only synthetic inputs and six released experts are used by the numerical
qualification. It is not training, a real-data evaluation, or lab certification.
The preserved validation-selected experiment protocol is unchanged. Legacy
final results, method gains and CCF A submission readiness remain unverified.
66 legacy archive files remain pending; 4 source files were reconstructed.
Local disk is below 2 GiB, so only small evidence is retrieved; bulk output
must remain on authorized server storage. Paid compute budget remains unset.


## 2026-11-24 — user-requested archival and local cleanup

All locally readable archive content was published and actual GitHub bytes
verified across main and both qualification branches. The full local data
checkout and Git object database were replaced by a shallow sparse code and
documentation checkout at the same path. Training cannot run from this partial
local checkout without restoring the required artifacts. No remote job,
experiment result or model was modified. The 66 unavailable iCloud files remain
preserved and pending. Details: ../../docs/LOCAL-STORAGE.md .
