"""Observed partial-source differences; absence never establishes a deletion."""
from collections import Counter
from copy import deepcopy
from ingestion.models import digest
from investigation.staged import StagedSourceReader,file_sha256


def _artifact_reference(a):
    if a is None:return None
    return {key:getattr(a,key) for key in ('artifact_id','commit_id','file_path','artifact_type',
        'symbol','content_hash','start_line','end_line')}


def compare_staged(reader,repository,base_commit,head_commit):
    """Read both checksum-validated snapshots; do not invoke Git, parsers or models.

    Each union file/artifact has exactly one outcome. Even a missing artifact in
    a PARSED counterpart stays UNKNOWN: extraction is not complete project gold.
    Object-ID relations are map observations, not fresh raw-source verification.
    """
    if not isinstance(reader,StagedSourceReader):raise TypeError('Expected a validated staged reader')
    base=reader.snapshot(repository,base_commit);head=reader.snapshot(repository,head_commit)
    if base['project_id']!=head['project_id'] or base['origin']!=head['origin']:
        raise ValueError('Staged comparison requires the same parser and repository scope')
    before={r['file']:r for r in base['files']};after={r['file']:r for r in head['files']}
    files=[]
    for path in sorted(before.keys()|after.keys()):
        a=before.get(path);b=after.get(path)
        # These IDs describe only entries explicitly present in the pinned maps.
        comparable=bool(a and b and a.get('object_id') and b.get('object_id'))
        outcome=('SAME_OBJECT_ID' if a['object_id']==b['object_id'] else 'DIFFERENT_OBJECT_ID') if comparable else 'UNKNOWN'
        files.append({'file':path,'base':deepcopy(a),'head':deepcopy(b),'outcome':outcome,
            'uncertainty':[] if comparable else ['MISSING_MAP_SIDE_OR_OBJECT_ID; absence is not pinned-tree absence']})
    old={a.artifact_id:a for a in base['artifacts']};new={a.artifact_id:a for a in head['artifacts']}
    artifacts=[]
    for aid in sorted(old.keys()|new.keys()):
        a=old.get(aid);b=new.get(aid);path=(a or b).file_path;reasons=[]
        relation=('SAME_EXTRACTED_CONTENT' if a.content_hash==b.content_hash else 'DIFFERENT_EXTRACTED_CONTENT') if a and b else 'UNPAIRED'
        for side,item,rows in [('BASE',a,before),('HEAD',b,after)]:
            row=rows.get(path)
            if row is None:reasons.append(side+'_FILE_NOT_IN_PARTIAL_MAP')
            elif row['status']!='PARSED':reasons.append(side+'_'+row['status'])
            if item is None:reasons.append(side+'_ARTIFACT_UNAVAILABLE_OR_UNEXTRACTED')
        artifacts.append({'artifact_id':aid,'file':path,'base':_artifact_reference(a),'head':_artifact_reference(b),
            'observed_content_relation':relation,'outcome':'UNKNOWN' if reasons else relation,'uncertainty':reasons})
    result={'policy':'partial-staged-comparison-v1','repository':repository,'project_id':base['project_id'],
        'base_commit':base_commit,'head_commit':head_commit,'files':files,'artifacts':artifacts,
        'denominators':{'file_union':len(files),'file_side_slots':2*len(files),
            'file_rows_observed':len(before)+len(after),'file_rows_unavailable':2*len(files)-len(before)-len(after),
            'artifact_union':len(artifacts),'artifact_side_slots':2*len(artifacts),
            'artifact_versions_observed':len(old)+len(new),'artifact_versions_unavailable':2*len(artifacts)-len(old)-len(new)},
        'outcomes':{'files':dict(Counter(r['outcome'] for r in files)),
            'artifacts':dict(Counter(r['outcome'] for r in artifacts))},
        'coverage':{'base':deepcopy(base['coverage']),'head':deepcopy(head['coverage']),
            'whole_repository_coverage':False,'absent_side_means_deleted_or_added':False,
            'semantic_equivalence':'NOT_ESTABLISHED','complete_impact':'NOT_ESTABLISHED',
            'consistency':'NOT_ESTABLISHED','negative_links':'NOT_ESTABLISHED'},
        'provenance':{'base':deepcopy(base['provenance']),'head':deepcopy(head['provenance']),
            'comparison_source_sha256':file_sha256(__file__)},
        'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    result['fingerprint']=digest(result)
    return result
