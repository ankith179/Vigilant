"""Audit findings are authored diagnostics, never a production parity claim."""
import json
from scripts.audit_artifact_lineage import run, CASES


def test_lineage_audit_retains_gaps_and_exact_source(tmp_path):
    result=run(tmp_path/'audit')
    assert result['cases_verified']==result['case_denominator']==len(CASES)==9
    assert result['production_lineage_implemented'] is False
    assert result['quality_target_91']=='NOT_EVALUATED'
    rows={r['case']:r for r in result['cases']}
    assert rows['missing_revision']['outcome']=='REJECTED_MISSING_REVISION'
    assert rows['duplicate_ordinal_shift']['outcome']=='AMBIGUOUS_ORDINAL_REUSE'
    assert rows['delete_recreate']['delta']['artifacts']==[]
    for row in result['cases']:
        assert row['logical_continuity']=='UNKNOWN'
        assert row['semantic_correctness']=='NOT_ESTABLISHED'
        for role in row.get('scope_source',{}).values():
            assert len(role['commit'])==40
            assert all(a['commit_id']==role['commit'] for a in role['artifacts'])
            assert all(len(f['object_id'])==40 for f in role['inventory'])
    assert json.loads((tmp_path/'audit/result.json').read_text())==result


def test_lineage_fixture_records_are_reproducible(tmp_path):
    # Fixed fixture commits, IDs and observation receipts exclude temp paths/times.
    assert run(tmp_path/'first')==run(tmp_path/'second')
