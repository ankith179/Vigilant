"""Offline reviewed-obligation intake; subject repository code is never executed."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from consistency.obligations import assess_registry
from database.store import Store
from evaluation.review_intake import OfflineReviewSourcePolicy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verified-source-cache',type=Path)
    parser.add_argument('--source-recovery-queue',type=Path)
    args = parser.parse_args()
    if bool(args.verified_source_cache)!=bool(args.source_recovery_queue):parser.error('Both cache and queue paths are required')
    if args.output.exists():parser.error('Output exists; preserve prior assessments')
    policy=OfflineReviewSourcePolicy(args.verified_source_cache,args.source_recovery_queue,Path(__file__).resolve().parents[1]) if args.verified_source_cache else None
    store=Store(args.database_url)
    try:result = assess_registry(store, json.loads(args.registry.read_text()), args.commit,source_policy=policy)
    finally:store.engine.dispose()
    # Preserve previous assessments; use a new result path after every reviewed revision.
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(args.output), 'findings': len(result['findings']), 'quality_target_91': 'NOT_EVALUATED'}))


if __name__ == '__main__':
    main()
