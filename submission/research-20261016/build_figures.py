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
a=json.loads((HERE/'data/revision-analysis.json').read_text())['paired']
fig,ax=plt.subplots(figsize=(3.5,2.4));ys=list(range(4));delta=[x['delta_map']for x in a]
ax.errorbar(delta,ys,xerr=[[x['delta_map']-x['ci95_low']for x in a],[x['ci95_high']-x['delta_map']for x in a]],fmt='o',color='#245b80',capsize=3,markersize=4,linewidth=1)
ax.axvline(0,color='#666666',lw=.7,ls='--');ax.set_yticks(ys,['SMOS','iTrust','eTour (English)','RTMX (modules)']);ax.invert_yaxis();ax.set_xlim(-.16,.03);ax.set_ylim(3.5,-.7);ax.set_xlabel('MAP difference (reranker − hybrid)');ax.spines[['top','right']].set_visible(False)
for y,v in zip(ys,delta):ax.text(v,y-.25,f'{v:+.4f}',ha='center',fontsize=8)
ax.tick_params(axis='both',labelsize=8);fig.tight_layout(pad=.4)
for fmt in ['pdf','svg','png']:fig.savefig(HERE/f'figures/rag-delta.{fmt}',dpi=600)
plt.close(fig)
fig,ax=plt.subplots(figsize=(3.5,3.05));ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
def box(x,y,w,h,t,c='#eaf1f5'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06,rounding_size=.08',facecolor=c,edgecolor='#334c5b',lw=.7));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=9.2)
def arrow(a,b,dashed=False):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=8,lw=.8,color='#334c5b',linestyle='--'if dashed else '-'))
box(.3,9.05,9.4,.7,'Git base and head revisions')
box(.3,7.75,9.4,.7,'Parsers and versioned artifacts')
box(.3,6.1,4.2,.8,'Structural graph')
box(5.5,6.1,4.2,.8,'Hybrid retrieval')
box(.3,4.4,4.2,.8,'Diff and impact')
box(5.5,4.4,4.2,.8,'Checked excerpts')
box(.3,2.7,4.2,.8,'Rule hypotheses','#f3efe5')
box(5.5,2.7,4.2,.8,'Qwen judgment')
box(.3,.8,9.4,.9,'Persisted report and review\nRules and model decision kept separate','#f3efe5')
for a,b in [((5,9.05),(5,8.45)),((2.4,7.75),(2.4,6.9)),((7.6,7.75),(7.6,6.9)),((2.4,6.1),(2.4,5.2)),((7.6,6.1),(7.6,5.2)),((4.5,4.8),(5.5,4.8)),((2.4,4.4),(2.4,3.5)),((7.6,4.4),(7.6,3.5)),((2.4,2.7),(2.4,1.7)),((7.6,2.7),(7.6,1.7))]:arrow(a,b)
arrow((4.5,3.1),(5.5,4.5),True)
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
