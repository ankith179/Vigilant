import copy
import unittest
from pydantic import ValidationError
from tools.case_card_v1 import CaseCard

BASE = {"case_id":"c1", "d_ids":["D14"], "priority_tier":"P1", "origin":"MINED",
        "source_id":"repo", "family":"repo", "split":"dev", "history_source":"A",
        "base_revision":"base", "head_revision":"head",
        "artifacts":{"requirement":[], "code":[{"path":"a.py", "revision":"head", "content_hash":"a"*64}], "test":[]},
        "change_facts":{}, "requirement_source":None, "expected_trace":None, "expected_consistency":None,
        "expected_test_obligation":None, "expected_authority":None, "impact_ground_truth":None,
        "supporting_evidence_ids":[], "adjudication":{"status":"PENDING", "reviewer_ids":[], "rationale":None},
        "notes":"", "label_status":"UNREVIEWED_SILVER"}

class CaseCardTests(unittest.TestCase):
    def test_unreviewed_card(self):
        self.assertEqual(CaseCard.model_validate(BASE).case_id, "c1")

    def test_rejects_invalid_provenance_and_labels(self):
        for change in (lambda c: c.update(expected_consistency="CONSISTENT"),
                       lambda c: c.update(history_source="NO_HISTORY"),
                       lambda c: c["artifacts"]["code"][0].update(content_hash=""),
                       lambda c: c["artifacts"]["code"][0].update(revision="other"),
                       lambda c: c.update(origin="SYNTHETIC", split="test")):
            item = copy.deepcopy(BASE)
            change(item)
            with self.assertRaises(ValidationError):
                CaseCard.model_validate(item)

if __name__ == "__main__":
    unittest.main()
