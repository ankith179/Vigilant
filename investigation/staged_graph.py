"""Separately versioned candidate graph over verified partial source snapshots."""
from copy import deepcopy
import json
from pydantic import Field
from database.store import Store
from evaluation.change_cases import SourceReference
from ingestion.models import digest
from investigation.service import Scope,SECRET,MAX_OUTPUT_BYTES
from investigation.staged import StagedSourceReader,file_sha256
from evaluation.review_intake import OfflineReviewSourcePolicy
from knowledge_graph.graph import build_graph
import knowledge_graph.graph as graph_module


class GraphSelection(Scope):
    artifact_ids:list[str]=Field(min_length=1,max_length=20)
    limit:int=Field(default=40,ge=1,le=100)
    offset:int=Field(default=0,ge=0,le=20_000)


def project_staged_graph(reader,source_policy,payload):
    if type(reader) is not StagedSourceReader or type(source_policy) is not OfflineReviewSourcePolicy:
        raise TypeError('Validated reader and explicit source policy required')
    args=GraphSelection.model_validate(payload)
    if SECRET.search(json.dumps(args.model_dump())):raise ValueError('Sensitive graph selection withheld')
    snapshot=reader.snapshot(args.repository,args.commit_id)
    by={a.artifact_id:a for a in snapshot['artifacts']};files={r['file']:r for r in snapshot['files']}
    if len(set(args.artifact_ids))!=len(args.artifact_ids) or not set(args.artifact_ids)<=by.keys():
        raise ValueError('Distinct existing snapshot artifact identities required')
    # Parse-error artifacts remain in coverage; they cannot supply resolved edges.
    eligible=[a for a in by.values() if files[a.file_path]['status']=='PARSED']
    disposable=Store('sqlite:///:memory:')
    try:
        _,edges=build_graph(disposable,eligible)
    finally:disposable.engine.dispose()
    selected=set(args.artifact_ids)
    candidates=sorted((e for e in edges if e['source_artifact'] in selected or e['target_artifact'] in selected),key=lambda e:e['id'])
    if len(candidates)>20_000:raise ValueError('Candidate edge budget exceeded')
    page=candidates[args.offset:args.offset+args.limit];receipts={};withheld=[];accepted=[]
    repo=reader._row('repositories',args.repository)
    for edge in page:
        endpoint_receipts=[];failure=False
        for aid in (edge['source_artifact'],edge['target_artifact']):
            if aid not in receipts:
                a=by[aid]
                try:
                    if SECRET.search(a.content):raise ValueError('Sensitive endpoint withheld')
                    ref=SourceReference(artifact_id=aid,commit_id=a.commit_id,file=a.file_path,
                        content_hash=a.content_hash,start_line=a.start_line,end_line=a.end_line)
                    receipts[aid]={'status':'VERIFIED','receipt':source_policy.verify(repo,a,ref)}
                except (ValueError,OSError):receipts[aid]={'status':'UNAVAILABLE_OR_WITHHELD'}
            endpoint_receipts.append(deepcopy(receipts[aid]))
            failure|=receipts[aid]['status']!='VERIFIED'
        if failure:
            withheld.append({'source_edge_id':edge['id'],'status':'UNKNOWN_SOURCE_SUPPORT'})
            continue
        item={'source_edge':deepcopy(edge),'endpoint_source_receipts':endpoint_receipts,
              'classification':'STATIC_RELATIONSHIP_CANDIDATE','causal_impact_verified':False,
              'semantic_support':'NOT_ESTABLISHED'}
        item['projection_edge_id']=digest('partial-staged-graph-edge-v1',item);accepted.append(item)
    result={'policy':'partial-staged-graph-v1','scope':{'repository':args.repository,'commit_id':args.commit_id,'project_id':snapshot['project_id']},
        'selection':args.model_dump(),'edges':accepted,'withheld_edges':withheld,
        'denominators':{'snapshot_artifacts':len(by),'eligible_artifacts':len(eligible),
            'artifacts_with_unavailable_or_error_file':len(by)-len(eligible),'incident_candidate_edges':len(candidates),
            'page_candidate_edges':len(page),'source_verified_edges':len(accepted),'withheld_edges':len(withheld)},
        'next_offset':args.offset+args.limit if args.offset+args.limit<len(candidates) else None,
        'coverage':deepcopy(snapshot['coverage']),
        'unknowns':['PARTIAL_UNREVIEWED_SOURCE_SCOPE','UNMODELED_OR_UNRESOLVED_RELATIONSHIPS',
                    'ABSENT_EDGE_IS_NOT_A_NEGATIVE_LINK','NO_REVIEWED_OBLIGATIONS_NO_MISSING_TEST_CONCLUSION'],
        'provenance':{'snapshot':deepcopy(snapshot['provenance']),'source_policy':deepcopy(source_policy.provenance),
                      'projection_source_sha256':file_sha256(__file__),'graph_builder_sha256':file_sha256(graph_module.__file__)},
        'findings':[],'consistency':'NOT_ESTABLISHED','complete_impact':'NOT_ESTABLISHED',
        'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    if SECRET.search(json.dumps(result)):raise ValueError('Sensitive graph result withheld')
    if len(json.dumps(result,ensure_ascii=False).encode())>MAX_OUTPUT_BYTES:raise ValueError('Graph output budget exceeded; request smaller page')
    result['result_id']=digest(result)
    return result
