"""Versioned dependency candidates. Edges are not proof of behavioral impact."""
from collections import defaultdict
import posixpath
import networkx as nx
from ingestion.models import digest


def build_graph(store,artifacts,declared=()):
 g=nx.MultiDiGraph();by={a.artifact_id:a for a in artifacts};names=defaultdict(list);files={a.file_path:a for a in artifacts if not a.symbol};edges={};nodes=[]
 def edge(s,t,relation,method='static',priority=1.,is_declared=False):
  if s==t or s not in by or t not in by:return
  a,b=by[s],by[t];key=digest(s,t,relation,a.commit_id,method,'typed-v2')
  provenance='DECLARED' if is_declared else ('STATICALLY_RESOLVED' if method in {'contains-reverse','client-owner','static','relative-module-path','compiler-usr'} else 'HEURISTIC')
  row={'id':key,'edge_policy':'typed-v2','source_artifact':s,'target_artifact':t,'relation_type':relation,'method':method,'confidence':None,'confidence_calibrated':False,'score':priority,'score_basis':'retrieval-priority-only','is_declared':is_declared,'evidence':[s,t],'repository':a.repository,'project_id':a.project_id,'commit_id':a.commit_id,
       'provenance_type':provenance,'resolution_status':'declared' if is_declared else ('local-syntax-relationship' if provenance=='STATICALLY_RESOLVED' else 'candidate-not-semantically-resolved'),
       'evidence_spans':[{'artifact_id':x.artifact_id,'file':x.file_path,'commit':x.commit_id,'start_line':x.start_line,'end_line':x.end_line,'content_hash':x.content_hash} for x in (a,b)]}
  if method=='compiler-usr':row['resolution_status']='compiler-reference-under-snapshot-context';row['build_configuration_verified']=False
  edges[key]=row;g.add_edge(s,t,key=key,**row)
 routes=defaultdict(list)
 for a in artifacts:
  g.add_node(a.artifact_id,artifact_type=a.artifact_type,file_path=a.file_path)
  nodes.append((digest(a.artifact_id,a.commit_id),{'artifact_id':a.artifact_id,'repository':a.repository,'project_id':a.project_id,'commit_id':a.commit_id,'artifact_type':a.artifact_type,'file':a.file_path,'symbol':a.symbol}))
  if a.symbol:
   names[a.symbol.split('(')[0].split('.')[-1]].append(a);edge(a.artifact_id,a.metadata['parent_id'],'CONTAINED_IN','contains-reverse')
  if a.artifact_type=='api':
   routes[(a.metadata.get('method'),a.metadata.get('route'))].append(a)
   if a.metadata.get('handler_id'):edge(a.metadata['handler_id'],a.artifact_id,'EXPOSES_API')
 compiler_symbols=defaultdict(list)
 for a in artifacts:
  if a.metadata.get('compiler_usr'):compiler_symbols[a.metadata['compiler_usr']].append(a)
 for a in artifacts:
  if 'compiler_calls' in a.metadata:
   if a.metadata.get('compiler_parse_clean'):
    for call in a.metadata['compiler_calls']:
     targets=compiler_symbols.get(call['target_usr'],[])
     definitions=[t for t in targets if t.metadata.get('is_definition')]
     targets=definitions or targets
     if len(targets)==1:edge(a.artifact_id,targets[0].artifact_id,'TESTS' if a.artifact_type=='test_method' else 'CALLS','compiler-usr')
   continue
  for call in a.metadata.get('calls',[]) if a.artifact_type not in {'class','source_file'} else []:
   candidates=[x for x in names.get(call.split('.')[-1],[]) if x.artifact_id!=a.artifact_id and x.file_path==a.file_path and x.artifact_type in {'function','method','test_method','frontend'}]
   scope=a.symbol.split('(')[0].rsplit('.',1)[0] if '.' in a.symbol.split('(')[0] else ''
   if '.' in call:
    if call.rsplit('.',1)[0] not in {'self','this'} or not scope:continue
    candidates=[x for x in candidates if x.symbol.split('(')[0].rsplit('.',1)[0]==scope]
   else:
    candidates=[x for x in candidates if (x.symbol.split('(')[0].rsplit('.',1)[0] if '.' in x.symbol.split('(')[0] else '') in {'',scope}]
   if len(candidates)==1:edge(a.artifact_id,candidates[0].artifact_id,'TESTS' if a.artifact_type=='test_method' else 'CALLS','same-file-syntax',.85)
  if a.artifact_type=='api_caller':
   targets=routes.get((a.metadata.get('method'),a.metadata.get('route')),[])
   if len(targets)==1:edge(a.artifact_id,targets[0].artifact_id,'CONSUMES_API','exact-literal-contract')
   if a.metadata.get('owner_id'):edge(a.metadata['owner_id'],a.artifact_id,'DEPENDS_ON','client-owner')
  if not a.symbol:
   for imp in a.metadata.get('imports',[]):
    relative=False
    if a.file_path.endswith(('.js','.jsx','.ts','.tsx')):
     if not imp.startswith('.'):continue
     module=posixpath.normpath(posixpath.join(posixpath.dirname(a.file_path),imp))
     if module.startswith(('../','/')):continue
     paths={module,*[module+e for e in ('.js','.jsx','.ts','.tsx')],*[module+'/index'+e for e in ('.js','.jsx','.ts','.tsx')]}
     targets=[b for p,b in files.items() if p in paths];relative=True
    else:
     module=imp.replace('.','/').lstrip('/')
     if not module:continue
     paths=[module+'.py',module+'/__init__.py',module+'.java']
     if imp.startswith('.'):
      root=posixpath.dirname(a.file_path)
      for _ in range(len(imp)-len(imp.lstrip('.'))-1):root=posixpath.dirname(root)
      paths=[posixpath.join(root,p) for p in paths];relative=True
     targets=[b for p,b in files.items() if any(p==m or (not relative and p.endswith('/'+m)) for m in paths)]
    if len(targets)==1:edge(a.artifact_id,targets[0].artifact_id,'IMPORTS','relative-module-path' if relative else 'module-path',.9)
 for row in declared:
  s,t=row['source_artifact'],row['target_artifact'];relation=row['relation_type']
  if relation in {'IMPLEMENTS','VALIDATES'} and s in by and by[s].artifact_type=='requirement':s,t=t,s
  if relation=='TESTS' and t in by and s in by and by[t].artifact_type in {'test','test_method'} and by[s].artifact_type not in {'test','test_method'}:s,t=t,s
  edge(s,t,relation,row.get('method','declared-trace'),row.get('confidence') or 1.,True)
 store.put_many('graph_nodes',nodes)
 for table in ('graph_edges','trace_links'):store.put_many(table,edges.items())
 return g,list(edges.values())


