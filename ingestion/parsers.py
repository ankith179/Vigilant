"""Python AST and mature Tree-sitter grammars; unsupported resolution stays explicit."""
import ast,re
from pathlib import Path
from ingestion.models import artifact,digest

def is_test(path,name=''):return bool(re.search(r'(^|[/_.])tests?([/_.]|$)|Test(?:s)?\.(?:java|tsx?|jsx?)$',path) or name.startswith('test_'))
def extract(project,repo,commit,path,content):
 suffix=Path(path).suffix.lower();kind='test' if is_test(path) else 'source_file'
 if suffix in {'.md','.rst','.txt'}:kind='requirement' if re.search(r'requirement|/UC/|REQ-',path,re.I) else 'documentation'
 elif suffix in {'.json','.yaml','.yml','.toml','.csv'}:kind='configuration'
 elif suffix=='.sql':kind='database'
 kind='configuration' if Path(path).name=='requirements.txt' else kind
 parent=artifact(project,repo,commit,path,kind,'',content);items=[parent];lines=content.splitlines();seen={}
 def add(kind,symbol,start,end,meta=None):
  ident=(kind,symbol);n=seen.get(ident,0);seen[ident]=n+1;meta=dict(meta or {})
  if n:symbol+=f'#occurrence-{n}';meta['identity_ambiguity']='duplicate symbol ordinal; edit may shift ordinal'
  a=artifact(project,repo,commit,path,kind,symbol,'\n'.join(lines[start-1:end]),start,end,meta);a.metadata['parent_id']=parent.artifact_id;items.append(a);return a
 if suffix=='.py':
  try:tree=ast.parse(content)
  except SyntaxError as e:parent.metadata['parse_error']=str(e);return items
  imports=[];prefixes={}
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
   if isinstance(n,ast.ImportFrom):imports.append('.'*n.level+(n.module or ''))
   if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call):
    for target in n.targets:
     if isinstance(target,ast.Name):
      for kw in n.value.keywords:
       if kw.arg=='prefix' and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,str):prefixes[target.id]=kw.value.value
  parent.metadata['imports']=imports
  def walk(node,scope=''):
   for n in ast.iter_child_nodes(node):
    if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
     symbol=scope+n.name;cls=isinstance(n,ast.ClassDef);k='class' if cls else ('test_method' if is_test(path,n.name) else ('method' if scope else 'function'))
     start=min([n.lineno]+[d.lineno for d in n.decorator_list]);calls=sorted({ast.unparse(x.func) for x in ast.walk(n) if isinstance(x,ast.Call)})
     a=add(k,symbol,start,n.end_lineno,{'calls':calls,'language':'python','signature':n.name if cls else ast.unparse(n.args),'syntax_hash':digest(ast.dump(n,include_attributes=False))})
     for dec in n.decorator_list:
      if not isinstance(dec,ast.Call) or not dec.args:continue
      route=dec.args[0];func=ast.unparse(dec.func);verb=func.split('.')[-1]
      if verb not in {'route','get','post','put','delete','patch','options'} or not isinstance(route,ast.Constant) or not isinstance(route.value,str):continue
      fullroute=prefixes.get(func.rsplit('.',1)[0],'')+route.value;methods=[verb.upper()] if verb!='route' else ['GET']
      for kw in dec.keywords:
       if kw.arg=='methods':
        try:methods=ast.literal_eval(kw.value)
        except Exception:pass
      for method in methods:add('api',method+' '+fullroute+'::'+symbol,start,n.end_lineno,{'method':method,'route':fullroute,'handler_id':a.artifact_id,'resolution':'literal decorator and local prefix'})
     walk(n,symbol+'.')
    else:walk(n,scope)
  walk(tree)
 elif suffix in {'.java','.js','.jsx','.ts','.tsx'}:
  from tree_sitter import Language,Parser
  if suffix=='.java':
   import tree_sitter_java as grammar
   lang=Language(grammar.language())
  elif suffix in {'.ts','.tsx'}:
   import tree_sitter_typescript as grammar
   lang=Language(grammar.language_tsx() if suffix=='.tsx' else grammar.language_typescript())
  else:
   import tree_sitter_javascript as grammar
   lang=Language(grammar.language())
  raw=content.encode();tree=Parser(lang).parse(raw);parent.metadata['parse_has_error']=tree.root_node.has_error
  parent.metadata['imports']=[a or b for a,b in re.findall(r'(?:from\s+[\'"]([^\'"]+)|import\s+([\w.]+))',content)]
  types={'class_declaration':'class','interface_declaration':'class','method_declaration':'method','constructor_declaration':'method','function_declaration':'function','method_definition':'method','arrow_function':'function'}
  def text(n):return raw[n.start_byte:n.end_byte].decode() if n else ''
  def walk(n,scope=''):
   nxt=scope
   if n.type in types:
    name=n.child_by_field_name('name')
    if n.type=='arrow_function' and n.parent.type=='variable_declarator':name=n.parent.child_by_field_name('name')
    if name:
     symbol=scope+text(name);k=types[n.type];params=n.child_by_field_name('parameters')
     if suffix=='.java' and k=='method':symbol+='('+re.sub(r'\s+',' ',text(params)).strip('()')+')'
     if is_test(path,text(name)) and k!='class':k='test_method'
     if suffix in {'.jsx','.tsx'} and text(name)[:1].isupper() and k=='function':k='frontend'
     a=add(k,symbol,n.start_point.row+1,n.end_point.row+1,{'language':suffix[1:],'calls':sorted(set(re.findall(r'\b([A-Za-z_$][\w.$]*)\s*\(',text(n)))),'signature':text(params)})
     if suffix=='.java' and k=='method':
      for m in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping\(\s*(?:value\s*=\s*)?"([^"]+)"',text(n)):
       add('api',m[1].upper()+' '+m[2]+'::'+symbol,n.start_point.row+1,n.end_point.row+1,{'method':m[1].upper(),'route':m[2],'handler_id':a.artifact_id,'resolution':'Spring literal method mapping; class prefix unresolved'})
     nxt=symbol+'.'
   for c in n.children:walk(c,nxt)
  walk(tree.root_node)
 def caller(m,verb,url):
  line=content.count('\n',0,m.start())+1;end=content.count('\n',0,m.end())+1
  owner=min((a for a in items if a.symbol and a.start_line<=line<=a.end_line),key=lambda a:a.end_line-a.start_line,default=parent)
  add('api_caller',verb+' '+url+'::'+owner.symbol,line,end,{'method':verb,'route':url,'owner_id':owner.artifact_id,'resolution':'literal client call'})
 if suffix in {'.js','.jsx','.ts','.tsx'}:
  for m in re.finditer(r'\b(?:fetch|axios\.(get|post|put|delete|patch))\s*\(\s*[\'"](/[^\'"]*)[\'"]',content):caller(m,(m[1] or 'get').upper(),m[2])
  for m in re.finditer(r"\.\s*(get|post|put|delete|patch)(?:<[^;{}]+>)?\s*\(\{[\s\S]{0,400}?\burl:\s*['\"]([^'\"]+)['\"]",content):caller(m,m[1].upper(),m[2])
  for m in re.finditer(r'\b(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[^\'"]*)[\'"]',content):
   line=content.count('\n',0,m.start())+1;add('api',m[1].upper()+' '+m[2],line,line,{'method':m[1].upper(),'route':m[2],'resolution':'literal Express route; mount prefixes unresolved'})
 return items
