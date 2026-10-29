"""Opt-in access to separately versioned development reports, with fresh verification."""
from pathlib import Path
import json
import re
import hashlib
from ingestion.models import digest
from investigation.service import SECRET
from investigation.staged import StagedSourceReader,file_sha256,read_json
from investigation.staged_report import compose_staged_report
from investigation.staged_inspection import StagedInvestigationService
from evaluation.review_intake import OfflineReviewSourcePolicy


class PartialReportAccess:
    def __init__(self,directory,manifest_sha256,reader_factory,source_policy):
        if not re.fullmatch(r'[0-9a-f]{64}',manifest_sha256):raise ValueError('Pinned report manifest SHA-256 required')
        if type(source_policy) is not OfflineReviewSourcePolicy:raise TypeError('Explicit source policy required')
        self.directory=Path(directory).resolve();self.manifest_sha256=manifest_sha256
        self.reader_factory=reader_factory;self.source_policy=source_policy
        self._manifest()

    def _manifest(self):
        path=self.directory/'result.json';raw,m=read_json(path,1_000_000)
        if hashlib.sha256(raw).hexdigest()!=self.manifest_sha256:raise ValueError('Report manifest changed')
        rows=m.get('rows');seen=set()
        if not isinstance(rows,list) or len(rows)>200 or len(rows)!=m.get('cases'):raise ValueError('Invalid report manifest denominator')
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get('case_id'),str):raise ValueError('Invalid report entry')
            if row.get('status')=='COMPOSED':
                rid=row.get('report_id');name=row.get('path')
                if not isinstance(rid,str) or not re.fullmatch(r'[0-9a-f]{64}',rid) or rid in seen:raise ValueError('Invalid or duplicate report identity')
                if not isinstance(name,str) or Path(name).name!=name or not re.fullmatch(r'report-[0-9]+\.json',name):raise ValueError('Invalid report path')
                seen.add(rid)
        return m

    def listing(self,offset=0,limit=20):
        if type(offset) is not int or type(limit) is not int or not 0<=offset<=200 or not 1<=limit<=100:raise ValueError('Invalid report page')
        m=self._manifest();rows=m['rows'];items=[]
        for row in rows[offset:offset+limit]:
            item={k:row[k] for k in ('case_id','status','report_id') if k in row}
            if row['status']=='COMPOSED':item['scope']=self._saved(row)['scope']
            items.append(item)
        result={'enabled':True,'items':items,'total':len(rows),'next_offset':offset+limit if offset+limit<len(rows) else None,
                'source_validation':'REQUIRED_ON_READ','scope':'PARTIAL_DEVELOPMENT_REPORTS','quality_target':'NOT_EVALUATED'}
        if SECRET.search(json.dumps(result)):raise ValueError('Sensitive catalog withheld')
        return result

    def _saved(self,row):
        _,saved=read_json(self.directory/row['path'],3_000_000)
        payload={k:v for k,v in saved.items() if k!='report_id'}
        if saved.get('report_id')!=row['report_id'] or digest(payload)!=row['report_id']:raise ValueError('Report identity mismatch')
        return saved

    def read(self,report_id,repository,base_commit,head_commit):
        rows=self._manifest()['rows'];row=next((r for r in rows if r.get('report_id')==report_id and r['status']=='COMPOSED'),None)
        if row is None:raise KeyError('Report not registered')
        saved=self._saved(row)
        scope=saved.get('scope',{})
        if any(scope.get(k)!=v for k,v in {'repository':repository,'base_commit':base_commit,'head_commit':head_commit}.items()):
            raise ValueError('Report outside requested revision scope')
        # Rebuild the exact bounded observation from the validated read-only Store.
        # A saved digest never bypasses fresh source verification or coverage checks.
        with self.reader_factory() as reader:
            fresh=compose_staged_report(reader,self.source_policy,saved['selection'])
        if fresh!=saved:raise ValueError('Report is stale or source support has changed')
        return {'report':fresh,'validation':{'report_identity':'VERIFIED','source_revalidation':'VERIFIED_NOW',
                    'manifest_sha256':self.manifest_sha256,'access_source_sha256':file_sha256(__file__),
                    'semantic_support':'NOT_ESTABLISHED','reviewer_authentication':'NOT_ESTABLISHED'}}

    def inspect(self,report_id,repository,base_commit,head_commit,commit_id,artifact_id,start_line=None,max_lines=40):
        report=self.read(report_id,repository,base_commit,head_commit)['report']
        allowed=set()
        for role in report['roles'].values():
            allowed.update((role['commit_id'],a) for a in role['selected_artifact_ids'])
            for edge in (role['graph'] or {}).get('edges',[]):
                allowed.update((role['commit_id'],edge['source_edge'][key]) for key in ('source_artifact','target_artifact'))
        if (commit_id,artifact_id) not in allowed:raise ValueError('Source is outside this report selection')
        with self.reader_factory() as reader:
            return StagedInvestigationService(reader,self.source_policy).call('inspect_artifact',
                {'repository':repository,'commit_id':commit_id,'artifact_id':artifact_id,'start_line':start_line,'max_lines':max_lines})


def packaged_access(root,manifest_sha256):
    root=Path(root)
    policy=OfflineReviewSourcePolicy(root/'reports/local-source-recovery-20261024/upstream-verified/result.json',root/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',root)
    def reader():return StagedSourceReader(root/'data/snapshots/pilot-review-recovered-20261024.db',root/'reports/verified-cache-maps-20261024/maps/index.json',root/'reports/recovered-review-20261024/STAGING.json')
    return PartialReportAccess(root/'reports/staged-report-20261025/reports',manifest_sha256,reader,policy)
