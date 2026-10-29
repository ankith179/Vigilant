import React,{useEffect,useMemo,useRef,useState} from 'react';

export default function InvestigationTools({api,repository,commit,commits=[]}){
 const [result,setResult]=useState(null),[query,setQuery]=useState(''),[artifact,setArtifact]=useState('');
 const [loading,setLoading]=useState(false),[error,setError]=useState(''),[base,setBase]=useState(''),[pathsText,setPathsText]=useState(''),[source,setSource]=useState(null);
 const key=JSON.stringify([repository,commit,base,pathsText]),current=useRef(key);current.current=key;
 const revisions=useMemo(()=>commits.filter(x=>x.repository===repository),[commits,repository]);
 const bases=revisions.filter(x=>x.commit_id!==commit),paths=pathsText.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 const validPaths=paths.length>0&&paths.length<=16&&paths.every(x=>x.length<=1024);
 useEffect(()=>{setResult(null);setSource(null);setError('');setLoading(false)},[repository,commit,base,pathsText]);
 useEffect(()=>{if(!bases.some(x=>x.commit_id===base))setBase(bases[0]?.commit_id||'')},[repository,commit,revisions,base]);
 async function run(name,extra={},scope=key){
  setResult(null);setSource(null);setError('');setLoading(true);
  try{const row=await api('investigation/call',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,arguments:{repository,commit_id:commit,...extra}})});if(current.current===scope)setResult(row)}
  catch(e){if(current.current===scope)setError(e.message)}finally{if(current.current===scope)setLoading(false)}
 }
 const disabled=loading||!repository||!commit,lineageDisabled=disabled||!base||base===commit||!validPaths;
 const lineage=result?.tool==='inspect_lineage'?result:null,record=lineage?.data?.lineage_record,evidence=result?.evidence||[];
 return <section className="content investigation-tools" aria-busy={loading} aria-label="Investigation tools workspace">
  <h2>Repository investigation</h2><p>Explore a pinned revision and inspect source-verified evidence. Semantic support remains subject to review.</p>
  <div className="report-actions"><button disabled={disabled} onClick={()=>run('explore_repository')}>Explore snapshot</button><button disabled={disabled} onClick={()=>run('run_recipe',{recipe:'understand_repository',max_steps:3})}>Understand project</button><button disabled={disabled} onClick={()=>run('list_unknowns')}>Review unknowns</button></div>
  <form onSubmit={e=>{e.preventDefault();run('retrieve_evidence',{query})}}><label>Evidence query<input aria-label="Investigation evidence query" value={query} maxLength={1200} onChange={e=>setQuery(e.target.value)} required/></label><button disabled={disabled||!query.trim()}>Find source evidence</button></form>
  <form onSubmit={e=>{e.preventDefault();run('run_recipe',{recipe:'explain_dependencies',artifact_id:artifact,max_steps:3})}}><label>Artifact identity<input aria-label="Investigation artifact identity" value={artifact} maxLength={128} onChange={e=>setArtifact(e.target.value)} required/></label><button disabled={disabled||!artifact.trim()}>Explain dependency paths</button></form>
  <section className="lineage-inspection" aria-label="Paired revision lineage inspection"><h3>Inspect artifact lineage</h3>
   <p>Compare selected files at two indexed revisions. Candidates remain unreviewed; logical continuity is unknown and semantic support is not established.</p>
   <label>Base revision<select aria-label="Lineage base revision" value={base} onChange={e=>setBase(e.target.value)}><option value="">Select base revision</option>{bases.map(x=><option key={x.commit_id} value={x.commit_id}>{x.commit_id} · {x.subject}</option>)}</select></label>
   <label>Repository-relative paths, one per line (1–16)<textarea aria-label="Lineage file paths" rows="4" maxLength="16400" value={pathsText} onChange={e=>setPathsText(e.target.value)} placeholder={'src/old.py\nsrc/new.py'}/></label>
   <button disabled={lineageDisabled} onClick={()=>run('inspect_lineage',{base_commit:base,paths})}>Inspect paired revisions</button>
   {pathsText&&!validPaths&&<p role="status">Enter 1–16 paths, each no longer than 1,024 characters.</p>}
  </section>
  {error&&<p role="alert" className="error">{error}</p>}{loading&&<p role="status">Verifying pinned repository evidence…</p>}
  {lineage&&record&&<section aria-label="Lineage observation result"><h3>Lineage observations</h3>
   <p>Base {record.scope.base.slice(0,12)} → head {record.scope.head.slice(0,12)} · UNREVIEWED · logical continuity UNKNOWN · semantic equivalence NOT_ESTABLISHED.</p>
   <p>Relationship transfer allowed: false. Source verification establishes identity, not semantic support.</p>
   <p>Selected files: {record.denominators.selected_files} · candidate pairs: {record.denominators.candidate_pairs} · unknown observations: {record.denominators.unknown_observations} · unavailable file sides: {record.denominators.unavailable_file_sides}</p>
   <div className="table-wrap"><table aria-label="Paired canonical source excerpts"><thead><tr><th>Base source</th><th>Head source</th></tr></thead><tbody>{paths.map(path=>{const left=evidence.find(x=>x.commit===record.scope.base&&x.file===path),right=evidence.find(x=>x.commit===record.scope.head&&x.file===path);return <tr key={path}><td><b>{path}</b>{left?<><small>{left.commit} · lines {left.start_line}–{left.end_line}</small><pre>{left.quote}</pre><small>Canonical artifact {left.artifact_id}</small></>:<p>Unavailable at base revision; retained as unknown.</p>}</td><td><b>{path}</b>{right?<><small>{right.commit} · lines {right.start_line}–{right.end_line}</small><pre>{right.quote}</pre><small>Canonical artifact {right.artifact_id}</small></>:<p>Unavailable at head revision; retained as unknown.</p>}</td></tr>})}</tbody></table></div>
   {record.observations.map(x=><details key={x.observation_id}><summary>{x.status} · {x.base?.path||'unknown'} → {x.head?.path||'unknown'}</summary><p>{x.reason} · {x.lifecycle} · continuity {x.logical_continuity} · semantics {x.semantic_equivalence} · transfer {String(x.relationship_transfer_allowed)}</p><pre>{JSON.stringify(x,null,2)}</pre></details>)}
   {record.limitations.map(x=><p className="muted" key={x}>{x}</p>)}
  </section>}
  {result&&<><p><b>{result.tool}</b> · {result.source_verification} · semantic support: {result.semantic_support}</p><small>Retained result: {result.result_id}</small>
   {!lineage&&result.data.items?.some(item=>item.artifact_id)&&<div className="table-wrap"><table><thead><tr><th>Artifact</th><th>Kind</th><th>Symbol</th><th>Action</th></tr></thead><tbody>{result.data.items.map(item=><tr key={item.artifact_id}><td>{item.file_path}</td><td>{item.artifact_type}</td><td>{item.symbol}</td><td><button onClick={()=>run('inspect_artifact',{artifact_id:item.artifact_id})} disabled={disabled}>Inspect source</button></td></tr>)}</tbody></table></div>}
  {!lineage&&evidence.map(e=><details key={e.evidence_id}><summary>{e.file}:{e.start_line}–{e.end_line} · {e.commit.slice(0,12)}</summary><pre>{e.quote}</pre><button disabled={loading} onClick={()=>api('artifacts/'+e.artifact_id+'?'+new URLSearchParams({repository,commit_id:e.commit})).then(setSource).catch(err=>setError(err.message))}>Open exact artifact</button></details>)}
  {source&&<details open><summary>{source.file_path} · {source.commit_id.slice(0,12)}</summary><pre>{source.content}</pre></details>}
  {lineage?.unknowns?.map(x=><p key={x.unknown_id}><b>{x.code}</b> — {x.question}</p>)}
   <details><summary>Structured result and provenance</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
   <button className="secondary" disabled={disabled} onClick={()=>run('inspect_retained_result',{result_id:result.result_id})}>Reverify retained result</button>
  </>}
  <p className="muted">Repository code is not executed. No model inference is made by this workspace.</p>
 </section>
}
