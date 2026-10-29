"""Mine revision-pinned repository changes as UNREVIEWED_SILVER candidates only."""
import argparse
import ast
import csv
import difflib
import hashlib
import json
import random
import re
import subprocess
import tokenize
from io import BytesIO
from pathlib import Path


DID = {
    "CODE_CHANGED_DOC_UNCHANGED": ["D14"],
    "ADDED_FUNCTION_NO_TEST_CANDIDATE": ["D17"],
    "DELETED_STILL_REFERENCED_CANDIDATE": ["D19"],
    "TEST_CHANGED_ASSERTIONS_UNCHANGED": ["D20"],
    "BOUNDARY_CHANGE_CANDIDATE": ["D22"],
    "EXCEPTION_CHANGE_CANDIDATE": ["D23"],
    "ROUTE_CHANGED_CANDIDATE": ["D25"],
    "PARAM_RENAMED_CANDIDATE": ["D26"],
    "RETURN_SCHEMA_CHANGED_CANDIDATE": ["D27"],
    "DEFAULT_CHANGED_CANDIDATE": ["D28"],
    "SHARED_FUNCTION_CHANGED_CANDIDATE": ["D30"],
    "INDIRECT_DEPENDENCY_CANDIDATE": ["D31"],
    "FIXTURE_CHANGED_CANDIDATE": ["D32"],
    "MOCK_TARGET_CHANGED_CANDIDATE": ["D33"],
    "PARSER_FAILURE_CANDIDATE": ["D36"],
}
CURATED_ONLY_DIDS = {"D13", "D15", "D16", "D18", "D21", "D24", "D29", "D34", "D35"}
MAX_REFERENCE_BYTES = 2_000_000
MAX_REFERENCE_LINES = 10_000


def run_git(repo, *args, timeout=90, check=True):
    return subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args], check=check,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, env={**__import__("os").environ, "GIT_NO_LAZY_FETCH": "1"},
    ).stdout


def _sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _is_test(path):
    parts = path.lower().split("/")
    name = parts[-1]
    return ("tests" in parts or "test" in parts or name.startswith("test_")
            or name.endswith("_test.py") or name == "conftest.py")


def _is_docs(path):
    p = path.lower()
    return (p.startswith(("docs/", "doc/")) or "/docs/" in p or "/doc/" in p
            or p.endswith((".rst", ".md", ".adoc")))


def _python(path):
    return path.lower().endswith(".py")


def _parse(source):
    try:
        return ast.parse(source), None
    except (SyntaxError, ValueError, TypeError) as exc:
        return None, f"{type(exc).__name__}:{getattr(exc, 'lineno', None)}"


def _funcs(tree):
    if tree is None:
        return {}
    result = {}
    class_prefix = []

    def visit(body, prefix=()):
        for node in body:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + (node.name,))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = ".".join(prefix + (node.name,))
                result[name] = node
                visit(node.body, prefix + (node.name,))
    visit(tree.body)
    return result


def _dump(node):
    return ast.dump(node, include_attributes=False) if node is not None else None


def _arg_names(fn):
    a = fn.args
    return ([x.arg for x in a.posonlyargs] + [x.arg for x in a.args]
            + ([a.vararg.arg] if a.vararg else []) + [x.arg for x in a.kwonlyargs]
            + ([a.kwarg.arg] if a.kwarg else []))


def _defaults(fn):
    values = [_dump(x) for x in fn.args.defaults]
    values += ["<REQUIRED>" for _ in range(max(0, len(fn.args.posonlyargs) + len(fn.args.args) - len(values)))]
    values += [_dump(x) if x is not None else "<REQUIRED>" for x in fn.args.kw_defaults]
    return values


def _assertions(fn):
    return sorted(_dump(n) for n in ast.walk(fn) if isinstance(n, ast.Assert))


def _exception_facts(fn):
    return sorted(_dump(n) for n in ast.walk(fn) if isinstance(n, (ast.Raise, ast.ExceptHandler)))


def _boundary_facts(fn):
    values = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Compare):
            literals = [x.value for x in n.comparators if isinstance(x, ast.Constant) and isinstance(x.value, int)]
            values.append((_dump(n.left), tuple(type(op).__name__ for op in n.ops), tuple(literals), _dump(n)))
    return values


