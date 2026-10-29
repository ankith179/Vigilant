"""Read-only API acceptance of saved partial development reports, without labels."""
import argparse,json,os,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['VIGILANT_DB']='sqlite:///:memory:'
from backend.app import create_app
from backend.partial_reports import packaged_access
from database.store import Store
from investigation.staged import file_sha256
from fastapi.testclient import TestClient


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite API audit')
    manifest=ROOT/'reports/staged-report-20261025/reports/result.json'
    saved=json.loads(manifest.read_text());access=packaged_access(ROOT,file_sha256(manifest))
    before=file_sha256(ROOT/'data/snapshots/pilot-review-recovered-20261024.db')
    rows=[];store=Store('sqlite:///:memory:')
    with TestClient(create_app(store,partial_reports=access)) as client:
        # Honor a configured workspace token; no public authentication bypass.
        if os.getenv('VIGILANT_ACCESS_TOKEN'):client.headers['Authorization']='Bearer '+os.environ['VIGILANT_ACCESS_TOKEN']
        listing=client.get('/api/partial-reports?limit=100');assert listing.status_code==200
        assert listing.json()['total']==saved['cases']
        for entry in saved['rows']:
            row={'case_id':entry['case_id'],'report_id':entry.get('report_id')}
            if entry['status']!='COMPOSED':row['status']='UNAVAILABLE_RETAINED';rows.append(row);continue
            report=json.loads((manifest.parent/entry['path']).read_text())
            params={k:report['scope'][k] for k in ('repository','base_commit','head_commit')}
            response=client.get('/api/partial-reports/'+entry['report_id'],params=params)
            row['http_status']=response.status_code
            if response.status_code==200:
                result=response.json();assert result['report']==report
                assert not result['report']['findings'] and result['report']['quality_target']=='NOT_EVALUATED'
                row.update(status='REVALIDATED',validation=result['validation'],unknown_artifacts=len(report['unknown_artifact_observations']))
            else:row['status']='REVALIDATION_REJECTED'
            rows.append(row)
        assert not store.rows('analysis_runs') and not store.rows('tool_results')
    store.engine.dispose()
    assert file_sha256(ROOT/'data/snapshots/pilot-review-recovered-20261024.db')==before
    result={'policy':'partial-report-api-audit-v1','cases':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
        'unknown_artifact_outcomes_retained':sum(r.get('unknown_artifacts',0) for r in rows),
        'rows':rows,'source_store_sha256':before,'canonical_store_writes':0,'model_calls':0,'independent_labels_created':0,
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED','ui_browser_acceptance':'NOT_RUN'}
    output.mkdir(parents=True);(output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(p.parse_args().output),indent=2))
