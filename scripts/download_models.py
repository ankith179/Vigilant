from pathlib import Path
import os,json,urllib.request,shutil,argparse
os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[1]
MODELS={'embedding':('sentence-transformers/all-MiniLM-L6-v2','1110a243fdf4706b3f48f1d95db1a4f5529b4d41','float32'),'llm':('Qwen/Qwen2.5-1.5B-Instruct',None,'bfloat16')}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--staging-only',action='store_true',help='Keep hosted model weights in VIGILANT_MODEL_STAGING; use runtime path overrides.');args=parser.parse_args()
 p=ROOT/'data/models.json';records=json.loads(p.read_text()) if p.exists() else {}
 for name,(model,rev,dtype) in MODELS.items():
  rev=records.get(name,{}).get('revision',rev)
  if rev is None:
   with urllib.request.urlopen('https://huggingface.co/api/models/'+model,timeout=40) as r:rev=json.load(r)['sha']
  destination=ROOT/'data/models'/name
  staging=Path(os.getenv('VIGILANT_MODEL_STAGING',str(ROOT/'data/models')))/name
  path=snapshot_download(model,revision=rev,allow_patterns=['*.json','*.txt','*.safetensors','*.model','1_Pooling/*'],local_dir=staging,max_workers=3)
  if staging!=destination and not args.staging_only:
   shutil.copytree(staging,destination,dirs_exist_ok=True)
   path=destination
  from safetensors import safe_open
  for weight in Path(path).glob('*.safetensors'):
   with safe_open(weight,framework='pt',device='cpu') as f:
    if not list(f.keys()):raise ValueError('Empty model weight file')
  records[name]={'model':model,'revision':rev,'dtype':dtype,'path':str(destination.relative_to(ROOT)),'license':'Apache-2.0'};p.write_text(json.dumps(records,indent=2));print(name,rev,'runtime',path,flush=True)
if __name__=='__main__':main()
