"""Frontend boundaries: complete pagination, exact graph limits and provenance."""
from fastapi.testclient import TestClient
from backend.app import create_app
from database.store import Store
from ingestion.models import artifact,digest


def test_pagination_ends_at_exact_multiple_and_preserves_scope():
    store = Store('sqlite:///:memory:')
    for i in range(7):
        store.put('changes', str(i), {'repository': 'r', 'commit_id': 'c', 'kind': str(i)})
    store.put('changes', 'other', {'repository': 'other', 'commit_id': 'c'})
    with TestClient(create_app(store)) as client:
        params = {'repository': 'r', 'commit_id': 'c', 'limit': 3}
        pages = [client.get('/api/changes', params={**params, 'offset': i}).json()
                 for i in (0, 3, 6)]
        assert [r['kind'] for p in pages for r in p['items']] == list(map(str, range(7)))
        assert [p['next_offset'] for p in pages] == [3, 6, None]
        exact = client.get('/api/changes', params={**params, 'limit': 7}).json()
        assert exact['returned'] == 7 and exact['has_more'] is False
        assert client.get('/api/changes', params={**params, 'commit_id': 'missing'}).json()['items'] == []
        assert client.get('/api/changes?offset=-1').status_code == 422


def test_graph_and_artifact_lookup_do_not_scan_snapshot(monkeypatch):
    store = Store('sqlite:///:memory:')
    for repo, commit in [('r', 'c'), ('r', 'old'), ('other', 'c')]:
        for name in ['a', 'b', 'c']:
            aid = repo + name
            row = {'artifact_id': aid, 'repository': repo, 'commit_id': commit}
            store.put('graph_nodes', digest(aid, commit), row)
            store.put('artifacts', digest(aid, commit), row)
        for source, target in [('a', 'b'), ('b', 'c')]:
            store.put('graph_edges', digest(repo, commit, source, target), {
                'source_artifact': repo+source, 'target_artifact': repo+target,
                'repository': repo, 'commit_id': commit, 'relation_type': 'CALLS'})
    store.put('graph_nodes', 'commit-node', {'artifact_id': 'commit-node',
              'artifact_type': 'commit', 'repository': 'r', 'commit_id': 'c'})
    store.put('graph_edges', 'zz-commit-edge', {'source_artifact': 'commit-node',
              'target_artifact': 'ra', 'repository': 'r', 'commit_id': 'c', 'relation_type': 'MODIFIES'})
    original = store.rows
    def no_snapshot_scan(table, **kwargs):
        assert table not in {'graph_nodes', 'artifacts'}
        return original(table, **kwargs)
    monkeypatch.setattr(store, 'rows', no_snapshot_scan)
    with TestClient(create_app(store)) as client:
        params = {'repository': 'r', 'commit_id': 'c'}
        result = client.get('/api/graph', params={**params, 'limit': 3}).json()
        assert len(result['nodes']) == 4 and result['truncated'] is False
        assert any(node['artifact_type'] == 'commit' for node in result['nodes'] if 'artifact_type' in node)
        result = client.get('/api/graph', params={**params, 'limit': 1}).json()
        assert len(result['edges']) == 1 and len(result['nodes']) == 2 and result['truncated'] is True
        assert all(n['repository'] == 'r' and n['commit_id'] == 'c' for n in result['nodes'])
        assert client.get('/api/artifacts/ra', params=params).json()['commit_id'] == 'c'
        assert client.get('/api/artifacts/ra', params={**params, 'repository': 'other'}).status_code == 404
        assert client.get('/api/artifacts/ra', params={**params, 'commit_id': 'missing'}).status_code == 404


def test_batched_primary_keys_cross_sqlite_parameter_boundary():
    store = Store('sqlite:///:memory:')
    for i in range(805):
        store.put('graph_nodes', str(i), {'artifact_id': str(i)})
    assert len(store.get_many('graph_nodes', map(str, range(805)))) == 805
    assert store.get_many('graph_nodes', []) == []
    assert len(store.get_many('graph_nodes', ['1', '1', 'missing'])) == 1


def test_chat_returns_verified_context_without_claiming_model_support():
    store = Store('sqlite:///:memory:')
    source = artifact('p','repo','commit','src/service.py','source_file','','def fetch_user():\n    return "active"')
    store.put('artifacts', digest(source.artifact_id, source.commit_id), source.model_dump())
    payload = {'repository':'repo','commit_id':'commit','question':'Where is fetch_user defined?'}
    with TestClient(create_app(store)) as client:
        response = client.post('/api/chat', json=payload)
        assert response.status_code == 200
        result = response.json()
        assert result['provider'] == 'none'
        assert result['source_verified'] is True
        assert result['semantic_entailment_verified'] is False
        assert result['citations'] == []
        assert result['retrieved_evidence'][0]['quote'] == source.content
        assert result['retrieved_evidence'][0]['content_hash'] == source.content_hash
        assert 'No model was called' in result['answer']
        assert client.post('/api/chat', json={**payload,'commit_id':'missing'}).status_code == 404
        assert client.post('/api/chat', json={**payload,'history':[{'role':'user','content':'x'}]*7}).status_code == 422


def test_chat_maps_model_citations_to_verified_excerpts(monkeypatch):
    import llm.providers
    store = Store('sqlite:///:memory:')
    source = artifact('p','repo','commit','src/service.py','source_file','','def fetch_user():\n    return "active"')
    store.put('artifacts', digest(source.artifact_id, source.commit_id), source.model_dump())

    class StubProvider:
        name = 'test-provider'
        def investigate(self, question, evidence):
            return {'provider':self.name,'validation_error':None,'decision':{
                'decision':'AFFECTED','consistency':'AFFECTED','confidence':0.5,
                'evidence_ids':[evidence[0]['evidence_id']],
                'affected_artifacts':[source.artifact_id],'reason':'The cited function matches the question.',
                'uncertainty':''}}

    monkeypatch.setattr(llm.providers,'provider',lambda _:StubProvider())
    payload={'repository':'repo','commit_id':'commit','question':'Where is fetch_user defined?','model':'local'}
    with TestClient(create_app(store)) as client:
        result=client.post('/api/chat',json=payload).json()
    assert result['provider']=='test-provider'
    assert result['citations'][0]['artifact_id']==source.artifact_id
    assert result['citations'][0]['quote']==source.content
    assert result['semantic_entailment_verified'] is False
