from ingestion.models import digest
from retrieval.index import Index,RETRIEVAL_POLICY
from knowledge_graph.graph import impact
import re
from collections import Counter,OrderedDict
from threading import Lock
_INDEX_CACHE=OrderedDict()
_INDEX_LOCK=Lock()

def lexical_index(candidates):
 key=digest(RETRIEVAL_POLICY,[(a["artifact_id"],a["commit_id"],a["content_hash"]) for a in candidates])
 with _INDEX_LOCK:
  if key in _INDEX_CACHE:
   _INDEX_CACHE.move_to_end(key);return _INDEX_CACHE[key]
 index=Index(candidates)
 with _INDEX_LOCK:
  _INDEX_CACHE[key]=index
  while len(_INDEX_CACHE)>2:_INDEX_CACHE.popitem(last=False)
 return index


def evidence(a,method='source',score=1.,max_lines=None,focus_line=None):
 lines=a.content.splitlines();offset=0
 if max_lines:
  if focus_line is not None:offset=max(0,min(len(lines)-max_lines,focus_line-a.start_line-max_lines//2))
  lines=lines[offset:offset+max_lines]
 start=a.start_line+offset;quote='\n'.join(lines);end=start+max(1,len(lines))-1
 return {'evidence_id':digest(a.artifact_id,a.commit_id,str(start),str(end),quote),'artifact_id':a.artifact_id,'repository':a.repository,'project_id':a.project_id,'file':a.file_path,'start_line':start,'end_line':end,'commit':a.commit_id,'commit_id':a.commit_id,'content_hash':a.content_hash,'quote':quote,'score':float(score),'retrieval_method':method,'revision':a.commit_id,'path':a.file_path,'extraction_method':method}

def paired_versions(changes,before,after,max_pairs=4):
 """Choose bounded before/after windows around actual Git changes, never gold labels."""
 old={a.artifact_id:a for a in before};new={a.artifact_id:a for a in after}
 priority={'requirement':0,'source_file':1,'api':2,'test_method':3}
 rows=sorted(changes['artifacts'],key=lambda c:(priority.get(c['artifact_type'],4),c['file'],c['artifact_id']))
 result=[]
 for change in rows[:max_pairs]:
  pair=digest(change['artifact_id'],change.get('new_artifact_id'))
  for version,by,aid in [('base',old,change['artifact_id']),('head',new,change.get('new_artifact_id') or change['artifact_id'])]:
   a=by.get(aid)
   if a is None:continue
   side='old' if version=='base' else 'new'
   lines=[h[side+'_start'] for f in changes.get('files',[]) if f[side+'_path']==a.file_path for h in f.get('hunks',[]) if a.start_line<=h[side+'_start']<=a.end_line]
   result.append({**evidence(a,'changed-'+version,max_lines=30,focus_line=lines[0] if lines else None),'pair_id':pair})
 return result
def verify(items,artifacts):
 by={(a.artifact_id,a.commit_id):a for a in artifacts};errors=[]
 for e in items:
  a=by.get((e['artifact_id'],e['commit']))
  if a is None:errors.append('Missing version '+e['evidence_id']);continue
  if (e.get('repository')!=a.repository or e.get('project_id')!=a.project_id or e.get('file')!=a.file_path or e.get('commit_id',e['commit'])!=a.commit_id or e['end_line']<e['start_line'] or e['evidence_id']!=digest(a.artifact_id,a.commit_id,str(e['start_line']),str(e['end_line']),e['quote'])):errors.append('Identity/scope mismatch '+e['evidence_id'])
  start=e['start_line']-a.start_line;end=e['end_line']-a.start_line+1;lines=a.content.splitlines()
  if start<0 or end>max(1,len(lines)) or '\n'.join(lines[start:end])!=e['quote'] or e['content_hash']!=a.content_hash:errors.append('Quote/range/hash mismatch '+e['evidence_id'])
 return errors


def verify_git(items,artifacts,repo):
 """Re-read immutable Git source independently of the stored artifact."""
 from ingestion.git import git,revision
 errors=verify(items,artifacts);cache={};by={(a.artifact_id,a.commit_id):a for a in artifacts};checked=set()
 for e in items:
  key=e['commit'],e['file']
  try:
   if key not in cache:
    if revision(repo,e['commit'])!=e['commit']:raise ValueError('Expected immutable commit SHA')
    raw=git(repo,'show',e['commit']+':'+e['file'],binary=True)
    try:text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:text=raw.decode('cp1252',errors='replace')
    cache[key]=text.splitlines()
   lines=cache[key]
   a=by.get((e['artifact_id'],e['commit']))
   if a and (a.artifact_id,a.commit_id) not in checked:
    checked.add((a.artifact_id,a.commit_id))
    if a.content.splitlines()!=lines[a.start_line-1:a.end_line]:errors.append('Git blob artifact content mismatch '+e['evidence_id'])
   if e['start_line']<1 or e['end_line']>max(1,len(lines)) or '\n'.join(lines[e['start_line']-1:e['end_line']])!=e['quote']:errors.append('Git blob quote mismatch '+e['evidence_id'])
  except Exception as exc:errors.append('Git blob unavailable '+e['evidence_id']+': '+type(exc).__name__)
 return errors


def balanced_change_context(changes,before,after,edges=(),max_lines=30):
 """Separate development retrieval arm: changed hunks plus role-balanced candidates.

 Uses source changes and structural edges, never expected labels or oracle targets.
 Missing roles remain explicit; candidates are not evidence of semantic sufficiency.
 """
 old={a.artifact_id:a for a in before}
 changed_files={f.get('new_path') or f.get('old_path') for f in changes['files']}
 seeds={c[k] for c in changes['artifacts'] for k in ('artifact_id','new_artifact_id') if c.get(k)}
 terms=Counter(re.findall(r'[A-Za-z_][A-Za-z_0-9]{2,}', ' '.join(
  line[1:] for f in changes['files'] for line in f.get('patch','').splitlines()
  if line.startswith(('+','-')) and not line.startswith(('+++','---')))))
 for word in ('def','return','assert','self','None','True','False','import','from','const','the','and','with','include'):
  terms.pop(word,None)
 neighbors=set()
 for edge in edges:
  if edge.get('relation_type') not in {'CALLS','TESTS','CONSUMES_API','EXPOSES_API','VALIDATES','IMPLEMENTS'}:continue
  if 'similar' in edge.get('method','').lower():continue
  s,t=edge['source_artifact'],edge['target_artifact']
  if s in seeds:neighbors.add(t)
  if t in seeds:neighbors.add(s)
 def role(a):
  path=a.file_path.lower()
  if a.artifact_type=='requirement':return 'requirement'
  if a.artifact_type=='test_method' or re.search(r'(^|/)(tests?(/|_)|test_)',path):return 'test'
  if a.artifact_type=='api_caller':return 'caller'
  if a.artifact_type=='api':return 'implementation'
  if a.artifact_type in {'function','method','api','source_file'}:
   return 'implementation' if a.file_path in changed_files else 'caller'
  return None
 def line_score(line):
  return sum(min(n,3) for token,n in terms.items() if token.lower() in line.lower())
 def focus(a):
  lines=a.content.splitlines()
  return a.start_line+max(range(len(lines)),key=lambda i:line_score(lines[i])) if lines else a.start_line
 def rank(a):
  return (a.artifact_id in neighbors, max((line_score(s) for s in a.content.splitlines()),default=0),
          bool(a.symbol), -len(a.content),a.artifact_id)
 result=[];seen=set();coverage={r:0 for r in ('requirement','implementation','caller','test')}
 def add(a,kind,pair,center=None):
  e=evidence(a,'changed-context-'+kind,max_lines=max_lines,focus_line=center or focus(a))
  key=(e['file'],e['commit'],e['start_line'],e['end_line'])
  if key not in seen:
   seen.add(key);result.append({**e,'pair_id':pair,'context_role':kind})
   if kind in coverage:coverage[kind]+=1
 # One pair per changed hunk avoids filling the budget with overlapping artifact types.
 hunks=0
 for f in changes['files']:
  for h in f.get('hunks',[]):
   if hunks>=4:break
   pair=digest('balanced-hunk',f.get('old_path'),f.get('new_path'),str(h));hunks+=1
   for side,artifacts in [('old',before),('new',after)]:
    matches=[a for a in artifacts if a.file_path==f.get(side+'_path') and not a.symbol]
    if matches:
     a=matches[0];kind=role(a) or 'changed';add(a,kind,pair,h[side+'_start'])
 # Reserve opportunities for every role before selecting any second candidate.
 for kind in coverage:
  candidates=[a for a in after if role(a)==kind and (a.artifact_id in neighbors or rank(a)[1]>0)]
  if kind=='implementation' and not candidates:
   candidates=[a for a in after if role(a)=='caller' and a.artifact_type!='api_caller' and rank(a)[1]>0]
  if kind=='caller':
   used={e['artifact_id'] for e in result}
   candidates=[a for a in candidates if a.artifact_id not in used]
  if not candidates:continue
  a=max(candidates,key=rank);pair=digest('balanced-role',kind,a.artifact_id)
  if a.artifact_id in old:add(old[a.artifact_id],kind,pair)
  add(a,kind,pair)
 errors=verify(result,before+after)
 if errors:raise ValueError(errors)
 return result,{'policy':'balanced-change-context-v2','candidate_role_excerpts':coverage,
                'missing_roles':[r for r,n in coverage.items() if not n],
                'changed_hunks_considered':hunks,'semantic_sufficiency':'UNREVIEWED',
                'limitations':['At most four changed hunks and one additional candidate per role.',
                               'Structural/lexical matches are candidates, not proven relevance or completeness.']}

def retrieve(query,artifacts,graph=None,seeds=(),encoder=None,k=8,max_chars=8000):
 by={a.artifact_id:a for a in artifacts};candidates=[a.model_dump() for a in artifacts if a.content.strip() and a.artifact_type!='configuration']
 if not candidates:return []
 index=Index(candidates,encoder) if encoder else lexical_index(candidates);found={}
 for rank,hit in enumerate(index.search(query,'hybrid' if encoder else 'bm25',k),1):
  if hit['score']>0:found[hit['artifact_id']]={**evidence(by[hit['artifact_id']],hit['retrieval_method'],hit['score'],24),'selection_rank':rank,'selection_arm':'retrieval'}
 if graph is not None:
  for rank,(aid,path) in enumerate(sorted(impact(graph,seeds,2).items(),key=lambda x:(len(x[1]),x[0]))[:k],1):
   if aid in by:found[aid]={**evidence(by[aid],'graph',1/len(path),24),'graph_path':path,'selection_rank':min(rank,found.get(aid,{}).get('selection_rank',rank)),'selection_arm':'graph'}
 for seed in sorted(seeds):
  if seed in by:found[seed]={**evidence(by[seed],'changed-artifact',1.,24),'selection_rank':0,'selection_arm':'changed'}
 result=[]
 for e in sorted(found.values(),key=lambda e:(e['selection_rank'],e['selection_arm'],e['evidence_id'])):
  if sum(len(x['quote']) for x in result)+len(e['quote'])<=max_chars:result.append(e)
 return result
