import json,shutil
import numpy as np,pandas as pd
from research_common import ROOT
W=ROOT/'Thailand_Objective3/web_app';O=ROOT/'Thailand_Objective2/analysis_v4'
d=json.loads((W/'data/analysis.json').read_text(encoding='utf-8'));dates=d['meta']['dates']
read=lambda name:pd.read_csv(O/'tables'/name,dtype={'region':str})
f=read('naturalized_attribution_timeseries.csv');m=read('climate_emulator_validation.csv');b=read('hydrological_benchmarks.csv');e=read('groundwater_attribution_evidence.csv')
def safe(v):
    if isinstance(v,dict):return {str(k):safe(x) for k,x in v.items()}
    if isinstance(v,list):return [safe(x) for x in v]
    if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
    if isinstance(v,np.integer):return int(v)
    if isinstance(v,np.bool_):return bool(v)
    return v
for r in d['regions']:
    code=r['code']
    for var in ['TWSA','GWSA']:
        z=f[(f.region==code)&(f.variable==var)].set_index('date').reindex(dates)
        for suffix,col in [('attribution_observed','observed_mm'),('climate','natural_continuous_mm'),('residual','residual_mm'),('benchmark','human_continuous_mm'),('modeledhuman','modeled_human_mm'),('discrepancy','discrepancy_mm')]:d['series'][code][var+'_'+suffix]=z[col].tolist()
        row=m[(m.region==code)&(m.variable==var)&(m.model=='Ensemble')&(m.period=='Test')].iloc[0].to_dict();row['credible_validation']=row['validation_support']
        score=b[(b.region==code)&(b.variable==var)&b.comparison.str.startswith('Historical')].iloc[0];row.update(benchmark_NSE=score.NSE,benchmark_r=score.r)
        land=b[(b.region==code)&(b.variable=='land_storage')].iloc[0];row['noah_land_NSE']=land.NSE;r['models'][var]=row
    d['evidence'][code]['correlations']=e[(e.region==code)&(e.quality=='retained_flags')&(e.component=='residual_mm')].assign(component='unexplained_residual').to_dict('records')
