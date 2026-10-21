from pathlib import Path
import csv,json,shutil,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib import font_manager
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
for p in (Path.home()/'.local/share/fonts/vigilant-paper').glob('*.TTF'):font_manager.fontManager.addfont(str(p))
plt.rcParams.update({'font.family':'Times New Roman','font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
src=ROOT/'reports/results/summary.json'
if src.exists():
 s=json.loads(src.read_text());(HERE/'data/results.json').write_text(json.dumps(s,indent=2));shutil.copyfile(ROOT/'reports/ablation/summary.json',HERE/'data/ablation.json')
else:s=json.loads((HERE/'data/results.json').read_text())
rows=s['traceability'];datasets=['SMOS','iTrust','eTour_en','RTMX-module-valid']; methods=['tfidf','bm25','embedding','hybrid','hybrid_kg','hybrid_rag_top5'];names=['TF-IDF','BM25','MiniLM','Hybrid','Hybrid + KG','Hybrid + RAG']
lookup={(r['dataset'],r['method']):r for r in rows}
with (HERE/'data/map-comparison.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['method']+datasets)
 for m in methods:w.writerow([m]+[lookup.get((d,m),{}).get('map','NOT RUN')for d in datasets])
tex=[]
for m,n in zip(methods,names):
 vals=[f"{lookup[d,m]['map']:.4f}" if (d,m)in lookup else '---' for d in datasets];tex.append(n+' & '+' & '.join(vals)+r' \\')
(HERE/'data/results-table.tex').write_text('\n'.join(tex)+'\n')
fig,ax=plt.subplots(figsize=(3.5,2.15)); ys=list(range(4)); delta=[lookup[d,'hybrid_rag_top5']['map']-lookup[d,'hybrid']['map']for d in datasets]
ax.barh(ys,delta,color=['#245b80' if x>=0 else '#ad493d'for x in delta],height=.58)
ax.axvline(0,color='black',lw=.7);ax.set_yticks(ys,['SMOS','iTrust','eTour (English)','RTMX (modules)']);ax.invert_yaxis();ax.set_xlim(-.065,.018);ax.set_xlabel('MAP difference: Hybrid + RAG minus Hybrid');ax.spines[['top','right']].set_visible(False)
for y,v in zip(ys,delta):ax.text(v+( .0015 if v>=0 else -.0015),y,f'{v:+.4f}',ha='left'if v>=0 else'right',va='center',fontsize=8)
ax.tick_params(axis='both',labelsize=8);fig.tight_layout(pad=.4)
for fmt in ['pdf','svg','png']:fig.savefig(HERE/f'figures/rag-delta.{fmt}',dpi=600)
plt.close(fig)
fig,ax=plt.subplots(figsize=(3.5,3.05));ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
def box(x,y,w,h,t,c='#eaf1f5'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06,rounding_size=.12',facecolor=c,edgecolor='#334c5b',lw=.7));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=8.4)
def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=8,lw=.8,color='#334c5b'))
box(.5,8.75,9,1,'Git base/head: requirements, code, tests')
box(.5,7.1,9,1,'Parsers + canonical artifacts + content hashes')
box(.5,5.25,4,1.15,'Structural KG\nbase/head graphs')
box(5.5,5.25,4,1.15,'Retrieval index\nBM25 + MiniLM')
box(.5,3.3,4,1.15,'Diff + 2-hop impact\nconservative rules')
box(5.5,3.3,4,1.15,'Evidence assembly\nquote verification')
box(5.5,1.6,4,1,'Qwen decision\nJSON validation')
box(.5,.05,9,.95,'SQLite run record + React review / evidence export', '#f3efe5')
for a,b in [((5,8.75),(5,8.1)),((3,7.1),(2.5,6.4)),((7,7.1),(7.5,6.4)),((2.5,5.25),(2.5,4.45)),((7.5,5.25),(7.5,4.45)),((4.5,3.88),(5.5,3.88)),((7.5,3.3),(7.5,2.6)),((7.5,1.6),(7.5,1)),((2.5,3.3),(2.5,1))]:arrow(a,b)
fig.tight_layout(pad=.1)
for fmt in ['pdf','svg','png']:fig.savefig(HERE/f'figures/architecture.{fmt}',dpi=600)
plt.close(fig)
paper=HERE/'paper.tex'
if paper.exists():
 import re
 text=paper.read_text()
 text=re.sub(r'% BEGIN GENERATED RESULTS.*?% END GENERATED RESULTS',lambda m:'% BEGIN GENERATED RESULTS\n'+'\n'.join(tex)+'\n% END GENERATED RESULTS',text,flags=re.S)
 paper.write_text(text)
print('Built vector figures, 600 dpi PNG copies, CSV and table from frozen records.')
