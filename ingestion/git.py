"""Read Git objects without executing repository code or hooks."""
from pathlib import Path
import os
import subprocess

def git(repo,*args,binary=False):
 if args and args[0] in {'diff','show','log'}:args=(args[0],'--no-ext-diff','--no-textconv',*args[1:])
 r=subprocess.run(['git','--no-pager','-c','core.hooksPath='+os.devnull,'-c','core.fsmonitor=false','-C',str(repo),*args],check=True,capture_output=True,timeout=180)
 return r.stdout if binary else r.stdout.decode('utf-8',errors='replace').strip()
def revision(repo,rev='HEAD'):
 if rev.startswith('-'):raise ValueError('Invalid revision')
 return git(repo,'rev-parse','--verify','--end-of-options',rev+'^{commit}')
INCLUDED_SUFFIXES={'.py','.java','.js','.jsx','.ts','.tsx','.c','.h','.cc','.cpp','.cxx','.hpp','.hxx','.hh','.swift','.md','.rst','.txt','.json','.yaml','.yml','.toml','.sql','.csv','.sh'}
IGNORED_PARTS={'node_modules','.git','.venv','vendor','dist','build'}


def inventory(repo,rev,max_bytes=2_000_000):
 sha=revision(repo,rev);rows=[]
 for entry in git(repo,'ls-tree','-rlz',sha,binary=True).split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t',1);mode,kind,oid,size=meta.split();path=path.decode('utf-8',errors='replace')
  reason=('not-regular-file' if mode not in {b'100644',b'100755'} else
          'excluded-directory' if any(x in IGNORED_PARTS for x in Path(path).parts) else
          'size-limit' if int(size)>max_bytes else
          'unsupported-suffix' if Path(path).suffix.lower() not in INCLUDED_SUFFIXES else None)
  rows.append({'file':path,'object_id':oid.decode(),'size_bytes':int(size) if size!=b'-' else None,
               'mode':mode.decode(),'eligible':reason is None,'exclusion_reason':reason})
 return rows


def snapshot(repo,rev,max_bytes=2_000_000):
 for row in inventory(repo,rev,max_bytes):
  if not row['eligible']:continue
  raw=git(repo,'cat-file','blob',row['object_id'],binary=True)
  if b'\0' in raw:continue
  try:text=raw.decode('utf-8-sig')
  except UnicodeDecodeError:text=raw.decode('cp1252',errors='replace')
  yield row['file'],text
