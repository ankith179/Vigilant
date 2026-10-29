import subprocess

from agents.assurance import assess_changes
from change_analysis.diff import detect
from database.store import Store
from ingestion.service import import_repository


def test_deleted_file_receipt_is_verified_and_exported_as_head_change_metadata(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    path = repo / "module.py"
    path.write_text("def redirect(url):\n    return url\n")
    git("add", ".")
    git("commit", "-m", "base")
    store = Store("sqlite:///:memory:")
    base = import_repository(store, repo)
    before = store.artifacts(base["repository"], base["commit_id"])
    path.unlink()
    git("add", "-A")
    git("commit", "-m", "delete")
    head = import_repository(store, repo)
    after = store.artifacts(head["repository"], head["commit_id"])
    changes = detect(repo, base["commit_id"], head["commit_id"], before, after)

    result = assess_changes(changes, before, after, repo)

    assert result["assessments"]
    assert any(e["extraction_method"] == "git_diff_deleted_file"
               and e["revision_role"] == "HEAD" for e in result["evidence"])
