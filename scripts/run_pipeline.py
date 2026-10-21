import sys,pathlib,argparse,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from database.store import Store
from agents.workflow import analyze
from evaluation.runs import save_run

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',default='data/repos/flask');p.add_argument('--base',default='HEAD~1');p.add_argument('--head',default='HEAD');p.add_argument('--model',default='none');p.add_argument('--semantic',action='store_true');a=p.parse_args()
 r=analyze(Store(),a.repo,a.base,a.head,model=a.model,semantic=a.semantic);path,_=save_run('pipeline',r);print(json.dumps({'report':str(path),'changes':len(r['changes']['artifacts']),'affected':len(r['affected_artifacts']),'findings':len(r['findings']),'evidence':len(r['evidence']),'model_error':r['model']['validation_error'],'metrics':r['metrics']},indent=2))
if __name__=='__main__':main()
