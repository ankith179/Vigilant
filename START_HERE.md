# New investigation tools and 95% evaluation

Extract into a new folder and preserve your current Windows database. Follow the setup below, then open Investigation Tools for source-verified snapshot tools and retained unknowns. Read docs/CLI_REFERENCE.md, docs/MCP_REFERENCE.md and docs/EVALUATION_PROTOCOL.md. The new target is 95%, not an achieved accuracy. Current measurement and test evidence are under reports/final-95/.

# Updated release — 23 October 2026

Extract into a separate empty folder first. Keep your existing Windows working directory, live databases and local model weights intact. This package preserves historical snapshots; it must not replace a newer live database. The updated pipeline and chat instructions are in `docs/EVIDENCE_FIRST.md`. The 91% correctness target remains NOT_EVALUATED; see `docs/QUALITY_TARGET.md`.

The earlier Windows execution results below are historical evidence, not a new Windows run for this release. In a fresh extraction use `Setup-Windows.ps1`, then `Start-VIGILANT.ps1` for evidence-only operation. Add local Ollama separately when needed.

---

# Open VIGILANT

Native Windows continuation, 21 October 2026: continue in this extracted folder.
Setup, software tests and browser acceptance have now been exercised on this PC.
See `reports/windows-20261021/VERIFICATION.md` for evidence and model results.
If the services are already running, open http://127.0.0.1:8000. After a reboot,
run `Start-Ollama-Local.ps1` in one terminal, then `Start-VIGILANT-Local.ps1` in
another. See `docs/LOCAL_MODELS_32GB.md` for the exact evaluation resume command.
The earlier installation/release notes below are retained for provenance.

This package contains the implemented research system, source code, built frontend,
knowledge graph snapshots, datasets and repository history, raw experiment outputs,
measured tables/figures, thesis and paper drafts, and demonstration slides.

## Windows

1. Extract this ZIP. Move the contents of its `VIGILANT` folder into
   `C:\Users\Ankith\Downloads\Code- Vigilant` (use an empty folder).
2. Install Python 3.12, Git for Windows and Node.js with npm if absent.
3. Open PowerShell in that folder and run:

```powershell
.\Setup-Windows.ps1
.\Start-VIGILANT.ps1
```

4. Open http://127.0.0.1:8000 in your browser.

The setup uses the included datasets, saved results and built project. Model weights
are intentionally downloaded separately: run `Setup-Windows.ps1 -DownloadModels`
when you want fresh embedding or local-model inference. Existing results and
deterministic investigations can be inspected without downloading model weights.
Internet access is needed to install dependencies. Windows execution still requires
verification on your computer; this package has been exercised on hosted Linux.

## Demonstrate the pipeline

Select the `08-api-changed` repository and snapshot beginning `892a3d521`.
Inspect Change Analysis, Knowledge Graph, Evidence, Agent Investigation and Reports.
To run a new deterministic investigation, select base revision
`1762adac6` and the reasoning provider `Deterministic tools only`.
See `docs/DEMO_RECORD.md` for the exact saved evidence and interpretation.

## Check the installation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\Test-Frontend.ps1 -InstallBrowser
```

Browser acceptance starts its own temporary server and runs on a disposable copy
of the saved database. It does not alter the experimental results.

## Read the deliverables

- `docs/COMPLETION_CHECKLIST.md`: completed work and external requirements.
- `docs/FINAL_STATUS.md`: measured results and limitations.
- `reports/results/RESULTS.md`: tables derived from saved outputs.
- `submission/output/Thesis-Draft.pdf`: technical thesis draft.
- `submission/output/Research-Paper-Draft.pdf`: research paper draft.
- `submission/output/Survey-Paper-Draft.pdf`: targeted survey draft.
- `submission/output/VIGILANT-Demonstration.pptx`: editable 14-slide deck.
- `RESUME.md` and `PROJECT_STATE.json`: continuation record; completed experiments
  must not be rerun merely to resume work.

The measured effects are mixed. The local consistency model did not outperform
the always-UNCERTAIN baseline. Author/institution details, independent scientific
review, final formatting and university/publication submission remain external.

## Free OmniRoute option — 2026-10-13

See `docs/OMNIROUTE_FREE.md`. Start the gateway with `Start-OmniRoute.ps1`, connect an eligible free provider, then use `Start-VIGILANT-OmniRoute.ps1 -Model` with the exact gateway route. Select OmniRoute in the dashboard. The adapter is tested; live inference and accuracy evaluation require the connected free account and have not run.

## Updated code release — 16 October 2026

Start with `docs/RUN_AND_CODE_GUIDE.md` for both operating systems, free OmniRoute,
local-model options, module/agent/RAG/KG explanation, API use and troubleshooting.
`docs/ARCHITECTURE_COVERAGE.md` maps each part of the supplied architecture to code
and explicitly lists absent or untested services. Release evidence is in
`reports/codebase-20261016/VERIFICATION.md`. Default setup now installs only core
dependencies; local weights remain optional. Latest Word/PDF research paper:
`submission/research-20261016/`.

## New: 32 GB local model comparison

Follow `docs/LOCAL_MODELS_32GB.md`. After setup and starting Ollama, run `Run-Local-Models.ps1 -DownloadModels`, then `Start-VIGILANT-Local.ps1`. New model accuracy remains unmeasured. Generic Graphify files are in `handoff/graphify/`; direct Graphify integration was unavailable.
