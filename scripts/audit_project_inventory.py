"""Static inventory only; imported subjects and REA code are never executed."""
from pathlib import Path
import ast,hashlib,json,re
from tree_sitter import Language,Parser
import tree_sitter_typescript

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/master-audit-20261025'
SOURCE=OUT/'rea-source'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def rea_inventory():
    parser=Parser(Language(tree_sitter_typescript.language_typescript()))
    rows=[];missing=[];visited=set()
    def contracts(path,symbol,kind='tool'):
        path=path.resolve();key=(str(path),symbol)
        if key in visited:return
        visited.add(key)
        if not path.is_file():missing.append({'path':str(path.relative_to(SOURCE)),'symbol':symbol});return
        raw=path.read_bytes();tree=parser.parse(raw)
        if tree.root_node.has_error:raise ValueError('TypeScript parse error: '+str(path))
        def txt(n):return raw[n.start_byte:n.end_byte].decode()
        imports={}
        for m in re.finditer(r'import\s*\{([^}]+)\}\s*from\s*"([^"]+)"',raw.decode(),re.S):
            for name in m[1].split(','):imports[name.strip()]=(path.parent/m[2]).with_suffix('.ts')
        found=[]
        def walk(n):
            if n.type=='variable_declarator' and txt(n.child_by_field_name('name'))==symbol:found.append(n.child_by_field_name('value'))
            for child in n.named_children:walk(child)
        walk(tree.root_node)
        if not found:raise ValueError('Missing declaration '+symbol)
        n=found[0]
        while n.type in {'as_expression','satisfies_expression','parenthesized_expression'}:n=n.named_children[0]
        for child in (n.named_children if n.type=='array' else [n]):
            if child.type=='comment':continue
            if child.type=='identifier':
                name=txt(child);contracts(imports.get(name,path),name,kind);continue
            if child.type=='spread_element':
                spread=child.named_children[0]
                if spread.type=='call_expression':
                    member=spread.child_by_field_name('function')
                    if member.type!='member_expression' or txt(member.child_by_field_name('property'))!='map':raise ValueError('Unresolved contract spread')
                    name=txt(member.child_by_field_name('object'))
                else:name=txt(spread)
                contracts(imports.get(name,path),name,kind);continue
            fields={}
            if child.type=='call_expression':
                args=child.child_by_field_name('arguments').named_children
                fields={'name':args[0],'description':args[1]}
            elif child.type=='object':
                for pair in child.named_children:
                    if pair.type=='pair':fields[txt(pair.child_by_field_name('key'))]=pair.child_by_field_name('value')
                    elif pair.type=='spread_element' and pair.named_children[0].type=='call_expression':
                        args=pair.named_children[0].child_by_field_name('arguments').named_children
                        if len(args)>1 and args[0].type=='string' and args[1].type=='string':fields.update(name=args[0],description=args[1])
            else:raise ValueError('Unsupported inventory element '+child.type)
            if 'name' not in fields:raise ValueError(str(path)+':'+str(child.start_point.row+1)+' '+txt(child)[:350])
            name=ast.literal_eval(txt(fields['name']))
            description=txt(fields['description'])
            if fields['description'].type=='string':description=ast.literal_eval(description)
            rows.append({'kind':kind,'name':name,'expected_behavior':description,'path':str(path.relative_to(SOURCE)),
                         'line':child.start_point.row+1,'source_sha256':sha(path),'behavior_execution':'NOT_RUN'})
    contracts(SOURCE/'src/contracts/toolContracts.ts','TOOL_CONTRACTS')
    contracts(SOURCE/'src/contracts/promptContracts.ts','PROMPT_CONTRACTS','prompt')
    cli=SOURCE/'src/cliCommandNames.ts'
    for m in re.finditer(r'^  (\w+): "([^"]+)"',cli.read_text(),re.M):
        rows.append({'kind':'cli','name':m[2],'path':'src/cliCommandNames.ts','line':cli.read_text()[:m.start()].count('\n')+1,
                     'source_sha256':sha(cli),'expected_behavior':'CLI registration; linked command handler must be verified before parity','behavior_execution':'NOT_RUN'})
    return {'rows':rows,'unresolved_imports':missing,'duplicates':len(rows)-len({(r['kind'],r['name']) for r in rows})}

def main():
    OUT.mkdir(exist_ok=True)
    files=[]
    paths=list(ROOT.glob('*.py'))+list(ROOT.glob('*.ps1'))+[ROOT/p for p in ['requirements.txt','requirements-core.txt','frontend/package.json','frontend/package-lock.json','Dockerfile','docker-compose.yml'] if (ROOT/p).is_file()]
    for directory in ['agents','backend','change_analysis','consistency','database','evaluation','ingestion','investigation','knowledge_graph','llm','rag','retrieval','traceability','scripts','tests','frontend/src']:
        paths.extend((ROOT/directory).rglob('*'))
    for p in sorted(set(paths)):
            if not p.is_file() or '__pycache__' in p.parts:continue
            row={'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
            if p.suffix=='.py':
                tree=ast.parse(p.read_text());row['definitions']=[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
                row['imports']=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module})
            files.append(row)
    fingerprint=hashlib.sha256(json.dumps([(r['path'],r['sha256']) for r in files],separators=(',',':')).encode()).hexdigest()
    (OUT/'source-inventory.json').write_text(json.dumps({'files':files,'source_fingerprint':fingerprint,'git_commit':None,'git_branch':None,'identity_type':'archive-working-copy'},indent=2)+'\n')
    inventory=rea_inventory();(OUT/'rea-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps({'local_source_files':len(files),'source_fingerprint':fingerprint,'rea_rows':len(inventory['rows']),'missing':inventory['unresolved_imports'],'duplicates':inventory['duplicates']}))

if __name__=='__main__':main()
