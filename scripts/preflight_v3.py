"""Report local model readiness without generation or network probes."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm.preflight import inspect_local

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend", choices=["none", "ollama", "local"], default="ollama")
    p.add_argument("--model", default="qwen3:8b")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = inspect_local(args.backend, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result))
    return 2 if result["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    raise SystemExit(main())
