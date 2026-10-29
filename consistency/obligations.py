"""Reviewed, source-backed development registry; no automatic obligation discovery."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from evaluation.change_cases import SourceReference, VerificationObligation
from ingestion.models import Artifact, digest
from rag.evidence import evidence, verify, verify_git
from consistency.search_inventory import SearchInventory,validate_inventory


class SearchScope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reviewer_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    completeness: Literal['REVIEWED_COMPLETE', 'PARTIAL', 'UNKNOWN']
    # This is an explicit reviewed boundary, not a claim about the entire repository.
    applicable_artifact_ids: list[str] = Field(min_length=1)
    searched_artifact_ids: list[str]
    unknown_regions: list[str]
    evidence: list[SourceReference] = Field(min_length=1)
    git_inventory: SearchInventory | None = None

    @model_validator(mode='after')
    def complete_scope(self):
        if not self.reviewer_id.strip() or not self.rationale.strip():
            raise ValueError('Nonblank search reviewer and rationale required')
        if self.completeness == 'REVIEWED_COMPLETE' and self.unknown_regions:
            raise ValueError('Unknown search regions prohibit reviewed completeness')
        for ids in (self.applicable_artifact_ids, self.searched_artifact_ids):
            if len(ids) != len(set(ids)) or any(not x.strip() for x in ids):
                raise ValueError('Search scope IDs must be distinct and nonempty')
        return self


class ObligationRevision(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    sequence: int = Field(ge=1)
    previous_fingerprint: str | None
    commit_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    obligation: VerificationObligation
    search_scope: SearchScope | None = None
    counterevidence: list[SourceReference]
    # Only explicit reviewed cause IDs group findings. Similarity is not causation.
    root_cause_id: str | None = Field(default=None, min_length=1)
    root_cause_evidence: list[SourceReference] = Field(default_factory=list)

    @model_validator(mode='after')
    def current_source(self):
        if not self.reviewer_id.strip() or not self.rationale.strip():
            raise ValueError('Nonblank review and rationale required')
        o = self.obligation
        if (not o.obligation_id.strip() or not o.requirement.strip() or not o.acceptance_criterion.strip()
            or len(o.applicable_artifact_ids) != len(set(o.applicable_artifact_ids))):
            raise ValueError('Obligation identity, criterion and distinct applicable IDs required')
        refs = [o.source, *o.evidence, *self.counterevidence, *self.root_cause_evidence]
        if self.search_scope:
            refs += self.search_scope.evidence
            if self.search_scope.completeness != o.test_search_coverage:
                raise ValueError('Search completeness differs from obligation judgment')
            if self.search_scope.git_inventory and self.search_scope.git_inventory.commit_id != self.commit_id:
                raise ValueError('Search inventory must match obligation revision')
        if any(r.commit_id != self.commit_id for r in refs):
            raise ValueError('Revision evidence must reference its pinned commit')
        if self.root_cause_id and not self.root_cause_evidence:
            raise ValueError('Root-cause grouping requires reviewed source evidence')
        return self


def revision_fingerprint(revision):
    payload = revision.model_dump()
    # Preserve fingerprints of histories created before optional Git enumeration.
    if payload.get('search_scope') and payload['search_scope'].get('git_inventory') is None:
        payload['search_scope'].pop('git_inventory', None)
    return digest('obligation-revision-v1', payload)


class ObligationRegistry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    repository: str = Field(min_length=1)
    parser_identity: str = Field(min_length=1)
    inventory: Literal['REVIEWED', 'INCOMPLETE', 'UNKNOWN']
    histories: list[list[ObligationRevision]]

    @model_validator(mode='after')
    def append_only_history(self):
        seen = set()
        for history in self.histories:
            if not history:
                raise ValueError('Empty obligation history')
            oid = history[0].obligation.obligation_id
            if oid in seen:
                raise ValueError('Duplicate obligation history')
            seen.add(oid)
            previous = None
            for sequence, revision in enumerate(history, 1):
                if (revision.sequence != sequence or revision.previous_fingerprint != previous
                    or revision.obligation.obligation_id != oid):
                    raise ValueError('Broken obligation history chain')
                previous = revision_fingerprint(revision)
        return self


def assess_registry(store, payload, commit_id, *, check_git=True, source_policy=None):
    if source_policy is not None:
        from evaluation.review_intake import OfflineReviewSourcePolicy
        if not check_git or type(source_policy) is not OfflineReviewSourcePolicy:
            raise ValueError('Offline policy requires pinned source verification')
    registry = ObligationRegistry.model_validate(payload)
    repo = store.get('repositories', registry.repository)
    assessments, groups = [], {};receipts=[]

    def artifact_at(aid, commit):
        row = store.get('artifacts', digest(aid, commit))
        if not row:
            raise ValueError('Unavailable obligation artifact version')
        a = Artifact.model_validate({k: v for k, v in row.items() if k != 'id'})
        if a.artifact_id != aid or a.commit_id != commit:
            raise ValueError('Stored obligation artifact identity/revision mismatch')
        if a.repository != registry.repository or a.project_id != registry.parser_identity:
            raise ValueError('Registry repository/parser identity mismatch')
        return a

    def validate_ref(ref):
        a = artifact_at(ref.artifact_id, ref.commit_id)
        item = evidence(a)
        quote = '\n'.join(a.content.splitlines()[ref.start_line-a.start_line:ref.end_line-a.start_line+1])
        item.update(file=ref.file, content_hash=ref.content_hash, start_line=ref.start_line,
                    end_line=ref.end_line, quote=quote,
                    evidence_id=digest(a.artifact_id, a.commit_id, str(ref.start_line), str(ref.end_line), quote))
        if check_git and not repo:
            raise ValueError('Pinned Git repository required')
        errors = verify([item], [a]) if source_policy is not None or not check_git else verify_git([item], [a], repo['path'])
        if errors:
            raise ValueError('Obligation source verification failed: ' + '; '.join(errors))
        if source_policy is not None:
            receipts.append({'obligation_id':revision.obligation.obligation_id,'revision_sequence':revision.sequence,
                **source_policy.verify(repo,a,ref)})

    for history in registry.histories:
        enumerations = {}
        for revision in history:
            o = revision.obligation
            refs = [o.source, *o.evidence, *revision.counterevidence, *revision.root_cause_evidence]
            if revision.search_scope:
                refs += revision.search_scope.evidence
                for aid in revision.search_scope.searched_artifact_ids:
                    artifact_at(aid, revision.commit_id)
            for aid in o.applicable_artifact_ids:
                artifact_at(aid, revision.commit_id)
            for ref in refs:
                validate_ref(ref)
            scope = revision.search_scope
            if scope and scope.git_inventory:
                if not check_git or not repo:
                    raise ValueError('Machine search enumeration requires pinned Git validation')
                enumerations[revision.sequence] = validate_inventory(repo['path'], scope.git_inventory,
                    artifact_at, scope.searched_artifact_ids, scope.completeness == 'REVIEWED_COMPLETE',
                    source_policy=source_policy,repository=repo)
        r = history[-1]; o = r.obligation; scope = r.search_scope
        blockers = []
        if r.commit_id != commit_id: blockers.append('STALE_REVISION')
        if registry.inventory != 'REVIEWED': blockers.append('INVENTORY_NOT_REVIEWED')
        if o.lifecycle != 'ACTIVE': blockers.append('LIFECYCLE_' + o.lifecycle)
        if o.verification_kind != 'TEST': blockers.append('NON_TEST_OBLIGATION')
        if o.satisfaction != 'UNMET': blockers.append('SATISFACTION_' + o.satisfaction)
        if not o.applicable_artifact_ids: blockers.append('NO_APPLICABLE_ARTIFACTS')
        if scope is None or scope.completeness != 'REVIEWED_COMPLETE': blockers.append('SEARCH_NOT_REVIEWED_COMPLETE')
        if scope and set(scope.applicable_artifact_ids) != set(o.applicable_artifact_ids): blockers.append('SEARCH_SCOPE_MISMATCH')
        if r.counterevidence: blockers.append('COUNTEREVIDENCE_REQUIRES_REVIEW')
        status = 'MISSING_TEST' if not blockers else 'NOT_ESTABLISHED'
        enumeration = enumerations.get(r.sequence)
        row = {'obligation_id': o.obligation_id, 'revision_fingerprint': revision_fingerprint(r),
               'status': status, 'blockers': blockers, 'lifecycle': o.lifecycle,
               'satisfaction': o.satisfaction, 'source': o.source.model_dump(),
               'search_scope': scope.model_dump() if scope else None,
               'counterevidence': [e.model_dump() for e in r.counterevidence],
               'root_cause_id': r.root_cause_id, 'reviewer_id': r.reviewer_id,
               'search_enumeration': enumeration or {'status':'NOT_MACHINE_ENUMERATED','basis':'reviewer attestation only'}}
        assessments.append(row)
        if status == 'MISSING_TEST':
            key = digest('reviewed-obligation-cause-v1', registry.repository, commit_id,
                         ['cause', r.root_cause_id] if r.root_cause_id else ['obligation', o.obligation_id])
            group = groups.setdefault(key, {'finding_id': key, 'status': status,
                'obligation_ids': [], 'revision_fingerprints': [], 'root_cause_id': r.root_cause_id,
                'evidence': [], 'affected_artifacts': [], 'method': 'reviewed-obligation-registry-v1',
                'assessment_basis': 'reviewer-attested-unmet-obligation-with-reviewed-search-boundary',
                'semantic_entailment_verified': False, 'test_execution': 'NOT_RUN'})
            group['obligation_ids'].append(o.obligation_id)
            group['revision_fingerprints'].append(revision_fingerprint(r))
            for ref in [o.source, *o.evidence, *scope.evidence, *r.root_cause_evidence]:
                if ref.model_dump() not in group['evidence']: group['evidence'].append(ref.model_dump())
            group['affected_artifacts'] = sorted(set(group['affected_artifacts'] + o.applicable_artifact_ids))
    registry_payload = registry.model_dump()
    for history in registry_payload['histories']:
        for row in history:
            if row.get('search_scope') and row['search_scope'].get('git_inventory') is None:
                row['search_scope'].pop('git_inventory', None)
    result={'policy': 'reviewed-obligation-registry-v1', 'commit_id': commit_id,
            'registry_fingerprint': digest(registry_payload), 'assessments': assessments,
            'findings': list(groups.values()), 'inventory': registry.inventory,
            'source_verification': 'PINNED_GIT_AND_STORED_ARTIFACTS' if check_git else 'STORED_ARTIFACTS_ONLY',
            'review_authentication': 'ATTESTED_NOT_INDEPENDENTLY_AUTHENTICATED',
            'scope': 'development; explicit reviewed boundary only; not whole-repository coverage',
            'quality_target_91': 'NOT_EVALUATED'}
    if source_policy is not None:result.update(source_verification='PINNED_TREE_EXACT_LOCAL_OR_SCOPED_CACHE_AND_STORED_ARTIFACTS',
        source_policy=dict(source_policy.provenance),source_verification_receipts=receipts)
    return result
