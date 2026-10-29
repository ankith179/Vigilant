from ingestion.parsers import extract
from ingestion.models import artifact
from agents.decision_rules import extract_facts, decide

def change_row(a, kind, new=None):
    return {"artifact_id": a.artifact_id, "new_artifact_id": new.artifact_id if new else None,
            "kind": kind, "artifact_type": a.artifact_type, "file": a.file_path, "symbol": a.symbol}

def test_deleted_python_function_with_same_module_head_test_reference_is_fact_and_rule():
    base = extract("p", "r", "base", "module.py", """def redirect(url):
    return url
""")
    head = extract("p", "r", "head", "module.py", """def test_old_route():
    redirect("/")
""")
    fn = next(a for a in base if a.artifact_type == "function")
    changes = {"base_commit": "base", "head_commit": "head",
        "files": [{"old_path": "module.py", "new_path": "module.py", "text_changed": True, "change_semantics": "NOT_CLASSIFIED"}],
        "artifacts": [change_row(fn, "deleted")]}
    facts = extract_facts(changes, base, head, subject_id=fn.artifact_id)
    assert facts.symbol_deleted_at_head.value is True
    assert facts.renamed_to.value is False
    assert facts.head_refs_symbol.value is True
    assert facts.symbol_deleted_at_head.sources[-1].revision == "HEAD"
    out = decide(facts)
    assert out.trace == "BROKEN_TRACE" and out.consistency == "INCONSISTENT"
    assert out.rule_id == "R1_DELETED_STILL_REFERENCED"

def test_comment_marker_detection_uses_python_comment_tokens():
    before = extract("p", "r", "base", "module.py", """# old
def f():
    return 1
""")
    after = extract("p", "r", "head", "module.py", """# must always return 1
def f():
    return 1
""")
    row = next(a for a in before if not a.symbol)
    new_row = next(a for a in after if not a.symbol)
    changes = {"base_commit": "base", "head_commit": "head",
         "files": [{"old_path": "module.py", "new_path": "module.py", "text_changed": True, "change_semantics": "COMMENT_ONLY",
                    "patch": "--- a/module.py\n+++ b/module.py\n@@ -1 +1 @@\n-# old\n+# must always return 1"}],
        "artifacts": [change_row(row, "modified", new_row)]}
    facts = extract_facts(changes, before, after, subject_id=row.artifact_id)
    assert facts.comment_has_contract_markers.value is True
    assert decide(facts).rule_id == "R2B_COMMENT_CONTRACT_TEXT"

def test_renamed_function_is_a_candidate_not_a_deleted_symbol():
    before = extract("p", "r", "base", "module.py", """def old_name(value):
    return value + 1
""")
    after = extract("p", "r", "head", "module.py", """def new_name(value):
    return value + 1
""")
    old = next(a for a in before if a.artifact_type == "function")
    new = next(a for a in after if a.artifact_type == "function")
    changes = {"base_commit": "base", "head_commit": "head",
        "files": [{"old_path": "module.py", "new_path": "module.py", "text_changed": True, "change_semantics": "NOT_CLASSIFIED"}],
        "artifacts": [change_row(old, "deleted"), change_row(new, "added", new)]}
    facts = extract_facts(changes, before, after, subject_id=old.artifact_id)
    assert facts.renamed_to.value == {"path": "module.py", "symbol": "new_name"}
    assert facts.symbol_deleted_at_head.value is True
    assert decide(facts).trace == "LINKED"


def test_rename_plus_edit_remains_unknown_instead_of_asserting_no_rename():
    before = extract("p", "r", "base", "module.py", """def old_name(value):
    return value + 1
""")
    after = extract("p", "r", "head", "module.py", """def new_name(value):
    return value + 2
""")
    old = next(a for a in before if a.artifact_type == "function")
    new = next(a for a in after if a.artifact_type == "function")
    changes = {"base_commit":"base","head_commit":"head",
        "files":[{"old_path":"module.py","new_path":"module.py","text_changed":True,"change_semantics":"NOT_CLASSIFIED"}],
        "artifacts":[change_row(old,"deleted"),change_row(new,"added",new)]}
    facts = extract_facts(changes,before,after,subject_id=old.artifact_id)
    assert facts.renamed_to.value is None
    assert "rename" in facts.renamed_to.unknown_reason.lower()

def test_cross_file_head_test_reference_is_not_recorded_as_absent():
    before = extract("p","r","base","module.py","""def redirect(url):
    return url
""")
    head_module = extract("p","r","head","module.py","VALUE = 1\n")
    head_test = extract("p","r","head","tests/test_module.py","""from module import redirect

def test_route():
    redirect("/")
""")
    fn=next(a for a in before if a.artifact_type=="function")
    changes={"base_commit":"base","head_commit":"head",
        "files":[{"old_path":"module.py","new_path":"module.py","text_changed":True,"change_semantics":"NOT_CLASSIFIED"}],
        "artifacts":[change_row(fn,"deleted")]}
    facts=extract_facts(changes,before,head_module+head_test,subject_id=fn.artifact_id)
    assert facts.head_refs_symbol.value is True

