import copy
import pytest
from pydantic import ValidationError
from database.store import Store
from ingestion.models import artifact, digest
from evaluation.review_intake import validate_reviews


def fixture_forms(a):
    ref = dict(artifact_id=a.artifact_id, commit_id=a.commit_id, file=a.file_path, content_hash=a.content_hash,
               start_line=a.start_line, end_line=a.end_line)
    case = dict(case_id='fixture', repository=a.repository, change_family='authored-fixture', base_commit=a.commit_id, head_commit=a.commit_id,
                change_intent='fixture', consistency_label='UNCERTAIN', affected_artifact_ids=[], trace_links=[],
                reviewed_negative_links=[], obligations=[], obligation_inventory='UNKNOWN', unknowns=['Implementation absent'],
                evidence=[ref], reviewer_ids=['reviewer-a', 'reviewer-b'], adjudicator_id='adjudicator',
                adjudication_rationale='Insufficient implementation evidence', semantic_support='INSUFFICIENT', semantic_reviewer_id='semantic-reviewer')
    assessment = dict(case_id='fixture', consistency_label='UNCERTAIN', trace_links=[], affected_artifact_ids=[], rationale='No implementation', evidence=[ref])
    forms = [dict(reviewer_id=who, independent_of_pipeline_author=True, cases=[assessment]) for who in case['reviewer_ids']]
    return case, forms


def test_intake_requires_real_judgments_distinct_reviewers_and_matching_sources():
    store = Store('sqlite:///:memory:')
    a = artifact('p', 'r', 'head', 'req.md', 'requirement', '', 'Return one')
    store.put('artifacts', digest(a.artifact_id, a.commit_id), a.model_dump())
    case, forms = fixture_forms(a)
    result = validate_reviews(store, [case], forms, check_git=False)
    assert result['split'] == 'development' and result['quality_target_91'] == 'NOT_EVALUATED'
    duplicate = copy.deepcopy(forms); duplicate[1]['reviewer_id'] = 'reviewer-a'
    with pytest.raises(ValueError): validate_reviews(store, [case], duplicate, check_git=False)
    malformed = copy.deepcopy(forms); malformed[0]['independent_of_pipeline_author'] = 'true'
    with pytest.raises(ValidationError): validate_reviews(store, [case], malformed, check_git=False)
    bad = copy.deepcopy(case); bad['evidence'][0]['end_line'] = 2
    with pytest.raises(ValueError): validate_reviews(store, [bad], forms, check_git=False)
    blank = copy.deepcopy(forms); blank[0]['cases'][0]['consistency_label'] = None
    with pytest.raises(ValidationError): validate_reviews(store, [case], blank, check_git=False)


def test_intake_rechecks_pinned_git_instead_of_trusting_database(tmp_path):
    from tests.test_integration import repository
    from ingestion.service import import_repository
    repo = tmp_path / 'repo'
    repository(repo)
    store = Store('sqlite:///:memory:')
    result = import_repository(store, repo)
    a = next(a for a in store.artifacts(result['repository'], result['commit_id']) if not a.symbol)
    case, forms = fixture_forms(a)
    assert validate_reviews(store, [case], forms)['verification_scope'] == 'Git blobs and stored artifacts'
    # A self-consistent forged stored artifact must still fail against its Git blob.
    a.content = a.content.replace('return 1', 'return 9')
    a.content_hash = digest(a.content)
    store.put('artifacts', digest(a.artifact_id, a.commit_id), a.model_dump(), replace=True)
    case, forms = fixture_forms(a)
    with pytest.raises(ValueError, match='Git blob'):
        validate_reviews(store, [case], forms)
