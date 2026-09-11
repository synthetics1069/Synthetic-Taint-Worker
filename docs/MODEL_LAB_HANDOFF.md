# Model Lab Execution Handoff

Prepared: 2026-09-10 UTC  
Package: `JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip`

## Execution Brief

- **CONFIRMED** — Commission a five-model, generation-only ComfyUI lab: HiDream-O1-Image Full, Chroma1-HD, KREA 2 Turbo, Kolors, and Z-Image Base.
- **CONFIRMED** — The experiment contract is 15 J.K.-approved prompts × 5 models × 12 fixed seeds = 900 PNGs, 75 model contact sheets, and 15 prompt comparison sheets.
- **CONFIRMED** — Begin on one interactive RunPod Pod with the existing `ss-model-lab` network volume mounted at `/workspace`. Do not convert to Serverless during commissioning.
- **CONFIRMED** — The package contains five human-readable UI workflows, five independent ComfyUI API workflows, an idempotent model downloader, and an approval-gated/resumable batch runner.
- **CONFIRMED** — Static validation and ZIP integrity pass. Docker build, live ComfyUI node validation, model downloads, GPU inference, and full-run timing are not yet verified.
- **PROPOSED** — The receiving agent should first perform read-only GitHub and RunPod inventory, commit the package and this handoff on a new branch, build/push an immutable image, populate the volume, and run one-image-per-model smoke tests.
- **UNKNOWN** — Live GPU availability/prices, approved spend ceiling, volume ID/size/tier/S3 status, registry/image digest, and repository default branch. The 15 prompt texts are approved.

## 1. Objective and Intended Lab Workflow

| Status | Item |
|---|---|
| **CONFIRMED** | Build a reproducible head-to-head image-generation lab that can be operated by Codex through ComfyUI's HTTP API and inspected by a human through ComfyUI. |
| **CONFIRMED** | Each model has a separate API workflow so an agent can submit work, poll history, retrieve outputs, inspect logs, retry safely, and resume interrupted batches. |
| **CONFIRMED** | A shared approved prompt and the same 12-seed set are applied across all five models. Execution is model-major to reduce checkpoint thrashing; artifacts are organized prompt-major for evaluation. |
| **CONFIRMED** | KREA prompt enhancement/Darkbrush LoRA and HiDream prompt refinement are disabled for literal-prompt comparison. |
| **CONFIRMED** | Wan 2.2 is excluded for a future video lab. Qwen-Image-Edit-2511 and JoyAI-Image-Edit-Plus are excluded for a future editing lab. GLM-Image is deferred to a hybrid-model lab. |
| **PROPOSED** | After commissioning, let Codex run the complete matrix unattended, download the output tree, and prepare evaluation artifacts. |
| **UNKNOWN** | The scoring rubric and whether the final evaluation will be human-only, model-assisted, or hybrid. |

## 2. Confirmed Infrastructure and Existing Resources

| Status | Resource | State |
|---|---|---|
| **CONFIRMED** | GitHub target | `synthetics1069/Synthetic-Taint-Worker` |
| **CONFIRMED** | Existing RunPod endpoint | `Synthetic-Taint-Worker`, endpoint ID `jko7f9190ucjtt` |
| **CONFIRMED** | Existing network volume | Name `ss-model-lab`, data center `EU-RO-1` |
| **CONFIRMED** | Reported authentication | Receiving Codex session has GitHub access, RunPod MCP, and authenticated `runpodctl`; revalidate at execution time. Credential name: `RUNPOD_API_KEY`. |
| **CONFIRMED** | Historical endpoint configuration only | `EU-RO-1`, queue-delay autoscaling at 4 seconds, CUDA minimum 12.0, and RTX PRO 6000 variants were previously visible. This is not live inventory. |
| **CONFIRMED** | Package artifact | `JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip`, 95,045 bytes, SHA-256 `6e72779af97da1d9d10459aa44cca140215297a866dec5e49c4497dfd62703f7` |
| **UNKNOWN** | Volume details | Volume ID, allocated size, used size, storage tier, S3 compatibility, and attachment state must be queried live. |
| **UNKNOWN** | Account state | Balance, quotas, current paid resources, current GPU stock, and current prices must be queried live. |

## 3. Repository, Branch, Image, Templates, Endpoints, Volumes, Mount Paths, and IDs

