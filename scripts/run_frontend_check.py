"""Run browser acceptance on an isolated database and a temporary local server."""
from pathlib import Path
from contextlib import closing
import argparse
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=ROOT/'data/snapshots/vigilant.db')
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error('A recorded database snapshot is required.')
    with tempfile.TemporaryDirectory(prefix='vigilant-browser-test-') as tmp:
        database = Path(tmp)/'browser.db'
        with closing(sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(database)) as target, target:
            source.backup(target)
            for identity, payload in target.execute('SELECT id,payload FROM repositories').fetchall():
                row = json.loads(payload)
                if '/data/' in row.get('path', '').replace('\\', '/'):
                    row['path'] = str(ROOT/'data'/row['path'].replace('\\', '/').split('/data/', 1)[1])
                    target.execute('UPDATE repositories SET payload=? WHERE id=?', (json.dumps(row), identity))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = {**os.environ, 'VIGILANT_DB': 'sqlite:///'+str(database),
             'VIGILANT_TEST_URL': f'http://127.0.0.1:{port}',
             'VIGILANT_TEST_MUTATIONS': os.getenv('VIGILANT_TEST_MUTATIONS', '1')}
        with (Path(tmp)/'server.log').open('w+') as log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app:app',
                                       '--host', '127.0.0.1', '--port', str(port)],
                                      cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(150):
                    if server.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        with urllib.request.urlopen(env['VIGILANT_TEST_URL']+'/api/health', timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.2)
                else:
                    raise TimeoutError('Temporary API server did not become ready')
                result = subprocess.run(['node', 'scripts/test_frontend.cjs'], cwd=ROOT, env=env)
                return result.returncode
            finally:
                server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == '__main__':
    raise SystemExit(main())