def test_whole_file_deletion_has_head_deletion_receipt_without_head_source():
    before=extract("p","r","base","module.py","""def redirect(url):
    return url
""")
    fn=next(a for a in before if a.artifact_type=="function")
    changes={"base_commit":"base","head_commit":"head",
        "files":[{"status":"D","old_path":"module.py","new_path":"module.py","patch":"deleted bytes"}],
        "artifacts":[change_row(fn,"deleted")]}
    facts=extract_facts(changes,before,[],subject_id=fn.artifact_id)
    assert facts.evidence_sufficient.value is True
    assert facts.symbol_deleted_at_head.value is True
    assert any(s.revision=="HEAD" for s in facts.symbol_deleted_at_head.sources)
    assert any(s.revision=="BASE" for s in facts.symbol_deleted_at_head.sources)


def route_facts(caller_method, caller_route, *, route_method="GET", required_parameters=(), keep_alias=False,
                head_handler_id="items"):
    base_file = artifact("p", "r", "base", "backend/routes.py", "source_file", "",
                         'router.get("/items")', metadata={"language": "python"})
    base_route = artifact("p", "r", "base", "backend/routes.py", "api", "GET /items::list_items",
                          'route("/items")', metadata={"method": "GET", "route": "/items", "handler_id": "base-handler-id"})
    head_file = artifact("p", "r", "head", "backend/routes.py", "source_file", "",
                         'router.get("/catalog")', metadata={"language": "python"})
    head_route = artifact("p", "r", "head", "backend/routes.py", "api", f"{route_method} /catalog::list_items",
                          'route("/catalog")', metadata={"method": route_method, "route": "/catalog",
                          "handler_id": head_handler_id, "required_parameters": list(required_parameters)})
    caller = artifact("p", "r", "head", "client.py", "api_caller", "load",
                      f'{caller_method.lower()}("{caller_route}")',
                      metadata={"method": caller_method, "route": caller_route})
    after = [head_file, head_route, caller]
    if keep_alias:
        after.append(artifact("p", "r", "head", "backend/routes.py", "api", "GET /items",
                              'route("/items")', metadata={"method": "GET", "route": "/items", "handler_id": "items"}))
    changes = {"base_commit": "base", "head_commit": "head",
        "files": [{"old_path": "backend/routes.py", "new_path": "backend/routes.py",
                   "text_changed": True, "change_semantics": "AST", "patch": "route changed"}],
        "artifacts": [{"artifact_id": base_route.artifact_id, "new_artifact_id": head_route.artifact_id,
                       "kind": "modified", "artifact_type": "api", "file": "backend/routes.py",
                       "symbol": "GET /items::list_items"}]}
    return extract_facts(changes, [base_file, base_route], after,
                         subject_id=base_route.artifact_id)


def test_route_change_compares_consumer_method_path_and_required_query_parameters():
    mismatch = route_facts("GET", "/items")
    assert mismatch.route_changed.value is True
    assert mismatch.consumer_matches_new_route.value is False
    assert decide(mismatch).rule_id == "R5_ROUTE_CONSUMER_MISMATCH"

    migrated = route_facts("GET", "/catalog?limit=2", required_parameters=("limit",))
    assert migrated.consumer_matches_new_route.value is True
    assert decide(migrated).rule_id != "R5_ROUTE_CONSUMER_MISMATCH"

    missing_required_parameter = route_facts("GET", "/catalog", required_parameters=("limit",))
    assert missing_required_parameter.consumer_matches_new_route.value is False
    assert decide(missing_required_parameter).rule_id == "R5_ROUTE_CONSUMER_MISMATCH"

    method_mismatch = route_facts("POST", "/catalog?limit=2", required_parameters=("limit",))
    assert method_mismatch.consumer_matches_new_route.value is False
    assert decide(method_mismatch).rule_id == "R5_ROUTE_CONSUMER_MISMATCH"

    kept_alias = route_facts("GET", "/items", keep_alias=True)
    assert decide(kept_alias).rule_id != "R5_ROUTE_CONSUMER_MISMATCH"


def test_route_change_uses_stable_handler_symbol_when_revision_ids_differ():
    stale = route_facts("GET", "/items", head_handler_id="head-handler-id")
    assert stale.route_changed.value is True
    assert stale.consumer_matches_new_route.value is False
    assert decide(stale).rule_id == "R5_ROUTE_CONSUMER_MISMATCH"

    migrated = route_facts("GET", "/catalog", head_handler_id="head-handler-id")
    assert migrated.consumer_matches_new_route.value is True
    assert decide(migrated).rule_id != "R5_ROUTE_CONSUMER_MISMATCH"


