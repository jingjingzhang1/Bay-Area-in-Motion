#!/usr/bin/env python3
"""Rebuild Bay Area 2023 B01003 ACS5 tract MOE and LODES joined outputs (stdlib only).
Run: python src/data/prepare_tract_acs.py
The source directory is bundled, no internet or paid libraries required.
"""
from pathlib import Path
import zipfile,csv,io,json,collections,statistics
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'data/raw/chiahao/tract'
DATA=ROOT/'data/processed/chiahao'
OUTPUTS=DATA
DATA.mkdir(parents=True,exist_ok=True)
ACS='ACSDT5Y2023.B01003_2026-10-28T163558.zip'
COUNTIES={'06001':'Alameda','06013':'Contra Costa','06041':'Marin','06055':'Napa','06075':'San Francisco','06081':'San Mateo','06085':'Santa Clara','06095':'Solano','06097':'Sonoma'}

def load_csv(path):
 with open(path,encoding='utf-8-sig',newline='') as fp:return list(csv.DictReader(fp))

def dump_csv(path, rows, cols):
 with open(path,'w',encoding='utf-8',newline='') as fp:
  writer=csv.DictWriter(fp,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(rows)

with zipfile.ZipFile(SOURCE/ACS) as z:
 with z.open('ACSDT5Y2023.B01003-Data.csv') as src:
  lines=io.TextIOWrapper(src,encoding='utf-8-sig',newline='')
  raw=list(csv.DictReader(lines))
# The second line in Census downloads is a human-readable variable-label row
assert raw[0]['GEO_ID']=='Geography', 'Census label row not found; examine file format'
acs=[]
for row in raw[1:]:
 geo=row['GEO_ID']
 assert geo.startswith('1400000US') and len(geo)==20,geo
 geoid=geo[-11:]
 if geoid[:5] not in COUNTIES:continue
 acs.append({'tract_geoid':geoid,'county_geoid':geoid[:5], 'county':COUNTIES[geoid[:5]],
   'acs5_2019_2023_population_estimate':int(row['B01003_001E']),
   'acs5_2019_2023_population_moe_90pct':int(row['B01003_001M']),
   'census_geography_name':row['NAME'],
   'acs_table':'B01003','acs_dataset':'2023 ACS 5-Year Detailed Tables','acs_table_reference':'https://data.census.gov/table/ACSDT5Y2023.B01003'})
acs.sort(key=lambda x:x['tract_geoid'])
assert len(acs)==1772, len(acs)
acs_map={r['tract_geoid']:r for r in acs}
assert len(acs_map)==len(acs),'Duplicate ACS GEOID'
dump_csv(DATA/'bay_area_2023_ACS5_B01003_E_MOE_1772_tracts.csv',acs,list(acs[0]))
mtc=load_csv(SOURCE/'mtc_tract_population_2017_2024_clean.csv')
assert len(mtc)==1765,len(mtc)
assert len({r['tract_geoid'] for r in mtc})==len(mtc),'Duplicate MTC tract GEOID'
assert {r['tract_geoid'] for r in mtc}.issubset(acs_map),'MTC geographies missing in official ACS5'
joined=[]
for m in mtc:
 r=acs_map[m['tract_geoid']]
 assert int(m['population_2023'])==r['acs5_2019_2023_population_estimate'],(m['tract_geoid'],m['population_2023'],r['acs5_2019_2023_population_estimate'])
 pop=r['acs5_2019_2023_population_estimate']; moe=r['acs5_2019_2023_population_moe_90pct']
 joined.append({**m,**{k:v for k,v in r.items() if k not in ['county','county_geoid']},
   'population_relative_moe':round(moe/pop,5) if pop else '',
   'flag_population_under_500':int(pop<500),'flag_population_zero':int(pop==0),
   'flag_relative_moe_gt_50pct':int(pop>0 and moe/pop>0.5)})
joined.sort(key=lambda x:x['tract_geoid'])
dump_csv(DATA/'mtc_acs5_2023_matched_population_moe_1765_tracts.csv',joined,list(joined[0]))
extra=[r for r in acs if r['tract_geoid'] not in {m['tract_geoid'] for m in mtc}]
assert len(extra)==7 and all(r['tract_geoid'][5:9]=='9900' or r['tract_geoid'][5:9]=='9901' or r['tract_geoid'][5:9]=='9902' for r in extra),extra
assert all(r['acs5_2019_2023_population_estimate']==0 for r in extra)
dump_csv(OUTPUTS/'acs_only_7_water_tracts.csv',extra,list(extra[0]))

by_year={year:{x['tract_geoid']:x for x in load_csv(SOURCE/f'tract_summary_{year}.csv')} for year in (2019,2023)}
proxy=[]
for m in joined:
 pop=m['acs5_2019_2023_population_estimate']; moe=m['acs5_2019_2023_population_moe_90pct']
 for year in (2019,2023):
  lod=by_year[year][m['tract_geoid']]
  wac=int(lod['wac']);rac=int(lod['rac']);net=wac-rac; daytime=pop+net
  proxy.append({'tract_geoid':m['tract_geoid'],'county':m['county'],'year':year,
  'resident_population_fixed_acs5_2019_2023':pop,
  'resident_population_acs5_moe_90pct':moe,
  'resident_population_relative_moe':m['population_relative_moe'],
  'wac':wac,'rac':rac,'net_jobs_wac_minus_rac':net,'daytime_population_proxy':daytime,
  'net_jobs_per_resident':round(net/pop,6) if pop else '',
  'flag_population_under_500':int(pop<500),
  'flag_relative_moe_gt_50pct':m['flag_relative_moe_gt_50pct'],
  'flag_nonpositive_proxy':int(daytime<=0),
  'population_source':'2023 ACS 5-Year B01003 (2019-2023 period, Census Bureau)',
  'method':'Fixed ACS5 P (same baseline for both years) + year-specific LODES WAC - RAC',
  'moe_scope':'90% MOE of resident population P only; NOT MOE for daytime proxy; does NOT include LODES uncertainty'})
proxy.sort(key=lambda x:(x['tract_geoid'],x['year']))
assert len(proxy)==3530,len(proxy)
dump_csv(OUTPUTS/'tract_daytime_proxy_fixed_2023P_2019_2023_with_population_MOE.csv',proxy,list(proxy[0]))

summary=[]
for code,name in COUNTIES.items():
 rows=[r for r in acs if r['county_geoid']==code]
 land=[r for r in joined if r['county_geoid']==code]
 summary.append({'county':name,'county_geoid':code,'official_acs_tracts':len(rows),'mtc_land_tracts':len(land),'water_tracts_missing_in_mtc':len(rows)-len(land),
  'official_2023_population_sum':sum(r['acs5_2019_2023_population_estimate'] for r in rows),
  'mtc_2023_population_sum':sum(int(r['population_2023']) for r in land),
  'official_equals_mtc':int(sum(r['acs5_2019_2023_population_estimate'] for r in rows)==sum(int(r['population_2023']) for r in land))})
dump_csv(OUTPUTS/'county_2023_population_reconciliation.csv',summary,list(summary[0]))
qa={'reference_period':'2019–2023 ACS 5-year (release 2023)','table':'B01003',
 'official_acs5_tract_rows_9_counties':len(acs),'mtc_land_tracts':len(mtc),
 'matched_MTC_to_official_acs5':len(joined),'mismatched_2023_population_estimates':0,
 'official_only_water_tracts':len(extra),'LODES_combined_2019_2023_rows':len(proxy),
 'nonpositive_daytime_proxy_rows':sum(r['flag_nonpositive_proxy'] for r in proxy),
 'resident_population_zero_tracts':sum(r['flag_population_zero'] for r in joined),
 'resident_population_under_500_tracts':sum(r['flag_population_under_500'] for r in joined),
 'resident_population_relative_moe_gt_50pct_tracts':sum(r['flag_relative_moe_gt_50pct'] for r in joined),
 'county_totals_match':all(r['official_equals_mtc']==1 for r in summary),
 'warning':'90% ACS MOE is for resident population only, not full daytime proxy; LODES has no matching ACS MOE',
 'coverage_note':'2020 MTC population_2020 is ACS 5-year (2016–2020), NOT decennial count and not substitute for 2020 ACS1 WFH'}
with open(OUTPUTS/'tract_validation.json','w',encoding='utf8') as fp:json.dump(qa,fp,ensure_ascii=False,indent=2)
print(json.dumps(qa,indent=2,ensure_ascii=False))
