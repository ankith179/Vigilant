// Run a copy in a private runtime directory with the bundled node_modules link.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile, FileBlob } from '@oai/artifact-tool';

const root=process.env.VIGILANT_PROJECT_ROOT;
const work=process.env.VIGILANT_DECK_WORK;
const skill='/root/.codex/skills/builtins/presentations';
if(!path.isAbsolute(root||'')||!path.isAbsolute(work||'')) throw Error('Absolute project and private build paths required');
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const family=resolvePresentationFont();
const summary=JSON.parse(await fs.readFile(path.join(root,'reports/results/summary.json'),'utf8'));
const demo=JSON.parse(await fs.readFile(path.join(root,'reports/submission/demo-evidence.json'),'utf8'));
if(summary.status!=='COMPLETED'||summary.rag.reduce((a,r)=>a+r.queries,0)!==251)throw Error('Incomplete source');
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#142B3C',muted:'#526778',teal:'#167B78',amber:'#AB7135',red:'#A24756',pale:'#ECF3F5',line:'#CFDADF'};
const source='Source: reports/results/summary.json and its immutable experiment provenance.';
function text(slide,value,x,y,w,h,size=26,bold=false,color=C.ink){
 const t=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 t.text=value;t.text.style={typeface:family,fontSize:size,bold,color,autoFit:'none'};return t;
}
function slide(title,notes=source){const s=deck.slides.add();s.background.fill='#FFFFFF';text(s,title,64,42,1152,100,44,true);s.speakerNotes.textFrame.setText(notes);return s;}
function note(s,value){text(s,value,64,632,1152,60,22,false,C.muted);}
function row(s,label,value,y){text(s,label,64,y,290,50,28,true,C.teal);text(s,value,400,y,805,82,28);}
function box(s,value,x,y,w,h){const b=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:C.pale,line:{fill:C.line,width:1}});b.text=value;b.text.style={typeface:family,fontSize:26,bold:true,color:C.ink,alignment:'center',verticalAlignment:'middle',autoFit:'none'};return b;}
function connect(s,a,b,from='right',to='left'){s.shapes.connect(a,b,{kind:'straight',fromSide:from,toSide:to,line:{style:'solid',fill:C.teal,width:2},tail:{type:'triangle',width:'sm',length:'sm'}});}
function table(s,values,widths,y=185,h=340,size=25){
 const tb=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height:h,columnWidths:widths,values});
 tb.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=tb.getCell(r,c);cell.fill=r===0?C.ink:(r%2===0?'#F3F6F7':'#FFFFFF');
  cell.text.style={typeface:family,fontSize:size,bold:r===0,color:r===0?'#FFFFFF':C.ink,autoFit:'none'};
 }
 return tb;
}
function chart(s,categories,series,options={}){
 const ch=s.charts.add('bar',{position:{left:70,top:172,width:1140,height:420},categories,
 series:series.map((v,i)=>({...v,values:v.values.map(x=>Number(x.toFixed(4))),fill:[C.ink,C.teal,C.amber][i],valuesFormatCode:'0.0000'})),
 barOptions:{direction:'column',grouping:'clustered',gapWidth:85},hasLegend:true,
 legend:{position:'bottom',overlay:false,textStyle:{fontSize:23,fill:C.ink,typeface:family}},
 xAxis:{textStyle:{fontSize:23,fill:C.ink,typeface:family},line:{fill:C.line,width:1}},
 yAxis:{min:0,max:options.max||0.9,majorUnit:options.step||0.2,numberFormatCode:'0.0',textStyle:{fontSize:21,fill:C.muted,typeface:family},majorGridlines:{fill:C.line,width:1}},
 dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:21,fill:C.ink,typeface:family}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF'});
 applyPresentationChartFont(ch,{fontFamily:family});return ch;
}
const score=(d,m,k='map')=>summary.traceability.find(r=>r.dataset===d&&r.method===m)[k];

// 1
{
 const s=deck.slides.add();s.background.fill=C.ink;
 text(s,'VIGILANT',64,172,1152,110,78,true,'#FFFFFF');
 text(s,'Software changes, traceability\nand evidence-backed investigation',68,310,1090,130,40,false,'#FFFFFF');
 text(s,'M.Tech research demonstration\n8 October 2026',68,545,1000,90,26,false,'#C8DEE4');
 s.speakerNotes.textFrame.setText('Technical demonstration draft. Add confirmed author, supervisor and institutional details before the final viva. The deck uses executed experiment records and reports negative findings explicitly.');
}
// 2
{
 const s=slide('Research scope');
 row(s,'Change detection','Which versioned artifacts changed between two Git commits?',180);
 row(s,'Traceability','Which requirements, code and tests are relevant candidates?',290);
 row(s,'Consistency','What can the available source evidence support?',400);
 row(s,'Evaluation','Do measured outcomes improve over appropriate baselines?',510);
}
// 3
{
 const s=slide('VIGILANT architecture','Source: docs/INTERFACE_CONTRACTS.md, knowledge_graph/graph.py and workflow execution in '+demo.source+'. Diagram summarizes implemented data flow. Similarity links remain candidates.');
 const git=box(s,'Git commits',64,180,245,80),art=box(s,'Versioned artifacts',400,180,330,80);
 const ret=box(s,'Hybrid retrieval',880,180,335,80),kg=box(s,'Structural graph',400,355,330,80);
 const ev=box(s,'Evidence + tools',880,355,335,80),out=box(s,'Rules + model\nReport',880,515,335,85);
 connect(s,git,art);connect(s,art,ret);connect(s,art,kg,'bottom','top');connect(s,ret,ev,'bottom','top');connect(s,kg,ev);connect(s,ev,out,'bottom','top');
 note(s,'Evidence retains commit, path, line range and content hash. The local API serves persisted records to the frontend.');
}
// 4
{
 const s=slide('Knowledge graph around the changed API','Source: reports/submission/demo-evidence.json, extracted read-only from data/snapshots/vigilant.db. Baseline '+demo.base_commit+'; changed '+demo.head_commit+'. Native diagram displays recorded static EXPOSES_API and exact-literal-contract CONSUMES_API edges. Structural matching is heuristic and does not establish a defect.');
 const edges=demo.graph_slices.base.edges;
 if(!edges.some(e=>e.relation_type==='EXPOSES_API')||!edges.some(e=>e.relation_type==='CONSUMES_API'))throw Error('Required graph edges absent');
 text(s,'Baseline commit 1762ada',64,154,1000,42,26,true,C.teal);
 const fn=box(s,'read_item\nBackend function',64,255,280,90),api=box(s,'GET /items/{id}\nAPI artifact',485,255,310,90),client=box(s,'readItem\nFrontend caller',935,255,280,90);
 connect(s,fn,api);connect(s,client,api,'left','right');
 text(s,'EXPOSES_API',335,211,200,40,22,true);text(s,'CONSUMES_API',797,211,240,40,22,true);
 text(s,'Changed commit 892a3d5',64,406,1000,42,26,true,C.teal);
 text(s,'Backend now exposes /catalog/{id}',64,474,1152,45,31,true);
 text(s,'Frontend keeps /api/v1/items/{id}. Its old API match disappears.',64,535,1152,58,29);
 note(s,'The investigation compares both snapshots. A missing graph endpoint prompts review of the replacement.');
}
// 5
{
 const s=slide('Evaluation populations');
 const names={'eTour_en':'eTour English','RTMX-module-valid':'RTMX modules'};
 table(s,[['Dataset','Requirements','Linked queries','Targets','Gold links'],...summary.datasets.map(r=>[names[r.dataset]||r.dataset,r.requirements,r.linked_queries,r.targets,r.links])],[330,210,220,180,212],185,330,25);
 note(s,'Ranking uses linked queries only. RTMX has seven modules. Controlled changes and SAFA have separate ground-truth scopes.');
}
// 6
{
 const ds=['SMOS','iTrust','eTour_en'];const s=slide('Graph context has mixed ranking effects');
 chart(s,['SMOS','iTrust','eTour English'],[{name:'BM25',values:ds.map(d=>score(d,'bm25'))},{name:'Hybrid',values:ds.map(d=>score(d,'hybrid'))},{name:'Hybrid + KG',values:ds.map(d=>score(d,'hybrid_kg'))}],{max:0.6,step:0.1});
 note(s,'Mean average precision, higher is better. On eTour, graph MAP rises while micro F1@10 falls from 0.3804 to 0.3713.');
}
// 7
{
 const ds=summary.datasets.map(r=>r.dataset);const s=slide('RAG produces mixed MAP results');
 chart(s,['SMOS','iTrust','eTour English','RTMX modules'],[{name:'Hybrid MAP',values:ds.map(d=>score(d,'hybrid'))},{name:'Hybrid + RAG MAP',values:ds.map(d=>score(d,'hybrid_rag_top5'))}]);
 note(s,'251 actual generations. MAP decreases on iTrust and RTMX. Reranking only the first five candidates leaves Recall@5 and @10 unchanged.');
}
// 8
{
 const s=slide('The local model abstains in every case');
 table(s,[['Variant','Calls','Label agreement','Uncertainty','Endpoint recall'],...summary.ablation.summary.map(r=>[r.variant,r.cases,(r.status_agreement*100).toFixed(0)+'%',(r.uncertainty_rate*100).toFixed(0)+'%',r.known_endpoint_recall.toFixed(2)])],[270,130,250,240,262],170,325,25);
 text(s,'E: LLM only   F: RAG   G: + graph   H: + tools   I: + temporal context',64,527,1152,65,23);
 note(s,'All variants match the always-UNCERTAIN baseline at 25% authored-label agreement. Endpoint recall uses a partial authored oracle.');
}
// 9
{
 const s=slide('Recorded API-change demonstration','Source: docs/DEMO_RECORD.md and '+demo.source+'. Baseline '+demo.base_commit+'; changed '+demo.head_commit+'. These are recorded outputs, not a claim that the browser demonstration ran in this environment.');
 row(s,'Backend change','Route prefix changes from /items to /catalog',185);
 row(s,'Unchanged client',"url: '/api/v1/items/{id}'",300);
 row(s,'Rule finding','POTENTIAL_INCONSISTENCY',415);
 row(s,'Model decision','UNCERTAIN',525);
}
// 10
{
 const s=slide('Investigation trajectory','Source: '+demo.source+'. Actual ordered trajectory: '+demo.trajectory.map(t=>t.tool).join(', ')+'. All twelve stages recorded SUCCESS. Named roles follow a fixed workflow rather than autonomous tool planning.');
 row(s,'1–3  Repository','Resolve commits, import snapshots, detect changed symbols',175);
 row(s,'4–6  Graph','Build both snapshots and traverse affected candidates',280);
 row(s,'7–9  Evidence','Recover trace candidates, retrieve context, apply rules',385);
 row(s,'10–12  Decision','Verify source excerpts, call the model, persist the report',490);
 note(s,'Twelve successful tool stages. Eleven changed artifact records, 33 impact candidates and 24 verified excerpts.');
}
// 11
{
 const s=slide('Evidence and interpretation','Source: docs/DEMO_RECORD.md. Evidence 41a15f4d521cebdbac2a7cbb8cad870a53288742fccc9cdb0b1183a335c3bf7a, frontend/src/client/sdk.gen.ts lines 340–343 at '+demo.head_commit+'. Quote validation checks source equality, not semantic entailment.');
 text(s,'frontend/src/client/sdk.gen.ts',64,175,1152,45,28,true,C.teal);
 text(s,"url: '/api/v1/items/{id}',",64,255,1152,80,38,true);
 text(s,'Lines 340–343 at changed commit 892a3d5',64,350,1152,50,27,false,C.muted);
 text(s,'The client retains the old contract.\nThe rule proposes an inconsistency for review.',64,445,1152,105,32);
 note(s,'Fifteen rule findings share a route-renaming cause. They do not represent fifteen independent confirmed defects.');
}
// 12
{
 const s=slide('Reopening the saved demonstration','Source: README.md, docs/DEMO_RECORD.md, windows installation scripts and immutable pipeline record. Browser navigation remains unverified in this environment. No Windows execution has been observed.');
 row(s,'1. Restore','Use the complete project ZIP and included Windows installer',170);
 row(s,'2. Start','Launch the local API and frontend with the saved setup guide',275);
 row(s,'3. Inspect','Choose the API-change analysis for commit 892a3d5',380);
 row(s,'4. Review','Open graph, evidence, investigation and report views',485);
 note(s,'The recorded JSON report remains available if the browser is unavailable. Models restore from pinned manifests.');
}
// 13
{
 const s=slide('What the evidence supports');
 row(s,'Executed','Git changes, persisted graph, retrieval and tool investigation',170);
 row(s,'Measured','251 RAG calls, 60 ablation calls and 12 controlled scenarios',275);
 row(s,'Research finding','Mixed retrieval effects. No model classification gain established.',380);
 row(s,'Still required','Independent labels, browser and Windows checks, institutional review',485);
 note(s,'The thesis and paper drafts report these limits. Publication and final university acceptance remain external decisions.');
}
// 14
{
 const s=slide('Appendix: complete MAP comparison');
 const methods=['tfidf','bm25','embedding','hybrid','hybrid_kg','hybrid_rag_top5'];
 table(s,[['Dataset','TF-IDF','BM25','MiniLM','Hybrid','+KG','+RAG'],...summary.datasets.map(r=>[r.dataset==='RTMX-module-valid'?'RTMX modules':r.dataset==='eTour_en'?'eTour English':r.dataset,...methods.map(m=>summary.traceability.some(x=>x.dataset===r.dataset&&x.method===m)?score(r.dataset,m).toFixed(4):'Not run')])],[276,146,146,146,146,146,146],205,310,23);
 note(s,'Separate arithmetic audits passed for 23 method rows and 1484 query rows. This verification does not replace independent semantic review.');
}

await fs.mkdir(path.join(work,'output'),{recursive:true});
const candidate=path.join(work,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const final=path.join(work,'output','VIGILANT-Demonstration.pptx');
const result=await finalizePresentation({workspaceDir:work,candidatePath:candidate,finalPath:final,
 pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',... [5,8,14].flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:[5,8,14],requiredNativeChartOwnerSlides:[6,7],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,receiptPath:path.join(work,'validation.json')});
console.log(JSON.stringify({final,result}));
const finished=await PresentationFile.importPptx(await FileBlob.load(final));
await fs.mkdir(path.join(work,'renders'),{recursive:true});
for(let i=0;i<finished.slides.items.length;i++){
 const image=await finished.export({slide:finished.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(work,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await image.arrayBuffer()));
}
console.log('Rendered all final slides');
