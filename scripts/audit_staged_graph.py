"""Project bounded graphs for exposed development packet scopes; never label them."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation.review_intake import OfflineReviewSourcePolicy
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_graph import project_staged_graph


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite graph audit')
    packets=ROOT/'reports/recovered-review-20261024/packets'
    manifest=json.loads((packets/'manifest.json').read_text())
    for name,h in manifest['files'].items():
        if file_sha256(packets/name)!=h:raise ValueError('Packet checksum mismatch')
    selections=defaultdict(set);unavailable=0;references=0
    for path in sorted(packets.glob('*-packet.json')):
        packet=json.loads(path.read_text())
        for side in packet['snapshot_sides'].values():
            for item in side['changed_files']:
                ref=item['source_reference']
                if ref is None:unavailable+=1;continue
                references+=1;selections[packet['repository'],ref['commit_id']].add(ref['artifact_id'])
    policy=OfflineReviewSourcePolicy(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',ROOT)
    output.mkdir(parents=True);rows=[];totals=Counter()
    with StagedSourceReader(ROOT/'data/snapshots/pilot-review-recovered-20261024.db',ROOT/'reports/verified-cache-maps-20261024/maps/index.json',ROOT/'reports/recovered-review-20261024/STAGING.json') as reader:
        for (repository,commit),ids in sorted(selections.items()):
            selected=sorted(ids)
            for start in range(0,len(selected),20):
                row={'repository':repository,'commit_id':commit,'selection':selected[start:start+20]}
                try:
                    result=project_staged_graph(reader,policy,{'repository':repository,'commit_id':commit,'artifact_ids':row['selection'],'limit':40})
                    name=f'graph-{len(rows):03d}.json';(output/name).write_text(json.dumps(result,indent=2)+'\n')
                    row.update(status='PROJECTED',result_id=result['result_id'],path=name,next_offset=result['next_offset'])
                    totals.update(result['denominators'])
                except (ValueError,OSError) as exc:row.update(status='FAILED_OR_WITHHELD',error_type=type(exc).__name__)
                rows.append(row)
        counts={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in ['artifacts','analysis_runs','graph_nodes','graph_edges','tool_results']}
    result={'policy':'staged-graph-audit-v1','rows':rows,'snapshot_scopes':len(selections),
        'packet_source_entries':references+unavailable,'available_reference_occurrences':references,'unavailable_reference_occurrences':unavailable,
        'projection_requests':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
        'request_weighted_denominators':dict(totals),'frozen_store_counts':counts,
        'scope':'First bounded incident-edge page per selection; not a complete application graph or independent quality evaluation',
        'model_calls':0,'independent_labels_created':0,'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output),indent=2))
