"""Import revisions under a new parser identity, preserving old artifact versions."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database.store import Store
from ingestion.service import import_repository
from ingestion.parsers import PARSER_POLICY
from knowledge_graph.graph import build_graph
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--project',default='vigilant');p.add_argument('--revisions',nargs='+',default=['HEAD~1','HEAD']);a=p.parse_args();s=Store()
 for rev in a.revisions:
  result=import_repository(s,a.path,a.project+'::'+PARSER_POLICY,rev);build_graph(s,s.artifacts(result['repository'],result['commit_id']));print(result)
