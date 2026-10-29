"""Compare all staged development pairs with retained UNKNOWN outcomes, no gold."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import digest
from investigation.staged import StagedSourceReader,read_json
from investigation.staged_comparison import compare_staged


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite staged comparison audit')
    database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    index=ROOT/'reports/verified-cache-maps-20261024/maps/index.json'
    staging=ROOT/'reports/recovered-review-20261024/STAGING.json'
    _,metadata=read_json(staging);cases=metadata['case_routes']
    if len({c['case_id'] for c in cases})!=len(cases):raise ValueError('Duplicate case ID')
    output.mkdir(parents=True,exist_ok=False);rows={};denominators=Counter();files=Counter();artifacts=Counter()
    with StagedSourceReader(database,index,staging) as reader:
        binding=dict(reader.binding)
        counts_before={t:reader.connection.execute('select count(*) from '+t).fetchone()[0]
            for t in ['artifacts','analysis_runs','graph_nodes','graph_edges']}
        # Staging routes must match the checksum-bound input cases, not labels.
        if len(cases)!=len(reader.index['cases']):raise ValueError('Case denominator mismatch')
        for c,source in zip(cases,reader.index['cases']):
            if c['case_id']!=source['case_id']:raise ValueError('Case routing mismatch')
            for side in ['base','head']:
                route=c[side];expected=reader.index['snapshots'][source[side]]
                if route['repository']!=expected['repository'] or route['commit_id']!=source[side].split('/')[1] or route['parser_identity']!=expected['parser_identity']:
                    raise ValueError('Case snapshot routing mismatch')
        with patch('subprocess.run',side_effect=AssertionError('Comparison must not invoke tools')):
            for ordinal,c in enumerate(cases):
                try:
                    if c['base']['repository']!=c['head']['repository']:raise ValueError('Cross-repository pair')
                    result=compare_staged(reader,c['base']['repository'],c['base']['commit_id'],c['head']['commit_id'])
                    d=result['denominators']
                    if (sum(result['outcomes']['files'].values())!=d['file_union'] or
                        sum(result['outcomes']['artifacts'].values())!=d['artifact_union'] or
                        d['file_rows_observed']+d['file_rows_unavailable']!=d['file_side_slots'] or
                        d['artifact_versions_observed']+d['artifact_versions_unavailable']!=d['artifact_side_slots']):
                        raise ValueError('Lost comparison outcome')
                    # This is an integrity fingerprint, not an independent quality metric.
                    fingerprint=result.pop('fingerprint')
                    if digest(result)!=fingerprint:raise ValueError('Comparison fingerprint mismatch')
                    result['fingerprint']=fingerprint
                    path=output/f'case-{ordinal:03d}.json'
                    with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
                    rows[c['case_id']]={'status':'PARTIAL_COMPARISON_SAVED','path':path.name,
                        'fingerprint':fingerprint,'denominators':d,'outcomes':result['outcomes']}
                    denominators.update(d);files.update(result['outcomes']['files']);artifacts.update(result['outcomes']['artifacts'])
                except Exception as exc:
                    rows[c['case_id']]={'status':'FAILED_RETAINED','error':type(exc).__name__+': '+str(exc)[:300],
                        'base':c['base'],'head':c['head']}
        counts_after={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in counts_before}
        if counts_before!=counts_after:raise ValueError('Frozen staged records changed')
    result={'policy':'partial-staged-comparison-audit-v1','cases':rows,'case_denominator':len(cases),
        'failed_cases':sum(r['status']=='FAILED_RETAINED' for r in rows.values()),
        'case_weighted_observation_denominators':dict(denominators),
        'case_weighted_outcomes':{'files':dict(files),'artifacts':dict(artifacts)},'binding':binding,
        'store_counts_unchanged':counts_after,'source_fetches':0,'imports':0,'reparses':0,'model_calls':0,
        'independent_labels_created':0,'actual_staged_investigations':'NOT_RUN; comparison only',
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED',
        'scope':'Development observations over unions of partial maps, not all project files/artifacts or quality denominators; no addition/deletion/impact/consistency/negative-link claims'}
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return {k:v for k,v in result.items() if k!='cases'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output)))
