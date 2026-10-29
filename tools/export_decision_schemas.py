"""Export JSON Schemas generated from the runtime V3 models."""
import json
from pathlib import Path

from ingestion.models import DecisionV3, FactsV3


def export(root=Path(__file__).resolve().parents[1]):
    schema_dir = root / "schemas"
    schema_dir.mkdir(exist_ok=True)
    for name, model in (("decision-schema-v3.json", DecisionV3), ("facts-v3.json", FactsV3)):
        target = schema_dir / name
        target.write_text(json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return schema_dir


if __name__ == "__main__":
    print(export())
