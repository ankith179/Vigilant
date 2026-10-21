"""Resume only inference with matching inputs and model configuration.

Validation failures after generation remain observations. Loading failures are
retryable runtime failures, not observations of model accuracy.
"""
from pathlib import Path
import hashlib
import json
import os


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    os.replace(temporary, path)


def reusable_model(row, messages, identity):
    result = row.get('model', {})
    usage = result.get('usage', {})
    return bool(result.get('raw_output')) and usage.get('output_tokens', 0) > 0 and (
        result.get('messages') == messages
        and all(usage.get(k) == identity[k] for k in ('model', 'revision', 'dtype'))
        and usage.get('temperature') == 0
        and usage.get('max_new_tokens') == 220
    )


def reusable_completion(row, messages, identity, call_fingerprint):
    """Match a direct provider completion and prove that generation executed."""
    usage = row.get('usage', {})
    return bool(row.get('raw_output')) and usage.get('output_tokens', 0) > 0 and (
        row.get('call_fingerprint') == call_fingerprint
        and row.get('messages') == messages
        and all(usage.get(k) == identity[k] for k in ('model', 'revision', 'dtype'))
        and usage.get('temperature') == 0
        and usage.get('max_new_tokens') == 220
    )


def preserve_previous(path):
    """Preserve a replaced partial exactly once under its content hash."""
    path = Path(path)
    if path.exists():
        data = path.read_bytes()
        archive = path.parent / 'previous' / (path.stem + '-' + hashlib.sha256(data).hexdigest()[:16] + '.json')
        archive.parent.mkdir(exist_ok=True)
        if not archive.exists():
            archive.write_bytes(data)
