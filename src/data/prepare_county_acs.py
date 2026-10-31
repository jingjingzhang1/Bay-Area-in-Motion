#!/usr/bin/env python3
"""Rebuild CP101 Bay Area county ACS1 data, 2017-2023, with official count MOEs.
Inputs bundled inside data/raw/chiahao/county/. 2020 has no standard ACS1 dataset.
2021-2022 Napa B08301 is absent in official download; do not invent zeros.
B01003 official MOE is ***** (controlled) in all nine counties in all published years.
Tract-level ACS5 data is built separately by src/data/prepare_tract_acs.py.
"""
from pathlib import Path
import csv, zipfile, io, json, math
ROOT=Path(__file__).resolve().parents[2]
INPUT=ROOT/'data/raw/chiahao/county'
OUTPUT=ROOT/'data/processed/chiahao'
OUTPUT.mkdir(parents=True, exist_ok=True)
COUNTIES={'06001':'Alameda','06013':'Contra Costa','06041':'Marin','06055':'Napa','06075':'San Francisco','06081':'San Mateo','06085':'Santa Clara','06095':'Solano','06097':'Sonoma'}
YEARS=(2017,2018,2019,2021,2022,2023)

def csv_rows(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,columns):
    with open(p,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
def census(t,year):
    archive=(INPUT/f'ACS2017_{t}_official.zip') if year==2017 else (INPUT/f'ACS2018_2019_2021_2022_2023_{t}_official.zip')
    with zipfile.ZipFile(archive) as z:
        with z.open(f'ACSDT1Y{year}.{t}-Data.csv') as stream:
            data=list(csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline='')))
    assert data[0]['GEO_ID']=='Geography',f'Unexpected Census header: {t} {year}'
    valid=[r for r in data[1:] if r['GEO_ID'].startswith('0500000US')]
    result={r['GEO_ID'][-5:]:r for r in valid}
    assert len(valid)==len(result) and set(result).issubset(COUNTIES),(t,year,len(valid),list(result))
    expected=set(COUNTIES)-({'06055'} if t=='B08301' and year in (2021,2022) else set())
    assert set(result)==expected,(t,year,set(result)^expected)
    return result

def number(v):
    if v is None or str(v).strip() in ('','nan','None','-','*****','**','N','(X)','null'):return ''
    v=float(v)
    return int(v) if v.is_integer() else v

