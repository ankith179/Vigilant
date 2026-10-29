# Change log

No root Git metadata is present in this project copy. This log records the current V047 pre-implementation checkpoint; source code and historical predictions have not been changed.

## V047 policy review / baseline checkpoint

- Added draft only: `docs/decision_policy.md`
  - SHA-256: `d59721d1bb9ade3302c89f3efa36e360c8f8883035d28aa5bddae3dc0837f28a`
  - Status: awaiting user decisions A-D; no policy-dependent implementation started.
- Added full pre-change test report: `reports/v047-baseline-tests.xml`
  - SHA-256: `756f8719800bfb54b424ba974f24d56c97903e18f508331fe64acd608d2335d6`
  - Command: `rtk run '.venv\\Scripts\\python.exe -B -X utf8 -m pytest -p no:cacheprovider --basetemp=tmp/v047-baseline --junitxml=reports/v047-baseline-tests.xml -q'`
  - Result: 450 passed, 4 failed, 0 errors, 0 skipped; 1 warning; exit code 1.
  - Failures: 3 tests require Windows symlink privilege (WinError 1314); 1 C++ cross-file overload-resolution assertion.
- Frozen historical diagnostic: `reports/llm-diagnostic-error-analysis/case-analysis.json`
  - SHA-256 before and after this checkpoint: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`
  - Historical authored-label result remains 4/12; this is not independent accuracy.

Next: receive and record decisions A-D in `docs/decision_policy.md`; only then continue with schema/rules and tests. After implementation, rerun focused and full validation and append exact file hashes and results here.

Policy decisions recorded 2026-10-28: comment-only/no marker => NO_ASSURANCE_IMPACT; authority hierarchy confirmed; separate test-obligation axis includes approved verification registries/acceptance criteria; 95% primary criterion is observed point estimate on frozen independently adjudicated cohort. V047 implementation resumed.


## V047 completed checkpoint (2026-10-28)

Decision V3, revision-scoped facts/rules, guarded local-only inference, evidence context checks, per-axis evaluator, read-only data audit and case schema/validator are implemented. Baseline suite: 450 passed/4 failed; final focused suite: 36 passed; final full suite: 485 passed/4 failed with the same four baseline failures (three WinError 1314 symlink setup failures and one C++ resolver failure). Inference was BLOCKED and no model call occurred. The original diagnostic SHA-256 remains c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864. See reports/v047/artifact_hash_manifest.json and checkpoint_manifest.json. The project has no root Git metadata.


## V047 code-review follow-up (2026-10-28T07:07:40+00:00)

- Focused verification: 46 passed, 0 failed; JUnit `reports/v047-followup-focused.xml`.
- Full suite: 500 passed, 4 failed, 0 errors, 0 skipped; same known three WinError 1314 symlink setup failures and one C++ overload-resolution failure; JUnit `reports/v047-followup-tests.xml`. Full run preceded final miner path-independent repository-ID tweak; focused miner test passed after it.
- Added Git-verified HEAD deletion receipt metadata, evidence collision disambiguation, supported-citation gate for every decisive LLM result, URL path route comparison, runtime JSON schemas, and local-only silver commit miner.
- Frozen diagnostic unchanged: SHA-256 `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. No inference, new accuracy, or independent evaluation. 95% NOT ESTABLISHED.
- Next exact action: rerun full suite after the final miner-only tweak if required, then proceed with authorized model preflight and independent adjudication preparation.


## V047 accuracy replay check (2026-10-28T07:15:28+00:00)

New V3 accuracy is NOT MEASURED. Offline rules replay was attempted with inference disabled; all 12 case folders lack `.git` metadata, so 0/12 predictions were produced. Historical Qwen3 8B remains 4/12 authored-label agreement, not independent accuracy. V3 uses orthogonal axes and the authored legacy labels are not multi-axis gold. Frozen diagnostic SHA-256 remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. See `reports/v047/ACCURACY_REPLAY_STATUS.md` and `reports/v047/rules-only-diagnostic-replay.json`.


## V047 measurement harness (2026-10-28T07:23:57+00:00)

Added `tools/measure.py` with per-axis strict scoring, repository-cluster bootstrap intervals, per-rule results, paired exact McNemar and cluster-bootstrap differences. Five unit tests pass. Held-out evaluation NOT_RUN; no independently adjudicated multi-axis gold or frozen predictions; accuracy NOT_MEASURED. Frozen diagnostic SHA-256 `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864` unchanged. See `reports/v047/measurement-harness-status.md`.


