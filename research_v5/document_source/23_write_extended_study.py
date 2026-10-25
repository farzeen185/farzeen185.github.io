"""A separately versioned 60-page AIT-style thesis and focused manuscript."""
from pathlib import Path
import os
from copy import deepcopy
import json,csv,re,hashlib,math
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
from v5_thesis_text import TEXT

ROOT=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve();OUT=ROOT/'Thailand_Research_v5';FIG=OUT/'figures'
S=json.loads((OUT/'logs/research_synthesis.json').read_text(encoding='utf-8'))
META_FILE=OUT/'logs/bibliographic_metadata.json'
if not META_FILE.exists():META_FILE=Path(__file__).with_name('bibliographic_metadata.json')
META=json.loads(META_FILE.read_text(encoding='utf-8'))
TEMPLATE=ROOT/'reports/AIT_official_template.docx'
if not TEMPLATE.exists():TEMPLATE=Path(__file__).with_name('AIT_official_template.docx')
assert hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()=='7e8a554d238f9143c412dee46338df67f276596ef23380f5fcdc5ea2c02a24d9'
TITLE='Water Storage Trends and Climate Attribution Across River Basins in Thailand'
PAPER_TITLE='Product dependence and monitoring network uncertainty constrain water storage attribution across Thailand'
AUTHOR='Farzeen Khan';ADVISOR='Dr. Natthachet Tangdamrongsub'
def select(key,**filters):return next(x for x in S[key] if all(x.get(k)==v for k,v in filters.items()))
def fmt(v,n=2):return 'not estimated' if v is None or isinstance(v,float) and not math.isfinite(v) else f'{v:.{n}f}'
def read(name):
    with (OUT/'tables'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def fl(v):
    try:return float(v)
    except (TypeError,ValueError):return float('nan')
def initials(value):return ' '.join(x[0]+'.' for x in value.replace('-',' ').split() if x)
def authorlist(authors):
    values=[a.get('family',a.get('name',''))+(', '+initials(a.get('given','')) if a.get('given') else '') for a in authors]
    return ', '.join(values[:6])+(', et al.' if len(values)>6 else '')
REFS=[]
for doi,m in META.items():
    if not doi.startswith('10.') or not m.get('title'):continue
    if doi=='10.1016/j.jeconom.2008.08.003':continue
    year=m.get('published',{}).get('date-parts',[[None]])[0][0];journal=(m.get('container-title') or [''])[0]
    if doi=='10.3390/rs14010173':year=2022 # Online-first December2021; journal volume14 is2022.
    ref=f"{authorlist(m.get('author',[]))} ({year}). {m['title'][0]}. {journal}"
    for key in ['volume','page']:
        if m.get(key):ref+=', '+str(m[key])
    REFS.append(ref+'. https://doi.org/'+doi)
manual=[
 'Mahto, S. S., Fatichi, S., & Galelli, S. (2025). A 1985–2023 time series dataset of absolute reservoir storage in Mainland Southeast Asia (MSEA-Res). Earth System Science Data, 17, 2693–2712. https://doi.org/10.5194/essd-17-2693-2025',
'Save, H., Bettadpur, S., & Tapley, B. D. (2016). High-resolution CSR GRACE RL05 mascons. Journal of Geophysical Research Solid Earth, 121, 7547–7569. https://doi.org/10.1002/2016JB013007',
'Save, H. (2020). CSR GRACE and GRACE-FO RL06 Mascon Solutions v02 [Data set]. University of Texas at Austin. https://doi.org/10.15781/cgq9-nh24',
'Center for Space Research (CSR). (2026). CSR GRACE and GRACE-FO RL06.3 mascon solutions and processing guidance. Data update 7 October 2026; accessed 24 October 2026. https://www2.csr.utexas.edu/grace/RL0603_mascons.html',
'Sharma, Y. K., Mohanasundaram, S., Kim, S., Shrestha, S., Babel, M. S., & Loc, H. H. (2025). Enhancing aquifer reliability and resilience assessment in data-scarce regions using satellite data: Application to the Chao Phraya River Basin. Remote Sensing, 17, 1731. https://doi.org/10.3390/rs17101731',
'Güntner, A., Sharifi, E., Haas, J., Boergens, E., Dahle, C., et al. (2024). Global Gravity-based Groundwater Product G3P version 1.12 [Data set]. GFZ Data Services. https://doi.org/10.5880/G3P.2024.001',
'Martens, B., Miralles, D. G., Lievens, H., van der Schalie, R., de Jeu, R. A. M., et al. (2017). GLEAM v3: Satellite-based land evaporation and root-zone soil moisture. Geoscientific Model Development, 10, 1903–1925. https://doi.org/10.5194/gmd-10-1903-2017',
'Bäthge, A., Ruz Vargas, C., Lischeid, G., Collenteur, R., Cuthbert, M., et al. (2026). GROW A Global-Scale Time Series Dataset for Groundwater Studies within the Earth System [Data set]. Zenodo. https://doi.org/10.5281/zenodo.15149480',
'Müller Schmied, H., Trautmann, T., Ackermann, S., Cáceres, D., Flörke, M., et al. (2024a). WaterGAP v2.2e model output driven by GSWP3–ERA5 neglecting direct human impacts [Data set]. Goethe University Frankfurt. https://doi.org/10.25716/GUDE.1TWP-GNQP',
'Müller Schmied, H., Trautmann, T., Ackermann, S., Cáceres, D., Flörke, M., et al. (2024b). WaterGAP v2.2e model output driven by GSWP3–ERA5 including direct human impacts [Data set]. Goethe University Frankfurt. https://doi.org/10.25716/GUDE.14B4-KQ6R',
'Asian Institute of Technology Language Center. (2026). Master thesis format January 2026 and thesis-format guidance. https://languages.ait.ac.th/thesis-format-template/',
'NASA. (n.d.). Global Land Data Assimilation System dataset specifications. https://ldas.gsfc.nasa.gov/gldas/dataset',
'Office of the National Water Resources. (n.d.). Thailand principal-basin boundaries [Project-supplied MainBasin_ONWR_Law_WGS84 spatial data].',
'Sutterley, T., et al. (2026). Gravity toolkit time utilities and special GRACE month adjustments [Software documentation]. https://read-grace-harmonics.readthedocs.io/en/latest/api_reference/time.html'
]
for ref in manual:
    url=ref.split('https://')[-1] if 'https://' in ref else ref
    if not any(url in x for x in REFS):REFS.append(ref)
REFS=sorted(REFS,key=str.casefold)

ABSTRACT=("Separating water-storage decline into climatic and human components requires more than a high prediction score. This study assessed terrestrial and groundwater storage anomalies (TWSA and GWSA) across Thailand's 22 principal basins using documented CSR RL06.3 mascons, a full-compartment groundwater balance, paired naturalized and historical-human WaterGAP simulations and 5,484 observed aggregates from 511 wells. The analysis combined seasonal Sen and Mann–Kendall methods with common-support product comparisons, climate-memory ablations, independent-precipitation forcing tests, additive trend uncertainty and station-panel resampling. National CSR-based TWSA declined by 7.51 mm/year through September 2024 and GWSA by 6.84 mm/year through September 2023. The contrasting COST-G/G3P chain retained a national negative direction but showed weak basin-ranking agreement: Spearman coefficients were 0.138 for TWSA and 0.027 for GWSA. Climate memory raised national held-out anomaly NSE from 0.283 to 0.890 for TWSA and from 0.039 to 0.723 for GWSA relative to current-weather Ridge models. Replacing native precipitation with CHIRPS reduced anomaly skill, exposing forcing dependence. The exact residual decomposition retained both the modeled direct-human perturbation and observation–historical-model discrepancy. The discrepancy-magnitude diagnostics were 0.938 and 0.991; these are descriptive indices, not causal human fractions. Longest-overlap residual–head correlations were 0.127 and 0.037, with broad station-bootstrap intervals. A strict balanced 2013–2022 panel gave groundwater correlation close to zero over eight usable storage years. The study demonstrates robust broad decline alongside unstable local rankings and unresolved human attribution. Its proposed contribution is an auditable credibility assessment linking processed gravity support, climate reconstruction and observation-network uncertainty, released with reproducible code and decision-support outputs.")

class Writer:
    def __init__(self,paper=False):
        self.d=Document(TEMPLATE);section=deepcopy(self.d.sections[0]._sectPr)
        for child in list(self.d._element.body):self.d._element.body.remove(child)
        self.d._element.body.append(section);self.paper=paper;self.captions=[];self.bookmark=1000;self.intended_pages=[]
        self.d.core_properties.author=AUTHOR;self.d.core_properties.title=PAPER_TITLE if paper else TITLE
        self.d.core_properties.subject='Extended CSR-based Thailand storage and attribution-credibility study'
        self.d.core_properties.comments='Research draft for advisor review; no committee or approval signatures invented.'
        for name in ['Normal','Body Text','Title','Heading 1','Heading 2','Heading 3','Caption']:
            if name in self.d.styles:
                st=self.d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0);st.font.size=Pt(12)
        self.d.styles['Title'].font.size=Pt(16);self.d.styles['Heading 1'].font.size=Pt(14)
        self.d.styles['Heading 1'].paragraph_format.page_break_before=False
        self.d.styles['Heading 2'].paragraph_format.page_break_before=False
        if paper:self.numbering('decimal')
    def numbering(self,fmt,start=1):
        sect=self.d.sections[-1];v=sect._sectPr.find(qn('w:pgNumType'))
        if v is None:v=OxmlElement('w:pgNumType');sect._sectPr.append(v)
        v.set(qn('w:fmt'),fmt);v.set(qn('w:start'),str(start))
    def para(self,text='',style='Normal',size=12,bold=False,align=None,spacing=1.5,after=4):
        p=self.d.add_paragraph(style=style);p.alignment=align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
        pf=p.paragraph_format;pf.line_spacing=spacing;pf.space_before=Pt(0);pf.space_after=Pt(after);pf.widow_control=True
        np=OxmlElement('w:numPr');ni=OxmlElement('w:numId');ni.set(qn('w:val'),'0');np.append(ni);p._p.get_or_add_pPr().append(np)
        r=p.add_run(str(text));r.font.name='Times New Roman';r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0);r.bold=bold
        if style=='Title':
            o=OxmlElement('w:outlineLvl');o.set(qn('w:val'),'9');p._p.get_or_add_pPr().append(o)
        return p
    def heading(self,title,level=2,toc=True):
        style='Heading '+str(level) if toc else 'Normal';p=self.para(title,style,size=14 if level==1 else 12,bold=True,align=WD_ALIGN_PARAGRAPH.CENTER if level==1 else WD_ALIGN_PARAGRAPH.LEFT,spacing=1.0,after=8)
        p.paragraph_format.keep_with_next=True;return p
    def page(self,number,title,chapter=None,toc=False):
        self.intended_pages.append({'number':number,'title':title})
        if chapter:p=self.heading('CHAPTER '+str(chapter)+'\n'+title.upper(),1)
        else:p=self.heading(title,2,toc=toc)
        if number!=1:p.paragraph_format.page_break_before=True
    def field(self,p,instruction):
        for tag,txt in [('begin',None),('instruction',instruction),('end',None)]:
            r=OxmlElement('w:r')
            if txt is None:e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),tag)
            else:e=OxmlElement('w:instrText');e.set(qn('xml:space'),'preserve');e.text=txt
            r.append(e);p._p.append(r)
    def caption(self,label,title):
        p=self.para(label+' '+title,'Caption',size=11,bold=True,align=WD_ALIGN_PARAGRAPH.CENTER,spacing=1.15,after=7);self.bookmark+=1
        a=OxmlElement('w:bookmarkStart');a.set(qn('w:id'),str(self.bookmark));a.set(qn('w:name'),label.replace(' ','').replace('.','_'));b=OxmlElement('w:bookmarkEnd');b.set(qn('w:id'),str(self.bookmark));p._p.insert(0,a);p._p.append(b)
        self.captions.append((label,title));return p
    def fig(self,label,title,file,height=4.8):
        p=self.para('',align=WD_ALIGN_PARAGRAPH.CENTER,spacing=1,after=3);p.paragraph_format.keep_with_next=True
        with Image.open(FIG/file) as im:w,h=im.size
        width=min(6.16,height*w/h);p.add_run().add_picture(str(FIG/file),width=Inches(width));self.caption(label,title)
    def table(self,label,title,headers,rows,widths=None):
        p=self.caption(label,title);p.paragraph_format.keep_with_next=True
        t=self.d.add_table(rows=1,cols=len(headers));t.autofit=False
        widths=widths or [6.15/len(headers)]*len(headers)
        for c,text in zip(t.rows[0].cells,headers):c.text=str(text)
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for c,text in zip(t.add_row().cells,row):c.text=str(text)
        for ri,row in enumerate(t.rows):
            for i,c in enumerate(row.cells):
                c.width=Inches(widths[i]);pr=c._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
                for side in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'B7B7B7');borders.append(e)
                pr.append(borders)
                for p in c.paragraphs:
                    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(10.5);r.bold=ri==0;r.font.color.rgb=RGBColor(0,0,0)
        return t
    def eq(self,text):
        p=self.para('',align=WD_ALIGN_PARAGRAPH.CENTER,spacing=1.2,after=8);o=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);o.append(r);p._p.append(o)
    def save(self,path):
        a=OxmlElement('w:updateFields');a.set(qn('w:val'),'true');self.d.settings._element.append(a);self.d.save(path)

