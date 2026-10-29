from fastapi.testclient import TestClient
from backend.app import create_app
from database.store import Store
from ingestion.models import digest
from ingestion.parsers import extract


def test_project_overview_uses_only_selected_revision_and_linked_sources():
    store = Store('sqlite:///:memory:')
    for repo, commit, text in [('r', 'head', 'Documented purpose'), ('other', 'head', 'FOREIGN_SECRET'), ('r', 'base', 'OLD_PURPOSE')]:
        for a in extract('p', repo, commit, 'README.md', text):
            store.put('artifacts', digest(a.artifact_id, a.commit_id), a.model_dump())
    with TestClient(create_app(store)) as client:
        r = client.post('/api/chat', json={'repository': 'r', 'commit_id': 'head', 'question': 'Explain this project'})
        assert r.status_code == 200
        r = r.json()
        assert r['intent'] == 'PROJECT_OVERVIEW' and r['inference_calls'] == 0
        assert 'FOREIGN_SECRET' not in str(r) and 'OLD_PURPOSE' not in str(r)
        assert 'Documented purpose' in r['answer']
        for source in r['citations']:
            assert source['repository'] == 'r' and source['commit'] == 'head'
            assert client.get(source['source_url']).status_code == 200
        assert client.get('/api/project-overview?repository=r&commit_id=absent').status_code == 404
