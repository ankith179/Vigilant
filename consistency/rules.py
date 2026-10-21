from ingestion.models import digest

def check(changes,before,after,edges):
 old={a.artifact_id:a for a in before};new={a.artifact_id:a for a in after};changed={x['artifact_id']:x for x in changes if not x.get('syntax_unchanged')};out=[]
 def emit(status,rule,ids,reason):out.append({'finding_id':digest(rule,*sorted(ids)),'status':status,'rule':rule,'affected_artifacts':sorted(set(ids)),'reason':reason,'confidence':1. if status=='BROKEN_TRACE' else .65,'method':'deterministic-rule','evidence_ids':[]})
 for e in edges:
  s,t=e['source_artifact'],e['target_artifact'];r=e['relation_type']
  if r not in {'IMPLEMENTS','VALIDATES','TESTS','CONSUMES_API','EXPOSES_API','CALLS'}:continue
  if s in old and t in old and (s not in new or t not in new) and (s in new or t in new):emit('BROKEN_TRACE','deleted-endpoint',[s,t],f'Previously evidenced {r} relation lost an endpoint. Revalidate its replacement.')
  if r=='TESTS' and t in changed and s not in changed and s in new:emit('POTENTIAL_INCONSISTENCY','implementation-changed-test-unchanged',[s,t],'Implementation changed; a statically associated test did not. Review needed, not a proven defect.')
  if r in {'IMPLEMENTS','VALIDATES'} and s in changed and t not in changed and t in new:emit('POTENTIAL_INCONSISTENCY','requirement-changed-linked-artifact-unchanged',[s,t],'A changed requirement retains a link to an unchanged artifact.')
  if r=='TESTS' and s not in new and t in new and not any(x['relation_type']=='TESTS' and x['target_artifact']==t and x['source_artifact'] in new for x in edges):emit('MISSING_TEST','last-known-test-deleted',[s,t],'No remaining test in the observed trace graph; coverage may be incomplete.')
  if r=='CONSUMES_API' and s in new and t not in new:
   caller=new[s];matches=[a for a in after if a.artifact_type=='api' and (a.metadata.get('method'),a.metadata.get('route'))==(caller.metadata.get('method'),caller.metadata.get('route'))]
   if not matches:emit('POTENTIAL_INCONSISTENCY','removed-api-consumer-remains',[s,t],'A previously matched literal API disappeared while its consumer retains the old contract. Dynamic routes remain unresolved.')
 if not out:emit('UNCERTAIN','no-decisive-rule',[x['artifact_id'] for x in changes][:20],'Available evidence does not establish consistency or inconsistency.')
 return out
