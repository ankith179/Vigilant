"""Evaluate saved V3 predictions per axis; does not call a model."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.decision_v3 import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not isinstance(data.get("cases"),list):
        raise SystemExit("Expected evaluation input schema_version=1 and cases[]")
    ids=[r.get("case_id") for r in data["cases"]]
    if None in ids or len(ids)!=len(set(ids)):raise SystemExit("Case IDs must be present and unique")
    result=evaluate(data)
    result["input_sha256"]=__import__("hashlib").sha256(args.input.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    print(json.dumps({"status":result["status"],"cases":result["case_count"],"conditions":list(result["conditions"])}))
if __name__=="__main__":raise SystemExit(main())
