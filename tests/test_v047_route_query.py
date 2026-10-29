from agents.evidence_first import analysis_packet
from ingestion.models import artifact


def test_route_candidate_comparison_uses_method_and_path_not_query_values():
    caller = artifact("p", "r", "head", "client.py", "api_caller", "load",
                      'get("/items?limit=2")', metadata={"method": "GET", "route": "/items?limit=2"})
    api = artifact("p", "r", "head", "api.py", "api", "GET /items",
                   "route", metadata={"method": "GET", "route": "/items"})
    packet = analysis_packet({"base_commit": "base", "head_commit": "head",
                              "files": [], "artifacts": []}, [], [caller, api], [])
    assert packet["route_compatibility_candidates"][0]["status"] == "LITERAL_ROUTE_MATCH_CANDIDATE"
    assert packet["route_compatibility_candidates"][0]["runtime_compatibility_verified"] is False
