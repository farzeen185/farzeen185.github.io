"""Shared slide content for editable PowerPoint and a compiled Beamer source."""
from pathlib import Path
import json,shutil
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT
OUT=ROOT/'Thailand_Research_v5';P=OUT/'presentation';F=P/'figures';F.mkdir(exist_ok=True)
S=json.loads((OUT/'logs/research_synthesis.json').read_text(encoding='utf-8'))
def pick(key,**filters):return next(x for x in S[key] if all(x.get(k)==v for k,v in filters.items()))
fmt=lambda x,n=2:f'{x:.{n}f}'
a=pd.read_csv(OUT/'tables/CSR_naturalized_attribution.csv',dtype={'region':str},parse_dates=['date'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,'axes.spines.top':False,'axes.spines.right':False})
for prefix,cols in [('paired',[('observed_mm','Observed','#173c50'),('climate_mm','Naturalized','#288c82'),('historical_human_mm','Historical human','#b66a3c')]),('residual',[('residual_mm','Residual R','#b66a3c'),('modeled_human_mm','Modeled human H','#288c82'),('discrepancy_mm','Discrepancy E','#7b78a4')])]:
    fig,axes=plt.subplots(2,1,figsize=(11,6),sharex=True)
    for ax,var in zip(axes,['TWSA','GWSA']):
        g=a[(a.region=='TH')&(a.variable==var)]
        for col,label,color in cols:ax.plot(g.date,g[col],color=color,label=label,lw=1.3)
        ax.set_ylabel(var+' (mm)')
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=3,fontsize=13);fig.tight_layout(rect=(0,0,1,.93))
    for ext in ['png','pdf']:fig.savefig(F/(prefix+'.'+ext),dpi=220,bbox_inches='tight')
    plt.close(fig)
slides=[]
def add(title,lines=None,table=None,figure=None,source='',equation=None):
    slides.append({'title':title,'lines':lines or [],'table':table,'figure':figure,'source':source,'equation':equation})
    if figure and not (F/(figure+'.png')).exists():
        for ext in ['png','pdf']:shutil.copy2(OUT/'figures'/(figure+'.'+ext),F/(figure+'.'+ext))
