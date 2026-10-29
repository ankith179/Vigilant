"""Machine enumeration of a reviewed search boundary, not proof of semantic coverage."""
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ingestion.git import inventory, revision
from ingestion.models import digest


class SearchEntry(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    file: str
    object_id: str=Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    disposition: Literal['SEARCHED','EXCLUDED','UNKNOWN']
    rationale: str=Field(min_length=1,max_length=1200)
    artifact_ids: list[str]


class SearchInventory(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    commit_id: str=Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    prefixes: list[str]=Field(min_length=1,max_length=40)
    entries: list[SearchEntry]=Field(max_length=20_000)

    @model_validator(mode='after')
    def unique_paths(self):
        if len({e.file for e in self.entries})!=len(self.entries):raise ValueError('Duplicate search inventory paths')
        for p in [*self.prefixes,*[e.file for e in self.entries]]:
            if p!='.' and (not p or PurePosixPath(p).is_absolute() or '..' in PurePosixPath(p).parts or '\\' in p or str(PurePosixPath(p))!=p):
                raise ValueError('Search boundary requires canonical repository-relative paths')
        if any(not e.rationale.strip() or len(e.artifact_ids)!=len(set(e.artifact_ids)) for e in self.entries):
            raise ValueError('Search rationale and distinct artifact identities required')
        return self


def in_boundary(file,prefixes):
    return any(p=='.' or file==p or file.startswith(p+'/') for p in prefixes)


def validate_inventory(repo,manifest,artifact_at,searched_ids,complete,*,source_policy=None,repository=None):
    if source_policy is None:
        if revision(repo,manifest.commit_id)!=manifest.commit_id:raise ValueError('Search inventory revision unavailable')
        actual={r['file']:r for r in inventory(repo,manifest.commit_id) if in_boundary(r['file'],manifest.prefixes)}
    else:
        from evaluation.review_intake import OfflineReviewSourcePolicy
        from ingestion.git import INCLUDED_SUFFIXES,IGNORED_PARTS
        if type(source_policy) is not OfflineReviewSourcePolicy:raise ValueError('Validated offline policy required')
        # UNKNOWN/EXCLUDED rows need tree identities, never blob contents or sizes.
        actual={p:{**r,'eligible':r['kind']=='blob' and r['mode'] in {'100644','100755'} and
            Path(p).suffix.lower() in INCLUDED_SUFFIXES and not set(Path(p).parts)&IGNORED_PARTS}
            for p,r in source_policy.tree(repository,manifest.commit_id).items() if in_boundary(p,manifest.prefixes)}
    entries={e.file:e for e in manifest.entries}
    if not actual or set(actual)!=set(entries):raise ValueError('Search inventory does not enumerate the complete pinned boundary')
    searched=set();receipts=[]
    for path,e in entries.items():
        if e.object_id!=actual[path]['object_id']:raise ValueError('Search inventory Git object mismatch')
        if e.disposition=='UNKNOWN' and complete:raise ValueError('Unknown inventory regions prohibit reviewed completeness')
        if e.disposition=='SEARCHED':
            if not actual[path]['eligible'] or not e.artifact_ids:raise ValueError('Searched files require eligible source-backed artifacts')
            for aid in e.artifact_ids:
                a=artifact_at(aid,manifest.commit_id)
                if a.artifact_id!=aid or a.commit_id!=manifest.commit_id:
                    raise ValueError('Search artifact identity/revision differs from pinned inventory')
                if a.file_path!=path:raise ValueError('Search artifact file differs from enumerated file')
                from rag.evidence import evidence,verify_git
                if source_policy is None:
                    if verify_git([evidence(a)],[a],repo):raise ValueError('Search artifact differs from pinned Git')
                else:
                    from evaluation.change_cases import SourceReference
                    ref=SourceReference(artifact_id=a.artifact_id,commit_id=a.commit_id,file=a.file_path,
                        content_hash=a.content_hash,start_line=a.start_line,end_line=a.end_line)
                    receipts.append(source_policy.verify(repository,a,ref))
                searched.add(aid)
        elif e.artifact_ids:raise ValueError('Unsearched files cannot attest searched artifact identities')
    if searched!=set(searched_ids):raise ValueError('Searched artifact identities differ from inventory manifest')
    result={'policy':'pinned-search-inventory-v1','fingerprint':digest(manifest.model_dump()),
            'commit_id':manifest.commit_id,'prefixes':manifest.prefixes,'files':len(actual),
            'dispositions':dict(Counter(e.disposition for e in manifest.entries)),
            'status':'MACHINE_ENUMERATED_REVIEWED_BOUNDARY' if complete else 'MACHINE_ENUMERATED_PARTIAL_BOUNDARY',
            'semantic_search_completeness':'REVIEWER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED',
            'whole_repository_coverage':False}
    if source_policy is not None:result.update(source_policy=dict(source_policy.provenance),source_verification_receipts=receipts)
    return result
