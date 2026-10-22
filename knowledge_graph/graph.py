"""Structural graph supports retrieval and conservative change propagation."""
from collections import defaultdict
import networkx as nx
from ingestion.models import digest

def build_graph(store,artifacts,declared=()):
 g=nx.MultiDiGraph();by={a.artifact_id:a for a in artifacts};names=defaultdict(list);files={a.file_path:a for a in artifacts if not a.symbol};edges={}
 def edge(s,t,relation,method='static',confidence=1.,is_declared=False):
  if s==t or s not in by or t not in by:return
  a=by[s];key=digest(s,t,relation,a.commit_id,method);row={'id':key,'source_artifact':s,'target_artifact':t,'relation_type':relation,'method':method,'confidence':confidence,'score':confidence,'is_declared':is_declared,'evidence':[s,t],'repository':a.repository,'project_id':a.project_id,'commit_id':a.commit_id};edges[key]=row;g.add_edge(s,t,key=key,**row)
 routes=defaultdict(list)
 for a in artifacts:
  g.add_node(a.artifact_id,artifact_type=a.artifact_type,file_path=a.file_path)
  store.put('graph_nodes',digest(a.artifact_id,a.commit_id),{'artifact_id':a.artifact_id,'repository':a.repository,'project_id':a.project_id,'commit_id':a.commit_id,'artifact_type':a.artifact_type,'file':a.file_path,'symbol':a.symbol})
  if a.symbol:names[a.symbol.split('.')[-1].split('(')[0]].append(a);edge(a.artifact_id,a.metadata['parent_id'],'DEPENDS_ON','contains-reverse')
  if a.artifact_type=='api':
   routes[(a.metadata.get('method'),a.metadata.get('route'))].append(a)
   if a.metadata.get('handler_id'):edge(a.metadata['handler_id'],a.artifact_id,'EXPOSES_API')
 for a in artifacts:
  for call in a.metadata.get('calls',[]) if a.artifact_type not in {'class','source_file'} else []:
   candidates=[x for x in names.get(call.split('.')[-1],[]) if x.artifact_id!=a.artifact_id and x.artifact_type not in {'api','api_caller'}];local=[x for x in candidates if x.file_path==a.file_path]
   if len(local)==1:candidates=local
   if len(candidates)==1:edge(a.artifact_id,candidates[0].artifact_id,'TESTS' if a.artifact_type=='test_method' else 'CALLS','unique-symbol',.85)
  if a.artifact_type=='api_caller':
   targets=routes.get((a.metadata.get('method'),a.metadata.get('route')),[])
   if len(targets)==1:edge(a.artifact_id,targets[0].artifact_id,'CONSUMES_API','exact-literal-contract')
   if a.metadata.get('owner_id'):edge(a.metadata['owner_id'],a.artifact_id,'DEPENDS_ON','client-owner')
  if not a.symbol:
   for imp in a.metadata.get('imports',[]):
    module=imp.replace('.','/').lstrip('/');targets=[b for p,b in files.items() if p.endswith(module+'.py') or p.endswith(module+'/__init__.py') or p.endswith(module+'.java')]
    if len(targets)==1:edge(a.artifact_id,targets[0].artifact_id,'IMPORTS','module-path',.9)
 for row in declared:edge(row['source_artifact'],row['target_artifact'],row['relation_type'],row.get('method','declared-trace'),row.get('confidence',1.),is_declared=True)
 for k,row in edges.items():
  persisted={key:value for key,value in row.items() if key!='is_declared'}
  store.put('graph_edges',k,persisted);store.put('trace_links',k,persisted)
 return g,list(edges.values())

def impact(g,seeds,depth=2,containment=False):
 filtered=nx.Graph();filtered.add_nodes_from(g.nodes)
 for s,t,e in g.edges(data=True):
  if containment or e.get('method')!='contains-reverse':filtered.add_edge(s,t)
 out={};seeds=set(seeds)
 for seed in seeds:
  if seed not in filtered:continue
  for target,path in nx.single_source_shortest_path(filtered,seed,cutoff=depth).items():
   if target not in seeds and (target not in out or len(path)<len(out[target])):out[target]=path
 return out
