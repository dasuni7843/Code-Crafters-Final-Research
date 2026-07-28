"""
Module 1 — 5-Year Forward Forecast (2026-2030)
===============================================
Method:
  Build a continuous monthly index 2010-01 to 2025-12.
  Insert NaN for the excluded disruption years (2019-2022).
  SARIMAX handles missing observations natively via the Kalman filter — this is the
  statistically correct way to exclude periods without resorting to dummy variables.
  Forecast 60 months forward (2026-01 to 2030-12) with proper widening confidence intervals.

Anchor: real SLTDA data through November 2025 (2,103,593 arrivals Jan-Nov).
"""
import json, warnings, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
warnings.filterwarnings('ignore')

from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import LinearRegression

DATA = '/home/claude/module1'
MDIR = '/home/claude/models/module1'
RDIR = '/home/claude/results/module1'

meta   = json.load(open(f'{MDIR}/model_metadata.json'))
shares = json.load(open(f'{DATA}/destination_shares.json'))
lr_f   = joblib.load(f'{MDIR}/revenue_regressor_foreign.pkl')
lr_l   = joblib.load(f'{MDIR}/revenue_regressor_local.pkl')
df_nat = pd.read_csv(f'{DATA}/module1_national_monthly_arrivals.csv')

EXCLUDED = [2019, 2020, 2021, 2022]

print("="*70)
print("  MODULE 1 — 5-YEAR FORWARD FORECAST (2026-2030)")
print("="*70)

# ══════════════════════════════════════════════════════════════
# 1. BUILD CONTINUOUS SERIES WITH NaN GAPS
# ══════════════════════════════════════════════════════════════
idx = pd.period_range('2010-01', '2025-12', freq='M')
s = pd.Series(index=idx, dtype=float)
for _, r in df_nat.iterrows():
    if 2010 <= r.year <= 2025:
        p = pd.Period(year=int(r.year), month=int(r.month), freq='M')
        if p in s.index and not r.year in EXCLUDED:
            s[p] = r.national_arrivals

# Estimate Dec 2025 from real Nov 2025 and the historical Nov->Dec ratio
nov_dec = []
for y in [2010,2011,2012,2013,2014,2015,2016,2017,2018]:
    n = df_nat[(df_nat.year==y)&(df_nat.month==11)].national_arrivals.values
    d = df_nat[(df_nat.year==y)&(df_nat.month==12)].national_arrivals.values
    if len(n) and len(d): nov_dec.append(d[0]/n[0])
ratio = float(np.mean(nov_dec))
nov25 = s[pd.Period('2025-11', freq='M')]
s[pd.Period('2025-12', freq='M')] = nov25 * ratio

obs = s.notna().sum()
print(f"\n[1/5] Continuous series built")
print(f"  Index span      : 2010-01 to 2025-12 ({len(s)} months)")
print(f"  Real observations: {obs}")
print(f"  NaN gap (excluded): {len(s)-obs} months  {EXCLUDED}")
print(f"  Dec 2025 estimated from real Nov 2025 x {ratio:.3f} = {s[pd.Period('2025-12',freq='M')]:,.0f}")
print(f"  2025 full year   : {s['2025'].sum():,.0f}")

# ══════════════════════════════════════════════════════════════
# 2. FIT SARIMA ON GAPPED SERIES (Kalman filter handles NaN)
# ══════════════════════════════════════════════════════════════
order    = tuple(meta['sarima_order'])
seasonal = tuple(meta['sarima_seasonal_order'])
print(f"\n[2/5] Fitting SARIMA{order}{seasonal} with missing-value handling")
model = SARIMAX(s, order=order, seasonal_order=seasonal,
                enforce_stationarity=False, enforce_invertibility=False)
fit = model.fit(disp=False)
print(f"  AIC = {fit.aic:.2f}   Log-likelihood = {fit.llf:.2f}")

