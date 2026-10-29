# D-ID 33/36 Status Check

**Status: `NOT_MEASURED` as accuracy and `NOT_MEASURED` as a frozen 36-case evaluation.**

The latest verified mining report (`reports/v047/mining-10commit-seed104730-20261028.md` and its JSON) records 746 mined candidate records across 12 repositories and 8 families. D-ID coverage is **13 of 24 candidate categories** (`D14, D17, D19, D20, D22, D23, D25, D26, D27, D28, D30, D31, D36`); 11 of those categories have no candidate in that batch (`D13, D15, D16, D18, D21, D24, D29, D32, D33, D34, D35`).

The candidate-card audit converted 279 D-ID-tagged records; the other 467 records had no D-ID assignment. Every converted card remains `UNREVIEWED_SILVER`, in `dev`, with assessment labels null and adjudication `PENDING`. No 36-case evaluation set was frozen and no predictions or gold judgments were produced. The evaluation-pool audit explicitly records **development 33/36: `NOT_MEASURED`**.

The D1–D12 original-case-to-repository mapping is not fully verified, so a total coverage fraction across all 36 D-IDs cannot be computed without assuming the unresolved mapping. The separate diagnostic-category coverage scaffold also remains at zero; it is a different inventory from mined D-ID coverage.

**Conclusion:** 33/36 has not been achieved as accuracy. Candidate/category coverage is not accuracy. The 11/12 V049 result is a separate 12-case authored-label regression agreement and must not be substituted for a 36-case result.

To measure 33/36 performance, first freeze the 36-case membership and repository split, resolve original-case mapping, obtain blind reviewed labels, then freeze predictions and score the predeclared metric. Until then the metric remains `NOT_MEASURED`.
