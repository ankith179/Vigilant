# GitHub source import repair — 4 November 2026

Base: `f699de8388c2213e7b0b55b384aa63d83cd500ba`.

GitHub returned no pull requests or issues (all states). Only `main` was listed.
The three October 29 Verify local core runs (40819018945, 40819716005,
40820153915) all stopped with 16 collection errors: `ModuleNotFoundError:
No module named 'investigation'`. Frontend installation/build and both saved-result
audits were skipped. The October 22 run 39753736780 succeeded on the earlier tree.

The tracked package manifest already lists eight `investigation/*.py` files,
but the tracked source tree contains none of them. Restored all eight from
the local continuation folder named in RESUME.md. Each source file's raw-byte
SHA-256 exactly matches its existing PACKAGE-MANIFEST.json entry. No source
logic was changed. Added `investigation*` to setuptools package discovery.

Validation on native Windows with the existing Python 3.12.14 environment:

- All 544 tests collect successfully, with one existing dependency warning.
- API (`backend.app`) and MCP (`investigation.mcp`) imports pass with an in-memory DB.
- Setuptools package discovery includes `investigation`.
- Focused execution: 77 passed, one dependency warning, in 191.88 seconds.
  Modules: staged_source_reader, staged_inspection, staged_comparison,
  staged_graph, staged_report, frontend_api, partial_delivery,
  partial_report_api and canonical_review_packets (all under tests/test_*.py).
- MCP subprocess discovery: one passed, one dependency warning, in 15.51 seconds.

An initial execution attempt encountered WinError 5 in the default pytest temp
directory. A sandbox retry also encountered WinError 5 creating a hard link.
The successful focused retry used elevated execution, workspace-local TEMP/TMP
and a fresh workspace-local `--basetemp`; no protection was removed from code.
Full-suite execution, Linux CI, frontend build and saved-result audits have not
been validated by this local pass. No historical inference was repeated.

Separate packaging limitation: wheel metadata generation fails because dynamic
dependencies read requirements.txt, whose `-r requirements-core.txt` directive
is pip syntax rather than a PEP 508 requirement. This predates this repair and
is not the cause of the GitHub pytest collection failure. Dependency policy
should be resolved separately before claiming an installable wheel.

The V049 saved report records 11/12 authored development-label agreement; it
does not establish independent accuracy, 95% acceptance, or LLM/RAG uplift.
The D-ID status report records 33/36 accuracy as NOT_MEASURED. Restoring source
does not change these scientific claims.

Review priority: verify restored-source provenance, run Linux CI, then assess
remaining failures on their evidence. Do not suppress imports or skip tests
to obtain a green check. Independent labels and adjudication remain external.
