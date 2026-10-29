"""Stage bounded public clones; failed imports never leave reusable partial repos."""
from pathlib import Path
import os,subprocess,tempfile,time
from urllib.parse import urlsplit

_PUBLIC_GIT_HOSTS={'github.com','gitlab.com'}

def validate_public_repository_url(value):
 if not isinstance(value,str) or not value or any(ord(c)<=32 or ord(c)==127 or c=='\\' for c in value):
  raise ValueError('Expected a public HTTPS GitHub or GitLab repository URL')
 try:parsed=urlsplit(value);port=parsed.port
 except ValueError as exc:raise ValueError('Expected a public HTTPS GitHub or GitLab repository URL') from exc
 host=(parsed.hostname or '').lower()
 segments=[part for part in parsed.path.split('/') if part]
 if (parsed.scheme.lower()!='https' or host not in _PUBLIC_GIT_HOSTS or
     port not in {None,443} or parsed.username is not None or parsed.password is not None or
     parsed.query or parsed.fragment or len(segments)<2 or any(part in {'.','..'} for part in segments)):
  raise ValueError('Expected a public HTTPS GitHub or GitLab repository URL')
 return parsed

def clone_repository(url,destination,max_bytes=512*1024*1024,timeout=180):
 validate_public_repository_url(url)
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='clone-',dir=destination.parent) as folder, tempfile.TemporaryFile() as errors:
  staged=Path(folder)/'repository';hooks=Path(folder)/'disabled-hooks';hooks.mkdir()
  global_config=Path(folder)/'empty.gitconfig';global_config.touch()
  environment=os.environ.copy()
  for key in ('GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS','GIT_ASKPASS','SSH_ASKPASS',
              'GIT_DIR','GIT_COMMON_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY',
              'GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_SHALLOW_FILE','GIT_NAMESPACE','GIT_PREFIX',
              'GIT_CEILING_DIRECTORIES','GIT_DISCOVERY_ACROSS_FILESYSTEM','GIT_SSH','GIT_SSH_COMMAND'):
   environment.pop(key,None)
  environment={key:value for key,value in environment.items() if not key.startswith(('GIT_CONFIG_KEY_','GIT_CONFIG_VALUE_'))}
  environment.update({'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':str(global_config),
                      'GIT_CEILING_DIRECTORIES':str(Path(folder).resolve()),'GIT_TERMINAL_PROMPT':'0'})
  command=['git','-c','core.hooksPath='+str(hooks),'-c','http.followRedirects=false','-c','protocol.ext.allow=never',
           '-c','protocol.file.allow=never','clone','--depth','40','--no-checkout','--',url,str(staged)]
  p=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=errors,env=environment,cwd=folder);start=time.monotonic()
  def size():
   total=0
   for entry in staged.rglob('*') if staged.exists() else ():
    try:
     if entry.is_file() and not entry.is_symlink():total+=entry.stat().st_size
    except FileNotFoundError:pass
   return total
  try:
   while p.poll() is None:
    if time.monotonic()-start>timeout:raise ValueError('Clone exceeded time budget')
    if size()>max_bytes:raise ValueError('Clone exceeded storage budget')
    try:p.wait(timeout=.25)
    except subprocess.TimeoutExpired:pass
   if p.returncode:
    errors.seek(0);detail=errors.read(2048).decode('utf-8',errors='replace').replace(url,'[repository]');raise ValueError('Clone failed: '+' '.join(detail.split())[:400])
   if size()>max_bytes:raise ValueError('Clone exceeded storage budget')
   os.replace(staged,destination)
  finally:
   if p.poll() is None:
    p.terminate()
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:p.kill();p.wait()