| Status | Field | Value |
|---|---|---|
| **CONFIRMED** | Repository | `synthetics1069/Synthetic-Taint-Worker` |
| **UNKNOWN** | Default branch and visibility | Resolve with GitHub before mutation. |
| **PROPOSED** | Working branch | `codex/model-lab-v1.1` |
| **PROPOSED** | Repository package path | `labs/jk-model-lab-v1.1/` |
| **PROPOSED** | Repository handoff path | `docs/MODEL_LAB_HANDOFF.md` |
| **PROPOSED** | Image tag | `ghcr.io/synthetics1069/synthetic-taint-worker:jk-model-lab-v1.1.0` |
| **UNKNOWN** | Image digest and registry authorization ID | Record after push/configuration. Do not deploy `latest`. |
| **CONFIRMED** | Docker base | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` |
| **CONFIRMED** | ComfyUI pin | `6f3895ed8d1e0f1d5fad11b48b3f159f7de1cc15` |
| **CONFIRMED** | Kolors wrapper pin | Repository `https://github.com/kijai/ComfyUI-KwaiKolorsWrapper.git`, commit `6fc1cd9d20bb7537facf180e5494b486b9710e24` |
| **CONFIRMED** | Existing endpoint ID | `jko7f9190ucjtt`; leave unchanged during Pod commissioning. |
| **CONFIRMED** | Volume name/DC | `ss-model-lab` / `EU-RO-1` |
| **UNKNOWN** | Volume ID | Resolve live; never substitute the volume name where an ID is required. |
| **CONFIRMED** | Pod volume mount | `/workspace` |
| **CONFIRMED** | Lab root | `/workspace/model-lab` |
| **CONFIRMED** | Models/cache/input/output/user paths | `/workspace/model-lab/models`, `/workspace/model-lab/.cache/huggingface`, `/workspace/model-lab/input`, `/workspace/model-lab/output`, `/workspace/model-lab/user` |
| **CONFIRMED** | Container application paths | ComfyUI `/opt/ComfyUI`; lab package `/opt/model-lab` |
| **UNKNOWN** | Pod/template IDs and proxy URL | Create only after approval; record exact IDs. Expected proxy form is `https://<POD_ID>-8188.proxy.runpod.net`. |

## 4. Pod Versus Serverless Decisions and Reasoning

| Status | Decision |
|---|---|
| **CONFIRMED** | Initial commissioning uses one interactive GPU Pod. It exposes ComfyUI, supports SSH/log inspection, and avoids serverless cold-start and queue ambiguity while dependencies are still being proven. |
| **CONFIRMED** | The current container starts ComfyUI directly. It is not yet packaged with a RunPod Serverless queue handler. |
| **CONFIRMED** | Multiple serverless workers increase concurrency; they do not pool VRAM for one workflow. Every single generation must fit on one worker GPU. |
| **PROPOSED** | Keep endpoint `jko7f9190ucjtt` unchanged/scaled to zero. Revisit Serverless only after five smoke tests, measured startup/runtime/VRAM, and a frozen request/response contract. |
| **UNKNOWN** | Final production topology: interactive Pod, load-balanced HTTP, or queue Serverless. Determine from measured duration, desired concurrency, and cold-start cost. |

## 5. Models, Workflows, Datasets, and Experiment Matrix

| Status | Model | Packaged setup |
|---|---|---|
| **CONFIRMED** | HiDream-O1-Image Full | `Comfy-Org/HiDream-O1-Image`, `hidream_o1_image_fp8_scaled.safetensors`; 2048×2048, 40 steps, CFG 5.0. |
| **CONFIRMED** | Chroma1-HD | `Comfy-Org/Chroma1-HD_repackaged`, FP8 diffusion model, T5 FP8 encoder, shared `ae.safetensors`; 1024×1024, 26 steps, CFG 3.5. |
| **CONFIRMED** | KREA 2 Turbo | `Comfy-Org/Krea-2`, FP8 diffusion model, Qwen3-VL 4B FP8 encoder, Qwen image VAE; 1024×1024, 8 steps, CFG 1.0. |
| **CONFIRMED** | Kolors | `Kwai-Kolors/Kolors`, FP16 UNet, ChatGLM3 quant8, fixed SDXL VAE, pinned KwaiKolors wrapper; 1024×1024, 25 steps, CFG 5.0. |
| **CONFIRMED** | Z-Image Base | `Comfy-Org/z_image`, `z_image_bf16.safetensors`, Qwen3 4B encoder, shared `ae.safetensors`; 1024×1024, 30 steps, CFG 4.0. |
| **CONFIRMED** | Workflow set | Five UI JSONs in `workflows/`; five API JSONs in `api_workflows/`; pinned upstream examples retained in `workflow_sources/`. |
| **CONFIRMED** | Matrix | 15 prompts × 5 models × 12 unique fixed seeds = 900 images. Seed order: `104729`, `130363`, `155921`, `181081`, `205759`, `230969`, `256019`, `281117`, `306239`, `331337`, `356387`, `381481`. |
| **CONFIRMED** | Prompt dataset state | J.K. approved protocol `1.0.0` on 2026-09-11. `experiments/prompt_manifest.json` contains 15 approved prompts, categories, test intents and failure signals. SHA-256: `ee34b067c62bebdf315d5bb766458a98db7643729c85edb35a683262f044202d`. |
| **CONFIRMED** | Canonical prompt protocol | `docs/MODEL_LAB_PROMPTS_AND_EXECUTION.md`; adult-age normalization, empty manifest-level negative prompts, fixed seeds, assistance restrictions and execution gates are approved. |