## V047 measurement and full-suite validation (2026-10-28T07:47:29+00:00)

The frozen historical known-answer evaluator test passes: 4/12, macro-F1 0.325, Wilson approximately 13.8%–60.9%, majority 50%, and the eight saved mismatches. This is arithmetic validation against authored legacy labels only, not V3 quality. Harness tests: 7 passed. Full project suite: 507 passed, 4 failed, 0 errors, 0 skipped; 1 existing Starlette/AnyIO deprecation warning. Failures: three Windows WinError 1314 symlink setup tests and one existing C++ compiler-USR resolver test. JUnit: `reports/v047-full-after-golden.xml`. Held-out evaluation remains NOT RUN; new V3 accuracy NOT MEASURED; 95% NOT ESTABLISHED. Frozen diagnostic SHA-256 remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.


## V047 authored regression replay 006 (2026-10-28)

- Added a revision-aware rule for a modified requirement with a source-provided VALIDATES edge to a test whose BASE and HEAD content hashes are equal. It emits only POTENTIAL_INCONSISTENCY and requires review; it does not claim test failure or semantic non-coverage.
- Matched route handlers across revisions using stable symbols when artifact IDs differ; added stale-consumer comparison only where the literal request resolved at BASE and no longer resolves at HEAD.
- Focused V3 suite: 43 passed. Full suite was interrupted after approximately 15 minutes; two failures had appeared, no final totals or JUnit report were produced. This run is incomplete. Previous complete suite remains 507 passed/4 failed, with three WinError 1314 symlink failures and one C++ overload-resolution failure.
- Frozen snapshot replay 006: 11/12 authored-label agreements (91.67%), target met for this regression set only. No LLM inference. Case 06 remains mismatched: authored MISSING_TEST maps to UNSATISFIED, but the evidence-only policy returns UNVERIFIED because no approved explicit obligation is supplied.
- The 12 cases informed development; this score is not independent accuracy, generalization, or overall system accuracy. Independent adjudication remains zero; 95% research/release acceptance is NOT ESTABLISHED.
- Frozen original case-analysis.json SHA-256 rechecked unchanged: c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864.
- Changed-file SHA-256: agents/decision_rules.py 3fe4086f1375b8d3ff78e826a27a44b729288e50d3ecbefc2ddb4fc015b8b6b2; ingestion/models.py 61244b08aa438fb67e94a1d4751250f3d67d6502c76ec3d04f384e423dc9dc83; tests/test_decision_v3_extraction.py 854292f091365e39491755a382f95a52df2a49e62281811d4934310a87876512.
- Preregistration, runner, predictions, and comparison are under the writable workspace work/contract-continuation/ as v047-authored-regression-preregister-006.json, v047-authored-snapshot-replay-006.py, v047-authored-snapshot-predictions-006.json, and v047-authored-snapshot-comparison-006.json.


## V047 post-006 full-suite completion (2026-10-28)

- The sandboxed post-change full suite hung in Starlette/AnyIO TestClient startup. An isolated reproduction with faulthandler showed asyncio blocked creating the Windows Proactor self-pipe. The same isolated test passed outside the sandbox (1 passed, 1 existing Starlette/AnyIO deprecation warning); no system security settings changed.
- Full suite completed outside the sandbox: 511 passed, 4 failed, 0 errors, 0 skipped, 1 warning in 780.13 seconds; exit code 1. JUnit is in the writable workspace at work/contract-continuation/v047-full-suite-unsandboxed-006.xml.
- Compared with the prior complete baseline (507 passed, 4 failed), the exact same four failure IDs remain: three WinError 1314 symlink setup failures and tests.test_native_languages::test_cpp_compiler_resolves_cross_file_overloads_and_keeps_errors_visible. Four added targeted tests pass; no new failure category.
- Replay 006 remains 11/12 authored-label agreements (91.67%) for the development/regression set; Case 06 is the sole mismatch (UNVERIFIED vs authored MISSING_TEST projected as UNSATISFIED). Independent evaluation and the broader 95% target remain NOT ESTABLISHED.
- Original case-analysis.json hash rechecked unchanged: c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864.

V047 C++ parser follow-up: replaced the empty clang VFS overlay with explicit mappings to temporary copies of supplied snapshot files. This allows repository-local headers to resolve while fallthrough remains disabled; rejects paths outside snapshot-relative form. The existing cross-file overload test and hostile absolute/macro include tests cover the intended and denied paths.

