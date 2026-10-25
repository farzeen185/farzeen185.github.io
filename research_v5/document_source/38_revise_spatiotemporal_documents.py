"""Integrate the requested spatial/temporal atlas into both research documents."""
from pathlib import Path
import importlib.util,json,shutil,os
import csv
SOURCE=Path(__file__).resolve().parent
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',SOURCE.parent)).resolve();O=R/'Thailand_Research_v5';A=O/'figure_revision'
def module(name,file):
    s=importlib.util.spec_from_file_location(name,SOURCE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=module('thesis_revised','23_write_extended_study.py');P=module('paper_revised','24_manuscript_v5.py')
archive=O/'archive/before_requested_figure_revision';archive.mkdir(exist_ok=True,parents=True)
for f in [O/'report/AIT_Extended_Thesis_Farzeen_Khan.docx',O/'report/AIT_Extended_Thesis_Farzeen_Khan.pdf',O/'manuscript/Manuscript_Attribution_Credibility_Farzeen_Khan.docx',O/'manuscript/Manuscript_Attribution_Credibility_Farzeen_Khan.pdf']+list((O/'presentation').glob('Thailand_Attribution_Credibility*')):
    if f.is_file() and not (archive/f.name).exists():shutil.copy2(f,archive/f.name)
inv=json.loads((A/'figure_inventory.json').read_text(encoding='utf-8'));I={x['id']:x for x in inv}
annual=list(csv.DictReader((A/'tables/climate_evaluation_by_test_year.csv').open()))
yearscore={v:float(next(x for x in annual if x['region']=='TH' and x['variable']==v and x['year']=='2022')['anomaly_NSE']) for v in ['TWSA','GWSA']}
annual_note=f"In 2022, national annual anomaly NSE is {yearscore['TWSA']:.3f} for TWSA and {yearscore['GWSA']:.3f} for GWSA. Pooled verification therefore masks important year-specific behaviour; an annual negative score is retained rather than hidden by the strong full-test seasonal score."
for f in (A/'figures').iterdir():
    if f.suffix in ['.png','.pdf']:shutil.copy2(f,O/'figures'/f.name)
SHORT={1:'CSR TWSA and derived GWSA seasonal Sen slopes and seasonal Mann–Kendall FDR maps.',2:'Monthly TWSA and GWSA for all 22 basins; observation gaps are retained.',3:'Spatial naturalized climate baseline and meteorological emulator trends for TWSA and GWSA.',4:'TWSA climate reconstruction for all 22 basins; shading marks held-out years.',5:'GWSA climate reconstruction for all 22 basins; shading marks held-out years.',6:'Spatial TWSA and GWSA residual trends and paired modeled direct-human perturbations.',7:'TWSA residual and modeled human time series for all 22 basins.',8:'GWSA residual and modeled human time series for all 22 basins.',9:'Spatial GLDAS and naturalized-model land-storage trends on matched compartment support.',10:'GLDAS and naturalized land-storage time series for all 22 basins.',11:'Spatial standardized trends and dependence between GLDAS land storage and residuals.',12:'GLDAS land storage and both residual histories for all 22 basins, standardized on common months.',13:'Spatial held-out climate-model raw NSE, anomaly NSE and RMSE.',14:'Climate-model anomaly NSE and RMSE by held-out year, with spatial interquartile variation.',15:'Spatial raw and detrended residual–head correlations and observed annual support.',16:'Annual groundwater and residual histories for all 22 basins on joint support.',17:'Spatial reservoir–residual agreement and fixed reservoir populations; hatching denotes missing evidence.',18:'Residual–head evaluation and represented observation-network support through time.'}
temporal={2,4,5,7,8,10,12,16};fourmaps={1,3,6}
sequence=[1,2,'ranking',3,4,5,13,14,6,7,8,9,10,11,12,15,16,17,18]
for page,item in zip(range(34,53),sequence):
    label=f'Figure 5.{page-33}'
    if item=='ranking':
        M.PAGES[page]=('Product dependent basin trend ranking','05_product_ranking_scatter.png',label,'Common-support CSR and COST-G/G3P trend comparisons; compartment processing also differs.',[
            'Direction is more stable than basin ranking. On common support the national TWS slopes are approximately −7.67 mm/year for CSR and −2.56 for COST-G/G3P. Basin rank correlations are only 0.138 for TWSA and 0.027 for GWSA. These shared-support comparisons are processing-chain sensitivities, not independent spatial replications.'
        ],4.0)
    else:
        x=I[item];height=6.5 if item in temporal or item in fourmaps else 5.1
        para=x['caption']
        if item==14:para+=' '+annual_note
        if item==17:para+=' National scene-supported TWS residual agreement is r=0.439 after season/trend removal across 73 months; this supports one storage component rather than an observed human-only total.'
        M.PAGES[page]=(x['title'],x['file'],label,SHORT[item],[para],height)
# Keep the native six-table structure, moving the product comparison to its matching page.
original_read=M.Writer.table
def report_table(self,label,title,headers,rows,widths=None):return original_read(self,label,title,headers,rows,widths)
M.Writer.table=report_table
source=(SOURCE/'23_write_extended_study.py').read_text(encoding='utf-8')
source=source[source.index('def write_thesis():'):source.index("if __name__=='__main__':")]
source=source.replace('if page==37:','if page==36:')
exec(compile(source,'revised_thesis_layout','exec'),M.__dict__)
M.write_thesis()
(A/'logs/report_figure_crosswalk.json').write_text(json.dumps([{'page':p,'label':v[2],'title':v[0],'file':v[1]} for p,v in sorted(M.PAGES.items())],indent=2),encoding='utf-8')
# Initialize the prior paper's additional reservoir paragraphs and provenance without altering data.
P.build();B=P.M;W=B.Writer
P.RESULTS[1][1].append(annual_note)
gldas=('3.4 GLDAS land storage and residual comparison',[
    'The matched-compartment comparison retains soil moisture, canopy and snow in both WaterGAP and GLDAS Noah. National agreement is r=0.969, NSE=0.738 and RMSE=52.49 mm over 261 months. Spatial trend and temporal panels expose where a high seasonal correlation coexists with different storage trends or amplitudes. Groundwater and surface water are excluded from this benchmark.',
    'Direct GLDAS–residual comparisons answer a separate question. The displayed land-storage and TWS/GWS residual series are standardized on identical observed months within each basin; maps show standardized slopes and descriptive timing correlations. Their different compartment definitions prevent treating GLDAS land storage as residual ground truth or calculating cross-compartment volume-error metrics. GLDAS is also used in GWS subtraction, which makes groundwater-residual comparisons partly dependent by construction.'
])
base=P.RESULTS
results=[base[0],base[1],base[2],gldas,('3.5 Groundwater validation in space and time',base[3][1]),('3.6 Independent reservoir component evidence',base[4][1])]
P.METHODS.append(('2.8 Spatial and temporal evaluation figures',[
    'The figure revision presents all 22 basin records, retaining mission gaps and unavailable validation. Spatial observed trends use seasonal Sen slopes and seasonal Mann–Kendall basin FDR; additive climate/residual maps use calendar-month fixed-effect OLS slopes. The frozen ensemble is evaluated against its naturalized parent on 2016–2023 data using raw and training-climatology-anomaly NSE and RMSE, with separate annual diagnostic scores. No test-year refitting is introduced.',
    'Groundwater maps report raw and detrended correlation with annual support; matched temporal panels retain actual year gaps. Eight-calendar-year rolling head correlations require six observed pairs and are descriptive because windows overlap. Reservoir maps retain screened scene estimates independently from provider interpolation. No head-to-water-storage coefficient, missing observation or human-only validation target is invented.'
]))
w=W(paper=True);sec=w.d.sections[0];sec.different_first_page_header_footer=False
for child in list(sec.footer._element):sec.footer._element.remove(child)
sec.footer.add_paragraph();w.field(sec.footer.paragraphs[0],'PAGE');sec.footer.paragraphs[0].alignment=B.WD_ALIGN_PARAGRAPH.CENTER
w.para(B.PAPER_TITLE,'Title',size=16,bold=True,align=B.WD_ALIGN_PARAGRAPH.CENTER,after=12);w.para(B.AUTHOR,align=B.WD_ALIGN_PARAGRAPH.CENTER);w.para('Water Engineering and Management, Asian Institute of Technology, Thailand',align=B.WD_ALIGN_PARAGRAPH.CENTER)
w.heading('Abstract');w.para(B.ABSTRACT);w.para('Keywords: GRACE; groundwater; climate reconstruction; GLDAS; attribution; basin validation',size=11)
w.heading('1 Introduction',1)
for para in P.INTRO:w.para(para)
w.heading('2 Materials and methods',1);figure=1;crosswalk=[]
for title,paras in P.METHODS:
    w.heading(title)
    for para in paras:w.para(para)
    if title.startswith('2.1'):
        w.fig('Figure 1','Thai principal basin framework; all temporal atlases retain the 22 basin codes.','01_study_basins.png',height=4.2);crosswalk.append({'figure':1,'file':'01_study_basins.png'})
    if title.startswith('2.2'):w.eq('GWSA = TWSA − SMSA − SWSA − CWSA − SWEA')
    if title.startswith('2.5'):w.eq('R = O − C = (A − C) + (O − A) = H + E')
w.heading('3 Results',1)
groups={0:[1,2,'ranking'],1:[3,4,5,13,14,'memory'],2:[6,7,8,'partition'],3:[9,10,11,12],4:[15,16,18],5:[17]}
for k,(title,paras) in enumerate(results):
    h=w.heading(title);h.paragraph_format.page_break_before=True
    for para in paras:w.para(para)
    if k==0:w.table('Table 1','National full-record primary seasonal Sen slopes',['Storage','Months','Slope mm/year','95% interval'],[['TWSA',237,'−7.51','−9.79 to −5.68'],['GWSA',225,'−6.84','−8.77 to −5.11']],widths=[1.3,.8,1.5,2.55])
    if k==2:
        rows=[]
        for field,label in [('observed_mm','Observed'),('climate_mm','Naturalized'),('modeled_human_mm','Modeled human'),('residual_mm','Residual'),('discrepancy_mm','Discrepancy')]:
            vals=[]
            for var in ['TWSA','GWSA']:
                q=B.select('national_OLS_intervals',variable=var,component=field,block_years=2);vals.append(B.fmt(q['ols_slope_mm_year'])+' ['+B.fmt(q['lo95'])+', '+B.fmt(q['hi95'])+']')
            rows.append([label,*vals])
        w.table('Table 2','Additive national slopes and conditional two-year-block intervals',['Component','TWSA mm/year','GWSA mm/year'],rows,widths=[1.55,2.3,2.3])
    if k==4:
        rows=[]
        for quality,label in [('retained_flags','Longest overlap'),('fixed_2013_2022','Fixed eligibility'),('common_period_retained','Common period'),('strict_balanced_2013_2022','Strict balanced')]:
            a=B.select('national_groundwater',variable='TWSA',component='residual_mm',quality=quality);b=B.select('national_groundwater',variable='GWSA',component='residual_mm',quality=quality);rows.append([label,str(a['n_years'])+'/'+str(b['n_years']),B.fmt(a['r'],3),B.fmt(b['r'],3)])
        w.table('Table 3','Residual–head association and temporal support',['Panel','TWS/GWS years','TWS r','GWS r'],rows,widths=[2.7,1.25,1.1,1.1])
    for item in groups[k]:
        figure+=1
        if isinstance(item,int):x=I[item];file=x['file'];title=x['title'];caption=x['caption'];height=6.6 if item in temporal or item in fourmaps else 5.2
        else:
            file,title,caption,height={
                'ranking':('05_product_ranking_scatter.png','Product dependent basin ranking','Common-support CSR and COST-G/G3P comparisons; groundwater chains also differ in compartment processing.',4.5),
                'memory':('13_climate_memory_ablation.png','Climate memory ablation','Controlled Ridge test-year anomaly NSE across basins. This is a separate method comparison from the frozen multi-family ensemble mapped above.',4.2),
                'partition':('10_additive_slope_uncertainty.png','Additive trend partition and uncertainty','Calendar-month fixed-effect national slopes with shared two-year wild-block intervals. R=H+E exactly on common support; discrepancy dominance does not establish that the full residual is either anthropogenic or non-human error.',4.6)
            }[item]
        h=w.heading(title,toc=False);h.paragraph_format.page_break_before=True;w.fig('Figure '+str(figure),caption,file,height=height);crosswalk.append({'figure':figure,'file':file,'title':title})
h=w.heading('4 Discussion',1);h.paragraph_format.page_break_before=True
for title,paras in P.DISCUSSION:
    w.heading(title)
    for para in paras:w.para(para)
w.heading('5 Conclusions',1)
for para in P.CONCLUSION:w.para(para)
w.heading('Data and code availability');w.para('All compact inputs, original and extended numerical scripts, figure-revision source, derived plot tables and verification receipts are available at https://github.com/pratikkhanal16/thailand-water-storage-dss . The figure atlas is an extension of the verified analysis, not a new test-fitted climate model. GROW noncommercial/share-alike and other source-specific terms remain attached to the supplied inputs.')
w.heading('Acknowledgment');w.para('Academic supervision is acknowledged to Dr. Natthachet Tangdamrongsub, Asian Institute of Technology. The cited data providers are acknowledged for the underlying records.')
w.heading('References',1)
for ref in B.REFS:
    p=w.para(ref,size=10.5,spacing=1.1,after=6,align=B.WD_ALIGN_PARAGRAPH.LEFT);p.paragraph_format.left_indent=B.Inches(.25);p.paragraph_format.first_line_indent=B.Inches(-.25)
w.save(O/'manuscript/Manuscript_Attribution_Credibility_Farzeen_Khan.docx')
(A/'logs/manuscript_figure_crosswalk.json').write_text(json.dumps(crosswalk,indent=2),encoding='utf-8')
assert figure>=15
print('Revised thesis: 21 figures; revised manuscript:',figure,'figures. Native Word pagination and visual review required.')
