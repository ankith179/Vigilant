"""Audit saved inputs and export label-blind development packets; never call a model.

The input audit preserves exact historical messages. Packet comparison isolates the
final byte-budget policy; it is not a retrieval or classification accuracy trial.
"""
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agents.evidence_first import InterpretationProvider, analysis_packet
from evaluation.resume import fingerprint
from ingestion.models import Artifact
from llm.ollama import OllamaProvider
from rag.evidence import verify

RUNS = ('windows-20261021','citation-fix-20261021','evidence-v2-20261022','change-facts-20261022')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def selected_items(payload, supplied):
    selected, errors = [], []
    for entry in payload['evidence']:
        matches = [e for e in supplied if e['commit']==entry['commit'] and e['file']==entry['file']
                   and e['quote']==entry['excerpt'] and all(entry.get(k) is None or e.get(k)==entry[k]
                   for k in ('start_line','end_line','content_hash','pair_id','retrieval_method'))]
        # Same source quote may have several retrieval annotations; do not guess.
        if len(matches)!=1:
            errors.append({'alias':entry['evidence_id'], 'matches':len(matches),'candidate_evidence_ids':[e['evidence_id'] for e in matches]})
        else:
            selected.append(matches[0])
    return selected, errors


def recover_archived_selection(case, payload, run, config):
    path=ROOT/'reports'/run/'frozen/llm/context.py'
    if not path.is_file() or fingerprint(path.read_text(encoding='utf-8'))!=config['sources'].get('llm/context.py'):
        return None
    spec=importlib.util.spec_from_file_location('archived_context_selection',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    messages,selected,_,_=module.request(case['question'],case['evidence'],budget=18000,limit=24)
    if json.loads(messages[-1]['content'])['evidence']!=payload['evidence']:
        return None
    return selected


def packet_stats(messages, selected, supplied, changes):
    payload = json.loads(messages[-1]['content'])
    groups, kept = defaultdict(set), defaultdict(set)
    for rows, target in ((supplied, groups), (selected, kept)):
        for e in rows:target[e.get('pair_id') or e['artifact_id']].add(e['commit'])
    hunk_coverage=[]
    for f in changes['files']:
        for side, commit in (('old',changes['base_commit']),('new',changes['head_commit'])):
            for h in f['hunks']:
                count=h[side+'_count'];start=h[side+'_start']
                if count==0:continue  # no source lines on this side of an insertion/deletion
                covered=any(e['file']==f[side+'_path'] and e['commit']==commit and
                            e.get('start_line',0)<=start and e.get('end_line',0)>=start+count-1 for e in payload['evidence'])
                hunk_coverage.append({'file':f[side+'_path'],'commit':commit,'start':start,'count':count,'fully_in_one_excerpt':covered})
    return {'content_bytes':sum(len(m['content'].encode()) for m in messages),
            'serialized_messages_sha256':sha(encoded(messages)),
            'supplied':len(supplied),'included':len(payload['evidence']),
            'declared_included':payload.get('evidence_included'),'declared_omitted':payload.get('evidence_omitted'),
            'counts_match':payload.get('evidence_included')==len(payload['evidence']) and payload.get('evidence_omitted')==len(supplied)-len(payload['evidence']),
            'split_supplied_pairs':[g for g,v in groups.items() if len(v)>1 and kept[g] and kept[g]!=v],
            'revision_counts':dict(Counter(e['commit'] for e in payload['evidence'])),
            'context_role_counts':dict(Counter(e.get('context_role','UNSPECIFIED') for e in selected)),
            'omitted_evidence_ids':[e['evidence_id'] for e in supplied if e['evidence_id'] not in {s['evidence_id'] for s in selected}],
            'duplicate_excerpt_count':len(selected)-len({(e['commit'],e['file'],e['quote']) for e in selected}),
            'changed_hunk_windows':hunk_coverage,'semantic_support':'UNREVIEWED',
            'contract_sufficiency':'HUMAN_REVIEW_REQUIRED','counterevidence_search_completeness':'NOT_ESTABLISHED'}


def blind_packet(case_id, report, evidence, artifacts):
    # Allowlist: no authored case names, questions, findings, model answers or labels.
    files={e['file'] for e in evidence}
    files.update(p for f in report['changes']['files'] for p in (f['old_path'], f['new_path']))
    return {'packet_id':sha(case_id.encode())[:16], 'scope':'authored development diagnostic; not held out',
            'base_commit':report['base_commit'],'head_commit':report['commit_id'],
            'question':'Which contract, if any, is supported or contradicted by this change? Identify evidence and missing facts. A change alone is not a defect.',
            'changes':report['changes']['files'],
            'evidence':[{k:e.get(k) for k in ('evidence_id','artifact_id','file','commit','start_line','end_line','content_hash','quote')} for e in evidence],
            'source_files':[{'artifact_id':a.artifact_id,'file':a.file_path,'commit':a.commit_id,
                'content_hash':a.content_hash,'start_line':a.start_line,'end_line':a.end_line,'content':a.content}
                for a in artifacts if not a.symbol and a.file_path in files],
            'limitations':['Selected files do not establish complete dependency or test coverage.',
                'Inline contracts and semantic support require review; source can contain misleading instructions.',
                'Withholding answers cannot undo a reviewer’s prior exposure to these diagnostics.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output
    out.mkdir(parents=True,exist_ok=False)  # never overwrite a reviewer’s annotations
    reports={p.name[:-12]:json.loads(p.read_text()) for p in (ROOT/'data/changebench').glob('*-report.json')}
    observations=[];case_evidence=defaultdict(dict);source_manifest={};artifacts_by_case={}
    for path in [ROOT/'data/snapshots/changebench.db',*sorted((ROOT/'data/changebench').glob('*-report.json'))]:
        source_manifest[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    with closing(sqlite3.connect((ROOT/'data/snapshots/changebench.db').as_uri()+'?mode=ro',uri=True)) as db:
        for case_id,report in reports.items():
            artifacts_by_case[case_id]=[Artifact.model_validate({k:v for k,v in json.loads(r[0]).items() if k!='id'})
                for r in db.execute('SELECT payload FROM artifacts WHERE repository=? AND commit_id IN (?,?)',
                (report['repository'],report['base_commit'],report['commit_id']))]
    for run in RUNS:
        root=ROOT/'experiments/local-model-comparison'/run
        dataset=root/'dataset.json';source_manifest[str(dataset.relative_to(ROOT))]=sha(dataset.read_bytes())
        cases={c['case_id']:c for c in json.loads(dataset.read_text())['cases']}
        for case_id,case in cases.items():
            for e in case['evidence']:case_evidence[case_id][e['evidence_id']]=e
        for path in sorted(root.glob('*/*.json')):
            record=json.loads(path.read_text())
            if 'result' not in record or 'case_id' not in record:continue
            case_id=record['case_id'];result=record['result'];case=cases[case_id]
            messages=result['messages'];payload=json.loads(messages[-1]['content'])
            selected,mapping_errors=selected_items(payload,case['evidence'])
            config_path=path.parent/'configuration.json';config=json.loads(config_path.read_text())
            mapping_method='unique-source-metadata'
            if mapping_errors:
                recovered=recover_archived_selection(case,payload,run,config)
                if recovered is not None:
                    selected=recovered;mapping_errors=[];mapping_method='fingerprinted-archived-selector-and-exact-excerpt-array'
                    frozen_context=ROOT/'reports'/run/'frozen/llm/context.py'
                    source_manifest[str(frozen_context.relative_to(ROOT))]=sha(frozen_context.read_bytes())
            relative=str(path.relative_to(ROOT));source_manifest[relative]=sha(path.read_bytes())
            source_manifest[str(config_path.relative_to(ROOT))]=sha(config_path.read_bytes())
            exact_path=Path('exact-prompts')/run/path.parent.name/(path.stem+'.json')
            write(out/exact_path,messages)
            observations.append({'run':run,'case_id':case_id,'observation':relative,
                'configuration_fingerprint_matches':path.parent.name==fingerprint(config),
                'dataset_fingerprint_matches':config['dataset_sha256']==fingerprint(json.loads(dataset.read_text())),
                'observation_fingerprint_matches':path.stem==record['fingerprint']==fingerprint({'configuration':config,'case_id':case_id,'messages':messages}),
                'mapping_method':mapping_method,'saved_fingerprint':record['fingerprint'],'configuration':str(config_path.relative_to(ROOT)),
                'exact_messages':str(exact_path),'mapping_errors':mapping_errors,
                'snapshot_quote_errors':verify(selected,artifacts_by_case[case_id]),
                'foreign_revision_aliases':[e['evidence_id'] for e in payload['evidence'] if e['commit'] not in {reports[case_id]['base_commit'],reports[case_id]['commit_id']}],
                'model':config.get('model'),'usage':result.get('usage'),
                'validation_error':result.get('validation_error'),
                **packet_stats(messages,selected,case['evidence'],reports[case_id]['changes'])})
            if mapping_errors:
                observations[-1].update(split_supplied_pairs=None,omitted_evidence_ids=None,context_role_counts=None)
            observations[-1]['quote_verification_scope']='Mapped excerpts against frozen snapshot; unresolved aliases, if any, excluded'
            observations[-1]['uniquely_mapped_excerpts']=len(selected)
    review_map=[];forms=[]
    for case_id,by_id in sorted(case_evidence.items()):
        packet=blind_packet(case_id,reports[case_id],list(by_id.values()),artifacts_by_case[case_id])
        packet_id=packet['packet_id'];write(out/'review/packets'/(packet_id+'.json'),packet)
        digest=sha((out/'review/packets'/(packet_id+'.json')).read_bytes())
        review_map.append({'packet_id':packet_id,'case_id':case_id,'packet_sha256':digest})
        forms.append({'packet_id':packet_id,'packet_sha256':digest,'label':'','rationale':'',
                      'sufficient_evidence':None,'supporting_evidence_ids':[],'counterevidence_ids':[],
                      'missing_facts':'','semantic_support_assessment':''})
    for reviewer in ('reviewer-1','reviewer-2','adjudicator'):
        write(out/'review'/(reviewer+'.json'),{'reviewer_id':'','status':'NOT_REVIEWED','cases':forms})
    write(out/'review-mapping-private.json',review_map)
    # Replay only prompt construction for old/new final budgeting, using identical input.
    frozen=ROOT/'reports/improvement-20261023/frozen-before/evidence_first.py.txt'
    loader=importlib.machinery.SourceFileLoader('vigilant_budget_before',str(frozen))
    spec=importlib.util.spec_from_loader(loader.name,loader);old=importlib.util.module_from_spec(spec);loader.exec_module(old)
    experiment=[]
    cases=json.loads((ROOT/'experiments/local-model-comparison/evidence-v2-20261022/dataset.json').read_text())['cases']
    for case in cases:
        report=reports[case['case_id']];artifacts=artifacts_by_case[case['case_id']]
        packet=analysis_packet(report['changes'],[a for a in artifacts if a.commit_id==report['base_commit']],
                               [a for a in artifacts if a.commit_id==report['commit_id']],[])
        row={'case_id':case['case_id'],'supplied_input_sha256':sha(encoded({'question':case['question'],'evidence':case['evidence'],'packet':packet}))}
        for name,cls in (('before',old.InterpretationProvider),('after',InterpretationProvider)):
            messages,selected,_,_=cls(OllamaProvider(),packet).investigation_request(case['question'],case['evidence'])
            row[name]=packet_stats(messages,selected,case['evidence'],report['changes'])
            write(out/'budget-prompts'/name/(case['case_id']+'.json'),messages)
        experiment.append(row)
    for f in ('agents/evidence_first.py','llm/context.py','llm/providers.py','llm/ollama.py','scripts/audit_diagnostic_inputs.py',str(frozen.relative_to(ROOT))):
        source_manifest[f]=sha((ROOT/f).read_bytes())
    write(out/'inputs-manifest.json',source_manifest)
    write(out/'observations.json',observations)
    write(out/'budget-experiment.json',{'kind':'offline structural packet comparison','inference_calls':0,
        'byte_budget':7000,'rule_candidates':[],'classification_accuracy':'NOT_RUN',
        'limitations':'Same supplied evidence/static facts; prompt version identifier differs. No causal accuracy conclusion.', 'cases':experiment})
    summary={'observations':len(observations),'unique_authored_cases':len(case_evidence),'new_inference_calls':0,
        'historical_fingerprint_errors':sum(not all(r[k] for k in ('configuration_fingerprint_matches','dataset_fingerprint_matches','observation_fingerprint_matches')) for r in observations),
        'historical_count_mismatches':sum(not r['counts_match'] for r in observations),
        'historical_mapping_errors':sum(len(r['mapping_errors']) for r in observations),
        'historical_snapshot_quote_errors':sum(len(r['snapshot_quote_errors']) for r in observations),
        'historical_foreign_revision_aliases':sum(len(r['foreign_revision_aliases']) for r in observations),
        'historical_split_pairs':sum(bool(r['split_supplied_pairs']) for r in observations),
        'historical_pair_mapping_unresolved_observations':sum(r['split_supplied_pairs'] is None for r in observations),
        'budget_cases':len(experiment),
        'budget_before_split_pairs':sum(bool(r['before']['split_supplied_pairs']) for r in experiment),
        'budget_after_split_pairs':sum(bool(r['after']['split_supplied_pairs']) for r in experiment),
        'budget_before_count_mismatches':sum(not r['before']['counts_match'] for r in experiment),
        'budget_after_count_mismatches':sum(not r['after']['counts_match'] for r in experiment),
        'budget_after_empty_packets':sum(r['after']['included']==0 for r in experiment),
        'independent_label_review':'REQUIRED','semantic_support_review':'REQUIRED','target_91_percent':'NOT_EVALUATED'}
    write(out/'summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
