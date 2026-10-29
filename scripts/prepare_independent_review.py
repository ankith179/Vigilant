"""Export blind annotation candidates from pinned local Git histories."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.git import git
SOURCE_SUFFIXES={'.c','.cc','.cpp','.cs','.go','.h','.hpp','.java','.js','.jsx','.kt','.m','.mm','.php','.py','.rs','.swift','.ts','.tsx'}
IGNORED_PARTS={'build','dist','generated','node_modules','target','vendor'}
REVIEW_FIELDS=[
 'case_id','repository','origin','base_commit','head_commit','changed_files',
 'reviewer_1_id','reviewer_1_label','reviewer_1_sufficient','reviewer_1_missing_evidence','reviewer_1_rationale',
 'reviewer_2_id','reviewer_2_label','reviewer_2_sufficient','reviewer_2_missing_evidence','reviewer_2_rationale',
 'adjudicator_id','adjudicated_label','adjudication_rationale'
]

def eligible(path):
 parts=Path(path).parts
 return Path(path).suffix.lower() in SOURCE_SUFFIXES and not any(part.lower() in IGNORED_PARTS for part in parts)

def candidate_id(origin,repository,base,head):
 key='\n'.join((origin,repository,base,head)).encode('utf-8')
 return hashlib.sha256(key).hexdigest()[:20]

def collect_repo(repo,limit=None):
 repo=Path(repo).resolve()
 remote=subprocess.run(['git','-C',str(repo),'remote','get-url','origin'],capture_output=True,text=True,timeout=30)
 origin=remote.stdout.strip() if remote.returncode==0 else 'local:'+repo.as_posix()
 name=repo.name
 commits=git(repo,'rev-list','--reverse','--no-merges','--all').splitlines()
 candidates=[]
 for head in commits:
  revisions=git(repo,'rev-list','--parents','-n','1',head).split()
  if len(revisions)!=2:continue
  base=revisions[1]
  names=git(repo,'diff','--name-only','-z',base,head).split('\0')
  files=sorted({path for path in names if path and eligible(path)})
  if not files:continue
  patch=git(repo,'diff','--no-ext-diff','--no-color','--unified=12',base,head,'--',*files)
  if not patch.strip():continue
  candidates.append({'case_id':candidate_id(origin,name,base,head),'repository':name,
   'origin':origin,'base_commit':base,'head_commit':head,'changed_files':files,
   'patch':patch,'review_question':'Review this base/head change. Identify only evidence-supported contract, API, caller, or test problems. If the repository evidence does not establish a conclusion, use UNCERTAIN. Do not infer a defect from the diff alone.'})
  if limit is not None and len(candidates)>=limit:break
 return candidates

def round_robin(groups,limit):
 pool=[];index=0
 while len(pool)<limit:
  added=False
  for group in groups:
   if index<len(group):
    pool.append(group[index]);added=True
    if len(pool)>=limit:break
  if not added:break
  index+=1
 return pool

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repos',type=Path,default=ROOT/'data/repos',help='Directory containing local Git repositories')
 parser.add_argument('--limit',type=int,default=200)
 parser.add_argument('--minimum',type=int,default=200)
 parser.add_argument('--output',type=Path,default=ROOT/'reports/independent-review-20261022')
 args=parser.parse_args()
 if args.limit<1 or args.minimum<1:parser.error('--limit and --minimum must be positive')
 repo_paths=sorted(path for path in args.repos.iterdir() if path.is_dir() and (path/'.git').exists())
 if not repo_paths:parser.error('No local Git repositories found under '+str(args.repos))
 groups=[collect_repo(path) for path in repo_paths]
 cases=round_robin(groups,args.limit)
 if args.output.exists():parser.error('Output already exists; choose a new output path to avoid overwriting reviewer work')
 args.output.mkdir(parents=True)
 pool={'schema_version':1,'kind':'UNLABELLED_ANNOTATION_CANDIDATES','status':'READY_FOR_ANNOTATION' if len(cases)>=args.minimum else 'INSUFFICIENT_CANDIDATES',
  'candidate_count':len(cases),'minimum_required':args.minimum,'shortfall':max(0,args.minimum-len(cases)),
  'selection':'Non-merge commits with at least one source-file change; round-robin over local repositories; stable oldest-first Git history order.',
  'label_status':'NO_LABELS_CREATED','split_status':'NOT_ASSIGNED; group by repository/change family before train/validation/test split.',
  'limitations':['Candidates are not ground truth and must not be scored as labeled cases.','Two reviewers must independently annotate each case using the approved decision policy; disagreements require adjudication.','Commit ancestry and duplicate/follow-up changes must be checked before assigning held-out splits.'],
  'cases':cases}
 (args.output/'candidate-cases.json').write_text(json.dumps(pool,indent=2,ensure_ascii=False),encoding='utf-8')
 with (args.output/'review-worksheet.csv').open('w',encoding='utf-8',newline='') as stream:
  writer=csv.DictWriter(stream,fieldnames=REVIEW_FIELDS);writer.writeheader()
  for case in cases:writer.writerow({**{key:case.get(key,'') for key in REVIEW_FIELDS if key in case},**{key:'' for key in REVIEW_FIELDS if key.startswith(('reviewer_','adjudicator_'))}})
 summary={key:pool[key] for key in ('status','candidate_count','minimum_required','shortfall','label_status','split_status')}
 summary['repository_counts']={path.name:len(group) for path,group in zip(repo_paths,groups)}
 (args.output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()