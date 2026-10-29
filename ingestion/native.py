"""Native-language adapters with explicit compiler/context limits."""
from pathlib import Path, PurePosixPath
import json
import os
import re
import shutil
import subprocess
import tempfile

CPP_SUFFIXES = {'.c', '.h', '.cc', '.cpp', '.cxx', '.hpp', '.hxx', '.hh'}


def cpp(path, content, parent, add, source_files, is_test):
    try:
        from clang.cindex import Index, CursorKind, Diagnostic
    except ImportError:
        parent.metadata['parse_error'] = 'libclang==18.1.1 is required for native C/C++ analysis'
        parent.metadata['compiler_status'] = 'NOT_AVAILABLE'
        return
    root = '/vigilant-snapshot/'
    files = {p: text for p, text in (source_files or {path: content}).items()
             if PurePosixPath(p).suffix.lower() in CPP_SUFFIXES}
    files[path] = content
    dirs = sorted({str(PurePosixPath(root + p).parent) for p in files})
    language = 'c' if path.endswith('.c') else 'c++'
    args = ['-x', language, '-std=c11' if language == 'c' else '-std=c++17', '-nostdinc', '-nostdinc++']
    args += ['-I' + d for d in dirs]
    try:
        # Disable filesystem fallthrough as well as standard include search.
        # Absolute or macro-expanded includes must not read host files.
        with tempfile.TemporaryDirectory(prefix='vigilant-clang-vfs-') as tmp:
            overlay = Path(tmp) / 'snapshot.json'
            snapshot_root = Path(tmp) / 'snapshot-files'
            snapshot_root.mkdir()
            roots = []
            for index, (relative, source) in enumerate(files.items()):
                virtual = PurePosixPath(relative)
                if virtual.is_absolute() or not virtual.parts or '..' in virtual.parts or '\\' in relative:
                    raise ValueError('C/C++ source path must stay inside the repository snapshot')
                external = snapshot_root / f'{index}.source'
                external.write_text(source, encoding='utf-8')
                roots.append({'type': 'file', 'name': root + virtual.as_posix(),
                              'external-contents': str(external)})
            overlay.write_text(json.dumps({'version': 0, 'fallthrough': False,
                                           'use-external-names': False, 'roots': roots}))
            unit = Index.create().parse(root + path, args=args + ['-ivfsoverlay', str(overlay)],
                                        unsaved_files=[(root + p, text) for p, text in files.items()])
    except Exception as exc:
        parent.metadata.update(parse_error=str(exc), compiler_status='FAILED')
        return
    diagnostics = [{'severity': int(d.severity), 'message': d.spelling,
                    'line': d.location.line} for d in unit.diagnostics]
    errors = any(d['severity'] >= Diagnostic.Error for d in diagnostics)
    parent.metadata.update(language=language, compiler='libclang-18.1.1', compiler_status='ERRORS' if errors else 'PARSED',
                           parse_has_error=errors, compiler_diagnostics=diagnostics[:50],
                           compiler_context={'standard': 'c11' if language == 'c' else 'c++17',
                           'include_directories': [d.removeprefix(root) for d in dirs],
                           'build_configuration_verified': False, 'system_headers_loaded': False,
                           'filesystem_scope': 'SNAPSHOT_ONLY; host filesystem fallthrough disabled'},
                           imports=[])
    kinds = {CursorKind.STRUCT_DECL: 'class', CursorKind.CLASS_DECL: 'class', CursorKind.UNION_DECL: 'class',
             CursorKind.ENUM_DECL: 'class', CursorKind.FUNCTION_DECL: 'function', CursorKind.CXX_METHOD: 'method',
             CursorKind.CONSTRUCTOR: 'method', CursorKind.DESTRUCTOR: 'method', CursorKind.FUNCTION_TEMPLATE: 'function',
             CursorKind.CLASS_TEMPLATE: 'class'}
    def local(cursor):
        return cursor.location.file is not None and str(cursor.location.file) == root + path
    def symbol(cursor):
        names = [cursor.displayname or cursor.spelling]
        p = cursor.semantic_parent
        while p and p.kind != CursorKind.TRANSLATION_UNIT:
            if p.spelling:
                names.append(p.spelling)
            p = p.semantic_parent
        return '.'.join(reversed(names))
    def calls(cursor):
        result = []
        def visit(node):
            if node is not cursor and (node.kind in kinds or node.kind == CursorKind.LAMBDA_EXPR):
                return
            if node.kind == CursorKind.CALL_EXPR:
                target = node.referenced
                if target and target.get_usr():
                    result.append({'name': target.spelling, 'target_usr': target.get_usr(),
                                   'line': node.location.line, 'resolution': 'compiler-reference-under-snapshot-context'})
            for child in node.get_children():
                visit(child)
        visit(cursor)
        return result
    def walk(cursor):
        if cursor.kind in kinds and local(cursor) and cursor.spelling:
            kind = kinds[cursor.kind]
            if kind != 'class' and is_test(path, cursor.spelling):
                kind = 'test_method'
            references = calls(cursor) if kind != 'class' else []
            add(kind, symbol(cursor), cursor.extent.start.line, cursor.extent.end.line,
                {'language': language, 'compiler_usr': cursor.get_usr(), 'is_definition': cursor.is_definition(),
                 'signature': cursor.type.spelling, 'calls': sorted({c['name'] for c in references}),
                 'compiler_calls': references, 'compiler_context_complete': False,
                 'compiler_parse_clean': not errors, 'resolution': 'compiler-reference-under-snapshot-context'})
        for child in cursor.get_children():
            if local(child) or child.kind == CursorKind.NAMESPACE:
                walk(child)
    walk(unit.cursor)


