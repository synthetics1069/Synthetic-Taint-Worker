#!/usr/bin/env python3
"""Populate persistent storage from the pinned model manifest."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download


ROOT = Path(__file__).resolve().parents[1]


def ready(path: Path, kind: str) -> bool:
    if kind == "snapshot":
        return path.is_dir() and any(item.is_file() for item in path.rglob("*"))
    return path.exists() and path.stat().st_size > 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(ROOT / "model_manifest.json"))
    parser.add_argument(
        "--models-root",
        default=os.environ.get("MODEL_LAB_MODELS", "/workspace/model-lab/models"),
    )
    parser.add_argument(
        "--cache-root",
        default=os.environ.get("HF_HOME", "/workspace/model-lab/.cache/huggingface"),
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy file assets instead of symlinking from the persistent cache.",
    )
    args = parser.parse_args()

    models_root = Path(args.models_root)
    cache_root = Path(args.cache_root)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    token = os.environ.get("HF_TOKEN")
    failures: list[str] = []

    for index, item in enumerate(manifest["models"], start=1):
        kind = item.get("kind", "file")
        destination = models_root / item["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if ready(destination, kind) and not args.force:
            print(f"[{index:02d}/{len(manifest['models']):02d}] present {item['role']}: {destination}")
            continue

        try:
            print(f"[{index:02d}/{len(manifest['models']):02d}] downloading {item['role']}...")
            if kind == "snapshot":
                snapshot_download(
                    repo_id=item["repo_id"],
                    cache_dir=cache_root,
                    local_dir=destination,
                    allow_patterns=item.get("allow_patterns"),
                    ignore_patterns=item.get("ignore_patterns"),
                    token=token,
                )
            elif kind == "file":
                cached = Path(
                    hf_hub_download(
                        repo_id=item["repo_id"],
                        filename=item["filename"],
                        cache_dir=cache_root,
                        token=token,
                        force_download=args.force,
                    )
                )
                if destination.is_symlink() or destination.exists():
                    destination.unlink()
                if args.copy:
                    shutil.copy2(cached, destination)
                else:
                    destination.symlink_to(cached)
            else:
                raise ValueError(f"unsupported asset kind: {kind}")
            if not ready(destination, kind):
                raise RuntimeError(f"download completed but destination is not usable: {destination}")
            print(f"    ready: {destination}")
        except Exception as error:
            failures.append(f"{item['role']}: {error}")
            print(f"    FAILED: {error}")

    if failures:
        raise SystemExit("\nModel preparation failed:\n- " + "\n- ".join(failures))
    print("All model assets are ready.")


if __name__ == "__main__":
    main()