V047 Windows follow-up: made UTF-8 JSON/text reads and writes explicit in dataset preparation and saved RAG-observation auditing, and added a regression test rejecting parent-traversal paths in C++ snapshot inputs. This addresses CP1252 default-codec failures without changing dataset labels or disabling filesystem protections.

V047 maintenance 007 verified: C++ snapshot-header VFS fixed; UTF-8 data reads made explicit; path traversal regression added. Focused suite: 13 passed. Full suite: 513 passed, 3 WinError 1314 symlink-setup failures, 0 errors/skips, 1 warning, 766.12 seconds. Historical case-analysis hash unchanged. See reports/v047/V047_MAINTENANCE_FOLLOWUP-007.md.

## V3 RAG-to-LLM evidence bridge

The workflow now passes retrieval-arm HEAD excerpts into the bounded semantic V3 stage only after exact snapshot/Git verification. The context reserves at most two RAG excerpts, keeps their role/provenance, and the citation guard accepts them only when the caller marked them verified. This is an integration change, not a measured accuracy result.

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `agents/assurance.py` | `9f65cffadf5729b98435e1f27bc9114c97657dfad96b1810ba5a7fcf42ef0018` | `43983a61bba06571985f6ab772647dffa12ff82dc18c40fd63e8b5f6e40e5cc3` |
| `agents/workflow.py` | `de50da662725e22b35942700fb2c8696a286b26b741b64c04b2e402b3b5f688a` | `5a30183ef9483d03bdb76b2343dd378bc97131c3aaaea3caf975aeec3e5c2eec` |
| `llm/context_v3.py` | `814597a0b46d300054ae03b2bd3da94ad8cdd8c479a3a26af4412c5e3d7f18c4` | `8b325c6562a0776907f575b2cb6589e7c568a147b4a57f9833534df72540b3e2` |
| `llm/providers.py` | `f3e9f284f1fcef5df28f87371886b7790e653b56165c29ddc67626557e588686` | `852f015108c9a184907cff610d5ddb2c96707bd208955db60fb018138c364114` |
| `agents/decision_rules.py` | `3fe4086f1375b8d3ff78e826a27a44b729288e50d3ecbefc2ddb4fc015b8b6b2` | `5a377794f9cf3ad5b794133d9d9ddef964f17282b023838bcb84e4dc796bbfb6` |
| `tests/test_decision_v3_context.py` | `a318120b6e6b7eac6f0c4f65135f29556e545df12e6a96a5d469461d7c008046` | `d96da8c229247637c16b53e13cd4cbb13e1bb0cc4f97bf1aaebc10fc9b297f44` |
| `tests/test_v3_rag_bridge.py` | `NEW` | `2657bb89c9cda7088b3ef2dece225bffe0258f105fcca346fe78f0f70073c3c9` |

Fixture correction: import_repository uses `rev`, not `commit`. `tests/test_v3_rag_bridge.py` SHA-256 `2657bb89c9cda7088b3ef2dece225bffe0258f105fcca346fe78f0f70073c3c9` → `6245a7fa7f7bc7be9fb47a1b2b36ddc2032e718096649981bdb364a435031ca9`.

Added workflow RAG forwarding test. `tests/test_v3_rag_bridge.py` SHA-256 `6245a7fa7f7bc7be9fb47a1b2b36ddc2032e718096649981bdb364a435031ca9` → `b71db76099974294e22ca14ad2485918364e917fdd580aea5354297ce7b8526a`.

Corrected workflow bridge assertion to count only retrieval-arm excerpts (the packet includes other evidence too). Test SHA-256 `b71db76099974294e22ca14ad2485918364e917fdd580aea5354297ce7b8526a` → `34262379cbd8a74d3c4e15d82717e37e59c72d7119364886c76aa195e578d8b0`.

Avoided redundant RAG verification when model=none; exact retrieval verification remains required for configured LLM calls.
- `agents/assurance.py` SHA-256 `43983a61bba06571985f6ab772647dffa12ff82dc18c40fd63e8b5f6e40e5cc3` → `d52808ad1a9b7b36948a8ae49324267f04b50802eb9c2b61ac1fd6e510bb3d68`.
- `agents/workflow.py` SHA-256 `5a30183ef9483d03bdb76b2343dd378bc97131c3aaaea3caf975aeec3e5c2eec` → `147f1a6bc6ee8f00d1b6b65fa26252a9be2e2ad5c2999e687439e30a861972cd`.
- `tests/test_v3_rag_bridge.py` SHA-256 `34262379cbd8a74d3c4e15d82717e37e59c72d7119364886c76aa195e578d8b0` → `77a760d93163e0eebbd239e00a327a18beb72123b0aa232bb6ce01be4bab155f`.

