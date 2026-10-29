"""Validate independent review attestations and source references without inventing labels."""
from pathlib import Path
import hashlib
from pydantic import BaseModel, ConfigDict, Field
from ingestion.models import Artifact, Status, digest
from evaluation.change_cases import ReviewedChangeCase, SourceReference
from rag.evidence import verify_git


class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    case_id: str = Field(min_length=1)
    consistency_label: Status
    trace_links: list[str]
    affected_artifact_ids: list[str]
    rationale: str = Field(min_length=1)
    evidence: list[SourceReference] = Field(min_length=1)


class ReviewerForm(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reviewer_id: str = Field(min_length=1)
    independent_of_pipeline_author: bool
    cases: list[Assessment] = Field(min_length=1)


class OfflineReviewSourcePolicy:
    """Explicit scoped-cache policy; original Git objects are never written."""
    def __init__(self, manifest, queue, project_root):
        from scripts.prepare_pilot_artifact_maps import load_verified_cache
        from scripts import check_review_source_readiness as checker
        self._cache=load_verified_cache(manifest,queue)
        self._root=Path(project_root).resolve()
        self._checker=checker
        self._trees={}
        self.provenance={'policy':'offline-scoped-review-intake-v1',
            'intake_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cache_manifest_sha256':self._cache['manifest_sha256'],'queue_sha256':self._cache['queue_sha256'],
            'source_verifier_sha256':hashlib.sha256(Path(checker.__file__).read_bytes()).hexdigest(),
            'cache_loader_sha256':hashlib.sha256(Path(load_verified_cache.__code__.co_filename).read_bytes()).hexdigest()}

    def _repository_path(self, repository):
        if (not repository or not isinstance(repository.get('project_id'),str) or
            not isinstance(repository.get('origin'),str) or not repository['origin'].startswith('https://') or
            digest(repository['project_id'],repository['origin'])!=repository.get('repository')):
            raise ValueError('Offline source repository identity mismatch')
        path=Path(repository['path'])
        path=(path if path.is_absolute() else self._root/path).resolve()
        if not path.is_relative_to(self._root) or not path.is_dir():
            raise ValueError('Offline repository path outside declared project root or unavailable')
        return path

    def tree(self, repository, commit):
        path=self._repository_path(repository);key=str(path),commit
        if key not in self._trees:self._trees[key]=self._checker.pinned_tree(path,commit)
        return {p:dict(row) for p,row in self._trees[key].items()}

    def verify(self, repository, artifact, reference):
        if (not repository or repository.get('project_id')!=artifact.project_id or
            repository.get('repository')!=artifact.repository):
            raise ValueError('Offline source repository identity mismatch')
        path=self._repository_path(repository)
        result=self._checker.verify_source(path,repository['origin'],reference.model_dump(),
            artifact.model_dump(),self._cache,self.tree(repository,artifact.commit_id))
        if result['status'] not in {'VERIFIED_LOCAL_GIT','VERIFIED_RECOVERY_CACHE'}:
            raise ValueError('Offline source verification failed: '+result['status'])
        return {**reference.model_dump(),'repository':artifact.repository,'project_id':artifact.project_id,
            'origin':repository['origin'],**{k:v for k,v in result.items() if k!='quote'}}


def validate_reviews(store, cases, forms, check_git=True, *, source_policy=None):
    if source_policy is not None and (not check_git or type(source_policy) is not OfflineReviewSourcePolicy):
        raise ValueError('Explicit offline policy requires source verification and a validated policy instance')
    reviewed = [ReviewedChangeCase.model_validate(c) for c in cases]
    reviewers = [ReviewerForm.model_validate(f) for f in forms]
    if len(reviewers) != 2 or len({f.reviewer_id.strip() for f in reviewers}) != 2:
        raise ValueError('Two distinct independent reviewer forms are required')
    if not all(f.independent_of_pipeline_author is True for f in reviewers):
        raise ValueError('Independent-author attestations are required')
    ids = [c.case_id for c in reviewed]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate adjudicated case IDs')
    expected = set(ids)
    for form in reviewers:
        observed = [r.case_id for r in form.cases]
        if len(observed) != len(set(observed)) or set(observed) != expected:
            raise ValueError('Reviewer case sets differ from adjudication')
    receipts=[]
    for case in reviewed:
        if {x.strip() for x in case.reviewer_ids} != {f.reviewer_id.strip() for f in reviewers}:
            raise ValueError('Adjudication reviewer identities do not match the forms')
        refs = list(case.evidence)
        refs += [o.source for o in case.obligations]
        refs += [e for o in case.obligations for e in o.evidence]
        refs += [e for f in reviewers for c in f.cases if c.case_id == case.case_id for e in c.evidence]
        repo = store.get('repositories', case.repository)
        for ref in refs:
            row = store.get('artifacts', digest(ref.artifact_id, ref.commit_id))
            if not row:
                raise ValueError('Review references an unavailable artifact version')
            artifact = Artifact.model_validate({k: v for k, v in row.items() if k != 'id'})
            if (artifact.repository != case.repository or ref.commit_id not in {case.base_commit, case.head_commit}
                or artifact.file_path != ref.file or artifact.content_hash != ref.content_hash
                or ref.start_line < artifact.start_line or ref.end_line > artifact.end_line):
                raise ValueError('Review evidence scope, hash or line range differs from the source')
            if check_git:
                if source_policy is not None:
                    receipts.append({'case_id':case.case_id,**source_policy.verify(repo,artifact,ref)})
                    continue
                if not repo or not Path(repo['path']).exists():
                    raise ValueError('Pinned repository cache is required for Git source verification')
                quote = '\n'.join(artifact.content.splitlines()[ref.start_line-artifact.start_line:ref.end_line-artifact.start_line+1])
                excerpt = {'evidence_id': digest(ref.artifact_id, ref.commit_id, str(ref.start_line), str(ref.end_line), quote),
                           'artifact_id': ref.artifact_id, 'repository': artifact.repository, 'project_id': artifact.project_id,
                           'file': ref.file, 'commit': ref.commit_id, 'commit_id': ref.commit_id,
                           'content_hash': ref.content_hash, 'start_line': ref.start_line, 'end_line': ref.end_line, 'quote': quote}
                if verify_git([excerpt], [artifact], repo['path']):
                    raise ValueError('Independent Git blob check failed')
    result={'status': 'REVIEW_ATTESTATIONS_VALIDATED', 'split': 'development',
            'cases': [{**c.model_dump(), 'adjudicated': True} for c in reviewed],
            'reviewer_ids': [f.reviewer_id for f in reviewers],
            'verification_scope': 'Git blobs and stored artifacts' if check_git else 'Stored artifact versions only',
            'reviewer_identity_authentication': 'ATTESTED_NOT_INDEPENDENTLY_AUTHENTICATED',
            'semantic_prediction_review': 'NOT_PERFORMED; annotation evidence review does not review future model claims',
            'quality_target_91': 'NOT_EVALUATED'}
    if source_policy is not None:
        result.update(verification_scope='Pinned Git trees, exact local/recovery blobs and stored artifacts',
            source_policy=dict(source_policy.provenance),source_verification_receipts=receipts)
    return result
