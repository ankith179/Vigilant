"""Exercise checksum-pinned staged reads; no source import, jobs, graphs or labels."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from investigation.staged import StagedSourceReader,file_sha256


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite staged-reader audit')
    database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    index=ROOT/'reports/verified-cache-maps-20261024/maps/index.json'
    staging=ROOT/'reports/recovered-review-20261024/STAGING.json'
    rows={};statuses=Counter();dispositions=Counter();artifacts=0;write_rejected=False
    with StagedSourceReader(database,index,staging) as reader:
        binding=dict(reader.binding)
        counts_before={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in ['artifacts','analysis_runs','graph_nodes','graph_edges']}
        try:reader.connection.execute('delete from artifacts')
        except sqlite3.OperationalError:write_rejected=True
        if not write_rejected:raise ValueError('Reader unexpectedly allowed a write')
        # Any subprocess means the reader escaped its promised no-Git/no-model path.
        with patch('subprocess.run',side_effect=AssertionError('Staged reader must not spawn tools')):
            for (repository,commit),s in reader.routes.items():
                key=repository+'/'+commit
                try:
                    snapshot=reader.snapshot(repository,commit);coverage=snapshot['coverage']
                    rows[key]={'status':'VALIDATED_PARTIAL_SNAPSHOT','project_id':snapshot['project_id'],
                        'coverage':coverage,'provenance':snapshot['provenance']}
                    statuses.update(coverage['file_statuses']);dispositions.update(coverage['search_dispositions']);artifacts+=len(snapshot['artifacts'])
                except Exception as exc:rows[key]={'status':'FAILED_RETAINED','files':s['files'],'error':type(exc).__name__+': '+str(exc)[:300]}
        counts_after={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in counts_before}
        if counts_before!=counts_after:raise ValueError('Frozen staged records changed')
        cases=len(reader.index['cases'])
    if file_sha256(database)!=binding['database_sha256']:raise ValueError('Frozen staged database changed')
    result={'policy':'validated-staged-source-reader-audit-v1','snapshots':rows,'snapshot_denominator':len(rows),
        'failed_snapshots':sum(r['status']=='FAILED_RETAINED' for r in rows.values()),'cases':cases,
        'artifact_versions_validated':artifacts,'file_statuses':dict(statuses),'search_dispositions':dict(dispositions),
        'binding':binding,'write_attempt_rejected':write_rejected,'store_counts_unchanged':counts_after,
        'source_fetches':0,'imports':0,'reparses':0,'model_calls':0,'independent_labels_created':0,
        'raw_git_verification':'NOT_PERFORMED_BY_READER; existing source-policy receipts remain separate',
        'actual_staged_investigations':'NOT_RUN; comparison/investigation adapters not implemented',
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='snapshots'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output)))
