import json

import pytest

from scripts.checkpoint import excluded_repository_clones, is_excluded_clone


def test_only_clones_marked_external_are_excluded_from_packages(tmp_path):
    path = tmp_path / "data/repos.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"repositories": [
        {"clone_path": "data/repos/pallets_flask", "package_included": False},
    ]}), encoding="utf-8")
    clones = excluded_repository_clones(tmp_path)
    assert is_excluded_clone("data/repos/pallets_flask/src/app.py", clones)
    assert not is_excluded_clone("data/repos/flask/app.py", clones)


def test_malformed_external_clone_manifest_fails_closed(tmp_path):
    path = tmp_path / "data/repos.json"
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        excluded_repository_clones(tmp_path)
