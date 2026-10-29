# Execution checkpoint - 25 October 2026, 17:30 UTC

Project status: IN_PROGRESS. This update supersedes the earlier note about the browser source-scope rejection. The rejection came from archived Git worktree .git pointer files that referenced unavailable Linux paths. The isolated test runner now resolves those pointers to matching packaged shared repositories in its disposable database copy. Project source and persisted data were not changed.

## Verified this milestone

- Browser acceptance: PASSED, Chromium 156.0.8078.47, 13 persisted-data pages, no page errors. Report: reports/frontend/2026-10-25T17-29-16-513Z/validation.json.
- Paired lineage UI/API: PASSED for repository fcbdf418593a45ccfd9e391227aa8b9b53b2591447e0a001d1876eb3baabdef1, base 1762adac607a1b29cfc4da129557780beea71616, head 892a3d5213e950be40467f4a0c8cfb33d12e8132, path backend/app/api/routes/items.py. Two canonical source receipts were verified, one per revision. Six candidate pairs and 10 unknown observations were retained; no relationship transfer occurred. The displayed observation states remained UNREVIEWED, UNKNOWN, and NOT_ESTABLISHED. Retained-result replay succeeded; changing the selected path cleared the result.
- The browser report contains source receipt metadata and a paired-lineage screenshot, but no source excerpts. The server used a disposable copy of the database, enabled the opt-in lineage tool only for this test, and made no model calls.
- Focused tests tests/test_lineage_tools.py and tests/test_investigation_tools.py: 20 passed; test_actual_mcp_subprocess_discovery failed once at its 20-second timeout. An isolated retry of that exact test passed in 16.43 seconds. Do not describe the combined run as fully passing.
- V015 bounded job-control tests: `rtk .venv\Scripts\python.exe -m pytest tests/test_job_controls.py -q --basetemp tmp\pytest-job-controls` passed 8 tests in 14.68 seconds. Covered queued cancellation, safe stage-boundary cancellation, deadline expiry including queued work, restart without replay, authentication/validation, partial-run preservation, and publication-versus-cancellation ordering.
- V015 limitation confirmed by code and tests: operation cancellation remains cooperative at stage boundaries. A hung in-flight operation cannot be force-preempted, and process-isolated workers with atomic publication are not implemented or verified. Keep V015 IN_PROGRESS.
- Frontend production build: PASS in the previous milestone (Vite 6.4.5); production frontend files were not changed during this milestone.
- Historical supplied release evidence reports 368 passing tests; the full suite was not rerun. The ZIP has no .git metadata, so a source branch or commit cannot be established from this checkout.

## Work recorded

- scripts/test_frontend.cjs: exercises actual paired lineage response, both source receipts, conservative status, retained replay, and scope-change invalidation; saves compact metadata and paired-lineage.png.
- scripts/run_frontend_check.py: resolves archived Git worktree pointers to local shared repositories only in the disposable validation database; enables opt-in lineage only for that test server.
- frontend/src/InvestigationTools.jsx, frontend/src/main.jsx, and frontend/src/style.css: prior milestone UI implementation and evidence rendering fix.
- docs/VIGILANT_MASTER_TASK_REGISTER.md, docs/VIGILANT_INTEGRATION_GAP_MATRIX.md, reports/execution/latest-status.json, and this checkpoint/resume prompt record current status.

## Task register

V001 VERIFIED; V002 IN_PROGRESS; V003 IN_PROGRESS; V004 IMPLEMENTED; V005 IN_PROGRESS; V006 IN_PROGRESS; V007 IMPLEMENTED; V008 IN_PROGRESS; V009 IMPLEMENTED; V010 IN_PROGRESS; V011 IN_PROGRESS; V012 IN_PROGRESS; V013 IMPLEMENTED; V014 IMPLEMENTED; V015 IN_PROGRESS; V016 IN_PROGRESS; V017 IMPLEMENTED; V018 IMPLEMENTED; V019 IMPLEMENTED; V020 IMPLEMENTED; V021 IMPLEMENTED; V022 VERIFIED; V023 IN_PROGRESS; V024 IMPLEMENTED; V025 IMPLEMENTED; V026 IN_PROGRESS; V027 NOT_STARTED; V028 BLOCKED; V029 BLOCKED; V030 IN_PROGRESS; V031 IN_PROGRESS; V032 BLOCKED; V033 BLOCKED; V034 IN_PROGRESS; V035 VERIFIED.

V008 remains IN_PROGRESS: paired-source and retained-result browser acceptance now pass, but independent logical-identity review and broader cross-revision lineage quality remain outstanding. V023 remains IN_PROGRESS: this browser run exercises saved UI flows, but a complete accessibility audit and native Windows acceptance have not been recorded.

## 95% quality target and release status

95% assurance remains NOT_EVALUATED. Independent judgments supplied: 0. Protocol: DRAFT_NOT_FROZEN. Independent, dependent, and end-to-end evaluation scores remain NOT_EVALUATED. Historical development retrieval Recall@10 of 85.11% on 314 TEBench cases is not overall accuracy and was not rerun. Security, performance, REA runtime parity, native Windows/Docker acceptance, and external review remain open. Release readiness: NOT MET. No labels were altered, no model inference or final-holdout exposure occurred, and no external submission or communication was made.

## Source hashes

- frontend/src/InvestigationTools.jsx: e6c1eede617fb44991e2685dfbc1ed824630ab179b77645d56bf33ed030af765
- frontend/src/main.jsx: 920626d285f3f83f34ba272db6811af20096f103b392f480710c45be14f30213
- frontend/src/style.css: f85421ea1e86420cd4ed52c66ba0a5da25bbc1fab25b5bbd5c842800d2525d8f
- scripts/test_frontend.cjs: 6b5f65ec4d24549fa28e062029348289329b6f102c9e5ea06bff68d593f47ff3
- scripts/run_frontend_check.py: 4bdbed2b874e6f650d926a1b40817722696ee0e57f85396fbe263b874a305299

## Next exact action

Continue V015 with a process-isolation and atomic-publication design for hard in-flight cancellation; inspect persistence side effects before modifying the worker model, then add bounded worker-termination and restart tests. Keep the known MCP timeout in test evidence and V008 open for independent logical-identity review. Do not claim the 95% target or release readiness without untouched, independently reviewed evidence.
