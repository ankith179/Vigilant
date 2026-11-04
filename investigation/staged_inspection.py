"""Explicit read-only staged inspection; no import, inference or result writes."""
from copy import deepcopy
import json
from evaluation.change_cases import SourceReference
from evaluation.review_intake import OfflineReviewSourcePolicy
from ingestion.models import digest
from investigation.service import Inspect,SECRET,MAX_OUTPUT_BYTES
from investigation.staged import StagedSourceReader,file_sha256
import investigation.staged as staged


class StagedInvestigationService:
    """A bounded source-navigation route, not the full investigation workflow."""
    def __init__(self,reader,source_policy):
        if type(reader) is not StagedSourceReader or type(source_policy) is not OfflineReviewSourcePolicy:
            raise TypeError('Validated staged reader and explicit offline source policy required')
        self.reader=reader;self.source_policy=source_policy

    def call(self,name,payload):
        if name!='inspect_artifact':raise ValueError('Staged route supports inspect_artifact only')
        args=Inspect.model_validate(payload)
        if SECRET.search(json.dumps(args.model_dump())):raise ValueError('Sensitive arguments withheld')
        snapshot=self.reader.snapshot(args.repository,args.commit_id)
        a=next((a for a in snapshot['artifacts'] if a.artifact_id==args.artifact_id),None)
        if a is None:raise ValueError('Artifact unavailable in selected staged snapshot; absence is not a negative')
        start=args.start_line if args.start_line is not None else a.start_line
        if start<a.start_line or start>a.end_line:raise ValueError('Excerpt outside stored artifact')
        end=min(a.end_line,start+args.max_lines-1)
        quote='\n'.join(a.content.splitlines()[start-a.start_line:end-a.start_line+1])
        if SECRET.search(quote):raise ValueError('Sensitive source withheld')
        ref=SourceReference(artifact_id=a.artifact_id,commit_id=a.commit_id,file=a.file_path,
            content_hash=a.content_hash,start_line=start,end_line=end)
        repo=self.reader._row('repositories',args.repository)
        receipt=self.source_policy.verify(repo,a,ref)
        file=next(r for r in snapshot['files'] if r['file']==a.file_path)
        evidence={**ref.model_dump(),'repository':a.repository,'project_id':a.project_id,'quote':quote,
            'evidence_id':digest(ref.model_dump(),quote)}
        result={'policy':'partial-staged-inspection-v1','tool':name,'arguments':args.model_dump(),
            'scope':{'repository':a.repository,'commit_id':a.commit_id,'project_id':a.project_id},
            'data':{'artifact_type':a.artifact_type,'symbol':a.symbol,'file_status':deepcopy(file)},
            'evidence':[evidence],'source_verification_receipts':[receipt],
            'coverage':deepcopy(snapshot['coverage']),
            'unknowns':['SEARCH_UNREVIEWED','WHOLE_PROJECT_SEMANTICS_NOT_ESTABLISHED']+
                (['PARSE_ERRORS_RETAINED'] if file['status']=='PARSED_WITH_ERRORS' else []),
            'provenance':{'snapshot':deepcopy(snapshot['provenance']),
                'source_policy':deepcopy(self.source_policy.provenance),
                'reader_source_sha256':file_sha256(staged.__file__),
                'inspection_source_sha256':file_sha256(__file__)},
            'semantic_support':'NOT_ESTABLISHED','consistency':'NOT_ESTABLISHED',
            'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
        if SECRET.search(json.dumps(result)):raise ValueError('Sensitive result withheld')
        if len(json.dumps(result,ensure_ascii=False).encode())>MAX_OUTPUT_BYTES:raise ValueError('Staged result exceeds output budget')
        result['result_id']=digest(result)
        return result
