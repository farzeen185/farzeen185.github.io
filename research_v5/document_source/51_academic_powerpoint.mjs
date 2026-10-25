import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const runtime='C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
process.env.RUNTIME_NODE_MODULES=runtime;
const req=createRequire(path.join(runtime,'__runtime__.cjs'));
const {Presentation,PresentationFile,layers,text}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const SKILL='C:/Users/ASUS/.codex/plugins/cache/openai-primary-runtime/presentations/26.1024.11018/skills/presentations';
const ROOT=process.env.TWSA_RESEARCH_ROOT||'P:/twsa';
const P=path.join(ROOT,'Thailand_Research_v5/presentation/academic_metropolis');
const {slides:D,main_slides:main}=JSON.parse(await fs.readFile(P+'/academic_slides.json','utf8'));
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const color={navy:'#203a49',teal:'#368c83',paper:'#fafaf8',gray:'#5b6c75'};
function tx(str,x,y,w,h,z=30,fill=color.navy,bold=false){return text([str],{position:{left:x,top:y},width:w,height:h,style:{typeface:'Arial',fontSize:`${z}px`,color:fill,bold,wrap:true,verticalAlignment:'top'}})}
function block(s,str,x,y,w,h,z=30,fill=color.navy,bold=false){s.compose(layers({width:'fill',height:'fill'},[tx(str,x,y,w,h,z,fill,bold)]),{frame:{left:0,top:0,width:1280,height:720},baseUnit:1})}
function fillRect(s,x,y,w,h,fill){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}})}
const tableOwners=[];
for(let i=0;i<D.length;i++){
 const d=D[i],s=deck.slides.add();s.background.fill=color.paper;
 if(d.layout==='title'){
  block(s,d.title,74,113,1100,148,58,color.navy,true);
  block(s,d.lines[0],77,283,1100,84,31,color.teal);
  block(s,'Farzeen Khan',77,424,1100,51,34,color.navy,true);
  block(s,'MS in Water Engineering and Management\nAsian Institute of Technology',77,489,1100,78,25);
  block(s,'Advisor: Dr. Natthachet Tangdamrongsub',77,598,1100,40,25);
 } else {
  // These are the repeated Metropolis template header/progress elements.
  fillRect(s,0,0,1280,111,color.navy);
  block(s,d.title,54,25,1172,77,d.title.length>66?33:39,'#ffffff',true);
  fillRect(s,0,109,1280*(Math.min(i+1,main)/main),4,color.teal);
  if(d.figure){
   const split=d.layout==='split';
   s.images.add({blob:await fs.readFile(P+'/figures/'+d.figure+'.png'),contentType:'image/png',position:split?{left:64,top:139,width:508,height:468}:{left:54,top:135,width:1172,height:455},fit:'contain',alt:d.title});
   if(split)for(let j=0;j<d.lines.length;j++)block(s,d.lines[j],643,205+j*123,560,110,30);
  } else if(d.table){
   const cols=d.table[0].length,dense=d.table.length>8;
   const widths=cols===2?[335,837]:cols===3?[410,330,432]:cols===4?[570,190,190,222]:Array(cols).fill(1172/cols);
   if(d.lines.length)block(s,d.lines[0],54,133,1172,44,25);
   const top=d.lines.length?190:(dense?144:165);
   const height=dense?415:Math.min(408,d.table.length*62);
   const t=s.tables.add({rows:d.table.length,columns:cols,left:54,top,width:1172,height,values:d.table,columnWidths:widths});
   t.borders.assign({style:'solid',fill:'#ccd3d5',width:.5});
   for(let r=0;r<d.table.length;r++)for(let c=0;c<cols;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?'#e5edec':color.paper;
    cell.text.style={typeface:'Arial',fontSize:dense?23:(cols>3?25:27),color:color.navy,bold:r===0};
   }
   tableOwners.push(i+1);
  } else {
   let y=d.equation?270:172;
   if(d.equation)block(s,d.equation,54,164,1172,84,d.equation.length>50?34:37,color.teal,true);
   const step=d.lines.length>3?94:123;
   for(let j=0;j<d.lines.length;j++)block(s,d.lines[j],65,y+j*step,1150,step-14,d.lines.length>4?27:30);
  }
 }
 if(d.note)block(s,d.note,54,605,1172,70,d.note.length>340?17:19,color.gray);
 if(d.layout!=='title'){
  block(s,d.backup?'Supporting results':d.section,54,687,1030,23,17,color.gray);
  block(s,d.backup?`B${i-main+1}`:`${i+1} / ${main}`,1130,685,96,25,18,color.gray);
 }
 s.speakerNotes.textFrame.setText([d.note,'Source: verified Thailand extended study, report and basin/forcing appendix.',d.backup?'Backup slide for discussion.':'Main research presentation.'].join('\n'));
}
const build=path.join(P,'.build');await fs.mkdir(build,{recursive:true});
const validated=path.join(P,'validated');await fs.mkdir(validated,{recursive:true});
const stamp=Date.now();const candidate=path.join(build,`candidate_${stamp}.pptx`),final=path.join(validated,`validated_${stamp}.pptx`);
await(await PresentationFile.exportPptx(deck)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
await finalizePresentation({workspaceDir:P,candidatePath:candidate,finalPath:final,
 pythonExecutable:'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 explicitTotalSlideCount:D.length,requiredNativeTableOwnerSlides:tableOwners,
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`validation_${stamp}.json`)});
await fs.copyFile(final,path.join(P,'Thailand_Academic_Metropolis.pptx'));
console.log('Academic editable PowerPoint:',D.length,'slides;',main,'main;',tableOwners.length,'native tables.');
