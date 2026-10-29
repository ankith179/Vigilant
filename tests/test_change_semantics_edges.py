from change_analysis.diff import _change_semantics


def test_unchanged_source_is_not_misclassified_as_comment_only():
    source = "def value():\n    return 1\n"
    assert _change_semantics("module.py", source, source) != "COMMENT_ONLY"


def test_actual_comment_edit_remains_comment_only():
    assert _change_semantics("module.py", "# before\nx=1\n", "# after\nx=1\n") == "COMMENT_ONLY"
