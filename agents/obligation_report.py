"""Attach reviewed development obligations to a new immutable saved report."""
from copy import deepcopy
import hashlib
from pathlib import Path
from consistency.obligations import ObligationRegistry, assess_registry
from evaluation.change_cases import SourceReference
from evaluation.review_intake import OfflineReviewSourcePolicy
from ingestion.models import Artifact, digest, now
from rag.evidence import evidence, verify, verify_git


def attach_obligations(store, parent_run_id, payload, *, source_policy=None):
    if source_policy is not None and type(source_policy) is not OfflineReviewSourcePolicy:
        raise ValueError('Validated offline source policy required')
    parent = store.get('analysis_runs', parent_run_id)
    if not parent or parent.get('status') != 'COMPLETED' or not parent.get('changes'):
        raise ValueError('A completed source investigation is required')
    if parent.get('obligation_review') is not None:
        raise ValueError('Attach each registry revision to the original investigation')
    registry = ObligationRegistry.model_validate(payload)
    if registry.repository != parent['repository'] or registry.parser_identity != parent['project_id']:
        raise ValueError('Registry must match the investigation repository and parser identity')
    allowed = {parent['base_commit'], parent['commit_id']}
    repo = store.get('repositories', parent['repository'])
    if not repo:
        raise ValueError('Pinned repository is required')
    artifacts = {}

    def get_artifact(aid, commit):
        key = aid, commit
        if key not in artifacts:
            row = store.get('artifacts', digest(aid, commit))
            if not row:
                raise ValueError('Missing report source artifact')
            a = Artifact.model_validate({k: v for k, v in row.items() if k != 'id'})
            if (a.repository != parent['repository'] or a.project_id != parent['project_id'] or
                a.artifact_id!=aid or a.commit_id!=commit):
                raise ValueError('Report source scope mismatch')
            artifacts[key] = a
        return artifacts[key]

    def verify_report(items, phase):
        for e in items:
            if e['commit'] not in allowed:raise ValueError('Report evidence outside pinned comparison')
            get_artifact(e['artifact_id'],e['commit'])
        errors=verify_git(items,list(artifacts.values()),repo['path']) if source_policy is None else verify(items,list(artifacts.values()))
        if errors:raise ValueError(phase+' report failed pinned source verification')
        receipts=[]
        if source_policy is not None:
            for e in items:
                ref=SourceReference(artifact_id=e['artifact_id'],commit_id=e['commit'],file=e['file'],
                    content_hash=e['content_hash'],start_line=e['start_line'],end_line=e['end_line'])
                receipts.append({'evidence_id':e['evidence_id'],**source_policy.verify(repo,get_artifact(e['artifact_id'],e['commit']),ref)})
        return receipts

    parent_receipts=verify_report(parent.get('evidence', []),'Original')
    assessment = assess_registry(store, registry.model_dump(), parent['commit_id'],source_policy=source_policy)
    parent_payload = {k: v for k, v in parent.items() if k != 'id'}
    fingerprint = digest(parent_payload)
    rid = digest('obligation-report-v1', parent_run_id, fingerprint, assessment['registry_fingerprint'])
    binding=None
    if source_policy is not None:
        binding={'source_policy':deepcopy(source_policy.provenance),
            'attachment_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        rid=digest('obligation-report-offline-v1',parent_run_id,fingerprint,assessment['registry_fingerprint'],binding)
    existing = store.get('analysis_runs', rid)
    if existing:
        if source_policy is not None:
            if existing.get('derivation',{}).get('source_binding')!=binding:
                raise ValueError('Existing report source binding differs')
            verify_report(existing.get('evidence',[]),'Derived')
        return existing
    report = deepcopy(parent_payload)
    report.update(run_id=rid, created_at=now())
    report['derivation'] = {'policy': 'obligation-report-v1', 'parent_run_id': parent_run_id,
        'parent_report_fingerprint': fingerprint, 'registry_fingerprint': assessment['registry_fingerprint'],
        'new_model_calls': 0, 'historical_report_modified': False}
    if source_policy is not None:
        report['derivation'].update(policy='obligation-report-offline-v1',source_binding=binding)
    report['obligation_review'] = assessment
    report['obligation_registry'] = registry.model_dump()
    report['config']['obligation_policy'] = 'reviewed-obligation-registry-v1'
    report['model']['obligation_assessment_scope'] = 'NOT_REVIEWED_BY_THIS_HISTORICAL_MODEL_OUTPUT'
    report['parent_investigation_metrics'] = report['metrics']
    report['metrics'] = {'new_model_calls': 0, 'semantic_grounding_rate': None,
                         'independent_quality_gate': 'NOT_EVALUATED'}
    by_id = {e['evidence_id']: e for e in report.get('evidence', [])}

    def excerpt(ref):
        if ref['commit_id'] not in allowed:
            return None  # stale assessments remain visible without foreign-comparison citations
        a = get_artifact(ref['artifact_id'], ref['commit_id'])
        e = evidence(a, 'reviewed-obligation-source')
        quote = '\n'.join(a.content.splitlines()[ref['start_line']-a.start_line:ref['end_line']-a.start_line+1])
        e.update(start_line=ref['start_line'], end_line=ref['end_line'], quote=quote,
                 evidence_id=digest(a.artifact_id, a.commit_id, str(ref['start_line']), str(ref['end_line']), quote),
                 revision_role='base-and-head' if parent['base_commit'] == parent['commit_id'] else ('head' if a.commit_id == parent['commit_id'] else 'base'))
        by_id.setdefault(e['evidence_id'], e)
        return e['evidence_id']

    for row in assessment['assessments']:
        refs = [row['source'], *row['counterevidence']]
        if row['search_scope']: refs += row['search_scope']['evidence']
        row['evidence_ids'] = sorted({eid for ref in refs if (eid := excerpt(ref))})
    for finding in assessment['findings']:
        f = deepcopy(finding)
        f.update(rule='reviewed-unmet-test-obligation', reason='Reviewer-attested unmet active test obligation within an explicit reviewed search boundary; semantic support remains unverified.',
                 confidence=None, confidence_calibrated=False,
                 evidence_ids=sorted({excerpt(ref) for ref in f['evidence']}))
        report['findings'].append(f)
    report['evidence'] = list(by_id.values())
    derived_receipts=verify_report(report['evidence'],'Derived')
    if source_policy is not None:
        report['derivation']['source_verification_receipts']={'parent':parent_receipts,'derived':derived_receipts}
    report['trajectory'].append({'role': 'Verifier', 'tool': 'attach-reviewed-obligation-registry-v1', 'status': 'SUCCESS', 'new_model_calls': 0})
    report['limitations'].append('Obligation judgments and search completeness are reviewer attestations within declared boundaries; reviewer identity and semantic correctness are not independently authenticated. No tests executed by attachment.')
    # One immutable record owns the derived evidence/findings. Do not modify graph,
    # artifact, parent finding or model records, or imply a fresh investigation ran.
    store.put('analysis_runs', rid, report)
    return store.get('analysis_runs', rid)
