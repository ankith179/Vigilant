"""Validate a single proposed diagnostic dataset case against the v1 contract."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.case_validation import validate_case

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',type=Path);a=p.parse_args()
    errors=validate_case(json.loads(a.case.read_text(encoding='utf-8')))
    print(json.dumps({'valid':not errors,'errors':errors}))
    return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
