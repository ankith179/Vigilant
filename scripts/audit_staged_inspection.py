"""Probe staged source navigation over exposed development packets, no labels."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import digest
from evaluation.review_intake import OfflineReviewSourcePolicy
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_inspection import StagedInvestigationService


def audit(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite audit')
    packets=ROOT/'reports/recovered-review-20261024/packets'
    manifest=json.loads((packets/'manifest.json').read_text())
    for name,h in manifest['files'].items():
        if file_sha256(packets/name)!=h:raise ValueError('Packet checksum mismatch')
    policy=OfflineReviewSourcePolicy(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json',ROOT)
    rows=[];output.mkdir(parents=True,exist_ok=False)
    db=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    with StagedSourceReader(db,ROOT/'reports/verified-cache-maps-20261024/maps/index.json',ROOT/'reports/recovered-review-20261024/STAGING.json') as reader:
        binding=dict(reader.binding);service=StagedInvestigationService(reader,policy)
        tables=['artifacts','analysis_runs','graph_nodes','graph_edges','tool_results']
        before={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in tables}
        for path in sorted(packets.glob('*-packet.json')):
            packet=json.loads(path.read_text())
            for side,snapshot in packet['snapshot_sides'].items():
                for item in snapshot['changed_files']:
                    row={'case_id':packet['case_id'],'side':side,'file':item['file']}
                    ref=item['source_reference']
                    if ref is None:row.update(status='NO_SOURCE_REFERENCE',recorded_source_status=item['source_status'])
                    else:
                        try:
                            result=service.call('inspect_artifact',{'repository':packet['repository'],'commit_id':ref['commit_id'],'artifact_id':ref['artifact_id'],'start_line':ref['start_line'],'max_lines':min(80,ref['end_line']-ref['start_line']+1)})
                            rid=result.pop('result_id')
                            if digest(result)!=rid:raise ValueError('Result fingerprint mismatch')
                            result['result_id']=rid;filename=f'inspection-{len(rows):03d}.json'
                            with (output/filename).open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
                            row.update(status=result['source_verification_receipts'][0]['status'],result_id=rid,path=filename)
                        except Exception as exc:row.update(status='FAILED_OR_WITHHELD_RETAINED',error=type(exc).__name__+': '+str(exc)[:200])
                    rows.append(row)
        after={t:reader.connection.execute('select count(*) from '+t).fetchone()[0] for t in tables}
        if before!=after:raise ValueError('Frozen Store changed')
    result={'policy':'staged-inspection-audit-v1','rows':rows,'denominator':len(rows),'cases':manifest['cases'],'source_statuses':dict(Counter(r['status'] for r in rows)),
        'binding':binding,'source_policy':policy.provenance,'store_counts_unchanged':after,
        'model_calls':0,'source_fetches':0,'independent_labels_created':0,'full_staged_workflow':'NOT_RUN; bounded source navigation only',
        'semantic_support':'NOT_ESTABLISHED','quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return {k:v for k,v in result.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().output)))
