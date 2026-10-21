"""Validate real dataset truth endpoints; label all exclusions explicitly."""
from pathlib import Path
import csv,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def decode(p):
 raw=p.read_bytes()
 for enc in (['utf-16'] if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else ['utf-8-sig','cp1252']):
  try:return raw.decode(enc),enc
  except UnicodeDecodeError:pass
 raise ValueError('Unknown encoding: '+str(p))
def item(p,id=None):
 text,enc=decode(p);return {'id':id or p.stem,'text':text,'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'encoding':enc}
def validate(ds):
 s={x['id'] for x in ds['sources']};t={x['id'] for x in ds['targets']}
 if len(s)!=len(ds['sources']) or len(t)!=len(ds['targets']):raise ValueError('Duplicate identifiers')
 if len(ds['links'])!=len(set(map(tuple,ds['links']))):raise ValueError('Duplicate links')
 missing=[x for x in ds['links'] if x[0] not in s or x[1] not in t]
 if missing:raise ValueError('Dangling links: '+str(missing[:3]))
 return {'sources':len(s),'targets':len(t),'links':len(ds['links']),'queries_with_links':len({x[0] for x in ds['links']}),'dangling_links':0}
def main():
 out=ROOT/'data/prepared';out.mkdir(exist_ok=True);manifest=json.loads((ROOT/'data/source-manifest.json').read_text());reports={};base=ROOT/'data/raw/lissa/LiSSA-RATLR-V2/lissa/datasets/req2code'
 for name,split in [('SMOS','train'),('iTrust','validation'),('eTour_en','test')]:
  p=base/name;ds={'name':name,'split':split,'commit':manifest['lissa']['commit'],'sources':[item(x) for x in sorted((p/'UC').iterdir()) if x.is_file()],'targets':[item(x) for x in sorted((p/'CC').iterdir()) if x.is_file()],'links':list(csv.reader((p/'answer.csv').read_text().splitlines())),'license':'LiSSA package MIT; retain original dataset notices; no blanket relicensing claim'}
  reports[name]=validate(ds);(out/(name+'.json')).write_text(json.dumps(ds,ensure_ascii=False))
 p=ROOT/'data/raw/rtmx';sources=[];targets={};links=[];missing=[]
 for row in csv.DictReader((p/'.rtmx/database.csv').open()):
  path=p/row['test_module'];tid=row['test_module']
  if not path.is_file():missing.append({'requirement':row['req_id'],'missing_test_module':tid});continue
  sources.append({'id':row['req_id'],'text':row['requirement_text'],'path':str((p/'.rtmx/database.csv').relative_to(ROOT))});targets[tid]=item(path,tid);links.append([row['req_id'],tid])
 ds={'name':'RTMX-module-valid','split':'external_test','commit':manifest['rtmx']['commit'],'sources':sources,'targets':list(targets.values()),'links':links,'license':'Apache-2.0','limitations':'Declared test_function symbols do not resolve; use existing module-level targets only. Two missing modules excluded explicitly. Requirement identifiers removed from retrieval input. Not comparable to original 24/24 baseline.'}
 reports[ds['name']]={**validate(ds),'excluded':missing};(out/(ds['name']+'.json')).write_text(json.dumps(ds));reports['RTMX-function-level']={'status':'BLOCKED','reason':'Declared function symbols do not resolve'}
 reports['Dronology']={'status':'BLOCKED','reason':(base/'dronology-re/CC/README.md').read_text().strip()}
 for name in ['V0','V1']:
  p=ROOT/'data/raw/safa'/f'{name}-simplified.json';data=json.loads(p.read_text());ids=set();edges=set()
  def visit(node,parent=None):
   if isinstance(node,dict):
    if 'id' in node:
     current=node['id'];ids.add(current)
     if parent and parent!=current:edges.add((parent,current))
     parent=current
    for x in node.values():visit(x,parent)
   elif isinstance(node,list):
    for x in node:visit(x,parent)
  visit(data);reports['SAFA-'+name]={'nodes':len(ids),'edges':len(edges),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 (out/'validation.json').write_text(json.dumps(reports,indent=2));(out/'splits.json').write_text(json.dumps({'strategy':'project-level','train':['SMOS'],'validation':['iTrust'],'test':['eTour_en'],'external_test':['RTMX-module-valid'],'temporal':'SAFA V0 context, V1 evaluation; same project family as Dronology','rule':'No test labels used for threshold/model fitting; do not random-split artifact pairs'},indent=2));print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
