"""Export exact prompts and a separate evidence-only development arm for review."""
from pathlib import Path
import csv
import json
import sqlite3
import sys
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.models import Artifact
from llm.ollama import OllamaProvider
from rag.evidence import balanced_change_context, verify
from evaluation.resume import fingerprint


def packet(path, case, engine):
    messages, selected, _, _ = engine.investigation_request(case['question'], case['evidence'])
    payload = json.loads(messages[-1]['content'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix('.json').write_text(json.dumps(messages, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['# '+case['case_id'], '', 'Expected labels and model answers are intentionally withheld.', '',
             '## Exact system prompt', '', messages[0]['content'], '', '## Question', '', case['question'], '',
             f"Supplied {len(case['evidence'])}; selected {len(selected)}; omitted {payload['evidence_omitted']}.", '']
    for e in payload['evidence']:
        lines += [f"## {e['evidence_id']} / {e['artifact_id']} - {e['file']}:{e['start_line']}-{e['end_line']}",
                  '', f"Commit: `{e['commit']}`; method: `{e['retrieval_method']}`", '', '````', e['excerpt'], '````', '']
    path.with_suffix('.md').write_text('\n'.join(lines), encoding='utf-8')
    return payload, selected


def main():
    baseline = ROOT/'experiments/local-model-comparison/windows-20261021/dataset.json'
    out = ROOT/'reports/citation-fix-20261021'
    data = json.loads(baseline.read_text(encoding='utf-8'))
    engine = OllamaProvider(); enriched = []; coverage = []; worksheet = []
    with closing(sqlite3.connect((ROOT/'data/snapshots/changebench.db').as_uri()+'?mode=ro', uri=True)) as db:
        for case in data['cases']:
            # Only report revisions and raw changes enter retrieval; no oracle fields.
            report = json.loads((ROOT/'data/changebench'/(case['case_id']+'-report.json')).read_text(encoding='utf-8'))
            def artifacts(commit):
                return [Artifact.model_validate({k:v for k,v in json.loads(row[0]).items() if k!='id'})
                        for row in db.execute('SELECT payload FROM artifacts WHERE repository=? AND commit_id=?',
                                              (report['repository'],commit))]
            before = artifacts(report['base_commit']); after = artifacts(report['commit_id'])
            edges = [json.loads(r[0]) for r in db.execute(
                'SELECT payload FROM graph_edges WHERE repository=? AND commit_id IN (?,?)',
                (report['repository'],report['base_commit'],report['commit_id']))]
            candidate, details = balanced_change_context(report['changes'],before,after,edges)
            improved = {**case,'evidence':candidate}
            old_payload, old_selected = packet(out/'review/baseline'/case['case_id'],case,engine)
            new_payload, new_selected = packet(out/'review/evidence-v2'/case['case_id'],improved,engine)
            assert not verify(old_selected,before+after) and not verify(new_selected,before+after)
            roles = {r:sum(e.get('context_role')==r for e in new_selected)
                     for r in ('requirement','implementation','caller','test')}
            coverage.append({'case_id':case['case_id'],'baseline_supplied':len(case['evidence']),
                'baseline_selected':len(old_selected),'baseline_files':sorted({e['file'] for e in old_selected}),
                'candidate_supplied':len(candidate),'candidate_selected':len(new_selected),
                'candidate_files':sorted({e['file'] for e in new_selected}),
                'selected_role_counts':roles,'missing_selected_roles':[r for r,n in roles.items() if not n],
                'prompt_sha256':fingerprint(new_payload),**details})
            enriched.append(improved)
            worksheet.append({'case_id':case['case_id'],'repository':report['repository'],
                'base':report['base_commit'],'head':report['commit_id'],
                'reviewer_1_id':'','reviewer_1_label':'','reviewer_1_sufficient':'','reviewer_1_missing_evidence':'',
                'reviewer_2_id':'','reviewer_2_label':'','reviewer_2_sufficient':'','reviewer_2_missing_evidence':'',
                'adjudicator_id':'','adjudicated_label':'','adjudication_rationale':''})
    # Keep authored labels only in the evaluator dataset, never in blind packets.
    (out/'evidence-v2-dataset.json').write_text(json.dumps({**data,'cases':enriched,
        'evidence_policy':'balanced-change-context-v1','review_status':'NOT_INDEPENDENTLY_REVIEWED'},indent=2),encoding='utf-8')
    (out/'evidence-coverage.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
    worksheet_path = out/'review/independent-labels.csv'
    # Never overwrite completed reviewer work when exporting again.
    if not worksheet_path.exists():
        with worksheet_path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(worksheet[0]));w.writeheader();w.writerows(worksheet)
    print(json.dumps({'cases':len(coverage),'exact_prompt_packets':24,'status':'REVIEW_REQUIRED',
                      'coverage':[{k:c[k] for k in ('case_id','baseline_selected','candidate_selected','missing_selected_roles')} for c in coverage]},indent=2))


if __name__=='__main__':main()
