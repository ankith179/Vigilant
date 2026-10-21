"""Restore missing controlled Git worktrees without rerunning or relabeling results."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.git import git, revision
from scripts.run_change_scenarios import mutate


def restore(contract):
    case = contract['id']
    if not re.fullmatch(r'[0-9]{2}-[a-z-]+', case):
        raise ValueError('Unexpected scenario identifier')
    source = ROOT/('data/raw/rtmx' if contract['repo'] == 'rtmx' else 'data/repos/'+contract['repo'])
    destination = ROOT/'data/changebench'/case
    if destination.exists():
        if revision(destination) != contract['change_commit']:
            raise ValueError('Existing worktree does not match the saved head; refusing to overwrite '+case)
        return {'case': case, 'status': 'PRESERVED', 'commit': contract['change_commit']}
    baseline = revision(source, contract['base_commit'])
    git(source, 'worktree', 'add', '--detach', str(destination), baseline)
    target = destination/contract['file']
    if not target.resolve().is_relative_to(destination.resolve()):
        raise ValueError('Mutation target escapes the controlled worktree')
    mutate(target, contract)
    git(destination, 'add', '--all')
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'VIGILANT ChangeBench',
           'GIT_AUTHOR_EMAIL': 'vigilant@example.invalid',
           'GIT_COMMITTER_NAME': 'VIGILANT ChangeBench',
           'GIT_COMMITTER_EMAIL': 'vigilant@example.invalid',
           'GIT_AUTHOR_DATE': '2026-10-05T00:00:00Z',
           'GIT_COMMITTER_DATE': '2026-10-05T00:00:00Z'}
    subprocess.run(['git', '-c', 'core.hooksPath='+os.devnull, '-c', 'commit.gpgsign=false',
                    '-C', str(destination), 'commit', '-m', case], env=env, check=True, capture_output=True)
    head = revision(destination)
    if head != contract['change_commit']:
        raise ValueError('Restored commit does not match preserved contract: '+case+' '+head)
    return {'case': case, 'status': 'RESTORED_EXACT_HASH', 'commit': head}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case')
    args = parser.parse_args()
    records = []
    for p in sorted((ROOT/'data/changebench').glob('[0-9][0-9]-*.json')):
        if p.stem.endswith('-report'):
            continue
        contract = json.loads(p.read_text())
        if args.case and args.case != contract['id']:
            continue
        result = restore(contract)
        records.append(result)
        print(json.dumps(result), flush=True)
    (ROOT/'reports/changebench-restoration.json').write_text(json.dumps(records, indent=2)+'\n')


if __name__ == '__main__':
    main()
