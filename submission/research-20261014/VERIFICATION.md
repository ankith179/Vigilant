# VIGILANT research paper — verification report

Prepared 14 October 2026. Status: **ready for technical review and final author verification**.

| Check | Result |
|---|---|
| Total length | **5 pages**, including title, abstract, figures, tables and all references |
| Template | Official, unmodified IEEEtran 1.8b conference class; two columns; no manual margin overrides |
| Page size | US Letter, 612 × 792 PDF points |
| Body type | Times New Roman, 10 TeX pt (9.96 PDF pt); mathematical and code notation use their respective embedded fonts |
| Font embedding | Every final PDF font embedded; no missing-font substitution in the prose |
| Abstract | 183 words |
| Required structure | All eight requested sections present; exact requested title; Ankith Singh as sole supplied author |
| Figures and tables | Two vector figures and two tables; editable figure generator, SVGs, CSV and 600 dpi PNG copies included |
| Numerical evidence | Table and chart derived from frozen records; 23 method rows, 251 linked queries; historical source hashes match |
| Citations | 14 references, all cited, in first-citation order; no unresolved citations or cross-references |
| Layout | All five final pages rendered and visually inspected; no clipped content, overlapping elements or overfull boxes |
| Reproducibility | Full model/dataset pins, aggregate records, audit records, source and build instructions included |
| New experiments | None; zero new inference calls; original result files preserved |

The class hash is `da751920a317ed318b7b5cd7fa585a6cc7d28502d457856382e9be24b10a3bd7`, matching the retrieved official class. Numerical checks and the final PDF SHA-256 appear in `verification.json`.

## Findings retained in the manuscript

RAG slightly improves MAP on SMOS and eTour, but reduces it on iTrust and RTMX. Top-five reranking cannot improve Recall@5 or Recall@10. All 60 consistency calls return uncertain, matching the 25% always-uncertain baseline; five citation failures are retained. Quote verification and valid JSON are not treated as semantic accuracy. The investigation is a prescribed bounded workflow. OmniRoute live inference and revised accuracy remain NOT RUN.

## Remaining actions and risks

- Affiliation, email, coauthors and acknowledgments were not supplied and have not been invented. Add them only as applicable and recheck pagination.
- Independent technical, semantic and annotation review remains outstanding. The paper does not claim statistical significance or general model superiority.
- Turnitin/iThenticate/IEEE CrossCheck similarity checks have **not** been run; conference similarity compliance is unverified.
- IEEE PDF eXpress has **not** been run. Embedded fonts and page geometry were checked locally, which does not replace that service's validation.
- No paper submission, copyright transfer, acceptance claim or camera-ready certification has been made.
- The editable deliverable is complete LaTeX source, as permitted in the request. It is not a Word imitation of the IEEE template. Compiling requires a licensed Times New Roman installation; font files are not redistributed.
- XeLaTeX emits legacy IEEEtran font-initialization and small-caps fallback warnings. The actual final prose font, embedding, text size and layout were verified. IEEEtran layout settings are unchanged.

The uploaded survey's review-year/venue error and the REFSQ task-scope correction are documented in `SOURCE-VERIFICATION.md`.
