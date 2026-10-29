"""Explain the imported project inventory and declared purpose at one revision."""
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import urlencode
import re
from fastapi import HTTPException
from rag.evidence import evidence, verify


def matches(question):
    return bool(re.search(r'\b(explain|describe|define|understand|overview|architecture|what (is|does))\b', question, re.I)
                and re.search(r'\b(project|repository|repo|codebase|architecture)\b', question, re.I))


def describe(store, repository, commit):
    artifacts = store.artifacts(repository, commit)
    if not artifacts:
        raise HTTPException(404, 'Repository snapshot not found')
    files = sorted((a for a in artifacts if not a.symbol), key=lambda a: a.file_path)
    roles = Counter(a.artifact_type for a in artifacts)
    folders = Counter(PurePosixPath(a.file_path).parts[0] if '/' in a.file_path else '(root)' for a in files)
    readmes = [a for a in files if PurePosixPath(a.file_path).name.lower().startswith('readme')]
    manifests = [a for a in files if PurePosixPath(a.file_path).name in
                 {'package.json', 'pyproject.toml', 'requirements.txt', 'pom.xml', 'build.gradle', 'Cargo.toml', 'Package.swift'}]
    apis = [a for a in artifacts if a.artifact_type == 'api']
    tests = [a for a in artifacts if a.artifact_type in {'test', 'test_method'}]
    selected = {a.artifact_id: a for a in readmes[:2] + manifests[:2] + apis[:2] + tests[:2]}
    if not selected:
        selected = {a.artifact_id: a for a in files[:4]}
    items = [evidence(a, 'project-overview', max_lines=30) for a in selected.values()]
    if verify(items, artifacts):
        raise HTTPException(409, 'Project overview evidence failed verification')
    citations = [{**e, 'revision_role': 'selected-snapshot', 'support_level': 'SOURCE_MATCH_ONLY',
                  'artifact_role': selected[e['artifact_id']].artifact_type,
                  'source_url': '/api/artifacts/' + e['artifact_id'] + '?' + urlencode({'repository': repository, 'commit_id': commit})}
                 for e in items]
    text = (f'Snapshot {commit[:12]} contains {len(files)} imported files and '
            f'{sum(bool(a.symbol) for a in artifacts)} extracted symbols. '
            f'It records {len(apis)} API artifacts, {len(tests)} test artifacts and {roles["requirement"]} requirement artifacts.\n'
            + 'Top folders: ' + ', '.join(f'{name} ({count} files)' for name, count in folders.most_common(8)) + '.\n')
    if readmes:
        text += 'Project documentation excerpt (' + readmes[0].file_path + '):\n' + '\n'.join(readmes[0].content.splitlines()[:12]) + '\n'
    text += ('Open the cited documentation and manifests for the declared purpose, setup and dependencies. '
             'This inventory covers imported files. Complete semantic, dependency and test coverage is not established. '
             'Select a saved investigation to explain base/head changes, findings and dependency paths.')
    return {'intent': 'PROJECT_OVERVIEW', 'answer': text, 'decision': {'decision': 'ANSWERED'},
            'citations': citations, 'retrieved_evidence': [], 'validation_error': None,
            'provider': 'deterministic-project-overview', 'inference_calls': 0,
            'source_verified': True, 'semantic_entailment_verified': False,
            'verification_scope': 'Excerpts against stored artifacts; Git blobs not re-read by this endpoint',
            'confidence_note': 'Imported snapshot inventory and documentation excerpt; no model was called.',
            'repository': repository, 'commit_id': commit,
            'claims': [{'text': text, 'basis': 'SCOPED_INVENTORY_AND_DOCUMENTATION', 'support_level': 'RECORDED_FACT',
                        'evidence_ids': [e['evidence_id'] for e in items]}],
            'project_map': {'imported_files': len(files), 'artifact_roles': dict(roles), 'top_folders': dict(folders),
                            'manifests': [a.file_path for a in manifests], 'coverage': 'IMPORTED_SNAPSHOT_ONLY'}}