add('Water storage trends and attribution credibility',[
'Farzeen Khan','MS in Water Engineering and Management · Asian Institute of Technology','Advisor: Dr. Natthachet Tangdamrongsub'])
add('Research objectives',[
'Storage trends for all 22 principal basins and national context.','Climate-driven storage reconstruction, paired human effects and groundwater evidence.','Interactive decision support with reproducible code and data.'])
add('Proposed research contribution',[
'Separate robust national decline from product-dependent basin rankings.','Test climate memory beyond seasonality and native forcing.','Audit human attribution through model discrepancy and well-network sensitivity.'],source='Integrated empirical contribution; no claim of a first-ever algorithm or journal acceptance.')
add('Study domain',figure='01_study_basins',source='ONWR principal-basin geometry. Basin codes and full names are retained in the thesis.')
add('Documented inputs and distinct scientific roles',table=[['Record','Period','Role'],['CSR RL06.3','2002–2024','Observed TWSA'],['GLDAS + G3P','2002–2023/24','Storage compartments'],['WaterGAP pairing','1981–2023','Naturalized/historical experiment'],['CHIRPS and cube','2003–2024','Forcing and context'],['511 Thai wells','Mostly annual','Groundwater consistency']],source='Full provenance, checksums and special-month audit accompany the data.')
add('Groundwater storage balance',[
'All compartments use mm water equivalent and a common reference.','Identical valid cells preserve the regional accounting identity.','Product depth and filtering differences remain structural uncertainty.'],equation=r'GWSA = TWSA − SMSA − SWSA − CWSA − SWEA',source='GLDAS Noah and G3P compartment data; Sharifi et al. (2025), doi:10.5194/hess-29-6985-2025.')
add('Three meanings of evaluation',table=[['Comparison','What it tests'],['Emulator / naturalized target','Reconstruction of a parent model'],['Matched land storage / GLDAS','Cross-model component consistency'],['Residual / groundwater heads','Groundwater pattern agreement']],source='A strong score in one comparison does not validate the other two.')
add('Chronological climate evaluation',table=[['Role','Years','Use'],['Warm-up','1981–1990','Antecedent weather memory'],['Train','1991–2009','Fit and internal tuning'],['Validation','2010–2015','Freeze ensemble choices'],['Test','2016–2023','Held-out performance']],source='No GRACE lag, well-head feature or unrestricted year trend enters the primary emulator.')
add('National CSR-based storage decline',table=[['Storage','Months','Sen mm/year','95% interval'],['TWSA','237','−7.51','−9.79 to −5.68'],['GWSA','225','−6.84','−8.77 to −5.11']],source='TWSA ends September 2024; GWSA ends September 2023. Intervals are conditional within-product estimates.')
add('Basin storage trends',figure='04_basin_trend_maps',source='Basin-level screening, not single-grid-point CSR inference. All 22 basins retain the provider caution.')
add('Product-dependent basin rankings',figure='05_product_ranking_scatter',source='Spearman rank agreement: TWSA 0.138; GWSA 0.027. Common months and cells; GWS chains also differ in compartments.')
add('Spatial support is shared',[
'National support touches 68 native mascons; inverse concentration is about 50.1.','All 22 principal basins are smaller than the provider’s approximate caution area.','Native concentration and overlap are diagnostics, not independent sample counts.'],source='CSR RL06.3 native mapping and basin intersection weights; provider documentation.')
add('Climate memory improves anomaly reconstruction',figure='13_climate_memory_ablation',source='National anomaly NSE: current → memory is 0.283 → 0.890 for TWSA and 0.039 → 0.723 for GWSA.')
add('Independent precipitation changes model skill',figure='14_precipitation_source_stress',source='CHIRPS replacement: anomaly NSE becomes 0.688 and 0.562. This is forcing sensitivity, not rainfall-accuracy validation.')
add('Held-out observed rainfall response',table=[['Storage','P accumulation','Delay','Test r','Paired months'],['TWSA','12 months','1 month','0.680','79'],['GWSA','12 months','2 months','0.606','76']],source='Selected in 2003–2015; tested in 2016–2023. Empirical delay is not aquifer residence time.')
add('Attribution retains unexplained discrepancy',[
'O: observed; C: naturalized; A: historical-human model.','H = A − C is the human perturbation represented by the model.','E = O − A remains unresolved observation–model discrepancy.'],equation='R = O − C = (A − C) + (O − A) = H + E',source='All terms share observed support and the 2004–2009 anomaly reference.')
add('Observed and modeled storage',figure='paired',source='CSR observations and paired WaterGAP storage; no invented 2024 counterfactual.')
add('Residual and paired human effect differ',figure='residual',source='R = H + E exactly. The residual alone is not a measured pumping history.')
add('Additive national trend partition',figure='10_additive_slope_uncertainty',source='OLS monthly fixed effects, identical dates and 999 shared two-year-block multipliers. Sen slopes are not additive.')
add('Discrepancy magnitude diagnostic',table=[['Storage','D','Conditional interval'],['TWSA','0.938','0.822–0.997'],['GWSA','0.991','0.978–0.999']],source='D = |βE| / (|βH| + |βE|). A descriptive magnitude index, not a causal human fraction.')
add('Groundwater observations',[
'5,484 real aggregates from 511 wells; 506 annual wells and five monthly wells.','Co-located wells are grouped before regional averaging.','Heads remain in head units; aquifer storage coefficients are not invented.'],source='GROW dataset, doi:10.5281/zenodo.15149480; source flags and original intervals retained.')
q=[['Panel','TWS r','GWS r','GWS years']]
for quality,label in [('retained_flags','All overlap'),('fixed_2013_2022','Fixed eligibility/wider history'),('common_period_retained','Common period'),('strict_balanced_2013_2022','Strict balanced')]:
    tw=pick('national_groundwater',variable='TWSA',component='residual_mm',quality=quality);gw=pick('national_groundwater',variable='GWSA',component='residual_mm',quality=quality)
    q.append([label,fmt(tw['r'],3),fmt(gw['r'],3),str(gw['n_years'])])