def impact(g,seeds,depth=2,containment=False):
 filtered=nx.DiGraph();filtered.add_nodes_from(g.nodes)
 for s,t,e in g.edges(data=True):
  if e.get('relation_type') in {'CALLS','TESTS','IMPORTS','DEPENDS_ON','IMPLEMENTS','VALIDATES','CONSUMES_API','EXPOSES_API'} or (containment and e.get('relation_type')=='CONTAINED_IN'):filtered.add_edge(t,s)
 out={};seeds=set(seeds)
 for seed in sorted(seeds):
  if seed not in filtered:continue
  for target,path in nx.single_source_shortest_path(filtered,seed,cutoff=depth).items():
   if target not in seeds and (target not in out or len(path)<len(out[target])):out[target]=path
 return out


def impact_snapshots(snapshots,seeds,depth=2):
 """Traverse each revision independently; never splice base and head edges."""
 candidates={}
 for role,g in snapshots:
  for target,path in impact(g,seeds,depth).items():
   steps=[]
   for dependency,dependent in zip(path,path[1:]):
    options=[dict(e) for e in g.get_edge_data(dependent,dependency,default={}).values()
             if e.get('relation_type') in {'CALLS','TESTS','IMPORTS','DEPENDS_ON','IMPLEMENTS','VALIDATES','CONSUMES_API','EXPOSES_API'}]
    options.sort(key=lambda e:(e.get('relation_type',''),e.get('id','')))
    steps.append({'from_artifact':dependency,'to_artifact':dependent,'direction':'reverse-dependency',
                  'edge_options':options,'ambiguous':len(options)>1})
   detail={'revision_role':role,'path':path,'steps':steps,'causal_impact_verified':False}
   item=candidates.setdefault(target,{'artifact_id':target,'path':path,'path_details':[]})
   item['path_details'].append(detail)
   if len(path)<len(item['path']):item['path']=path
 return [candidates[key] for key in sorted(candidates)]
