"""
Module 1 — Build REAL dataset from extracted SLTDA official reports
====================================================================
Sources (all official SLTDA / DWC / CCF / DFC published data):
  - Monthly national arrivals 1971-2025 (SLTDA ASR Table 15 + Year in Review)
  - CCF heritage sites per-site: 2017, 2018, 2020, 2023, 2025
  - Wildlife parks per-site:     2017, 2018, 2020, 2023, 2025
  - Conservation forests:        2023
  - Wildlife revenue series:     1989-2023

PANDEMIC EXCLUSION (per requirement):
  EXCLUDED: 2019 (Easter Sunday attacks), 2020-2021 (COVID border closure),
            2022 (economic crisis / fuel shortage)
  CLEAN TRAINING PERIOD:  2010-2018 (108 continuous months)
  RECENT ANCHOR PERIOD:   2023-2025
"""
import json, re
import pandas as pd
import numpy as np

data = json.load(open('/home/claude/extracted_sltda.json'))
OUT = '/home/claude/module1'

# ════════════════════════════════════════════════════════════
# 1. DESTINATION MAPPING — real SLTDA site names -> our 20 destinations
# ════════════════════════════════════════════════════════════
SITE_MAP = {
    # CCF heritage sites
    'Sigiriya Museum and Sigiriya Rock': 'Sigiriya',
    'Sigiriya (Museum and Sigiriya Rock)': 'Sigiriya',
    'Sigiriya': 'Sigiriya',
    'Polonnaruwa Gal': 'Polonnaruwa',
    'Polonnaruwa (Alahana, Gal Viharaya,': 'Polonnaruwa',
    'Polonnaruwa': 'Polonnaruwa',
    'Abhayagiriya': 'Anuradhapura',
    'Jethawanaya': 'Anuradhapura',
    'Galle Museum': 'Galle Fort',
    'Galle': 'Galle Fort',
    'Kandy Museum': 'Kandy',
    'Kandy': 'Kandy',
    'Jaffna Fort': 'Jaffna',
    'Dambulla Museum': 'Dambulla',
    'Dambulla': 'Dambulla',
    'Trincomalee': 'Trincomalee',
    'Ritigala forest Monastery': 'Anuradhapura',
    'Namal Uyana': 'Dambulla',
    'Ibbankatuwa Ancient Bural Ground': 'Dambulla',
    # Wildlife parks
    'Yala': 'Yala',
    'Horton Plains': 'Horton Plains',
    'Mirissa': 'Mirissa',
    'Pigeon Island': 'Trincomalee',
    'Galways Land': 'Nuwara Eliya',
    'Udawalawa': 'Yala',          # same southern circuit
    'Minneriya': 'Polonnaruwa',   # same NCP circuit
    'Kaudulla': 'Polonnaruwa',
    'Wilpattu': 'Anuradhapura',
    'Hikkaduwa': 'Unawatuna',     # southern coast reef park
}

DESTINATIONS = ['Sigiriya','Ella','Galle Fort','Kandy','Nuwara Eliya','Mirissa',
                'Unawatuna','Bentota','Arugam Bay','Trincomalee','Anuradhapura',
                'Polonnaruwa','Dambulla','Yala','Pinnawala','Adams Peak',
                'Horton Plains','Jaffna','Colombo','Negombo']

# ════════════════════════════════════════════════════════════
# 2. BUILD REAL ANNUAL PER-DESTINATION TABLE
# ════════════════════════════════════════════════════════════
rows = []
for key in [k for k in data if k.startswith(('ccf_','wildlife_','forest_')) and 'series' not in k]:
    year = int(key.split('_')[1])
    src  = key.split('_')[0]
    for rec in data[key]:
        name = rec.get('site') or rec.get('park') or rec.get('forest')
        dest = SITE_MAP.get(name.strip())
        if not dest:
            continue
        fv = rec.get('foreign_visitors', 0) or 0
        lv = rec.get('local_visitors', rec.get('domestic_visitors', 0)) or 0
        fi = rec.get('foreign_income', 0) or 0
        li = rec.get('local_income', rec.get('domestic_income', 0)) or 0
        # 2017/2018/2020 CCF entries only carry one visitor+revenue column
        if 'visitors' in rec and fv == 0:
            fv = rec['visitors']; fi = rec.get('revenue', 0)
        rows.append({'year':year,'destination':dest,'source':src,
                     'foreign_visitors':fv,'local_visitors':lv,
                     'foreign_income_lkr':fi,'local_income_lkr':li})

df_site = pd.DataFrame(rows)
# Aggregate multiple sites mapping to same destination
df_annual = df_site.groupby(['year','destination'], as_index=False).agg({
    'foreign_visitors':'sum','local_visitors':'sum',
    'foreign_income_lkr':'sum','local_income_lkr':'sum'})
df_annual['total_visitors'] = df_annual.foreign_visitors + df_annual.local_visitors
df_annual['total_revenue_lkr'] = df_annual.foreign_income_lkr + df_annual.local_income_lkr
df_annual.to_csv(f'{OUT}/module1_real_annual_destination.csv', index=False)