PAGES={
18:('Study area and official basin framework','01_study_basins.png','Figure 3.1','Official principal basins and analysis codes; full names appear in Appendix A.',[
"The spatial framework contains 22 principal basins and separately coded island features assigned to their parent basin for the revised analysis. The retained polygon–grid intersection area totals approximately 515,230 km² for national context. This is the analytical intersection-area total, not a replacement estimate of Thailand's official national area.",
"The official Chao Phraya principal basin is not synonymous with the entire greater Chao Phraya drainage system used in some earlier studies. The distinction is retained when interpreting local literature or comparing basin slopes. No basin boundaries are selected to maximize a trend or correlation. National context provides a larger-scale comparison, while all individual principal basins retain the CSR provider's small-basin caution."],5.0),
22:('Hydroclimatic context and seasonal structure','16_hydroclimate_seasonality.png','Figure 3.2','National calendar-month climatologies from the retained multisource cube; the products have different physical meanings.',[
"Rainfall, actual evapotranspiration, soil moisture and land-surface temperature describe complementary parts of the regional seasonal cycle. The plotted climatologies summarize available 2003–2024 observations in the harmonized cube; they are not used to fill missing gravity or groundwater measurements.",
"The two ET records and the soil products are retained as context rather than assumed to be external climatic causes. Their response can include management effects, and their structural definitions differ. CHIRPS supplies the independent precipitation forcing and the observed rainfall–storage test. The main naturalized-model emulators use meteorological P and potential ET, with training-derived seasonal references."],4.8),
34:('National storage change','02_national_storage.png','Figure 5.1','CSR-based national TWSA and full-balance GWSA; real missing satellite months remain gaps.',[
"The primary CSR record gives a TWSA seasonal Sen slope of −7.51 mm/year, with a 300-resample conditional interval of −9.79 to −5.68. Derived GWSA declines at −6.84 mm/year, with an interval of −8.77 to −5.11. TWSA contains 237 observed monthly solutions through September 2024; GWSA contains 225 through September 2023.",
"These are robust summaries of processed storage records, not constant annual losses in every year. The seasonal cycle and shorter-period recoveries remain visible. GWSA is a compartment-derived estimate with model and filtering uncertainty, and its shorter endpoint follows surface-water availability. The intervals do not contain every source of product or structural error."],4.7),
35:('Basin trend estimates and conditional intervals','03_basin_sen_intervals.png','Figure 5.2','All-basin seasonal Sen slopes and conditional 95 percent bootstrap intervals; codes refer to Appendix A.',[
"All principal basins have negative primary full-record slope estimates for both storage types. Their magnitudes vary substantially, with several southern coastal basins showing particularly large declines. The interval calculations describe uncertainty within the selected processed record and should not be read as a product-independent ordering of basin stress.",
"The common-source audit, soil alternative and native-support analysis are therefore needed alongside this forest plot. A basin interval can exclude zero while its relative position remains sensitive to another processing chain. The national result is supported over a larger area; local interpretations require additional compartment and aquifer evidence."],5.6),
36:('Spatial distribution of basin storage trends','04_basin_trend_maps.png','Figure 5.3','Basin-level CSR trend maps in millimetres per year; colours are centred on zero.',[
"The maps display regional screening estimates rather than independent quarter-degree groundwater observations. Basin polygons are the reporting framework, while the gravity information is spatially broader and regularized. The large southern magnitudes deserve attention together with the coastline and support diagnostics.",
"A full-compartment subtraction has been used, so the groundwater pattern is not obtained by ignoring surface water or canopy storage. Nevertheless, represented soil depth, surface-water filtering and coastal support remain structural uncertainties. The maps should guide investigation and comparison with independent records rather than directly prescribe a basin-specific pumping reduction."],5.6),
37:('Product dependent magnitudes and rankings','05_product_ranking_scatter.png','Figure 5.4','Common-support slopes from CSR-based and COST-G/G3P chains; the groundwater comparison changes compartments as well as gravity processing.',[
"National decline persists in both documented chains, but magnitude and local ordering differ. On the 223-month common source support, TWSA Sen slopes are approximately −7.67 for CSR and −2.56 mm/year for COST-G/G3P. Groundwater slopes are −6.88 and −3.45 mm/year, respectively. These contrasts are not removed by a common anomaly reference.",
"Across the 22 basins, rank agreement is weak: Spearman coefficients are 0.138 for TWSA and 0.027 for GWSA. The legacy export agrees closely with CSR but has unresolved provenance and is not counted as independent replication. Agreement in national direction is consequently stronger than agreement in a basin priority list."],3.7),
38:('Groundwater product and soil representation','06_groundwater_product_structure.png','Figure 5.5','Groundwater slopes under alternative estimation structures; differing definitions prevent a single-factor interpretation.',[
"Replacing the primary Noah soil contribution with the filtered root-zone alternative changes the national CSR groundwater slope from −6.84 to −7.86 mm/year. The negative direction remains, but the magnitude changes by about one millimetre per year. The native G3P groundwater chain gives a smaller decline on common source support.",
"The alternatives do not form an independent probabilistic ensemble. They share satellite information and differ in soil, filtering or gravity-processing choices. Their spread is a structural sensitivity, not a confidence interval or proof that one product is correct. The basin differences show why a detailed local map should retain its product definition and uncertainty context."],5.5),
39:('Shared native gravity support','07_shared_native_support.png','Figure 5.6','Overlap of mapped native-mascon weight fractions; the matrix is not gravity-error covariance.',[
"Some reporting basins share mapped native gravity support. Positive off-diagonal values indicate that part of their spatial representation is drawn from the same native mascon identifiers. The diagonal is one by construction and should not be interpreted as a validation result.",
"The matrix makes spatial dependence visible without estimating an unavailable full covariance or averaging kernel. Regularization can couple information beyond the mapped overlap. Consequently, the 22 basin tests do not constitute 22 independent satellite experiments. This supports interpreting FDR-adjusted significance and cross-basin rank statistics as screening evidence rather than as complete spatial attribution."],5.5),
40:('Concentration of basin representation','08_support_concentration.png','Figure 5.7','Native-weight concentration and basin area; inverse concentration is not an effective statistical sample size.',[
"National context intersects 68 mapped native mascons and has an inverse weight-concentration count near 50.1. Individual basin values are smaller and uneven. A large number of convenience-grid cells therefore does not imply a comparable number of independent gravity observations.",
"All 22 principal basins remain below the CSR guidance's approximate small-basin caution area. This flag is not a statement that every estimate is unusable. It identifies a scale limitation that should accompany the result. The appropriate use is to combine the storage screen with product agreement, groundwater coverage and independently observed hydrological information, rather than to convert the concentration diagnostic into degrees of freedom."],4.0),
41:('Climate memory beyond seasonal prediction','13_climate_memory_ablation.png','Figure 5.8','Controlled Ridge feature ablations evaluated in 2016–2023; boxes summarize basins and points show national context.',[
"Memory improves reconstruction of anomalies that a seasonal cycle or current weather alone does not capture. National TWSA anomaly NSE rises from 0.283 for current weather to 0.890 with lagged weather and memory. The corresponding GWSA change is from 0.039 to 0.723. The basin-median memory scores are approximately 0.844 and 0.680.",
"These are parent-model reconstruction results. They demonstrate useful meteorological information and the need to separate seasonality from anomaly skill, but they do not verify actual human depletion. The primary counterfactual remains the published naturalized simulation. The ablation does not replace it merely because a particular statistical feature set scores well."],3.8),
42:('Sensitivity to independent precipitation forcing','14_precipitation_source_stress.png','Figure 5.9','Frozen-model forcing replacement against a native-forced naturalized target; this is a sensitivity test, not rainfall-product validation.',[
"Using unadjusted CHIRPS in the frozen memory emulator reduces national anomaly NSE from 0.890 to 0.688 for TWSA and from 0.723 to 0.562 for GWSA. Training-only monthly mean adjustment does not restore the original scores. The test therefore exposes dependence on forcing consistency even when the native reconstruction is strong.",
"A score reduction does not establish that CHIRPS is less accurate precipitation. The evaluation target was generated with the native forcing. The useful finding is that approximation skill and independent hydrological validity are distinct. Reported performance should identify the input source and target, and model uncertainty should not be represented solely by the spread among algorithms trained on one common parent simulation."],3.8),
43:('Transfer of observed rainfall and storage associations','15_heldout_rainfall_response.png','Figure 5.10','Observed 2016–2023 rainfall–storage associations after development-only selection; dark bars pass basin FDR screening.',[
"National observed TWSA is most strongly associated in development with a twelve-month precipitation accumulation delayed by one month; GWSA selects a two-month delay. The held-out correlations are approximately 0.680 and 0.606, based on 79 and 76 paired monthly values. Whole-year precipitation permutations provide a conditional reference for these later-period associations.",
"The result supports a hydroclimatic role in observed interannual storage variability. It does not make the selected delay an aquifer residence time or identify a purely climatic groundwater response. Irrigation and pumping can also respond to rainfall conditions. The association is therefore interpreted with the paired-model and groundwater evidence, not used to label the remaining trend as automatically anthropogenic."],5.4),
44:('Paired naturalized and historical human storage','09_paired_national_decomposition.png','Figure 5.11','Observed and paired modeled storage on common support, with residual R, paired human H and discrepancy E.',[
"Naturalized and historical-human simulations reproduce much seasonal storage behaviour, but substantial observation–model differences remain. The right-hand panels retain both the paired modeled human perturbation and the discrepancy from observed storage. Their sum equals the residual by construction, a relationship verified in the exported data.",
"A large residual therefore cannot be interpreted as measured human depletion simply because it is calculated after subtracting a naturalized baseline. The historical-human simulation does not reproduce that residual fully. This leaves an unresolved combination of unrepresented management, process and forcing errors, and observation or compartment effects. The experiment provides structured attribution evidence without uniquely assigning those alternatives."],4.4),
45:('Additive trend decomposition','10_additive_slope_uncertainty.png','Figure 5.12','Monthly-fixed-effect OLS slopes with shared two-year-block wild-bootstrap intervals; these point slopes are additive.',[
"The common-date national TWSA OLS slopes are −8.36 mm/year observed, −0.54 naturalized, −0.49 paired modeled human, −7.81 residual and −7.32 discrepancy. The corresponding groundwater values are −7.28, −0.21, +0.06, −7.07 and −7.13 mm/year. These coefficients are distinct from the robust Sen summaries and preserve the exact component identities.",
"For groundwater, the modeled-human two-year-block interval spans approximately −0.01 to +0.13 mm/year, while the residual and discrepancy intervals remain negative. This does not prove the discrepancy is non-human error. It shows that the represented paired human perturbation does not account for the observed residual trend within this experiment."],3.9),
46:('Dependence on uncertainty block length','12_block_length_sensitivity.png','Figure 5.13','Conditional slope intervals under one-, two- and three-year calendar blocks; missing dates are retained.',[
"Longer blocks permit more persistence in the regression residuals and can alter uncertainty around small component trends. The interval comparison is particularly relevant to the modeled-human term, whose magnitude is much smaller than the observed residual. A borderline interval under one block choice should not be treated as decisive attribution evidence.",
"Shared multipliers preserve the decomposition in every replicate. The intervals remain conditional on the chosen model, processed inputs and linear trend specification. They do not propagate complete GRACE inversion uncertainty or the full range of plausible groundwater-model structures. Product and compartment comparisons therefore remain separate parts of the evidence rather than being absorbed into a single narrow interval."],4.0),
47:('Discrepancy magnitude and attribution credibility','11_discrepancy_diagnostic_maps.png','Figure 5.14','Descriptive discrepancy-magnitude index D; it is not a human fraction or an independent error-budget allocation.',[
"The national two-year-block diagnostic is 0.938 for TWSA and 0.991 for GWSA. Values near one indicate that the discrepancy trend is large relative to the paired modeled-human trend in this magnitude comparison. The map exposes where the interpretation of an observed residual depends strongly on the unexplained part of the historical-human simulation.",
"Neither a high index nor its conditional interval identifies the cause of the discrepancy. Omitted human intervention and hydrological-model error are both possible contributors. The diagnostic should be used to qualify an attribution claim and guide further investigation, not to estimate a proportion of depletion caused by humans. This distinction is retained in the manuscript and decision-support material."],5.5),
48:('Observation network coverage through time','17_well_network_coverage.png','Figure 5.15','Annual coordinate-station availability by basin; values display log of one plus actual station count.',[
"The well dataset is spatially and temporally uneven despite its large total number of records. Annual coverage changes materially through the observation period, and some basins lack a useful annual validation population. Co-location grouping and the coverage matrix expose the difference between the number of well identifiers and the number of contributing station groups.",
"This changing network can influence a national or basin head index even when every retained observation is real. The study therefore retains annual counts, source flags and panel definitions. A smooth index is not evidence that the same aquifers were sampled throughout the record. Missing or weakly supported comparisons are reported explicitly rather than replaced with fabricated correlations."],5.2),
49:('Common period and balanced panel comparisons','18_network_panel_sensitivity.png','Figure 5.16','Residual–head relationships across quality and panel conditions; different time supports must be distinguished.',[
"The longest-overlap national residual–head correlations are 0.127 for TWSA and 0.037 for GWSA. The fixed-eligibility, wider-history panel gives larger raw values, approximately 0.657 and 0.511. That improvement cannot be interpreted as validation without separating a panel effect from a time-support effect.",
"On the common 2013–2022 window, only eight storage years pass the availability rule. The all-well GWSA residual correlation is 0.029; the strict balanced panel gives approximately −0.0004. The latter uses 189 coordinate station groups. Groundwater agreement therefore remains weak under the fairer time-matched comparison, despite an apparently attractive correlation under the broader fixed-eligibility condition."],3.9),
50:('Well head trajectories and direction uncertainty','19_station_trend_directions.png','Figure 5.17','Eligible annual head trends and station-resampled declining fractions; head units are not storage units.',[
"The well-level trend screen retains 382 annual wells meeting the observation and span criteria. After co-location grouping, 225 station trajectories contribute to the national direction summary. The median station head slope is approximately −0.016 m/year, and 54.2 percent of station-median slopes are negative.",
"The station-resampling interval for the declining fraction is about 47.1 to 60.0 percent. It does not establish a clearly dominant national direction within the monitored population. More importantly, the population is not a random sample of all Thai aquifers. Head trajectories provide useful local evidence, but their magnitude cannot be equated with millimetres of regional GWSA without verified storage coefficients and aquifer support."],4.3),
51:('Basin groundwater agreement and station uncertainty','20_basin_groundwater_uncertainty.png','Figure 5.18','Primary GWS residual–head associations and coordinate-station bootstrap intervals; absent intervals indicate inadequate support.',[
"Basin-level correlations vary, but their interpretation depends on the number and distribution of station groups and the common observed years. The station bootstrap holds those years fixed while resampling the monitored spatial population. Its intervals therefore describe network sensitivity, not all temporal or product uncertainty.",
"A basin with a positive point correlation is not automatically validated, particularly where few independent station groups or few annual pairs are available. A basin with no adequate comparison is an observation gap, not evidence of either absence or presence of depletion. The decision-support interpretation retains this distinction and directs attention to the monitoring information needed for a stronger assessment."],5.3),
52:('Trend windows and shorter period recoveries','21_trend_window_sensitivity.png','Figure 5.19','Fixed-window seasonal Sen slopes; colours saturate at ±30 mm/year and full numerical values remain in the CSV.',[
"The record is not a monotonic trajectory. Several later-period basin slopes are positive even where the long common-record trend is negative. In contrast, some southern records retain strong negative slopes across windows. The fixed comparisons reveal the influence of period choice without selecting a window solely because it produces a desired direction.",
"The 2019–2023 window is short and can be dominated by a few wet or dry years. Its slope should not be interpreted as a forecast or as evidence of permanent recovery. The same caution applies to steep early-window declines. Longer records, source comparisons and independent compartment observations are needed to distinguish transient variation from a durable change in storage regime."],5.3)
}

