"""Build review drafts; derive all result tables from the audited summary."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission/output'


def latex_table(caption, label, columns, headers, rows, wide=False):
    kind = 'table*' if wide else 'table'
    content = [rf'\begin{{{kind}}}[!t]', r'\centering\footnotesize',
               rf'\caption{{{caption}}}\label{{{label}}}',
               rf'\begin{{tabular}}{{{columns}}}\toprule',
               ' & '.join(headers) + r' \\\midrule']
    content += [' & '.join(map(str,row)) + r' \\' for row in rows]
    return '\n'.join(content + [r'\bottomrule\end{tabular}', rf'\end{{{kind}}}'])


def references():
    keys = ['bm25','rrf','sbert','rag','lissa','transarc','ardoco','graphrag','sweagent','minilm','qwen']
    blocks = (ROOT/'submission/references.md').read_text().strip().split('\n\n')
    items = []
    for key,block in zip(keys,blocks,strict=True):
        block = re.sub(r'^\d+\. ', '', block)
        block = re.sub(r'\*([^*]+)\*', r'\\emph{\1}', block)
        block = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\href{\2}{\1}', block)
        block = re.sub(r'`([^`]+)`', lambda m:r'\texttt{'+m[1].replace('_',r'\_')+'}',block)
        items.append(r'\bibitem{'+key+'} '+block)
    return '\n'.join([r'\begin{thebibliography}{11}',*items,r'\end{thebibliography}'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('paper',choices=['research','survey']);args=ap.parse_args()
    summary_path=ROOT/'reports/results/summary.json';s=json.loads(summary_path.read_text())
    assert s['status']=='COMPLETED' and s['metric_audit']['status']=='PASS'
    assert sum(r['queries'] for r in s['rag'])==251
    for record in s['provenance'].values():
        assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
    labels={'SMOS':'SMOS','iTrust':'iTrust','eTour_en':'eTour','RTMX-module-valid':'RTMX*'}
    methods=['tfidf','bm25','embedding','hybrid','hybrid_kg','hybrid_rag_top5']
    scores={(r['dataset'],r['method']):r for r in s['traceability']}
    replacements={
        'REFERENCES':references(),
        'DATASET_TABLE':latex_table('Evaluated populations. RTMX* is the module-valid subset.','tab:data','lrrrr',
            ['Dataset','Req.','Linked','Targets','Links'],[[labels[r['dataset']],r['requirements'],r['linked_queries'],r['targets'],r['links']] for r in s['datasets']]),
        'MAP_TABLE':latex_table('MAP from complete saved rankings; -- means not run. RTMX* uses seven modules.','tab:map','lrrrrrr',
            ['Dataset','TF-IDF','BM25','MiniLM','Hybrid','+KG','+RAG'],
            [[labels[d['dataset']]]+[f"{scores[(d['dataset'],m)]['map']:.4f}" if (d['dataset'],m) in scores else '--' for m in methods] for d in s['datasets']],wide=True),
        'RAG_TABLE':latex_table('Frozen RAG: paired MAP differences relative to hybrid.','tab:rag','lrrr',
            ['Dataset','Calls','MAP difference','Mean seconds'],
            [[labels[r['dataset']],r['queries'],f"{scores[(r['dataset'],'hybrid_rag_top5')]['map']-scores[(r['dataset'],'hybrid')]['map']:+.4f}",f"{r['mean_generation_seconds']:.2f}"] for r in s['rag']]),
        'ABLATION_TABLE':latex_table('Twelve cases per variant. Agree.: authored-label agreement; Unc.: uncertainty; Cite.: citation validity; End.: known-endpoint recall.','tab:abl','lrrrr',
            ['Variant','Agree.','Unc.','Cite.','End.'],
            [[r['variant']]+[f"{r[k]:.3f}" for k in ['status_agreement','uncertainty_rate','schema_citation_validity','known_endpoint_recall']] for r in s['ablation']['summary']]),
    }
    hits=sum(r['known_affected_recovered'] for r in s['changebench']);misses=sum(r['known_affected_missed'] for r in s['changebench'])
    replacements.update(KNOWN_HITS=str(hits),KNOWN_MISSES=str(misses),KNOWN_TOTAL=str(hits+misses))
    source=(ROOT/f'submission/{args.paper}-paper.tex.in').read_text()
    for key,value in replacements.items():source=source.replace('@'+key+'@',value)
    assert not re.search(r'@[A-Z_]+@',source), 'Unresolved template token'
    name='Research-Paper-Draft' if args.paper=='research' else 'Survey-Paper-Draft'
    OUT.mkdir(parents=True,exist_ok=True);tex=OUT/(name+'.tex');tex.write_text(source)
    logdir=ROOT/'reports/submission';logdir.mkdir(exist_ok=True)
    # TEXINPUTS preserves the usual search while adding our pinned class.
    import os
    env=dict(os.environ);env['TEXINPUTS']=str(ROOT/'submission')+':'+env.get('TEXINPUTS','')
    with (logdir/(args.paper+'-build.log')).open('w') as log:
        for _ in range(2):
            subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',tex.name],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (logdir/(args.paper+'-source-provenance.json')).write_text(json.dumps({
        'status':'DRAFT_FOR_REVIEW','summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        'sources':s['provenance'],'reference_record':'docs/LITERATURE_VERIFICATION.md',
        'independent_review':False,'venue_selected':False},indent=2)+'\n')
    print(OUT/(name+'.pdf'))


if __name__=='__main__':main()
