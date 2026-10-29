# Bounded verification-obligation registry

This offline development intake complements existing review schemas and rules.
It does not discover obligations, authenticate reviewers, execute tests, prove
semantic entailment or establish whole-project coverage. It can now be attached to a separately versioned saved investigation report;
it does not change persisted graph records or run a new investigation. Existing rules keep
the no-obligation/no-MISSING_TEST guard and historical outputs are unchanged.

Use `consistency.obligations.ObligationRegistry` or the exported JSON schema at
`reports/obligations-20261024/registry-schema.json`. Each history has one stable
obligation ID and sequential revisions. Every revision names its prior content
fingerprint and retains lifecycle, criterion, source, satisfaction, review
rationale, search scope and counterevidence. A new revision must be appended
rather than replacing a previous assessment. Fingerprints detect inconsistent
chains, but are not signatures or tamper-proof external audit storage. Retain
prior registry files and output reports as independent versions.

The registry repository and parser identity must match stored source artifacts.
Import into a separate parser identity; never rewrite frozen artifacts to make
the IDs fit. Each referenced artifact version, hash, path and span is validated
against storage and independently reread through pinned Git blobs. Every event
uses its own pinned revision; stale final events produce NOT_ESTABLISHED. A
retirement event needs current source evidence for retirement. Where that evidence
or an applicable artifact no longer exists, leave it unresolved rather than forge
an event. Full commit SHAs are enforced by the Git evidence verifier.

A MISSING_TEST finding requires an ACTIVE TEST obligation reviewed UNMET, a
reviewed obligation inventory and an explicit reviewed-complete search boundary
matching the applicable artifacts. Search evidence and reviewer rationale are
required even if the searched artifact list is empty. The empty list is a review
attestation, never machine proof that no tests exist. Unknown search regions,
missing scope, unknown satisfaction/lifecycle and outstanding counterevidence
prevent a finding. SATISFIED records do not establish global CONSISTENT status.
Only declared source-backed root-cause IDs group findings; all underlying
obligation assessments, evidence and fingerprints remain available. This is
reviewer-attested classification; source authenticity does not validate semantics.

Run from the existing project root with a canonical imported development database
and a real reviewed registry (do not use fixtures as research labels):

```powershell
python scripts/assess_obligations.py --database-url sqlite:///path/to/development.db --registry reviewed-registry.json --commit FULL_HEAD_SHA --output new-obligation-assessment.json
```

Output creation refuses to overwrite an existing report. The CLI always checks
Git source. The Python `check_git=False` switch is for explicitly disclosed
stored-only fixtures, not accepted live intake. All reviews remain attested, not
independently authenticated. No model calls occur. The independent 91% gate
remains NOT_EVALUATED; registry fixtures do not supply independent annotations.

## Attach a registry to a saved investigation

```powershell
python scripts/attach_obligations.py --database-url sqlite:///path/to/development.db --parent-run-id ORIGINAL_RUN_ID --registry reviewed-registry.json
```

The registry must match the investigation repository and separate parser identity.
Pinned Git evidence is reverified for both the original report and registry. A new
immutable report ID incorporates the original report content and registry fingerprints;
repeating the exact attachment reuses that ID. Attach subsequent registry revisions
to the original report. Parent reports, model outputs, graph records and artifacts
are unchanged. The derived report records inherited metrics separately and reports
zero new model calls. Historical model output explicitly excludes the attached review.

The existing report API, JSON/HTML exports and saved-report chat can read the new ID.
Finding CSV exports retain their findings-only contract; use JSON or HTML full records
for every obligation assessment, including blocked/unknown rows and counterevidence.
Derived evidence/findings are embedded in this report, not duplicated into global
finding/evidence tables or the graph. No upload endpoint or registry editing UI is
added. Chat retains NOT_ESTABLISHED for global coverage and discloses review attestations.
Reports without a registry retain the original abstention behavior.

Optional `search_scope.git_inventory` enumerates every Git object under explicit
repository-relative prefixes at the revision's pinned SHA. Each file is SEARCHED,
EXCLUDED or UNKNOWN with a rationale. SEARCHED entries require source-backed
artifact IDs; exclusions and unknowns cannot claim searched IDs. Omitted files,
object mismatches and UNKNOWN entries in a reviewed-complete scope are rejected.
Partial boundaries retain unknowns. Exclusions are reviewer decisions, never
negative traceability labels or proof that excluded files are irrelevant.

Every lifecycle revision's inventory is verified, including superseded revisions.
Stored artifact IDs and commit IDs must exactly match their lookup keys and the
search inventory revision, even if the source text is unchanged. Source authenticity
and exact enumeration still do not prove semantic search completeness. Legacy
registries without inventories remain explicitly NOT_MACHINE_ENUMERATED; their
review attestations are not silently upgraded to machine verification.

Next: exercise this path on real, independently reviewed development registries
and review exclusion rationales/unknown boundaries. Broader production lifecycle,
actual independent review and semantic acceptance remain open.

## Prepare drafts without altering review work

`python scripts/build_search_inventory.py REPOSITORY --commit PINNED_SHA --prefix . --output NEW.json`
creates UNKNOWN-only entries from Git tree identities. It refuses an existing output
or empty boundary. It does not load blob sizes or source text; in partial clones this
avoids one-by-one source downloads. Tree enumeration is not content verification.
Reviewers must provide actual scope decisions, source-backed artifact identities and
obligation judgments before reviewed intake. EXCLUDED entries require real rationale.

`reports/search-drafts-20261024/prepared/index.json` maps all 32 existing development
pilot cases to 53 unique pinned snapshots. All 10,970 entries remain UNKNOWN; no new
labels, canonical artifact IDs, reviewer identities or exclusions were generated.
The original pilot and blind reviewer forms remain unchanged. To reproduce in a fresh
copy, run `python reports/search-drafts-20261024/prepare.py`; it refuses existing outputs.
