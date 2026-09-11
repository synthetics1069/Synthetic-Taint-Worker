# JK Model Lab v1.1

This is a generation-only ComfyUI comparison lab designed for both agent operation and optional human inspection. It runs the same approved prompt and fixed seed set through five image models:

1. HiDream-O1-Image Full
2. Chroma1-HD
3. KREA 2 Turbo
4. Kolors
5. Z-Image Base

Wan 2.2 and the Qwen/JoyAI edit models were intentionally removed. Video generation and image editing belong in separate labs. GLM-Image is deferred because its hybrid architecture warrants its own setup and evaluation.

## Experiment contract

- 15 approved prompt variations
- 12 fixed seeds per prompt and model
- 5 models
- 900 total images
- 75 per-model contact sheets
- 15 cross-model prompt comparison sheets

The 15-prompt protocol was approved by J.K. on 2026-09-11 and is included in both human-readable and machine-readable forms. The approved `experiments/prompt_manifest.json` has SHA-256 `ee34b067c62bebdf315d5bb766458a98db7643729c85edb35a683262f044202d`. The runner still validates approval and completeness before spending GPU time.

## Persistent layout

The Docker image contains ComfyUI, workflows, and orchestration code. Model weights and all experiment artifacts live on persistent storage:

```text
/workspace/model-lab/
├── models/
├── input/
├── output/Model_Lab_01/
└── user/
```

Expected experiment output:

```text
output/Model_Lab_01/
├── prompt_manifest.snapshot.json
├── models.snapshot.json
├── run_state.json
└── Prompt_01/
    ├── hidream_o1_full/
    │   ├── Prompt_01__hidream_o1_full__Image_01__seed-104729.png
    │   ├── ... 11 more PNG files
    │   ├── metrics.json
    │   └── contact_sheet.jpg
    ├── chroma1_hd/
    ├── krea2_turbo/
    ├── kolors/
    ├── z_image_base/
    └── Prompt_01__comparison.jpg
```

## Prepare the network volume

From a running container or prep Pod with the volume mounted at `/workspace`:

```bash
python /opt/model-lab/scripts/download_models.py
```

Set the credential name `HF_TOKEN` only if Hugging Face requests authentication. Do not place secret values in the package. Downloads are idempotent and cached under `/workspace/model-lab/.cache/huggingface`.

## Build and run

```bash
docker build --platform=linux/amd64 -t YOUR_REGISTRY/jk-model-lab:v1.1.0 .
docker run --rm --gpus all -p 8188:8188 \
  -v "$(pwd)/runtime:/workspace/model-lab" \
  YOUR_REGISTRY/jk-model-lab:v1.1.0
```

Open `http://localhost:8188` for manual inspection. The five UI workflows are in `workflows/`; their immutable upstream source copies are in `workflow_sources/`. Automated experiments use the five API-format workflows in `api_workflows/`.

## Validate and execute

Static validation does not need a GPU:

```bash
python scripts/verify_package.py
```

After ComfyUI is running and the manifest is approved, run one image per model:

```bash
python scripts/run_lab.py --smoke
```

Then run or resume the complete experiment:

```bash
python scripts/run_lab.py
```

To complete the 60-image gate for the first prompt before authorizing the rest:

```bash
python scripts/run_lab.py --prompt Prompt_01
```

Execution is model-major to avoid repeatedly loading large model families. Storage is prompt-major for evaluation. Valid existing PNGs are skipped, metrics are written atomically, and only transient network errors, HTTP 5xx responses, and timeouts receive bounded retries. Workflow rejection and model execution errors stop the run.

## Fair-comparison decisions

- KREA's optional prompt enhancer and Darkbrush LoRA are bypassed in the API workflow.
- HiDream prompt refinement is disabled.
- The supplied prompt is passed literally to every model.
- A nonempty manifest-level negative prompt overrides a model workflow's default; an empty value preserves the tested default.
- Seeds, output sizes, steps, CFG, scheduler, and sampler are recorded in the model configuration and per-output metrics.

## Runtime architecture

The initial path is an interactive RunPod Pod, not Serverless. It is easier to inspect ComfyUI, validate custom nodes, measure actual VRAM, and recover from model-specific failures. Serverless conversion comes only after all five smoke tests pass and runtime behavior is measured.

Preferred GPU class is a single physical 96 GB or larger GPU. VRAM from multiple workers is not pooled for one ComfyUI job. Use one paid Pod at a time and set an explicit termination deadline.

The Dockerfile pins:

- ComfyUI commit `6f3895ed8d1e0f1d5fad11b48b3f159f7de1cc15`
- ComfyUI-KwaiKolorsWrapper commit `6fc1cd9d20bb7537facf180e5494b486b9710e24`

Kolors is the only custom-node dependency. Its model card requires separate attention to commercial-use registration. Review every upstream model and component license before commercial deployment.

## Primary references

- https://docs.comfy.org/tutorials/image/hidream/hidream-o1
- https://huggingface.co/lodestones/Chroma1-HD
- https://huggingface.co/Comfy-Org/Krea-2
- https://huggingface.co/Kwai-Kolors/Kolors
- https://github.com/kijai/ComfyUI-KwaiKolorsWrapper
- https://huggingface.co/Tongyi-MAI/Z-Image
- https://huggingface.co/Comfy-Org/z_image