add('Panel and period control change validation',table=q,source='2013–2022 common-period comparisons retain only eight usable storage years. No mission-gap interpolation.')
add('Groundwater evidence remains limited',[
'Strict balanced groundwater residual–head correlation is approximately zero.','382 eligible annual wells reduce to 225 coordinate-station trend trajectories.','54.2% decline in head, with a station-resampling interval of 47.1–60.0%.'],source='Head-direction results do not estimate groundwater mass or validate total human TWSA.')
add('Conclusions',[
'Broad storage decline is more robust than local severity rankings.','Climate memory reconstructs a naturalized model well; attribution remains conditional.','Groundwater panel tests do not validate the whole residual as human-caused depletion.'])
add('Decision support and reproducibility',[
'Inspect basin records, products, conditional uncertainty and observation support.','Download source-specific inputs, scientific tables and executable scripts.','github.com/pratikkhanal16/thailand-water-storage-dss'],source='The extended CSR study is versioned separately from the earlier release.')
add('Research priorities',[
'Aquifer-specific monthly heads, screened intervals and verified storage coefficients.','Independent pumping, recharge and reservoir-operation histories.','Additional naturalized models and physically harmonized compartment products.'])
add('Selected references',[
'Save et al. (2016): doi:10.1002/2016JB013007','Müller Schmied et al. (2024): doi:10.5194/gmd-17-8817-2024','Sharifi et al. (2025): doi:10.5194/hess-29-6985-2025'],source='Complete bibliography and primary source metadata are included in the thesis and manuscript.')
add('Related Thai work and contribution',[
'Abhishek et al. (2021): doi:10.1016/j.jhydrol.2021.126868','Sharma et al. (2025): doi:10.3390/rs17101731','Contribution: joint product, climate-memory, discrepancy and observation-network audit.'],source='No claim that GRACE analysis, storage subtraction or groundwater validation is new to Thailand.')
add('Validation beyond groundwater levels',table=[['Independent evidence','What it can test'],['Reservoir volume and operation','Surface-water contribution and management timing'],['Pumping and consumptive use','Withdrawal mechanism; returns and recharge still matter'],['InSAR / GNSS subsidence','Aquifer deformation; requires geomechanical context']],source='No single proxy directly measures total human-only storage. Avoid using the same data in subtraction and validation.')
add('New independent reservoir check',table=[['Product','Matched months','Adjusted TWS r'],['Scene-supported Level 1','73','0.439 [0.188, 0.665]'],['Provider-interpolated Level 2','228','0.381 [0.144, 0.552]']],source='26 pre-2004 reservoirs; calendar-month and linear-trend effects removed on matched support. Conditional year-cluster intervals. MSEA-Res: doi:10.5194/essd-17-2693-2025.')
(P/'slide_content.json').write_text(json.dumps(slides,indent=2,ensure_ascii=False),encoding='utf-8')
def esc(s):
    for a,b in [ ('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('$',r'\$'),('#',r'\#'),('_',r'\_') ]:s=s.replace(a,b)
    return s
head=r'''\documentclass[aspectratio=169,10pt]{beamer}
\usepackage{fontspec}
\usefonttheme{serif}
\setmainfont{Times New Roman}
\setsansfont{Times New Roman}
\usepackage{graphicx,booktabs,array,amsmath}
\usetheme{Boadilla}
\definecolor{aitblue}{HTML}{173C50}
\setbeamercolor{structure}{fg=aitblue}
\setbeamercolor{palette primary}{bg=aitblue,fg=white}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{\leavevmode\hbox{\begin{beamercolorbox}[wd=.78\paperwidth,ht=2.5ex,dp=1ex,leftskip=1em]{author in head/foot}Farzeen Khan \quad AIT \quad October 2026\end{beamercolorbox}\begin{beamercolorbox}[wd=.22\paperwidth,ht=2.5ex,dp=1ex,rightskip=1em plus1fil]{date in head/foot}\hfill\insertframenumber/\inserttotalframenumber\end{beamercolorbox}}}
\setbeamersize{text margin left=7mm,text margin right=7mm}
\title{Water storage trends and attribution credibility}
\author{Farzeen Khan}
\institute{Water Engineering and Management\\Asian Institute of Technology}
\date{October 2026}
\begin{document}
'''
tex=[head]
for i,s in enumerate(slides):
    tex.append(r'\begin{frame}{'+esc(s['title'])+'}')
    if i==0:
        tex.append(r'\centering\vspace{3mm}{\Large Farzeen Khan}\par\vspace{4mm}MS in Water Engineering and Management\par Asian Institute of Technology\par\vspace{4mm}Advisor: Dr. Natthachet Tangdamrongsub')
    elif s['figure']:tex.append(r'\centering\includegraphics[width=.96\textwidth,height=.68\textheight,keepaspectratio]{figures/'+s['figure']+'.pdf}')
    elif s['table']:
        values=s['table'];n=len(values[0]);width=.90/n;tex.append(r'\centering\small\setlength{\tabcolsep}{2pt}\renewcommand{\arraystretch}{1.45}\begin{tabular}{'+''.join(['p{'+str(round(width,3))+r'\textwidth}']*n)+r'}\toprule')
        for ri,row in enumerate(values):tex.append(' & '.join((r'\textbf{'+esc(str(x))+'}') if ri==0 else esc(str(x)) for x in row)+r'\\'+(r'\midrule' if ri==0 else ''))
        tex.append(r'\bottomrule\end{tabular}')
    else:
        if s['equation']:
            formula=r'GWSA=TWSA-SMSA-SWSA-CWSA-SWEA' if i==5 else r'R=O-C=(A-C)+(O-A)=H+E'
            tex.append(r'\[ '+formula+r' \]')
        tex.append(r'\begin{itemize}\setlength{\itemsep}{4mm}')
        for line in s['lines']:tex.append(r'\item '+esc(line))
        tex.append(r'\end{itemize}')
    if s['source']:tex.append(r'\vfill{\fontsize{6.6}{7.8}\selectfont\color{gray}'+esc(s['source'])+'}')
    tex.append(r'\end{frame}')
tex.append(r'\end{document}')
(P/'Thailand_Attribution_Credibility_Beamer.tex').write_text('\n'.join(tex),encoding='utf-8')
(P/'README.md').write_text('Compile from this directory with: xelatex -interaction=nonstopmode -halt-on-error Thailand_Attribution_Credibility_Beamer.tex (run twice for total frame count). Times New Roman must be installed; replace the two fontspec font names for another available serif font. The figures directory is required. slide_content.json is the shared source for the editable PowerPoint and Beamer deck. All results are from the separate extended CSR-based study.\n',encoding='utf-8')
print('Prepared',len(slides),'slides and self-contained Beamer source.')