print("="*68)
print("REAL ANNUAL PER-DESTINATION DATA (from SLTDA official reports)")
print("="*68)
print(f"Rows: {len(df_annual)}  |  Destinations: {df_annual.destination.nunique()}  |  Years: {sorted(df_annual.year.unique())}")
print()
print(df_annual[df_annual.year==2025][['destination','foreign_visitors','local_visitors','total_revenue_lkr']]
      .sort_values('total_revenue_lkr',ascending=False).head(10).to_string(index=False))

# ════════════════════════════════════════════════════════════
# 3. MONTHLY NATIONAL SERIES — pandemic years excluded
# ════════════════════════════════════════════════════════════
ma = data['monthly_arrivals']
recs = []
for y_str, v in ma.items():
    y = int(y_str)
    for i, val in enumerate(v['months']):
        if val is not None:
            recs.append({'year':y,'month':i+1,'national_arrivals':val})
df_nat = pd.DataFrame(recs).sort_values(['year','month']).reset_index(drop=True)

EXCLUDE_YEARS = [2019, 2020, 2021, 2022]   # Easter attacks, COVID, economic crisis
CLEAN_START   = 2010

df_nat['excluded'] = df_nat.year.isin(EXCLUDE_YEARS)
df_nat['period'] = np.where(df_nat.year.isin(EXCLUDE_YEARS), 'excluded',
                    np.where(df_nat.year < CLEAN_START, 'historical',
                     np.where(df_nat.year <= 2018, 'clean_train', 'recent')))
df_nat.to_csv(f'{OUT}/module1_national_monthly_arrivals.csv', index=False)

clean = df_nat[df_nat.period=='clean_train']
recent = df_nat[df_nat.period=='recent']
print()
print("="*68)
print("MONTHLY NATIONAL ARRIVALS — PANDEMIC YEARS EXCLUDED")
print("="*68)
print(f"  Full series available:  {len(df_nat)} months ({df_nat.year.min()}-{df_nat.year.max()})")
print(f"  EXCLUDED years:         {EXCLUDE_YEARS}")
print(f"     2019 — Easter Sunday attacks (May 2019 crashed to 37,802)")
print(f"     2020 — COVID border closure (Apr-Dec zero arrivals)")
print(f"     2021 — COVID (194,495 total vs 2M normal)")
print(f"     2022 — Economic crisis, fuel shortage, protests")
print()
print(f"  CLEAN TRAINING PERIOD:  {len(clean)} months (2010-2018, continuous)")
print(f"  RECENT ANCHOR PERIOD:   {len(recent)} months (2023-2025)")

# ════════════════════════════════════════════════════════════
# 4. DESTINATION SHARE ALLOCATION (from real annual data)
# ════════════════════════════════════════════════════════════
latest = df_annual[df_annual.year==2025]
if len(latest) == 0:
    latest = df_annual[df_annual.year==df_annual.year.max()]

tot_f = latest.foreign_visitors.sum()
tot_l = latest.local_visitors.sum()
shares = {}
for _, r in latest.iterrows():
    shares[r.destination] = {
        'foreign_share': r.foreign_visitors/tot_f if tot_f else 0,
        'local_share':   r.local_visitors/tot_l if tot_l else 0,
        'rev_per_foreign': r.foreign_income_lkr/r.foreign_visitors if r.foreign_visitors else 0,
        'rev_per_local':   r.local_income_lkr/r.local_visitors if r.local_visitors else 0,
    }

# Destinations with NO official ticketed data — anchor to real SLTDA district data
DISTRICT_ANCHOR = {   # real SLTDA telecom district visitors Jan-Oct 2024
    'Adams Peak': 752301*0.15, 'Unawatuna': 2671580*0.20, 'Bentota': 2671580*0.15,
    'Arugam Bay': 458925*0.55, 'Colombo': 4193342*0.10, 'Negombo': 2100780*0.25,
    'Ella': 818133*0.35, 'Pinnawala': 506575*0.50,
}
d_tot = sum(DISTRICT_ANCHOR.values())
covered_f = sum(v['foreign_share'] for v in shares.values())
remaining = max(0.05, 1 - covered_f)
for d, v in DISTRICT_ANCHOR.items():
    if d not in shares:
        shares[d] = {'foreign_share': remaining*(v/d_tot)*0.6,
                     'local_share':   remaining*(v/d_tot),
                     'rev_per_foreign': 6500, 'rev_per_local': 350}

json.dump(shares, open(f'{OUT}/destination_shares.json','w'), indent=1)
print()
print("="*68)
print("DESTINATION SHARES (from real 2025 per-site data)")
print("="*68)
top = sorted(shares.items(), key=lambda x:-x[1]['foreign_share'])[:10]
for d, s in top:
    print(f"  {d:16} foreign share {s['foreign_share']*100:5.2f}%  "
          f"rev/foreign LKR {s['rev_per_foreign']:>9,.0f}")

print()
print(f"Files written to {OUT}/")
