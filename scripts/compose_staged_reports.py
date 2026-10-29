"""Compose separate partial development reports; no Store writes or labels."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_report import compose_staged_report
from evaluation.review_intake import OfflineReviewSourcePolicy


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite reports')
    packets=ROOT/'reports/recovered-review-20261024/packets';manifest=json.loads((packets/'manifest.json').read_text())
    for name,h in manifest['files'].items():
        if file_sha256(packets/name)!=h:raise ValueError('Packet checksum mismatch')
    index=ROOT/'reports/verified-cache-maps-20261024/maps/index.json';cases=json.loads(index.read_text())['cases']
    by={c['case_id']:c for c in cases}
    policy=OfflineReviewSourcePolicy(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',ROOT)
    output.mkdir(parents=True);rows=[];counts=Counter();unavailable=[]
    with StagedSourceReader(ROOT/'data/snapshots/pilot-review-recovered-20261024.db',index,ROOT/'reports/recovered-review-20261024/STAGING.json') as reader:
        for path in sorted(packets.glob('*-packet.json')):
            packet=json.loads(path.read_text());case=by[packet['case_id']]
            args={'repository':packet['repository'],'base_commit':case['base'].split('/')[1],'commit_id':case['head'].split('/')[1]}
            for role in ('base','head'):
                unavailable.extend({'case_id':packet['case_id'],'revision_role':role,'file':i['file'],'status':i['source_status']} for i in packet['snapshot_sides'][role]['changed_files'] if i['source_reference'] is None)
                # Packet side names are the canonical lower-case base/head roles.
                args[role+'_artifact_ids']=sorted({i['source_reference']['artifact_id'] for i in packet['snapshot_sides'][role]['changed_files'] if i['source_reference'] is not None})
            row={'case_id':packet['case_id']}
            try:
                report=compose_staged_report(reader,policy,args)
                name=f'report-{len(rows):03d}.json';(output/name).write_text(json.dumps(report,indent=2)+'\n')
                row.update(status='COMPOSED',path=name,report_id=report['report_id'])
                counts.update({'unknown_artifact_observations':len(report['unknown_artifact_observations']),
                    'changed_artifact_observations':len(report['changed_artifact_observations']),
                    'verified_source_occurrences':len(report['evidence']),'withheld_source_occurrences':len(report['source_unknowns'])})
            except (ValueError,OSError) as exc:row.update(status='FAILED_OR_WITHHELD',error_type=type(exc).__name__)
            rows.append(row)
        store_counts={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in ('artifacts','analysis_runs','graph_nodes','graph_edges','tool_results')}
    summary={'policy':'partial-staged-report-audit-v1','cases':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),
        'counts':dict(counts),'unavailable_source_references':unavailable,'unavailable_reference_occurrences':len(unavailable),'packet_source_entries':counts['verified_source_occurrences']+counts['withheld_source_occurrences']+len(unavailable),'frozen_store_counts':store_counts,'rows':rows,'model_calls':0,'independent_labels_created':0,
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED',
        'application_integration':'NOT_RUN; separate report artifacts, no canonical analysis_runs'}
    (output/'result.json').write_text(json.dumps(summary,indent=2)+'\n');return {k:v for k,v in summary.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(p.parse_args().output),indent=2))
