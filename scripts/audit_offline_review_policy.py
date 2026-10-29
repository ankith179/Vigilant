"""Exercise opt-in source receipts on real development packets without labels."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from pydantic import ValidationError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation.change_cases import SourceReference
from evaluation.review_intake import OfflineReviewSourcePolicy,ReviewerForm
from ingestion.models import Artifact,digest


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite policy audit')
    report=ROOT/'reports/recovered-review-20261024';packets=report/'packets'
    staging=json.loads((report/'STAGING.json').read_text());database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    before=hashlib.sha256(database.read_bytes()).hexdigest()
    if before!=staging['database_sha256']:raise ValueError('Source Store differs')
    manifest_path=packets/'manifest.json';manifest=json.loads(manifest_path.read_text())
    for name,h in manifest['files'].items():
        if hashlib.sha256((packets/name).read_bytes()).hexdigest()!=h:raise ValueError('Frozen packets differ')
    policy=OfflineReviewSourcePolicy(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',
        ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',ROOT)
    rows=[];blank_rejections=0
    for name in ['reviewer-1.json','reviewer-2.json']:
        try:ReviewerForm.model_validate(json.loads((packets/name).read_text()))
        except ValidationError:blank_rejections+=1
    if blank_rejections!=2:raise ValueError('Expected untouched blank reviewer forms')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        for file in sorted(packets.glob('*-packet.json')):
            packet=json.loads(file.read_text())
            repo=json.loads(db.execute('select payload from repositories where id=?',(packet['repository'],)).fetchone()[0])
            for side,snapshot in packet['snapshot_sides'].items():
                for item in snapshot['changed_files']:
                    row={'case_id':packet['case_id'],'side':side,'file':item['file'],'search_disposition':item['search_disposition']}
                    if item['source_reference'] is None:
                        # These four paths remain explicit, outside any intake source assertion.
                        row['status']='NO_SOURCE_REFERENCE';row['recorded_source_status']=item['source_status']
                    else:
                        ref=SourceReference.model_validate(item['source_reference'])
                        a=json.loads(db.execute('select payload from artifacts where id=?',(digest(ref.artifact_id,ref.commit_id),)).fetchone()[0])
                        a.pop('id',None)
                        try:row.update(policy.verify(repo,Artifact.model_validate(a),ref))
                        except Exception as exc:row.update(status='FAILED_RETAINED',error=type(exc).__name__+': '+str(exc)[:200])
                    rows.append(row)
    if hashlib.sha256(database.read_bytes()).hexdigest()!=before:raise ValueError('Frozen Store changed')
    result={'policy':policy.provenance,'rows':rows,'denominator':len(rows),'cases':manifest['cases'],
        'source_statuses':dict(Counter(r['status'] for r in rows)),
        'database_sha256':before,'packet_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'blank_forms_rejected':blank_rejections,'actual_review_intake':'NOT_RUN; no real reviewer judgments supplied',
        'independent_labels_created':0,'model_calls':0,'new_fetches':0,'semantic_review':'NOT_PERFORMED',
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(p.parse_args().output)))
