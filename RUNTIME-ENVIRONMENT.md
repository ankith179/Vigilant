# Runtime environment

The `.venv` directory was copied with its installed dependencies. The original checkout and runtime remain unchanged. The source `.runtime` contains the TEBench Git cache and was not duplicated. The 12 `.git` files omitted from this Windows copy are stale worktree pointers to old `/workspace/scratch` paths, not source code.

Focused target-path tests passed 7/7. The full Windows suite has not passed; see `reports/realworld-20261026/95-percent-target-update.md`. Use `.venv\Scripts\python.exe -X utf8` from this folder.
