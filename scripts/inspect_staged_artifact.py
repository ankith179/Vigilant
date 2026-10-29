"""Opt-in exact-source inspection of a frozen staged snapshot; no model calls."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation.review_intake import OfflineReviewSourcePolicy
from investigation.staged import StagedSourceReader
from investigation.staged_inspection import StagedInvestigationService


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['repository','commit-id','artifact-id']:p.add_argument('--'+name,required=True)
    p.add_argument('--start-line',type=int);p.add_argument('--max-lines',type=int,default=40)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--database',type=Path,default=ROOT/'data/snapshots/pilot-review-recovered-20261024.db')
    p.add_argument('--index',type=Path,default=ROOT/'reports/verified-cache-maps-20261024/maps/index.json')
    p.add_argument('--staging',type=Path,default=ROOT/'reports/recovered-review-20261024/STAGING.json')
    p.add_argument('--verified-source-cache',type=Path,required=True)
    p.add_argument('--source-recovery-queue',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to overwrite inspection')
    policy=OfflineReviewSourcePolicy(a.verified_source_cache,a.source_recovery_queue,ROOT)
    with StagedSourceReader(a.database,a.index,a.staging) as reader:
        result=StagedInvestigationService(reader,policy).call('inspect_artifact',
            {k:getattr(a,k) for k in ['repository','commit_id','artifact_id','start_line','max_lines']})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'result_id':result['result_id'],'model_calls':0,'semantic_support':'NOT_ESTABLISHED'}))


if __name__=='__main__':main()
