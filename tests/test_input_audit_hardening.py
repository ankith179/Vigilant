import json
import shlex
import subprocess
import sys

import pytest
from agents.evidence_first import InterpretationProvider
from ingestion.git import git
from llm.providers import LLMProvider, uncertain


class CountingProvider(LLMProvider):
    name = 'ollama'
    requests = 0
    calls = 0

    def investigation_request(self, question, evidence):
        self.requests += 1
        return super().investigation_request(question, evidence)

    def complete(self, messages):
        self.calls += 1
        return uncertain('Missing contract',schema_version=2).model_dump_json(), {'input_tokens':1200}


def packet():
    return dict(base_commit='base', head_commit='head', verified_change_facts=[],
                review_candidates=[], evidence_gaps=[])


def evidence(size=1200):
    return [dict(evidence_id=f'id{i}', artifact_id='artifact', pair_id='renamed-pair',
                 content_hash=f'hash{i}', commit=revision, file='api.py', quote='x'*size,
                 start_line=1, end_line=1, retrieval_method='changed-hunk')
            for i, revision in enumerate(('base', 'head'))]


def test_final_budget_keeps_pairs_atomic_and_counts_accurate():
    engine = CountingProvider()
    wrapper = InterpretationProvider(engine, packet())
    # Find the boundary where only one version fits; no half-pair may survive.
    for size in range(600, 3001, 100):
        messages, selected, aliases, _ = wrapper.investigation_request('Check contract', evidence(size))
        payload = json.loads(messages[-1]['content'])
        assert len(selected) in (0, 2)
        assert payload['evidence_included'] == len(selected) == len(aliases)
        assert payload['evidence_omitted'] == 2-len(selected)


def test_audit_describes_one_actual_request():
    engine = CountingProvider()
    result = InterpretationProvider(engine, packet()).investigate('Check contract', evidence(10))
    assert engine.requests == 1
    assert engine.calls == 1
    assert result['input_audit']['selected_evidence']['E1']['evidence_id'] == 'id0'


def test_no_evidence_never_calls_engine():
    engine = CountingProvider()
    result = InterpretationProvider(engine, packet()).investigate('Check contract', [])
    assert engine.calls == 0
    assert result['validation_error']
    assert result['decision']['decision'] == 'UNCERTAIN'


@pytest.mark.parametrize('driver', ['external', 'textconv'])
def test_git_reads_do_not_execute_diff_helpers(tmp_path, driver):
    subprocess.run(['git','init',str(tmp_path)], check=True, capture_output=True)
    for key, value in [('user.email','fixture@example.invalid'), ('user.name','Fixture')]:
        git(tmp_path, 'config', key, value)
    (tmp_path/'sample.txt').write_text('before\n')
    (tmp_path/'.gitattributes').write_text('*.txt diff=fixture\n')
    git(tmp_path, 'add', '.'); git(tmp_path, 'commit', '-m', 'base')
    (tmp_path/'sample.txt').write_text('after\n')
    git(tmp_path, 'add', '.'); git(tmp_path, 'commit', '-m', 'head')
    marker = tmp_path/'executed'
    helper = tmp_path/'helper.py'
    helper.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("executed")\n')
    command = shlex.join([sys.executable, str(helper)])
    git(tmp_path, 'config', 'diff.external' if driver=='external' else 'diff.fixture.textconv', command)
    diff = git(tmp_path, 'diff', 'HEAD~1', 'HEAD')
    assert not marker.exists()
    assert '-before' in diff and '+after' in diff


def test_blind_packets_do_not_export_answers():
    from scripts.audit_diagnostic_inputs import blind_packet, selected_items
    source = evidence(10)
    report = {'base_commit':'base','commit_id':'head','changes':{'files':[]},
              'expected_status':'SECRET_ORACLE','findings':[{'reason':'SECRET_REASON'}]}
    packet = blind_packet('SECRET_CASE_NAME', report, source, [])
    assert 'SECRET_' not in json.dumps(packet)
    duplicate = {**source[0],'artifact_id':'another-symbol','evidence_id':'another-id'}
    excerpt = {'evidence_id':'E1','commit':'base','file':'api.py','excerpt':source[0]['quote']}
    selected, errors = selected_items({'evidence':[excerpt]}, [source[0],duplicate])
    assert selected == [] and errors[0]['matches'] == 2


@pytest.mark.parametrize('url',[
    'http://github.com/org/repo.git','https://localhost/org/repo.git',
    'https://github.com.attacker.invalid/org/repo.git','https://user@github.com/org/repo.git',
    'https://github.com:8443/org/repo.git','https://github.com/org/repo.git?redirect=1',
    'https://github.com/org/repo.git#fragment','https://github.com/','https://github.com\\@127.0.0.1/org/repo.git'
])
def test_public_repository_url_policy_rejects_internal_and_ambiguous_targets(url):
    from backend.repository_import import validate_public_repository_url
    with pytest.raises(ValueError,match='public HTTPS GitHub or GitLab'):
        validate_public_repository_url(url)


def test_public_clone_disables_redirects_checkout_and_user_git_helpers(monkeypatch,tmp_path):
    import backend.repository_import as importer
    calls={}
    class FailedClone:
        returncode=1
        def poll(self):return 1
    def popen(command,**kwargs):
        calls.update(command=command,environment=kwargs['env'],cwd=kwargs['cwd']);return FailedClone()
    monkeypatch.setattr(importer.subprocess,'Popen',popen)
    monkeypatch.setenv('GIT_ASKPASS','untrusted-helper')
    monkeypatch.setenv('GIT_CONFIG_COUNT','1')
    monkeypatch.setenv('GIT_CONFIG_KEY_0','protocol.ext.allow')
    monkeypatch.setenv('GIT_CONFIG_VALUE_0','always')
    with pytest.raises(ValueError,match='Clone failed'):
        importer.clone_repository('https://github.com/example/project.git',tmp_path/'repo')
    command=calls['command'];environment=calls['environment']
    assert 'http.followRedirects=false' in command
    assert 'protocol.ext.allow=never' in command
    assert '--no-checkout' in command
    assert environment['GIT_CONFIG_NOSYSTEM']=='1' and environment['GIT_CONFIG_GLOBAL'].endswith('empty.gitconfig')
    assert environment['GIT_CEILING_DIRECTORIES']==calls['cwd'] and 'clone-' in calls['cwd']
    assert environment['GIT_TERMINAL_PROMPT']=='0'
    assert not any(key.startswith(('GIT_CONFIG_KEY_','GIT_CONFIG_VALUE_')) for key in environment)
    assert 'GIT_ASKPASS' not in environment and 'GIT_CONFIG_COUNT' not in environment


def test_import_api_rejects_nonpublic_urls_before_clone(monkeypatch):
    from backend.app import create_app
    from database.store import Store
    from fastapi.testclient import TestClient
    import backend.repository_import as importer
    store=Store('sqlite:///:memory:')
    monkeypatch.setattr(importer,'clone_repository',lambda *args,**kwargs:pytest.fail('Rejected URL reached git clone'))
    try:
        with TestClient(create_app(store)) as client:
            for url in ('http://127.0.0.1/repo.git','https://github.com.attacker.invalid/org/repo.git',
                        'https://user@github.com/org/repo.git','https://github.com/org/repo.git?x=1'):
                response=client.post('/api/repositories/import',json={'url':url})
                assert response.status_code==400 and 'public HTTPS' in response.json()['detail']
    finally:store.engine.dispose()