raw={('B08301',y):census('B08301',y) for y in YEARS}
raw.update({('B08604',y):census('B08604',y) for y in YEARS})
raw.update({('B01003',y):census('B01003',y) for y in YEARS})
base_wfh={(int(r['year']),r['GEOID']):r for r in csv_rows(INPUT/'county_wfh_acs1_2017_2024.csv')}
base_work={(int(r['year']),r['GEOID']):r for r in csv_rows(INPUT/'county_workplace_acs1_2018_2024.csv')}
base_pop={(int(r['year']),r['GEOID']):r for r in csv_rows(INPUT/'county_population_acs1_2018_2024.csv')}
county_lodes={(int(r['year']),r['county_fips']):r for r in csv_rows(INPUT/'county_lodes_acs_merged_previous.csv')}
columns=['year','county_geoid','county','acs1_release','population_B01003_estimate','population_B01003_moe_raw','population_B01003_moe_status','workers_residence_B08301_estimate','workers_residence_B08301_moe_90pct','worked_from_home_B08301_estimate','worked_from_home_B08301_moe_90pct','wfh_share_percent','workers_workplace_B08604_estimate','workers_workplace_B08604_moe_90pct','net_workers_ACS_workplace_minus_residence','acs_commuter_adjusted_daytime_proxy','lodes_WAC','lodes_RAC','lodes_commuter_adjusted_daytime_proxy','lodes_minus_acs_daytime_proxy','estimate_coverage','moe_count_coverage','notes']
records=[]
for year in range(2017,2024):
 for geo,county in COUNTIES.items():
    r={col:'' for col in columns}
    r.update(year=year,county_geoid=geo,county=county,acs1_release='ACS_1_year' if year!=2020 else 'unavailable_2020_standard_ACS1')
    if year==2020:
        r.update(estimate_coverage='2020_standard_ACS1_unavailable',moe_count_coverage='2020_unavailable',notes='No standard ACS 1-year release; not interpolated.')
        records.append(r);continue
    b083=raw[('B08301',year)].get(geo);b086=raw[('B08604',year)][geo]
    p=raw[('B01003',year)][geo]
    pt=base_pop.get((year,geo))
    w=base_wfh.get((year,geo)); q=base_work.get((year,geo))
    r['population_B01003_estimate']=number(p['B01003_001E'])
    r['population_B01003_moe_raw']=p['B01003_001M']
    assert p['B01003_001M']=='*****',('unexpected B01003 MOE marker',year,geo,p['B01003_001M'])
    r['population_B01003_moe_status']='controlled_estimate_no_numeric_MOE'
    if pt is not None:
        assert r['population_B01003_estimate']==number(pt['population']),(year,geo,'official population vs prior team CSV mismatch')
    r['workers_workplace_B08604_estimate']=number(b086['B08604_001E'])
    r['workers_workplace_B08604_moe_90pct']=number(b086['B08604_001M'])
    if b083:
        r['workers_residence_B08301_estimate']=number(b083['B08301_001E'])
        r['workers_residence_B08301_moe_90pct']=number(b083['B08301_001M'])
        r['worked_from_home_B08301_estimate']=number(b083['B08301_021E'])
        r['worked_from_home_B08301_moe_90pct']=number(b083['B08301_021M'])
        if w:
            for official,field in [('B08301_001E','workers_residence'),('B08301_021E','work_from_home')]:
                assert number(b083[official])==number(w[field]),(year,geo,official,'team estimate mismatch')
    else:
        assert geo=='06055' and year in (2021,2022) and (w is None or number(w['workers_residence'])==''),(year,geo)
    if q: assert number(b086['B08604_001E'])==number(q['workers_workplace']),(year,geo,'B08604 mismatch')
    pop=r['population_B01003_estimate'];res=r['workers_residence_B08301_estimate'];wfh=r['worked_from_home_B08301_estimate'];work=r['workers_workplace_B08604_estimate']
    if res!='' and wfh!='' and res!=0:r['wfh_share_percent']=round(wfh/res*100,5)
    if res!='' and work!='':r['net_workers_ACS_workplace_minus_residence']=work-res
    if pop!='' and r['net_workers_ACS_workplace_minus_residence']!='':r['acs_commuter_adjusted_daytime_proxy']=pop+r['net_workers_ACS_workplace_minus_residence']
    l=county_lodes.get((year,geo))
    if l:
        r['lodes_WAC']=number(l['WAC']);r['lodes_RAC']=number(l['RAC'])
        if pop!='' and r['lodes_WAC']!='' and r['lodes_RAC']!='':
            r['lodes_commuter_adjusted_daytime_proxy']=pop+r['lodes_WAC']-r['lodes_RAC']
            if r['acs_commuter_adjusted_daytime_proxy']!='':r['lodes_minus_acs_daytime_proxy']=r['lodes_commuter_adjusted_daytime_proxy']-r['acs_commuter_adjusted_daytime_proxy']
    r['estimate_coverage']='complete_B01003_B08301_B08604' if all(x!='' for x in (pop,res,work)) else 'B08301_missing_official_Napa_2021_2022'
    if b083 and all(r[k]!='' for k in ('workers_residence_B08301_moe_90pct','worked_from_home_B08301_moe_90pct','workers_workplace_B08604_moe_90pct')):
        r['moe_count_coverage']='available_B08301_B08604_B01003_controlled'
    else:r['moe_count_coverage']='B08604_and_B01003_available_B08301_missing_official'
    if not b083:r['notes']='Napa B08301 absent from official ACS1 download for 2021/2022; not zero. Official B01003 MOE is ***** (controlled). B08604 numeric MOE available.'
    else:r['notes']='Official B01003 MOE raw = ***** (controlled); B08301 and B08604 count MOEs numeric.'
    records.append(r)
