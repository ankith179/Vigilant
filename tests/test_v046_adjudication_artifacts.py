import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V046 = ROOT / "reports" / "v046"
EXPECTED = "c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864"


def test_frozen_diagnostic_hash_and_case_coverage():
    manifest = json.loads((V046 / "frozen_case_manifest.json").read_text(encoding="utf-8"))
    source = ROOT / manifest["immutable_source"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED
    assert manifest["source_sha256"] == EXPECTED
    assert manifest["case_count"] == 12
    assert len(manifest["case_ids"]) == 12
    assert manifest["authored_match_count"] == 4


def test_protocol_and_blinded_sheets_are_consistent():
    protocol = (V046 / "adjudication_protocol.md").read_bytes()
    protocol_hash = hashlib.sha256(protocol).hexdigest()
    sheets = sorted((V046 / "case_review_sheets").glob("review-*.json"))
    assert len(sheets) == 12
    for path in sheets:
        sheet = json.loads(path.read_text(encoding="utf-8"))
        assert sheet["protocol_sha256"] == protocol_hash
        assert sheet["review_status"] == "PENDING"
        assert sheet["review_blinding"] == {
            "authored_label_included": False,
            "historical_prediction_included": False,
            "raw_model_output_included": False,
            "raw_confidence_included": False,
            "original_prompt_included": False,
        }
        assert sheet["reviewer_judgment"]["status"] == "PENDING"
        assert sheet["reviewer_judgment"]["traceability_disposition"] is None
        assert sheet["reviewer_judgment"]["consistency"] is None


def test_no_judgments_or_predictions_fabricated():
    labels = json.loads((V046 / "reviewed_labels.json").read_text(encoding="utf-8"))
    replay = json.loads((V046 / "replay" / "replay_manifest.json").read_text(encoding="utf-8"))
    inputs = json.loads((V046 / "replay" / "frozen_inputs.json").read_text(encoding="utf-8"))
    assert labels["reviewer_count"] == 0
    assert labels["completed_independent_reviews"] == 0
    assert len(labels["cases"]) == 12
    assert all(c["status"] == "PENDING" and c["consensus"] is None for c in labels["cases"])
    assert replay["status"] == "BLOCKED"
    assert replay["inference_calls"] == 0
    assert replay["predictions_created"] == 0
    assert len(inputs["cases"]) == 12
    assert replay["frozen_input_package"]["contains_labels"] is False
    assert replay["frozen_input_package"]["sha256"] == hashlib.sha256((V046 / "replay" / "frozen_inputs.json").read_bytes()).hexdigest()
    forbidden = {"expected_label", "expected_status", "actual_label", "prediction", "raw_model_output", "confidence"}
    assert all(not (forbidden & set(case)) for case in inputs["cases"])
    assert not (V046 / "replay" / "predictions.json").exists()
    assert not (V046 / "replay" / "raw_outputs.jsonl").exists()