Made wrong-revision RAG test enable the LLM path being guarded. Test SHA-256 `77a760d93163e0eebbd239e00a327a18beb72123b0aa232bb6ce01be4bab155f` → `d06a84d2b0da537a170a17ea4d1a12a9756eaacb8ce3ba2570216fb4482481da`.

Evaluation status and RAG bridge documentation updated; targeted legacy encoding repaired in CHANGES.md.
| File | SHA-256 |
|---|---|
| `agents/assurance.py` | `d52808ad1a9b7b36948a8ae49324267f04b50802eb9c2b61ac1fd6e510bb3d68` |
| `agents/workflow.py` | `147f1a6bc6ee8f00d1b6b65fa26252a9be2e2ad5c2999e687439e30a861972cd` |
| `agents/decision_rules.py` | `5a377794f9cf3ad5b794133d9d9ddef964f17282b023838bcb84e4dc796bbfb6` |
| `llm/context_v3.py` | `8b325c6562a0776907f575b2cb6589e7c568a147b4a57f9833534df72540b3e2` |
| `llm/providers.py` | `852f015108c9a184907cff610d5ddb2c96707bd208955db60fb018138c364114` |
| `tests/test_v3_rag_bridge.py` | `d06a84d2b0da537a170a17ea4d1a12a9756eaacb8ce3ba2570216fb4482481da` |
| `tests/test_decision_v3_context.py` | `d96da8c229247637c16b53e13cd4cbb13e1bb0cc4f97bf1aaebc10fc9b297f44` |
| `reports/evaluation_status.md` | `e269848d85cc463bebce49dafb4238ef7d38b3ff0b02e579db863a16f631f929` |
| `reports/experiment_matrix.md` | `74cbabd48b16de446d337121bc874d0e97d679365bdf332e91b9e48e505d1d31` |

Full-suite diagnostic refined with the sandbox local-socket blocker; no tests or labels changed.
| `reports/evaluation_status.md` | `368f83a00c561d5da19dca1735f6b5177c747ed7fc4422638b2fa118bd52c98d` |

Full-suite blocker updated with faulthandler evidence; no socket controls bypassed.
| `reports/evaluation_status.md` | `157cf5bd9741e4636c790f0525ae4b4f93b8a0457b09855238d1d4bc0d397e90` |

Evaluation next action aligned with verified full-suite local-socket blocker.
| `reports/evaluation_status.md` | `8ec11ff1cb48056bb5e3e29f9821668c79f0e0d70750e5b427617debf51d110b` |

## Miner submodule handling (2026-10-28)
Git tree entries now distinguish blobs from gitlinks/other objects. Unsupported objects are emitted as unreviewed candidates with object provenance; they are not treated as missing files. Added a gitlink regression test.
- `tools/mine_cases.py` SHA-256: `43b173a3326a1c1b2dbc84f58b72e48608885a7c6b5d020cf2e4a4abf3abd8a9`
- `tests/test_v047_tools.py` SHA-256: `9db1a0f798de80f4be1ea67594f5211dda1bbe0a55dd8e0e3256093471ae3c7d`

Follow-up: unsupported-object evidence reads now use the typed Git tree entry directly, without retrying it as file bytes. The first regression run caught this remaining call path.
- `tools/mine_cases.py` SHA-256: `193442f30f0ee5b1d7966000536b33da83b4a69edd191dd19423d30815cb53bc`
- `tests/test_v047_tools.py` SHA-256: `9db1a0f798de80f4be1ea67594f5211dda1bbe0a55dd8e0e3256093471ae3c7d`

## V047 candidate mining status (2026-10-28)
Recorded the completed five-commit candidate batch, D-ID coverage (not accuracy), frozen-diagnostic hash check, and the interrupted 30-commit run. The partial run is preserved and excluded from metrics.
- `reports/mining_v047_status.json` SHA-256: `c03a1f40e7a85ac0d262150d46d49e940fe88d4e64e78bd8170d14d5bdac1c8c`
- `reports/mining_v047_status.md` SHA-256: `3e605b94877d8c4463a55df67d8106f2f1257c453e52aa9ce22a3bc932b51f06`
- `reports/evaluation_status.md` SHA-256: `3a190da9262e7e18db5b6f2da2fc041ca5128f81758d8f91e7306345ee64a7aa`

