"""Probe import routing read-only; never start analysis or fabricate reviewed results."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion import service
from ingestion.models import digest
from scripts.prepare_pilot_artifact_maps import local_git


class ReadOnlyProbe:
    def __init__(self,connection):self.connection=connection;self.write_attempts=[]
    def get(self,table,key):
        if table not in {'projects','repositories','commits'}:raise ValueError('Unexpected probe table')
        row=self.connection.execute('select payload from '+table+' where id=?',(key,)).fetchone()
        return json.loads(row[0]) if row else None
    def put(self,table,*args,**kwargs):
        self.write_attempts.append(table);raise AssertionError('Probe forbids all metadata writes')
    def artifacts(self,*args,**kwargs):raise AssertionError('Guard must run before artifact loading or parsing')


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite routing audit')
    database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    before=hashlib.sha256(database.read_bytes()).hexdigest()
    staging=json.loads((ROOT/'reports/recovered-review-20261024/STAGING.json').read_text())
    if before!=staging['database_sha256']:raise ValueError('Frozen source Store differs')
    index_path=ROOT/'reports/verified-cache-maps-20261024/maps/index.json';index=json.loads(index_path.read_text())
    if hashlib.sha256(index_path.read_bytes()).hexdigest()!=staging['source_index_sha256']:raise ValueError('Map index differs')
    rows={};statuses=Counter();metadata_commands=Counter()
    def safe_git(repo,*args,binary=False):
        metadata_commands[args[0]]+=1;raw=local_git(repo,*args)
        return raw if binary else raw.decode('utf-8',errors='replace').strip()
    def safe_revision(repo,rev):return safe_git(repo,'rev-parse','--verify','--end-of-options',rev+'^{commit}')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        initial_counts={t:db.execute('select count(*) from '+t).fetchone()[0] for t in ['analysis_runs','artifacts','graph_nodes','graph_edges']}
        for key,s in index['snapshots'].items():
            alias,commit=key.split('/');repo_path=ROOT/'data/repos'/alias;probe=ReadOnlyProbe(db)
            repository=probe.get('repositories',s['repository']);stored=probe.get('commits',digest(s['repository'],commit))
            origin=safe_git(repo_path,'remote','get-url','origin')
            row={'repository':s['repository'],'project_id':repository['project_id'],'commit_id':commit,
                'files':s['files'],'artifact_versions':s['artifacts'],
                'default_project_repository_matches':digest('vigilant',origin)==s['repository'],
                'explicit_project_repository_matches':digest(repository['project_id'],origin)==s['repository'],
                'recorded_partial_status':stored['review_source_map']['status']}
            statuses.update(stored['review_source_map']['file_statuses'])
            try:
                with patch.object(service,'git',safe_git),patch.object(service,'revision',safe_revision):
                    service.import_repository(probe,repo_path,repository['project_id'],commit,repository_id=s['repository'])
                row['status']='UNEXPECTED_IMPORT_RETURN'
            except ValueError as exc:
                row['status']='EXPECTED_STAGED_IMPORT_REJECTION' if 'Staged source snapshot' in str(exc) else 'FAILED_RETAINED'
                row['reason']=str(exc)[:300]
            except Exception as exc:row.update(status='FAILED_RETAINED',reason=type(exc).__name__+': '+str(exc)[:300])
            row['write_attempts']=probe.write_attempts;rows[key]=row
        final_counts={t:db.execute('select count(*) from '+t).fetchone()[0] for t in initial_counts}
    if initial_counts!=final_counts or hashlib.sha256(database.read_bytes()).hexdigest()!=before:
        raise ValueError('Frozen Store changed')
    result={'policy':'staged-investigation-routing-audit-v1','snapshots':rows,'snapshot_denominator':len(rows),
        'cases':len(index['cases']),'guarded_snapshots':sum(r['status']=='EXPECTED_STAGED_IMPORT_REJECTION' for r in rows.values()),
        'failed_or_unexpected_snapshots':sum(r['status']!='EXPECTED_STAGED_IMPORT_REJECTION' for r in rows.values()),
        'metadata_write_attempts':sum(len(r['write_attempts']) for r in rows.values()),
        'default_project_route_mismatches':sum(not r['default_project_repository_matches'] for r in rows.values()),
        'explicit_project_route_mismatches':sum(not r['explicit_project_repository_matches'] for r in rows.values()),
        'file_statuses_preserved':dict(statuses),'store_counts_unchanged':final_counts,'database_sha256':before,
        'metadata_git_commands':dict(metadata_commands),
        'routing_barriers':['Default project identity differs from staged canonical identity.',
            'Full-import metadata writes occur before the prior-artifact shortcut; staged guard now rejects before writes.',
            'Full workflow still uses Git blob diff/rename detection, size-based coverage and Git-only evidence verification.',
            'Investigation tool exploration still requests size-based inventory; it is not an offline partial-snapshot adapter.',
            'Missing extracted artifacts cannot be interpreted as artifact deletion/addition without coverage-aware comparison.'],
        'source_fetches':0,'reparses':0,'model_calls':0,'independent_labels_created':0,
        'actual_staged_investigations':'NOT_RUN; existing-snapshot workflow adapter not implemented',
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='snapshots'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output)))
