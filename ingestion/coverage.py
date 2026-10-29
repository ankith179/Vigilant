"""Git inventory and extraction coverage; no semantic completeness claim."""
from collections import Counter
from pathlib import Path
from ingestion.git import inventory

LANGUAGES={'.py':'Python','.java':'Java','.js':'JavaScript','.jsx':'JSX','.ts':'TypeScript','.tsx':'TSX',
           '.c':'C','.h':'C/C++','.cc':'C++','.cpp':'C++','.cxx':'C++','.hpp':'C++','.hxx':'C++','.hh':'C++','.swift':'Swift','.go':'Go','.rs':'Rust','.kt':'Kotlin','.cs':'C#'}


def coverage(repo,commit,artifacts,graph):
    files={a.file_path:a for a in artifacts if not a.symbol}
    rows=inventory(repo,commit);languages={};exclusions=Counter()
    for row in rows:
        a=files.get(row['file']);failed=bool(a and (a.metadata.get('parse_error') or a.metadata.get('parse_has_error')))
        row['extracted']=a is not None
        row['parse_status']='FAILED' if failed else ('EXTRACTED' if a else 'NOT_EXTRACTED')
        row['compiler_status']=a.metadata.get('compiler_status','NOT_RUN') if a else 'NOT_RUN'
        row['compiler_context_complete']=a.metadata.get('compiler_context',{}).get('build_configuration_verified',False) if a else False
        row['language']=LANGUAGES.get(Path(row['file']).suffix.lower(),'Other/text')
        if row['exclusion_reason']:exclusions[row['exclusion_reason']]+=1
        stat=languages.setdefault(row['language'],{'discovered':0,'eligible':0,'extracted':0,'parse_failures':0})
        stat['discovered']+=1;stat['eligible']+=row['eligible'];stat['extracted']+=a is not None;stat['parse_failures']+=failed
    calls=[(a,call) for a in artifacts if a.artifact_type not in {'source_file','class'} for call in a.metadata.get('calls',[])]
    by={a.artifact_id:a for a in artifacts};matched=0
    for a,call in calls:
        targets=[by[t] for _,t,e in graph.out_edges(a.artifact_id,data=True)
                 if e.get('relation_type') in {'CALLS','TESTS'} and t in by]
        matched+=any(t.symbol.split('(')[0].split('.')[-1]==call.split('.')[-1] for t in targets)
    compiler_edges=[e for _,_,e in graph.edges(data=True) if e.get('method')=='compiler-usr']
    return {'policy':'git-inventory-coverage-v2','commit_id':commit,'discovered_files':len(rows),
            'eligible_files':sum(r['eligible'] for r in rows),'extracted_files':len(files),
            'eligible_but_not_extracted':[r['file'] for r in rows if r['eligible'] and not r['extracted']],
            'parse_failures':[r['file'] for r in rows if r['parse_status']=='FAILED'],
            'exclusions_by_reason':dict(exclusions),'languages':languages,'inventory':rows,
            'symbol_count':sum(bool(a.symbol) for a in artifacts),
            'test_artifacts':sum(a.artifact_type in {'test','test_method'} for a in artifacts),
            'requirement_artifacts':sum(a.artifact_type=='requirement' for a in artifacts),
            'call_references':len(calls),'candidate_matched_calls':matched,
            'unresolved_or_unmodelled_calls':len(calls)-matched,
            'compiler_reference_edges':len(compiler_edges),
            'compiler_parse_files':sum(r['compiler_status'] in {'PARSED','SYNTAX_VALIDATED'} for r in rows),
            'compiler_unavailable_files':[r['file'] for r in rows if r['compiler_status']=='NOT_AVAILABLE'],
            'semantic_resolution':'PARTIAL_SNAPSHOT_COMPILER_REFERENCES' if compiler_edges else 'NOT_ESTABLISHED',
            'complete_test_coverage':'NOT_ESTABLISHED',
            'limitations':['Extracted text is not proof of syntactic or semantic coverage.',
                          'Candidate name matches are not compiler-resolved references.',
                          'Native compiler references use recorded snapshot include/standard assumptions, not a verified project build.',
                          'Excluded files and unobserved dynamic calls can contain relevant evidence.']}