def _return_schema(fn):
    annotation = _dump(fn.returns)
    keys = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            keys.extend(k.value for k in n.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str))
    return annotation, sorted(set(keys))


def _enclosing_function(source, line):
    tree, error = _parse(source)
    if error:
        return None
    matches = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.lineno <= line <= getattr(n, "end_lineno", n.lineno)]
    if not matches:
        return None
    return min(matches, key=lambda n: getattr(n, "end_lineno", n.lineno) - n.lineno).name


def _route_literals(source):
    patterns = (
        r"(?:route|add_url_rule|path|re_path)\s*\([^\n]*?['\"]([^'\"]+)['\"]",
        r"@[^\n]*(?:route|get|post|put|patch|delete)\s*\([^\n]*?['\"]([^'\"]+)['\"]",
    )
    return sorted({match for pattern in patterns for match in re.findall(pattern, source, re.I)})


def _token_signature(source):
    return [(t.type, t.string) for t in tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
            if t.type not in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.COMMENT, tokenize.NL,
                              tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT}]


class UnsupportedGitObjectError(ValueError):
    def __init__(self, revision, path, entry):
        self.revision = revision
        self.path = path
        self.mode = entry["mode"]
        self.object_type = entry["type"]
        self.object_id = entry["object_id"]
        super().__init__(f"Unsupported Git object {self.object_type} at {revision}:{path}")


def _git_tree_entry(repo, revision, path):
    env = {**__import__("os").environ, "GIT_NO_LAZY_FETCH": "1"}
    subprocess.run(["git", "--no-pager", "-C", str(repo), "cat-file", "-e", f"{revision}^{{commit}}"],
                   capture_output=True, timeout=60, env=env, check=True)
    tree = subprocess.run(["git", "--no-pager", "-C", str(repo), "ls-tree", "-z", "--full-tree", revision, "--", path],
                          capture_output=True, timeout=60, env=env, check=True)
    if not tree.stdout:
        return None
    metadata = tree.stdout.split(b"\0", 1)[0].split(b"\t", 1)[0].decode("ascii").split()
    mode, object_type, object_id = metadata
    return {"mode": mode, "type": object_type, "object_id": object_id}


def _git_bytes(repo, revision, path):
    entry = _git_tree_entry(repo, revision, path)
    if entry is None:
        return None
    if entry["type"] != "blob":
        raise UnsupportedGitObjectError(revision, path, entry)
    env = {**__import__("os").environ, "GIT_NO_LAZY_FETCH": "1"}
    result = subprocess.run(["git", "--no-pager", "-C", str(repo), "cat-file", "blob", entry["object_id"]],
                            capture_output=True, timeout=60, env=env, check=True)
    return result.stdout


def _git_evidence(repo, revision, path):
    entry = _git_tree_entry(repo, revision, path)
    if entry is None:
        return _evidence(path, revision, None, "git-ls-tree-pinned")
    if entry["type"] != "blob":
        return {"revision": revision, "path": path, "start_line": None, "end_line": None,
                "content_hash": None, "extraction_method": "git-ls-tree-pinned",
                "presence": "PRESENT_UNSUPPORTED_GIT_OBJECT", "object_mode": entry["mode"],
                "object_type": entry["type"], "object_id": entry["object_id"]}
    raw = subprocess.run(["git", "--no-pager", "-C", str(repo), "cat-file", "blob", entry["object_id"]],
                         capture_output=True, timeout=60,
                         env={**__import__("os").environ, "GIT_NO_LAZY_FETCH": "1"}, check=True).stdout
    return _evidence(path, revision, raw, "git-cat-file-pinned")


def _name_status(repo, base, head, path_filters):
    raw = subprocess.run(["git", "--no-pager", "-C", str(repo), "diff-tree", "--no-commit-id",
                          "--name-status", "-r", "-M", "-z", base, head], check=True,
                         capture_output=True, timeout=90).stdout.decode("utf-8", "replace").split("\0")
    result, i = [], 0
    while i < len(raw) and raw[i]:
        status = raw[i]; i += 1
        if status.startswith(("R", "C")):
            old, new = raw[i], raw[i + 1]; i += 2
            item = {"status": status, "path": new, "old_path": old}
        else:
            path = raw[i]; i += 1
            item = {"status": status, "path": path, "old_path": None}
        if not path_filters or any(item["path"] == p or item["path"].startswith(p.rstrip("/") + "/") for p in path_filters):
            result.append(item)
    return result