## 6. Required Inputs and Expected Outputs

| Status | Type | Detail |
|---|---|---|
| **CONFIRMED** | Required package | The ZIP identified in Section 2. |
| **CONFIRMED** | Required experiment input | Fifteen nonempty prompt records, each marked `APPROVED`, plus top-level `manifest_status: APPROVED`. Optional negative prompts may be supplied. |
| **CONFIRMED** | Credentials by name only | `RUNPOD_API_KEY`; `HF_TOKEN` if Hugging Face requires it; `GH_TOKEN` for GitHub if needed; `CR_PAT` if private GHCR access is required; `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` only if RunPod S3 access is deliberately used. |
| **CONFIRMED** | Expected primary output | 900 valid PNGs and per-image timing/seed/Comfy prompt-ID records. |
| **CONFIRMED** | Expected derived output | 75 `contact_sheet.jpg` files, 15 `Prompt_NN__comparison.jpg` files, 75 `metrics.json` files, manifest/model snapshots, and `run_state.json`. |
| **PROPOSED** | Commissioning report | Record image digest, Pod/GPU/DC, cold start, download sizes, per-model runtime, peak VRAM, failures/retries, and teardown confirmation. |
| **UNKNOWN** | Final local download destination and evaluator | J.K. must specify where the completed tree should be downloaded and how it will be scored. |

## 7. Exact Commands Already Verified

- **CONFIRMED** — These commands completed successfully in the package authoring environment:

```bash
python -m py_compile scripts/download_models.py scripts/run_lab.py scripts/verify_package.py
bash -n scripts/start.sh
python scripts/verify_package.py
python scripts/run_lab.py --help
```

- **CONFIRMED** — Static verifier output:

```text
PASS: 5 models, 5 UI workflows, 5 API workflows, 15 approved prompts, 12 fixed seeds, 900 planned images
```

- **CONFIRMED** — Every JSON file in `model_manifest.json`, `experiments/`, `api_workflows/`, `workflows/`, and `workflow_sources/` passed `jq empty`.
- **CONFIRMED** — Archive verification completed with:

```bash
unzip -t JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip
sha256sum JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip
```

```text
No errors detected in compressed data of JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip.
6e72779af97da1d9d10459aa44cca140215297a866dec5e49c4497dfd62703f7  JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip
```

- **CONFIRMED** — Docker was not installed in the authoring environment (`docker: command not found`). No Docker or live-GPU claim is made.

## 8. Proposed Provisioning and Execution Commands

- **PROPOSED** — First run read-only inventory and confirm live CLI syntax:

```bash
gh auth status
gh repo view synthetics1069/Synthetic-Taint-Worker --json nameWithOwner,defaultBranchRef,isPrivate,url
runpodctl version
runpodctl user
runpodctl pod create --help
runpodctl network-volume list
runpodctl serverless list
runpodctl serverless get jko7f9190ucjtt
runpodctl gpu list --include-unavailable
runpodctl datacenter list
runpodctl ssh list-keys
runpodctl billing pods
runpodctl billing serverless
runpodctl billing network-volume
```

- **PROPOSED** — Use RunPod MCP structured list/get operations for the same inventory where supported. Record timestamps; never rely on the earlier screenshots for stock.
- **PROPOSED** — Place the files in GitHub without overwriting unrelated work:

```bash
git clone https://github.com/synthetics1069/Synthetic-Taint-Worker.git
cd Synthetic-Taint-Worker
git switch -c codex/model-lab-v1.1
mkdir -p labs/jk-model-lab-v1.1 docs
unzip /absolute/path/JK_Model_Lab_v1.1.0_RunPod_ComfyUI.zip -d /tmp/jk-model-lab-v1.1
cp -a /tmp/jk-model-lab-v1.1/JK_Model_Lab_v1.1/. labs/jk-model-lab-v1.1/
cp /absolute/path/MODEL_LAB_HANDOFF.md docs/MODEL_LAB_HANDOFF.md
python labs/jk-model-lab-v1.1/scripts/verify_package.py
git status --short
```

- **PROPOSED** — Build and push after registry approval:

```bash
export MODEL_LAB_IMAGE='ghcr.io/synthetics1069/synthetic-taint-worker:jk-model-lab-v1.1.0'
echo "$CR_PAT" | docker login ghcr.io -u synthetics1069 --password-stdin
docker buildx build --platform linux/amd64 --check labs/jk-model-lab-v1.1
docker buildx build --platform linux/amd64 -t "$MODEL_LAB_IMAGE" --push labs/jk-model-lab-v1.1
docker buildx imagetools inspect "$MODEL_LAB_IMAGE"
```

- **PROPOSED** — After a prep Pod or approved GPU Pod mounts the resolved network volume at `/workspace`, populate weights idempotently:

```bash
python /opt/model-lab/scripts/download_models.py
du -sh /workspace/model-lab/models /workspace/model-lab/.cache/huggingface
python /opt/model-lab/scripts/download_models.py
```

- **PROPOSED** — Confirm exact flags with live `runpodctl pod create --help`; then adapt this representative command without guessing IDs:

```bash
runpodctl pod create \
  --name jk-model-lab-v1-1 \
  --image "$MODEL_LAB_IMAGE" \
  --gpu-id '<EXACT_LIVE_GPU_TYPE_ID>' \
  --ports '8188/http,22/tcp' \
  --network-volume-id '<VOLUME_ID>' \
  --volume-mount-path /workspace \
  --env '{"AUTO_DOWNLOAD_MODELS":"0","MODEL_LAB_ROOT":"/workspace/model-lab","HF_HOME":"/workspace/model-lab/.cache/huggingface","COMFYUI_PORT":"8188","SELF_TERMINATE_AFTER_SECONDS":"14400"}'
```

- **PROPOSED** — Once the Pod is healthy and the prompt manifest is approved:

```bash
curl -sf http://127.0.0.1:8188/system_stats
python /opt/model-lab/scripts/run_lab.py --smoke
python /opt/model-lab/scripts/run_lab.py --prompt Prompt_01
python /opt/model-lab/scripts/run_lab.py
```

- **PROPOSED** — Commit/push after static validation and image build; do not merge without J.K.'s approval:

```bash
git add labs/jk-model-lab-v1.1 docs/MODEL_LAB_HANDOFF.md
git commit -m 'Add JK Model Lab v1.1 generation benchmark'
git push -u origin codex/model-lab-v1.1
```

## 9. Artifact/Output Storage and Naming Conventions

| Status | Convention |
|---|---|
| **CONFIRMED** | Root | `/workspace/model-lab/output/Model_Lab_01/` |
| **CONFIRMED** | Prompt folder | `Prompt_01` through `Prompt_15` |
| **CONFIRMED** | Model folders | `hidream_o1_full`, `chroma1_hd`, `krea2_turbo`, `kolors`, `z_image_base` |
| **CONFIRMED** | Image filename | `Prompt_NN__<model_slug>__Image_NN__seed-<seed>.png` |
| **CONFIRMED** | Per-model artifacts | Twelve PNGs, `metrics.json`, `contact_sheet.jpg` |
| **CONFIRMED** | Per-prompt comparison | `Prompt_NN__comparison.jpg` |
| **CONFIRMED** | Run control | Root `prompt_manifest.snapshot.json`, `models.snapshot.json`, and atomic `run_state.json` |
| **CONFIRMED** | GitHub exclusions | Never commit model weights, HF cache, personal/private inputs, generated outputs, or credentials. |
| **PROPOSED** | Retrieval | Download the complete `Model_Lab_01` directory only after counts and checksums pass; preserve it unchanged as the raw benchmark artifact. |
| **UNKNOWN** | S3 path | Use only if the volume actually has S3 compatibility and J.K. approves credentials/transfer. |

