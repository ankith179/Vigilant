"""Opt-in, read-only endpoint observations in a separate parser namespace.

Candidates never establish logical continuity or transfer canonical relationships.
"""
from collections import Counter
from pathlib import Path, PurePosixPath
from importlib.metadata import version, PackageNotFoundError
import hashlib
import re
import subprocess
import sys

from ingestion.git import git, inventory, revision
from ingestion.models import digest
from ingestion.parsers import extract, PARSER_POLICY

POLICY = 'source-backed-lineage-observations-v1'
MAX_FILES = 64
MAX_ARTIFACTS = 2000
HISTORY_LIMIT = 32
ROOT = Path(__file__).resolve().parents[1]
MODULES = ('change_analysis/lineage.py', 'ingestion/models.py', 'ingestion/git.py',
           'ingestion/parsers.py', 'ingestion/native.py', 'requirements-core.txt')


def _path(value):
    if not isinstance(value,str) or not value or '\\' in value or '\0' in value or '\ufffd' in value:
        raise ValueError('Invalid selected path')
    p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or p.as_posix()!=value:
        raise ValueError('Selected paths must be canonical repository-relative paths')
    return value


def _key(a):
    return (a.file_path,a.artifact_type,a.symbol)


def _group(a):
    return (a.file_path,a.artifact_type,re.sub(r'#occurrence-\d+$','',a.symbol))


