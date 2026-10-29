import React,{useEffect,useState} from 'react';
import './chat.css';

export default function Chat({api}){
 const[reports,setReports]=useState([]),[run,setRun]=useState(''),[finding,setFinding]=useState(''),[source,setSource]=useState(null);
 const[open,setOpen]=useState(false),[repositories,setRepositories]=useState([]),[commits,setCommits]=useState([]);
 const[repository,setRepository]=useState(''),[commit,setCommit]=useState(''),[model,setModel]=useState('none');
 const[ollamaModel,setOllamaModel]=useState('qwen3:8b'),[messages,setMessages]=useState([]),[question,setQuestion]=useState('');
 const[intent,setIntent]=useState(''),[context,setContext]=useState(null),[pendingRun,setPendingRun]=useState('');
 const[loading,setLoading]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;Promise.all([api('repositories?limit=500'),api('commits?limit=500')]).then(([r,c])=>{
  if(active){setRepositories(r.items||[]);setCommits(c.items||[]);if(r.items?.length)setRepository(r.items[0].repository)}
 }).catch(e=>active&&setError(e.message));return()=>{active=false}},[api]);
 useEffect(()=>{let available=commits.filter(item=>item.repository===repository);if(!available.some(item=>item.commit_id===commit))setCommit(available[0]?.commit_id||'')},[repository,commits,commit]);
 useEffect(()=>{setMessages([]);setError('');setRun('');setFinding('');setSource(null);setQuestion('');setContext(null);setIntent('')},[repository,commit]);
 useEffect(()=>{let active=true;(async()=>{let all=[],offset=0;for(;;){let d=await api('reports?'+new URLSearchParams({repository,commit_id:commit,limit:500,offset}));all.push(...d.items.filter(r=>r.status==='COMPLETED'&&r.changes));if(!d.has_more)break;offset=d.next_offset}if(active)setReports(all)})().catch(e=>active&&setError(e.message));return()=>{active=false}},[repository,commit,api]);
 useEffect(()=>{if(pendingRun&&reports.some(r=>r.run_id===pendingRun)){setRun(pendingRun);setPendingRun('')}},[reports,pendingRun]);
 const selectedReport=reports.find(r=>r.run_id===run);
 useEffect(()=>{setMessages([]);setFinding('');setSource(null);setQuestion('');setContext(null);setIntent('')},[run]);
 async function send(event){
  event.preventDefault();let text=question.trim();if(!text||!repository||!commit||loading)return;
  const history=messages.slice(-6).map(item=>({role:item.role,content:item.role==='user'?item.content:item.result.answer}));
  setMessages(items=>[...items,{role:'user',content:text}]);setQuestion('');setLoading(true);setError('');
  try{let result=await api(selectedReport?'report-chat':'chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(selectedReport?{project_id:selectedReport.project_id,repository,run_id:run,base_commit:selectedReport.base_commit,head_commit:selectedReport.commit_id,question:text,finding_id:finding||null,intent:intent||null,context}:{repository,commit_id:commit,question:text,history,model,ollama_model:model==='ollama'?ollamaModel:null})});
   if(result.action==='COMPARE_REVISIONS'){
    let complete=null;
    for(let n=0;n<180;n++){
     const job=await api('reports/'+result.job_id);
     if(['FAILED','CANCELLED','TIMED_OUT'].includes(job.status)){result={...result,state:job.status,decision:{decision:job.status},answer:'Comparison '+job.status.toLowerCase()+': '+(job.error||'No completed comparison was produced.')};break}
     if(job.status==='COMPLETED'){complete=await api('reports/'+job.result_run_id);break}
     await new Promise(resolve=>setTimeout(resolve,1000));
    }
    if(complete)result={...result,state:'COMPLETED',decision:{decision:'COMPLETED'},comparison_report:complete,answer:`Compared ${complete.base_commit.slice(0,12)} → ${complete.commit_id.slice(0,12)}. Recorded ${complete.changes.files.length} changed files and ${complete.findings.length} findings. Open this investigation for evidence and impact-path follow-ups.`};
    else if(!['FAILED','CANCELLED','TIMED_OUT'].includes(result.state))result={...result,state:'RUNNING',decision:{decision:'RUNNING'},answer:'The comparison is still running. Find its saved job in Agent Investigation.'};
   }
   setMessages(items=>[...items,{role:'assistant',result}]);setContext(selectedReport?result.context||null:null)}
  catch(e){setError(e.message)}finally{setLoading(false)}
 }
 return <div className="vigilant-chat">
  {open&&<section className="chat-panel" role="dialog" aria-label="VIGILANT project chat">
   <header className="chat-header"><div><strong>VIGILANT Chat</strong><small>Repository evidence assistant</small></div><button type="button" aria-label="Close chat" onClick={()=>setOpen(false)}>×</button></header>
   <div className="chat-scope">
    <label>Repository<select disabled={loading} aria-label="Chat repository" value={repository} onChange={e=>setRepository(e.target.value)}><option value="">Select repository</option>{repositories.map(item=><option key={item.repository} value={item.repository}>{item.name||item.repository}</option>)}</select></label>
    <label>Snapshot<select disabled={loading} aria-label="Chat snapshot" value={commit} onChange={e=>setCommit(e.target.value)}><option value="">Select snapshot</option>{commits.filter(item=>item.repository===repository).map(item=><option key={item.commit_id} value={item.commit_id}>{item.commit_id.slice(0,12)}</option>)}</select></label>
    <label>Investigation<select disabled={loading} aria-label="Chat investigation" value={run} onChange={e=>setRun(e.target.value)}><option value="">Snapshot evidence search</option>{reports.map(r=><option key={r.run_id} value={r.run_id}>{r.base_commit.slice(0,7)} → {r.commit_id.slice(0,7)} · {r.run_id.slice(0,6)}</option>)}</select></label>
    {selectedReport&&<label>Finding<select disabled={loading} aria-label="Chat finding" value={finding} onChange={e=>{setFinding(e.target.value);setMessages([]);setContext(null)}}><option value="">All recorded findings</option>{selectedReport.findings.map(f=><option key={f.finding_id} value={f.finding_id}>{f.status}: {f.rule}</option>)}</select></label>}
    {selectedReport&&<label>Topic<select aria-label="Chat topic" disabled={loading} value={intent} onChange={e=>setIntent(e.target.value)}><option value="">Detect from question</option>{[['CHANGES','Changes'],['FINDING','Finding'],['IMPACT','Impact chain'],['REQUIREMENT_TRACE','Requirement trace'],['API_CONTRACT','API contract'],['TEST_OBLIGATIONS','Test obligations'],['EVIDENCE','Evidence'],['LIMITATIONS','Coverage and limitations']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>}
    {!selectedReport&&<label>Reasoning<select disabled={loading} aria-label="Chat reasoning provider" value={model} onChange={e=>setModel(e.target.value)}><option value="none">Evidence only</option><option value="ollama">Local Ollama</option><option value="local">Local Transformers</option><option value="omniroute">OmniRoute</option><option value="glm">GLM API (external)</option></select></label>}
    {!selectedReport&&model==='ollama'&&<label>Model<select disabled={loading} aria-label="Chat Ollama model" value={ollamaModel} onChange={e=>setOllamaModel(e.target.value)}><option>qwen3:8b</option><option>qwen2.5-coder:14b</option><option>qwen3:14b</option></select></label>}
   </div>
   <div className="chat-messages" aria-live="polite">
    {!messages.length&&<p className="chat-empty">Ask “Explain this project”, “compare HEAD~1 with HEAD”, what changed, why a finding was raised, or which evidence and tests deserve review.</p>}
    {messages.map((item,index)=><article className={'chat-message '+item.role} key={index}>
     {item.role==='user'?<p>{item.content}</p>:<>
      <strong>{item.result.decision.decision}</strong><p>{item.result.answer}</p>
      {item.result.claims?.length>0&&<details className="chat-citations"><summary>Claim support</summary>{item.result.claims.map((claim,i)=><p key={i}>{claim.text}<br/><small>{claim.support_level} · {claim.basis} · {claim.evidence_ids.length} excerpt references</small></p>)}</details>}
      {item.result.impact_paths?.length>0&&<details className="chat-citations"><summary>Recorded dependency paths</summary>{item.result.impact_paths.map((path,i)=><div key={i}><b>{path.revision_role} revision</b>{path.steps.map((step,j)=><p key={j}>{step.from_artifact.slice(0,12)} → {step.to_artifact.slice(0,12)}<br/>{step.edge_options.map(e=>[e.relation_type,e.provenance_type,e.resolution_status].join(' · ')).join('; ')}</p>)}</div>)}</details>}
      {item.result.comparison_report&&<button type="button" onClick={()=>{let r=item.result.comparison_report;if(commit===r.commit_id){setReports(items=>[r,...items.filter(x=>x.run_id!==r.run_id)]);setRun(r.run_id)}else{setPendingRun(r.run_id);setCommits(items=>items.some(x=>x.repository===r.repository&&x.commit_id===r.commit_id)?items:[...items,{repository:r.repository,commit_id:r.commit_id,subject:'Chat comparison'}]);setCommit(r.commit_id)}}}>Explain this comparison</button>}
      {item.result.test_suggestions?.length>0&&<details className="chat-citations"><summary>Test review suggestions</summary>{item.result.test_suggestions.map((s,i)=><p key={i}>{s.file}:{s.start_line} — {s.question}<br/><small>{s.status} · {s.expected_behavior} · {s.test_execution}</small></p>)}</details>}
      {item.result.validation_error&&<p className="chat-warning">The model response failed validation; treat this answer as uncertain.</p>}
      {item.result.citations.length>0&&<div className="chat-citations"><b>Source citations</b>{item.result.citations.map(source=><details key={source.evidence_id}><summary>{source.file}:{source.start_line}-{source.end_line}</summary><small>{source.revision_role||'Selected snapshot'} · {source.commit?.slice(0,12)} · {source.artifact_role||'Role unrecorded'} · {source.support_level||'SOURCE_MATCH_ONLY'}</small><pre>{source.quote}</pre>{source.source_url&&<button type="button" onClick={()=>api(source.source_url.replace('/api/','')).then(setSource).catch(e=>setError(e.message))}>Open exact source</button>}</details>)}</div>}
      {item.result.decision.decision==='UNCERTAIN'&&item.result.retrieved_evidence.length>0&&<div className="chat-citations"><b>Retrieved evidence, not claimed as support</b>{item.result.retrieved_evidence.map(source=><details key={source.evidence_id}><summary>{source.file}:{source.start_line}-{source.end_line}</summary><small>{source.revision_role||'Selected snapshot'} · {source.commit?.slice(0,12)} · {source.artifact_role||'Role unrecorded'} · {source.support_level||'SOURCE_MATCH_ONLY'}</small><pre>{source.quote}</pre>{source.source_url&&<button type="button" onClick={()=>api(source.source_url.replace('/api/','')).then(setSource).catch(e=>setError(e.message))}>Open exact source</button>}</details>)}</div>}
      <small className="chat-caveat">{item.result.confidence_note} Semantic support is not independently verified.</small>
     </>}
    </article>)}
    {loading&&<p className="chat-loading">Checking repository evidence…</p>}
   </div>
   {source&&<details className="chat-message chat-source" open><summary>{source.file_path} · {source.commit_id?.slice(0,12)}</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{source.content}</pre></details>}
   {error&&<p className="chat-error" role="alert">{error}</p>}
   <form key={repository+commit+run+loading} className="chat-form" onSubmit={send}><label className="visually-hidden" htmlFor="vigilant-chat-question">Question</label><textarea id="vigilant-chat-question" value={question} maxLength={1200} rows={3} placeholder="Ask about changes, findings or evidence…" onChange={e=>setQuestion(e.target.value)} disabled={!commit} readOnly={loading}/><button type="submit" aria-label="Send question" disabled={!commit||loading||!question.trim()}>Send</button></form>
   {!selectedReport&&model!=='none'&&<p className="chat-warning">Evidence excerpts and conversation context are sent to the selected reasoning provider. Check source content before using an external route.</p>}
   <footer>Session-only conversation · no repository changes are made</footer>
  </section>}
  <button className="chat-launcher" type="button" onClick={()=>setOpen(value=>!value)} aria-expanded={open} aria-label={open?'Close VIGILANT chat':'Open VIGILANT chat'}>Chat</button>
 </div>
}
