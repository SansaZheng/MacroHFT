"""Generate a descriptive report from the immutable pilot, without model selection."""
import json,pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=pathlib.Path(__file__).resolve().parents[1]
p=json.loads((R/'results/pilot.json').read_text());d=pd.DataFrame(p['rows']);manifest=json.loads((R/'results/data-manifest.json').read_text())
variants=['scalar_memory','transport_memory','guarded_transport']
labels=['Stale scalar memory','Cost transport','Transport + rejection']
colors=['#777777','#1479b8','#bd4d28']
fig,axes=plt.subplots(2,3,figsize=(11.2,6.2),sharex=True)
for col,symbol in enumerate(['BTCUSDT','ETHUSDT','SOLUSDT']):
 for variant,label,color in zip(variants,labels,colors):
  rows=d[(d.symbol==symbol)&(d.variant==variant)].sort_values('cost_bps')
  axes[0,col].plot(rows.cost_bps,rows.return_pct,'o-',color=color,label=label,lw=1.8,ms=4)
  axes[1,col].plot(rows.cost_bps,100*rows.participation,'o-',color=color,lw=1.8,ms=4)
 axes[0,col].axhline(0,color='#222222',ls=':',lw=1,label='Cash (0%)' if col==0 else None)
 axes[0,col].set_title(symbol.replace('USDT',''))
 axes[1,col].set_xlabel('One-way fee (bps)')
 axes[1,col].set_ylim(bottom=0)
 for ax in axes[:,col]:
  ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False);ax.set_xticks([2,5,10,20])
axes[0,0].set_ylabel('Validation return (%) ↑');axes[1,0].set_ylabel('Traded blocks (%)')
fig.suptitle('Lower losses can come from almost never trading',fontsize=14,y=.99)
handles,labs=axes[0,0].get_legend_handles_labels();fig.legend(handles,labs,loc='upper center',bbox_to_anchor=(.5,.94),ncol=4,frameon=False,fontsize=9)
fig.tight_layout(rect=[0,.07,1,.87]);fig.text(.5,.025,'March 2026 validation · fixed initial capital · next-bar execution · both sides charged\nComponent diagnostic only; not MacroHFT or final test performance.',ha='center',fontsize=9,color='#444444')
fig.savefig(R/'results/pilot-diagnostic.png',dpi=180);fig.savefig(R/'results/pilot-diagnostic.svg');plt.close(fig)
lines=['# Pilot outcome and research decision','','Client date: 2026-10-14. Status: diagnostic completed; research contribution NOT established.','','## 中文结论','','已完成 BTC、ETH、SOL 三个市场、四档单边手续费和七种组件/控制策略，共 84 个验证设置。数据来自 Binance 官方月度文件，九个下载均校验 SHA256；没有下载或评估保留测试月份。六项因果性及会计测试通过。','','这轮结果不支持把“成本重估＋距离拒绝”直接作为新的顶会方法。高费用下损失下降主要伴随交易活动接近零；低费用时，成本迁移也可能比原始固定标签更差。不能把规避交易造成的低回撤包装为预测能力或策略质量提升。','','## Nominal 5 bps validation measurements','','| Asset | Component | Return (%) ↑ | Drawdown (%) ↓ | Participation (%) |','| --- | --- | ---: | ---: | ---: |']
for _,v in d[(d.cost_bps==5)&d.variant.isin(variants+['cash'])].iterrows():lines.append(f'| {v.symbol} | {v.variant} | {v.return_pct:.4f} | {v.max_drawdown_pct:.4f} | {100*v.participation:.2f} |')
lines+=['','![Cost and participation diagnostic](../results/pilot-diagnostic.png)','','## English interpretation','','The decomposition passes exact-accounting checks but does not establish predictive skill or novel methodology. At the nominal fee, transport and scalar memory are identical by construction. The guarded method trades only 0.67%, 2.43% and 1.62% of BTC, ETH and SOL blocks, respectively. At 20 bps it holds cash on every asset. At 2 bps, mean returns across these three independent validation scenarios are approximately +0.789% for stale scalar memory and −1.318% for transported memory. These are descriptive averages, not a portfolio result or significance test. Do not select the more favorable fee after seeing these results.','','The pilot uses 60-minute flat/long round trips, eight causal minute-bar features and a frozen nearest-neighbor memory. It has no learned MacroHFT experts, no deep RL training and no calibrated execution impact. Its denominator, dates and policy class differ from the original benchmark: no comparison with 39.28% is valid. Multi-asset market observations are correlated; three symbols in one month are not independent replications.','','## Decision','','Do not promote this component as a CCF A contribution. Retain the causal/accounting infrastructure and negative results. The next discriminating study must separate state-support failure, conditional-return drift, and cost-label mismatch, and compare activity-matched controls. A stronger integrated RL mechanism and an independent theoretical/novelty audit are required before expensive sweeps or a finished manuscript.','','Remote historical test results remain UNKNOWN because c225/c220ts timed out. Restore connectivity before reconciling the original three-seed comparison. No new remote job or paid rental was launched.','','## Reproducibility','','Registered protocol: `protocol.json`; source: `src/memory.py`; runner: `scripts/pilot.py`; six tests: `tests/test_core.py`; complete outcomes: `results/pilot.json` and `results/pilot.csv`; data checksums: `results/data-manifest.json`; code hashes: `results/execution-manifest.json`. Report regeneration: `../../.venv/bin/python scripts/report.py` from this route root.','','Raw archive bytes: '+str(sum(x['bytes'] for x in manifest))+'. Total raw rows: '+str(sum(x['rows'] for x in manifest))+'. Pilot elapsed seconds: '+f"{p['elapsed_seconds']:.2f}"+'.']
(R/'docs/pilot-report.md').write_text('\n'.join(lines)+'\n')
summary={'decision':'do_not_promote_component_as_novel_RL_method','test_evaluated':False,'evaluated_settings':len(d),'market_count':3,'training_seed_replications':0,'raw_rows':sum(x['rows'] for x in manifest),'raw_archive_bytes':sum(x['bytes'] for x in manifest),'caveat':'deterministic validation diagnostic; no significance or CCF A readiness claim'}
(R/'results/decision.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
