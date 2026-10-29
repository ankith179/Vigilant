from ingestion.models import digest


def check(changes,before,after,edges,file_changes=()):
 old={a.artifact_id:a for a in before};new={a.artifact_id:a for a in after};changed={x['artifact_id']:x for x in changes if not x.get('syntax_unchanged')};out=[];emitted=set()
 def emit(status,rule,ids,reason):
  key=digest(rule,*sorted(ids))
  if key in emitted:return
  emitted.add(key);out.append({'finding_id':key,'status':status,'rule':rule,'affected_artifacts':sorted(set(ids)),'reason':reason,'confidence':None,'confidence_calibrated':False,'method':'deterministic-rule','evidence_ids':[],'semantic_entailment_verified':False,'assessment_basis':'declared-trace-and-verified-deletion' if status=='BROKEN_TRACE' else 'review-candidate'})
 observed_paths={a.file_path for a in after if not a.symbol};deleted_paths={f['old_path'] for f in file_changes if f['status']=='D'}
 tested={e['target_artifact'] for e in edges if e['relation_type']=='TESTS' and e['source_artifact'] in new}
 contracts={(a.metadata.get('method'),a.metadata.get('route')) for a in after if a.artifact_type=='api'}
 parse_errors=any(a.metadata.get('parse_error') or a.metadata.get('parse_has_error') for a in after)
 for e in edges:
  s,t=e['source_artifact'],e['target_artifact'];r=e['relation_type']
  if r not in {'IMPLEMENTS','VALIDATES','TESTS','CONSUMES_API','EXPOSES_API','CALLS'}:continue
  if s in old and t in old and (s not in new or t not in new) and (s in new or t in new):
   if s in new and t not in new and r in {'CALLS','TESTS'}:
    leaf=old[t].symbol.split('(')[0].split('.')[-1]
    if leaf not in {c.split('.')[-1] for c in new[s].metadata.get('calls',[])}:continue
   if s in new and t not in new and r=='CONSUMES_API' and any(new[s].metadata.get(k)!=old[s].metadata.get(k) for k in ('method','route')):continue
   missing=s if s not in new else t;path=old[missing].file_path
   deleted=changed.get(missing,{}).get('kind')=='deleted' and (path in observed_paths or path in deleted_paths)
   declared=e.get('is_declared') or e.get('provenance_type')=='DECLARED' or e.get('method')=='declared-trace'
   status='BROKEN_TRACE' if declared and deleted and not parse_errors else 'POTENTIAL_INCONSISTENCY'
   emit(status,'deleted-endpoint',[s,t],f'{r} endpoint absent from the parsed head snapshot. '+('Explicit link and source deletion verified.' if status=='BROKEN_TRACE' else 'Resolution, coverage or replacement requires review; no broken trace established.'))
  if r=='TESTS' and t in changed and t in new and s not in changed and s in new:emit('POTENTIAL_INCONSISTENCY','implementation-changed-test-unchanged',[s,t],'Implementation changed; a statically associated test did not. Review needed, not a proven defect.')
  if r in {'IMPLEMENTS','VALIDATES'} and t in changed and s not in changed and s in new:emit('POTENTIAL_INCONSISTENCY','requirement-changed-linked-artifact-unchanged',[s,t],'A changed requirement retains a link to an unchanged artifact.')
  if r=='TESTS' and s not in new and t in new and t not in tested:emit('POTENTIAL_INCONSISTENCY','last-known-test-deleted',[s,t],'Last associated test is absent. Testing obligations and complete coverage are unverified; MISSING_TEST is not established.')
  if r=='CONSUMES_API' and s in new and t not in new:
   caller=new[s]
   if (caller.metadata.get('method'),caller.metadata.get('route')) not in contracts:emit('POTENTIAL_INCONSISTENCY','removed-api-consumer-remains',[s,t],'Previously matched literal API disappeared; consumer retains an unmatched contract. Dynamic routes remain unresolved.')
 if not out:emit('UNCERTAIN','no-decisive-rule',[x['artifact_id'] for x in changes][:20],'Available evidence does not establish consistency or inconsistency.')
 return out
