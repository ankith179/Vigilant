"""Report descriptive agreement for two completed reviewer form JSON files."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.reviewer_agreement import summarize_reviewer_agreement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-forms", type=Path, nargs=2, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserve prior reviewer work")
    forms = [json.loads(path.read_text(encoding="utf-8")) for path in args.reviewer_forms]
    result = summarize_reviewer_agreement(forms)
    result["source_files"] = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in args.reviewer_forms
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Reported descriptive agreement for {result['case_count']} shared cases.")
    print("This report is not an accuracy or independent evaluation result.")


if __name__ == "__main__":
    main()
