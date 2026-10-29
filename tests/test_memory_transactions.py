from concurrent.futures import ThreadPoolExecutor
from threading import Event
from database.store import Store


def test_memory_reader_cannot_rollback_an_inflight_writer():
    store = Store('sqlite:///:memory:')
    started, release, reading = Event(), Event(), Event()
    table = store.tables['projects']
    def writer():
        with store.connection(write=True) as connection:
            connection.execute(table.insert().values(id='p', payload={'id': 'p', 'name': 'kept'}))
            started.set()
            assert release.wait(5)
    def reader():
        reading.set()
        return store.get('projects', 'p')
    with ThreadPoolExecutor(max_workers=2) as executor:
        writing = executor.submit(writer)
        assert started.wait(5)
        result = executor.submit(reader)
        assert reading.wait(5)
        release.set()
        writing.result(timeout=5)
        assert result.result(timeout=5)['name'] == 'kept'
    assert store.get('projects', 'p')['name'] == 'kept'
