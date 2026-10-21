import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from database.store import Store
from ingestion.service import import_repository
from knowledge_graph.graph import build_graph
from traceability.recovery import recover
s=Store();results=[]
for name in ['flask','petclinic','express','fullstack']:
 r=import_repository(s,'data/repos/'+name);arts=s.artifacts(r['repository'],r['commit_id']);_,edges=build_graph(s,arts);links=recover(s,arts);r.update(name=name,graph_edges=len(edges),trace_candidates=len(links));results.append(r);print(json.dumps(r),flush=True)
pathlib.Path('reports/repository-imports.json').write_text(json.dumps(results,indent=2))
