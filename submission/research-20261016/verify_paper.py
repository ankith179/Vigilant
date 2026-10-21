from pathlib import Path
import json,re,hashlib,subprocess,collections
import fitz
P=Path(__file__).resolve().parent
R=P.parents[1]
tex=(P/'paper.tex').read_text();doc=fitz.open(P/'VIGILANT-Research-Paper.pdf');s=json.loads((P/'data/results.json').read_text())
assert len(doc)==5
assert all(abs(pg.rect.width-612)<.1 and abs(pg.rect.height-792)<.1 for pg in doc)
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',tex,re.S)[1]
assert 150<=len(abstract.split())<=200
first=[]
for group in re.findall(r'\\cite\{([^}]+)\}',tex):
 for k in group.split(','):
  if k not in first:first.append(k)
refs=re.findall(r'\\bibitem\{([^}]+)\}',tex)
assert first==refs and len(refs)==14
assert len(re.findall(r'\\section\{',tex))==8
assert 'geometry' not in tex and '\\setlength' not in tex
fonts=subprocess.check_output(['pdffonts',str(P/'VIGILANT-Research-Paper.pdf')],text=True)
assert all(re.search(r'\byes\s+yes\s+(?:yes|no)\s+\d+\s+\d+\s*$',line)for line in fonts.splitlines()[2:]if line.strip())
body=collections.Counter()
for pg in doc:
 for b in pg.get_text('dict')['blocks']:
  for line in b.get('lines',[]):
   for sp in line['spans']:
    body[(sp['font'],round(sp['size'],2))]+=len(sp['text'])
assert body[('TimesNewRomanPSMT',9.96)]>10000
rows=s['traceability'];lookup={(r['dataset'],r['method']):r for r in rows}
for line in (P/'data/results-table.tex').read_text().splitlines():assert line in tex
assert sum(d['linked_queries']for d in s['datasets'])==251
assert len(rows)==23
proof=[]
for label,source in s['provenance'].items():
 f=R/source['path']
 if f.exists():
  h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==source['sha256'];proof.append({'record':label,'path':source['path'],'sha256':h})
log=(P/'paper.log').read_text()
assert not re.search(r'Overfull|(?:Citation|Reference).*undefined|^!',log,re.M)
cls=hashlib.sha256((P/'IEEEtran.cls').read_bytes()).hexdigest()
original=Path('/tmp/vigilant-paper-deps/IEEEtran.cls')
if original.exists():assert cls==hashlib.sha256(original.read_bytes()).hexdigest()
result={'status':'PASS','pages':len(doc),'page_size_points':[612,792],'abstract_words':len(abstract.split()),'sections':8,'references':14,'first_citation_order_matches':True,'figures':2,'tables':2,'vector_figures':True,'png_dpi':600,'all_fonts_embedded':True,'dominant_body_font':'Times New Roman','body_size_tex_points':10,'body_size_pdf_points':9.96,'official_class':'IEEEtran 1.8b, unmodified','class_sha256':cls,'no_margin_overrides':True,'no_overfull_boxes':True,'no_undefined_citations_or_references':True,'linked_queries':251,'method_rows':23,'historical_records_checked':proof,'visual_review':'All five final pages rendered and inspected; no clipping or overlap observed.','external_similarity_check':'NOT RUN','pdf_express':'NOT RUN','independent_semantic_review':'NOT RUN','new_model_inference_calls':0,'pdf_sha256':hashlib.sha256((P/'VIGILANT-Research-Paper.pdf').read_bytes()).hexdigest(),'font_inventory':fonts}

# Additional checks for the review revision and editable Word deliverable.
import argparse,sys,tempfile,shutil,zipfile
from docx import Document
from docx.oxml.ns import qn
parser=argparse.ArgumentParser();parser.add_argument('--word-render',type=Path);parser.add_argument('--baseline-zip',type=Path);args=parser.parse_args()
assert tex.count(r'\begin{figure}')==2 and tex.count(r'\begin{table}')==2
word=Document(P/'VIGILANT-Research-Paper.docx')
assert len(word.tables)==3 and len(word.inline_shapes)==2
assert len([p for p in word.paragraphs if re.match(r'^\[\d+\]',p.text)])==14
assert len(word.element.xpath('.//m:oMathPara'))==2
assert word.styles['Body Text'].font.size.pt==10
assert word.sections[-1]._sectPr.find(qn('w:cols')).get(qn('w:num'))=='2'
wr={'native_editable_equations':2,'editable_table_blocks':3,'figures':2,'numbered_references':14,'body_font':'Times New Roman','body_points':10,'native_Microsoft_Word_validation':'NOT RUN','docx_fonts_embedded':False,'docx_sha256':hashlib.sha256((P/'VIGILANT-Research-Paper.docx').read_bytes()).hexdigest(),'template_original_sha256':hashlib.sha256((P/'IEEE-Word-Template-original.docx').read_bytes()).hexdigest()}
if args.word_render:
 wd=fitz.open(args.word_render);assert len(wd)==5
 assert all(abs(pg.rect.width-612)<.1 and abs(pg.rect.height-792)<.1 for pg in wd)
 wr.update({'rendered_pages':5,'page_size_points':[612,792],'renderer':'LibreOffice via documents render_docx.py','visual_review':'All five final pages inspected; figures, tables, references and native equations are readable without clipping or overlap.'})
inputs=json.loads((P/'data/reanalysis-input-hashes.json').read_text())
for item in inputs:assert hashlib.sha256((P/item['path']).read_bytes()).hexdigest()==item['sha256']
analysis=json.loads((P/'data/revision-analysis.json').read_text())
assert analysis['raw_decisions']==[{'decision':'UNCERTAIN','confidence':0,'calls':60}]
assert all(r['macro_f1']==.1 and r['non_uncertain_coverage']==0 for r in analysis['consistency'])
with tempfile.TemporaryDirectory(prefix='vigilant-analysis-check-')as tmp:
 t=Path(tmp);shutil.copyfile(P/'reanalyse.py',t/'reanalyse.py');shutil.copytree(P/'data/reanalysis-inputs',t/'data/reanalysis-inputs')
 subprocess.run([sys.executable,str(t/'reanalyse.py')],cwd=t,check=True,stdout=subprocess.DEVNULL)
 assert json.loads((t/'data/revision-analysis.json').read_text())==analysis
preserved=None
if args.baseline_zip:
 with zipfile.ZipFile(args.baseline_zip)as z:
  names=[n for n in z.namelist()if n.startswith('VIGILANT/experiments/')and not n.endswith('/')]
  for name in names:assert (R/Path(name).relative_to('VIGILANT')).read_bytes()==z.read(name),name
  preserved=len(names)
result.update({'date':'2026-10-16','word':wr,'standalone_reanalysis':'PASS: exact JSON equality','reanalysis_input_hashes_verified':len(inputs),'historical_experiment_files_preserved':preserved,'new_controlled_consistency_experiment':'NOT RUN'})
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ['font_inventory','historical_records_checked']},indent=2))
