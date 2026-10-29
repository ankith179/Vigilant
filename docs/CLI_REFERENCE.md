# CLI reference

Run from the extracted VIGILANT directory after setup and `python scripts/restore_checkpoint.py`. Keep your current Windows database; extract this release into a separate folder.

```
python vigilant.py --help
python vigilant.py tools
python vigilant.py call explore_repository --arguments scope.json
python vigilant.py call run_recipe --arguments recipe.json
python vigilant.py compare --repository IMPORTED_REPOSITORY_ID --base BASE_REVISION --head HEAD_REVISION
python vigilant.py mcp
python scripts/measure_quality.py --output reports/my-quality-audit.json
python scripts/check_quality_target.py --output reports/my-95-gate.json
```

`scope.json` must contain `repository` and an exact immutable `commit_id` from your imported snapshots. Tools reject HEAD aliases. `recipe.json` adds a recipe name and, where needed, query, artifact_id or run_id; inspect `tools` for exact schemas. Existing import endpoints and scripts index snapshots; tools do not import arbitrary paths.

The optional global `--database` URL appears before the subcommand. Default is VIGILANT_DB, then sqlite:///data/vigilant.db. JSON goes to stdout, command failures use stderr and exit 2. CLI compare runs deterministic analysis and retains a report; no LLM is invoked. Existing install, reindex, evaluation and model scripts are retained.

To generate an unreviewed search inventory:

```
python scripts/build_search_inventory.py PATH_TO_REPOSITORY --commit COMMIT_SHA --prefix tests --output search-inventory.json
```

Every generated entry is UNKNOWN until reviewed. Do not use authored fixture judgments as independent evaluation labels.