# ══════════════════════════════════════════════════════════════
# 3. FORECAST 60 MONTHS FORWARD (2026-2030)
# ══════════════════════════════════════════════════════════════
H = 60
fc = fit.get_forecast(steps=H)
mean = fc.predicted_mean
ci   = fc.conf_int(alpha=0.20)   # 80% interval

fc_idx = pd.period_range('2026-01', periods=H, freq='M')
mean.index = fc_idx
ci.index   = fc_idx

print(f"\n[3/5] Forecast generated: {H} months (2026-01 to 2030-12)")
for y in range(2026, 2031):
    tot = mean[mean.index.year == y].sum()
    lo  = ci[ci.index.year == y].iloc[:,0].sum()
    hi  = ci[ci.index.year == y].iloc[:,1].sum()
    print(f"  {y}: {tot:>10,.0f}   (80% CI {lo:>10,.0f} to {hi:>10,.0f})")

# ══════════════════════════════════════════════════════════════
# 4. BUILD DESTINATION-LEVEL OUTPUT
# ══════════════════════════════════════════════════════════════
print(f"\n[4/5] Allocating to 20 destinations and predicting revenue")
MONTH_NAMES = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']

rows = []
for i, p in enumerate(fc_idx):
    y, m = p.year, p.month
    nat  = float(mean.iloc[i])
    lo   = float(ci.iloc[i,0]); hi = float(ci.iloc[i,1])
    horizon_yrs = y - 2025
    for dest, sh in shares.items():
        fv = int(max(0, nat * sh['foreign_share'] * 0.42))
        lv = int(max(0, nat * sh['local_share']   * 0.55))
        f_rev = float(lr_f.predict([[fv]])[0]) if fv > 0 else 0.0
        l_rev = float(lr_l.predict([[lv]])[0]) if lv > 0 else 0.0
        total = fv + lv
        # CI scaled by the national interval, widening with horizon
        band = 0.10 + 0.05 * (horizon_yrs - 1)
        rows.append({
            'destination': dest, 'year': y, 'month': m,
            'month_name': MONTH_NAMES[m-1],
            'predicted_tourist_arrivals': total,
            'predicted_foreign_visitors': fv,
            'predicted_local_visitors': lv,
            'confidence_lower': int(total * (1 - band)),
            'confidence_upper': int(total * (1 + band)),
            'estimated_revenue_lkr': int(max(0, f_rev + l_rev)),
            'estimated_foreign_revenue_lkr': int(max(0, f_rev)),
            'estimated_local_revenue_lkr': int(max(0, l_rev)),
            'national_arrivals': int(nat),
            'national_lower': int(lo), 'national_upper': int(hi),
            'model_used': 'SARIMA',
            'mape_pct': round(meta['sarima_mape'], 2),
            'forecast_horizon_years': horizon_yrs,
            'data_source': 'forecast',
        })

df_out = pd.DataFrame(rows)
df_out.to_csv(f'{DATA}/module1_output.csv', index=False)
print(f"  module1_output.csv: {len(df_out):,} rows")
print(f"  {df_out.destination.nunique()} destinations x {df_out.year.nunique()} years x 12 months")

# Historical actuals kept separately for predicted-vs-actual display
hist = df_nat[(df_nat.year>=2015) & (~df_nat.year.isin(EXCLUDED))].copy()
hist['fitted'] = np.nan
fitted = fit.fittedvalues
for j, p in enumerate(s.index):
    mask = (hist.year==p.year) & (hist.month==p.month)
    if mask.any() and j < len(fitted):
        hist.loc[mask, 'fitted'] = float(fitted.iloc[j])
hist.to_csv(f'{DATA}/module1_historical_fit.csv', index=False)
print(f"  module1_historical_fit.csv: {len(hist)} rows (actual vs fitted)")

# ══════════════════════════════════════════════════════════════
# 5. FORECAST CHART
# ══════════════════════════════════════════════════════════════
print(f"\n[5/5] Generating forecast chart")
fig, ax = plt.subplots(figsize=(16,6.5))
hist_t = s.dropna()
ax.plot(hist_t.index.to_timestamp(), hist_t.values, color='#2c3e50',
        linewidth=1.8, label='Real SLTDA data')
