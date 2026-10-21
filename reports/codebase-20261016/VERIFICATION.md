# VIGILANT updated codebase verification

Date: 16 October 2026. Scope: the complete local research application and supplied
source/data/documentation package. This is not a certification of every possible
input, production security or model accuracy.

## Changes in this release

- Bounded one-worker queue with persisted requests and pinned Git commits. Recovery
  resumes unstarted work and marks interrupted running jobs failed, avoiding silent
  replay of a potentially completed inference call.
- Snapshot restore uses SQLite backup and modifies only the working database.
  Frozen snapshot bytes and pre-existing user records are preserved.
- Optional shared-workspace Bearer token across data APIs and the dashboard.
- Free-only default rejects cloud/Gemini/Claude in API and CLI provider selection;
  OmniRoute's explicit eligible-route configuration remains required.
- Scoped impact pagination no longer depends on the first 30 reports in the UI.
  Repository and snapshot selectors load all pages.
- Verified BM25 evidence API, consistency/evaluation aliases, job metrics and
  complete JSON/findings CSV/printable HTML report exports. HTML is escaped and
  CSV formula-like text is neutralized.
- Core-only setup avoids unnecessary model downloads; full local inference remains
  optional. Native launchers, Docker/Compose and a CI recipe are included.
- Watcher state rejects a different repository and writes atomically.
- Historical RAG provenance audit accepts an explicit exact archived provider
  source; current/altered implementations still fail historical fingerprint checks.
- Run/module guide and image-to-code coverage matrix explain the implemented scope.

## Executed checks

| Check | Result | Evidence |
| --- | --- | --- |
| Original regression suite | 53 passed | `tests-before.log` |
| Updated regression suite | **62 passed** | `tests-after.log`; one upstream AnyIO alias deprecation warning |
| Core requirements install | PASS | `core-install.log`; Python 3.12 test venv with runtime system packages |
| React production build | PASS | `frontend-build.log`; Vite 6.3.5 |
| Browser acceptance | **PASS, 13 pages** | `../frontend/20261016-release/validation.json`; Chromium 138.0.7204.0 on Linux |
| JSON/CSV/HTML downloads and new UI controls | PASS | Same browser record; exact JSON run identity checked |
| Isolated deterministic investigation | PASS | Same browser record and `ui-investigation.json`; no LLM call |
| Graph, evidence, pagination, keyboard access, transport recovery | PASS | Same browser record |
| Mobile dashboard and graph at 390px | PASS | No document overflow; mobile/dashboard and report layout visually inspected |
| Retrieval arithmetic audit | PASS: 23 method rows, 1,484 per-query metric rows | `metrics-audit.json` |
| Saved RAG evidence/protocol audit | PASS: 251 actual generations | `rag-audit.json` |
| Original experiment preservation | PASS: 418 files, zero changes | `preservation.json`, SHA-256 comparison to prior saved full release |
| Linux setup shell syntax | PASS | `bash -n scripts/setup.sh` |

The standard Playwright Chromium download returned a truncated ZIP in this hosted
network. Browser checks used the npm-distributed `@sparticuz/chromium@138.0.2`
binary instead, with Playwright 1.64.0. No mock research data replaced saved records.
One explicitly injected HTTP failure tests UI error recovery only. Browser screenshots
are internal QA and excluded from the delivered archives.

The RAG audit originally rejected current provider code because the later OmniRoute
integration changed its source hash. The archived 7 October provider recovered from
the pre-extension source checkpoint has SHA-256
`e3e52d4be2aa53a726bf3858305724912680bcc41f764f1dbe93cf6966f2421b`.
It is included at `evaluation/frozen/20261007/providers.py.txt`. Passing it explicitly
restores exact provenance verification without changing any saved observation or
weakening the fingerprint assertions. It is audit input, not the current provider.

No new local or remote LLM inference was performed. The browser's new deterministic
run used a disposable database; all original experiment files remain unchanged.

## Portable extraction check

A fresh extraction into a different temporary directory was restored, synchronized
and used to run the documented deterministic CLI example. It completed with 11
changes, 33 impact candidates, 15 rule findings and 25 verified excerpts. All three
frozen SQLite snapshots retained their hashes. See `portable-smoke.json` and
`portable-smoke.log`.

The first attempt exposed a real report-save failure: the hosted PID namespace made
`psutil.Process()` unavailable. The optional memory reading now records null plus
an explicit error type instead of preventing the completed report from being saved.
A regression test covers this. The successful portable run overlaid this final fix
and its test onto the extracted package; recorded runtime-file hashes are checked
against the final archive before delivery. The earlier failure log is retained.

## Not executed / not established

- Native Windows execution and writing to the user's Windows drive.
- Docker build/runtime and remote GitHub Actions execution; supplied as recipes.
- Live OmniRoute gateway/provider calls, free-account billing eligibility, model
  comparison or revised accuracy. Adapter fixtures are synthetic, not live results.
- New local model inference or a clean full ML installation on user hardware.
- Production scale, multiple server processes, PostgreSQL/Neo4j/vector services,
  distributed queues, public authentication/RBAC, webhook or external log stacks.
- Independent labels, semantic entailment, longitudinal validation or superior-model
  accuracy. The saved 60-call consistency model abstains on every case.

See `docs/ARCHITECTURE_COVERAGE.md` for the complete architecture mapping. The current
code is a validated local research system, not a fully implemented production version
of every component in the reference image.

## Reproduction

Run the commands in `docs/RUN_AND_CODE_GUIDE.md` from the project root. The full ZIP
contains raw Git repositories, snapshots and datasets. The source-only ZIP requires
its data companion/full package for the saved demonstration. Large dependencies and
model weights are intentionally excluded. The unified ZIP contains a per-file hash
manifest; its final whole-archive checksum is delivered separately. Packaging performs
ZIP integrity checks; these are integrity checks, not executable security review.
