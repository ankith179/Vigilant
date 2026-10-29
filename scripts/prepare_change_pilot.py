"""Prepare unlabelled pilot records from existing candidates; no inference or new labels."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation.change_cases import ReviewedChangeCase


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--count',type=int,default=32)
    args=p.parse_args()
    if not 25<=args.count<=40:p.error('Pilot size must be between 25 and 40')
    source=ROOT/'reports/independent-review-20261022/candidate-cases.json'
    pool=json.loads(source.read_text())
    if len(pool['cases'])<args.count:p.error('Insufficient candidates')
    args.output.mkdir(parents=True,exist_ok=False)
    cases=[]
    for candidate in pool['cases'][:args.count]:
        case={k:candidate[k] for k in ('case_id','repository','base_commit','head_commit')}
        case.update(change_family=None,change_intent=None,consistency_label=None,affected_artifact_ids=None,
                    trace_links=None,reviewed_negative_links=None,obligations=[],obligation_inventory='UNKNOWN',
                    unknowns=[],evidence=[],reviewer_ids=[],adjudicator_id=None,adjudication_rationale=None,
                    semantic_support=None,semantic_reviewer_id=None)
        cases.append(case)
        packet={k:candidate[k] for k in ('case_id','repository','origin','base_commit','head_commit','changed_files','patch')}
        (args.output/(candidate['case_id']+'-packet.json')).write_text(json.dumps(packet,indent=2)+'\n')
    (args.output/'unlabelled-cases.json').write_text(json.dumps({'split':'pilot','held_out':False,'label_status':'UNLABELLED','cases':cases},indent=2)+'\n')
    (args.output/'reviewed-case-schema.json').write_text(json.dumps(ReviewedChangeCase.model_json_schema(),indent=2)+'\n')
    summary={'status':'ANNOTATION_REQUIRED','pilot_cases':len(cases),'independently_reviewed_cases':0,
             'candidate_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
             'selection':'First 32 (or requested count) of preserved round-robin candidate pool; no label-based selection',
             'new_model_calls':0,'target_91_percent':'NOT_EVALUATED',
             'limitations':['These repositories have prior project exposure; this pilot is not a held-out benchmark.',
                            'Unknown annotations are null, not negative or UNCERTAIN labels.',
                            'Two independent reviews, adjudication and semantic evidence review remain required.']}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
