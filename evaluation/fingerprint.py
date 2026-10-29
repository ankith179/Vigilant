"""Fingerprint executable pipeline sources, independent of timestamps and outputs."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES=('agents','backend','change_analysis','consistency','database','evaluation','ingestion',
             'investigation','knowledge_graph','llm','rag','retrieval','traceability','frontend/src')


def pipeline_fingerprint(root=ROOT):
    files=[root/'vigilant.py',root/'requirements-core.txt',root/'requirements.txt',root/'frontend/package-lock.json']
    for directory in DIRECTORIES:
        files.extend(p for p in (root/directory).rglob('*') if p.is_file() and p.suffix in {'.py','.jsx','.js','.css'} and '__pycache__' not in p.parts)
    manifest=[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
    return {'sha256':hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'files':manifest}
