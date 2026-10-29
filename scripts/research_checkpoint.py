"""Make a small validated overlay while long real-project experiments run."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('UPDATED_STATUS.md', 'PROJECT_STATE.json', 'RESUME.md', 'RECOVERY_SOURCES.json', 'backend/app.py',
         'backend/project_overview.py', 'frontend/src/Chat.jsx', 'scripts/test_evolution.py',
         'scripts/research_checkpoint.py', 'tests/test_test_evolution.py', 'tests/test_project_overview.py',
         'docs/IMMEDIATE_EXECUTION.md', 'scripts/prefetch_test_evolution.py', 'scripts/recover_test_evolution.py',
         'frontend/src/main.jsx', 'scripts/test_frontend.cjs', 'scripts/audit_test_evolution.py', 'docs/FINAL_STATUS.md',
         'requirements-core.txt', 'vigilant.py', 'data/snapshots/pilot-review-20261024.db',
         'data/snapshots/pilot-review-recovered-20261024.db')
DIRECTORIES = ('reports/lineage-tools-20261025', 'reports/lineage-observations-20261025', 'reports/lineage-audit-20261025', 'change_analysis', 'reports/partial-report-delivery-20261025', 'reports/job-controls-20261025', 'reports/master-audit-20261025', 'reports/partial-report-ui-20261025', 'reports/partial-report-api-20261025', 'reports/staged-report-20261025', 'reports/staged-graph-20261025', 'reports/staged-inspection-20261025', 'reports/staged-comparison-20261025', 'reports/staged-source-reader-20261025', 'reports/staged-routing-20261025', 'reports/offline-obligation-report-20261025', 'data/raw/TEBench', 'data/test-evolution/TEBench', 'experiments/test-evolution',
               'reports/realworld-20261024', 'reports/completion-20261024', 'frontend/dist',
               'ingestion', 'knowledge_graph', 'database', 'backend', 'frontend/src', 'tests', 'docs', 'scripts',
               'evaluation', 'agents', 'consistency', 'investigation', 'reports/obligation-source-policy-20261025', 'reports/offline-review-policy-20261025', 'reports/review-source-readiness-20261024', 'reports/recovered-review-20261024', 'reports/verified-cache-maps-20261024', 'reports/local-source-recovery-20261024', 'reports/canonical-review-20261024', 'reports/pilot-store-20261024', 'reports/pilot-artifacts-20261024', 'reports/search-drafts-20261024', 'reports/search-provenance-20261024',
               'reports/obligations-20261024', 'reports/obligation-integration-20261024', 'submission/research-20261024')


def main():
    files = {ROOT / name for name in FILES if (ROOT / name).is_file()}
    files.update(p for name in DIRECTORIES for p in (ROOT / name).rglob('*')
                 if p.is_file() and p.suffix not in {'.pending','.pyc'} and '__pycache__' not in p.parts
                 and not (p.suffix == '.png' and any(part.startswith('browser') for part in p.parts)))
    destination = ROOT.parent / 'VIGILANT-realworld-work.zip'
    pending = destination.with_suffix('.pending')
    manifest = {}
    with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            data = p.read_bytes(); name = 'VIGILANT/' + p.relative_to(ROOT).as_posix()
            z.writestr(name, data); manifest[name] = hashlib.sha256(data).hexdigest()
        z.writestr('VIGILANT/REALWORLD-MANIFEST.json', json.dumps(manifest, indent=2))
    with zipfile.ZipFile(pending) as z:
        if z.testzip() is not None:
            raise ValueError('Checkpoint integrity failure')
    pending.replace(destination)
    print(json.dumps({'path': str(destination), 'files': len(manifest), 'bytes': destination.stat().st_size,
                      'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
