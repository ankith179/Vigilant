"""Audit the new development maps against frozen originals and exact recovered bytes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import digest
from scripts.prepare_pilot_artifact_maps import load_verified_cache
from scripts.stage_pilot_review_store import validate_map


def audit(baseline_archive):
    base=ROOT/'reports/pilot-artifacts-20261024/maps'
    new=ROOT/'reports/verified-cache-maps-20261024/maps'
    old_index=json.loads((base/'index.json').read_text());index=json.loads((new/'index.json').read_text())
    queue_path=ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json'
    queue=json.loads(queue_path.read_text())
    cache=load_verified_cache(ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json',queue_path)
    assert old_index['cases']==index['cases'] and set(old_index['snapshots'])==set(index['snapshots'])
    statuses=Counter();recovered=Counter();identities=set();cached_oids=set();routes={};versions=0;old_ids=set();new_ids=set()
    for key,s in index['snapshots'].items():
        assert s['status']=='PARTIAL_SOURCE_MAP'
        raw=(new/s['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']
        m=json.loads(raw);items=validate_map(m);identities.add(m['parser_identity'])
        assert m['quality_target']=='NOT_EVALUATED' and m['verified_cache']['manifest_sha256']==cache['manifest_sha256']
        assert m['source_policy_sha256']==hashlib.sha256((ROOT/'scripts/prepare_pilot_artifact_maps.py').read_bytes()).hexdigest()
        old_s=old_index['snapshots'][key];old_raw=(base/old_s['path']).read_bytes()
        assert hashlib.sha256(old_raw).hexdigest()==old_s['sha256']
        old=json.loads(old_raw);old_rows={r['file']:r for r in old['files']};rows={r['file']:r for r in m['files']}
        assert {(p,r['object_id']) for p,r in rows.items()}=={(p,r['object_id']) for p,r in old_rows.items()}
        assert (m['origin'],m['commit_id'],m['draft_fingerprint'],m['limits'])==(old['origin'],old['commit_id'],old['draft_fingerprint'],old['limits'])
        parents={a.file_path:a for a in items if not a.symbol}
        for row in rows.values():
            previous=old_rows[row['file']];assert row['search_disposition']=='UNKNOWN'
            if row['source_origin']=='VERIFIED_UPSTREAM_CACHE':
                assert previous['status']=='MISSING_LOCAL_BLOB'
                source=cache['objects'][row['object_id']]
                assert (m['origin'],m['commit_id'],row['file']) in source['scopes']
                assert parents[row['file']].content==source['bytes'].decode('utf-8-sig')
                assert row['size_bytes']==len(source['bytes'])
                recovered[row['status']]+=1;cached_oids.add(row['object_id'])
            else:assert (row['status'],row['size_bytes'])==(previous['status'],previous['size_bytes'])
        # Existing available source text/spans are preserved under fresh IDs.
        shape=lambda a:(a['file_path'],a['artifact_type'],a['symbol'],a['content'],a['start_line'],a['end_line'])
        assert {shape(a) for a in old['artifacts']} <= {shape(a) for a in m['artifacts']}
        for a in items:assert a.content_hash==digest(a.content)
        old_ids.update(a['artifact_id'] for a in old['artifacts']);new_ids.update(a.artifact_id for a in items)
        counts=Counter(r['status'] for r in rows.values())
        assert dict(counts)==s['file_statuses'] and len(rows)==s['files'] and len(items)==s['artifacts']
        statuses.update(counts);versions+=len(items);routes[key]=rows
    assert len(identities)==1 and not old_ids & new_ids
    for e in queue['missing_file_side_entries']:
        row=routes[e['original_alias']+'/'+e['commit_id']][e['file']]
        assert row['source_origin']=='VERIFIED_UPSTREAM_CACHE' and row['object_id']==e['object_id'] and row['status']=='PARSED'
    for e in queue['absent_pinned_tree_paths']:
        assert e['file'] not in routes[e['original_alias']+'/'+e['commit_id']]
    mutable={'PROJECT_STATE.json','RESUME.md','RECOVERY_SOURCES.json','CHECKPOINT.json',
             'scripts/prepare_pilot_artifact_maps.py','scripts/stage_pilot_review_store.py','scripts/research_checkpoint.py'}
    preserved={}
    with zipfile.ZipFile(baseline_archive) as z:
        for name in z.namelist():
            relative=name.removeprefix('VIGILANT/')
            if name.endswith('/') or relative in mutable:continue
            raw=z.read(name);assert (ROOT/relative).read_bytes()==raw,relative
            preserved[relative]=hashlib.sha256(raw).hexdigest()
    result={'status':'PASS','snapshots':len(routes),'cases':len(index['cases']),'files':sum(statuses.values()),
        'artifact_versions_identity_hash_span_verified':versions,'parser_identity':next(iter(identities)),
        'recovered_snapshot_file_rows':sum(recovered.values()),'recovered_file_statuses':dict(recovered),
        'unique_recovered_blob_ids':len(cached_oids),'queued_case_side_occurrences_covered':len(queue['missing_file_side_entries']),
        'unchanged_absent_pinned_tree_paths':len(queue['absent_pinned_tree_paths']),'file_statuses':dict(statuses),
        'baseline_archive_sha256':hashlib.sha256(Path(baseline_archive).read_bytes()).hexdigest(),
        'unchanged_baseline_files':len(preserved),'old_new_artifact_id_overlap':len(old_ids & new_ids),
        'model_calls':0,'new_fetches':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    report=ROOT/'reports/verified-cache-maps-20261024'
    for filename,value in [('AUDIT.json',result),('preservation.json',preserved)]:
        with (report/filename).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-archive',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().baseline_archive)))