def test_changed_literal_consumer_is_stale_only_after_base_route_match_breaks():
    base_call = artifact("p", "r", "base", "client.py", "api_caller",
                         "GET /items::ItemsService.readItems", 'get("/items")',
                         metadata={"method": "GET", "route": "/items"})
    head_call = artifact("p", "r", "head", "client.py", "api_caller",
                         "GET /obsolete::ItemsService.readItems", 'get("/obsolete")',
                         metadata={"method": "GET", "route": "/obsolete"})
    base_route = artifact("p", "r", "base", "api.py", "api", "GET /items",
                          'route("/items")', metadata={"method": "GET", "route": "/items"})
    head_route = artifact("p", "r", "head", "api.py", "api", "GET /items",
                          'route("/items")', metadata={"method": "GET", "route": "/items"})
    base_client_file = artifact("p", "r", "base", "client.py", "source_file", "", 'get("/items")',
                                metadata={"language": "python"})
    head_client_file = artifact("p", "r", "head", "client.py", "source_file", "", 'get("/obsolete")',
                                metadata={"language": "python"})
    base_api_file = artifact("p", "r", "base", "api.py", "source_file", "", 'route("/items")',
                             metadata={"language": "python"})
    head_api_file = artifact("p", "r", "head", "api.py", "source_file", "", 'route("/items")',
                             metadata={"language": "python"})
    changes = {"base_commit": "base", "head_commit": "head",
        "files": [{"old_path": "client.py", "new_path": "client.py", "text_changed": True}],
        "artifacts": [change_row(base_call, "deleted"), change_row(head_call, "added", head_call)]}
    facts = extract_facts(changes, [base_call, base_route, base_client_file, base_api_file],
                          [head_call, head_route, head_client_file, head_api_file],
                          subject_id=base_call.artifact_id)
    assert facts.stale_consumer.value is True
    out = decide(facts)
    assert out.trace == "BROKEN_TRACE" and out.consistency == "POTENTIAL_INCONSISTENCY"
    assert all(source.revision in {"BASE", "HEAD"} for source in facts.stale_consumer.sources)

    migrated = artifact("p", "r", "head", "client.py", "api_caller",
                        "GET /items::ItemsService.readItems", 'get("/items")',
                        metadata={"method": "GET", "route": "/items"})
    changes["artifacts"][1] = change_row(migrated, "added", migrated)
    facts = extract_facts(changes, [base_call, base_route, base_client_file, base_api_file],
                          [migrated, head_route, head_client_file, head_api_file],
                          subject_id=base_call.artifact_id)
    assert facts.stale_consumer.value is None


def test_changed_requirement_with_unchanged_linked_test_is_only_potential():
    base_req = artifact("p", "r", "base", "REQ-1.md", "requirement", "REQ-1", "old requirement")
    head_req = artifact("p", "r", "head", "REQ-1.md", "requirement", "REQ-1", "changed requirement")
    base_test = artifact("p", "r", "base", "tests/test_req.py", "test", "test_req", "assert behavior()")
    head_test = artifact("p", "r", "head", "tests/test_req.py", "test", "test_req", "assert behavior()")
    base_req_file = artifact("p", "r", "base", "REQ-1.md", "source_file", "", "old requirement")
    head_req_file = artifact("p", "r", "head", "REQ-1.md", "source_file", "", "changed requirement")
    link = {"source_artifact": head_req.artifact_id, "target_artifact": head_test.artifact_id,
            "relation_type": "VALIDATES", "method": "upstream-rtmx-module-declaration"}
    changes = {"base_commit": "base", "head_commit": "head",
        "files": [{"old_path": "REQ-1.md", "new_path": "REQ-1.md", "text_changed": True}],
        "artifacts": [change_row(base_req, "modified", head_req)]}
    facts = extract_facts(changes, [base_req, base_test, base_req_file],
                          [head_req, head_test, head_req_file], declared_links=[link],
                          subject_id=base_req.artifact_id)
    out = decide(facts)
    assert out.rule_id == "R8_CHANGED_REQUIREMENT_LINKED_TEST_UNCHANGED"
    assert out.consistency == "POTENTIAL_INCONSISTENCY" and out.needs_review

    changed_test = artifact("p", "r", "head", "tests/test_req.py", "test", "test_req",
                            "assert changed_behavior()")
    updated = {**link, "target_artifact": changed_test.artifact_id}
    facts = extract_facts(changes, [base_req, base_test, base_req_file],
                          [head_req, changed_test, head_req_file], declared_links=[updated],
                          subject_id=base_req.artifact_id)
    assert facts.linked_verification_unchanged.value is False
    assert decide(facts).rule_id != "R8_CHANGED_REQUIREMENT_LINKED_TEST_UNCHANGED"
