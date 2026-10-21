"""Create resumable source/data archives and consistent SQLite backups.

Publishing these local archives to persistent storage is a separate host action.
Never copy live SQLite WAL files or partially downloaded models into a checkpoint.
"""
from pathlib import Path
from contextlib import closing
import argparse, datetime, hashlib, json, os, sqlite3, zipfile, tempfile, shutil

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.venv', 'node_modules', '__pycache__', '.pytest_cache', '.cache', '.runtime'}

def backup(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.tmp')
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro', uri=True)) as src, closing(sqlite3.connect(temporary)) as dst:
        if src.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError(f'Invalid SQLite database: {source}')
        src.backup(dst)
        dst.execute('PRAGMA journal_mode=DELETE')
    os.replace(temporary, destination)
    return {'source': str(source), 'snapshot': str(destination.relative_to(ROOT))}

def pack(destination, files):
    manifest = []
    scratch=Path(tempfile.mkdtemp(prefix='vigilant-checkpoint-'))
    staged=scratch/destination.name
    with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            relative = Path('VIGILANT') / path.relative_to(ROOT)
            data = path.read_bytes()
            archive.writestr(relative.as_posix(), data)
            manifest.append({'path': relative.as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        archive.writestr('VIGILANT/ARCHIVE-MANIFEST-' + destination.stem + '.json', json.dumps(manifest, indent=2))
    with zipfile.ZipFile(staged) as archive:
        if archive.testzip() is not None:raise ValueError('Checkpoint ZIP integrity failure')
    pending=destination.with_suffix('.pending')
    shutil.copyfile(staged,pending)
    os.replace(pending,destination)
    shutil.rmtree(scratch)
    return {'path': str(destination), 'files': len(manifest), 'bytes': destination.stat().st_size,
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', default='/tmp/vigilant-runtime')
    parser.add_argument('--source-only', action='store_true')
    parser.add_argument('--preserve-snapshots', action='store_true', help='Package existing immutable snapshots without replacing them from live databases')
    args = parser.parse_args()
    snapshots, failures = [], []
    runtime = Path(args.runtime)
    runtime_databases = [p for p in runtime.glob('*') if p.suffix in {'.db', '.sqlite'}]
    for path in ([] if args.source_only or args.preserve_snapshots else runtime_databases):
        try:
            snapshots.append(backup(path, ROOT / 'data/snapshots' / path.name))
        except Exception as exc:
            failures.append(str(exc))
    if not args.source_only and not args.preserve_snapshots and (ROOT / 'data/embedding-cache.sqlite').exists() and not (runtime/'embedding-cache.sqlite').exists():
        try:
            snapshots.append(backup(ROOT / 'data/embedding-cache.sqlite', ROOT / 'data/snapshots/embedding-cache.sqlite'))
        except Exception as exc:
            failures.append(str(exc))
    record = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'snapshots': snapshots, 'backup_failures': failures,
              'excluded_reproducible_dependencies': ['.venv', 'node_modules', 'model weights', 'package caches'],
              'recovery': 'Read RESUME.md. Source + data archives share a VIGILANT root.'}
    (ROOT / 'CHECKPOINT.json').write_text(json.dumps(record, indent=2))
    source, data = [], []
    for path in ROOT.rglob('*'):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(p in EXCLUDED for p in rel.parts) or path.is_symlink():
            continue
        # Browser screenshots are internal QA, not requested deliverables.
        if rel.as_posix().startswith('reports/frontend/') and path.suffix == '.png':
            continue
        if path.name.startswith('ARCHIVE-MANIFEST-') or path.name == 'PACKAGE-MANIFEST.json' or path.suffix in {'.tmp', '.pending'}:
            continue
        if rel.as_posix().startswith('data/models/'):
            continue
        if (path.suffix in {'.db', '.sqlite'} or path.name.endswith(('-wal', '-shm'))) and 'snapshots' not in rel.parts:
            continue
        # A failed, incomplete worktree snapshot is reproduced from Git instead.
        target = data if rel.as_posix().startswith(('data/raw/', 'data/repos/', 'data/snapshots/')) or (rel.as_posix().startswith('data/changebench/') and len(rel.parts)>3) else source
        target.append(path)
    index_path = ROOT.parent / 'VIGILANT-checkpoint-index.json'
    previous = {}
    if args.source_only and index_path.exists():
        try:
            previous = json.loads(index_path.read_text())
        except (ValueError, OSError):
            previous = {}
    result = {'source': pack(ROOT.parent / 'VIGILANT-source.zip', source), 'backup_failures': failures}
    if args.source_only:
        # A source checkpoint must not erase the identity of the independently
        # preserved data archive. Keep only a complete prior record whose file
        # still exists; otherwise omit it and force explicit restoration.
        data_record = previous.get('data')
        if isinstance(data_record, dict) and all(data_record.get(key) for key in ('path', 'bytes', 'sha256')):
            if Path(data_record['path']).is_file():
                result['data'] = data_record
    else:
        result['data'] = pack(ROOT.parent / 'VIGILANT-data.zip', data)
    index_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
