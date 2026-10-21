import sys,pathlib,sqlite3,os,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from database.store import Store,TABLES
from evaluation.runs import ROOT
def experiment_record(p):
 d=json.loads(p.read_text());excluded_path=p.parent/'EXCLUDED.json';excluded=json.loads(excluded_path.read_text()) if excluded_path.exists() else None
 summary=d.get('summary') or d.get('counts')
 if summary is None and isinstance(d.get('results'),list):summary=[{k:v for k,v in x.items() if k in ['dataset','method','metrics','ranking','classification','status']} for x in d['results']]
 try:relative=str(p.relative_to(ROOT))
 except ValueError:relative=str(p)
 rows=d.get('results',[])
 if not isinstance(rows,list):rows=[]
 labels=lambda field:', '.join(sorted({str(x[field]) for x in rows if isinstance(x,dict) and x.get(field)})) or d.get(field)
 return {'kind':d['kind'],'run_id':d['run_id'],'status':'EXCLUDED_RUNTIME_FAILURE' if excluded else d.get('status','COMPLETED'),'path':relative,'dataset':labels('dataset'),'method':labels('method'),'summary':None if excluded else summary,'seconds':d.get('seconds'),'limitations':d.get('limitations',[]),'excluded_from_accuracy_comparison':bool(excluded),'exclusion':excluded}
def main():
 url=os.getenv('VIGILANT_DB','sqlite:///data/vigilant.db');s=Store(url);bench=pathlib.Path(os.getenv('VIGILANT_BENCH_PATH',str(ROOT/'data/snapshots/changebench.db')))
 if url.startswith('sqlite:///') and bench.exists() and pathlib.Path(url[10:]).resolve()!=bench.resolve():
  with sqlite3.connect(url[10:]) as c:
   c.execute('ATTACH DATABASE ? AS bench',(str(bench),))
   for t in TABLES:c.execute(f'INSERT OR IGNORE INTO main.{t} SELECT * FROM bench.{t}')
 for p in (ROOT/'experiments').glob('*/*/results.json'):
  record=experiment_record(p)
  # This is a derived dashboard view. Raw experiment records remain immutable.
  s.put('experiments',record['run_id'],record,replace=True)
 print('Dashboard synchronized with recorded analyses and experiments.')
if __name__=='__main__':main()
