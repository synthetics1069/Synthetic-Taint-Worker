#!/usr/bin/env python3
"""Run the five-model prompt manifest against ComfyUI with resume support."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("/workspace/model-lab/output/Model_Lab_01")


class PermanentError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def request_json(base_url: str, path: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        if error.code in {400, 401, 403, 404}:
            raise PermanentError(f"HTTP {error.code} for {path}: {detail}") from error
        raise
    return json.loads(body) if body else {}


def bind(workflow: dict, binding: list[str], value) -> None:
    node_id, input_name = binding
    workflow[node_id]["inputs"][input_name] = value


def validate_manifest(manifest: dict) -> None:
    prompts = manifest.get("prompts", [])
    seeds = manifest.get("seed_set", [])
    if manifest.get("manifest_status") != "APPROVED":
        raise PermanentError(
            "Prompt manifest is not APPROVED. J.K. must supply and approve all 15 prompts."
        )
    if len(prompts) != 15:
        raise PermanentError(f"expected 15 prompts, found {len(prompts)}")
    if len(seeds) != 12 or len(set(seeds)) != 12:
        raise PermanentError("seed_set must contain 12 unique integers")
    if manifest.get("samples_per_prompt_per_model") != 12:
        raise PermanentError("samples_per_prompt_per_model must equal 12")
    expected_ids = [f"Prompt_{index:02d}" for index in range(1, 16)]
    actual_ids = [item.get("prompt_id") for item in prompts]
    if actual_ids != expected_ids:
        raise PermanentError(f"prompt IDs must be ordered exactly as {expected_ids}")
    incomplete = [
        item.get("prompt_id", "<unknown>")
        for item in prompts
        if item.get("status") != "APPROVED" or not item.get("prompt", "").strip()
    ]
    if incomplete:
        raise PermanentError("unapproved or empty prompts: " + ", ".join(incomplete))


def required_classes(workflow: dict) -> set[str]:
    return {item["class_type"] for item in workflow.values()}


def validate_comfy(base_url: str, models: list[dict]) -> None:
    object_info = request_json(base_url, "/object_info", timeout=60)
    missing: dict[str, list[str]] = {}
    for model in models:
        workflow = read_json(PACKAGE_ROOT / model["workflow"])
        absent = sorted(required_classes(workflow) - set(object_info))
        if absent:
            missing[model["slug"]] = absent
    if missing:
        raise PermanentError("ComfyUI is missing required node classes: " + json.dumps(missing))


def submit_and_wait(
    base_url: str,
    workflow: dict,
    client_id: str,
    timeout_seconds: int,
) -> tuple[str, dict, float]:
    started = time.monotonic()
    submitted = request_json(
        base_url,
        "/prompt",
        {"prompt": workflow, "client_id": client_id},
        timeout=60,
    )
    prompt_id = submitted.get("prompt_id")
    if not prompt_id:
        raise PermanentError(f"ComfyUI rejected workflow: {submitted}")

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        history = request_json(base_url, f"/history/{prompt_id}", timeout=30)
        if prompt_id in history:
            record = history[prompt_id]
            status = record.get("status", {})
            if status.get("status_str") == "error":
                raise PermanentError(
                    f"ComfyUI execution failed for {prompt_id}: "
                    + json.dumps(status.get("messages", []))
                )
            if record.get("outputs"):
                return prompt_id, record, time.monotonic() - started
        time.sleep(2)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} exceeded {timeout_seconds} seconds")


def output_images(record: dict) -> list[dict]:
    images: list[dict] = []
    for node_output in record.get("outputs", {}).values():
        images.extend(node_output.get("images", []))
    return images


def resolve_comfy_output(output_root: Path, image_record: dict) -> Path:
    filename = image_record["filename"]
    subfolder = image_record.get("subfolder", "")
    return output_root / subfolder / filename


def validate_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def make_contact_sheet(model_dir: Path, records: list[dict]) -> Path:
    paths = [model_dir / item["filename"] for item in records]
    thumbs: list[Image.Image] = []
    tile_size = 384
    label_height = 44
    font = ImageFont.load_default()
    for item, path in zip(records, paths):
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (tile_size, tile_size + label_height), "black")
            x = (tile_size - image.width) // 2
            y = (tile_size - image.height) // 2
            tile.paste(image, (x, y))
            draw = ImageDraw.Draw(tile)
            draw.text((10, tile_size + 8), f"Image {item['image_index']:02d} | seed {item['seed']}", fill="white", font=font)
            thumbs.append(tile)

    sheet = Image.new("RGB", (tile_size * 4, (tile_size + label_height) * 3), "#161616")
    for index, tile in enumerate(thumbs):
        sheet.paste(tile, ((index % 4) * tile_size, (index // 4) * (tile_size + label_height)))
    path = model_dir / "contact_sheet.jpg"
    sheet.save(path, quality=92)
    return path


def make_prompt_comparison(prompt_dir: Path, models: list[dict]) -> Path | None:
    sheets = [prompt_dir / model["slug"] / "contact_sheet.jpg" for model in models]
    if not all(path.exists() for path in sheets):
        return None
    font = ImageFont.load_default()
    panels: list[Image.Image] = []
    for model, path in zip(models, sheets):
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((900, 760), Image.Resampling.LANCZOS)
            panel = Image.new("RGB", (920, image.height + 50), "#101010")
            panel.paste(image, ((920 - image.width) // 2, 40))
            ImageDraw.Draw(panel).text((12, 12), model["display_name"], fill="white", font=font)
            panels.append(panel)
    width = max(panel.width for panel in panels)
    height = sum(panel.height for panel in panels)
    comparison = Image.new("RGB", (width, height), "#101010")
    y = 0
    for panel in panels:
        comparison.paste(panel, (0, y))
        y += panel.height
    output = prompt_dir / f"{prompt_dir.name}__comparison.jpg"
    comparison.save(output, quality=90)
    return output


def free_models(base_url: str) -> None:
    try:
        request_json(base_url, "/free", {"unload_models": True, "free_memory": True}, timeout=60)
    except Exception as error:
        print(f"WARNING: ComfyUI memory-release request failed: {error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--manifest", type=Path, default=PACKAGE_ROOT / "experiments/prompt_manifest.json")
    parser.add_argument("--models", type=Path, default=PACKAGE_ROOT / "experiments/models.json")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--comfy-output-root", type=Path, default=Path("/workspace/model-lab/output"))
    parser.add_argument("--model", action="append", dest="model_filters")
    parser.add_argument("--prompt", action="append", dest="prompt_filters")
    parser.add_argument("--smoke", action="store_true", help="Run only Prompt_01, seed 1, for selected models.")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    model_config = read_json(args.models)
    validate_manifest(manifest)
    models = model_config["models"]
    if args.model_filters:
        wanted = set(args.model_filters)
        models = [item for item in models if item["slug"] in wanted]
        missing = wanted - {item["slug"] for item in models}
        if missing:
            raise PermanentError("unknown model filters: " + ", ".join(sorted(missing)))
    validate_comfy(args.base_url, models)

    prompts = manifest["prompts"]
    if args.prompt_filters:
        wanted_prompts = set(args.prompt_filters)
        prompts = [item for item in prompts if item["prompt_id"] in wanted_prompts]
        missing_prompts = wanted_prompts - {item["prompt_id"] for item in prompts}
        if missing_prompts:
            raise PermanentError("unknown prompt filters: " + ", ".join(sorted(missing_prompts)))
    if args.smoke:
        prompts = prompts[:1]
    seeds = manifest["seed_set"][:1] if args.smoke else manifest["seed_set"]
    args.output_root.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_root / "prompt_manifest.snapshot.json", manifest)
    atomic_json(args.output_root / "models.snapshot.json", model_config)
    state_path = args.output_root / "run_state.json"
    state = read_json(state_path) if state_path.exists() else {
        "lab_id": manifest["lab_id"],
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "completed": {},
    }
    client_id = str(uuid.uuid4())

    for model_index, model in enumerate(models):
        if model_index:
            free_models(args.base_url)
        template = read_json(PACKAGE_ROOT / model["workflow"])
        print(f"MODEL {model['display_name']}")
        for prompt in prompts:
            prompt_dir = args.output_root / prompt["prompt_id"]
            model_dir = prompt_dir / model["slug"]
            model_dir.mkdir(parents=True, exist_ok=True)
            metrics_path = model_dir / "metrics.json"
            metrics = read_json(metrics_path) if metrics_path.exists() else {
                "prompt_id": prompt["prompt_id"],
                "model_slug": model["slug"],
                "model_display_name": model["display_name"],
                "effective_defaults": model["defaults"],
                "images": [],
            }
            by_index = {item["image_index"]: item for item in metrics["images"]}

            for image_index, seed in enumerate(seeds, start=1):
                filename = (
                    f"{prompt['prompt_id']}__{model['slug']}__"
                    f"Image_{image_index:02d}__seed-{seed}.png"
                )
                final_path = model_dir / filename
                state_key = f"{prompt['prompt_id']}::{model['slug']}::{image_index:02d}"
                if final_path.exists():
                    try:
                        validate_png(final_path)
                        print(f"  SKIP {state_key}")
                        continue
                    except Exception:
                        raise PermanentError(f"existing output is corrupt: {final_path}")

                workflow = copy.deepcopy(template)
                bindings = model["bindings"]
                bind(workflow, bindings["prompt"], prompt["prompt"])
                if "negative_prompt" in bindings and prompt.get("negative_prompt"):
                    bind(workflow, bindings["negative_prompt"], prompt["negative_prompt"])
                bind(workflow, bindings["seed"], seed)
                bind(workflow, bindings["width"], model["defaults"]["width"])
                bind(workflow, bindings["height"], model["defaults"]["height"])
                prefix = f"Model_Lab_01/_staging/{prompt['prompt_id']}__{model['slug']}__{image_index:02d}"
                bind(workflow, bindings["output_prefix"], prefix)

                for attempt in range(1, args.retries + 1):
                    try:
                        prompt_id, history, elapsed = submit_and_wait(
                            args.base_url, workflow, client_id, args.timeout_seconds
                        )
                        images = output_images(history)
                        if len(images) != 1:
                            raise PermanentError(
                                f"expected one image for {state_key}; ComfyUI returned {len(images)}"
                            )
                        source = resolve_comfy_output(args.comfy_output_root, images[0])
                        if not source.exists():
                            raise PermanentError(f"ComfyUI output is missing: {source}")
                        shutil.move(str(source), str(final_path))
                        width, height = validate_png(final_path)
                        record = {
                            "image_index": image_index,
                            "seed": seed,
                            "filename": filename,
                            "width": width,
                            "height": height,
                            "elapsed_seconds": round(elapsed, 3),
                            "comfy_prompt_id": prompt_id,
                            "completed_at": utc_now(),
                        }
                        by_index[image_index] = record
                        metrics["images"] = [by_index[key] for key in sorted(by_index)]
                        atomic_json(metrics_path, metrics)
                        state["completed"][state_key] = record
                        state["updated_at"] = utc_now()
                        atomic_json(state_path, state)
                        print(f"  PASS {state_key} {elapsed:.1f}s")
                        break
                    except PermanentError:
                        raise
                    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as error:
                        if attempt >= args.retries:
                            raise
                        delay = 5 * (2 ** (attempt - 1))
                        print(f"  RETRY {state_key} after {error}; waiting {delay}s")
                        time.sleep(delay)

            complete_records = [by_index[index] for index in sorted(by_index) if index <= len(seeds)]
            if len(complete_records) == len(seeds):
                make_contact_sheet(model_dir, complete_records)

    for prompt in prompts:
        make_prompt_comparison(args.output_root / prompt["prompt_id"], models)
    state["finished_at"] = utc_now()
    state["updated_at"] = utc_now()
    atomic_json(state_path, state)
    print(f"Lab run complete: {args.output_root}")


if __name__ == "__main__":
    main()
