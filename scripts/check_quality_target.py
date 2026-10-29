"""Evaluate a requested quality protocol without model calls; missing labels remain NOT_EVALUATED."""
import argparse,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.quality_gate import evaluate
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path);p.add_argument('--predictions',type=Path);p.add_argument('--protocol',type=Path,default=ROOT/'evaluation/quality-target-95.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 protocol=json.loads(a.protocol.read_text())
 if protocol.get('protocol')=='vigilant-assurance-95-v2':
  from evaluation.assurance_gate import evaluate
 if not a.dataset or not a.predictions:result={'status':'NOT_EVALUATED','target':protocol['target'],'reason':'Independent frozen labels and matching predictions not supplied','accuracy_claim_supported':False,'inference_calls':0}
 else:
  data=json.loads(a.dataset.read_text());data['frozen_sha256']=hashlib.sha256(a.dataset.read_bytes()).hexdigest();pred=json.loads(a.predictions.read_text())
  if protocol.get('protocol')=='vigilant-assurance-95-v2':
   from evaluation.fingerprint import pipeline_fingerprint
   actual=pipeline_fingerprint()['sha256']
   if protocol.get('frozen_pipeline_sha256')!=actual:result={'status':'NOT_EVALUATED','target':protocol['target'],'issues':['Frozen pipeline fingerprint does not match these executable sources'],'accuracy_claim_supported':False,'inference_calls':0}
   else:result=evaluate(data,pred,protocol)
  else:result=evaluate(data,pred,protocol)
  result['dataset_sha256']=data['frozen_sha256'];result['prediction_sha256']=hashlib.sha256(a.predictions.read_bytes()).hexdigest()
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
