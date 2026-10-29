# Real-world research plan

Status: development plan, not a frozen independent protocol. Target: separate
traceability precision/recall/F1 and consistency accuracy/macro-F1 of at least
0.91. No operational-test count is combined with either research metric.

## Verified benchmark source

The current trace-ranking study uses the public LiSSA ICSE 2025 replication
package at commit `a8e652f29bbdcc4bdcd3d98cd85aa4a37cb65480`.
The official repository and commit were rechecked through read-only GitHub access
on 23 October 2026. The outer package declares MIT; dataset-specific notices are
retained and are not blanket-relicensed. Paper DOI:
`10.1109/ICSE55347.2025.00186`; replication DOI:
`10.5281/zenodo.14714706`.

| Project | Role already used by VIGILANT | Allowed conclusion |
| --- | --- | --- |
| SMOS | Training | Fit retrieval/ranking policy only. |
| iTrust | Validation | Development comparison; no policy update. |
| eTour English | Test | Previously exposed development test; not final independent evidence. |
| RTMX module-valid | External sanity check | Small authored project with exclusions; not comparable to the LiSSA projects. |

All four projects and their saved rankings were exposed before this plan. They
must stay on the tuning/exposure ledger and cannot be promoted to the final test.

## Bounded reinforcement-learning increment

Use an offline LinUCB contextual bandit whose arms are the existing frozen
TF-IDF, BM25, embedding and hybrid rankings. The only reward is per-query average
precision from SMOS reviewed positive links. Query-text features contain no
labels. Validation/test rewards never update the policy. Compare the frozen
selector with every fixed arm and preserve a negative result. This is policy
learning over retrieval arms, not LLM-weight reinforcement learning.

Full LLM-weight RL is out of scope until reliable independently reviewed rewards,
suitable hardware and a preregistered protocol exist. It must never be reported
as run without training logs and weight/checkpoint fingerprints.

## Task boundaries

- Trace-link recovery uses reviewed directed links and ranking/link metrics.
- Fault localization needs defect-to-location gold and is not supplied by the
  LiSSA trace matrices.
- Change impact needs independently reviewed affected sets; a bug-fix diff is
  neither complete impact truth nor a negative label for unchanged artifacts.
- Consistency needs one adjudicated contract question per case and its frozen
  decision rubric. A trace link or changed file does not supply that label.
- Semantic support needs claim/excerpt review; valid hashes and spans alone do
  not establish entailment.

## Path to the independent gate

1. Keep every tuning repository and change family on the exposure ledger.
2. Obtain two blinded reviews and adjudication for development packets; keep
   unknown and insufficient-evidence cases visible.
3. Freeze repository/change-family-disjoint validation and final-test groups,
   pipeline hashes, cutoffs, rubric and denominators before opening final labels.
4. Collect at least 200 independently reviewed real-change cases with explicit
   positive, scoped negative and unknown regions. Never infer negative links from
   absence or complete impact sets from patches.
5. Run the frozen pipeline once. Count invalid/missing predictions as errors and
   report traceability, impact, consistency and semantic support separately.

The existing 32-case change pilot remains unlabelled development material. The
91% gate stays `NOT_EVALUATED` until the independent freeze and test are real.
