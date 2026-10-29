"""Bounded candidates; retrieval similarity is not a calibrated confidence."""
from retrieval.index import Index,RETRIEVAL_POLICY
from ingestion.models import digest
from rag.evidence import evidence

def recover(store,artifacts,encoder=None,k=3):
 sources=[a for a in artifacts if a.artifact_type=='requirement'];targets=[a for a in artifacts if a.artifact_type in {'function','method','class','source_file','test','test_method','frontend'} and a.content.strip()]
 if not sources or not targets:return []
 index=Index([a.model_dump() for a in targets],encoder);result=[]
 for a in sources:
  method='hybrid' if encoder else 'tfidf'
  for hit in index.search(a.content,method,k):
   if method=='tfidf' and hit['score']<.12:continue
   row={'retrieval_policy':RETRIEVAL_POLICY,'source_artifact':a.artifact_id,'target_artifact':hit['artifact_id'],'relation_type':'RELATED_TO','proposed_relation':'VALIDATES' if hit['artifact_type'] in {'test','test_method'} else 'IMPLEMENTS','score':hit['score'],'confidence':None,'method':method,'status':'CANDIDATE_REQUIRES_REVIEW','evidence':[evidence(a,'requirement'),{'artifact_id':hit['artifact_id'],'file':hit['file_path'],'start_line':hit['start_line'],'end_line':hit['end_line'],'commit':hit['commit_id']}],'repository':a.repository,'project_id':a.project_id,'commit_id':a.commit_id}
   result.append(row)
 store.put_many('trace_links',[(digest(row['source_artifact'],row['target_artifact'],row['commit_id'],row['method'],RETRIEVAL_POLICY),row) for row in result])
 return result
