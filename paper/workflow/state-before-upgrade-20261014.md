# MacroHFT experiment status

Last verified: 2026-10-02T23:51:57.777318+08:00.

The distributed pipeline stopped at 2026-10-02 17:12 +08 when c203 ran out of disk space. Its /data directory shares the root filesystem. Startup free space was approximately 79 GiB, but the shared filesystem now reports zero available space. Both seed-42 trials failed (reference after 12 validated epochs, combined after 13). The startup-only storage check was insufficient; no exact resume is possible because upstream checkpoints omit replay, episodic memory, optimizer and RNG state.

Six trials completed all 15 epochs: all four seed-12345 configurations, plus reference and combined seed 2024. Four unselected speculative trials were intentionally stopped after validation selection. No final test evaluation has run.

Candidate selection was frozen at 2026-10-02 15:49 +08: combined. Initial-seed best validation returns: reference 28.0383%, combined 44.6062%, action-memory 29.2796%, cost-aligned 41.9511%. These are validation results and cannot establish that the paper's 39.28% test return was surpassed.

Recovery stage [004-storage-recovery](prompts/004-storage-recovery.md) restarts only reference and combined seed 42 on c224:/date/zyy/macrohft-cluster, where about 4 TiB is free. Failed c203 artifacts remain untouched, and logs/checkpoints were copied to c225:/date/zyy/macrohft-reproduction/results/recovery-20261002/c203/. Completed trials and the frozen selection are reused.

Recovery coordinator: 3256303; phase: recovery_training; live check: True. Its 30-second storage check pauses only the two exact owned training processes below 60 GiB and resumes above 120 GiB. Six sealed-test evaluations and final-summary.json remain pending. No paid server was rented.

This remains ETH hyper-agent retraining using released experts, not an all-market or from-scratch reproduction. Other users' files, environments and jobs were not changed.

中文：c203 的共享磁盘在运行期间被写满，两项 seed-42 实验失败，调度器于 17:12 停止。六项完整训练及验证选出的组合方法已保留；四项未选中的额外种子实验按计划停止。仅两项失败实验在约有 4 TiB 空间的 c224 上重新训练，并增加每 30 秒的磁盘检查。测试尚未完成，44.61% 是验证集收益，不能声称超过论文。
