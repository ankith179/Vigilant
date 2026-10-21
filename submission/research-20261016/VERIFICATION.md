# VIGILANT review revision — verification report

Completed 16 October 2026. Status: **local document and saved-result checks passed; independent empirical and external submission checks remain open**.

| Check | Actual result |
|---|---|
| PDF length | 5 pages, including title, figures, tables and references |
| Word rendering | 5 pages using LibreOffice through the document renderer |
| Page size | US Letter, 612 × 792 points in both rendered outputs |
| PDF template | Official unmodified IEEEtran 1.8b conference class; two columns; no manual margin overrides |
| Word template | IEEE conference Word template from UVA teaching mirror; normalized OOXML, template margins and two-column body; provenance in README |
| Body type | Times New Roman, 10 TeX pt in PDF (9.96 PDF pt), 10 pt in Word; math uses appropriate notation fonts |
| PDF embedding | Every font embedded; no missing-font substitution in prose |
| Abstract | 179 whitespace-delimited words in LaTeX source |
| Structure | Eight sections, exact requested title, Ankith Singh as sole supplied author |
| Figures and tables | Two vector PDF figures; Word embeds 600 dpi PNGs; two logical tables, three editable Word table blocks |
| Equations | Two native Office Math display blocks in Word |
| Citations | 14 numbered references in first-citation order; no unresolved LaTeX references |
| Visual checks | All five final PDF pages and all five final Word-rendered pages inspected; no clipped figures/equations, overlapping text or missing reference numbers |
| LaTeX build | No overfull boxes or undefined citations/references |
| Frozen results | 23 method rows, 251 linked queries; source provenance hashes match |
| Additional analysis | Paired bootstrap, per-class metrics and raw-response diagnosis reproduced from saved inputs |
| Standalone reproduction | Exact JSON equality using only the packaged input mirror, without project dependencies or inference |
| Input integrity | All 36 mirrored input hashes verified |
| Historical preservation | All 418 original experiment files match the previously saved full-project archive byte for byte |
| New inference | Zero calls |

The IEEEtran class SHA-256 is `da751920a317ed318b7b5cd7fa585a6cc7d28502d457856382e9be24b10a3bd7`. Final document hashes, font inventory and numerical check results appear in `verification.json`.

## Interpretation retained

The reranker raises MAP slightly on SMOS and eTour and reduces it on iTrust and RTMX. Only SMOS's interval excludes zero under conditional query resampling; there is no claim of cross-project or model superiority. All 60 raw consistency outputs already select UNCERTAIN with zero confidence, with five additional citation failures. Every configuration has macro-F1 0.10 and zero non-uncertain coverage. Quote validity is not semantic accuracy. The authored rule findings are not independent ground truth.

## Explicitly unverified

- Independently adjudicated semantic/consistency labels and no-link negatives: NOT RUN.
- New controlled consistency comparison and prompt-causality experiment: NOT RUN; protocol supplied.
- Longitudinal assurance, live OmniRoute accuracy and revised model superiority: NOT ESTABLISHED.
- Native Microsoft Word rendering: NOT RUN. DOCX fonts are referenced, not embedded; pagination can change with fonts/application version. Recheck after edits.
- Similarity checks through Turnitin/iThenticate/CrossCheck: NOT RUN.
- IEEE PDF eXpress and venue-specific camera-ready certification: NOT RUN.
- Affiliation, email, coauthors and acknowledgments were not supplied and are not invented.
- Submission, copyright transfer, acceptance or indexing verification: NOT PERFORMED.

XeLaTeX reports legacy IEEEtran font-initialization/small-caps fallback warnings; the actual final prose font, embedding, page geometry and layout were checked. Licensed Times New Roman font files are not redistributed. The Word template retains its documented margins; paragraph whitespace was condensed while keeping 10 pt body text. Local validation is not a substitute for independent scientific review or venue checks.
