from agents.evidence_first import analysis_packet
from change_analysis.diff import _change_semantics, detect
from database.store import Store
from ingestion.service import import_repository
from ingestion.models import artifact
from ingestion.parsers import extract
import subprocess


def test_python_comment_only_is_distinguished_from_assertion_change():
    before = 'def test_route():\n    # old note\n    assert get("/items")\n'
    comment = 'def test_route():\n    # updated note\n    assert get("/items")\n'
    assertion = 'def test_route():\n    # old note\n    assert get("/catalog")\n'
    assert _change_semantics('tests/test_api.py', before, comment) == 'COMMENT_ONLY'
    assert _change_semantics('tests/test_api.py', before, assertion) == 'NOT_CLASSIFIED'


def test_comment_only_classification_flows_from_git_diff_into_analysis_packet(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    def git(*args):
        return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
    git('init'); git('config','user.email','test@example.invalid'); git('config','user.name','Test')
    source = repo / 'tests' / 'test_api.py'
    source.parent.mkdir()
    source.write_text('def test_route():\n    # initial comment\n    assert get("/items")\n')
    git('add','.'); git('commit','-m','base')
    store = Store('sqlite:///:memory:')
    base = import_repository(store,repo)
    before = store.artifacts(base['repository'],base['commit_id'])
    source.write_text('def test_route():\n    # edited comment\n    assert get("/items")\n')
    git('commit','-am','comment-only')
    head = import_repository(store,repo)
    after = store.artifacts(head['repository'],head['commit_id'])
    changes = detect(repo,base['commit_id'],head['commit_id'],before,after)
    assert changes['files'][0]['change_semantics'] == 'COMMENT_ONLY'
    packet = analysis_packet(changes,before,after,[])
    assert packet['file_change_facts'][0]['text_changed'] is True
    assert packet['file_change_facts'][0]['change_semantics'] == 'COMMENT_ONLY'


def test_literal_route_comparison_handles_incompatibility_and_alias():
    caller = artifact('p','r','head','client.py','api_caller','get_items','get("/items")',metadata={'method':'GET','route':'/items'})
    catalog = artifact('p','r','head','api.py','api','GET /catalog','route',metadata={'method':'GET','route':'/catalog'})
    changes={'base_commit':'base','head_commit':'head','files':[],'artifacts':[]}
    packet=analysis_packet(changes,[],[catalog,caller],[])
    assert packet['route_compatibility_candidates'][0]['status']=='NO_LITERAL_ROUTE_MATCH_REVIEW_REQUIRED'
    alias=artifact('p','r','head','api.py','api','GET /items','route',metadata={'method':'GET','route':'/items'})
    packet=analysis_packet(changes,[],[catalog,alias,caller],[])
    assert packet['route_compatibility_candidates'][0]['status']=='LITERAL_ROUTE_MATCH_CANDIDATE'
    assert packet['route_compatibility_candidates'][0]['runtime_compatibility_verified'] is False
    assert packet['route_compatibility_candidates'][0]['causal_impact_verified'] is False


def test_default_change_is_reported_without_asserting_contract_violation():
    before=extract('p','r','base','api.py','def list_items(limit=100):\n return limit\n')
    after=extract('p','r','head','api.py','def list_items(limit=50):\n return limit\n')
    old=next(a for a in before if a.symbol=='list_items')
    new=next(a for a in after if a.symbol=='list_items')
    packet=analysis_packet({'base_commit':'base','head_commit':'head','files':[],'artifacts':[{'artifact_id':old.artifact_id,'new_artifact_id':new.artifact_id,'kind':'modified','artifact_type':'function','file':'api.py','symbol':'list_items'}]},before,after,[])
    fact=packet['parameter_default_changes'][0]
    assert fact['base_defaults']==[{'parameter':'limit','expression':'100'}]
    assert fact['head_defaults']==[{'parameter':'limit','expression':'50'}]
    assert fact['contract_authority']=='NOT_ESTABLISHED'
    assert fact['behavioral_effect']=='NOT_EVALUATED'
