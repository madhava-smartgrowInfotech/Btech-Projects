"""Download the pre-trained local models PolicyLens uses into ``models/hf/``.

Usage (from the project root):
    venv\\Scripts\\python scripts\\download_models.py

The weights are not stored in git (about 460 MB). This script fetches the exact
revisions recorded in ``models/manifest.json`` (or the latest revision when the
manifest has none yet, then records it). After this, the app runs offline except
for Gemini calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "models" / "manifest.json"
TARGET = ROOT / "models" / "hf"

DEFAULT_MODELS = [
    {
        "key": "embedder",
        "repo_id": "sentence-transformers/all-MiniLM-L6-v2",
        "purpose": "Dense clause embeddings for semantic retrieval (384 dimensions)",
        "license": "Apache-2.0",
    },
    {
        "key": "reranker",
        "repo_id": "cross-encoder/ms-marco-MiniLM-L6-v2",
        "purpose": "Cross-encoder re-ranking of fused BM25 + dense candidates",
        "license": "Apache-2.0",
    },
    {
        "key": "nli",
        "repo_id": "cross-encoder/nli-deberta-v3-xsmall",
        "purpose": "Natural-language inference for the answer faithfulness score",
        "license": "Apache-2.0",
    },
]

IGNORE = ["onnx/*", "openvino/*", "*.onnx", "*.h5", "*.msgpack", "*.ot", "tf_model*", "flax_model*",
          "rust_model*", "*.tflite", "pytorch_model.bin", "README.md", "*.png", "*.jpg"]


def folder_for(repo_id: str) -> Path:
    return TARGET / repo_id.replace("/", "__")


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"models": DEFAULT_MODELS}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError:
        print("[FAIL] huggingface_hub is missing - run setup.bat first.")
        return 1

    manifest = load_manifest()
    api = HfApi()
    TARGET.mkdir(parents=True, exist_ok=True)
    ok = True
    for entry in manifest["models"]:
        repo_id = entry["repo_id"]
        dest = folder_for(repo_id)
        revision = entry.get("revision")
        try:
            if not revision:
                revision = api.model_info(repo_id).sha
            print(f"-> {entry['key']}: {repo_id} @ {revision[:10]} ...", flush=True)
            snapshot_download(repo_id=repo_id, revision=revision, local_dir=dest, ignore_patterns=IGNORE)
            if not any(dest.glob("*.safetensors")):
                # Older repos only ship PyTorch .bin weights.
                snapshot_download(repo_id=repo_id, revision=revision, local_dir=dest,
                                  allow_patterns=["pytorch_model.bin"])
            size_mb = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) / 1e6
            entry.update({"revision": revision, "local_dir": dest.relative_to(ROOT).as_posix(),
                          "size_mb": round(size_mb, 1)})
            print(f"[OK]   {repo_id} ({size_mb:.0f} MB) -> {dest.relative_to(ROOT)}", flush=True)
        except Exception as exc:  # noqa: BLE001 - report and continue with the other models
            ok = False
            print(f"[FAIL] {repo_id}: {exc}", flush=True)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nAll local models are ready." if ok else "\nSome models failed - check your internet connection and run again.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
