"""Local replay runtime: preserve generation settings, retain model, cache each response."""
import hashlib
import json
import os
from pathlib import Path
import time


def install(engine, folder):
    import httpx
    cache = folder / "calls"
    cache.mkdir(exist_ok=True)
    call_index = 0

    def complete(messages):
        nonlocal call_index
        call_index += 1
        schema = getattr(engine, "output_schema", None) or engine.citation_schema(messages)
        body = {"model": engine.model, "messages": messages, "stream": False,
                "format": schema, "keep_alive": "10m",
                "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 512, "seed": 42}}
        if engine.identity["supports_thinking"]:
            body["think"] = False
        key = hashlib.sha256(json.dumps({"call_index": call_index, "body": body, "identity": engine.identity}, sort_keys=True).encode()).hexdigest()
        target = cache / (key + ".json")
        if target.exists():
            saved = json.loads(target.read_text(encoding="utf-8"))
            if saved["request"] != body or saved["model"] != engine.identity:
                raise ValueError("Cached request/model identity mismatch")
            return saved["raw"], saved["usage"]
        with (folder / "call_progress.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({"event": "START", "key": key, "time": time.time()}) + "\n")
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=600) as client:
            response = client.post(engine.base_url() + "/api/chat", json=body)
            response.raise_for_status()
            data = response.json()
        raw = data.get("message", {}).get("content")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("Ollama returned no final text")
        usage = {"input_tokens": data.get("prompt_eval_count"), "output_tokens": data.get("eval_count"),
                 "reported_model": data.get("model"), "api_cost_usd": 0., "local_model": engine.identity,
                 "elapsed_seconds": data.get("total_duration", 0) / 1e9,
                 "completion_error": None if data.get("done") and data.get("done_reason") == "stop" else "Incomplete Ollama generation",
                 "done": data.get("done"), "done_reason": data.get("done_reason"), "output_schema": schema,
                 "citation_policy": "selected-alias-enums-v1"}
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps({"request": body, "model": engine.identity, "raw": raw, "usage": usage}), encoding="utf-8")
        os.replace(temp, target)
        with (folder / "call_progress.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({"event": "DONE", "key": key, "time": time.time(), "seconds": usage["elapsed_seconds"]}) + "\n")
        return raw, usage

    engine.complete = complete
