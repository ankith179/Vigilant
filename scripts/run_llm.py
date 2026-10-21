import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ingestion.parsers import extract
from ingestion.git import revision
from rag.evidence import evidence
from llm.providers import LocalLLMProvider
from evaluation.runs import ROOT,save_run
p=ROOT/'data/repos/fullstack/backend/app/api/routes/items.py';commit=revision(ROOT/'data/repos/fullstack');a=next(x for x in extract('smoke','fullstack',commit,'backend/app/api/routes/items.py',p.read_text()) if x.symbol=='read_item' and x.artifact_type=='function')
r=LocalLLMProvider().investigate('Are caller and test consistency established by this function alone? Use UNCERTAIN if not.',[evidence(a)]);path,_=save_run('llm',r);print(path);print(json.dumps({k:v for k,v in r.items() if k!='messages'},indent=2))
