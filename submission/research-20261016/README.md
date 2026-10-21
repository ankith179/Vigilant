# VIGILANT revised research paper

Completed 16 October 2026. Author: Ankith Singh. The exact requested title is retained. This revision addresses the supplied review while preserving the measured mixed retrieval and negative consistency results.

## Deliverables

- `VIGILANT-Research-Paper.docx`: editable Word text, tables and native Office Math equations; 600 dpi figure images.
- `VIGILANT-Research-Paper.pdf`: five-page IEEEtran PDF with vector figures.
- `paper.tex`: canonical manuscript with 14 numbered references.
- `REVIEW-RESPONSE.md`: actions against every concern and unresolved empirical/external work.
- `SUPPLEMENTARY-ANALYSIS.md`: intervals, confusion matrices, class metrics and saved rules-only diagnostic.
- `CONTROLLED-EVALUATION-PROTOCOL.md`: concrete follow-up design, explicitly not executed.
- `data/`: CSVs, pins, original result records, input mirror and hashes, and blank independent annotation worksheet.
- `figures/`: editable SVG, vector PDF and 600 dpi PNG copies.
- `VERIFICATION.md`, `verification.json`: actual local checks and limitations.

## Reproduce the numerical analysis

Use Python 3 with NumPy, from this directory:

```sh
python reanalyse.py
```

This uses the full project when available, otherwise the included `data/reanalysis-inputs` mirror. No model weights, API account, network or inference are required. It recomputes 20,000 paired-query bootstrap samples per dataset using seeds 20261015–20261018, confusion matrices, class metrics, raw-output diagnostics and saved rule finding sets. The original measurements remain unchanged.

## Build documents

Install Matplotlib and a licensed Times New Roman font to regenerate figures:

```sh
python build_figures.py
```

Install XeLaTeX and the packages declared in `paper.tex`, then compile twice:

```sh
xelatex -interaction=nonstopmode -halt-on-error paper.tex
xelatex -interaction=nonstopmode -halt-on-error paper.tex
```

The output is `paper.pdf`; the delivery copy is `VIGILANT-Research-Paper.pdf`. IEEEtran controls page geometry. Proprietary fonts are not redistributed.

Install Pandoc and python-docx to build Word:

```sh
python build_word.py
```

The converter reads the same LaTeX, preserves editable text/tables and native equations, and applies IEEE Word-template styles and geometry. Word pagination depends on fonts and application version; recheck after editing. Both final outputs were rendered and inspected locally. For automated validation, use Python with PyMuPDF, python-docx and NumPy, plus `pdffonts`, then `python verify_paper.py`. Optional `--word-render PATH` checks a PDF rendered from the DOCX; `--baseline-zip PATH` compares historical experiment files with an earlier full package.

## Template provenance

The official IEEE conference template link is published at https://cai.ieee.org/2025/manuscript-templates-for-conference-proceedings/ and points to https://www.ieee.org/content/dam/ieee-org/ieee/web/org/conferences/conference-template-letter.docx . That endpoint did not provide usable bytes in the environment. The template was obtained from the University of Virginia Data Science teaching mirror: https://raw.githubusercontent.com/UVADS/ds6013/main/conference-template-letter.docx . Original bytes are retained as `IEEE-Word-Template-original.docx`; `IEEE-Word-Template.docx` is its LibreOffice-normalized OOXML copy used by the builder.

The template supplies US Letter margins, two-column body geometry and style conventions. Author placeholders are replaced with the supplied author. Body paragraph whitespace is condensed while preserving 10 pt prose and template margins. The PDF separately uses unmodified IEEEtran 1.8b. Word and PDF pagination and equation typography may differ.

## Limits

All measured LLM outputs come from the pinned local Qwen2.5-1.5B-Instruct model. Live OmniRoute accuracy remains NOT RUN. Every raw consistency output abstains with zero confidence. Conditional query-bootstrap intervals do not establish cross-project superiority. Independent annotation, the proposed controlled comparison, no-link detection evaluation, external similarity checks and PDF eXpress remain pending.
