"""Shared-block uncertainty, product dependence and trend-window sensitivity."""
import json
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from research_common import ROOT,seasonal_sen
OUT=ROOT/'Thailand_Research_v5';rng=np.random.default_rng(18516)
f=pd.read_csv(OUT/'tables/CSR_naturalized_attribution.csv',dtype={'region':str},parse_dates=['date'])
fields=['observed_mm','climate_mm','historical_human_mm','modeled_human_mm','residual_mm','discrepancy_mm'];rows=[];diagnostics=[];windows=[]
for (code,var),g in f.groupby(['region','variable'],sort=False):
    g=g.dropna(subset=fields);date=pd.DatetimeIndex(g.date);t=(date-date[0]).days.to_numpy()/365.25
    X=np.column_stack([np.ones(len(g)),t]+[(date.month==m).astype(float) for m in range(2,13)])
    Y=g[fields].to_numpy();pinv=np.linalg.pinv(X);beta=pinv@Y;fitted=X@beta;res=Y-fitted;slope=beta[1]
    assert abs(slope[0]-slope[1]-slope[4])<1e-8 and abs(slope[4]-slope[3]-slope[5])<1e-8
    for length in [1,2,3]:
        # Same multiplier for all components preserves both physical identities.
        sims=[]
        for _ in range(999):
            offset=int(rng.integers(length));block=(date.year.to_numpy()-date.year.min()+offset)//length
            signs=rng.choice([-1.,1.],int(block.max()+1))[block]
            sims.append(slope+(pinv[1]*signs)@res)
        sims=np.asarray(sims);lo,hi=np.quantile(sims,[.025,.975],axis=0)
        for j,key in enumerate(fields):rows.append({'region':code,'variable':var,'component':key,'block_years':length,'n':len(g),'ols_slope_mm_year':slope[j],'lo95':lo[j],'hi95':hi[j],'conditional_sign_support':float(np.mean(sims[:,j]<0)),'replicates':999,'interval_scope':'Fixed data support; calendar-block wild regression uncertainty, not full product/model uncertainty'})
        den=np.abs(sims[:,3])+np.abs(sims[:,5]);D=np.divide(np.abs(sims[:,5]),den,out=np.full(len(den),np.nan),where=den>0)
        diagnostics.append({'region':code,'variable':var,'block_years':length,'discrepancy_magnitude_index':abs(slope[5])/(abs(slope[3])+abs(slope[5])),'index_lo95':np.nanquantile(D,.025),'index_hi95':np.nanquantile(D,.975),'residual_vs_discrepancy_r':float(np.corrcoef(g.residual_mm,g.discrepancy_mm)[0,1]),'interpretation':'Magnitude index is descriptive, not a causal human fraction or independent error budget'})
    for start,end,label in [('2003','2023','common_2003_2023'),('2003','2016','pre_mission_gap'),('2019','2023','post_mission_gap'),('2003','2010','early_record'),('2012','2023','later_record')]:
        z=g[g.date.dt.year.between(int(start),int(end))]
        for key in ['observed_mm','residual_mm']:
            windows.append({'region':code,'variable':var,'component':key,'window':label,'n':len(z),'seasonal_sen_mm_year':seasonal_sen(z[key],z.date)})
    print('Attribution wild-block robustness',code,var,flush=True)
pd.DataFrame(rows).to_csv(OUT/'tables/attribution_wild_block_intervals.csv',index=False)
pd.DataFrame(diagnostics).to_csv(OUT/'tables/discrepancy_magnitude_diagnostic.csv',index=False)
pd.DataFrame(windows).to_csv(OUT/'tables/trend_window_sensitivity.csv',index=False)
a=pd.read_csv(OUT/'tables/common_support_product_audit.csv',dtype={'region':str});comparisons=[]
for var,g in a[a.region!='TH'].groupby('variable'):
    tab=g.pivot(index='region',columns='source',values='sen_slope_mm_year')
    for source in ['Legacy_unidentified','COSTG_G3P']:
        x,y=tab.CSR,tab[source];r,p=spearmanr(x,y)
        comparisons.append({'variable':var,'source_compared_to_CSR':source,'basins':len(tab),'spearman_rho':r,'spearman_p_descriptive':p,'same_slope_sign_basins':int((np.sign(x)==np.sign(y)).sum()),'median_absolute_slope_difference_mm_year':float(np.median(abs(x-y))),'spatial_dependence_note':'Basins share native GRACE support; p is descriptive and not an independent spatial replication test'})
pd.DataFrame(comparisons).to_csv(OUT/'tables/product_ranking_robustness.csv',index=False)
(OUT/'logs/robustness_qa.json').write_text(json.dumps({'passed':True,'region_targets':46,'bootstrap_replicates':999,'block_lengths_years':[1,2,3],'missing_observations_not_filled':True,'paired_slope_identity_verified':True},indent=2),encoding='utf-8')