d['meta'].update(release_date='2026-10-24',author='Farzeen Khan',method='Naturalized WaterGAP baseline and paired human experiment; emulator skill is not independent validation')
d['meta']['sources']=[x for x in d['meta']['sources'] if 'WaterGAP naturalized' not in x['name']]+[{'name':'WaterGAP naturalized and historical-human simulations','url':'https://doi.org/10.25716/GUDE.1TWP-GNQP','note':'GSWP3–ERA5 through 2023. Paired human run DOI 10.25716/GUDE.14B4-KQ6R. CC BY 4.0.'}]
(W/'data/analysis.json').write_text(json.dumps(safe(d),ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
p=W/'app.js';s=p.read_text(encoding='utf-8')
s=s.replace("let names=[{key:state.storage,label:'Observed '+state.storage", "let names=[{key:state.objective===2?state.storage+'_attribution_observed':state.storage,label:state.objective===2?'Observed on common model footprint':'Observed '+state.storage")
s=s.replace("label:'Climate reconstruction'","label:'Naturalized climate baseline'").replace("label:state.storage==='TWSA'?'GLDAS land-storage benchmark':'G3P related GWS product'","label:'Historical human-impact model'")
s=s.replace('Climate estimates start after the two-year spin-up.','Naturalized and human-impact models end December 2023. Attribution uses a common model footprint.')
start=s.index('function updateStats()');end=s.index('\nfunction renderTable',start)
new="""function updateStats(){const t=trend(),m=model(),r=region();el('slopeValue').textContent=number(t.sen_slope_mm_year);el('slopeLabel').textContent='Observed seasonal Sen slope';el('slopeSub').textContent='mm/year · full observation record';el('pValue').textContent=ptext(t.mk_seasonal_p);el('pSub').textContent='Seasonal MK · serial dependence remains';el('skillValue').textContent=number(m.NSE);el('skillSub').textContent=`emulator / naturalized target · ${m.n||0} test months`;el('wellValue').textContent=r.groundwater_wells||0;el('wellSub').textContent=`${r.monthly_wells||0} monthly wells · remaining annual`;el('qualityFlags').innerHTML='<span>Shared coarse GRACE support</span><span>Residual includes model discrepancy</span>';el('interpretationTitle').textContent='Separate model skill from human attribution';el('interpretationText').textContent=`${r.name}: the climate baseline comes from WaterGAP without water use or artificial reservoirs. A paired historical-human run estimates modeled direct human effects. Observed minus naturalized storage also includes model and observation error. Wells cannot directly validate total human TWSA.`;const a=(data.evidence[state.basin]?.correlations||[]).find(x=>x.variable===state.storage);const rows=[['Emulator test / naturalized target',`NSE ${number(m.NSE)} · anomaly NSE ${number(m.deseasonalized_NSE)}`],['Historical-human model / observations',`NSE ${number(m.benchmark_NSE)} · r ${number(m.benchmark_r)}`],['Matched land storage / GLDAS Noah',`NSE ${number(m.noah_land_NSE)}`],['Residual / annual well heads',a?`r ${number(a.r)} · ${a.n} years`:'Insufficient pairs'],['Well agreement controlling climate',a?`partial r ${number(a.partial_r_controlling_natural_climate)}`:'Insufficient pairs']];el('validationContent').innerHTML=rows.map(([a,b])=>`<div class="validation-row"><span>${escape(a)}</span><strong>${escape(b)}</strong></div>`).join('')+'<p class="validation-footnote">High emulator NSE verifies a model, not human depletion. Noah benchmarks soil, canopy and snow only. Wells provide groundwater consistency rather than causal validation of total human TWSA.</p>';el('status').textContent=`${r.name} · ${state.storage==='GWSA'?'Groundwater observations through September 2023':'GRACE observations through September 2024'} · Naturalized baseline through December 2023`;el('status').className='status warning';}
"""
s=s[:start]+new+s[end:]
start=s.index('function methods()');end=s.index('\nasync function start',start)
new="""function methods(){el('methodsContent').innerHTML=`<h3>Three objectives</h3><p>All 22 basins retain TWSA/GWSA Sen and Mann–Kendall analysis. Revised Objective 2 uses paired naturalized and historical-human WaterGAP runs, with no GRACE fitting of the climate baseline.</p><h3>Decomposition</h3><p>Climate = naturalized storage. Residual = observed − naturalized. Modeled human effect = historical-human − naturalized. Discrepancy = observed − historical-human. Thus residual = modeled human effect + discrepancy. All anomalies use 2004–2009; this does not estimate depletion before GRACE.</p><h3>Emulator verification</h3><p>Predictors are meteorological precipitation, potential ET, antecedent memory and seasonal harmonics. Warm-up 1981–1990; train 1991–2009; validation 2010–2015; test 2016–2023. High skill verifies the naturalized parent model, not real-world human depletion. Earlier GRACE-trained M0–M4 experiments remain empirical sensitivities.</p><h3>Groundwater validation clarified</h3><p>5,484 actual aggregates from 511 Thai wells comprise 506 annual and five monthly wells. Raw, climate-controlled, detrended and consecutive-year associations are tested. Heads contain both climate and human effects. They assess groundwater consistency, not the full human TWSA residual. No storage coefficient or specific yield is invented.</p><h3>Limits</h3><p>Common footprints are used for attribution. Grid spacing is not effective GRACE resolution. Filtering mismatch and incomplete input processing metadata remain limitations. Sen slopes are not additive; OLS monthly-fixed-effect slopes supply the additive trend partition. Models end December 2023 and are not extrapolated.</p><h3>Sources</h3><ul>${data.meta.sources.map(x=>`<li><a href="${escape(x.url)}" target="_blank" rel="noopener">${escape(x.name)}</a> — ${escape(x.note||'')}</li>`).join('')}</ul><p>WaterGAP CC BY 4.0; GROW CC BY-NC-SA 4.0. Noncommercial research release.</p>`;el('methodsDialog').showModal();}
"""
s=s[:start]+new+s[end:];p.write_text(s,encoding='utf-8')
p=W/'index.html';s=p.read_text(encoding='utf-8').replace('Independent climate skill','Climate emulator skill');p.write_text(s,encoding='utf-8')
for p in (O/'tables').glob('*.csv'):shutil.copy2(p,W/'downloads'/p.name)
shutil.copy2(ROOT/'reports/OBJECTIVE2_METHODOLOGY_v4.md',W/'downloads/OBJECTIVE2_METHODOLOGY_v4.md')
print('Dashboard revised: naturalized baseline and distinct validation roles.')
