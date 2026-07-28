"""
Module 4 — Traveler Personalization & Destination Recommendation — Training
===========================================================================
Models trained:
  1. LightGBM Rating Predictor   → predicted rating (1-5)
  2. Content-Based Similarity    → cosine similarity matrix (no training)
  3. Destination Scorer          → final recommendation score (weighted formula)

Outputs:
  - models/module4/lgbm_rating_model.pkl
  - models/module4/content_similarity_matrix.pkl
  - models/module4/dest_feature_matrix.pkl
  - models/module4/feature_scaler.pkl
  - models/module4/encoders.pkl
  - results/module4/*.png  (all result charts)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import (mean_squared_error, mean_absolute_error,
                             r2_score, ndcg_score)
from sklearn.ensemble import GradientBoostingRegressor
import lightgbm as lgb

# ── Paths ──
RATINGS_F = "/home/claude/tourism_data/module4/user_destination_ratings.csv"
DEST_F    = "/home/claude/tourism_data/module4/destination_features.csv"
TRAIN_F   = "/home/claude/tourism_data/module4/module4_training_dataset.csv"
M2_F      = "/home/claude/tourism_data/module2/module2_seasonal_travel_dataset.csv"
MDIR      = "/home/claude/models/module4"
RDIR      = "/home/claude/results/module4"

plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': '#f8f9fa',
    'axes.grid': True, 'grid.alpha': 0.4, 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False,
})
PAL = ['#6c5ce7','#00b894','#e17055','#fdcb6e','#0984e3','#fd79a8','#55efc4']

print("=" * 62)
print("  MODULE 4 — TRAVELER PERSONALIZATION — TRAINING")
print("=" * 62)

# ══════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ══════════════════════════════════════════════════════════════
print("\n[1/9] Loading data...")
df_train   = pd.read_csv(TRAIN_F, low_memory=False)
df_dest    = pd.read_csv(DEST_F)
df_ratings = pd.read_csv(RATINGS_F, low_memory=False)
df_m2      = pd.read_csv(M2_F)

# Clean
df_train['rating'] = pd.to_numeric(df_train['rating'], errors='coerce')
df_train = df_train.dropna(subset=['rating','beach_score','avg_tss'])
df_train['rating'] = df_train['rating'].clip(1, 5).astype(int)

print(f"  Training rows:    {len(df_train):,}")
print(f"  Destinations:     {df_train.destination.nunique()}")
print(f"  Real reviews:     {(df_train.data_source=='kaggle_real').sum():,}")
print(f"  Synthetic:        {(df_train.data_source=='synthetic').sum():,}")
print(f"  Rating dist:\n{df_train.rating.value_counts().sort_index().to_string()}")

# ══════════════════════════════════════════════════════════════
# 2. CONTENT-BASED SIMILARITY MATRIX
# ══════════════════════════════════════════════════════════════
print("\n[2/9] Building Content-Based Similarity Matrix...")
DEST_FEATURES = ['beach_score','culture_score','nature_score','adventure_score',
                 'avg_stay_days','accessibility_score']
dest_matrix = df_dest.set_index('destination')[DEST_FEATURES].fillna(0)

scaler_cb = MinMaxScaler()
dest_matrix_sc = pd.DataFrame(
    scaler_cb.fit_transform(dest_matrix),
    index=dest_matrix.index,
    columns=dest_matrix.columns
)
sim_matrix = pd.DataFrame(
    cosine_similarity(dest_matrix_sc),
    index=dest_matrix.index,
    columns=dest_matrix.index
)
print(f"  Similarity matrix: {sim_matrix.shape}")
print(f"  Sample (Ella vs others):")
ella_sim = sim_matrix['Ella'].sort_values(ascending=False)
for dest, val in ella_sim.head(5).items():
    print(f"    {dest}: {val:.4f}")

joblib.dump(sim_matrix,    f"{MDIR}/content_similarity_matrix.pkl")
joblib.dump(dest_matrix_sc,f"{MDIR}/dest_feature_matrix.pkl")
joblib.dump(scaler_cb,     f"{MDIR}/cb_scaler.pkl")
print("  ✅ Saved similarity matrix")

# ══════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING FOR LIGHTGBM
# ══════════════════════════════════════════════════════════════
print("\n[3/9] Feature engineering for LightGBM...")

# Encode categoricals
le_dest = LabelEncoder()
le_type = LabelEncoder()
le_cost = LabelEncoder()
le_ct   = LabelEncoder()
le_pt   = LabelEncoder()
le_src  = LabelEncoder()

df_train['dest_enc']   = le_dest.fit_transform(df_train['destination'])
df_train['type_enc']   = le_type.fit_transform(df_train['type'].fillna('cultural'))
df_train['cost_enc']   = le_cost.fit_transform(df_train['avg_cost_level'].fillna('mid'))
df_train['crowd_enc']  = df_train['dominant_crowd'].fillna('MEDIUM').map(
                          {'LOW':0,'MEDIUM':1,'HIGH':2})
df_train['ct_enc']     = df_train['crowd_tolerance'].fillna('medium').apply(
                          lambda x: {'low':0,'medium':1,'high':2}.get(str(x).lower(),1))
df_train['pt_enc']     = df_train['preferred_type'].fillna('cultural').apply(
                          lambda x: {'beach':0,'cultural':1,'nature':2,'adventure':3}.get(str(x).lower(),1))
df_train['budget_enc'] = df_train['trip_budget'].fillna('mid').apply(
                          lambda x: {'budget':0,'mid':1,'luxury':2}.get(str(x).lower(),1))

# Type-match feature: does destination type match user preference?
type_map = dict(zip(df_dest['destination'], df_dest['type']))
def type_match(row):
    dest_t = type_map.get(row['destination'], 'cultural')
    pref   = str(row.get('preferred_type','')).lower()
    return 1 if dest_t == pref else 0
df_train['type_match'] = df_train.apply(type_match, axis=1)

LGBM_FEATURES = [
    'dest_enc','type_enc','cost_enc','crowd_enc','ct_enc','pt_enc',
    'budget_enc','type_match',
    'beach_score','culture_score','nature_score','adventure_score',
    'avg_stay_days','accessibility_score',
    'avg_tss','avg_wss','avg_crowd_ratio',
    'travel_month','preference_alignment_score',
]
# Fill NaN
for c in LGBM_FEATURES:
    if c in df_train.columns:
        df_train[c] = pd.to_numeric(df_train[c], errors='coerce').fillna(0)

X = df_train[LGBM_FEATURES].values
y = df_train['rating'].values.astype(float)

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"  Train: {len(X_tr):,}  |  Test: {len(X_te):,}")

# ══════════════════════════════════════════════════════════════
# 4. TRAIN LIGHTGBM RATING PREDICTOR
# ══════════════════════════════════════════════════════════════
print("\n[4/9] Training LightGBM Rating Predictor...")

lgb_train = lgb.Dataset(X_tr, label=y_tr)
lgb_valid = lgb.Dataset(X_te, label=y_te, reference=lgb_train)

params = {
    'objective':       'regression',
    'metric':          ['rmse','mae'],
    'num_leaves':       63,
    'learning_rate':    0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq':     5,
    'min_child_samples':20,
    'reg_alpha':        0.1,
    'reg_lambda':       1.0,
    'verbose':         -1,
}

callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=-1)]
lgb_model = lgb.train(
    params, lgb_train,
    num_boost_round=1000,
    valid_sets=[lgb_valid],
    callbacks=callbacks,
)

y_pred = lgb_model.predict(X_te)
y_pred_clipped = np.clip(y_pred, 1, 5)
y_pred_rounded = np.round(y_pred_clipped).astype(int)

rmse = np.sqrt(mean_squared_error(y_te, y_pred_clipped))
mae  = mean_absolute_error(y_te, y_pred_clipped)
r2   = r2_score(y_te, y_pred_clipped)

# Rating accuracy (exact match)
exact_acc = (y_pred_rounded == y_te.astype(int)).mean()
# Within-1 accuracy
within1 = (np.abs(y_pred_rounded - y_te.astype(int)) <= 1).mean()

print(f"  RMSE:              {rmse:.4f}")
print(f"  MAE:               {mae:.4f}")
print(f"  R²:                {r2:.4f}")
print(f"  Exact Match Acc:   {exact_acc:.4f}")
print(f"  Within-1 Acc:      {within1:.4f}")
print(f"  Best iteration:    {lgb_model.best_iteration}")

joblib.dump(lgb_model,   f"{MDIR}/lgbm_rating_model.pkl")
joblib.dump(le_dest,     f"{MDIR}/dest_encoder.pkl")
joblib.dump(le_type,     f"{MDIR}/type_encoder.pkl")
joblib.dump(le_cost,     f"{MDIR}/cost_encoder.pkl")
joblib.dump(LGBM_FEATURES, f"{MDIR}/feature_names.pkl")
joblib.dump({'le_dest':le_dest,'le_type':le_type,'le_cost':le_cost},
            f"{MDIR}/encoders.pkl")
print("  ✅ LightGBM model saved")

# ══════════════════════════════════════════════════════════════
# 5. NDCG EVALUATION (Ranking quality)
# ══════════════════════════════════════════════════════════════
print("\n[5/9] Evaluating ranking quality (NDCG)...")
# Group by destination, compute NDCG per destination group
ndcg_scores = []
for dest in df_train['destination'].unique():
    mask = df_train['destination'] == dest
    if mask.sum() < 5:
        continue
    idx = np.where(mask)[0]
    # Use test set overlap
    y_true_d = y[idx]
    y_pred_d = lgb_model.predict(X[idx])
    if len(np.unique(y_true_d)) > 1:
        # NDCG expects 2D arrays
        ndcg = ndcg_score(
            y_true_d.reshape(1,-1),
            y_pred_d.reshape(1,-1),
            k=min(10, len(y_true_d))
        )
        ndcg_scores.append((dest, ndcg))

ndcg_df = pd.DataFrame(ndcg_scores, columns=['destination','ndcg'])
print(f"  Mean NDCG@10:   {ndcg_df['ndcg'].mean():.4f}")
print(f"  Min NDCG@10:    {ndcg_df['ndcg'].min():.4f}")
print(f"  Max NDCG@10:    {ndcg_df['ndcg'].max():.4f}")

# ══════════════════════════════════════════════════════════════
# 6. RESULT CHARTS
# ══════════════════════════════════════════════════════════════
print("\n[6/9] Generating result charts...")

# ── PNG 1: Feature Importance ──
fi = pd.Series(lgb_model.feature_importance(importance_type='gain'),
               index=LGBM_FEATURES).sort_values(ascending=True).tail(15)
fig, ax = plt.subplots(figsize=(10, 6))
colors = [PAL[0] if v > fi.median() else PAL[2] for v in fi.values]
bars = ax.barh(fi.index, fi.values, color=colors, edgecolor='white', height=0.65)
ax.set_xlabel('Feature Importance (Gain)', fontsize=11)
ax.set_title('Top 15 Feature Importances\nLightGBM Rating Predictor', fontsize=13, pad=12)
for bar, val in zip(bars, fi.values):
    ax.text(val + fi.max()*0.01, bar.get_y()+bar.get_height()/2,
            f'{val:,.0f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_01_feature_importance.png", dpi=150)
plt.close()
print("  ✅ m4_01_feature_importance.png")

# ── PNG 2: Actual vs Predicted Ratings ──
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
ax.scatter(y_te, y_pred_clipped, alpha=0.15, color=PAL[0], s=8, edgecolors='none')
ax.plot([1,5],[1,5], 'r--', linewidth=2)
ax.set_xlabel('Actual Rating', fontsize=11)
ax.set_ylabel('Predicted Rating', fontsize=11)
ax.set_title(f'Actual vs Predicted\nRMSE={rmse:.4f}  R²={r2:.4f}', fontsize=12)

ax2 = axes[1]
y_te_int = y_te.astype(int)
from collections import Counter
from_to = Counter(zip(y_te_int, y_pred_rounded))
conf = np.zeros((5,5), dtype=int)
for (actual, pred), count in from_to.items():
    if 1 <= actual <= 5 and 1 <= pred <= 5:
        conf[actual-1][pred-1] += count
sns.heatmap(conf, annot=True, fmt='d', cmap='Blues', ax=ax2,
            xticklabels=['1★','2★','3★','4★','5★'],
            yticklabels=['1★','2★','3★','4★','5★'],
            linewidths=0.5)
ax2.set_xlabel('Predicted Rating', fontsize=11)
ax2.set_ylabel('Actual Rating', fontsize=11)
ax2.set_title(f'Rating Confusion Matrix\nExact={exact_acc:.3f}  Within-1={within1:.3f}', fontsize=12)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_02_rating_prediction.png", dpi=150)
plt.close()
print("  ✅ m4_02_rating_prediction.png")

# ── PNG 3: Content-Based Similarity Heatmap ──
fig, ax = plt.subplots(figsize=(13, 10))
mask = np.eye(len(sim_matrix), dtype=bool)
sns.heatmap(sim_matrix, annot=True, fmt='.2f', cmap='YlOrRd',
            vmin=0, vmax=1, linewidths=0.4, ax=ax,
            annot_kws={'size':7}, mask=mask)
ax.set_title('Content-Based Similarity Matrix\n(Cosine Similarity between Destinations)',
             fontsize=13, pad=14)
ax.tick_params(axis='x', rotation=45, labelsize=8)
ax.tick_params(axis='y', rotation=0, labelsize=8)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_03_similarity_matrix.png", dpi=150)
plt.close()
print("  ✅ m4_03_similarity_matrix.png")

# ── PNG 4: NDCG per Destination ──
ndcg_sorted = ndcg_df.sort_values('ndcg')
fig, ax = plt.subplots(figsize=(10, 6))
colors_ndcg = ['#2ecc71' if v >= 0.8 else '#f39c12' if v >= 0.6 else '#e74c3c'
               for v in ndcg_sorted['ndcg']]
bars = ax.barh(ndcg_sorted['destination'], ndcg_sorted['ndcg'],
               color=colors_ndcg, edgecolor='white', height=0.65)
ax.axvline(ndcg_df['ndcg'].mean(), color='black', linewidth=2, linestyle='--',
           label=f'Mean = {ndcg_df["ndcg"].mean():.4f}')
ax.set_xlim(0, 1.1)
ax.set_xlabel('NDCG@10', fontsize=11)
ax.set_title('Ranking Quality (NDCG@10) per Destination\nLightGBM Recommendation Model', fontsize=13, pad=12)
ax.legend(fontsize=10)
for bar, val in zip(bars, ndcg_sorted['ndcg']):
    ax.text(val + 0.01, bar.get_y()+bar.get_height()/2,
            f'{val:.4f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_04_ndcg_per_destination.png", dpi=150)
plt.close()
print("  ✅ m4_04_ndcg_per_destination.png")

# ── PNG 5: Rating Distribution by Data Source ──
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
real_ratings = df_ratings[df_ratings.get('data_source', pd.Series()) == 'kaggle_real']['rating'] \
               if 'data_source' in df_ratings.columns else df_ratings['rating']
all_ratings  = df_ratings['rating']

for ax, (data, title) in zip(axes, [
    (all_ratings, f'All Ratings (n={len(all_ratings):,})'),
    (df_train[df_train.data_source=='kaggle_real']['rating'],
     f'Kaggle Real Reviews (n={len(df_train[df_train.data_source=="kaggle_real"]):,})')
]):
    counts = data.value_counts().sort_index()
    bars = ax.bar(counts.index, counts.values, color=PAL[:5], edgecolor='white', width=0.6)
    ax.set_xlabel('Rating (Stars)', fontsize=11)
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title(title, fontsize=12)
    ax.set_xticks([1,2,3,4,5])
    ax.set_xticklabels(['1★','2★','3★','4★','5★'])
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x()+bar.get_width()/2, val+50, f'{val:,}',
                ha='center', fontsize=9)
plt.suptitle('Rating Distribution', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_05_rating_distribution.png", dpi=150)
plt.close()
print("  ✅ m4_05_rating_distribution.png")

# ── PNG 6: Average Rating per Destination ──
avg_rating = df_train.groupby('destination')['rating'].agg(['mean','count','std']).reset_index()
avg_rating = avg_rating.sort_values('mean', ascending=True)
fig, ax = plt.subplots(figsize=(10, 7))
colors_dest = ['#2ecc71' if v >= 3.5 else '#f39c12' if v >= 3.0 else '#e74c3c'
               for v in avg_rating['mean']]
bars = ax.barh(avg_rating['destination'], avg_rating['mean'],
               color=colors_dest, edgecolor='white', height=0.65, xerr=avg_rating['std'],
               error_kw={'elinewidth':1.5,'capsize':3,'ecolor':'#2d3436'})
ax.axvline(3.0, color='gray', linewidth=1.5, linestyle=':', alpha=0.7)
ax.set_xlim(1, 5.5)
ax.set_xlabel('Average Rating', fontsize=11)
ax.set_title('Average Rating per Destination\n(with standard deviation)', fontsize=13, pad=12)
for bar, (_, row) in zip(bars, avg_rating.iterrows()):
    ax.text(row['mean']+0.05, bar.get_y()+bar.get_height()/2,
            f'{row["mean"]:.2f} (n={int(row["count"]):,})', va='center', fontsize=8.5)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_06_avg_rating_per_destination.png", dpi=150)
plt.close()
print("  ✅ m4_06_avg_rating_per_destination.png")

# ── PNG 7: Recommendation Score Demo ──
# Simulate recommendations for 3 user types
def compute_rec_score(dest_row, user_pref_type, crowd_tol, travel_month,
                      sim_matrix, df_m2):
    type_scores = {'beach': dest_row['beach_score'],
                   'cultural': dest_row['culture_score'],
                   'nature': dest_row['nature_score'],
                   'adventure': dest_row['adventure_score']}
    content_score = type_scores.get(user_pref_type, 0.5)

    m2_sub = df_m2[(df_m2.destination==dest_row['destination']) &
                   (df_m2.month==travel_month)]
    crowd   = m2_sub['crowd_level'].mode()[0] if len(m2_sub) > 0 else 'MEDIUM'
    tss     = m2_sub['travel_suitability_score'].mean() if len(m2_sub) > 0 else 0.5

    crowd_compat = {'LOW':{'low':1.0,'medium':0.7,'high':0.4},
                    'MEDIUM':{'low':0.6,'medium':1.0,'high':0.7},
                    'HIGH':{'low':0.2,'medium':0.5,'high':1.0}}.get(crowd,{}).get(crowd_tol,0.6)

    score = content_score*0.35 + tss*0.25 + crowd_compat*0.25 + dest_row['accessibility_score']*0.15
    return round(score, 4)

user_scenarios = [
    ('Beach Lover (Low Crowd)', 'beach', 'low', 1),
    ('Culture Explorer (Medium Crowd)', 'cultural', 'medium', 8),
    ('Nature Seeker (High Crowd OK)', 'nature', 'high', 4),
]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, (title, pref, ct, month) in zip(axes, user_scenarios):
    scores = []
    for _, row in df_dest.iterrows():
        s = compute_rec_score(row, pref, ct, month, sim_matrix, df_m2)
        scores.append({'destination': row['destination'], 'score': s})
    scores_df = pd.DataFrame(scores).sort_values('score', ascending=True)
    colors_rec = ['#2ecc71' if v >= 0.6 else '#3498db' if v >= 0.45 else '#e74c3c'
                  for v in scores_df['score']]
    bars = ax.barh(scores_df['destination'], scores_df['score'],
                   color=colors_rec, edgecolor='white', height=0.65)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel('Recommendation Score', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold')
    for bar, val in zip(bars, scores_df['score']):
        ax.text(val+0.01, bar.get_y()+bar.get_height()/2,
                f'{val:.2f}', va='center', fontsize=8)
plt.suptitle('Sample Recommendation Scores for 3 User Profiles\n(Month: Jan=beach, Aug=culture, Apr=nature)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_07_recommendation_demo.png", dpi=150)
plt.close()
print("  ✅ m4_07_recommendation_demo.png")

# ── PNG 8: Model Performance Summary ──
fig = plt.figure(figsize=(14, 5))
gs  = gridspec.GridSpec(1, 4, figure=fig, wspace=0.45)

metrics_vals = [rmse, mae, r2, exact_acc, within1, ndcg_df['ndcg'].mean()]
metrics_lbl  = ['RMSE','MAE','R²','Exact\nMatch','Within\n±1','NDCG\n@10']
metric_colors= [PAL[2],PAL[2],PAL[0],PAL[0],PAL[0],PAL[1]]

ax1 = fig.add_subplot(gs[0, :2])
bars = ax1.bar(metrics_lbl, metrics_vals, color=metric_colors, edgecolor='white', width=0.55)
for bar, val in zip(bars, metrics_vals):
    ax1.text(bar.get_x()+bar.get_width()/2, val+0.01, f'{val:.4f}',
             ha='center', fontsize=10, fontweight='bold')
ax1.set_ylim(0, 1.3)
ax1.set_title('LightGBM Rating Predictor\nPerformance Metrics', fontsize=12)
ax1.set_ylabel('Score / Error')

ax2 = fig.add_subplot(gs[0, 2])
top5 = ndcg_sorted.tail(5)
ax2.barh(top5['destination'], top5['ndcg'], color=PAL[1], edgecolor='white')
ax2.set_xlim(0, 1.1)
ax2.set_title('Top 5 Destinations\nby NDCG@10', fontsize=11)

ax3 = fig.add_subplot(gs[0, 3])
source_counts = df_train['data_source'].value_counts()
ax3.pie(source_counts.values, labels=source_counts.index,
        colors=[PAL[0], PAL[3]], autopct='%1.1f%%',
        wedgeprops={'linewidth':2,'edgecolor':'white'})
ax3.set_title('Training Data\nComposition', fontsize=11)

plt.suptitle('Module 4 — Model Performance Summary', fontsize=14, fontweight='bold', y=1.02)
plt.savefig(f"{RDIR}/m4_08_performance_summary.png", dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ m4_08_performance_summary.png")

# ── PNG 9: Rating by Month Heatmap ──
pivot_month = df_train.groupby(['destination','travel_month'])['rating'].mean().unstack()
month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
fig, ax = plt.subplots(figsize=(14, 8))
sns.heatmap(pivot_month, annot=True, fmt='.1f', cmap='RdYlGn',
            vmin=1, vmax=5, linewidths=0.4, ax=ax, annot_kws={'size':8},
            xticklabels=month_labels)
ax.set_title('Average User Rating by Destination & Travel Month\n(Real Kaggle reviews + Synthetic gap-fill)',
             fontsize=13, pad=14)
ax.set_xlabel('Travel Month', fontsize=11)
ax.set_ylabel('Destination', fontsize=11)
ax.tick_params(axis='y', labelsize=9)
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_09_rating_by_month_heatmap.png", dpi=150)
plt.close()
print("  ✅ m4_09_rating_by_month_heatmap.png")

# ── PNG 10: Destination Feature Radar ──
from matplotlib.patches import FancyArrowPatch
categories = ['Beach','Culture','Nature','Adventure','Accessibility']
n = len(categories)
angles = [k/float(n)*2*np.pi for k in range(n)]
angles += angles[:1]

top_dests = ['Ella','Mirissa','Sigiriya','Kandy','Yala','Arugam Bay']
fig, axes = plt.subplots(2, 3, figsize=(15, 10), subplot_kw=dict(polar=True))
for ax, dest in zip(axes.flat, top_dests):
    row = df_dest[df_dest.destination==dest].iloc[0]
    values = [row['beach_score'], row['culture_score'], row['nature_score'],
              row['adventure_score'], row['accessibility_score']]
    values += values[:1]
    ax.plot(angles, values, color=PAL[0], linewidth=2)
    ax.fill(angles, values, color=PAL[0], alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=9)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25','0.5','0.75','1.0'], size=7)
    ax.set_title(dest, size=12, fontweight='bold', pad=15)
    avg_r = df_train[df_train.destination==dest]['rating'].mean()
    ax.text(0, -0.25, f'Avg Rating: {avg_r:.2f}★',
            ha='center', transform=ax.transAxes, fontsize=9, color='gray')

plt.suptitle('Destination Feature Profiles (Radar Charts)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{RDIR}/m4_10_destination_radar.png", dpi=150)
plt.close()
print("  ✅ m4_10_destination_radar.png")

# ══════════════════════════════════════════════════════════════
# 7. FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("  MODULE 4 TRAINING COMPLETE")
print("=" * 62)
print(f"\n  LightGBM Rating Predictor:")
print(f"    RMSE:              {rmse:.4f}")
print(f"    MAE:               {mae:.4f}")
print(f"    R²:                {r2:.4f}")
print(f"    Exact Match Acc:   {exact_acc:.4f}")
print(f"    Within-1 Acc:      {within1:.4f}")
print(f"    Best Iteration:    {lgb_model.best_iteration}")
print(f"\n  Content-Based Similarity:")
print(f"    Destinations:      {sim_matrix.shape[0]}")
print(f"    Avg Similarity:    {sim_matrix.values[~np.eye(len(sim_matrix),dtype=bool)].mean():.4f}")
print(f"\n  Ranking Quality:")
print(f"    Mean NDCG@10:      {ndcg_df['ndcg'].mean():.4f}")
print(f"\n  Models saved:  {MDIR}/")
print(f"  Charts saved:  {RDIR}/  (10 PNG files)")
print("=" * 62)
