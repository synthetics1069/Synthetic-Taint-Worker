#!/usr/bin/env python3
"""Static validation for JK Model Lab v1.1."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SLUGS = [
    "hidream_o1_full",
    "chroma1_hd",
    "krea2_turbo",
    "kolors",
    "z_image_base",
]
EXPECTED_PROMPTS = [f"Prompt_{index:02d}" for index in range(1, 16)]
FORBIDDEN_ROLES = ("wan", "qwen_image_edit", "joyai", "glm_image")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    model_manifest = read_json(ROOT / "model_manifest.json")
    experiment = read_json(ROOT / "experiments" / "models.json")
    prompts = read_json(ROOT / "experiments" / "prompt_manifest.json")

    models = experiment["models"]
    slugs = [item["slug"] for item in models]
    assert slugs == EXPECTED_SLUGS, f"unexpected model order: {slugs}"
    assert experiment["execution_order"] == "model_major"
    assert prompts["samples_per_prompt_per_model"] == 12
    assert len(prompts["seed_set"]) == 12
    assert len(set(prompts["seed_set"])) == 12
    assert [item["prompt_id"] for item in prompts["prompts"]] == EXPECTED_PROMPTS
    assert len(prompts["prompts"]) * len(models) * len(prompts["seed_set"]) == 900

    destinations = [item["destination"] for item in model_manifest["models"]]
    assert len(destinations) == len(set(destinations)), "duplicate model destinations"
    roles = " ".join(item["role"].lower() for item in model_manifest["models"])
    assert not any(token in roles for token in FORBIDDEN_ROLES), "deferred model found in manifest"

    assert model_manifest["lab_version"] == "1.1.0"
    custom_nodes = model_manifest["custom_nodes"]
    assert len(custom_nodes) == 1
    assert custom_nodes[0]["name"] == "ComfyUI-KwaiKolorsWrapper"
    assert custom_nodes[0]["commit"] == "6fc1cd9d20bb7537facf180e5494b486b9710e24"

    for model in models:
        api_path = ROOT / model["workflow"]
        ui_path = ROOT / "workflows" / f"{model['slug']}.json"
        assert api_path.exists(), f"missing API workflow: {api_path}"
        assert ui_path.exists(), f"missing UI workflow: {ui_path}"
        api = read_json(api_path)
        assert isinstance(api, dict) and api, f"empty API workflow: {api_path}"
        save_nodes = [node for node in api.values() if node.get("class_type") == "SaveImage"]
        assert len(save_nodes) == 1, f"expected one SaveImage node in {api_path}"
        for name, binding in model["bindings"].items():
            node_id, input_name = binding
            assert node_id in api, f"{model['slug']} binding {name} has missing node {node_id}"
            assert input_name in api[node_id].get("inputs", {}), (
                f"{model['slug']} binding {name} has missing input {node_id}.{input_name}"
            )

    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "6f3895ed8d1e0f1d5fad11b48b3f159f7de1cc15" in dockerfile
    assert "6fc1cd9d20bb7537facf180e5494b486b9710e24" in dockerfile
    assert "EXPOSE 8188 8888" in dockerfile
    start_script = (ROOT / "scripts" / "start.sh").read_text(encoding="utf-8")
    assert start_script.index("/start.sh") < start_script.index("download_models.py"), (
        "RunPod SSH/Jupyter services must start before model downloads"
    )
    assert "runs/model-downloads.log" in start_script
    initialize_script = (ROOT / "scripts" / "initialize.sh").read_text(encoding="utf-8")
    assert 'models/diffusers/Kolors' in initialize_script
    assert 'models/diffusers" "$COMFY_ROOT/models/diffusers' not in initialize_script
    smoke_script = (ROOT / "scripts" / "container_smoke_test.sh").read_text(encoding="utf-8")
    assert smoke_script.count("/opt/model-lab/scripts/initialize.sh") == 2
    assert ".preexisting-content" in smoke_script
    assert "ComfyUI-KwaiKolorsWrapper" in smoke_script
    assert "/system_stats" in smoke_script
    assert "RUN /opt/model-lab/scripts/container_smoke_test.sh" in dockerfile
    assert prompts["protocol_version"] == "1.0.0"
    assert prompts["approved_by"] == "J.K."
    assert prompts["manifest_status"] == "APPROVED"
    assert all(item["status"] == "APPROVED" and item["prompt"] for item in prompts["prompts"])
    protocol = ROOT / "docs" / "MODEL_LAB_PROMPTS_AND_EXECUTION.md"
    assert protocol.exists(), "canonical prompt protocol is missing"
    protocol_text = protocol.read_text(encoding="utf-8")
    assert "**Protocol version:** `1.0.0`" in protocol_text
    assert "**Protocol status:** `APPROVED`" in protocol_text
    manifest_bytes = (ROOT / "experiments" / "prompt_manifest.json").read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    recorded_hash = (ROOT / "experiments" / "prompt_manifest.sha256").read_text(encoding="utf-8").split()[0]
    assert digest == recorded_hash == "ee34b067c62bebdf315d5bb766458a98db7643729c85edb35a683262f044202d"
    print(
        "PASS: 5 models, 5 UI workflows, 5 API workflows, "
        "15 approved prompts, 12 fixed seeds, 900 planned images"
    )


if __name__ == "__main__":
    main()