def _source(repo, commit, paths, indexed, project, repository):
    receipts={};texts={}
    for path in paths:
        row=indexed.get(path)
        if row is None:
            receipts[path]={'status':'ABSENT_AT_THIS_REVISION'};continue
        if not row['eligible']:raise ValueError('Selected source is excluded: '+path)
        raw=git(repo,'cat-file','blob',row['object_id'],binary=True)
        algorithm='sha1' if len(row['object_id'])==40 else 'sha256'
        oid=hashlib.new(algorithm,b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if oid!=row['object_id']:raise ValueError('Git blob integrity failure')
        receipt={'object_id':oid,'raw_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        if b'\0' in raw:
            receipts[path]={**receipt,'status':'UNAVAILABLE_BINARY'};continue
        try:text=raw.decode('utf-8-sig');decoder='utf-8-sig'
        except UnicodeDecodeError:text=raw.decode('cp1252',errors='replace');decoder='cp1252-replacement'
        texts[path]=text;receipts[path]={**receipt,'status':'SOURCE_VERIFIED','decoder':decoder}
    items=[]
    for path,text in texts.items():
        items.extend(extract(project,repository,commit,path,text,source_files=texts))
        if len(items)>MAX_ARTIFACTS:raise ValueError('Artifact scope exceeds observer limit')
    return items,receipts


def _history(repo, base, head, paths):
    try:common=git(repo,'merge-base',base,head)
    except subprocess.CalledProcessError as exc:
        if exc.returncode!=1:raise
        common=None
    relation=('SAME_REVISION' if base==head else 'FORWARD_ANCESTRY' if common==base else
              'REVERSE_ANCESTRY' if common==head else 'DIVERGED' if common else 'UNRELATED')
    result={'relation':relation,'merge_base':common,'commit_limit':HISTORY_LIMIT,
            'status':'NOT_REVIEWED','commits':[],'file_deletions':[]}
    if relation not in {'FORWARD_ANCESTRY','SAME_REVISION'}:return result
    commits=git(repo,'rev-list','--ancestry-path',f'--max-count={HISTORY_LIMIT+1}',base+'..'+head).splitlines()
    result['commits']=commits
    if len(commits)>HISTORY_LIMIT:
        result['status']='INCOMPLETE_COMMIT_LIMIT';return result
    result['status']='BOUNDED_FILE_DELETION_SCAN_COMPLETE'
    # ponytail: bounded Git file-history scan; symbol history needs a separate reviewed policy.
    for commit in commits:
        raw=git(repo,'diff-tree','--root','-r','-m','--no-commit-id','--name-only',
                '--diff-filter=D','--no-renames','-z',commit,'--',*paths,binary=True)
        for path in sorted(set(raw.decode('utf-8').split('\0'))- {''}):
            result['file_deletions'].append({'commit':commit,'path':path})
    return result


def observe(repo, *, project, repository, base, head, paths=None):
    """Read pinned Git sources, parse selected files, return unreviewed sidecar data.

    `repository` is caller-supplied context, not an authenticated remote identity.
    No Store, frozen artifact list, model, subject executable or worktree is written.
    """
    if any(not isinstance(v,str) or not v.strip() or len(v)>128 for v in (project,repository)):
        raise ValueError('Explicit bounded project/repository context required')
    for value in (base,head):
        if not isinstance(value,str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',value):
            raise ValueError('Exact pinned commit SHA required')
        if revision(repo,value)!=value:raise ValueError('Revision does not resolve exactly')
    indexed={role:{r['file']:r for r in inventory(repo,c)} for role,c in [('base',base),('head',head)]}
    if paths is not None and (not isinstance(paths,(list,tuple)) or not paths):
        raise ValueError('Nonempty selected-path list required')
    selected=sorted({_path(p) for p in paths}) if paths is not None else sorted(
        {p for files in indexed.values() for p,row in files.items() if row['eligible']})
    if not selected or len(selected)>MAX_FILES:raise ValueError('Select between 1 and 64 source files')
    for path in selected:
        _path(path)
        if not any(path in files for files in indexed.values()):raise ValueError('Selected path absent from both revisions')
    fingerprints={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in MODULES}
    versions={}
    for package in ('tree-sitter','tree-sitter-java','tree-sitter-javascript',
                    'tree-sitter-typescript','tree-sitter-swift','libclang'):
        try:versions[package]=version(package)
        except PackageNotFoundError:versions[package]='NOT_INSTALLED'
    runtime={'python':sys.version.split()[0],'git':git(repo,'--version'),'parser_packages':versions}
    observer_project=project+':'+POLICY
    observer_repo=digest(POLICY,project,repository,PARSER_POLICY,fingerprints,runtime)
    roles={};items={}
    for role,commit in [('base',base),('head',head)]:
        items[role],receipts=_source(repo,commit,selected,indexed[role],observer_project,observer_repo)
        roles[role]={'commit':commit,'tree':git(repo,'rev-parse',commit+'^{tree}'),
                     'selected_sources':receipts,'total_inventory_files':len(indexed[role]),
                     'unselected_inventory_files':len(set(indexed[role])-set(selected))}
    history=_history(repo,base,head,selected)
    # Git -M evidence only. Equal-content copies and cross-file symbols are not merged.
    # Preserve separately the actual rename heuristic used to form candidates.
    raw=git(repo,'diff','--name-status','-z','-M',base,head,binary=True).decode('utf-8').split('\0')
    renames={};i=0
    while i<len(raw) and raw[i]:
        status,old=raw[i:i+2];i+=2
        if status.startswith(('R','C')):
            new=raw[i];i+=1
            if status.startswith('R'):renames[old]={'new_path':new,'git_status':status}
    blocked={};groups={role:Counter(_group(a) for a in values) for role,values in items.items()}
    bad_files={role:{a.file_path for a in values if a.metadata.get('parse_error') or a.metadata.get('parse_has_error')}
               for role,values in items.items()}
    for role,values in items.items():
        for a in values:
            reason=None
            if history['relation'] not in {'FORWARD_ANCESTRY','SAME_REVISION'}:reason='NONLINEAR_REVISION_SCOPE'
            elif history['status']=='INCOMPLETE_COMMIT_LIMIT':reason='HISTORY_LIMIT_UNKNOWN'
            elif a.file_path in bad_files[role]:reason='PARSE_ERROR_UNKNOWN'
            elif any(g.get(_group(a),0)>1 for g in groups.values()) or a.metadata.get('identity_ambiguity'):
                reason='DUPLICATE_SYMBOL_GROUP'
            elif any(d['path']==a.file_path and not (role=='base' and a.file_path in renames and d['commit']==head)
                     for d in history['file_deletions']):reason='FILE_DELETION_HISTORY'
            if reason:blocked[(role,a.artifact_id)]=reason
    def endpoint(a,role):
        return {'observer_artifact_id':a.artifact_id,'commit':a.commit_id,
                'path':a.file_path,'artifact_type':a.artifact_type,'symbol':a.symbol,
                'content_hash':a.content_hash,'start_line':a.start_line,'end_line':a.end_line,
                'source_receipt':roles[role]['selected_sources'][a.file_path]}
    observations=[];paired=set()
    content_counts={role:Counter((a.artifact_type,a.symbol,a.content_hash) for a in values)
                    for role,values in items.items()}
    after={_key(a):a for a in items['head']}
    def append(a,b,status,reason,git_status=None):
        row={'status':status,'reason':reason,'base':endpoint(a,'base') if a else None,
             'head':endpoint(b,'head') if b else None,'git_status':git_status,
             'lifecycle':'UNREVIEWED','logical_continuity':'UNKNOWN',
             'semantic_equivalence':'NOT_ESTABLISHED','relationship_transfer_allowed':False}
        row['observation_id']=digest(POLICY,observer_repo,base,head,row)
        observations.append(row)
    for a in items['base']:
        reason=blocked.get(('base',a.artifact_id));b=after.get(_key(a));status='SAME_KEY_CANDIDATE';git_status=None
        if b is None and a.file_path in renames:
            evidence=renames[a.file_path];b=after.get((evidence['new_path'],a.artifact_type,a.symbol))
            status='GIT_RENAME_CANDIDATE';git_status=evidence['git_status']
        if b is not None:
            reason=reason or blocked.get(('head',b.artifact_id))
            if status=='GIT_RENAME_CANDIDATE' and (
                content_counts['base'][(a.artifact_type,a.symbol,a.content_hash)]>1 or
                content_counts['head'][(b.artifact_type,b.symbol,b.content_hash)]>1):
                reason=reason or 'DUPLICATED_CONTENT_RENAME'
            if b.artifact_id in paired:reason='NON_UNIQUE_TARGET'
        if b is not None and not reason:
            paired.add(b.artifact_id);append(a,b,status,'ENDPOINT_SOURCE_CORRESPONDENCE_ONLY',git_status)
        else:append(a,None,'UNKNOWN',reason or 'NO_UNIQUE_SUPPORTED_ENDPOINT')
    for b in items['head']:
        if b.artifact_id not in paired:append(None,b,'UNKNOWN',blocked.get(('head',b.artifact_id)) or 'NO_UNIQUE_SUPPORTED_ENDPOINT')
    result={'policy':POLICY,'scope':{'project':project,'repository':repository,'base':base,'head':head,'selected_paths':selected},
            'observer_namespace':{'project':observer_project,'repository':observer_repo,'parser_policy':PARSER_POLICY},
            'source_sha256':fingerprints,'runtime':runtime,
            'sources':roles,'history':history,'observations':observations,
            'denominators':{'selected_files':len(selected),'base_artifacts':len(items['base']),'head_artifacts':len(items['head']),
                            'candidate_pairs':len(paired),'unknown_observations':sum(r['status']=='UNKNOWN' for r in observations),
                            'unavailable_file_sides':sum(r['status']!='SOURCE_VERIFIED' for role in roles.values() for r in role['selected_sources'].values())},
            'canonical_writes':0,'model_calls':0,'quality_target_91':'NOT_EVALUATED',
            'limitations':['Selected-file syntax scope; not complete project or impact coverage',
                           'File-deletion scan is bounded; symbol disappearance/recreation within surviving files is unresolved',
                           'Git similarity is heuristic; candidates are not approved logical identities',
                           'No graph, citation or obligation propagation; canonical artifact IDs remain unchanged',
                           'Caller context is not authenticated repository ownership; no independent review performed']}
    result['record_id']=digest(POLICY,result)
    return result


def verify(repo, record, *, project, repository, base, head, paths=None):
    """Freshly reconstruct exact scope; fail closed on tampering, code or scope drift."""
    if not isinstance(record,dict):raise ValueError('Lineage object required')
    scope=record.get('scope',{})
    if any(scope.get(k)!=v for k,v in {'project':project,'repository':repository,'base':base,'head':head}.items()):
        raise ValueError('Foreign lineage scope')
    fresh=observe(repo,project=project,repository=repository,base=base,head=head,paths=paths)
    if record!=fresh:raise ValueError('Lineage record differs from freshly verified sources/policy')
    return fresh