def front(w):
    w.numbering('lowerRoman');w.d.sections[0].different_first_page_header_footer=True
    w.intended_pages.append({'number':1,'title':'Cover'})
    w.para(TITLE,'Title',size=16,bold=True,align=WD_ALIGN_PARAGRAPH.CENTER,after=24)
    for text in ['by',AUTHOR,'A research thesis report','Master of Science in Water Engineering and Management','Advisor '+ADVISOR,'Asian Institute of Technology','Thailand','October 2026']:
        w.para(text,align=WD_ALIGN_PARAGRAPH.CENTER,after=15)
    w.page(2,'ABSTRACT');w.para(ABSTRACT,after=5)
    w.page(3,'CONTENTS');p=w.para('',spacing=1);w.field(p,'TOC \\o "1-2" \\h \\z')
    for name in ['TOC 1','TOC 2']:
        if name in w.d.styles:
            st=w.d.styles[name];st.font.name='Times New Roman';st.font.size=Pt(10.5);st.paragraph_format.line_spacing=1;st.paragraph_format.space_after=Pt(2)
    w.page(4,'LIST OF FIGURES');w.figure_list_placeholder=len(w.d.paragraphs)
    # Captions are known before writing body, preserving live page-reference fields.
    for number,(_,file,label,caption,paras,height) in sorted(PAGES.items()):
        p=w.para(label+' '+caption+'\t',size=10.5,align=WD_ALIGN_PARAGRAPH.LEFT,spacing=1,after=4);p.paragraph_format.tab_stops.add_tab_stop(Inches(6.1),WD_TAB_ALIGNMENT.RIGHT);w.field(p,'PAGEREF '+label.replace(' ','').replace('.','_')+' \\h')
    w.page(5,'LIST OF TABLES')
    for label,title in [('Table 3.1','Input records and scientific roles'),('Table 3.2','Storage-compartment definitions'),('Table 4.1','Evaluation chronology'),('Table 5.1','National source and structure comparisons'),('Table 5.2','National groundwater-panel comparisons'),('Table A.1','All-basin storage, native support and head evidence')]:
        p=w.para(label+' '+title+'\t',align=WD_ALIGN_PARAGRAPH.LEFT,spacing=1.2,after=9);p.paragraph_format.tab_stops.add_tab_stop(Inches(6.1),WD_TAB_ALIGNMENT.RIGHT);w.field(p,'PAGEREF '+label.replace(' ','').replace('.','_')+' \\h')
    w.page(6,'ABBREVIATIONS AND SYMBOLS')
    for a,b in [('AIT','Asian Institute of Technology'),('CSR','Center for Space Research'),('TWSA','Terrestrial water storage anomaly'),('GWSA','Groundwater storage anomaly'),('GLDAS','Global Land Data Assimilation System'),('G3P','Global Gravity-based Groundwater Product'),('NSE','Nash–Sutcliffe efficiency'),('FDR','False discovery rate'),('OLS','Ordinary least squares'),('P and PET','Precipitation and potential evapotranspiration'),('O, C and A','Observed, naturalized and historical-human storage'),('R, H and E','Residual, modeled direct-human perturbation and discrepancy'),('D','Descriptive discrepancy-magnitude index'),('Head','Signed negative depth to water; not water-storage volume')]:w.para(a+' — '+b,align=WD_ALIGN_PARAGRAPH.LEFT,spacing=1.3,after=7)
    w.d.add_section(WD_SECTION_START.NEW_PAGE);w.numbering('decimal');w.d.sections[-1].different_first_page_header_footer=False;foot=w.d.sections[-1].footer;foot.is_linked_to_previous=False
    for p in foot.paragraphs:p.clear()
    p=foot.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;w.field(p,'PAGE')