def _grep(repo, revision, symbol, *, tests_only=False, calls_only=False):
    if not symbol or not re.fullmatch(r"[A-Za-z_]\w*", symbol):
        return {"status": "UNKNOWN_INVALID_SYMBOL", "paths": [], "lines": []}
    pattern = re.escape(symbol)
    if calls_only:
        pattern += r"[[:space:]]*\("
    proc = subprocess.run(["git", "--no-pager", "-C", str(repo), "grep", "-n", "-I", "-w", "-E",
                          pattern, revision, "--", "*.py"], capture_output=True, timeout=20,
                         env={**__import__("os").environ, "GIT_NO_LAZY_FETCH": "1"})
    raw = proc.stdout
    if proc.returncode not in {0, 1}:
        return {"status": "UNKNOWN_SEARCH_ERROR", "paths": [], "lines": []}
    if len(raw) > MAX_REFERENCE_BYTES:
        return {"status": "UNKNOWN_OUTPUT_LIMIT", "paths": [], "lines": []}
    lines = [line.removeprefix(revision + ":") for line in raw.decode("utf-8", "replace").splitlines()]
    if len(lines) > MAX_REFERENCE_LINES:
        return {"status": "UNKNOWN_LINE_LIMIT", "paths": [], "lines": []}
    if tests_only:
        lines = [line for line in lines if _is_test(line.split(":", 2)[0])]
    if calls_only:
        lines = [line for line in lines if not re.search(r"\b(?:async\s+)?def\s+" + re.escape(symbol) + r"\b", line)]
    paths = sorted({line.split(":", 2)[0] for line in lines})
    return {"status": "COMPLETE", "paths": paths, "lines": lines}


def _evidence(path, rev, raw, method):
    if raw is None:
        return {"revision": rev, "path": path, "start_line": None, "end_line": None,
                "content_hash": None, "extraction_method": method, "presence": "ABSENT_AT_REVISION"}
    source = raw.decode("utf-8", "replace")
    return {"revision": rev, "path": path, "start_line": 1, "end_line": max(1, len(source.splitlines())),
            "content_hash": _sha(raw), "extraction_method": method, "presence": "PRESENT"}


def _is_doc_default(doc):
    return sorted(re.findall(r"(?im)\bdefault\s*[:=]\s*([^,;\n]+)", doc or ""))