## 10. GPU Selection Logic and Fallback Order

| Priority | Status | Choice |
|---:|---|---|
| 1 | **PROPOSED** | One available RTX PRO 6000 WK / RTX PRO 6000 Blackwell 96 GB in the volume's data center. |
| 2 | **PROPOSED** | Another single 96 GB RTX PRO 6000 variant in the same data center; Max-Q may trade speed for availability. |
| 3 | **PROPOSED** | One H100 NVL 94 GB or H200 141 GB in the same data center, if price is approved. |
| 4 | **PROPOSED** | One A100 SXM 80 GB or H100 SXM 80 GB in the same data center, subject to a model-by-model smoke test and measured headroom. |
| 5 | **PROPOSED** | Move to another data center only if storage can be recreated/synchronized there and J.K. explicitly approves the latency, transfer, and storage implications. |
| — | **CONFIRMED** | Do not substitute multiple L4/24 GB workers and describe their aggregate memory as one 96 GB GPU. Workers are independent. |
| — | **UNKNOWN** | Actual peak VRAM and throughput for every packaged workflow. Measure on the selected physical GPU before a full run. |

## 11. Cost Limits, Automatic Termination, and Teardown Requirements

| Status | Requirement |
|---|---|
| **CONFIRMED** | No paid Pod may be created without J.K. approving the GPU, current hourly rate, maximum runtime, and maximum estimated spend. |
| **CONFIRMED** | Only one paid prep/commissioning Pod may run at a time. Check for existing paid resources before creating another. |
| **CONFIRMED** | Every Pod creation must include `SELF_TERMINATE_AFTER_SECONDS` as an explicit termination deadline. Current RunPod MCP and `runpodctl pod create` schemas do not expose the former native stop/terminate flags, so the container uses the injected pod-scoped CLI credential to remove itself at the deadline. Never rely on memory or a browser tab. |
| **PROPOSED** | Initial caps: at most two hours for volume preparation and at most four hours for build/smoke commissioning, each subject to J.K.'s approval. |
| **UNKNOWN** | Full 900-image cap. Calculate from measured per-model smoke throughput plus margin and obtain approval before starting. |
| **CONFIRMED** | On success or a stop condition, terminate the Pod, confirm billing has stopped, and preserve the network volume. |
| **CONFIRMED** | Do not delete the volume, endpoint, image, template, or Git branch unless J.K. explicitly approves that destructive action. |

## 12. Verification Tests Proving the Container and Workflow Work

| Stage | Status | Acceptance test |
|---|---|---|
| Static package | **CONFIRMED** | `python scripts/verify_package.py` passes; all JSON parses; ZIP test/hash match Section 7. |
| Image build | **PROPOSED** | `linux/amd64` Docker build succeeds, starts with no dependency traceback, and records an immutable digest. |
| Persistence | **PROPOSED** | Model download completes, rerun skips present assets, and restart retains models/user/output on the volume. |
| Comfy readiness | **PROPOSED** | `/system_stats` and `/object_info` respond; runner preflight finds every required node class, including Kolors custom nodes. |
| Per-model smoke | **PROPOSED** | `run_lab.py --smoke` creates exactly one valid PNG from each model with expected dimensions, filename, metrics, and no execution error. |
| Fairness | **PROPOSED** | Inspect submitted API graphs/logs to confirm identical prompt text/seed and disabled prompt enhancement; record each model's native defaults. |
| Resume | **PROPOSED** | Interrupt after at least one valid image, rerun, and confirm valid files are skipped while missing work resumes without duplicate images. |
| Prompt_01 batch | **PROPOSED** | Produce 60 images, five contact sheets, one prompt comparison, and complete metrics before authorizing the remaining prompts. |
| Full matrix | **PROPOSED** | Count exactly 900 valid PNGs, 75 contact sheets, 15 comparison sheets, and 900 completed records; no corrupt/zero-byte outputs. |
| Teardown | **PROPOSED** | Pod is terminated, billing ceases, volume remains attached/available, and commissioning report records final state. |

## 13. Failure Handling and Safe Retry Rules

