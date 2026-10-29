"""Create an immutable registry-derived report, without rerunning investigation or inference."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.obligation_report import attach_obligations
from database.store import Store
from evaluation.review_intake import OfflineReviewSourcePolicy


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database-url', required=True)
    p.add_argument('--parent-run-id', required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--verified-source-cache',type=Path)
    p.add_argument('--source-recovery-queue',type=Path)
    a = p.parse_args()
    if bool(a.verified_source_cache)!=bool(a.source_recovery_queue):p.error('Both cache and queue paths are required')
    policy=OfflineReviewSourcePolicy(a.verified_source_cache,a.source_recovery_queue,Path(__file__).resolve().parents[1]) if a.verified_source_cache else None
    store=Store(a.database_url)
    try:result = attach_obligations(store, a.parent_run_id, json.loads(a.registry.read_text()),source_policy=policy)
    finally:store.engine.dispose()
    print(json.dumps({'run_id': result['run_id'], 'parent_run_id': a.parent_run_id,
                      'new_model_calls': 0, 'quality_target_91': 'NOT_EVALUATED'}))


if __name__ == '__main__':
    main()
