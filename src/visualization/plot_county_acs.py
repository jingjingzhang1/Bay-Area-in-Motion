#!/usr/bin/env python3
"""Recreate the county WFH and LODES-vs-ACS charts from cleaned CSVs.
Run from any working directory: python src/visualization/plot_county_acs.py
"""
from pathlib import Path
import csv
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/processed/chiahao/county_ACS1_2017_2023_estimates_MOE_availability.csv'
FIG = ROOT / 'reports/figures/chiahao'
FIG.mkdir(parents=True, exist_ok=True)
with DATA.open(encoding='utf-8-sig', newline='') as f:
    records = list(csv.DictReader(f))
COUNTIES = ['Alameda','Contra Costa','Marin','Napa','San Francisco','San Mateo','Santa Clara','Solano','Sonoma']
def number(v):
    return float(v) if str(v).strip() else math.nan

fig, ax = plt.subplots(figsize=(12,6.5))
for name in COUNTIES:
    rows = sorted((r for r in records if r['county']==name),key=lambda r:int(r['year']))
    xs = [int(r['year']) for r in rows]
    ys = [number(r['wfh_share_percent']) for r in rows]
    ax.plot(xs, ys, marker='o',lw=3 if name=='San Francisco' else 1.5,
            alpha=1 if name=='San Francisco' else .75,
            color='#c74936' if name=='San Francisco' else None,
            label=name,zorder=4 if name=='San Francisco' else 2)
ax.set(title='Work-from-home share by Bay Area county | 2017–2023',
       xlabel='Year', ylabel='Workers who worked from home (% of resident workers)')
ax.set_xticks(list(range(2017,2024)))
ax.axvspan(2019.75,2020.25,color='#e5e7eb',alpha=.65,zorder=0)
ax.grid(alpha=.2);ax.legend(loc='upper left',ncol=3,fontsize=8,frameon=False)
ax.text(0,-.20,'Source: ACS 1-Year B08301. No standard 2020 ACS 1-Year; Napa 2021–22 absent from official download. No interpolation.',
        transform=ax.transAxes,fontsize=9)
fig.tight_layout(rect=[0,.05,1,1])
fig.savefig(FIG/'01_wfh_share_2017_2023.png',dpi=180,bbox_inches='tight')
plt.close(fig)

rs23=[r for r in records if r['year']=='2023']
assert len(rs23)==9
lo=min(min(number(r['acs_commuter_adjusted_daytime_proxy']),number(r['lodes_commuter_adjusted_daytime_proxy'])) for r in rs23)
hi=max(max(number(r['acs_commuter_adjusted_daytime_proxy']),number(r['lodes_commuter_adjusted_daytime_proxy'])) for r in rs23)
fig,ax=plt.subplots(figsize=(8,7))
ax.plot([lo*.85,hi*1.08],[lo*.85,hi*1.08],ls='--',color='#8aacc4',label='Equal proxy values')
for r in rs23:
    x=number(r['acs_commuter_adjusted_daytime_proxy'])
    y=number(r['lodes_commuter_adjusted_daytime_proxy'])
    ax.scatter(x,y,s=80,color='#2879aa',alpha=.88,zorder=3)
    ax.annotate(r['county'],(x,y),xytext=(7,7),textcoords='offset points',fontsize=9)
ax.set(xlabel='ACS-only commuter-adjusted daytime proxy (people)',
       ylabel='LODES-based commuter-adjusted daytime proxy (people)',
       title='LODES vs. ACS daytime population proxies | 2023')
ax.set_xlim(lo*.85,hi*1.08);ax.set_ylim(lo*.85,hi*1.08)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1e6:.1f}M'))
ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1e6:.1f}M'))
ax.grid(alpha=.18);ax.legend(frameon=False)
ax.text(0,-.18,'Source: ACS 1-Year B01003/B08301/B08604 & LODES WAC/RAC. Both are proxies, not observed daytime presence.',transform=ax.transAxes,fontsize=8.2)
fig.tight_layout(rect=[0,.04,1,1])
fig.savefig(FIG/'02_lodes_vs_acs_daytime_proxy_2023.png',dpi=180,bbox_inches='tight')
plt.close(fig)
print('Saved two county charts:', FIG)