Gitlink regression strengthened to exercise `mine_repository` end-to-end across a pinned commit containing a gitlink.
- `tests/test_v047_tools.py` SHA-256: `76d255d2bee073a5b2951b2d0e3fd788c0afb8a25b1159ab11dabece2f54fde4`
- `reports/mining_v047_status.json` SHA-256: `eb2b5a7da9499e8c9580e8e99841667863afa8e78b69d331ae02cae11d754d1f`

Final V047 gitlink test verification: repository-level mining regression passed with the other focused miner tests (4 passed, 9.10s).
- `tools/mine_cases.py` SHA-256: `193442f30f0ee5b1d7966000536b33da83b4a69edd191dd19423d30815cb53bc`
- `tests/test_v047_tools.py` SHA-256: `76d255d2bee073a5b2951b2d0e3fd788c0afb8a25b1159ab11dabece2f54fde4`
- `reports/mining_v047_status.json` SHA-256: `63e3086ef01e4f3f9cc8b4a14e74b79fbdf2de67d7c3a728c75a173690e1e19d`
- `reports/mining_v047_status.md` SHA-256: `fdc7e1b05c1819744e52e98cc02c69d32534ed5ba14bdbc1795b2b24f9ffd7f9`

Candidate-to-card conversion now binds either BASE/HEAD role names or exact commit SHAs and rejects unbound evidence revisions. Added a positive/negative regression.
- `tools/candidates_to_cards.py` SHA-256: `ca95ce0a8a632f6968da84bb04982a28ea871e060f7f21ca3d69cdaadf9d35f3`
- `tests/test_candidates_to_cards.py` SHA-256: `e6dd6885c0b33f25a6e71017db86c11131c0ede57824fa1a2c8e55d72046d65c`

Blind review sheets now include reviewer ID, UTC timestamp, rationale, uncertainty reason and pending status fields; no judgments are prefilled.
- `tools/blind_review.py` SHA-256: `041533d3706d2be470f049155cce38e0260f8d98b2f1ecbb6a30c88e2774c6ec`
- `tests/test_blind_review.py` SHA-256: `1e097a470f671f05debf89aed98baf35e2b06a17c6995f323177c83209b0f876`

V047 blind development pilot prepared: 24 revision-pinned, unlabeled cards selected from the verified mined pool; two blinded sheets created; no reviewer judgments or accuracy results.
- `data/prepared/v047-dev-pilot-cards-20261028.jsonl` SHA-256: `106db38b08ccd8adcda106ca5dcfd16871e5e7f5d90155338576f9fd7f80a89c`
- `data/prepared/v047-dev-pilot-selection-20261028.json` SHA-256: `8e203450ad4227ea9216b3b6b49525711b29f0f63a0abff1888bd0f79f356105`
- `docs/adjudication_protocol_v047.md` SHA-256: `efe53d846cce71d5f9cd8ea209b0b38567a0448ab4c579513727a02c43cad5ef`
- `docs/reviewer_instructions_v047.md` SHA-256: `ef38af26b50aa3e24a4c0eba76af191e7ca80ddb378fc5c020af93653e6f34ac`
- `reports/v047-dev-pilot-preparation.md` SHA-256: `5120cd2a9d917681eb9867f6fd06bb8f92790ff4732744d41c79653326b58132`
- `data/reviews/v047-dev-pilot-20261028/reviewer-1.csv` SHA-256: `a87095440dc445717a2fb9cfff0b3bcb925231c64a386700087bef07cf9ad9d2`
- `data/reviews/v047-dev-pilot-20261028/reviewer-2.csv` SHA-256: `a87095440dc445717a2fb9cfff0b3bcb925231c64a386700087bef07cf9ad9d2`
- `reports/evaluation_status.md` SHA-256: `5757a55c8fa50a13c29cdf6f5c0b1f327cbf78476308399f29094b82b2c56d33`

V047 development pilot v2 stratified across every available D-ID before any reviewer labels; v1 was retained and marked superseded. No labels or predictions were created.
- `data/prepared/v047-dev-pilot-cards-20261028-v2.jsonl` SHA-256: `5616a63d65cae86eb14767dfab31817fe2bcbce3be18bd899293635cf316debf`
- `data/prepared/v047-dev-pilot-selection-20261028-v2.json` SHA-256: `b243856c3d2d7085966567d0a657d79508ede5416510586e23b2af9f09cc504c`
- `data/reviews/v047-dev-pilot-20261028-v2/reviewer-1.csv` SHA-256: `3ae15c8fcacb1080629a350a8ac9b448152df073fb071de7d4435610f411dfd8`
- `data/reviews/v047-dev-pilot-20261028-v2/reviewer-2.csv` SHA-256: `3ae15c8fcacb1080629a350a8ac9b448152df073fb071de7d4435610f411dfd8`
- `docs/adjudication_protocol_v047-v2.md` SHA-256: `bd38ebcf9f6cff06f220134cc0c5cf03f55067c88795df5f6cdce218cd11d1b2`
- `reports/v047-dev-pilot-preparation-v2.md` SHA-256: `a40cc683c2cb53d16e37289a45ae9256f7eca5e5a20af15e86d8ee23ff3bd31f`
- `reports/evaluation_status.md` SHA-256: `6321ccf6979bf5eb0c0fc623495dd5a2ebe7a6fcb8d18abbb5f29905b93d9f59`

