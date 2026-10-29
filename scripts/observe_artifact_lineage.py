"""Explicit, read-only lineage observation command; never overwrites a report."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from change_analysis.lineage import observe, verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository-path',type=Path,required=True)
    p.add_argument('--project',required=True)
    p.add_argument('--repository-id',required=True)
    p.add_argument('--base',required=True)
    p.add_argument('--head',required=True)
    p.add_argument('--path',action='append',dest='paths')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to overwrite lineage observations')
    args={'project':a.project,'repository':a.repository_id,'base':a.base,'head':a.head,'paths':a.paths}
    result=observe(a.repository_path,**args)
    verify(a.repository_path,result,**args)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'record_id':result['record_id'],'denominators':result['denominators'],
                      'lifecycle':'UNREVIEWED','logical_continuity':'UNKNOWN'}))


if __name__=='__main__':main()
