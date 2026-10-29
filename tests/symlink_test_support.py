"""Use real symlinks when permitted; simulate the symlink predicate on locked Windows hosts."""
from pathlib import Path


def make_symlink_or_mark(path, target, monkeypatch):
    path, target = Path(path), Path(target)
    try:
        path.symlink_to(target)
        return "REAL_SYMLINK"
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314:
            raise
        path.write_bytes(target.read_bytes())
        original = Path.is_symlink

        def is_symlink(candidate):
            return candidate == path or original(candidate)

        monkeypatch.setattr(Path, "is_symlink", is_symlink)
        return "SYMLINK_PREDICATE_SIMULATED_PERMISSION_UNAVAILABLE"
