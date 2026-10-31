#!/usr/bin/env python3
"""Simple 2017/2023 WFH and 2019/2023 tract pre-post summary for report tables.
Run: python src/analysis/summarize_daytime_changes.py
Not a population forecast or a direct observation of daytime physical presence.
"""
from pathlib import Path
import csv
from collections import defaultdict
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT/'data/processed/chiahao'

def read(name):
    with (DIR/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))
def save(name,rows):
    with (DIR/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

county=read('county_ACS1_2017_2023_estimates_MOE_availability.csv')
by={(r['county'],int(r['year'])):r for r in county}
summary=[]
for name in sorted({r['county'] for r in county}):
    a,b=by[name,2017],by[name,2023]
    summary.append({'county':name,'wfh_2017_pct':a['wfh_share_percent'],
       'wfh_2023_pct':b['wfh_share_percent'],
       'change_percentage_points': round(float(b['wfh_share_percent'])-float(a['wfh_share_percent']),3),
       '2023_acs_daytime_proxy':b['acs_commuter_adjusted_daytime_proxy'],
       '2023_lodes_daytime_proxy':b['lodes_commuter_adjusted_daytime_proxy'],
       '2023_lodes_minus_acs_proxy':b['lodes_minus_acs_daytime_proxy']})
save('county_pre_post_wfh_summary.csv',summary)

tract=read('tract_daytime_proxy_fixed_2023P_2019_2023_with_population_MOE.csv')
aggregate=defaultdict(lambda:defaultdict(int))
for r in tract:
    c,y=r['county'],int(r['year'])
    aggregate[c,y]['net_jobs'] += int(r['net_jobs_wac_minus_rac'])
    aggregate[c,y]['daytime_proxy'] += int(r['daytime_population_proxy'])
results=[]
for c in sorted({c for c,y in aggregate}):
    a,b=aggregate[c,2019],aggregate[c,2023]
    results.append({'county':c,'fixed_population_baseline':'2023 ACS5 (2019–2023 period)',
       'net_jobs_2019':a['net_jobs'],'net_jobs_2023':b['net_jobs'],
       'net_jobs_change':b['net_jobs']-a['net_jobs'],
       'daytime_proxy_2019':a['daytime_proxy'],'daytime_proxy_2023':b['daytime_proxy'],
       'daytime_proxy_change':b['daytime_proxy']-a['daytime_proxy'],
       'note':'Change reflects LODES net job flow only because resident population is held fixed'})
save('county_2019_2023_fixed_baseline_change_summary.csv',results)
print('Saved 2 report-ready summaries into',DIR)
