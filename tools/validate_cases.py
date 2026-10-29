"""Validate JSONL case cards without producing or changing labels."""
import argparse
import json
from pathlib import Path
from pydantic import ValidationError
try:
    from .case_card_v1 import CaseCard
except ImportError:
    from case_card_v1 import CaseCard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    seen, errors, count = set(), [], 0
    with args.input.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                card = CaseCard.model_validate_json(line)
                if card.case_id in seen:
                    raise ValueError("duplicate case_id")
                seen.add(card.case_id)
                count += 1
            except (ValidationError, ValueError) as exc:
                errors.append({"line": line_number, "error": str(exc)})
    print(json.dumps({"valid_cards": count, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