assert len(records)==63
assert len({(r['year'],r['county_geoid']) for r in records})==63
assert sum(r['estimate_coverage']=='complete_B01003_B08301_B08604' for r in records)==52
assert sum(r['estimate_coverage']=='2020_standard_ACS1_unavailable' for r in records)==9
assert sum(r['estimate_coverage']=='B08301_missing_official_Napa_2021_2022' for r in records)==2
write(OUTPUT/'county_ACS1_2017_2023_estimates_MOE_availability.csv',records,columns)
write(OUTPUT/'county_2017_three_official_ACS_tables_with_MOE.csv',[r for r in records if r['year']==2017],columns)
summary=[]
for year in range(2017,2024):
 rr=[r for r in records if r['year']==year]
 summary.append({'year':year,'counties':len(rr),'B01003_population_estimates':sum(r['population_B01003_estimate']!='' for r in rr),
     'B08301_resident_workers_estimates':sum(r['workers_residence_B08301_estimate']!='' for r in rr),
     'B08301_WFH_estimates':sum(r['worked_from_home_B08301_estimate']!='' for r in rr),
     'B08604_workplace_workers_estimates':sum(r['workers_workplace_B08604_estimate']!='' for r in rr),
     'B08301_resident_workers_numeric_MOE':sum(r['workers_residence_B08301_moe_90pct']!='' for r in rr),
     'B08301_WFH_numeric_MOE':sum(r['worked_from_home_B08301_moe_90pct']!='' for r in rr),
     'B08604_workplace_workers_numeric_MOE':sum(r['workers_workplace_B08604_moe_90pct']!='' for r in rr),
     'B01003_population_numeric_MOE':sum(r['population_B01003_moe_status']!='controlled_estimate_no_numeric_MOE' and r['population_B01003_moe_raw']!='' for r in rr),
     'B01003_population_MOE_source_status':'2020 no standard ACS1' if year==2020 else 'official B01003 MOE ***** (controlled; no numeric MOE)',
     '2020_release_status':'No standard ACS1 2020' if year==2020 else '',
     'additional_MOE_needed':'No further B01003 MOE downloads needed; ***** is an official control marker' if year!=2020 else 'No standard 2020 ACS1'})
write(OUTPUT/'county_year_data_MOE_coverage_audit.csv',summary,list(summary[0]))
rs23=[r for r in records if r['year']==2023]
assert all(r['lodes_minus_acs_daytime_proxy']!='' for r in rs23)
write(OUTPUT/'county_2023_LODES_vs_ACS_comparison.csv',rs23,columns)
sf17=next(r for r in records if r['year']==2017 and r['county']=='San Francisco')
sf23=next(r for r in records if r['year']==2023 and r['county']=='San Francisco')
checks={
 'bay_area_counties':9, 'years':[2017,2018,2019,2020,2021,2022,2023], 'county_year_panel_rows':len(records),
 'official_B08301_county_records':sum(len(raw[('B08301',y)]) for y in YEARS),
 'official_B08604_county_records':sum(len(raw[('B08604',y)]) for y in YEARS),
 'official_B08301_resident_and_WFH_numeric_MOEs':sum(r['workers_residence_B08301_moe_90pct']!='' and r['worked_from_home_B08301_moe_90pct']!='' for r in records),
 'official_B08604_numeric_MOEs':sum(r['workers_workplace_B08604_moe_90pct']!='' for r in records),
 'county_rows_full_B01003_B08301_B08604':52, 'missing_2020_standard_ACS1_rows':9,'missing_official_Napa_B08301_2021_2022':2,
 '2017_B01003_MOE':'***** official controlled-estimate suppression in all nine counties',
 '2018_2023_B01003_MOE':'All official 2018/2019/2021/2022/2023 county B01003 records mark MOE as ***** (controlled); no numeric MOE imputed',
 'san_francisco_WFH_share_2017_pct':sf17['wfh_share_percent'], 'san_francisco_WFH_share_2023_pct':sf23['wfh_share_percent'],
 'sf_2023_LODES_minus_ACS_proxy':sf23['lodes_minus_acs_daytime_proxy'],
 'moe_scope':'Official B08301/B08604 count 90% MOE. NOT a margin of error for their ratio or daytime proxy.',
 'provenance':'Official Census ACS1 B01003, B08301, B08604 ZIPs for 2017–2019 and 2021–2023; 2018–2023 B01003 estimates checked against previous team CSV.'}
(OUTPUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
# Table of source availability for handoff
with open(OUTPUT/'official_download_coverage.csv','w',newline='',encoding='utf-8') as f:
 ww=csv.writer(f);ww.writerow(['year','table','county_rows_in_official_Census_download','counties_missing_in_official_download','source'])
 for y in YEARS:
  for t in ('B08301','B08604'):
   dd=raw[(t,y)];ww.writerow([y,t,len(dd),'; '.join(COUNTIES[k] for k in COUNTIES if k not in dd),('ACS2017_'+t+'_official.zip' if y==2017 else 'ACS2018_2019_2021_2022_2023_'+t+'_official.zip')])
 for y in YEARS:
  ww.writerow([y,'B01003',len(raw[('B01003',y)]),'','ACS2017_B01003_official.zip' if y==2017 else 'ACS2018_2019_2021_2022_2023_B01003_official.zip'])
print(json.dumps(checks,ensure_ascii=False,indent=2))