def analyze_change(repo, *, repository_id, family, split, base, head, changed, changed_paths):
    """Return unreviewed candidate facts for one pinned commit pair."""
    rows = []
    doc_changed = any(_is_docs(x["path"]) for x in changed)
    code_changed = any(_python(x["path"]) and not _is_test(x["path"]) for x in changed)
    test_changed = any(_is_test(x["path"]) for x in changed)
    docs_and_code = doc_changed and code_changed

    def emit(category, dids, path, symbol, facts, base_path=None, head_path=None):
        base_path = base_path or path; head_path = head_path or path
        evidence = [_git_evidence(repo, base, base_path),
                    _git_evidence(repo, head, head_path)]
        candidate_id = hashlib.sha256(
            f"{repository_id}:{base}:{head}:{category}:{base_path}:{head_path}:{symbol}".encode("utf-8")
        ).hexdigest()[:24]
        rows.append({
            "case_id": candidate_id, "case_candidate_id": candidate_id,
            "d_ids": list(dids), "origin": "MINED", "label_status": "UNREVIEWED_SILVER",
            "repository_id": repository_id, "family": family, "split": split,
            "base": base, "head": head, "base_revision": base, "head_revision": head,
            "path": head_path or base_path, "symbol": symbol, "candidate_category": category,
            "facts": {**facts, "evidence": evidence, "candidate_only": True},
            "artifacts": {"requirement": None, "code": evidence, "test": []},
            "requirement_source": None, "expected_trace": None, "expected_consistency": None,
            "expected_test_obligation": None, "expected_authority": None,
            "impact_ground_truth": None, "supporting_evidence_ids": [],
            "adjudication": {"status": "PENDING", "reviewer_ids": [], "rationale": None},
            "source": "local_git_history", "commit_message_used_for_labeling": False,
        })

    removed_function_names = set()
    for item in changed:
        path, old_path = item["path"], item.get("old_path") or item["path"]
        if _python(path) or _python(old_path):
            try:
                b = _git_bytes(repo, base, old_path)
                h = _git_bytes(repo, head, path)
            except UnsupportedGitObjectError:
                continue
            btree, _ = _parse(b.decode("utf-8", "replace")) if b is not None and _python(old_path) else (None, None)
            htree, _ = _parse(h.decode("utf-8", "replace")) if h is not None and _python(path) else (None, None)
            removed_function_names.update(n.rsplit(".", 1)[-1] for n in set(_funcs(btree)) - set(_funcs(htree)))

    for item in changed:
        path, status = item["path"], item["status"]
        old_path = item.get("old_path") or path
        try:
            braw, hraw = _git_bytes(repo, base, old_path), _git_bytes(repo, head, path)
        except UnsupportedGitObjectError as exc:
            emit("UNSUPPORTED_GIT_OBJECT_CANDIDATE", [], path, "", {
                "status": status, "unsupported_revision": exc.revision,
                "unsupported_object": {"mode": exc.mode, "type": exc.object_type, "object_id": exc.object_id},
                "candidate_only": True, "review_required": True,
            }, old_path, path)
            continue
        bsrc = braw.decode("utf-8", "replace") if braw is not None else ""
        hsrc = hraw.decode("utf-8", "replace") if hraw is not None else ""
        base_tree, b_error = _parse(bsrc) if _python(old_path) and braw is not None else (None, None)
        head_tree, h_error = _parse(hsrc) if _python(path) and hraw is not None else (None, None)
        bf, hf = _funcs(base_tree), _funcs(head_tree)
        symbols = sorted(set(bf) | set(hf))

        generic_kind = ("rename_candidate" if status.startswith("R") else "added_artifact_candidate" if status.startswith("A")
                        else "deleted_artifact_candidate" if status.startswith("D") else "modified_artifact_candidate")
        generic = [generic_kind]
        if _is_test(path) or _is_test(old_path): generic.append("test_file_candidate")
        if any(t in path.lower() for t in ("requirement", "specification", "openapi", "swagger")):
            generic.append("contract_file_candidate")
        emit("ARTIFACT_CHANGE_CANDIDATE", [], path, "", {"status": status, "candidate_kinds": generic,
             "old_path": old_path if old_path != path else None}, old_path, path)

        if _python(path) and h_error:
            emit("PARSER_FAILURE_CANDIDATE", DID["PARSER_FAILURE_CANDIDATE"], path, "",
                 {"parse_error": h_error, "status": "PARSER_FAILURE_CANDIDATE"}, old_path, path)
        if _python(path) and hraw is not None and braw is not None:
            try:
                bt, ht = _token_signature(bsrc), _token_signature(hsrc)
                if bsrc != hsrc and bt == ht:
                    emit("COMMENT_ONLY_CANDIDATE", [], path, "", {"text_changed": True,
                         "token_sequence_unchanged_ignoring_comments": True, "behavioral_equivalence": "NOT_ASSESSED"}, old_path, path)
            except (tokenize.TokenError, IndentationError, SyntaxError):
                pass
            if base_tree is not None and head_tree is not None and _dump(base_tree) == _dump(head_tree) and bsrc != hsrc:
                emit("FORMAT_ONLY_CANDIDATE", [], path, "", {"ast_equal": True, "raw_text_changed": True}, old_path, path)
            if _route_literals(bsrc) != _route_literals(hsrc):
                emit("ROUTE_CHANGED_CANDIDATE", DID["ROUTE_CHANGED_CANDIDATE"], path, "",
                     {"base_routes": _route_literals(bsrc), "head_routes": _route_literals(hsrc),
                      "route_compatibility": "UNREVIEWED_CANDIDATE"}, old_path, path)

        if docs_and_code and _python(path):
            emit("CO_EVOLUTION_CANDIDATE", [], path, "", {"documentation_changed_same_commit": True}, old_path, path)

        if _python(path):
            for name in symbols:
                before, after = bf.get(name), hf.get(name)
                if before is not None and after is not None and _dump(before) != _dump(after):
                    bdoc, hdoc = ast.get_docstring(before), ast.get_docstring(after)
                    if bdoc == hdoc and not doc_changed and not _is_test(path):
                        emit("CODE_CHANGED_DOC_UNCHANGED", DID["CODE_CHANGED_DOC_UNCHANGED"], path, name,
                             {"function_ast_changed": True, "function_docstring_unchanged": True,
                              "documentation_paths_changed_in_commit": False}, old_path, path)
                    if _defaults(before) != _defaults(after):
                        emit("DEFAULT_CHANGED_CANDIDATE", DID["DEFAULT_CHANGED_CANDIDATE"], path, name,
                             {"base_defaults": _defaults(before), "head_defaults": _defaults(after)}, old_path, path)
                    if _arg_names(before) != _arg_names(after) and len(_arg_names(before)) == len(_arg_names(after)):
                        emit("PARAM_RENAMED_CANDIDATE", DID["PARAM_RENAMED_CANDIDATE"], path, name,
                             {"base_parameters": _arg_names(before), "head_parameters": _arg_names(after),
                              "caller_search": _grep(repo, head, name, calls_only=True)}, old_path, path)
                    if _return_schema(before) != _return_schema(after):
                        emit("RETURN_SCHEMA_CHANGED_CANDIDATE", DID["RETURN_SCHEMA_CHANGED_CANDIDATE"], path, name,
                             {"base_return_schema": _return_schema(before), "head_return_schema": _return_schema(after)}, old_path, path)
                    b_bounds, h_bounds = _boundary_facts(before), _boundary_facts(after)
                    if b_bounds != h_bounds:
                        one_step = any(abs(a[2][0] - b[2][0]) == 1 for a in b_bounds for b in h_bounds
                                       if a[0] == b[0] and a[1] == b[1] and a[2] and b[2])
                        operator_change = any(a[0] == b[0] and a[2] == b[2] and a[1] != b[1]
                                              for a in b_bounds for b in h_bounds if a[2])
                        if one_step or operator_change:
                            emit("BOUNDARY_CHANGE_CANDIDATE", DID["BOUNDARY_CHANGE_CANDIDATE"], path, name,
                                 {"base_comparisons": b_bounds, "head_comparisons": h_bounds}, old_path, path)
                    if _exception_facts(before) != _exception_facts(after):
                        emit("EXCEPTION_CHANGE_CANDIDATE", DID["EXCEPTION_CHANGE_CANDIDATE"], path, name,
                             {"base_exceptions": _exception_facts(before), "head_exceptions": _exception_facts(after)}, old_path, path)
                    if _is_test(path) and _assertions(before) == _assertions(after):
                        emit("TEST_CHANGED_ASSERTIONS_UNCHANGED", DID["TEST_CHANGED_ASSERTIONS_UNCHANGED"], path, name,
                             {"test_body_ast_changed": True, "assertion_ast_unchanged": True}, old_path, path)
                    refs = _grep(repo, head, name, calls_only=True)
                    caller_paths = [p for p in refs["paths"] if p not in {path, old_path}]
                    if refs["status"] == "COMPLETE" and len(refs["lines"]) >= 3 and len(caller_paths) >= 2:
                        emit("SHARED_FUNCTION_CHANGED_CANDIDATE", DID["SHARED_FUNCTION_CHANGED_CANDIDATE"], path, name,
                             {"caller_reference_count": len(refs["lines"]), "caller_paths": caller_paths,
                              "reference_kind": "lexical_callsite_candidates", "reference_scan": refs["status"]}, old_path, path)
                        for caller in refs["lines"][:50]:
                            pieces = caller.split(":", 2)
                            fpath = pieces[0]
                            source = _git_bytes(repo, head, fpath)
                            caller_name = (_enclosing_function(source.decode("utf-8", "replace"), int(pieces[1]))
                                           if source is not None and len(pieces) == 3 else None)
                            if not caller_name: continue
                            second = _grep(repo, head, caller_name, calls_only=True)
                            if second["status"] == "COMPLETE" and any(p not in {fpath, path, old_path} for p in second["paths"]):
                                emit("INDIRECT_DEPENDENCY_CANDIDATE", DID["INDIRECT_DEPENDENCY_CANDIDATE"], path, name,
                                     {"direct_caller": caller_name, "direct_caller_path": fpath,
                                      "second_hop_paths": [p for p in second["paths"] if p not in {fpath, path, old_path}],
                                      "graph_status": "LEXICAL_TWO_HOP_CANDIDATE"}, old_path, path)
                                break

                elif before is None and after is not None and not after.name.startswith("_"):
                    refs = _grep(repo, head, after.name, tests_only=True)
                    if refs["status"] == "COMPLETE" and not refs["lines"]:
                        emit("ADDED_FUNCTION_NO_TEST_CANDIDATE", DID["ADDED_FUNCTION_NO_TEST_CANDIDATE"], path, name,
                             {"public_function_added": True, "test_reference_scan": refs["status"],
                              "test_reference_paths": [], "search_scope": "tracked Python files in pinned HEAD"}, old_path, path)
                elif before is not None and after is None:
                    new_funcs = list(hf.values())
                    nearest = sorted(((difflib.SequenceMatcher(None, _dump(before), _dump(n)).ratio(), n.name) for n in new_funcs), reverse=True)
                    renamed = nearest[0][1] if nearest and nearest[0][0] >= 0.82 and (len(nearest) == 1 or nearest[0][0] > nearest[1][0]) else None
                    if renamed:
                        emit("FUNCTION_RENAME_CANDIDATE", [], path, name,
                             {"renamed_to_candidate": renamed, "similarity": nearest[0][0],
                              "rename_identity": "UNREVIEWED"}, old_path, path)
                    elif not _is_test(path):
                        refs = _grep(repo, head, before.name, tests_only=True)
                        if refs["status"] == "COMPLETE" and refs["lines"]:
                            emit("DELETED_STILL_REFERENCED_CANDIDATE", DID["DELETED_STILL_REFERENCED_CANDIDATE"], path, name,
                                 {"symbol_absent_at_head": True, "renamed_to": None,
                                  "test_reference_scan": refs["status"], "test_reference_paths": refs["paths"],
                                  "test_reference_lines": refs["lines"][:100]}, old_path, path)
                    if _is_test(path):
                        emit("TEST_DELETED_CANDIDATE", [], path, name, {"test_deleted": True}, old_path, path)

        if _is_test(path) and hraw is not None:
            for target in re.findall(r"(?:mock\.)?patch\s*\(\s*['\"]([^'\"]+)['\"]", hsrc):
                name = target.rsplit(".", 1)[-1]
                if name in removed_function_names:
                    emit("MOCK_TARGET_CHANGED_CANDIDATE", DID["MOCK_TARGET_CHANGED_CANDIDATE"], path, name,
                         {"mock_target": target, "target_resolution_at_head": "NOT_FOUND_CANDIDATE"}, old_path, path)

    if test_changed and code_changed:
        for item in changed:
            if "conftest.py" in item["path"].lower() or ("fixture" in item["path"].lower() and _is_test(item["path"])):
                emit("FIXTURE_CHANGED_CANDIDATE", DID["FIXTURE_CHANGED_CANDIDATE"], item["path"], "",
                     {"fixture_path_changed": True, "behavior_path_changed_same_commit": True},
                     item.get("old_path") or item["path"], item["path"])
    return rows


