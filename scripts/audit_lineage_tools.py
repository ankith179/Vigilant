"""Exercise real HTTP and retained-result routes on disposable authored imports."""
from pathlib import Path
import argparse
import json
import os
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['VIGILANT_DB']='sqlite:///:memory:'
from fastapi.testclient import TestClient
from backend.app import create_app
from database.store import Store
from ingestion.models import digest
from ingestion.service import import_repository
from ingestion.git import inventory
from scripts.audit_artifact_lineage import fixture, CASES


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite lineage transport audit')
    output.mkdir(parents=True)
    os.environ['VIGILANT_LINEAGE_TOOLS']='1'
    os.environ['VIGILANT_ACCESS_TOKEN']='disposable-lineage-audit-token'
    rows=[]
    with tempfile.TemporaryDirectory(prefix='vigilant-lineage-tool-fixtures-') as tmp:
        for name in CASES:
            f=fixture(Path(tmp)/name,name);store=Store('sqlite:///:memory:')
            rid=digest('lineage-tool-authored-fixture-v1',name)
            try:
                for commit in ([f['base']] if name=='missing_revision' else [f['base'],f['head']]):
                    import_repository(store,f['path'],project='authored-lineage-tools-v1',rev=commit,repository_id=rid)
                paths=sorted({r['file'] for commit in ([f['base']] if name=='missing_revision' else [f['base'],f['head']]) for r in inventory(f['path'],commit) if r['eligible']})
                args={'repository':rid,'commit_id':f['head'],'base_commit':f['base'],'paths':paths}
                preserved={table:store.rows(table) for table in ['artifacts','commits','graph_nodes','graph_edges','analysis_runs']}
                with TestClient(create_app(store)) as client:
                    payload={'name':'inspect_lineage','arguments':args};headers={'Authorization':'Bearer disposable-lineage-audit-token'}
                    assert client.post('/api/investigation/call',json=payload).status_code==401
                    response=client.post('/api/investigation/call',json=payload,headers=headers)
                    if name=='missing_revision':
                        assert response.status_code==409 and not store.rows('tool_results') and not store.rows('unknown_revisions')
                        rows.append({'case':name,'status':'UNKNOWN_MISSING_REVISION','http_status':409,'result':None})
                        continue
                    assert response.status_code==200,response.text
                    result=response.json()
                    retained=client.post('/api/investigation/call',json={'name':'inspect_retained_result','arguments':{
                        'repository':rid,'commit_id':f['head'],'result_id':result['result_id']}},headers=headers)
                    assert retained.status_code==200 and retained.json()==result
                    assert preserved=={table:store.rows(table) for table in preserved}
                    assert len(store.rows('tool_results'))==1
                    record=result['data']['lineage_record']
                    assert all(r['logical_continuity']=='UNKNOWN' and not r['relationship_transfer_allowed'] for r in record['observations'])
                    with (output/(name+'.json')).open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
                    rows.append({'case':name,'status':'SOURCE_REVALIDATED_UNREVIEWED','http_status':200,
                                 'result':name+'.json','result_id':result['result_id'],'denominators':record['denominators'],
                                 'indexed_artifacts_preserved':True,'graph_and_investigation_writes':0,
                                 'tool_results':1,'unknown_revisions':len(store.rows('unknown_revisions'))})
            finally:store.engine.dispose()
    summary={'status':'AUTHORED_HTTP_AND_RETAINED_ACCEPTANCE_VERIFIED','case_denominator':len(CASES),
             'accepted_cases':sum(r['http_status']==200 for r in rows),'missing_revision_unknowns':sum(r['http_status']==409 for r in rows),
             'unauthenticated_requests_rejected':len(rows),'cases':rows,'model_calls':0,
             'independent_labels_created':0,'frozen_production_database_writes':0,
             'quality_target_91':'NOT_EVALUATED','scope':'Authored fixture imports; no independent accuracy or semantic/lineage proof'}
    assert len(rows)==9
    with (output/'result.json').open('x') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    result=run(p.parse_args().output)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
