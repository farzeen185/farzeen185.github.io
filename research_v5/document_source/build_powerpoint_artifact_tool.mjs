import fs from 'node:fs/promises';
import {Presentation,PresentationFile,layers,text} from '@oai/artifact-tool';
const ROOT='P:/twsa/Thailand_Research_v5/presentation';
const D=JSON.parse(await fs.readFile(ROOT+'/slide_content.json','utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
function tx(v,x,y,w,h,z=30,color='#1e2930',bold=false){return text([v],{position:{left:x,top:y},width:w,height:h,style:{typeface:'Times New Roman',fontSize:`${z}px`,color,bold,wrap:true,verticalAlignment:'top'}})}
for(let i=0;i<D.length;i++){
 const d=D[i],s=p.slides.add();s.background.fill='#ffffff';
 const items=[tx(d.title,54,35,1172,96,43,'#173c50',true),tx('Farzeen Khan  ·  AIT  ·  October 2026',54,682,1030,23,19,'#61707a'),tx(`${i+1} / ${D.length}`,1150,682,90,23,19,'#61707a')];
 if(i===0){items.push(tx('Farzeen Khan',54,193,1172,60,39,'#173c50'),tx('MS in Water Engineering and Management',54,298,1172,52,31),tx('Asian Institute of Technology',54,367,1172,52,31),tx('Advisor: Dr. Natthachet Tangdamrongsub',54,468,1172,62,31));}
 else if(!d.figure&&!d.table){
   let y=175;if(d.equation){items.push(tx(d.equation,54,155,1172,72,33,'#173c50'));y=263;}
   for(let j=0;j<d.lines.length;j++)items.push(tx(d.lines[j],70,y+j*(d.equation?102:132),1140,d.equation?94:112,30));
 }
 if(d.source)items.push(tx(d.source,54,624,1172,50,18,'#637079'));
 s.compose(layers({width:'fill',height:'fill'},items),{frame:{left:0,top:0,width:1280,height:720},baseUnit:1});
 if(d.figure)s.images.add({blob:await fs.readFile(ROOT+'/figures/'+d.figure+'.png'),contentType:'image/png',position:{left:54,top:145,width:1172,height:464},fit:'contain',alt:d.title});
 if(d.table){
   const cols=d.table[0].length;const widths=cols===2?[470,702]:cols===3?[360,260,552]:cols===4?[440,210,260,262]:[210,280,190,210,282];
   const t=s.tables.add({rows:d.table.length,columns:cols,left:54,top:167,width:1172,height:Math.min(440,d.table.length*68),values:d.table,columnWidths:widths});
   t.borders.assign({style:'solid',fill:'#bdc9d0',width:.7});
   for(let r=0;r<d.table.length;r++)for(let c=0;c<cols;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#eaf0f4':'#ffffff';cell.text.style={typeface:'Times New Roman',fontSize:cols>=4?24:26,color:'#1e2930',bold:r===0};}
 }
 s.speakerNotes.textFrame.setText(d.source+'\nSource: extended CSR-based study; the thesis, manuscript, analysis scripts and LaTeX Beamer source accompany this deck.');
}
await fs.mkdir(ROOT+'/.build',{recursive:true});
await (await PresentationFile.exportPptx(p)).save(ROOT+'/.build/candidate.pptx');
console.log('Editable candidate exported',D.length,'slides.');
