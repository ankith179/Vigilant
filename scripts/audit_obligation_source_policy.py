"""Validate saved UNKNOWN search drafts without inventing reviewed obligations."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from consistency.search_inventory import SearchInventory,validate_inventory
from evaluation.review_intake import OfflineReviewSourcePolicy


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite enumeration audit')
    database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    staging=json.loads((ROOT/'reports/recovered-review-20261024/STAGING.json').read_text())
    before=hashlib.sha256(database.read_bytes()).hexdigest()
    if before!=staging['database_sha256']:raise ValueError('Frozen source Store differs')
    index_path=ROOT/'reports/search-drafts-20261024/prepared/index.json';index=json.loads(index_path.read_text())
    policy=OfflineReviewSourcePolicy(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',
        ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',ROOT)
    rows={};dispositions=Counter()
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        repos={r['name']:r for (raw,) in db.execute('select payload from repositories') for r in [json.loads(raw)]}
        for key,s in index['snapshots'].items():
            raw=(index_path.parent/s['draft']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Frozen draft checksum differs')
            manifest=SearchInventory.model_validate(json.loads(raw))
            if any(e.disposition!='UNKNOWN' or e.artifact_ids for e in manifest.entries):raise ValueError('Expected UNKNOWN drafts')
            repo=repos[s['repository']]
            try:
                result=validate_inventory(repo['path'],manifest,None,[],False,source_policy=policy,repository=repo)
                rows[key]={'status':'PARTIAL_UNKNOWN_BOUNDARY_VERIFIED','result':result}
                dispositions.update(result['dispositions'])
            except Exception as exc:rows[key]={'status':'FAILED_RETAINED','error':type(exc).__name__+': '+str(exc)[:300],'files':len(manifest.entries)}
    if hashlib.sha256(database.read_bytes()).hexdigest()!=before:raise ValueError('Frozen Store changed')
    result={'policy':policy.provenance,'snapshots':rows,'snapshot_denominator':len(index['snapshots']),
        'failed_snapshots':sum(r['status']=='FAILED_RETAINED' for r in rows.values()),'cases':len(index['cases']),
        'dispositions':dict(dispositions),'database_sha256':before,'draft_index_sha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),
        'actual_reviewed_registry_intake':'NOT_RUN; no real reviewed registry supplied','source_fetches':0,
        'independent_labels_created':0,'model_calls':0,'whole_repository_semantics':False,
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='snapshots'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output)))
