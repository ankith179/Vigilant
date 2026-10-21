"""Export one immutable graph scope to generic JSON, CSV and GraphML."""
from pathlib import Path
import argparse
import csv
import json
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import networkx as nx


def export(database,repository,commit,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(f'file:{Path(database).resolve()}?mode=ro',uri=True) as db:
        def rows(table):
            return [json.loads(r[0]) for r in db.execute('SELECT payload FROM '+table+' WHERE repository=? AND commit_id=? ORDER BY id',(repository,commit))]
        nodes=rows('graph_nodes');edges=rows('graph_edges')
    if not nodes:raise ValueError('No graph exists for this repository and commit')
    ids={n['artifact_id'] for n in nodes}
    if any(e['source_artifact'] not in ids or e['target_artifact'] not in ids for e in edges):raise ValueError('Dangling edge in saved graph')
    graph={'repository':repository,'commit_id':commit,'nodes':nodes,'edges':edges,
           'interpretation':'Structural and declared relationships retain method/confidence; they are not causal or semantic proof.'}
    (output/'graph.json').write_text(json.dumps(graph,indent=2))
    for name,items in [('nodes',nodes),('edges',edges)]:
        with (output/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=sorted({k for item in items for k in item}));writer.writeheader()
            writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in item.items()} for item in items)
    g=nx.MultiDiGraph(repository=repository,commit_id=commit)
    clean=lambda item:{k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in item.items() if v is not None}
    for n in nodes:g.add_node(n['artifact_id'],**clean(n))
    for e in edges:g.add_edge(e['source_artifact'],e['target_artifact'],key=e['id'],**clean(e))
    nx.write_graphml_xml(g,output/'graph.graphml')
    return {'repository':repository,'commit_id':commit,'nodes':len(nodes),'edges':len(edges),'native_graphify_import_verified':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=ROOT/'data/snapshots/vigilant.db')
    p.add_argument('--repository',required=True);p.add_argument('--commit',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'handoff/graphify');a=p.parse_args()
    print(json.dumps(export(a.database,a.repository,a.commit,a.output),indent=2))

if __name__=='__main__':main()
