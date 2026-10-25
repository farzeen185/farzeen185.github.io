"""Append spatial evaluation and matched GLDAS comparisons to the summary deck."""
from pathlib import Path
import json,shutil
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT
O=ROOT/'Thailand_Research_v5';A=O/'figure_revision';P=O/'presentation';F=P/'figures'
slides=json.loads((P/'slide_content.json').read_text(encoding='utf-8'))[:30]
inv={x['id']:x for x in json.loads((A/'figure_inventory.json').read_text(encoding='utf-8'))}
plt.rcParams.update({'font.size':17,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
for file,cols,name,ylabel in [('GLDAS_matched_land_timeseries.csv',[('GLDAS_land_mm','GLDAS land','#4d7d8c'),('naturalized_land_mm','Naturalized land','#b66a3c')],'revised_gldas_national','mm water equivalent'),('GLDAS_residual_standardized_timeseries.csv',[('GLDAS_land_mm','GLDAS land','#4d7d8c'),('TWS_residual_mm','TWS residual','#b66a3c'),('GWS_residual_mm','GWS residual','#7b78a4')],'revised_gldas_residual_national','Standard deviation units')]:
    d=pd.read_csv(A/'tables'/file,dtype={'region':str},parse_dates=['date']);g=d[d.region=='TH'];fig,ax=plt.subplots(figsize=(12,5.3))
    for col,label,color in cols:ax.plot(g.date,g[col],color=color,label=label,lw=1.3)
    ax.set(xlabel='Calendar year',ylabel=ylabel);ax.legend(ncol=len(cols),loc='upper center',fontsize=14);fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(F/(name+'.'+ext),dpi=150,bbox_inches='tight')
    plt.close(fig)
def add(title,figure,source):slides.append({'title':title,'lines':[],'table':None,'figure':figure,'source':source,'equation':None})
for n in [1,3,6,9,11,13,14,15,17,18]:
    x=inv[n];name=Path(x['file']).stem
    for ext in ['png','pdf']:shutil.copy2(A/'figures'/(name+'.'+ext),F/(name+'.'+ext))
    source={1:'CSR basin-average trends; seasonal MK does not adjust serial dependence. All basins retain provider support cautions.',3:'Naturalized baseline C and statistical emulator are related model estimates; neither is an observed counterfactual.',6:'R = O − C = H + E; each panel has its own scale. H is the represented model perturbation, not pumping observations.',9:'GLDAS and naturalized land storage both include soil, canopy and snow; no groundwater or surface water.',11:'Different compartments: standardized timing/shape comparisons, not a human-only validation target.',13:'Frozen ensemble; 2016–2023 parent-model verification. NSE colours saturate below −1.',14:'Annual diagnostics use 12 modeled months; spatial IQR is not a confidence interval.',15:'Head correlations and annual support; hatching means insufficient evidence, not zero effect.',17:'Independent MSEA-Res scene estimates; reservoir changes respond to both climate and operations.',18:'Overlapping 8-year windows require six annual pairs. Station counts are not temporal sample sizes.'}[n]
    add(x['title'],name,source)
add('Matched GLDAS comparison through time','revised_gldas_national','National soil + canopy + snow comparison. The revised report and manuscript include temporal subplots for all 22 basins.')
add('GLDAS and residual timing comparison','revised_gldas_residual_national','Separately standardized on joint observed months. GLDAS land storage does not represent human-only residual ground truth.')
(P/'slide_content.json').write_text(json.dumps(slides,indent=2,ensure_ascii=False),encoding='utf-8')
# Preserve the reviewed Beamer preamble and regenerate frames from the same slide source.
texold=(P/'Thailand_Attribution_Credibility_Beamer.tex').read_text(encoding='utf-8');head=texold.split(r'\begin{document}')[0]+r'\begin{document}'
def esc(s):
    for a,b in [('&',r'\&'),('%',r'\%'),('$',r'\$'),('#',r'\#'),('_',r'\_')]:s=s.replace(a,b)
    return s
tex=[head]
for i,s in enumerate(slides):
    tex.append(r'\begin{frame}{'+esc(s['title'])+'}')
    if i==0:tex.append(r'\centering\vspace{3mm}{\Large Farzeen Khan}\par\vspace{4mm}MS in Water Engineering and Management\par Asian Institute of Technology\par\vspace{4mm}Advisor: Dr. Natthachet Tangdamrongsub')
    elif s['figure']:tex.append(r'\centering\includegraphics[width=.96\textwidth,height=.68\textheight,keepaspectratio]{figures/'+s['figure']+'.pdf}')
    elif s['table']:
        rows=s['table'];n=len(rows[0]);tex.append(r'\centering\small\setlength{\tabcolsep}{2pt}\renewcommand{\arraystretch}{1.45}\begin{tabular}{'+''.join([r'p{'+str(round(.9/n,3))+r'\textwidth}']*n)+r'}\toprule')
        for k,row in enumerate(rows):tex.append(' & '.join(r'\textbf{'+esc(str(x))+'}' if k==0 else esc(str(x)) for x in row)+r'\\'+(r'\midrule' if k==0 else ''))
        tex.append(r'\bottomrule\end{tabular}')
    else:
        if s['equation']:tex.append(r'\[ '+(r'GWSA=TWSA-SMSA-SWSA-CWSA-SWEA' if i==5 else r'R=O-C=(A-C)+(O-A)=H+E')+r' \]')
        tex.append(r'\begin{itemize}\setlength{\itemsep}{4mm}')
        tex.extend(r'\item '+esc(x) for x in s['lines']);tex.append(r'\end{itemize}')
    if s['source']:tex.append(r'\vfill{\fontsize{6.6}{7.8}\selectfont\color{gray}'+esc(s['source'])+'}')
    tex.append(r'\end{frame}')
tex.append(r'\end{document}');(P/'Thailand_Attribution_Credibility_Beamer.tex').write_text('\n'.join(tex),encoding='utf-8')
print('Revised presentation source:',len(slides),'slides; 12 additional figure slides.')
