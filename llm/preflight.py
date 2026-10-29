"""Local inference readiness; never installs assets, starts services, or changes security."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_local(backend="ollama", model="qwen3:8b", *, root=ROOT):
    result = {"backend": backend, "model": model, "status": "BLOCKED",
              "generation_attempted": False, "missing": [], "hashes": {},
              "python": sys.version, "schema_version": 3, "seed": 42, "temperature": 0}
    if backend == "none":
        result.update(status="NOT_REQUESTED")
        return result
    if backend == "ollama":
        if ":cloud" in model.lower() or "/" in model or "\\" in model or ".." in model:
            result["missing"].append("An approved local model name is required")
            return result
        runtime = shutil.which("ollama")
        candidates = [root/".runtime/ollama/ollama.exe", root/".runtime/ollama.exe"]
        runtime = Path(runtime) if runtime else next((p for p in candidates if p.is_file()), None)
        if runtime is None:
            result["missing"].append("Ollama executable unavailable")
        else:
            result["hashes"]["runtime"] = sha256(runtime)
        asset_root = Path(os.getenv("OLLAMA_MODELS", str(Path.home()/".ollama/models")))
        name, _, tag = model.partition(":")
        manifest = asset_root/"manifests/registry.ollama.ai/library"/name/(tag or "latest")
        if not manifest.is_file():
            result["missing"].append("Configured model manifest unavailable")
        else:
            result["hashes"]["model_manifest"] = sha256(manifest)
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                for layer in [data.get("config", {}), *data.get("layers", [])]:
                    digest = layer.get("digest", "")
                    if not digest.startswith("sha256:") or len(digest) != 71 or any(c not in "0123456789abcdef" for c in digest[7:]):
                        raise ValueError("Invalid model layer digest")
                    blob = asset_root/"blobs"/digest.replace(":", "-")
                    if not blob.is_file():
                        result["missing"].append("Model layer unavailable: "+digest)
                    elif sha256(blob) != digest[7:]:
                        result["missing"].append("Model layer hash mismatch: "+digest)
                    else:
                        result["hashes"][digest] = digest[7:]
            except (OSError, ValueError, TypeError) as exc:
                result["missing"].append("Invalid model manifest: "+type(exc).__name__)
    elif backend == "local":
        config = json.loads((root/"data/models.json").read_text(encoding="utf-8"))["llm"]
        folder = Path(os.getenv("VIGILANT_LLM_PATH", str(root/config["path"])))
        result["model"] = config.get("model")
        result["model_revision"] = config.get("revision")
        for dep in ("torch", "transformers", "lmformatenforcer"):
            if importlib.util.find_spec(dep) is None:
                result["missing"].append("Dependency unavailable: "+dep)
        for name in ("config.json", "tokenizer_config.json"):
            if not (folder/name).is_file():
                result["missing"].append("Model asset unavailable: "+name)
        weights = list(folder.glob("*.safetensors")) if folder.is_dir() else []
        if not weights:
            result["missing"].append("Model weights unavailable")
        else:
            for file in [*weights, *folder.glob("*.json")]:
                result["hashes"][file.name] = sha256(file)
    else:
        result["missing"].append("V3 local inference does not silently select an external provider")
    if not result["missing"]:
        result["status"] = "ASSETS_READY"
    return result
