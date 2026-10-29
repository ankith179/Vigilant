"""Bounded authored acceptance for the opt-in lineage observer; retains failures."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from change_analysis.lineage import observe, verify
from scripts.audit_artifact_lineage import fixture, CASES


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite lineage acceptance')
    output.mkdir(parents=True)
    rows=[]
    with tempfile.TemporaryDirectory(prefix='vigilant-lineage-observations-') as tmp:
        for name in CASES:
            f=fixture(Path(tmp)/name,name)
            args=dict(project='authored-acceptance',repository='authored-'+name,base=f['base'],head=f['head'])
            if name=='missing_revision':
                try:observe(f['path'],**args)
                except subprocess.CalledProcessError as exc:
                    rows.append({'case':name,'status':'UNKNOWN_MISSING_REVISION','git_exit_code':exc.returncode,
                                 'scope':args,'record':None})
                    continue
                raise AssertionError('Missing revision accepted')
            record=observe(f['path'],**args)
            assert verify(f['path'],record,**args)==record
            with (output/(name+'.json')).open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
            rows.append({'case':name,'status':'SOURCE_REVALIDATED_UNREVIEWED',
                         'scope':args,'record':name+'.json','record_id':record['record_id'],
                         'denominators':record['denominators']})
    result={'status':'BOUNDED_AUTHORED_ACCEPTANCE_VERIFIED','case_denominator':len(CASES),
            'sidecars_revalidated':sum(r['record'] is not None for r in rows),
            'unknown_missing_revision':sum(r['status']=='UNKNOWN_MISSING_REVISION' for r in rows),'cases':rows,
            'model_calls':0,'canonical_writes':0,'independent_labels_created':0,
            'production_consumers':'NOT_INTEGRATED','quality_target_91':'NOT_EVALUATED',
            'scope':'Authored Python fixtures; no independent logical-continuity or project-semantic labels'}
    assert len(rows)==len(CASES)==9
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    result=run(p.parse_args().output)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
