"""Small dependency-free validator for the published diagnostic case template."""
import hashlib,re

LABELS={'trace':{'LINKED','BROKEN_TRACE','MISSING_TRACE','UNCERTAIN'},
        'consistency':{'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','NO_ASSURANCE_IMPACT','UNCERTAIN'},
        'test_obligation':{'SATISFIED','UNSATISFIED','UNVERIFIED','NOT_APPLICABLE'}}
STATUSES={'PENDING','IN_REVIEW','ADJUDICATED','UNRESOLVED'}
SPLITS={'development','validation','test'}

def validate_case(case):
    required={'case_id','repository_id','base_revision','head_revision','artifact_hashes',
              'evidence_packet','labels','review','adjudication_status','split'}
    errors=[]
    if set(case)!=required:errors.append('case fields must exactly match the v1 contract')
    for key in ('case_id','repository_id','base_revision','head_revision','evidence_packet'):
        if not isinstance(case.get(key),str) or not case[key].strip():errors.append(key+' must be a nonempty string')
    hashes=case.get('artifact_hashes')
    if not isinstance(hashes,list) or any(not isinstance(x,str) or not re.fullmatch('[0-9a-f]{64}',x) for x in hashes):
        errors.append('artifact_hashes must be SHA-256 hex strings')
    labels=case.get('labels',{})
    if set(labels)!=set(LABELS):errors.append('labels must contain trace, consistency and test_obligation')
    for axis,allowed in LABELS.items():
        if labels.get(axis) is not None and labels.get(axis) not in allowed:errors.append('invalid '+axis+' label')
    review=case.get('review',{})
    if set(review)!={'reviewer_id','rationale','timestamp'}:errors.append('review fields must match v1 contract')
    if any(review.get(k) is not None and not isinstance(review[k],str) for k in ('reviewer_id','rationale','timestamp')):
        errors.append('review values must be strings or null')
    if case.get('adjudication_status') not in STATUSES:errors.append('invalid adjudication_status')
    if case.get('split') not in SPLITS:errors.append('invalid split')
    if case.get('split')=='test' and not case.get('repository_id'):errors.append('test cases require repository ID for group splitting')
    return errors
