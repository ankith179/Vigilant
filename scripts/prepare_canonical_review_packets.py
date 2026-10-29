"""Export blind development source packets without changing snapshots or judgments."""
import argparse
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import Artifact,digest
from rag.evidence import evidence


def prepare(database,staging,pilot,handoff,output):
    database,staging,pilot,handoff,output=map(Path,(database,staging,pilot,handoff,output))
    if output.exists():raise FileExistsError('Refusing to overwrite reviewer work')
    routes=json.loads(staging.read_text());db_hash=hashlib.sha256(database.read_bytes()).hexdigest()
    if db_hash!=routes['database_sha256']:raise ValueError('Review snapshot checksum mismatch')
    source=json.loads((pilot/'unlabelled-cases.json').read_text());cases=source['cases']
    if len({c['case_id'] for c in cases})!=len(cases):raise ValueError('Duplicate pilot case IDs')
    mapping={c['case_id']:c for c in routes['case_routes']}
    if set(mapping)!={c['case_id'] for c in cases}:raise ValueError('Pilot/staging case sets differ')
    forms=[]
    for name in ('reviewer-1.json','reviewer-2.json'):
        form=json.loads((handoff/name).read_text())
        if (form['reviewer_id'] is not None or form['independent_of_pipeline_author'] is not None or
            len(form['cases'])!=len(cases) or {c['case_id'] for c in form['cases']}!=set(mapping) or
            any(v not in (None,[]) for c in form['cases'] for k,v in c.items() if k!='case_id')):
            raise ValueError('Expected blank independent-review templates; refusing to expose judgments')
        forms.append(form)
    adjudication=copy.deepcopy(source);packets=[];cache={}
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        def row(table,key):
            record=db.execute('SELECT payload FROM '+table+' WHERE id=?',(key,)).fetchone()
            if record is None:raise ValueError('Unavailable canonical snapshot/source')
            return json.loads(record[0])
        def snapshot(route):
            key=route['repository'],route['commit_id']
            if key not in cache:
                repo=row('repositories',route['repository']);commit=row('commits',digest(*key))
                if repo['project_id']!=route['parser_identity'] or commit['repository']!=key[0] or commit['commit_id']!=key[1]:
                    raise ValueError('Canonical route differs from staged source scope')
                coverage=commit['review_source_map']
                if coverage['status']!='PARTIAL_UNREVIEWED':raise ValueError('Expected unreviewed partial source scope')
                records=db.execute("SELECT payload FROM artifacts WHERE repository=? AND commit_id=? AND json_extract(payload,'$.symbol')=''",key)
                parents={}
                for (raw,) in records:
                    a=Artifact.model_validate({k:v for k,v in json.loads(raw).items() if k!='id'});parents[a.file_path]=a
                cache[key]=repo,coverage,parents
            return cache[key]
        for source_case,case in zip(cases,adjudication['cases'],strict=True):
            cid=case['case_id'];route=mapping[cid]
            if not re.fullmatch(r'[A-Za-z0-9_-]+',cid):raise ValueError('Unsafe case ID')
            original=json.loads((pilot/(cid+'-packet.json')).read_text())
            if original['case_id']!=cid or original['repository']!=source_case['repository'] or route['original_repository_alias']!=source_case['repository']:
                raise ValueError('Original packet/canonical alias mismatch')
            if route['base']['repository']!=route['head']['repository']:raise ValueError('Foreign base/head repositories')
            packet={k:original[k] for k in ('case_id','origin','base_commit','head_commit','changed_files','patch')}
            packet.update(repository=route['base']['repository'],original_repository_alias=original['repository'],
                source_scope='UNREVIEWED_PARTIAL_DEVELOPMENT',snapshot_sides={},
                evidence_scope='Changed-file candidates only; no complete impact set or semantic-support judgment',
                excerpt_policy='At most the first 40 lines of each available changed-file parent; inspect full source before judging')
            for side in ('base','head'):
                r=route[side]
                if r['commit_id']!=source_case[side+'_commit'] or r['commit_id']!=original[side+'_commit']:
                    raise ValueError('Packet/canonical revision mismatch')
                repo,coverage,parents=snapshot(r)
                if repo['name']!=original['repository'] or repo['origin']!=original['origin']:
                    raise ValueError('Canonical repository origin mismatch')
                rows={v['file']:v for v in coverage['files']};selected=[]
                for path in original['changed_files']:
                    status=rows.get(path);a=parents.get(path)
                    item={'file':path,'source_status':status['status'] if status else 'NOT_IN_PINNED_TREE',
                        'candidate_artifact_ids':status['artifact_ids'] if status else [],'search_disposition':'UNKNOWN',
                        'source_reference':None,'excerpt':None,'api_path':None}
                    if a is not None:
                        if (a.repository!=r['repository'] or a.project_id!=r['parser_identity'] or a.commit_id!=r['commit_id']
                            or not status or a.artifact_id not in status['artifact_ids']):raise ValueError('Changed-file source identity mismatch')
                        e=evidence(a,max_lines=40)
                        item.update(source_reference={k:e[k] for k in ('artifact_id','commit_id','file','content_hash','start_line','end_line')},
                            excerpt=e['quote'],api_path='/api/artifacts/'+a.artifact_id+'?'+urlencode({'repository':a.repository,'commit_id':a.commit_id}))
                    selected.append(item)
                packet['snapshot_sides'][side]={**r,'file_statuses':coverage['file_statuses'],
                    'snapshot_file_count':len(coverage['files']),'changed_files':selected}
            case['repository']=packet['repository']
            identity_fields={'case_id','repository','base_commit','head_commit','obligation_inventory'}
            if case['obligation_inventory']!='UNKNOWN' or any(v not in (None,[]) for k,v in case.items() if k not in identity_fields):
                raise ValueError('Expected untouched unlabelled pilot template')
            packets.append(packet)
    output.mkdir(parents=True,exist_ok=False)
    files={}
    def write(name,data):
        path=output/name
        with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2);stream.write('\n')
        if name!='manifest.json':files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for packet in packets:write(packet['case_id']+'-packet.json',packet)
    for name,form in zip(('reviewer-1.json','reviewer-2.json'),forms,strict=True):write(name,form)
    write('adjudication-template.json',adjudication)
    for name in ('reviewer-schema.json','adjudication-schema.json'):write(name,json.loads((handoff/name).read_text()))
    summary={'policy':'canonical-blind-development-review-v1','cases':len(packets),'held_out':False,
        'database_sha256':db_hash,'staging_sha256':hashlib.sha256(staging.read_bytes()).hexdigest(),
        'source_pilot_sha256':hashlib.sha256((pilot/'unlabelled-cases.json').read_bytes()).hexdigest(),
        'files':files,'independent_labels_created':0,'model_calls':0,'quality_target':'NOT_EVALUATED'}
    write('manifest.json',summary)
    if hashlib.sha256(database.read_bytes()).hexdigest()!=db_hash:raise ValueError('Frozen snapshot changed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--database',type=Path,default=ROOT/'data/snapshots/pilot-review-20261024.db')
    p.add_argument('--staging',type=Path,default=ROOT/'reports/pilot-store-20261024/STAGING.json')
    p.add_argument('--pilot',type=Path,default=ROOT/'reports/audit-v2-20261023/change-pilot')
    p.add_argument('--handoff',type=Path,default=ROOT/'reports/completion-20261024/review-handoff-final');a=p.parse_args()
    r=prepare(a.database,a.staging,a.pilot,a.handoff,a.output)
    print(json.dumps({k:v for k,v in r.items() if k!='files'}))