def _uniform_commit_sample(commits, limit, seed):
    if len(commits) <= limit:
        return commits
    rng = random.Random(seed)
    selected = []
    for i in range(limit):
        lo = (i * len(commits)) // limit
        hi = ((i + 1) * len(commits)) // limit
        selected.append(commits[rng.randrange(lo, max(lo + 1, hi))])
    return selected


def mine_repository(repo, *, repository_id, family, split, pinned_rev, max_commits=200,
                    seed=104729, path_filters=None):
    repo = Path(repo)
    actual = run_git(repo, "rev-parse", "--verify", f"{pinned_rev}^{{commit}}").strip()
    if actual != pinned_rev:
        raise ValueError(f"Pinned revision mismatch for {repository_id}")
    commits = run_git(repo, "rev-list", pinned_rev, timeout=300).splitlines()
    commits = _uniform_commit_sample(commits, max_commits, seed)
    rows = []
    for head in commits:
        parents = run_git(repo, "rev-list", "--parents", "-n", "1", head).split()
        if len(parents) < 2:
            continue
        base = parents[1]
        changed = _name_status(repo, base, head, path_filters or [])
        if changed:
            rows.extend(analyze_change(repo, repository_id=repository_id, family=family, split=split,
                                       base=base, head=head, changed=changed,
                                       changed_paths=[c["path"] for c in changed]))
    return rows, len(commits)


