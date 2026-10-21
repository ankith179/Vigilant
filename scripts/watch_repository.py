"""Poll one local checkout without fetching remotely."""
import sys, pathlib, time, argparse, json, os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ingestion.git import revision
from agents.workflow import analyze
from database.store import Store


def read_previous(state, repository):
    if not state.exists():
        return revision(repository)
    saved = json.loads(state.read_text())
    if pathlib.Path(saved['repository']).resolve() != repository:
        raise ValueError('Watcher state belongs to another repository; use a separate --state file.')
    return revision(repository, saved['last_commit'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('repository')
    p.add_argument('--interval', type=float, default=5)
    p.add_argument('--model', default='none')
    p.add_argument('--state', default='data/watch-state.json')
    p.add_argument('--once', action='store_true')
    a = p.parse_args()
    repository = pathlib.Path(a.repository).resolve()
    state = pathlib.Path(a.state)
    previous = read_previous(state, repository)
    store = Store()
    while True:
        current = revision(repository)
        if current != previous:
            r = analyze(store, repository, previous, current, model=a.model)
            print(json.dumps({'run_id':r['run_id'], 'commit':current}), flush=True)
            previous = current
        state.parent.mkdir(exist_ok=True, parents=True)
        temporary = state.with_suffix(state.suffix+'.tmp')
        temporary.write_text(json.dumps({'repository':str(repository), 'last_commit':previous}))
        os.replace(temporary, state)
        if a.once:
            break
        time.sleep(max(.2, a.interval))


if __name__ == '__main__':
    main()
