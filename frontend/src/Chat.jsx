import React,{useEffect,useState} from 'react';
import './chat.css';

export default function Chat({api}){
 const[open,setOpen]=useState(false),[repositories,setRepositories]=useState([]),[commits,setCommits]=useState([]);
 const[repository,setRepository]=useState(''),[commit,setCommit]=useState(''),[model,setModel]=useState('none');
 const[ollamaModel,setOllamaModel]=useState('qwen3:8b'),[messages,setMessages]=useState([]),[question,setQuestion]=useState('');
 const[loading,setLoading]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;Promise.all([api('repositories?limit=500'),api('commits?limit=500')]).then(([r,c])=>{
  if(active){setRepositories(r.items||[]);setCommits(c.items||[]);if(r.items?.length)setRepository(r.items[0].repository)}
 }).catch(e=>active&&setError(e.message));return()=>{active=false}},[api]);
 useEffect(()=>{let available=commits.filter(item=>item.repository===repository);if(!available.some(item=>item.commit_id===commit))setCommit(available[0]?.commit_id||'')},[repository,commits,commit]);
 useEffect(()=>{setMessages([]);setError('')},[repository,commit]);
 async function send(event){
  event.preventDefault();let text=question.trim();if(!text||!repository||!commit||loading)return;
  const history=messages.slice(-6).map(item=>({role:item.role,content:item.role==='user'?item.content:item.result.answer}));
  setMessages(items=>[...items,{role:'user',content:text}]);setQuestion('');setLoading(true);setError('');
  try{let result=await api('chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({repository,commit_id:commit,question:text,history,model,ollama_model:model==='ollama'?ollamaModel:null})});setMessages(items=>[...items,{role:'assistant',result}])}
  catch(e){setError(e.message)}finally{setLoading(false)}
 }
 return <div className="vigilant-chat">
  {open&&<section className="chat-panel" role="dialog" aria-label="VIGILANT project chat">
   <header className="chat-header"><div><strong>VIGILANT Chat</strong><small>Repository evidence assistant</small></div><button type="button" aria-label="Close chat" onClick={()=>setOpen(false)}>×</button></header>
   <div className="chat-scope">
    <label>Repository<select aria-label="Chat repository" value={repository} onChange={e=>setRepository(e.target.value)}><option value="">Select repository</option>{repositories.map(item=><option key={item.repository} value={item.repository}>{item.name||item.repository}</option>)}</select></label>
    <label>Snapshot<select aria-label="Chat snapshot" value={commit} onChange={e=>setCommit(e.target.value)}><option value="">Select snapshot</option>{commits.filter(item=>item.repository===repository).map(item=><option key={item.commit_id} value={item.commit_id}>{item.commit_id.slice(0,12)}</option>)}</select></label>
    <label>Reasoning<select aria-label="Chat reasoning provider" value={model} onChange={e=>setModel(e.target.value)}><option value="none">Evidence only</option><option value="ollama">Local Ollama</option><option value="local">Local Transformers</option><option value="omniroute">OmniRoute</option></select></label>
    {model==='ollama'&&<label>Model<select aria-label="Chat Ollama model" value={ollamaModel} onChange={e=>setOllamaModel(e.target.value)}><option>qwen3:8b</option><option>qwen2.5-coder:14b</option><option>qwen3:14b</option></select></label>}
   </div>
   <div className="chat-messages" aria-live="polite">
    {!messages.length&&<p className="chat-empty">Ask what changed, why a finding was raised, or which evidence and tests deserve review.</p>}
    {messages.map((item,index)=><article className={'chat-message '+item.role} key={index}>
     {item.role==='user'?<p>{item.content}</p>:<>
      <strong>{item.result.decision.decision}</strong><p>{item.result.answer}</p>
      {item.result.validation_error&&<p className="chat-warning">The model response failed validation; treat this answer as uncertain.</p>}
      {item.result.citations.length>0&&<div className="chat-citations"><b>Model citations</b>{item.result.citations.map(source=><details key={source.evidence_id}><summary>{source.file}:{source.start_line}-{source.end_line}</summary><pre>{source.quote}</pre></details>)}</div>}
      {item.result.decision.decision==='UNCERTAIN'&&item.result.retrieved_evidence.length>0&&<div className="chat-citations"><b>Retrieved evidence, not claimed as support</b>{item.result.retrieved_evidence.map(source=><details key={source.evidence_id}><summary>{source.file}:{source.start_line}-{source.end_line}</summary><pre>{source.quote}</pre></details>)}</div>}
      <small className="chat-caveat">{item.result.confidence_note} Semantic support is not independently verified.</small>
     </>}
    </article>)}
    {loading&&<p className="chat-loading">Checking repository evidence…</p>}
   </div>
   {error&&<p className="chat-error" role="alert">{error}</p>}
   <form className="chat-form" onSubmit={send}><label className="visually-hidden" htmlFor="vigilant-chat-question">Question</label><textarea id="vigilant-chat-question" value={question} maxLength={1200} rows={3} placeholder="Ask about this snapshot…" onChange={e=>setQuestion(e.target.value)} disabled={!commit||loading}/><button type="submit" aria-label="Send question" disabled={!commit||loading||!question.trim()}>Send</button></form>
   <footer>Session-only conversation · no repository changes are made</footer>
  </section>}
  <button className="chat-launcher" type="button" onClick={()=>setOpen(value=>!value)} aria-expanded={open} aria-label={open?'Close VIGILANT chat':'Open VIGILANT chat'}>Chat</button>
 </div>
}