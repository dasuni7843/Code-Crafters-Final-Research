"""
Module 2 — Seasonal Travel Planning — RETRAIN (REPORT COMPLIANT, no crowd)
Crowd is REMOVED from features and scoring per interim report.
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

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, f1_score, mean_squared_error,
                             mean_absolute_error, r2_score)
from xgboost import XGBRegressor

DATA = "/home/claude/tourism_data/module2/module2_seasonal_travel_dataset.csv"
MDIR = "/home/claude/models/module2"
RDIR = "/home/claude/results/module2"

plt.rcParams.update({'figure.facecolor':'white','axes.facecolor':'#f8f9fa',
    'axes.grid':True,'grid.alpha':0.4,'font.size':11,
    'axes.spines.top':False,'axes.spines.right':False})
COLORS = {'BEST':'#2ecc71','GOOD':'#3498db','AVOID':'#e74c3c'}
PAL = ['#2ecc71','#3498db','#e74c3c','#f39c12','#9b59b6']

print("="*60)
print("  MODULE 2 — RETRAIN (NO CROWD, REPORT COMPLIANT)")
print("="*60)

df = pd.read_csv(DATA)
print(f"\n[1/6] Loaded {len(df):,} rows")
print(df.suitability_label.value_counts().to_string())

FEATURES = ['avg_temp_c','total_rainfall_mm','rainy_days','avg_humidity_pct',
    'sunshine_hours','weather_suitability_score','is_peak_national',
    'is_best_period_for_dest','holiday_count','holiday_factor',
    'tourism_event_score','event_attractiveness','accessibility_score',
    'comfort_index','elevation_m','avg_stay_days','month','year']

le_dest=LabelEncoder(); le_clim=LabelEncoder(); le_type=LabelEncoder()
df['dest_enc']=le_dest.fit_transform(df['destination'])
df['clim_enc']=le_clim.fit_transform(df['climate_zone'])
df['type_enc']=le_type.fit_transform(df['dest_type'])
FEATURES += ['dest_enc','clim_enc','type_enc']
print(f"  Features: {len(FEATURES)} (crowd EXCLUDED)")

X=df[FEATURES].values; y_cls=df['suitability_label'].values; y_reg=df['travel_suitability_score'].values
scaler=StandardScaler(); X_sc=scaler.fit_transform(X)
le_label=LabelEncoder(); y_enc=le_label.fit_transform(y_cls)
X_tr,X_te,y_tr,y_te=train_test_split(X_sc,y_enc,test_size=0.2,random_state=42,stratify=y_enc)
Xr_tr,Xr_te,yr_tr,yr_te=train_test_split(X_sc,y_reg,test_size=0.2,random_state=42)

print("\n[2/6] Training RandomForest...")
rf=RandomForestClassifier(n_estimators=300,max_depth=12,min_samples_leaf=4,
    class_weight='balanced',random_state=42,n_jobs=-1)
rf.fit(X_tr,y_tr); y_pred_cls=rf.predict(X_te)
acc=accuracy_score(y_te,y_pred_cls); f1=f1_score(y_te,y_pred_cls,average='weighted')
cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
cv_scores=cross_val_score(rf,X_sc,y_enc,cv=cv,scoring='accuracy')
print(f"  Acc={acc:.4f} F1={f1:.4f} CV={cv_scores.mean():.4f}±{cv_scores.std():.4f}")

print("\n[3/6] Training XGBoost...")
xgb=XGBRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,
    colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=1.0,random_state=42,verbosity=0)
xgb.fit(Xr_tr,yr_tr,eval_set=[(Xr_te,yr_te)],verbose=False)
yr_pred=xgb.predict(Xr_te)
rmse=np.sqrt(mean_squared_error(yr_te,yr_pred)); mae=mean_absolute_error(yr_te,yr_pred); r2=r2_score(yr_te,yr_pred)
print(f"  RMSE={rmse:.4f} MAE={mae:.4f} R2={r2:.4f}")

print("\n[4/6] Saving models...")
joblib.dump(rf,f"{MDIR}/seasonal_classifier.pkl")
joblib.dump(xgb,f"{MDIR}/tss_regressor.pkl")
joblib.dump(le_label,f"{MDIR}/label_encoder.pkl")
joblib.dump(scaler,f"{MDIR}/feature_scaler.pkl")
joblib.dump(le_dest,f"{MDIR}/dest_encoder.pkl")
joblib.dump(le_clim,f"{MDIR}/climate_encoder.pkl")
joblib.dump(le_type,f"{MDIR}/type_encoder.pkl")
joblib.dump(FEATURES,f"{MDIR}/feature_names.pkl")

print("\n[5/6] Charts...")
ml=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

fig,ax=plt.subplots(figsize=(7,6))
cm=confusion_matrix(y_te,y_pred_cls)
sns.heatmap(cm,annot=True,fmt='d',cmap='Blues',xticklabels=le_label.classes_,
    yticklabels=le_label.classes_,linewidths=0.5,ax=ax,annot_kws={"size":13})
ax.set_xlabel('Predicted'); ax.set_ylabel('Actual')
ax.set_title(f'Confusion Matrix - Seasonal Classifier\nAccuracy: {acc:.3f}  F1: {f1:.3f}',pad=14)
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_01_confusion_matrix.png",dpi=150); plt.close()

fi=pd.Series(rf.feature_importances_,index=FEATURES).sort_values().tail(15)
fig,ax=plt.subplots(figsize=(9,6))
colors=[PAL[0] if v>fi.median() else PAL[2] for v in fi.values]
bars=ax.barh(fi.index,fi.values,color=colors,edgecolor='white',height=0.65)
ax.set_xlabel('Feature Importance'); ax.set_title('Top 15 Feature Importances\nRandomForest (no crowd)',pad=12)
for bar,val in zip(bars,fi.values): ax.text(val+0.002,bar.get_y()+bar.get_height()/2,f'{val:.3f}',va='center',fontsize=9)
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_02_feature_importance.png",dpi=150); plt.close()

fig,ax=plt.subplots(figsize=(7,5))
folds=[f'Fold {i+1}' for i in range(len(cv_scores))]
bars=ax.bar(folds,cv_scores,color=PAL[1],edgecolor='white',width=0.55)
ax.axhline(cv_scores.mean(),color=PAL[0],linewidth=2.5,linestyle='--',label=f'Mean = {cv_scores.mean():.4f}')
for bar,val in zip(bars,cv_scores): ax.text(bar.get_x()+bar.get_width()/2,val+0.002,f'{val:.4f}',ha='center',fontsize=10,fontweight='bold')
ax.set_ylim(0.7,1.02); ax.set_ylabel('Accuracy'); ax.set_title('5-Fold Cross-Validation'); ax.legend()
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_03_cross_validation.png",dpi=150); plt.close()

fig,axes=plt.subplots(1,2,figsize=(13,5))
axes[0].scatter(yr_te,yr_pred,alpha=0.3,color=PAL[1],s=15,edgecolors='none')
mn,mx=min(yr_te.min(),yr_pred.min()),max(yr_te.max(),yr_pred.max())
axes[0].plot([mn,mx],[mn,mx],'r--',linewidth=2,label='Perfect')
axes[0].set_xlabel('Actual TSS'); axes[0].set_ylabel('Predicted TSS')
axes[0].set_title(f'XGBoost - Actual vs Predicted\nR2={r2:.4f} RMSE={rmse:.4f}'); axes[0].legend()
res=yr_te-yr_pred
axes[1].hist(res,bins=50,color=PAL[3],edgecolor='white',alpha=0.85)
axes[1].axvline(0,color='red',linewidth=2,linestyle='--')
axes[1].set_xlabel('Residual'); axes[1].set_ylabel('Count')
axes[1].set_title(f'Residual Distribution\nMean={res.mean():.4f} Std={res.std():.4f}')
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_04_tss_regression.png",dpi=150); plt.close()

pivot=df.groupby(['destination','month'])['travel_suitability_score'].mean().unstack()
fig,ax=plt.subplots(figsize=(14,8))
sns.heatmap(pivot,annot=True,fmt='.2f',cmap='RdYlGn',vmin=0.2,vmax=0.9,linewidths=0.4,ax=ax,annot_kws={'size':8},xticklabels=ml)
ax.set_title('Travel Suitability Score by Destination & Month\n(no crowd in scoring)',pad=14)
ax.set_xlabel('Month'); ax.set_ylabel('Destination'); ax.tick_params(axis='y',labelsize=9)
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_05_suitability_heatmap.png",dpi=150); plt.close()

lc=df.groupby(['destination','suitability_label']).size().unstack(fill_value=0).reindex(columns=['BEST','GOOD','AVOID'])
fig,ax=plt.subplots(figsize=(13,6))
lc.plot(kind='bar',ax=ax,color=[COLORS['BEST'],COLORS['GOOD'],COLORS['AVOID']],edgecolor='white',width=0.75)
ax.set_xlabel('Destination'); ax.set_ylabel('Month-Year Count')
ax.set_title('Suitability Label Distribution per Destination'); ax.legend(title='Label')
ax.tick_params(axis='x',rotation=45,labelsize=9)
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_06_label_distribution.png",dpi=150); plt.close()

mt=df.groupby('month').agg(avg=('travel_suitability_score','mean'),std=('travel_suitability_score','std')).reset_index()
fig,ax=plt.subplots(figsize=(11,5))
ax.plot(ml,mt['avg'],color=PAL[0],linewidth=3,marker='o',markersize=8,markerfacecolor='white',markeredgewidth=2.5)
ax.fill_between(ml,mt['avg']-mt['std'],mt['avg']+mt['std'],alpha=0.15,color=PAL[0])
for m,v in zip(ml,mt['avg']): ax.annotate(f'{v:.2f}',(m,v),textcoords='offset points',xytext=(0,10),ha='center',fontsize=9)
ax.axhline(mt['avg'].mean(),color='red',linewidth=1.5,linestyle='--',alpha=0.6,label='Annual Mean')
ax.set_ylim(0.3,0.9); ax.set_ylabel('Average TSS'); ax.set_title('Average Travel Suitability Score by Month'); ax.legend()
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_07_monthly_tss_trend.png",dpi=150); plt.close()

fig=plt.figure(figsize=(13,5)); gs=gridspec.GridSpec(1,3,figure=fig,wspace=0.4)
ax1=fig.add_subplot(gs[0])
mm={'Accuracy':acc,'F1 Score\n(weighted)':f1,'CV Mean\nAccuracy':cv_scores.mean()}
bars=ax1.bar(list(mm.keys()),list(mm.values()),color=[PAL[0],PAL[1],PAL[2]],edgecolor='white',width=0.5)
for bar,val in zip(bars,mm.values()): ax1.text(bar.get_x()+bar.get_width()/2,val+0.01,f'{val:.4f}',ha='center',fontsize=11,fontweight='bold')
ax1.set_ylim(0,1.1); ax1.set_title('Classifier Metrics'); ax1.set_ylabel('Score')
ax2=fig.add_subplot(gs[1])
rmm={'RMSE':rmse,'MAE':mae}
bars2=ax2.bar(list(rmm.keys()),list(rmm.values()),color=[PAL[3],PAL[4]],edgecolor='white',width=0.4)
for bar,val in zip(bars2,rmm.values()): ax2.text(bar.get_x()+bar.get_width()/2,val+0.001,f'{val:.4f}',ha='center',fontsize=11,fontweight='bold')
ax2.set_title('XGBoost Error'); ax2.set_ylabel('Error')
ax3=fig.add_subplot(gs[2])
ax3.pie([r2,1-r2],labels=[f'Explained\n({r2:.3f})',f'Unexplained\n({1-r2:.3f})'],colors=[PAL[0],'#dfe6e9'],startangle=90,wedgeprops={'linewidth':2,'edgecolor':'white'},textprops={'fontsize':11})
ax3.set_title(f'XGBoost R2\n{r2:.4f}')
plt.suptitle('Module 2 - Performance Summary (no crowd)',fontsize=14,fontweight='bold',y=1.02)
plt.savefig(f"{RDIR}/m2_08_performance_summary.png",dpi=150,bbox_inches='tight'); plt.close()

sd=df.groupby(['season','destination'])['travel_suitability_score'].mean().reset_index()
fig,axes=plt.subplots(1,3,figsize=(16,6))
seasons=['dry_season','southwest_monsoon','northeast_monsoon']
slabels=['Dry Season\n(Dec-Apr)','SW Monsoon\n(May-Sep)','NE Monsoon\n(Oct-Nov)']
for i,(s,lbl) in enumerate(zip(seasons,slabels)):
    sub=sd[sd['season']==s].sort_values('travel_suitability_score')
    cb=['#2ecc71' if v>0.65 else '#3498db' if v>0.5 else '#e74c3c' for v in sub['travel_suitability_score']]
    axes[i].barh(sub['destination'],sub['travel_suitability_score'],color=cb,edgecolor='white',height=0.6)
    axes[i].set_xlim(0,1.0); axes[i].set_title(lbl,fontweight='bold'); axes[i].set_xlabel('Avg TSS')
    for j,(d,v) in enumerate(zip(sub['destination'],sub['travel_suitability_score'])): axes[i].text(v+0.01,j,f'{v:.2f}',va='center',fontsize=8)
plt.suptitle('Destination Suitability by Season',fontsize=14,fontweight='bold')
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_09_destination_by_season.png",dpi=150); plt.close()

fig,axes=plt.subplots(1,3,figsize=(15,5))
pairs=[('total_rainfall_mm','Rain (mm)'),('avg_temp_c','Avg Temp (C)'),('sunshine_hours','Sunshine Hrs/Day')]
for ax,(col,label) in zip(axes,pairs):
    ax.scatter(df[col],df['travel_suitability_score'],c=df['suitability_label'].map({'BEST':0,'GOOD':1,'AVOID':2}),cmap='RdYlGn_r',alpha=0.3,s=12,edgecolors='none')
    ax.set_xlabel(label); ax.set_ylabel('TSS'); ax.set_title(f'{label} vs TSS')
    corr=df[col].corr(df['travel_suitability_score'])
    ax.text(0.05,0.92,f'r = {corr:.3f}',transform=ax.transAxes,fontsize=10,bbox=dict(facecolor='white',alpha=0.8))
plt.suptitle('Weather Features vs Travel Suitability Score',fontsize=13,fontweight='bold')
plt.tight_layout(); plt.savefig(f"{RDIR}/m2_10_weather_vs_tss.png",dpi=150); plt.close()
print("  All 10 charts regenerated")

print("\n[6/6] Summary")
print("="*60)
print(f"  RandomForest:  Acc={acc:.4f}  F1={f1:.4f}  CV={cv_scores.mean():.4f}")
print(f"  XGBoost:       RMSE={rmse:.4f}  MAE={mae:.4f}  R2={r2:.4f}")
print(f"  Crowd:         EXCLUDED (report compliant)")
print("="*60)
