"""Partial-aware report composition; no obligations or judgments are invented."""
from copy import deepcopy
import json
from pydantic import BaseModel,ConfigDict,Field
from ingestion.models import digest
from investigation.service import Scope,SECRET
from investigation.staged_comparison import compare_staged
from investigation.staged_graph import project_staged_graph
from investigation.staged_inspection import StagedInvestigationService
from investigation.staged import file_sha256


class ReportSelection(Scope):
    base_commit:str=Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    base_artifact_ids:list[str]=Field(default_factory=list,max_length=20)
    head_artifact_ids:list[str]=Field(default_factory=list,max_length=20)


def compose_staged_report(reader,source_policy,payload):
    args=ReportSelection.model_validate(payload)
    if SECRET.search(json.dumps(args.model_dump())):raise ValueError('Sensitive report selection withheld')
    comparison=compare_staged(reader,args.repository,args.base_commit,args.commit_id)
    service=StagedInvestigationService(reader,source_policy)
    roles={};evidence=[];unknowns=[]
    for role,commit,ids in [('base',args.base_commit,args.base_artifact_ids),('head',args.commit_id,args.head_artifact_ids)]:
        if len(set(ids))!=len(ids):raise ValueError('Duplicate report selection')
        graph=project_staged_graph(reader,source_policy,{'repository':args.repository,'commit_id':commit,'artifact_ids':ids}) if ids else None
        inspections=[]
        for aid in ids:
            try:
                item=service.call('inspect_artifact',{'repository':args.repository,'commit_id':commit,'artifact_id':aid,'max_lines':20})
                inspections.append(item);evidence.extend(item['evidence'])
            except (ValueError,OSError):
                unknowns.append({'revision_role':role,'artifact_id':aid,'status':'SOURCE_UNAVAILABLE_OR_WITHHELD'})
        roles[role]={'commit_id':commit,'selected_artifact_ids':ids,'graph':graph,'inspections':inspections}
    unknown_artifacts=[deepcopy(a) for a in comparison['artifacts'] if a['outcome']=='UNKNOWN']
    changed_artifacts=[deepcopy(a) for a in comparison['artifacts'] if a['outcome']=='DIFFERENT_EXTRACTED_CONTENT']
    report={'policy':'partial-staged-report-v1','kind':'PARTIAL_DEVELOPMENT_OBSERVATION_REPORT',
        'scope':{'repository':args.repository,'base_commit':args.base_commit,'head_commit':args.commit_id,'project_id':comparison['project_id']},
        'selection':args.model_dump(),'comparison_reference':{'fingerprint':comparison['fingerprint'],'provenance':comparison['provenance']},
        'denominators':deepcopy(comparison['denominators']),'observed_outcomes':deepcopy(comparison['outcomes']),
        'changed_artifact_observations':changed_artifacts,'unknown_artifact_observations':unknown_artifacts,
        'roles':roles,'evidence':evidence,'source_unknowns':unknowns,'coverage':deepcopy(comparison['coverage']),
        'findings':[],'obligation_assessment':{'status':'NOT_ESTABLISHED','reviewed_registry_supplied':False},
        'consistency':'NOT_ESTABLISHED','complete_impact':'NOT_ESTABLISHED','semantic_support':'NOT_ESTABLISHED',
        'limitations':['Partial maps do not establish complete project coverage or negative links.',
            'Graph edges are source-backed relationship candidates; no behavioral impact is proven.',
            'Without reviewed obligations no MISSING_TEST conclusion is permitted.',
            'This separate report does not populate canonical analysis_runs or reviewer labels.'],
        'provenance':{'composition_source_sha256':file_sha256(__file__)},
        'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    if SECRET.search(json.dumps(report)):raise ValueError('Sensitive report withheld')
    if len(json.dumps(report,ensure_ascii=False).encode())>3_000_000:raise ValueError('Partial report exceeds 3 MB budget')
    report['report_id']=digest(report)
    return report
