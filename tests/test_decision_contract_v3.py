import pytest
from ingestion.models import DecisionV3, FactSource, FactsV3, SourcedFact, legacy_to_v3
from agents.decision_rules import decide, apply_llm_guard

def src(rev='HEAD', role='implementation', name='ev'):
    return FactSource(revision=rev,commit_id=rev,path=f'{name}.py',start_line=1,end_line=3,
        content_hash='a'*64,extraction_method='fixture-parser',artifact_role=role,evidence_id=name)

def known(value, role='implementation', rev='HEAD', name='ev'):
    return SourcedFact(value=value,sources=[src(rev,role,name)])

def facts(**values):
    data={'evidence_sufficient':known(True,name='scope')}
    data.update(values)
    return FactsV3(**data)

def full_head():
    return known(True,role='requirement',name='req'),known(True,role='implementation',name='impl'),known(True,role='test',name='test')

def test_fact_provenance_is_mandatory_and_revision_scoped():
    with pytest.raises(ValueError,match='revision-scoped provenance'):
        SourcedFact(value=True)
    with pytest.raises(ValueError,match='Unknown facts require a reason'):
        SourcedFact(value=None)
    with pytest.raises(ValueError,match='Invalid revision evidence source'):
        FactSource(revision='HEAD',commit_id='h',path='../escape.py',start_line=2,end_line=1,
            content_hash='a'*64,extraction_method='parser',evidence_id='x')

def test_r0_unknown_or_insufficient_evidence_abstains_on_all_axes():
    out=decide(facts(evidence_sufficient=known(False,name='incomplete')))
    assert (out.trace,out.consistency,out.test_obligation)==('UNCERTAIN','UNCERTAIN','UNVERIFIED')
    assert out.rule_id=='R0_INSUFFICIENT_EVIDENCE' and not out.needs_llm

def test_r1_deleted_and_referenced_is_broken_and_inconsistent():
    out=decide(facts(symbol_deleted_at_head=known(True,rev='BASE',name='base'),
        renamed_to=known(False,rev='BASE',name='rename-scan'),
        head_refs_symbol=known(True,role='test',name='head-call')))
    assert out.trace=='BROKEN_TRACE' and out.consistency=='INCONSISTENT'
    assert out.rule_id=='R1_DELETED_STILL_REFERENCED'

@pytest.mark.parametrize('rename,ref,expected',[
    (True,True,'LINKED'),(False,False,'UNCERTAIN')])
def test_r1_negative_twins_renamed_or_no_remaining_reference(rename,ref,expected):
    out=decide(facts(symbol_deleted_at_head=known(True,rev='BASE',name='base'),
        renamed_to=known({'path':'new.py'} if rename else False,rev='BASE',name='rename'),
        head_refs_symbol=known(ref,role='test',name='call')))
    assert out.trace==expected
    if rename: assert out.rule_id=='R_RENAME_CANDIDATE'

def test_r2a_comment_only_without_marker_is_not_behavioral_equivalence():
    out=decide(facts(change_kind=known('COMMENT_ONLY',rev='BASE',name='comments'),
        comment_has_contract_markers=known(False,rev='BASE',name='marker-scan')))
    assert out.consistency=='NO_ASSURANCE_IMPACT' and not out.needs_llm
    assert 'not inferred' in out.rationale

def test_r2b_comment_marker_requires_semantic_review():
    out=decide(facts(change_kind=known('COMMENT_ONLY',rev='BASE',name='comments'),
        comment_has_contract_markers=known(True,rev='BASE',name='marker-scan')))
    assert out.needs_llm and 'comment_may_carry_contract' in out.blockers

@pytest.mark.parametrize('authority,expected',[
    ('NORMATIVE','INCONSISTENT'),('INFORMATIONAL','POTENTIAL_INCONSISTENCY'),
    ('NOT_ESTABLISHED','POTENTIAL_INCONSISTENCY')])
def test_r3_default_conflict_respects_contract_authority(authority,expected):
    out=decide(facts(doc_default=known('303',rev='BASE',name='docs'),
        sig_default=known('307',name='sig'),
        contract_authority=known(authority,role='contract',name='authority')))
    assert out.consistency==expected and out.rule_id=='R3_DOC_SIGNATURE_DEFAULT_CONFLICT'