def load_repo_manifest(path, split_path, overrides):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    split = json.loads(Path(split_path).read_text(encoding="utf-8"))
    if split.get("status") not in {"PROVISIONAL_PENDING_ORIGINAL_CASE_MAPPING", "FROZEN"}:
        raise ValueError("Split manifest must state a valid pre-mining status")
    if set(split.get("dev_families", [])) & set(split.get("test_families", [])):
        raise ValueError("Repository family cannot be assigned to both development and test")
    assignments = {family: "dev" for family in split.get("dev_families", [])}
    assignments.update({family: "test" for family in split.get("test_families", [])})
    rows, revisions = [], dict(overrides)
    for repo in manifest["repositories"]:
        if repo.get("phase") != "mine":
            continue
        family = repo["family"]
        if family not in assignments:
            raise ValueError(f"No predeclared split for family {family}")
        rev = revisions.get(repo["id"], repo["pinned_head_sha"])
        if rev != repo["pinned_head_sha"]:
            raise ValueError(f"--rev override must match recorded pinned SHA for {repo['id']}")
        rows.append({**repo, "split": assignments[family], "pinned_head_sha": rev})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-json", default="data/repos.json")
    parser.add_argument("--split-map", default="data/splits.json")
    parser.add_argument("--rev", action="append", default=[], metavar="REPOSITORY=SHA",
                        help="Assert the manifest-pinned revision for a repository")
    parser.add_argument("--path-filter", action="append", default=[], metavar="REPOSITORY=PATH",
                        help="Add a repository-relative prefix filter")
    parser.add_argument("--output", required=True, help="Write a new JSONL candidate file")
    parser.add_argument("--max-commits", type=int, default=200)
    parser.add_argument("--seed", type=int, default=104729)
    args = parser.parse_args()
    if not 1 <= args.max_commits <= 2000:
        parser.error("--max-commits must be between 1 and 2000")
    overrides = {}
    for item in args.rev:
        key, sep, value = item.partition("=")
        if not sep or not re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", value):
            parser.error("--rev format is REPOSITORY=40_OR_64_HEX_SHA")
        overrides[key] = value
    filters = {}
    for item in args.path_filter:
        key, sep, value = item.partition("=")
        if not sep or value.startswith("/") or ".." in Path(value).parts:
            parser.error("--path-filter format is REPOSITORY=SAFE/RELATIVE/PREFIX")
        filters.setdefault(key, []).append(value.replace("\\", "/"))
    repos = load_repo_manifest(args.repos_json, args.split_map, overrides)
    output = Path(args.output)
    if output.exists():
        parser.error("Refusing to overwrite candidate output")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    counts, failures, total = {}, [], 0
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for repo in repos:
            active_filters = filters.get(repo["id"], repo.get("path_filter") or [])
            try:
                rows, sampled = mine_repository(repo["clone_path"], repository_id=repo["id"],
                    family=repo["family"], split=repo["split"], pinned_rev=repo["pinned_head_sha"],
                    max_commits=args.max_commits, seed=args.seed, path_filters=active_filters)
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                counts[repo["id"]] = {"sampled_commits": sampled, "candidate_count": len(rows),
                                      "family": repo["family"], "split": repo["split"],
                                      "head": repo["pinned_head_sha"], "path_filter": active_filters}
                total += len(rows)
            except Exception as exc:
                failures.append({"repository_id": repo["id"], "error_type": type(exc).__name__,
                                 "message": str(exc)[:300]})
        stream.flush()
    if failures:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("Mining incomplete; no candidate output published: " + json.dumps(failures))
    temporary.replace(output)
    print(json.dumps({"status": "CANDIDATES_ONLY", "candidate_count": total,
                      "repositories": counts, "failures": failures, "output": str(output),
                      "seed": args.seed, "max_commits_per_repository": args.max_commits,
                      "labels_created": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
