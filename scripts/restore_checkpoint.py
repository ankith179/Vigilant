"""Repair only project-owned checkout locations after extracting a checkpoint."""
from pathlib import Path
from contextlib import closing
import json, sqlite3, subprocess, os
ROOT = Path(__file__).resolve().parents[1]

def require_database(path):
    """A GitHub source archive may contain an LFS pointer instead of SQLite bytes."""
    with Path(path).open('rb') as stream:
        header = stream.read(64)
    if header.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise ValueError(f'Unresolved Git LFS database: {path}. Fetch its exact object with git lfs pull, or use a complete project archive. Do not overwrite a live database with an older snapshot.')
    if not header.startswith(b'SQLite format 3\x00'):
        raise ValueError(f'Not a SQLite database: {path}')

def main():
    destination=ROOT/'data/vigilant.db'
    if destination.exists():require_database(destination)
    for parent in [ROOT/'data/raw', ROOT/'data/repos']:
        for repo in parent.iterdir() if parent.exists() else []:
            if (repo/'.git').is_dir():
                for entry in (repo/'.git/worktrees').glob('*') if (repo/'.git/worktrees').exists() else []:
                    worktree = ROOT/'data/changebench'/entry.name
                    if worktree.exists():
                        (worktree/'.git').write_text('gitdir: '+entry.as_posix()+'\n', encoding='utf-8', newline='\n')
                        (entry/'gitdir').write_text((worktree/'.git').as_posix()+'\n', encoding='utf-8', newline='\n')
                subprocess.run(['git', '-C', str(repo), 'worktree', 'repair'], check=True)
    if not destination.exists():
        source=ROOT/'data/snapshots/vigilant.db'
        if not source.exists():source=ROOT/'data/snapshots/changebench.db'
        if source.exists():restore_database(source,destination)
    if destination.exists():
        with sqlite3.connect(destination) as conn:
            for identity,payload in conn.execute('SELECT id,payload FROM repositories').fetchall():
                row=json.loads(payload);old=row.get('path','').replace('\\','/')
                if '/data/' in old:
                    suffix=Path(old.split('/data/',1)[1])
                    if suffix.is_absolute() or '..' in suffix.parts:raise ValueError('Unsafe stored repository path')
                    row['path']=str(ROOT/'data'/suffix)
                    conn.execute('UPDATE repositories SET payload=? WHERE id=?',(json.dumps(row),identity))
    cache=ROOT/'data/embedding-cache.sqlite'
    if not cache.exists() and (ROOT/'data/snapshots/embedding-cache.sqlite').exists():restore_database(ROOT/'data/snapshots/embedding-cache.sqlite',cache)
    print('Recorded database restored if absent; repository paths repaired.')

def restore_database(source,destination):
    """Preserve frozen snapshots; include committed WAL data in an atomic backup."""
    require_database(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.restore-tmp')
    try:
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(temporary)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid database snapshot')
            dst.execute('PRAGMA journal_mode=DELETE')
        os.replace(temporary,destination)
    finally:temporary.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
