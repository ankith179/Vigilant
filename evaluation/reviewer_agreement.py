"""Descriptive agreement statistics for two completed reviewer forms."""
from collections import Counter

from evaluation.review_intake import ReviewerForm


LABELS = (
    "CONSISTENT",
    "INCONSISTENT",
    "POTENTIAL_INCONSISTENCY",
    "BROKEN_TRACE",
    "MISSING_TEST",
    "AFFECTED",
    "UNCERTAIN",
)


def _kappa(left, right):
    """Return nominal Cohen's kappa and its inputs; undefined remains null."""
    n = len(left)
    matrix = {a: {b: 0 for b in LABELS} for a in LABELS}
    for a, b in zip(left, right):
        matrix[a][b] += 1
    rows = {a: sum(matrix[a].values()) for a in LABELS}
    columns = {b: sum(matrix[a][b] for a in LABELS) for b in LABELS}
    observed = sum(matrix[label][label] for label in LABELS) / n
    expected = sum(rows[label] * columns[label] for label in LABELS) / (n * n)
    value = None if expected == 1 else (observed - expected) / (1 - expected)
    return {
        "n": n,
        "raw_agreement": observed,
        "cohen_kappa": value,
        "kappa_status": "UNDEFINED_DEGENERATE_MARGINALS" if value is None else "DEFINED",
        "labels": list(LABELS),
        "confusion_matrix_reviewer_1_rows_reviewer_2_columns": matrix,
    }


def _set_agreement(left, right):
    intersections = [a & b for a, b in zip(left, right)]
    intersection_count = sum(map(len, intersections))
    left_count = sum(map(len, left))
    right_count = sum(map(len, right))
    union_count = sum(len(a | b) for a, b in zip(left, right))
    exact = sum(a == b for a, b in zip(left, right))
    per_case_jaccard = [len(a & b) / len(a | b) if a | b else 1.0 for a, b in zip(left, right)]
    precision = intersection_count / left_count if left_count else None
    recall = intersection_count / right_count if right_count else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else 0.0 if precision is not None and recall is not None else None
    )
    return {
        "cases": len(left),
        "exact_set_agreement_cases": exact,
        "exact_set_agreement_rate": exact / len(left),
        "mean_case_jaccard_empty_empty_is_one": sum(per_case_jaccard) / len(per_case_jaccard),
        "reviewer_1_to_reviewer_2_micro": {
            "intersection": intersection_count,
            "reviewer_1_items": left_count,
            "reviewer_2_items": right_count,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "status": "UNDEFINED_EMPTY_DENOMINATOR" if precision is None or recall is None else "DEFINED",
        },
        "union_items": union_count,
    }


def summarize_reviewer_agreement(forms):
    """Validate and compare exactly two independent, case-matched forms.

    The independence fields are attestations only; this function does not
    authenticate people or verify source evidence. Source validation remains
    the responsibility of ``scripts/import_independent_reviews.py``.
    """
    if not isinstance(forms, list) or len(forms) != 2:
        raise ValueError("Exactly two reviewer forms are required")
    reviewers = [ReviewerForm.model_validate(form) for form in forms]
    ids = [form.reviewer_id.strip() for form in reviewers]
    if not all(ids) or ids[0] == ids[1]:
        raise ValueError("Two distinct nonempty reviewer IDs are required")
    if not all(form.independent_of_pipeline_author for form in reviewers):
        raise ValueError("Both forms must attest independence from the pipeline author")

    by_reviewer = []
    for form in reviewers:
        cases = [assessment.model_dump() for assessment in form.cases]
        ids_in_form = [case["case_id"] for case in cases]
        if len(set(ids_in_form)) != len(ids_in_form):
            raise ValueError("Duplicate case IDs in reviewer form")
        by_reviewer.append({case["case_id"]: case for case in cases})
    left_ids, right_ids = set(by_reviewer[0]), set(by_reviewer[1])
    if left_ids != right_ids:
        raise ValueError("Reviewer case sets do not match")
    case_ids = sorted(left_ids)
    if not case_ids:
        raise ValueError("At least one shared case is required")

    left = [by_reviewer[0][case_id] for case_id in case_ids]
    right = [by_reviewer[1][case_id] for case_id in case_ids]
    label_agreement = _kappa(
        [case["consistency_label"] for case in left],
        [case["consistency_label"] for case in right],
    )
    trace_agreement = _set_agreement(
        [set(case["trace_links"]) for case in left],
        [set(case["trace_links"]) for case in right],
    )
    affected_agreement = _set_agreement(
        [set(case["affected_artifact_ids"]) for case in left],
        [set(case["affected_artifact_ids"]) for case in right],
    )
    return {
        "status": "INTER_RATER_AGREEMENT_DESCRIPTIVE_ONLY",
        "reviewer_ids": ids,
        "reviewer_independence": "SELF_ATTESTED_NOT_AUTHENTICATED",
        "case_count": len(case_ids),
        "case_ids": case_ids,
        "consistency_label": label_agreement,
        "trace_link_sets": trace_agreement,
        "affected_artifact_sets": affected_agreement,
        "limitations": [
            "Agreement is not accuracy, semantic support, or evidence-source verification.",
            "UNCERTAIN is retained as a label; abstentions are not dropped.",
            "Reviewer forms do not encode a complete negative-link search scope; empty sets do not prove absence.",
            "The two reviewers are not authenticated by these files.",
            "Use a separate adjudication record; do not overwrite either initial form.",
        ],
    }
