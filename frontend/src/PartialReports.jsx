import React,{useEffect,useRef,useState} from 'react';

const scopeQuery=scope=>new URLSearchParams(Object.fromEntries(['repository','base_commit','head_commit'].map(k=>[k,scope[k]])));
const short=id=>id.slice(0,12);

export default function PartialReports({api}){
  const [offset,setOffset]=useState(0),[catalog,setCatalog]=useState(null),[selection,setSelection]=useState(null);
  const [loaded,setLoaded]=useState(null),[target,setTarget]=useState(null),[source,setSource]=useState(null);
  const [error,setError]=useState(''),[sourceError,setSourceError]=useState(''),[line,setLine]=useState('1');
  const [intent,setIntent]=useState('scope'),[question,setQuestion]=useState(null),[answer,setAnswer]=useState(null),[exporting,setExporting]=useState(false);
  const sourceView=useRef(null);
  const currentReport=useRef(null);currentReport.current=loaded?.report.report_id;
  useEffect(()=>{if(target)sourceView.current?.scrollIntoView({block:'start'})},[target]);
  useEffect(()=>{
    let active=true;setCatalog(null);setSelection(null);setLoaded(null);setTarget(null);setError('');
    api('partial-reports?limit=10&offset='+offset).then(data=>active&&setCatalog(data)).catch(e=>active&&setError(e.message));
    return()=>{active=false};
  },[offset,api]);
  useEffect(()=>{
    let active=true;setLoaded(null);setTarget(null);setSource(null);setError('');
    if(selection)api('partial-reports/'+selection.report_id+'?'+scopeQuery(selection.scope))
      .then(data=>active&&setLoaded(data)).catch(e=>active&&setError(e.message));
    return()=>{active=false};
  },[selection,api]);
  useEffect(()=>{
    let active=true;setSource(null);setSourceError('');
    if(target&&loaded){
      const query=scopeQuery(loaded.report.scope);
      Object.entries(target).forEach(([k,v])=>query.set(k,v));query.set('max_lines','40');
      api('partial-reports/'+loaded.report.report_id+'/source?'+query)
        .then(data=>{if(active){setSource(data);setLine(String(data.evidence[0].start_line))}})
        .catch(e=>active&&setSourceError(e.message));
    }
    return()=>{active=false};
  },[target,loaded,api]);
  useEffect(()=>{
    let active=true;setAnswer(null);
    if(loaded&&question?.report_id===loaded.report.report_id){
      api('partial-reports/'+question.report_id+'/explain',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({...Object.fromEntries(scopeQuery(loaded.report.scope)),intent:question.intent})})
        .then(data=>active&&setAnswer(data)).catch(e=>active&&rejectDelivery(e.message,question.report_id));
    }
    return()=>{active=false};
  },[loaded,question,api]);
  function rejectDelivery(message,id){
    if(currentReport.current!==id)return;
    setLoaded(null);setAnswer(null);setSource(null);setTarget(null);setError(message);
  }
  function inspect(commit_id,artifact_id,start_line){
    setSource(null);setSourceError('');setTarget({commit_id,artifact_id,...(start_line?{start_line}:{})});
  }
  async function download(format){
    const id=loaded.report.report_id,query=scopeQuery(loaded.report.scope);query.set('format',format);
    setExporting(true);setError('');
    try{
      const token=sessionStorage.getItem('vigilant-token');
      const response=await fetch('/api/partial-reports/'+id+'/export?'+query,{headers:token?{Authorization:'Bearer '+token}:{},cache:'no-store'});
      if(!response.ok){const failure=await response.json();throw Error(failure.detail||'Partial report export failed')}
      const blob=await response.blob();if(currentReport.current!==id)return;
      const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='vigilant-partial-report-'+id+'.'+format;a.click();URL.revokeObjectURL(url);
    }catch(e){rejectDelivery(e.message,id)}finally{setExporting(false)}
  }
  const report=loaded?.report;
  return <section className="partial-reports">
    <h2>Partial development reports</h2>
    <p>Source-backed observations for review. Graph links remain candidates; missing evidence remains unknown.</p>
    <p className="partial-notice"><strong>91% accuracy: NOT_EVALUATED.</strong> Semantic correctness, complete impact and independent review are not established. No reviewed obligation means no MISSING_TEST finding.</p>
    {error&&<p role="alert" className="error">{error}</p>}
    {!catalog&&!error&&<p role="status">Loading partial report catalog…</p>}
    {catalog&&!catalog.enabled&&<p role="status">Partial reports are disabled. An administrator must enable a pinned report registry before this view can load evidence.</p>}
    {catalog?.enabled&&<>
      <p>Showing {catalog.items.length?offset+1:0}–{offset+catalog.items.length} of {catalog.total} development cases. Source validation is required each time a report is opened.</p>
      <div className="table-wrap"><table aria-label="Partial report catalog"><thead><tr><th>Case</th><th>Base → head</th><th>Status</th><th>Report</th></tr></thead><tbody>
        {catalog.items.map(row=><tr key={row.case_id}><td>{row.case_id}</td><td>{row.scope?short(row.scope.base_commit)+' → '+short(row.scope.head_commit):'Scope unavailable'}</td><td>{row.status}</td><td>
          {row.scope?<button className="secondary" onClick={()=>{setLoaded(null);setTarget(null);setSelection({...row})}} aria-label={'Open partial report '+row.case_id}>Open report</button>:<span>Unavailable; retained in total</span>}
        </td></tr>)}
      </tbody></table></div>
      <div className="pagination"><button className="secondary" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-10))}>Previous reports</button><button className="secondary" disabled={catalog.next_offset===null} onClick={()=>setOffset(catalog.next_offset)}>Next reports</button></div>
    </>}
    {selection&&!loaded&&!error&&<p role="status">Revalidating report and source evidence…</p>}
    {report&&<article aria-label="Selected partial report">
      <div className="section-head"><h2>Review: {selection.case_id}</h2><div className="report-actions">{['json','html'].map(format=><button className="secondary" key={format} disabled={exporting} onClick={()=>download(format)}>Download partial report {format.toUpperCase()}</button>)}</div></div>
      <p>Source revalidation: <strong>{loaded.validation.source_revalidation}</strong>. Source hashes verify identity, not semantic correctness.</p>
      <dl className="partial-scope"><dt>Report ID</dt><dd>{report.report_id}</dd><dt>Repository ID</dt><dd>{report.scope.repository}</dd><dt>Base commit</dt><dd>{report.scope.base_commit}</dd><dt>Head commit</dt><dd>{report.scope.head_commit}</dd></dl>
      <section aria-label="Guided partial report explanation">
        <h3>Explain this partial report</h3><p>Choose a recorded topic. Answers quote verified report fields; no model or independent semantic review is used.</p>
        <label>Report topic<select aria-label="Partial report explanation topic" value={intent} onChange={e=>setIntent(e.target.value)}>{['scope','changes','unknowns','graph','evidence','limitations'].map(topic=><option key={topic} value={topic}>{topic}</option>)}</select></label>
        <button className="secondary" onClick={()=>setQuestion({report_id:report.report_id,intent})}>Explain selected topic</button>
        {question?.report_id===report.report_id&&!answer&&<p role="status">Revalidating report for explanation…</p>}
        {answer&&<div aria-label="Partial report explanation"><h4>Recorded topic: {answer.intent}</h4><p>{answer.answer}</p><p>Report: {answer.report_id} · semantic support: {answer.semantic_support} · accuracy: {answer.quality_target}</p>{answer.claims.map(claim=><details key={claim.claim_id}><summary>{claim.json_pointer} · {claim.support}</summary><pre>{JSON.stringify(claim.value,null,2)}</pre></details>)}<details><summary>Explanation validation and provenance</summary><pre>{JSON.stringify(answer,null,2)}</pre></details></div>}
      </section>
      <h3>Observed changes and uncertainty</h3>
      <p>{report.observed_outcomes.artifacts.DIFFERENT_EXTRACTED_CONTENT||0} changed extracted contents · <strong>{report.observed_outcomes.artifacts.UNKNOWN||0} UNKNOWN artifact outcomes</strong> · {report.denominators.artifact_side_slots} artifact side slots.</p>
      <p>Findings: {report.findings.length}. Reviewed obligation registry: {report.obligation_assessment.reviewed_registry_supplied?'supplied':'not supplied'}. No conclusion about missing tests follows from an empty findings list.</p>
      <details><summary>Unknown artifact outcomes ({report.unknown_artifact_observations.length})</summary><ul>{report.unknown_artifact_observations.map(row=><li key={row.artifact_id}>{row.file}: {row.uncertainty.join(', ')} — UNKNOWN</li>)}</ul></details>
      <details><summary>Coverage, denominators and unavailable source references</summary><pre>{JSON.stringify({coverage:report.coverage,denominators:report.denominators,source_unknowns:report.source_unknowns},null,2)}</pre></details>
      <h3>Source evidence</h3>
      <ul className="partial-evidence">{report.evidence.map((e,i)=><li key={e.evidence_id+':'+i}><span>{e.file} · {short(e.commit_id)} · lines {e.start_line}–{e.end_line}</span><button className="secondary" onClick={()=>inspect(e.commit_id,e.artifact_id,e.start_line)}>Inspect source {i+1}</button></li>)}</ul>
      {Object.entries(report.roles).map(([name,role])=>{
        const graph=role.graph;
        if(!graph)return <p key={name}>{name} graph: unavailable; no artifacts selected. Absence is not a negative link.</p>;
        const d=graph.denominators;
        return <details key={name} className="partial-graph"><summary>{name} graph candidates ({d.source_verified_edges} source-verified on saved page)</summary>
          <p>Revision: {role.commit_id}</p><p>{d.page_candidate_edges} examined of {d.incident_candidate_edges} incident candidates; {d.withheld_edges} withheld; {d.incident_candidate_edges-d.page_candidate_edges} outside this saved page. These are bounded candidates, not proven impact or complete graph coverage.</p>
          <div className="table-wrap"><table aria-label={name+' graph candidates'}><thead><tr><th>Relation candidate</th><th>Source</th><th>Target</th></tr></thead><tbody>{graph.edges.map(edge=><tr key={edge.projection_edge_id}><td>{edge.source_edge.relation_type}<small>{edge.classification}</small></td>{['source_artifact','target_artifact'].map(key=><td key={key}><button className="secondary" aria-label={'Inspect '+name+' '+key+' '+edge.projection_edge_id} onClick={()=>inspect(role.commit_id,edge.source_edge[key])}>{short(edge.source_edge[key])}</button></td>)}</tr>)}</tbody></table></div>
          <details><summary>Graph receipts and withheld candidates</summary><pre>{JSON.stringify(graph,null,2)}</pre></details>
        </details>;
      })}
      <details><summary>Full report and verification provenance</summary><pre>{JSON.stringify(loaded,null,2)}</pre></details>
    </article>}
    {target&&<section ref={sourceView} className="partial-source" aria-label="Verified source viewer">
      <div className="section-head"><h2>Source inspection</h2><button className="secondary" onClick={()=>{setTarget(null);setSource(null)}}>Close source</button></div>
      {sourceError?<p role="alert" className="error">{sourceError}</p>:!source?<p role="status">Revalidating exact source…</p>:<>
        <p>{source.evidence[0].file} · revision {source.scope.commit_id}</p>
        <p>Lines {source.evidence[0].start_line}–{source.evidence[0].end_line}. Semantic support: {source.semantic_support}; consistency: {source.consistency}.</p>
        <form onSubmit={e=>{e.preventDefault();inspect(target.commit_id,target.artifact_id,Number(line))}}><label>Start line<input aria-label="Source start line" type="number" min="1" required value={line} onChange={e=>setLine(e.target.value)}/></label><button>Inspect lines</button></form>
        <pre aria-label="Verified source excerpt">{source.evidence[0].quote.split('\n').map((s,i)=>`${source.evidence[0].start_line+i}: ${s}`).join('\n')}</pre>
        <details><summary>Source receipts and uncertainty</summary><pre>{JSON.stringify(source,null,2)}</pre></details>
      </>}
    </section>}
  </section>;
}
