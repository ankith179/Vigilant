from database.store import Store
from ingestion.parsers import extract
from knowledge_graph.graph import build_graph


def test_cpp_compiler_resolves_cross_file_overloads_and_keeps_errors_visible():
    files = {'api.h': 'int value(int x); double value(double x);',
             'api.cpp': '#include "api.h"\nint value(int x){ return x; }\ndouble value(double x){ return x; }',
             'caller.cpp': '#include "api.h"\nint run(){ return value(2); }'}
    items = [a for path, text in files.items() for a in extract('p', 'r', 'c', path, text, source_files=files)]
    graph, edges = build_graph(Store('sqlite:///:memory:'), items)
    by = {a.artifact_id: a for a in items}
    calls = [e for e in edges if e['relation_type'] == 'CALLS']
    assert len(calls) == 1 and calls[0]['method'] == 'compiler-usr'
    assert by[calls[0]['target_artifact']].symbol == 'value(int)'
    assert by[calls[0]['target_artifact']].metadata['is_definition']
    assert graph.get_edge_data(calls[0]['source_artifact'], calls[0]['target_artifact'])[calls[0]['id']]['resolution_status'] == 'compiler-reference-under-snapshot-context'
    assert not calls[0]['build_configuration_verified']
    broken = extract('p', 'r', 'c', 'broken.cpp', '#include "missing.h"\nint run(){return unknown();}')
    assert broken[0].metadata['parse_has_error'] and broken[0].metadata['compiler_status'] == 'ERRORS'
    _, errors = build_graph(Store('sqlite:///:memory:'), broken)
    assert not any(e['relation_type'] == 'CALLS' for e in errors)


def test_swift_scopes_and_receiver_uncertainty_are_explicit():
    text = 'struct Service { func sum(_ x: Int) -> Int { x + 1 } }\nfunc caller() -> Int { Service().sum(2) }'
    items = extract('p', 'r', 'c', 'Service.swift', text)
    assert not items[0].metadata['parse_has_error']
    assert any(a.symbol.startswith('Service.sum(') for a in items)
    caller = next(a for a in items if a.symbol.startswith('caller('))
    assert 'Service().sum' in caller.metadata['calls']
    _, edges = build_graph(Store('sqlite:///:memory:'), items)
    assert not any(e['relation_type'] == 'CALLS' for e in edges)
    assert items[0].metadata['semantic_resolution'] == 'SYNTAX_CANDIDATES_ONLY'



def test_cpp_rejects_snapshot_paths_outside_repository():
    source = '#include "api.h"\\nint run(){ return value(2); }'
    items = extract('p', 'r', 'c', 'caller.cpp', source,
                    source_files={'caller.cpp': source, '../api.h': 'int value(int x);'})
    assert items[0].metadata['compiler_status'] == 'FAILED'
    assert 'must stay inside the repository snapshot' in items[0].metadata['parse_error']
    assert not any(a.metadata.get('compiler_calls') for a in items)


def test_cpp_absolute_and_macro_includes_cannot_read_host_files(tmp_path):
    header = tmp_path / 'host.h'
    header.write_text('int host_only(){return 1;}')
    for include in (f'#include "{header.as_posix()}"',
                    f'#define HEADER "{header.as_posix()}"\n#include HEADER'):
        items = extract('p', 'r', 'c', 'caller.cpp', include + '\nint run(){return host_only();}')
        assert items[0].metadata['compiler_status'] == 'ERRORS'
        assert 'fallthrough disabled' in items[0].metadata['compiler_context']['filesystem_scope']
        assert not any(a.symbol.startswith('host_only') for a in items)