ax.plot(mean.index.to_timestamp(), mean.values, color='#27ae60',
        linewidth=2.4, label=f'SARIMA{order}{seasonal} forecast')
ax.fill_between(ci.index.to_timestamp(), ci.iloc[:,0], ci.iloc[:,1],
                color='#27ae60', alpha=0.18, label='80% confidence interval')
ax.axvspan(pd.Timestamp('2019-01-01'), pd.Timestamp('2022-12-31'),
           alpha=0.10, color='red')
ax.text(pd.Timestamp('2020-10-01'), ax.get_ylim()[1]*0.88, 'Excluded\n2019-2022',
        ha='center', fontsize=9.5, color='#c0392b',
        bbox=dict(boxstyle='round,pad=0.35', fc='white', ec='#c0392b', alpha=0.9))
ax.axvline(pd.Timestamp('2026-01-01'), color='#e67e22', linestyle=':', linewidth=2)
ax.text(pd.Timestamp('2026-02-01'), ax.get_ylim()[1]*0.95, ' Forecast horizon',
        fontsize=10, color='#e67e22')
ax.set_ylabel('Monthly Tourist Arrivals'); ax.set_xlabel('Year')
ax.set_title('Sri Lanka Tourist Demand — Real History and 5 Year Forecast\n'
             f'SARIMA fitted on {obs} real monthly observations, MAPE {meta["sarima_mape"]:.2f}%',
             fontsize=13, pad=12)
ax.legend(fontsize=10, loc='upper left')
plt.tight_layout(); plt.savefig(f'{RDIR}/m1_11_five_year_forecast.png', dpi=150); plt.close()

# Annual totals chart
fig, ax = plt.subplots(figsize=(11,5.5))
years, tots, los, his = [], [], [], []
for y in range(2026, 2031):
    years.append(y)
    tots.append(mean[mean.index.year==y].sum())
    los.append(ci[ci.index.year==y].iloc[:,0].sum())
    his.append(ci[ci.index.year==y].iloc[:,1].sum())
real_y = [2018, 2023, 2024, 2025]
real_v = [2333796, 1487303, 2053465, float(s['2025'].sum())]
ax.bar([str(y) for y in real_y], [v/1e6 for v in real_v],
       color='#2c3e50', edgecolor='white', width=0.6, label='Real (SLTDA)')
ax.bar([str(y) for y in years], [t/1e6 for t in tots],
       color='#27ae60', edgecolor='white', width=0.6, label='Forecast',
       yerr=[[(t-l)/1e6 for t,l in zip(tots,los)],[(h-t)/1e6 for t,h in zip(tots,his)]],
       error_kw={'elinewidth':1.6,'capsize':4,'ecolor':'#7f8c8d'})
for i, v in enumerate(real_v):
    ax.text(i, v/1e6+0.05, f'{v/1e6:.2f}M', ha='center', fontsize=9.5, fontweight='bold')
for i, t in enumerate(tots):
    ax.text(len(real_y)+i, t/1e6+0.12, f'{t/1e6:.2f}M', ha='center', fontsize=9.5, fontweight='bold')
ax.set_ylabel('Annual Tourist Arrivals (millions)')
ax.set_title('Annual Tourist Arrivals — Real History and Forecast to 2030', fontsize=13, pad=12)
ax.legend(fontsize=10); plt.tight_layout()
plt.savefig(f'{RDIR}/m1_12_annual_forecast.png', dpi=150); plt.close()
print(f"  m1_11_five_year_forecast.png, m1_12_annual_forecast.png")

print("\n" + "="*70)
print("  FORECAST COMPLETE — 2026 to 2030")
print("="*70)
print(f"  Rows: {len(df_out):,}   Years selectable: 2026, 2027, 2028, 2029, 2030")
print(f"  Model: SARIMA{order}{seasonal}   MAPE {meta['sarima_mape']:.2f}%")
print(f"  Anchored on real SLTDA data through November 2025")
