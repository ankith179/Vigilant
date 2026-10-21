# VIGILANT research manuscript — 14 October 2026

This is the requested five-page IEEE conference research manuscript by Ankith Singh. It reports existing implementation and frozen measurements. It is ready for technical review and final author verification; it has not been submitted or certified by PDF eXpress or a similarity service.

## Files

- `paper.tex`: complete editable manuscript, including numbered references.
- `VIGILANT-Research-Paper.pdf`: compiled five-page paper.
- `IEEEtran.cls`: unmodified official IEEEtran 1.8b class, obtained from CTAN.
- `figures/`: vector PDF/SVG figures and 600 dpi PNG versions.
- `build_figures.py`: editable Python source for both figures and the measured table.
- `data/`: frozen results, comparison CSV, provenance, and exact model/dataset pins.
- `VERIFICATION.md` and `verification.json`: checks and remaining author actions.
- `SOURCE-VERIFICATION.md`: authoritative bibliographic and formatting sources.

## Compile the manuscript

Install a current TeX distribution with XeLaTeX, fontspec, IEEEtran dependencies, amsmath, graphicx, booktabs, cite, url, balance, and hyperref. Install a licensed copy of **Times New Roman**, visible to your system font manager. Proprietary font files are not redistributed here. Compilation intentionally requires this font rather than silently changing the requested body typeface.

From this directory run:

```sh
xelatex -interaction=nonstopmode -halt-on-error paper.tex
xelatex -interaction=nonstopmode -halt-on-error paper.tex
```

The result is `paper.pdf`. The delivered PDF uses Times New Roman for prose, with embedded math and monospaced fonts for the respective notation. IEEEtran controls paper size, margins, columns, title, captions, and bibliography sizes; no geometry or margin overrides are used. The source may emit initial legacy font-shape warnings and a small-caps fallback warning with XeLaTeX; final embedded fonts and rendered pages were inspected. Body text remains 10 pt. Adding affiliation or other author details may change pagination and requires a fresh check.

## Rebuild the figures and table

Install Python 3 with matplotlib and make Times New Roman visible to matplotlib, then run:

```sh
python3 build_figures.py
```

The script uses the project's frozen result summary when run inside VIGILANT; otherwise it uses the bundled `data/results.json`. It updates figures, the CSV, and the marked results rows in `paper.tex`. It performs **no model inference**. Build the PDF again after edits.

The bundled summaries are sufficient to regenerate the paper's tables and figure. Full raw outputs, query rankings, code, dataset snapshots, and existing audit scripts are in the accompanying complete `VIGILANT-project.zip`. No LLM weights or virtual environments are included; pinned model identities are recorded in `data/models.json`.

## Interpretation

Measured LLM: Qwen2.5-1.5B-Instruct. OmniRoute is an implemented extension with no live evaluation in these results. The architecture is a prescribed, bounded agent workflow. Structural links and graph impact candidates are not independently validated semantic relationships. RAG results are mixed; all 60 consistency calls remain uncertain. The report distinguishes quote/schema checks from correctness.
