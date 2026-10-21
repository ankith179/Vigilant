# Submission drafts

The ready-to-read outputs are in `submission/output/`:

- `Thesis-Draft.pdf`: 27-page technical thesis draft.
- `Research-Paper-Draft.pdf`: four-page IEEE research draft.
- `Survey-Paper-Draft.pdf`: four-page targeted literature review draft.
- `VIGILANT-Demonstration.pptx`: 14 editable demonstration slides.

These are review drafts. They retain mixed and negative results. Author,
supervisor, institutional formatting, independent semantic/scientific review,
plagiarism review and publication requirements are not complete. The targeted
survey does not claim systematic or comprehensive full-text coverage.

## Manuscript reproduction

From the VIGILANT project root, with Python, Pandoc and a LaTeX installation
providing `pdflatex`, `booktabs`, `balance` and standard fonts:

```
python scripts/build_thesis.py
python scripts/build_papers.py research
python scripts/build_papers.py survey
```

The repository supplies `IEEEtran.cls`. Builders read the editable templates
under `submission/`, validate result-source hashes and populate measured tables
from `reports/results/summary.json`. They do not make model calls. Source hashes,
build logs and visual-review records are under `reports/submission/`.

## Presentation source

`scripts/build_demo_deck.mjs` uses the supplied artifact-tool runtime. It requires
absolute `VIGILANT_PROJECT_ROOT` and `VIGILANT_DECK_WORK` paths and the runtime's
`RUNTIME_NODE`, `RUNTIME_NODE_MODULES`, `RUNTIME_BIN_DIR` and `RUNTIME_PYTHON`
variables. Copy the builder into a fresh private build directory with a
`node_modules` link to the bundled runtime. The finalizer writes a new output,
checks native chart data and renders each final slide. A separate visual review
is required after edits. This builder is runtime-specific, not an ordinary
dependency of the VIGILANT application.

The PPTX itself is editable without rerunning the builder. Charts use measured
values rounded to four decimal places, with embedded workbook snapshots. Full
precision remains in the experiment records. Notes identify each source. The
graph excerpt in `reports/submission/demo-evidence.json` comes from the saved
database, and the preview PNGs correspond to the reviewed final deck. Native
PowerPoint execution was not available for validation.
