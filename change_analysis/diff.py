import re
import io
import tokenize
from ingestion.git import git,revision

def _python_tokens(text):
 try:return [(token.type,token.string) for token in tokenize.generate_tokens(io.StringIO(text).readline) if token.type not in {tokenize.COMMENT,tokenize.NL,tokenize.ENCODING}]
 except (IndentationError,tokenize.TokenError):return None

def _python_comments(text):
 try:return [token.string for token in tokenize.generate_tokens(io.StringIO(text).readline) if token.type==tokenize.COMMENT]
 except (IndentationError,tokenize.TokenError):return None

def _change_semantics(path,old_text,new_text):
 if path.endswith('.py') and old_text is not None and new_text is not None and old_text!=new_text:
  before,after=_python_tokens(old_text),_python_tokens(new_text)
  old_comments,new_comments=_python_comments(old_text),_python_comments(new_text)
  if before is not None and before==after and old_comments is not None and new_comments is not None and old_comments!=new_comments:
   return 'COMMENT_ONLY'
 return 'NOT_CLASSIFIED'

def format_change_facts(changes,max_chars=2400):
 facts=[]
 for item in changes.get('artifacts',[])[:24]:
  symbol='::'+item['symbol'] if item.get('symbol') else ''
  facts.append(f"Artifact delta: {item.get('kind','changed')} {item.get('artifact_type','artifact')} {item.get('file','')}"+symbol)
 for item in changes.get('files',[])[:12]:
  old=item.get('old_path') or '';new=item.get('new_path') or ''
  facts.append(f"Git file status {item.get('status','?')}: {old}"+(f" -> {new}" if new!=old else ''))
  changed=[line for line in item.get('patch','').splitlines() if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
  facts.extend('Diff line: '+line[:240] for line in changed[:12])
 text='\n'.join(facts)
 return text[:max_chars]

def detect(repo,base,head,before,after):
 base=revision(repo,base);head=revision(repo,head);fields=git(repo,'diff','--name-status','-z','-M',base,head,binary=True).decode().split('\0');files=[];i=0
 while i<len(fields) and fields[i]:
  status=fields[i];old=fields[i+1];new=old;i+=2
  if status.startswith(('R','C')):new=fields[i];i+=1
  patch=git(repo,'diff','--unified=0',base,head,'--',old,new);hunks=[{'old_start':int(m[1]),'old_count':int(m[2] or 1),'new_start':int(m[3]),'new_count':int(m[4] or 1)} for m in re.finditer(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',patch,re.M)]
  old_file=next((a for a in before if not a.symbol and a.file_path==old),None)
  new_file=next((a for a in after if not a.symbol and a.file_path==new),None)
  files.append({'status':status,'old_path':old,'new_path':new,'hunks':hunks,'patch':patch,
                'text_changed':bool(old_file and new_file and old_file.content!=new_file.content),
                'change_semantics':_change_semantics(new or old,old_file.content if old_file else None,new_file.content if new_file else None)})
 old={a.artifact_id:a for a in before};new={a.artifact_id:a for a in after};changes=[];paired=set();renames={f['old_path']:f['new_path'] for f in files if f['status'].startswith('R')}
 for aid,a in old.items():
  b=new.get(aid)
  if b is None and a.file_path in renames:
   matches=[x for x in after if x.file_path==renames[a.file_path] and x.symbol==a.symbol and x.artifact_type==a.artifact_type]
   if len(matches)==1:b=matches[0]
  if b:paired.add(b.artifact_id)
  kind='deleted' if b is None else ('renamed' if a.file_path!=b.file_path else 'modified')
  if b and a.content_hash==b.content_hash and kind!='renamed':continue
  changes.append({'artifact_id':aid,'new_artifact_id':b.artifact_id if b else None,'kind':kind,'artifact_type':a.artifact_type,'file':a.file_path,'symbol':a.symbol,'base_hash':a.content_hash,'head_hash':b.content_hash if b else None,'syntax_unchanged':bool(b and a.metadata.get('syntax_hash') and a.metadata.get('syntax_hash')==b.metadata.get('syntax_hash'))})
 for aid,a in new.items():
  if aid not in old and aid not in paired:changes.append({'artifact_id':aid,'new_artifact_id':aid,'kind':'added','artifact_type':a.artifact_type,'file':a.file_path,'symbol':a.symbol,'base_hash':None,'head_hash':a.content_hash,'syntax_unchanged':False})
 return {'base_commit':base,'head_commit':head,'files':files,'artifacts':changes,'semantic_equivalence':'NOT_RUN; syntax/content changes are not behavioural proofs'}