def test_r3_equal_defaults_do_not_create_conflict():
    out=decide(facts(doc_default=known('307',rev='BASE',name='docs'),
        sig_default=known('307',name='sig'),
        contract_authority=known('INFORMATIONAL',role='contract',name='authority')))
    assert out.rule_id=='R7_LLM_SEMANTIC_RESIDUE'

def test_r4_normative_default_match_requires_all_head_artifact_roles():
    req,impl,test=full_head()
    out=decide(facts(default_changed_base_to_head=known(True,rev='BASE',name='diff'),
        contract_authority=known('NORMATIVE',role='contract',name='authority'),
        requirement_default=known('50',role='requirement',name='req-default'),
        sig_default=known('50',role='implementation',name='head-signature'),
        has_head_evidence_for_req_impl_test=SourcedFact(value=True,sources=[*req.sources,*impl.sources,*test.sources])))
    assert out.consistency=='CONSISTENT' and out.blockers==[]

def test_r4_unknown_authority_is_only_potential():
    out=decide(facts(default_changed_base_to_head=known(True,rev='BASE',name='diff'),
        sig_default=known('50',name='head-signature')))
    assert out.consistency=='POTENTIAL_INCONSISTENCY' and 'contract_authority_not_normative' in out.blockers

def test_r5_route_change_detects_candidate_mismatch_but_alias_is_negative_twin():
    mismatch=decide(facts(route_changed=known(True,rev='BASE',name='route-diff'),
        route_alias_kept=known(False,name='head-routes'),
        consumer_exists=known(True,role='consumer',name='consumer'),
        consumer_matches_new_route=known(False,role='consumer',name='compare')))
    assert mismatch.consistency=='POTENTIAL_INCONSISTENCY' and mismatch.rule_id=='R5_ROUTE_CONSUMER_MISMATCH'
    alias=decide(facts(route_changed=known(True,rev='BASE',name='route-diff'),
        route_alias_kept=known(True,name='head-routes'),
        consumer_exists=known(True,role='consumer',name='consumer'),
        consumer_matches_new_route=known(False,role='consumer',name='compare')))
    assert alias.rule_id=='R7_LLM_SEMANTIC_RESIDUE'
    migrated=decide(facts(route_changed=known(True,rev='BASE',name='route-diff'),
        route_alias_kept=known(False,name='head-routes'),
        consumer_exists=known(True,role='consumer',name='consumer'),
        consumer_matches_new_route=known(True,role='consumer',name='compare')))
    assert migrated.consistency!='POTENTIAL_INCONSISTENCY'

def test_r5_missing_consumer_inventory_is_a_blocker():
    out=decide(facts(route_changed=known(True,rev='BASE',name='route-diff'),
        route_alias_kept=known(False,name='head-routes')))
    assert 'route_consumer_unverified' in out.blockers and out.needs_review

@pytest.mark.parametrize('explicit,covered,expected',[
    (False,None,'UNVERIFIED'),(True,True,'SATISFIED'),(True,False,'UNSATISFIED')])
def test_test_obligation_deleted_test_outcomes(explicit,covered,expected):
    kw={'test_deleted':known(True,rev='BASE',role='test',name='deleted-test'),
        'obligation_explicit':known(explicit,role='contract',name='obligation')}
    if covered is not None:kw['other_test_covers_path']=known(covered,role='test',name='coverage-review')
    assert decide(facts(**kw)).test_obligation==expected

def test_r6_stale_consumer_is_not_a_hard_consistency_proof():
    out=decide(facts(stale_consumer=known(True,role='consumer',name='stale')))
    assert out.trace=='BROKEN_TRACE' and out.consistency=='POTENTIAL_INCONSISTENCY'

def test_consistent_is_rejected_with_any_blocker():
    with pytest.raises(ValueError,match='blockers'):
        DecisionV3(consistency='CONSISTENT',evidence_ids=['head-evidence'],blockers=['unknown_contract'])

def test_unknown_relevant_facts_never_award_consistent():
    out=decide(facts(default_changed_base_to_head=known(True,rev='BASE',name='diff'),
        contract_authority=known('NORMATIVE',role='contract',name='authority'),
        requirement_default=known('50',role='requirement',name='req-default'),
        sig_default=known('50',name='head-signature')))
    assert out.consistency=='UNCERTAIN' and out.blockers

