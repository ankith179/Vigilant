"""Prepare blank review forms or import completed forms against immutable source evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.store import Store
from evaluation.review_intake import OfflineReviewSourcePolicy, ReviewerForm, validate_reviews
from evaluation.change_cases import ReviewedChangeCase


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare', type=Path, help='Unlabelled pilot/case JSON to prepare two blank forms')
    p.add_argument('--adjudication', type=Path)
    p.add_argument('--reviewer-forms', type=Path, nargs=2)
    p.add_argument('--database', type=Path, default=ROOT / 'data/vigilant.db')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verified-source-cache', type=Path, help='Explicit opt-in exact recovery manifest; never relax source checks')
    p.add_argument('--source-recovery-queue', type=Path, help='Checksum-matching queue required with --verified-source-cache')
    a = p.parse_args()
    if bool(a.verified_source_cache)!=bool(a.source_recovery_queue) or (a.prepare and a.verified_source_cache):
        p.error('Use both cache/queue paths for completed review intake only')
    if a.output.exists():
        p.error('Output exists; preserve prior reviewer work')
    if a.prepare:
        data = json.loads(a.prepare.read_text())
        cases = data['cases'] if isinstance(data, dict) else data
        a.output.mkdir(parents=True)
        (a.output / 'adjudication-template.json').write_text(json.dumps({'split': 'pilot', 'held_out': False,
            'label_status': 'UNLABELLED', 'cases': cases}, indent=2) + '\n')
        (a.output / 'adjudication-schema.json').write_text(json.dumps(ReviewedChangeCase.model_json_schema(), indent=2) + '\n')
        for number in (1, 2):
            form = {'reviewer_id': None, 'independent_of_pipeline_author': None,
                    'cases': [{'case_id': c['case_id'], 'consistency_label': None, 'trace_links': None,
                               'affected_artifact_ids': None, 'rationale': None, 'evidence': []} for c in cases]}
            (a.output / f'reviewer-{number}.json').write_text(json.dumps(form, indent=2) + '\n')
        (a.output / 'reviewer-schema.json').write_text(json.dumps(ReviewerForm.model_json_schema(), indent=2) + '\n')
        (a.output / 'README.md').write_text('''# Independent review handoff

The two reviewer files intentionally contain null judgments. Each reviewer must
work independently using the pinned source packets and classification rubric.
Do not copy the model prediction or equate a patch with complete impact truth.
Record actual canonical artifact IDs, commits, hashes, line spans and rationale.
An adjudicator then completes the ReviewedChangeCase records separately.

Run scripts/import_independent_reviews.py with --adjudication, both
--reviewer-forms, the live source database and a fresh --output file. Intake
checks the source references against stored versions and pinned Git blobs.
It records reviewer attestations, not authenticated identities. It exports
development labels; it does not freeze a final test or review prediction claims.

The pilot uses repository names such as express. Before adjudication, import the
needed source revisions under the current parser identity and use the returned
canonical repository ID and artifact IDs in the completed adjudication. Do not
copy the repository name into a canonical ID field. Missing source versions are
rejected, not silently imported or assumed correct. From the project root:

python scripts/reindex_repository.py data/repos/express --project review-development --revisions BASE_SHA HEAD_SHA

The command uses VIGILANT_DB if supplied. Preserve the original pilot packets in
reports/audit-v2-20261023/change-pilot; use the packet matching each case ID and
inspect its Git revisions. This development pilot must not become the final test.

After completing the two reviews and separate adjudication, run:
python scripts/import_independent_reviews.py --adjudication COMPLETED.json --reviewer-forms reviewer-1.json reviewer-2.json --database data/vigilant.db --output NEW-development-labels.json
''')
        print('Prepared blank forms for', len(cases), 'cases; no labels created.')
        return
    if not a.adjudication or not a.reviewer_forms or not a.database.is_file():
        p.error('Completed adjudication, two reviewer forms and an existing source database are required')
    data = json.loads(a.adjudication.read_text())
    cases = data['cases'] if isinstance(data, dict) else data
    forms = [json.loads(path.read_text()) for path in a.reviewer_forms]
    policy=OfflineReviewSourcePolicy(a.verified_source_cache,a.source_recovery_queue,ROOT) if a.verified_source_cache else None
    store = Store('sqlite:///' + str(a.database.resolve()))
    try:
        result = validate_reviews(store, cases, forms, source_policy=policy)
    finally:
        store.engine.dispose()
    result['source_files'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in [a.adjudication, *a.reviewer_forms]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print('Validated', len(cases), 'attested development annotations; independent final evaluation remains separate.')


if __name__ == '__main__':
    main()