def write_thesis():
    w=Writer();front(w)
    TEXT[30][1].append('The reservoir extension uses MSEA-Res screened scene estimates and, separately, provider-interpolated daily storage. A fixed pre-2004 panel is summed only when every reservoir is represented, converted from km³ to basin-equivalent mm and referenced to available 2004–2009 months. Matched-month correlations remove calendar-month effects and linear trend; 499 whole-year cluster resamples describe conditional uncertainty. Reservoirs provide surface-water consistency evidence, not observed human-only storage.')
    TEXT[28][1].append('The retained base analysis also compares naturalized WaterGAP soil, canopy and snow storage with the same GLDAS Noah compartments. National agreement over 261 months is r=0.969, NSE=0.738 and RMSE=52.49 mm. This matched-compartment benchmark is distinct from full TWS and GWS validation: groundwater and surface water are excluded, climatic drivers may be shared, and GLDAS already contributes to the GWS subtraction.')
    chapters={7:(1,'Introduction'),11:(2,'Literature Review'),18:(3,'Study Area and Data'),24:(4,'Methodology'),34:(5,'Results'),53:(6,'Discussion'),56:(7,'Conclusions and Recommendations')}
    toc_pages={8,9,12,13,14,15,16,19,20,23,25,26,28,30,31,32,33,35,37,41,44,45,48,49,54,55}
    for page in range(7,57):
        if page in TEXT:title,paras=TEXT[page]
        else:title,_,_,_,paras,_=PAGES[page]
        if page==7:
            w.intended_pages.append({'number':7,'title':title});w.heading('CHAPTER 1\nINTRODUCTION',1);w.heading('1.1 '+title,toc=False)
        elif page in chapters:
            chapter,titlec=chapters[page];w.page(page,titlec,chapter=chapter);w.heading(title,toc=False)
        else:w.page(page,title,toc=page in toc_pages)
        if page in PAGES:
            _,file,label,cap,paras,height=PAGES[page];w.fig(label,cap,file,height=height)
        if page==24:w.eq('GWSA = TWSA − SMSA − SWSA − CWSA − SWEA')
        if page==26:w.eq('R = O − C = (A − C) + (O − A) = H + E')
        if page==27:w.eq('D = |β_E| / (|β_H| + |β_E|)')
        if page==19:
            w.table('Table 3.1','Input records and scientific roles',['Record','Period used','Role'],[
                ['CSR RL06.3','Apr 2002–Sep 2024','Primary gravity storage'],['GLDAS Noah','Apr 2002–Sep 2024','Soil, canopy, snow'],['G3P v1.12','Apr 2002–Sep 2023','Surface water and alternatives'],['WaterGAP 2.2e','1981–2023','Naturalized/historical pairing'],['Multisource cube','2003–2024','CHIRPS and ancillary context'],['Thai GROW observations','2004–2024 annual; 2018–2023 monthly','Groundwater consistency']],widths=[1.65,1.85,2.65]);paras=paras[:2]+paras[-1:]
        if page==21:
            w.table('Table 3.2','Storage-compartment definitions',['Term','Primary representation'],[['TWSA','CSR corrected mass anomaly'],['SMSA','Four GLDAS Noah soil layers'],['SWSA','G3P modeled surface-water anomaly'],['CWSA and SWEA','GLDAS canopy and snow'],['Soil sensitivity','Filtered root-zone alternative']],widths=[1.25,4.9]);paras=paras[:3]
        if page==28:
            w.table('Table 4.1','Evaluation chronology',['Role','Years','Target use'],[['Warm-up','1981–1990','Antecedent climate memory'],['Train','1991–2009','Fit and internal tuning'],['Validation','2010–2015','Freeze model selection'],['Test','2016–2023','Held-out evaluation']],widths=[1.25,1.5,3.4]);paras=paras[:3]+paras[-1:]
        for para in paras:w.para(para)
        if page==37:
            w.table('Table 5.1','National common-support Sen slopes in millimetres per year',['Processing chain','TWSA','GWSA'],[[label,fmt(select('national_product_audit',variable='TWSA',source=source)['sen_slope_mm_year']),fmt(select('national_product_audit',variable='GWSA',source=source)['sen_slope_mm_year'])] for source,label in [('CSR','CSR-based'),('COSTG_G3P','COST-G/G3P'),('Legacy_unidentified','Legacy unidentified')]],widths=[3.15,1.5,1.5])
        if page==49:
            w.table('Table 5.2','National GWS residual and head comparisons',['Panel','Years','Raw r'],[[label,select('national_groundwater',variable='GWSA',component='residual_mm',quality=q)['n_years'],fmt(select('national_groundwater',variable='GWSA',component='residual_mm',quality=q)['r'],3)] for q,label in [('retained_flags','All overlap'),('fixed_2013_2022','Fixed eligibility'),('common_period_retained','All wells common period'),('strict_balanced_2013_2022','Strict balanced')]],widths=[3.35,1.3,1.5])
    # Concise author lists follow the manuscript's author-date bibliography style.
    split=(len(REFS)+1)//2
    for page,refs in [(57,REFS[:split]),(58,REFS[split:])]:
        w.page(page,'REFERENCES' if page==57 else 'REFERENCES CONTINUED',toc=page==57)
        for ref in refs:
            p=w.para(ref,size=10.5,spacing=1.0,after=3,align=WD_ALIGN_PARAGRAPH.LEFT);p.paragraph_format.left_indent=Inches(.25);p.paragraph_format.first_line_indent=Inches(-.25)
    w.page(59,'APPENDIX A\nALL BASIN RESULTS',toc=True)
    rows=[]
    for z in S['basin_support']:
        code=z['region']
        if code=='TH':continue
        tw=next(x for x in S['basin_trends'] if x['region']==code and x['variable']=='TWSA');gw=next(x for x in S['basin_trends'] if x['region']==code and x['variable']=='GWSA')
        rows.append([code+' '+z['region_name'],fmt(tw['sen_slope_mm_year']),fmt(gw['sen_slope_mm_year']),fmt(z['native_weight_concentration_count'],1)])
    w.table('Table A.1','All-basin primary slopes and mapped support',['Basin','TWSA mm/yr','GWSA mm/yr','Native conc.'],rows,widths=[3.05,1.05,1.05,1.0])
    w.para('Native concentration is inverse weight concentration, not an independent sample count. All principal basins retain the provider small-support caution. Complete tests, intervals, coverage and groundwater evidence are in the versioned CSV tables.',size=10.5,spacing=1.15)
    title,paras=TEXT[60];w.page(60,'APPENDIX B\n'+title.upper(),toc=True)
    for para in paras:w.para(para)
    w.para('Code and data access: https://github.com/pratikkhanal16/thailand-water-storage-dss',size=11,align=WD_ALIGN_PARAGRAPH.LEFT)
    path=OUT/'report/AIT_Extended_Thesis_Farzeen_Khan.docx';w.save(path)
    (OUT/'logs/report_page_contract.json').write_text(json.dumps(w.intended_pages,indent=2),encoding='utf-8')
    return w

if __name__=='__main__':
    thesis=write_thesis()
    (OUT/'logs/writing_source.json').write_text(json.dumps({'author':AUTHOR,'title':TITLE,'manuscript_title':PAPER_TITLE,'abstract':ABSTRACT,'text_pages':TEXT,'figure_pages':PAGES,'references':REFS},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Extended thesis created; Word pagination and visual review required.')