def test_llm_guard_only_runs_for_semantic_residue_and_cannot_override_rules():
    f=facts(change_kind=known('COMMENT_ONLY',rev='BASE',name='comments'),
        comment_has_contract_markers=known(False,rev='BASE',name='marker-scan'))
    d=decide(f)
    llm=DecisionV3(consistency='INCONSISTENT',rationale='proposal')
    assert apply_llm_guard(d,f,llm).consistency=='NO_ASSURANCE_IMPACT'

def test_llm_consistent_requires_full_head_scope_and_valid_head_citations():
    req,impl,test=full_head()
    scope=SourcedFact(value=True,sources=[*req.sources,*impl.sources,*test.sources])
    f=facts(has_head_evidence_for_req_impl_test=scope)
    d=decide(f);llm=DecisionV3(consistency='CONSISTENT',evidence_ids=['req','impl','test'],rationale='supported')
    blocked=apply_llm_guard(d,f,llm,votes_agree=True,valid_head_citations=['req'])
    assert blocked.consistency=='UNCERTAIN' and 'consistent_requires_complete_head_evidence' in blocked.blockers
    allowed=apply_llm_guard(d,f,llm,votes_agree=True,valid_head_citations=['req','impl','test'])
    assert allowed.consistency=='CONSISTENT'

def test_legacy_mapping_preserves_raw_confidence_without_claiming_new_axes():
    legacy={'schema_version':2,'decision':'BROKEN_TRACE','consistency':'UNCERTAIN',
        'confidence':0.95,'evidence_ids':['e1']}
    out=legacy_to_v3(legacy)
    assert out.trace=='BROKEN_TRACE' and out.consistency=='UNCERTAIN'
    assert out.raw_confidence==0.95 and out.blockers


def test_r3_normative_requirement_matching_signature_marks_stale_documentation():
    out=decide(facts(doc_default=known('303',rev='BASE',name='docs'),
        sig_default=known('307',name='sig'),
        requirement_default=known('307',role='requirement',name='required-default'),
        contract_authority=known('NORMATIVE',role='contract',name='authority')))
    assert out.rule_id=='R3_STALE_DOC_AGAINST_NORMATIVE'
    assert out.consistency=='POTENTIAL_INCONSISTENCY' and out.needs_review

def test_r3_symbolic_signature_is_not_compared_as_a_literal():
    out=decide(facts(doc_default=known('307',rev='BASE',name='docs'),
        sig_default=known('status.HTTP_307_TEMPORARY_REDIRECT',name='sig')))
    assert out.rule_id=='R7_LLM_SEMANTIC_RESIDUE'

def test_r4_missing_signature_is_unknown_not_a_contract_violation():
    out=decide(facts(default_changed_base_to_head=known(True,rev='BASE',name='diff'),
        contract_authority=known('NORMATIVE',role='contract',name='authority'),
        requirement_default=known('50',role='requirement',name='required-default')))
    assert out.consistency=='UNCERTAIN' and out.rule_id=='R4_DEFAULT_NONLITERAL'

def test_no_test_change_is_not_applicable_on_test_obligation_axis():
    assert decide(facts()).test_obligation=='NOT_APPLICABLE'

def test_decisive_llm_label_without_valid_citation_abstains():
    f=facts(contract_authority=known('NORMATIVE',role='contract',name='authority'))
    rule=decide(f)
    proposed=DecisionV3(consistency='INCONSISTENT',rationale='claim')
    out=apply_llm_guard(rule,f,proposed,votes_agree=True,valid_head_citations=[])
    assert out.consistency=='UNCERTAIN'
    assert 'decisive_verdict_without_valid_citation' in out.blockers

def test_non_normative_llm_conflict_still_requires_valid_citation():
    f=facts(contract_authority=known('NOT_ESTABLISHED',role='contract',name='authority'))
    rule=decide(f)
    proposed=DecisionV3(consistency='INCONSISTENT',rationale='claim')
    out=apply_llm_guard(rule,f,proposed,votes_agree=True,valid_head_citations=[])
    assert out.consistency=='UNCERTAIN'
    assert 'decisive_verdict_without_valid_citation' in out.blockers
