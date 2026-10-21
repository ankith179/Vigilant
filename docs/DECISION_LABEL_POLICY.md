# Proposed decision policy v1 - independent review required

This is a proposed annotation policy, not a retrospective relabeling of the
12 authored cases. It is NOT applied to the citation-only comparison. Reviewers
must approve it before using it to create new validation/test labels. The current
prompt remains frozen for that comparison.

The unit is one stated contract at a specified base/head change. Record multiple
findings separately when the change affects unrelated contracts. A missing
excerpt means unavailable evidence, not a missing implementation or test.

Use the first supported rule below for a single required primary label. Record
secondary finding types separately. A higher-priority label needs its own
positive evidence; precedence never supplies missing evidence.

| Order | Label | Necessary evidence and boundary |
| ---: | --- | --- |
| 1 | INCONSISTENT | A specific applicable contract and implementation/caller/test directly contradict one another at head. Cite both sides. A mere change or unchanged test is insufficient. |
| 2 | BROKEN_TRACE | An explicitly declared trace endpoint existed at base and is absent at head, supported by an exact inventory/diff. Similarity links are not declarations. Excerpt omission does not prove deletion. If an observable contract contradiction is established, use INCONSISTENT instead. |
| 3 | MISSING_TEST | An explicit testing obligation applies and a reviewed test inventory shows it is unmet. A deleted test alone does not establish this if equivalent coverage may exist. A present test that contradicts its contract belongs under INCONSISTENT. |
| 4 | POTENTIAL_INCONSISTENCY | Concrete evidence suggests a particular mismatch, but one named, testable assumption is unresolved. State the supporting facts and the assumption. Generic lack of context is UNCERTAIN. |
| 5 | AFFECTED | A supported dependency is exposed to the change, without evidence satisfying the preceding labels. Name the dependency and affected operation. A graph candidate alone is insufficient if resolution is ambiguous. |
| 6 | CONSISTENT | Supplied evidence positively establishes compliance for the entire stated check. Absence of a detected defect is insufficient. Do not use this to certify the repository as a whole. |
| 7 | UNCERTAIN | The evidence cannot support a higher rule for this check, including insufficient contract, missing relevant implementation, unresolved scope, or ambiguous dependency resolution. Name what is needed. |

For all labels, separately record evidence sufficiency (`sufficient`, `partial`,
`insufficient`), supporting aliases and line ranges, missing facts, and whether
the answer changes with additional repository context. Confidence is not an
accuracy estimate. Citation resolution and semantic support are separate axes.

## Independent review procedure

Two reviewers work independently without seeing model answers, historical gold
labels, or each other's labels. Give them the exact prompt packets first. Ask
whether a human can answer from those same excerpts; record missing evidence
before showing additional context. Then allow repository inspection to establish
the repository-level label, recording every additional source. Distinguish the
prompt-answerable label from the full-repository label.

Use `reports/citation-fix-20261021/review/independent-labels.csv`. Its label and
reviewer fields are intentionally blank. Record both initial labels, agreement,
and an adjudicator's final decision/rationale; never overwrite disagreement.
Report raw agreement and a chance-adjusted statistic with its limitations.
Keep ambiguous/unanswerable cases visible rather than dropping them to raise a
score. The user confirmed that no independently reviewed dataset is available.

The review packets contain source text from controlled mutations, which can
reveal the nature of the change. They are not independent held-out material.
