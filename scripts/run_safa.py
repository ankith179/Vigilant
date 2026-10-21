import sys,pathlib,json,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from evaluation.runs import ROOT,save_run
def flatten(data):
 nodes={};edges=set();conflicts=[]
 def visit(x,parent=None):
  if isinstance(x,dict):
   if 'id' in x:
    current=x['id'];content={k:v for k,v in x.items() if k!='children'}
    if current in nodes and nodes[current]!=content:conflicts.append(current)
    nodes[current]=content
    if parent and parent!=current:edges.add((parent,current))
    parent=current
   for v in x.values():visit(v,parent)
  elif isinstance(x,list):
   for v in x:visit(v,parent)
 visit(data);return nodes,edges,sorted(set(conflicts))
def main():
 p=[ROOT/'data/raw/safa'/f'V{i}-simplified.json' for i in [0,1]];(a,ae,ac),(b,be,bc)=[flatten(json.loads(x.read_text())) for x in p];added=sorted(b.keys()-a.keys());removed=sorted(a.keys()-b.keys());modified=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]);path,_=save_run('safa',{'status':'COMPLETED','base_version':'V0','head_version':'V1','source_hashes':[hashlib.sha256(x.read_bytes()).hexdigest() for x in p],'counts':{'base_nodes':len(a),'head_nodes':len(b),'base_edges':len(ae),'head_edges':len(be),'added_nodes':len(added),'deleted_nodes':len(removed),'modified_nodes':len(modified),'added_edges':len(be-ae),'deleted_edges':len(ae-be)},'added':added,'deleted':removed,'modified':[{'id':k,'before':a[k],'after':b[k]} for k in modified],'duplicate_content_conflicts':{'V0':ac,'V1':bc},'consistency_accuracy':None,'limitations':['No independent consistency or affected-artifact labels.','Existing safety trees, not Git code snapshots.','Context-dependent duplicate IDs use their last content occurrence and are reported.','Dronology family is not an independent project family.']});print(path)
if __name__=='__main__':main()