V047 pilot-v2 checkpoint completion (2026-10-28). Added version-matched reviewer instructions; bound their hash into the v2 selection manifest; corrected the sampling description to include symbol-level event uniqueness; refreshed pilot/evaluation status and checkpoint. No labels or predictions created.
- `docs/reviewer_instructions_v047-v2.md` SHA-256: `975f909690065c1eb86ea2c6b14ad5b19f342939b9fe8354622b96053db737a0`
- `data/prepared/v047-dev-pilot-selection-20261028-v2.json` SHA-256: `d02bef15d47d511f42c7ec3585c28b03cdcadcc3316b12a198c39382e4a6b812`
- `reports/v047-dev-pilot-preparation-v2.md` SHA-256: `c3bc5191c8f9a37a23078e61b2681cc726da6903e08d71cba39acc73d3a44a65`
- Frozen case-analysis SHA-256 rechecked: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`

V047 original-case mapping audit correction v2 (2026-10-28). The v1 per-case scan correctly found five Flask BASE commit matches but its narrative incorrectly claimed zero. A read-only privileged verification confirmed the BASE commit in the verified `pallets/flask` clone; RTMX/fullstack upstream origins remain unresolved. V2 preserves and supersedes v1.
- `reports/v047/original-case-mapping-audit-v2.json` SHA-256: `2a80942fee92290d4afc2d67279cc6c192a7ffa3cd814910be9b1cf48ab122ea`
- `reports/v047/original-case-mapping-audit-v2.md` SHA-256: `4ae0ff9250db87e1d73fcaf075de2a168022c86458f3adf9cc3ad35e760fe807`
- Frozen diagnostic SHA-256 rechecked: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`

V047 pilot report mapping addendum (2026-10-28). Added current partial mapping status to the v2 pilot report; selection inputs remain unchanged.
- `reports/v047-dev-pilot-preparation-v2.md` SHA-256: `00dd90dc398c4fb7b5b22d5f23f0adeac84bc216de4e142c36bb6687674650e6`


## V047 original-case mapping identity corroboration v3 (2026-10-28)

