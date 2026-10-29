"""Bounded all-case presentation audit; not semantic correctness or independent gold."""
from pathlib import Path
import argparse,hashlib,json,os,sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ['VIGILANT_DB']='sqlite:///:memory:'
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.partial_reports import packaged_access
from backend.partial_delivery import TOPICS
from database.store import Store
from investigation.staged import file_sha256
from tests.test_partial_delivery import RecordParser


def run(output):
    if output.exists():raise FileExistsError('Refusing to overwrite delivery audit')
    manifest=ROOT/'reports/staged-report-20261025/reports/result.json';index=json.loads(manifest.read_text())
    access=packaged_access(ROOT,file_sha256(manifest));db=ROOT/'data/snapshots/pilot-review-recovered-20261024.db';before=file_sha256(db)
    store=Store('sqlite:///:memory:');rows=[];intents=list(TOPICS)
    with TestClient(create_app(store,partial_reports=access)) as client:
        if os.getenv('VIGILANT_ACCESS_TOKEN'):client.headers['Authorization']='Bearer '+os.environ['VIGILANT_ACCESS_TOKEN']
        for i,entry in enumerate(index['rows']):
            row={'case_id':entry['case_id'],'status':'UNAVAILABLE_RETAINED'};rows.append(row)
            if entry['status']!='COMPOSED':continue
            saved=json.loads((manifest.parent/entry['path']).read_text());scope={k:saved['scope'][k] for k in ['repository','base_commit','head_commit']};base='/api/partial-reports/'+saved['report_id']
            explanation=client.post(base+'/explain',json={**scope,'intent':intents[i%len(intents)]});assert explanation.status_code==200,explanation.text
            result=explanation.json();assert result['report_id']==saved['report_id'] and result['inference_calls']==0
            for claim in result['claims']:
                value={'report':saved}
                for key in claim['json_pointer'].strip('/').split('/'):value=value[key]
                assert value==claim['value']
            response=client.get(base+'/export',params={**scope,'format':'json'});assert response.status_code==200
            payload=response.json();assert payload['report']==saved
            response=client.get(base+'/export',params={**scope,'format':'html'});assert response.status_code==200
            parsed=RecordParser();parsed.feed(response.text);assert not parsed.active and json.loads(''.join(parsed.parts))==payload
            row.update(status='VERIFIED',report_id=saved['report_id'],intent=result['intent'],claims=len(result['claims']),unknowns=len(saved['unknown_artifact_observations']),
                explanation_sha256=hashlib.sha256(explanation.content).hexdigest(),html_sha256=hashlib.sha256(response.content).hexdigest(),source_validation=result['validation'])
            print(json.dumps({'case':i+1,'of':index['cases'],'status':row['status']}),flush=True)
        assert not store.rows('analysis_runs') and not store.rows('tool_results')
    assert file_sha256(db)==before
    result={'policy':'partial-report-delivery-audit-v1','cases':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
      'explanation_api_requests':sum(r['status']=='VERIFIED' for r in rows),'explanation_intents':dict(Counter(r.get('intent','UNAVAILABLE') for r in rows)),
      'export_requests':2*sum(r['status']=='VERIFIED' for r in rows),'unknown_artifact_outcomes_retained':sum(r.get('unknowns',0) for r in rows),
      'rows':rows,'source_store_sha256':before,'canonical_writes':0,'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    output.mkdir(parents=True);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.output);print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