| Status | Rule |
|---|---|
| **CONFIRMED** | Runner retries only timeouts, network errors, and HTTP 5xx conditions; default maximum is two attempts with exponential delay. |
| **CONFIRMED** | HTTP 400/401/403/404, workflow rejection, missing nodes/models, Comfy execution errors, corrupt existing outputs, or unexpected image counts are permanent stop conditions. |
| **CONFIRMED** | Valid existing PNGs are verified and skipped. Metrics/state use atomic replacement. Do not delete successful outputs to make a retry look clean. |
| **CONFIRMED** | Models are explicitly unloaded between model families. A memory-release warning is logged but does not erase work. |
| **PROPOSED** | On CUDA OOM: stop that model, save logs/system stats, try one clean process/Pod restart, then change GPU/offload/workflow only with an explicitly versioned configuration. |
| **PROPOSED** | On dependency failure: pin the smallest necessary change, rebuild under a new image tag, rerun static plus affected-model smoke tests, and record the delta. |
| **PROPOSED** | On capacity unavailability: leave work queued only if the approved cost/window remains valid; otherwise stop and ask J.K. before changing DC or GPU class. |
| **CONFIRMED** | Never create a second paid Pod as an automatic recovery while another paid Pod exists. |

## 14. Actions Requiring J.K.'s Approval or Manual Intervention

| Status | Action |
|---|---|
| **CONFIRMED** | Completed: J.K. supplied/approved the 15 prompt texts, empty manifest-level negative prompts, categories, intents and failure signals on 2026-09-11. |
| **CONFIRMED** | Approve GPU type, live hourly rate, termination time, and maximum spend for prep, smoke, and full run. |
| **CONFIRMED** | Approve creating/replacing/deleting RunPod Pods, templates, endpoints, volumes, registry authorizations, or S3 credentials. Read-only inventory does not require approval. |
| **CONFIRMED** | Complete/approve any Kwai Kolors commercial-use registration or license review before commercial use. |
| **CONFIRMED** | Manually resolve any Hugging Face gating/terms acceptance if encountered; use credential name `HF_TOKEN`, never its value in artifacts. |
| **CONFIRMED** | Approve pushing a public container image, opening/merging a PR, or merging directly to the repository default branch. |
| **CONFIRMED** | Approve moving the experiment to a different data center or copying the persistent dataset/weights across regions. |
| **UNKNOWN** | Whether S3 compatibility is wanted for retrieval. The batch can run using the mounted filesystem alone. |

## 15. Completed Work, Current State, Immediate Next Action, and Unresolved Questions

| Status | Item |
|---|---|
| **CONFIRMED** | Completed: v1.1 package rebuilt as generation-only; Z-Image Base, KREA 2 Turbo, and Kolors added; Wan/edit/GLM removed or deferred; separate UI/API workflows created. |
| **CONFIRMED** | Completed: model manifest/downloader, persistent mount wiring, fixed seed set, approved 15-prompt protocol and executable manifest, resumable batch runner, metrics, contact sheets, comparison sheets, verifier, README, version, and changelog. |
| **CONFIRMED** | Current state: Python/shell/static JSON/package/ZIP checks pass. No Docker build, model download, Comfy boot, custom-node runtime preflight, GPU generation, RunPod mutation, GitHub commit, or full experiment has occurred from this package. |
| **PROPOSED** | Immediate next action: receiving agent performs read-only GitHub/RunPod inventory and reports exact live resource IDs, stock, prices, balance, and branch/registry state before any paid mutation. |
| **PROPOSED** | After inventory and approval: commit package/handoff, build/push the image, populate the volume, then run one-image-per-model smoke tests. |
| **UNKNOWN** | Volume ID/size/tier/S3 state; live GPU stock/prices; account balance; repository branch/visibility; final registry/image digest; approved cost ceilings; Kolors commercial registration state; full-run duration; peak VRAM; and local artifact download destination. |

## Source References

- **CONFIRMED** — HiDream: https://docs.comfy.org/tutorials/image/hidream/hidream-o1
- **CONFIRMED** — Chroma1-HD: https://huggingface.co/lodestones/Chroma1-HD
- **CONFIRMED** — KREA 2 package: https://huggingface.co/Comfy-Org/Krea-2
- **CONFIRMED** — Kolors: https://huggingface.co/Kwai-Kolors/Kolors
- **CONFIRMED** — Kolors ComfyUI wrapper: https://github.com/kijai/ComfyUI-KwaiKolorsWrapper
- **CONFIRMED** — Z-Image upstream: https://huggingface.co/Tongyi-MAI/Z-Image
- **CONFIRMED** — Z-Image ComfyUI split files: https://huggingface.co/Comfy-Org/z_image
