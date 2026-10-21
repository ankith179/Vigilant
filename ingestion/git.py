"""Read Git objects without executing repository code or hooks."""
from pathlib import Path
import subprocess

def git(repo,*args,binary=False):
 r=subprocess.run(['git','-c','core.hooksPath=/dev/null','-C',str(repo),*args],check=True,capture_output=True,timeout=180)
 return r.stdout if binary else r.stdout.decode('utf-8',errors='replace').strip()
def revision(repo,rev='HEAD'):
 if rev.startswith('-'):raise ValueError('Invalid revision')
 return git(repo,'rev-parse','--verify','--end-of-options',rev+'^{commit}')
def snapshot(repo,rev,max_bytes=2_000_000):
 sha=revision(repo,rev)
 for entry in git(repo,'ls-tree','-rlz',sha,binary=True).split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t',1);mode,kind,oid,size=meta.split();path=path.decode()
  if mode not in {b'100644',b'100755'} or int(size)>max_bytes:continue
  if any(x in Path(path).parts for x in ['node_modules','.git','.venv','vendor','dist','build']):continue
  if Path(path).suffix.lower() not in {'.py','.java','.js','.jsx','.ts','.tsx','.md','.rst','.txt','.json','.yaml','.yml','.toml','.sql','.csv','.sh'}:continue
  raw=git(repo,'cat-file','blob',oid.decode(),binary=True)
  if b'\0' in raw:continue
  try:text=raw.decode('utf-8-sig')
  except UnicodeDecodeError:text=raw.decode('cp1252',errors='replace')
  yield path,text
