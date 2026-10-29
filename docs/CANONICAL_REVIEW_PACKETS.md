# Canonical-ID development review packets

Use `reports/canonical-review-20261024/packets`. All 32 original development pilot
cases are retained under the same case IDs. Canonical repository, parser and
base/head commit identities come from the separate offline source store. Original
packets, forms, databases, graph records and labels remain unchanged.

Each packet supplies the original patch and changed-file paths, plus a canonical
source candidate for each changed file on each side. Available candidates include
a source reference, content hash, bounded excerpt and relative artifact API path.
Excerpts are at most the first 40 lines, not a semantic relevance ranking. Inspect
the full stored source before judging. Candidate artifact IDs are navigation aids,
not positive trace links or complete impact gold. All search dispositions stay UNKNOWN.

The actual 140 changed-file side entries comprise 44 available source references,
92 missing local blobs and four paths absent from the pinned tree. The 92 entries
refer to 79 distinct missing blob IDs; `SOURCE_RECOVERY_QUEUE.json` retains every
case/side/path/commit/origin for separate recovery. No fetch was attempted here.
Absence at a pinned path does not establish that a file was newly added or renamed.
The existing 22-Java-path TEBench diagnosis is separate and was not repeated.

Two blank reviewer forms, a canonical-ID adjudication template and the existing
schemas accompany the packets. Reviewer identities, independent-author attestations,
consistency/trace/impact judgments and rationales remain null. Blank templates fail
scored review intake intentionally. Complete actual independent reviews, source
evidence and adjudication before calling the existing intake tools. Do not fill
labels from the patch, source availability, model output or another reviewer.

## Reproduce without replacing reviewer work

Run from the project root, choosing an unused output directory:

```powershell
python scripts/prepare_canonical_review_packets.py --output NEW_REVIEW_DIRECTORY
```

The builder reads the immutable review snapshot through read-only SQLite, checks
its checksum against staging, verifies canonical scope and refuses existing output
directories, mismatched revisions or judgment-contaminated templates. It does not
execute repository code, contact a model or send messages. It does not authenticate
human reviewers or establish semantic entailment. Use the separate writable source
store described in PILOT_REVIEW_STORE.md for API navigation.

These previously exposed pilot projects are development material. They are not an
independent final set, and current incomplete packets are not review-complete.
Both independent 91% and the newer 95% target remain NOT_EVALUATED. Next local work:
verify existing worktree/cache candidates against the 79 exact missing Git object
IDs, retaining all mismatches/gaps in a separate recovery record. Actual independent
reviews, semantic adjudication and a disjoint final-test freeze remain external.
