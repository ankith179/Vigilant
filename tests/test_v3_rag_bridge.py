"""RAG-to-LLM bridge tests; fixtures are synthetic and are not accuracy data."""
import subprocess

import pytest

from agents.assurance import assess_changes
from agents.decision_rules import apply_llm_guard
from change_analysis.diff import detect
from database.store import Store
from ingestion.models import DecisionV3, FactSource, FactsV3, SourcedFact
from ingestion.service import import_repository
from rag.evidence import evidence


def repository(tmp_path):
    repo=tmp_path/"repo";repo.mkdir()
    def git(*args):
        return subprocess.run(["git","-C",str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
    git("init");git("config","user.email","bridge@example.invalid");git("config","user.name","Bridge Test")
    (repo/"requirements.md").write_text("The service returns a result.\n")
    (repo/"service.py").write_text("def calculate(value):\n    return value + 1\n")
    (repo/"tests").mkdir();(repo/"tests"/"test_service.py").write_text("def test_calculate():\n    assert True\n")
    git("add",".");git("commit","-m","base");base=git("rev-parse","HEAD")
    (repo/"service.py").write_text("def calculate(value):\n    return value + 2\n")
    git("add",".");git("commit","-m","head");head=git("rev-parse","HEAD")
    store=Store("sqlite:///:memory:")
    base_import=import_repository(store,repo,rev=base)
    head_import=import_repository(store,repo,rev=head)
    before=store.artifacts(base_import["repository"],base)
    after=store.artifacts(head_import["repository"],head)
    changes=detect(repo,base,head,before,after)
    return repo,base,head,before,after,changes


def test_retrieved_head_excerpt_is_verified_and_passed_to_semantic_provider(tmp_path,monkeypatch):
    import agents.assurance as assurance
    repo,base,head,before,after,changes=repository(tmp_path)
    target=next(a for a in after if a.file_path=="tests/test_service.py")
    rag=evidence(target,"bm25",score=0.8);rag["selection_arm"]="retrieval"
    captured=[]
    rule=DecisionV3(needs_llm=True,rule_id="TEST_SEMANTIC_RESIDUE")
    class FakeProvider:
        def investigate_v3(self,question,items,facts,**kwargs):
            captured.append((items,kwargs))
            return {"decision":rule.model_dump(),"inference_requested":False}
    monkeypatch.setattr(assurance,"decide",lambda facts:rule)
    monkeypatch.setattr(assurance,"inspect_local",lambda *args:{"status":"ASSETS_READY"})
    monkeypatch.setattr("llm.providers.provider",lambda name:FakeProvider())
    result=assess_changes(changes,before,after,repo,model="local",retrieved_evidence=[rag])
    assert result["rag_candidates_verified"]==1
    assert captured
    items,kwargs=captured[0]
    assert rag["evidence_id"] in {x["evidence_id"] for x in items}
    assert rag["evidence_id"] in kwargs["validated_evidence_ids"]
    assert not any(x.get("raw_outputs") for x in result["assessments"])


def test_retrieved_evidence_from_wrong_revision_is_rejected(tmp_path):
    repo,base,head,before,after,changes=repository(tmp_path)
    target=next(a for a in after if a.file_path=="tests/test_service.py")
    rag=evidence(target,"bm25");rag["selection_arm"]="retrieval";rag["commit"]=base
    with pytest.raises(ValueError,match="exact HEAD snapshot"):
        assess_changes(changes,before,after,repo,model="local",retrieved_evidence=[rag])


def test_guard_accepts_only_explicitly_verified_head_retrieval_citations():
    sources=[FactSource(revision="HEAD",commit_id="head",path=path,start_line=1,end_line=1,
        content_hash=(str(i+1)*64)[:64],extraction_method="fixture",artifact_role=role,evidence_id=eid)
        for i,(eid,role,path) in enumerate((
            ("req","requirement","req.md"),("impl","implementation","src.py"),("test","test","test.py")))]
    facts=FactsV3(evidence_sufficient=SourcedFact(value=True,sources=sources),
        has_head_evidence_for_req_impl_test=SourcedFact(value=True,sources=sources))
    rule=DecisionV3(needs_llm=True,contract_authority="NORMATIVE")
    proposed=DecisionV3(consistency="CONSISTENT",contract_authority="NORMATIVE",
        evidence_ids=["req","impl","test","rag"],rationale="supported")
    citations=["req","impl","test","rag"]
    verified=[{"evidence_id":"rag","artifact_role":"requirement"}]
    accepted=apply_llm_guard(rule,facts,proposed,votes_agree=True,valid_head_citations=citations,
        valid_citations=citations,verified_head_evidence=verified)
    rejected=apply_llm_guard(rule,facts,proposed,votes_agree=True,valid_head_citations=citations,
        valid_citations=citations)
    assert accepted.consistency=="CONSISTENT"
    assert rejected.consistency=="UNCERTAIN"



def test_workflow_forwards_verified_retrieval_candidates_to_assurance(tmp_path,monkeypatch):
    import agents.workflow as workflow
    repo,base,head,before,after,changes=repository(tmp_path)
    captured={}
    def retrieve_one(query,artifacts,graph=None,seeds=(),encoder=None,k=8,max_chars=8000):
        target=next(a for a in artifacts if a.file_path=="tests/test_service.py")
        row=evidence(target,"bm25",score=0.8);row["selection_arm"]="retrieval"
        return [row]
    def fake_assess(changes,before,after,repo,*,retrieved_evidence=(),**kwargs):
        captured["items"]=list(retrieved_evidence)
        return {"schema_version":3,"assessments":[],"evidence":[],"preflight":None,
            "model_scopes":0,"max_model_scopes":3,"max_calls_per_scope":9}
    monkeypatch.setattr(workflow,"retrieve",retrieve_one)
    monkeypatch.setattr("agents.assurance.assess_changes",fake_assess)
    report=workflow.analyze(Store("sqlite:///:memory:"),repo,base,model="local")
    assert report["status"]=="COMPLETED"
    rag_rows=[item for item in captured["items"] if item.get("selection_arm")=="retrieval"]
    assert len(rag_rows)==1
    assert rag_rows[0]["revision_role"]=="head"
