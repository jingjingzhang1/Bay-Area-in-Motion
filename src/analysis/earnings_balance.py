"""HF2a: annual and period-average employment balances by nominal earnings band."""
from pathlib import Path
import pandas as pd
from src.utils.config import BAY_AREA_COUNTIES, TABLES_DIR, WAC_RAC_TRACTS, YEARS

BANDS = {'CE01': '<= $1,250/month', 'CE02': '$1,251-$3,333/month', 'CE03': '> $3,333/month'}
PERIODS = {2017:'pre', 2018:'pre', 2019:'pre', 2020:'during', 2021:'during', 2022:'post', 2023:'post'}


def validate_input(frame):
    """Reject incomplete panels and inconsistent band totals rather than impute."""
    cols = ['WAC', 'RAC'] + [f'{side}_{band}' for side in ('WAC','RAC') for band in BANDS]
    required = ['tract_geoid','county_fips','year'] + cols
    if set(required) - set(frame):
        raise ValueError('Missing columns: ' + str(sorted(set(required)-set(frame))))
    if frame[required].isna().any().any() or frame.duplicated(['tract_geoid','year']).any():
        raise ValueError('Null values or duplicate tract-year keys')
    if not frame.tract_geoid.str.fullmatch(r'06\d{9}').all():
        raise ValueError('Expected 11-digit California tract GEOIDs')
    if not frame.county_fips.eq(frame.tract_geoid.str[:5]).all():
        raise ValueError('County and tract GEOIDs disagree')
    if set(frame.county_fips) != set(BAY_AREA_COUNTIES) or set(frame.year) != set(YEARS):
        raise ValueError('Expected all nine counties and years 2017-2023')
    if not frame.groupby('tract_geoid').year.nunique().eq(len(YEARS)).all():
        raise ValueError('Incomplete tract-year panel')
    if (frame[cols] < 0).any().any() or (frame[cols] % 1 != 0).any().any():
        raise ValueError('Job counts must be nonnegative integers')
    for side in ('WAC','RAC'):
        if not frame[[f'{side}_{b}' for b in BANDS]].sum(axis=1).eq(frame[side]).all():
            raise ValueError(f'{side} earnings bands do not sum to total')


def build_tables(frame):
    """Return tract/county annual, period means and changes; no percent change on signed balances."""
    validate_input(frame)
    parts = []
    for band, label in BANDS.items():
        part = frame[['tract_geoid','county_fips','year',f'WAC_{band}',f'RAC_{band}']].rename(columns={f'WAC_{band}':'wac_jobs',f'RAC_{band}':'rac_jobs'})
        part = part.assign(earnings_band=band, monthly_earnings=label)
        parts.append(part)
    tract = pd.concat(parts, ignore_index=True)
    metrics = ['wac_jobs','rac_jobs','net_jobs']
    tract['net_jobs'] = tract.wac_jobs - tract.rac_jobs
    county = tract.groupby(['county_fips','year','earnings_band','monthly_earnings'],as_index=False)[metrics].sum()
    tables = {}
    for scale, annual in [('tract',tract),('county',county)]:
        annual = annual.copy()
        annual['county_name'] = annual.county_fips.map(BAY_AREA_COUNTIES)
        annual['period'] = annual.year.map(PERIODS)
        keys = (['tract_geoid'] if scale == 'tract' else []) + ['county_fips','county_name','earnings_band','monthly_earnings']
        annual = annual.sort_values(keys+['year']).reset_index(drop=True)
        group = annual.groupby(keys+['period'],as_index=False)
        period = group[metrics].mean().rename(columns={m:'mean_annual_'+m for m in metrics})
        period = period.merge(group.year.nunique().rename(columns={'year':'n_years'}),on=keys+['period'],validate='one_to_one')
        wide = period.pivot(index=keys,columns='period',values='mean_annual_net_jobs').reset_index().rename_axis(None,axis=1)
        for before, after in [('pre','during'),('pre','post'),('during','post')]:
            wide[f'{after}_minus_{before}_net_jobs'] = wide[after]-wide[before]
        tables[f'hf2a_{scale}_annual'] = annual
        tables[f'hf2a_{scale}_period_means'] = period
        tables[f'hf2a_{scale}_period_changes'] = wide
    # County aggregation must preserve each year's regional totals for every band.
    pd.testing.assert_frame_equal(tract.groupby(['year','earnings_band'])[metrics].sum(),county.groupby(['year','earnings_band'])[metrics].sum())
    return tables


def write_tables(frame, output_dir=TABLES_DIR):
    tables = build_tables(frame)
    Path(output_dir).mkdir(parents=True,exist_ok=True)
    for name, table in tables.items():
        table.to_csv(Path(output_dir)/f'{name}.csv',index=False)
    return tables


if __name__ == '__main__':
    frame = pd.read_csv(WAC_RAC_TRACTS,dtype={'tract_geoid':str,'county_fips':str})
    for name, table in write_tables(frame).items():
        print(f'{name}: {len(table):,} rows')
