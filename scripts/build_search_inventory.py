"""Prepare an UNKNOWN search manifest; a real reviewer must classify every file."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ingestion.git import git,revision
from consistency.search_inventory import SearchInventory,in_boundary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('repository',type=Path);p.add_argument('--commit',required=True)
    p.add_argument('--prefix',action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    sha=revision(a.repository,a.commit)
    # UNKNOWN drafts only need tree identities. Asking for blob sizes (-l) in a
    # partial clone may download source contents one blob at a time.
    rows=[]
    for entry in git(a.repository,'ls-tree','-rz',sha,binary=True).split(b'\0'):
        if not entry:continue
        meta,path=entry.split(b'\t',1);mode,kind,oid=meta.split()
        file=path.decode('utf-8',errors='replace')
        if in_boundary(file,a.prefix):rows.append({'file':file,'object_id':oid.decode()})
    result={'commit_id':sha,'prefixes':a.prefix,'entries':[{'file':r['file'],'object_id':r['object_id'],'disposition':'UNKNOWN',
        'rationale':'Awaiting independent review','artifact_ids':[]} for r in rows]}
    manifest=SearchInventory.model_validate(result)
    # Reject empty or mismatched boundaries before creating an output.
    if not manifest.entries:raise ValueError('Search boundary has no pinned entries')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # Reviewer edits are evidence: never overwrite an existing draft or review.
    with a.output.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(rows),'status':'UNKNOWN_UNREVIEWED','output':str(a.output)}))
