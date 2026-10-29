"""Axis-wise evaluation for frozen decisions. Authored labels remain dependent."""
from collections import Counter
from math import comb, sqrt

AXES = {
    "trace": {"LINKED", "BROKEN_TRACE", "MISSING_TRACE", "UNCERTAIN"},
    "consistency": {"CONSISTENT", "INCONSISTENT", "POTENTIAL_INCONSISTENCY", "NO_ASSURANCE_IMPACT", "UNCERTAIN"},
    "test_obligation": {"SATISFIED", "UNSATISFIED", "UNVERIFIED", "NOT_APPLICABLE"},
    "authority": {"NORMATIVE", "INFORMATIONAL", "NOT_ESTABLISHED"},
}
UNKNOWN = {"", "UNKNOWN", "UNLABELED", "NOT_EVALUATED", None}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None
    p = k/n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [center-half, center+half]


def mcnemar_exact(a_only, b_only):
    n = a_only+b_only
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(a_only,b_only)+1))/(2**n)
    return min(1.0, 2*tail)


def score_axis(rows, axis, condition):
    def normalize(value):
        if value in UNKNOWN:
            return "<MISSING>"
        return value if value in AXES[axis] else "<INVALID>"
    eligible = [(r["truth"].get(axis), normalize(r.get("predictions", {}).get(condition, {}).get(axis)))
                for r in rows if r["truth"].get(axis) not in UNKNOWN]
    if any(g not in AXES[axis] for g, _ in eligible):
        raise ValueError("Invalid reference label for " + axis)
    labels = sorted({gold for gold, _ in eligible} | set(AXES[axis]))
    n = len(eligible)
    correct = sum(g == p for g,p in eligible)
    decisive = [(g,p) for g,p in eligible if p not in {"<MISSING>", "<INVALID>", "UNCERTAIN"}
                and not (axis == "authority" and p == "NOT_ESTABLISHED")
                and not (axis == "test_obligation" and p == "UNVERIFIED")]
    classes = {}
    for label in labels:
        tp=sum(p==label and g==label for g,p in eligible)
        fp=sum(p==label and g!=label for g,p in eligible)
        fn=sum(p!=label and g==label for g,p in eligible)
        classes[label]={"precision":tp/(tp+fp) if tp+fp else None,
                        "recall":tp/(tp+fn) if tp+fn else None,
                        "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                        "support":tp+fn}
    f1=[v["f1"] for v in classes.values() if v["f1"] is not None]
    truth_counts=Counter(g for g,_ in eligible)
    majority=max(truth_counts.values())/n if n else None
    prediction_labels = labels + ["<MISSING>", "<INVALID>"]
    confusion={g:{p:sum(gg==g and pp==p for gg,pp in eligible) for p in prediction_labels} for g in labels}
    errs=sum(g!=p for g,p in decisive)
    return {"n_labeled":n,"correct_including_abstentions":correct,
            "accuracy_all_labeled":correct/n if n else None,"wilson_95":wilson(correct,n),
            "macro_f1_over_observed_and_supported_classes":sum(f1)/len(f1) if f1 else None,
            "per_class":classes,"confusion_matrix":confusion,
            "majority_baseline":majority,"decisive_coverage":len(decisive)/n if n else None,
            "abstention_rate":1-len(decisive)/n if n else None,
            "selective_risk":errs/len(decisive) if decisive else None,
            "denominator_policy":"All labeled rows; missing and invalid predictions count incorrect. An abstention matches only an identical reviewed label. UNVERIFIED and NOT_ESTABLISHED are abstentions for coverage on their respective axes."}


def evaluate(data):
    rows=data["cases"]
    conditions=sorted({c for r in rows for c in r.get("predictions",{})})
    result={"status":"COMPLETED_OFFLINE_SCORE","cohort":data.get("cohort","UNSPECIFIED"),
            "split":data.get("split","UNSPECIFIED"),"case_count":len(rows),
            "independent_evaluation":data.get("independent_evaluation",False),
            "authored_or_dependent_caveat":"A cohort is not independent merely because it is scored offline.",
            "conditions":{},"paired_comparisons":{},"evidence_metrics":{}}
    for condition in conditions:
        result["conditions"][condition]={"axes":{a:score_axis(rows,a,condition) for a in AXES},
            "format_only_valid_response_rate":(
                sum(bool(r.get("predictions",{}).get(condition,{}).get("format_valid")) for r in rows) /
                len(rows) if rows else None)}
        reviewed=[r["predictions"][condition]["evidence_support_review"] for r in rows
                  if condition in r.get("predictions",{}) and type(r["predictions"][condition].get("evidence_support_review")) is bool]
        result["evidence_metrics"][condition]={"independently_reviewed_support_rate":
            sum(reviewed)/len(reviewed) if reviewed else None,"reviewed_denominator":len(reviewed),
            "status":"MEASURED" if reviewed else "NOT_MEASURED"}
    for i,a in enumerate(conditions):
        for b in conditions[i+1:]:
            legacy_axes = ("trace", "consistency", "test_obligation")
            comparable=[r for r in rows if all(r.get("truth",{}).get(axis) not in UNKNOWN for axis in legacy_axes)]
            a_only=b_only=0
            for r in comparable:
                ap=r.get("predictions",{}).get(a,{})
                bp=r.get("predictions",{}).get(b,{})
                if all(ap.get(x)==r["truth"].get(x) for x in legacy_axes) and not all(bp.get(x)==r["truth"].get(x) for x in legacy_axes):a_only+=1
                elif all(bp.get(x)==r["truth"].get(x) for x in legacy_axes) and not all(ap.get(x)==r["truth"].get(x) for x in legacy_axes):b_only+=1
            result["paired_comparisons"][a+"_vs_"+b]={"scope":"all labeled axes exact row match (descriptive only)",
                "a_correct_b_wrong":a_only,"a_wrong_b_correct":b_only,"mcnemar_exact_two_sided":mcnemar_exact(a_only,b_only)}
            per_axis = {}
            for axis in AXES:
                eligible = [r for r in rows if r.get("truth", {}).get(axis) not in UNKNOWN]
                only_a = only_b = 0
                for row in eligible:
                    gold = row["truth"][axis]
                    a_correct = row.get("predictions", {}).get(a, {}).get(axis) == gold
                    b_correct = row.get("predictions", {}).get(b, {}).get(axis) == gold
                    only_a += a_correct and not b_correct
                    only_b += b_correct and not a_correct
                per_axis[axis] = {"n": len(eligible), "a_correct_b_wrong": only_a,
                                  "a_wrong_b_correct": only_b,
                                  "mcnemar_exact_two_sided": mcnemar_exact(only_a, only_b) if eligible else None,
                                  "limitation": "Descriptive; case correlation and repository clustering are not modeled."}
            result["paired_comparisons"][a+"_vs_"+b]["per_axis"] = per_axis
    return result
