# Primary-source reference verification

Checked 2026-10-07 UTC. This is a targeted source collection for the forthcoming
drafts, not a systematic review, complete literature search or publication-index
verification. Only the metadata and abstract/model-card scope below were checked;
no claim is made that every full paper was reviewed. External reported scores
will not be pooled with VIGILANT's measurements.

| Key | Verified reference | Primary source | Scope used in drafts |
| --- | --- | --- | --- |
| bm25 | S. Robertson and H. Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*, 2009, DOI 10.1561/1500000019 | https://doi.org/10.1561/1500000019 | Probabilistic retrieval framework and BM25 family |
| rrf | G. V. Cormack, C. L. A. Clarke and S. Buettcher, *Reciprocal rank fusion outperforms condorcet and individual rank learning methods*, SIGIR 2009, pp. 758–759, DOI 10.1145/1571941.1572114 | https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/ | Rank fusion background |
| sbert | N. Reimers and I. Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*, EMNLP-IJCNLP 2019, pp. 3982–3992, DOI 10.18653/v1/D19-1410 | https://aclanthology.org/D19-1410/ | Sentence embeddings and cosine comparison |
| rag | P. Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, arXiv:2005.11401, 2020; viewed revision v4, 2021 | https://arxiv.org/abs/2005.11401 | Retrieval-supported generation background; not a traceability benchmark |
| lissa | D. Fuchß, T. Hey, J. Keim, H. Liu, N. Ewald, T. Thirolf and A. Koziolek, *LiSSA: Toward Generic Traceability Link Recovery Through Retrieval-Augmented Generation*, ICSE 2025, pp. 1396–1408, DOI 10.1109/ICSE55347.2025.00186 | https://ardoco.de/c/icse25 | RAG-based traceability across artifact types; our code is not a replication of its method |
| transarc | J. Keim, S. Corallo, D. Fuchß, T. Hey, T. Telge and A. Koziolek, *Recovering Trace Links Between Software Documentation And Code*, ICSE 2024, article 215, DOI 10.1145/3597503.3639130 | https://ardoco.de/c/icse24 | Architecture models as intermediate artifacts for transitive linking |
| consistency | J. Keim, S. Corallo, D. Fuchß and A. Koziolek, *Detecting Inconsistencies in Software Architecture Documentation Using Traceability Link Recovery*, ICSA 2023, pp. 141–152, DOI 10.1109/ICSA56044.2023.00021 | https://ardoco.de/c/icsa23 | Documentation/model inconsistency through trace links; different labels from Git-change scenarios |
| graphrag | D. Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, arXiv:2404.16130, 2024; viewed v2, 2025 | https://arxiv.org/abs/2404.16130 | Entity graphs and community summaries for corpus-level questions; different from VIGILANT's parsed structural graph |
| sweagent | J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan and O. Press, *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*, arXiv:2405.15793, 2024; viewed v3 | https://arxiv.org/abs/2405.15793 | Interactive software-engineering agents; VIGILANT's bounded workflow is not a SWE-bench evaluation |
| minilm | Sentence Transformers, *all-MiniLM-L6-v2 model card* | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | Model identity; actual experimental revision is pinned in data/models.json |
| qwen | Qwen, *Qwen2.5-1.5B-Instruct model card* | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | Model identity; actual experimental revision is pinned in data/models.json |

## Search and access notes

Targeted searches used the paper titles, LiSSA traceability/RAG, ARDoCo
documentation-to-code, reciprocal rank fusion, Sentence-BERT and BM25. Primary
author/project pages, ACL Anthology, author-submitted arXiv records, model
publisher cards and the DOI publisher landing page were then opened. Discovery
results from aggregators were not used as technical evidence.

The original nowpublishers BM25 URL returned 403. Its DOI redirected to an
accessible publisher page with title, authors, abstract and year. Volume/page
metadata differed from some secondary listings, so the draft reference should
use the verified title/authors/year/DOI without relying on disputed pagination.
The old vector-space-model publisher page also returned 403; it is not included
as a verified source in this collection. A source being inaccessible does not
mean the cited work is invalid.

No author performance claim in this table is a reproduced VIGILANT result.
VIGILANT's comparisons use its own fixed populations and metric definitions.
Further full-text review and broader traceability literature coverage remain
necessary before representing a survey as comprehensive or submission-ready.