Official public repository content corroborates RTMX and FastAPI snapshot identities; exact revision ancestry remains unverified. Flask BASE exact match retained. No labels, scores, or split changed. No tests/inference ran.
- `reports/v047/original-case-mapping-audit-v3.json` SHA-256: `767457cd2f1c943a6b5ef920044bba3a4d2e4e9579714b763f9e438359e19fb6`
- `reports/v047/original-case-mapping-audit-v3.md` SHA-256: `095e576c7b475a7ccd6fbf5d4c57adf7f5b01da899b82077211e962b3640aa8b`
- Frozen case-analysis SHA-256 rechecked before writes: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`


## V047 mapping v3 focused validation follow-up (2026-10-28)

- Measurement harness: `tests/test_measure.py` — 7 passed, 0 failed/errors/skipped in 1.17s.
- JUnit: `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\measure-v047-current.xml` SHA-256 `ca6b93f7493efa805916a277578af8883a1567b37de45f8cc9078757884e0a19`.
- Frozen case-analysis SHA-256 rechecked after test: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.
- No inference, new labels, split changes, or accuracy scores.


## Evaluation target reporting scope (2026-10-28)

Recorded both targets separately: 33/36 development diagnostic and >=95% independent research target; the latter governs the principal scientific claim. Current results remain NOT MEASURED / NOT ESTABLISHED. No data or labels changed.


## C++ native-language temp-path recheck (2026-10-28)

- With sandbox default TEMP/TMP: focused C++ test failed during Clang VFS temp creation (`WinError 5`, access denied); no product assertion reached.
- With TEMP/TMP redirected to writable task workspace: focused C++ test 1 passed (3.77s); native-language module 4 passed (3.61s).
- No resolver code changed; full suite not rerun; accuracy and inference not measured.
- JUnit hashes: focused `4172fc994caf0086f0c08451a9e939ea097e875ee49c775ba02940364179695e`, module `8174b661af9f5b03a95c5d45ab7ab70d567f20d34f58ae44c746d3c336067383`. Frozen case hash: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.


## Full-suite status reconciliation (2026-10-28)

Verified JUnit `work/contract-continuation/v047-full-suite-009.xml` has 516 tests: 513 passed, 3 failed, 0 errors, 0 skipped; exit 1. The three failures are Windows symlink fixture setup (`WinError 1314`). The earlier C++ failure is absent from this JUnit and passed in a later targeted run using writable TEMP/TMP. Full suite not rerun after that targeted run. JUnit SHA-256: `28616c87532f77f2d42312c0cfd7777f14f00f9c1b0aa0b16f101ab1e0c9be44`. Frozen case-analysis hash unchanged: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.


## Saved evaluation report bundle (2026-10-28)

Added the missing saved-evidence evaluations and a source hash manifest. No model call, label, or source code was changed. Frozen case SHA-256: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. V3/33-of-36 accuracy remains NOT MEASURED; independent 95% NOT ESTABLISHED. Report hashes are recorded in `reports/evaluation_status.md`.


## 2026-10-28 - V047 10-commit candidate mining

- Added 746 unreviewed, development-only mined candidates from 12 pinned repositories (10 sampled commits each; seed 104730); no labels or predictions.
- Added `reports/v047/mining-10commit-seed104730-20261028.md` and `reports/v047/mining-10commit-seed104730-20261028.json`; latest status, evaluation status, checkpoint, and master register now record the run.
- SHA-256 by changed file:
  - `data/prepared/v047-candidates-20261028-10commits-seed104730.jsonl`: `e2ac4e067f037c00b50576e500ffa2fb91d5ec05d26669ac5b965f7ed1f97f77`
  - `reports/v047/mining-10commit-seed104730-20261028.md`: `74ad2b4630d14326a05e4b15a5d140d677a85af2b239308bfffc6d9ebb48f128`
  - `reports/v047/mining-10commit-seed104730-20261028.json`: `9f6935c60282d4fd20c6ecadcb3f410a53da453046f64b8d14d2f5b754c7135d`
  - `reports/execution/latest-status.json`: `82bbdd1fc2832d28df9961d22cb8069722ab7f3da0c5d1afca7263cb2c0281fa`
  - `reports/evaluation_status.md`: `7ea8ae4dd4574bc7bd6f19ec5676f7cdc0706c9186f28848372b5335c56eed00`
  - `docs/EXECUTION_CHECKPOINT.md`: `5bfdc0cecfd17f00a7c6900ed5dcbe212a5f425362945ed3b7bb37bd4dafedf4`
  - `docs/VIGILANT_MASTER_TASK_REGISTER.md`: `0f390310e9bad16123385fb9f493709851fd5cd67b7ee08742cae9cc7b3afc0b`


## 2026-10-28 - V047 inference preflight refresh

- Rechecked local model readiness without network access or generation; both configured backends remain blocked.
- Added versioned raw results, summary and manifest; updated status/checkpoint/register.
- SHA-256 by changed file:
  - `reports/v047/preflight-result-ollama-20261028-followup.json`: `daafee6d02da452e10181fa74b5f158e57127d6a00b6963638a6cc3d0e712855`
  - `reports/v047/preflight-result-local-20261028-followup.json`: `8636f82aca4dc3567a2b3ba6ee05844379d32d3ac112ec659f8b1792258319e1`
  - `reports/v047/inference-preflight-followup-20261028.md`: `0500a7c91afa1e0af55585ae8d9d783780c289dc25a5b92c1ff2598e8160ca98`
  - `reports/v047/inference-preflight-followup-20261028.json`: `19845f61421041f933959cb4ca33c3a381c41d0ad81448cb3445f0e959159b06`
  - `reports/execution/latest-status.json`: `cbbf59accf40b1b3080091bb35ee45e3fcfe1d895c05d52cb4c8ee91ccab3b31`
  - `reports/evaluation_status.md`: `23ed710e74b6b0a31842205718535e92fa1f015900c6d267c904688e7f7e0824`
  - `docs/EXECUTION_CHECKPOINT.md`: `ef3a43a37e1602d5106bb48d0d1a92821af401079a9f06838a361b2b5a9e0411`
  - `docs/VIGILANT_MASTER_TASK_REGISTER.md`: `143187ade72c1a38c3edb02760f7bec34e5ef5be7e5b1fe150dad43d39829258`


## 2026-10-29 - Candidate card schema validation

- Converted and schema-validated 279 D-ID-tagged candidates; kept all labels null and adjudications pending. Generic changes without D-ID remain in the source pool.
- Recorded the run and updated status/checkpoint/register. The 24-case reviewer pilot and zero-count reviewed-coverage scaffold were not changed.
- SHA-256 by changed file:
  - `data/prepared/v047-candidate-cards-20261029-10commit-did-eligible.jsonl`: `723a730147c6b572ff73d29e7e30a7b372d309495ea3d8e5cfdab7f98c8c5aa5`
  - `reports/v047/candidate-card-validation-20261029.md`: `060c470f3541648e8fea5d7147efbd8b9e9bde96854b5811bdc746c3f7b38bd7`
  - `reports/v047/candidate-card-validation-20261029.json`: `06a5ab6000b5f56a317585d674df285a56ce6d14c87df32d69e7a7730f230402`
  - `reports/execution/latest-status.json`: `1c381a5eb478ef4b7efc359c0f888925e7c1d4cca03cdb13215f812b3ca09f56`
  - `reports/evaluation_status.md`: `5f48d156ac5216fd902ae4a7bcb6b300e9269e622457affba558a3a9d4dbcedc`
  - `docs/EXECUTION_CHECKPOINT.md`: `fdb480f1e6fdf32a7b663c6ea28e62d03a2f0dfab8b6479dce0459a649fa1421`
  - `docs/VIGILANT_MASTER_TASK_REGISTER.md`: `01f75cfca78d14b06ce5e2b88de4108b6eb69c713e7a11d6c34302b13741425d`


## 2026-10-29 — Development-pool integrity audit

- Extended `scripts/audit_diagnostic_cases_v3.py` to accept JSON arrays/JSONL candidate pools and retrieval inputs, compare exact repository/revision/text overlap, report split contamination and unreviewed-label integrity, and include source hashes and run time. No raw candidate hunks were available, so semantic near-duplicate screening is explicitly NOT MEASURED.
- Added five focused regression tests; all passed. Full suite not rerun. No labels, predictions, or model calls.
- Frozen case-analysis SHA-256 verified unchanged: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.
- Evidence hashes:
  - `scripts/audit_diagnostic_cases_v3.py`: `db0df97d7cd622044299c9c3e971f7b77eae05f0ef693860dabf64708c18730a`
  - `tests/test_audit_diagnostic_cases_v3.py`: `8af6fe970c493f195b427152a5e62db4867f68832c40b42a3c53b8944a4990c6`
  - `reports/v047/audit_diagnostic_cases_v3-before-20261029.py`: `e4a97b5460d9e494ef32e1dbb8a42f3554b14a1f07046524164ef9bc866fd2e3`
  - `reports/v047/evaluation-pool-audit-20261029.json`: `f93132ae1bdc2ef151d373913817beaadd591c7183dd75d92826eb49c6e5ef10`
  - `reports/v047/evaluation-pool-audit-tests-20261029.xml`: `b188f181f334a26634607210999246156ff0fe5e449197d8c43d93278c96a855`
  - `reports/v047/evaluation-pool-audit-20261029.md`: `8c2ba33fcdaff2b74f7b57310d4b8e0e98a441ce13f79e491a8730bdec5ab936`
  - `reports/execution/latest-status.json`: `878c2186168d63db155401864d77f0f265842382dda22f1d7e8661bf9be8c4ed`
  - `reports/evaluation_status.md`: `798ff5ca9e0a1ba2210a37f0aaf6dbf2f34fe7c2255871c0724fadd074875fdf`
  - `docs/EXECUTION_CHECKPOINT.md`: `57b628127b149d2dc53843039632def1d6ae0d810163e5804239013162940eea`
  - `docs/VIGILANT_MASTER_TASK_REGISTER.md`: `98c38ae89b2ef1335cee95b4da64c5219d60a633aab8f01dcbde5011e9cc6972`
  - `docs/EXECUTION_RESUME_PROMPT.md`: `18f77b5fddc8de5ab7193792d40a3820ac17f769d8ccd124e509e9f744cc88d7`
  - `reports/v047/V047_FINAL_REPORT.md`: `715315117b15947245838bc096dec599697e7f29781fdb84bff4431ed694c308`
  - `reports/llm-diagnostic-error-analysis/case-analysis.json`: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`