def swift(path, content, parent, add, is_test):
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_swift
    except ImportError:
        parent.metadata.update(parse_error='tree-sitter-swift==0.7.3 is required', compiler_status='NOT_AVAILABLE')
        return
    raw = content.encode()
    tree = Parser(Language(tree_sitter_swift.language())).parse(raw)
    parent.metadata.update(language='swift', parse_has_error=tree.root_node.has_error,
                           imports=[], semantic_resolution='SYNTAX_CANDIDATES_ONLY', compiler_status='NOT_AVAILABLE')
    compiler = os.getenv('VIGILANT_SWIFTC') or shutil.which('swiftc')
    if compiler:
        try:
            # Parse only: no linking, program execution, macros or build scripts.
            command=[compiler]+([] if PurePosixPath(compiler).name=='swift-frontend' else ['-frontend'])+['-parse','-']
            checked = subprocess.run(command, input=raw,
                                     capture_output=True, timeout=30)
            parent.metadata.update(compiler_status='SYNTAX_VALIDATED' if checked.returncode == 0 else 'ERRORS',
                                   compiler='swiftc-frontend-parse',
                                   compiler_diagnostics=checked.stderr.decode(errors='replace')[:4000])
            parent.metadata['parse_has_error'] |= checked.returncode != 0
        except (OSError, subprocess.TimeoutExpired) as exc:
            parent.metadata.update(compiler_status='FAILED', compiler_diagnostics=str(exc))
    def text(node):
        return raw[node.start_byte:node.end_byte].decode() if node else ''
    declarations = {'class_declaration': 'class', 'protocol_declaration': 'class',
                    'function_declaration': 'function', 'init_declaration': 'method'}
    def calls(node):
        result = []
        def visit(n):
            if n is not node and n.type in declarations:
                return
            if n.type == 'call_expression' and n.named_children:
                result.append(text(n.named_children[0]))
            for child in n.named_children:
                visit(child)
        visit(node)
        return sorted(set(result))
    def walk(node, scope=''):
        next_scope = scope
        if node.type == 'import_declaration':
            parent.metadata['imports'].append(re.sub(r'^import\s+', '', text(node)).strip())
        if node.type in declarations:
            name = node.child_by_field_name('name')
            name_text = text(name) or ('init' if node.type == 'init_declaration' else '')
            if name_text:
                body = node.child_by_field_name('body')
                signature = raw[name.end_byte if name else node.start_byte:body.start_byte if body else node.end_byte].decode().strip()
                kind = declarations[node.type]
                if kind != 'class':
                    kind = 'test_method' if is_test(path, name_text) or name_text.startswith('test') else ('method' if scope else kind)
                symbol = scope + name_text + (signature if kind != 'class' else '')
                add(kind, symbol, node.start_point.row + 1, node.end_point.row + 1,
                    {'language': 'swift', 'signature': signature, 'calls': calls(node) if kind != 'class' else [],
                     'resolution': 'syntax-only; receiver types unresolved'})
                next_scope = scope + name_text + '.'
        for child in node.named_children:
            walk(child, next_scope)
    walk(tree.root_node)
