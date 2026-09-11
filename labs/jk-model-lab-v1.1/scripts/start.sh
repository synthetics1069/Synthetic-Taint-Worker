#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="${MODEL_LAB_ROOT:-/workspace/model-lab}"
COMFY_ROOT="${COMFYUI_ROOT:-/opt/ComfyUI}"

mkdir -p \
  "$LAB_ROOT/models/checkpoints" \
  "$LAB_ROOT/models/diffusion_models" \
  "$LAB_ROOT/models/text_encoders" \
  "$LAB_ROOT/models/vae" \
  "$LAB_ROOT/models/loras" \
  "$LAB_ROOT/models/LLM" \
  "$LAB_ROOT/models/diffusers" \
  "$LAB_ROOT/input" \
  "$LAB_ROOT/output" \
  "$LAB_ROOT/runs" \
  "$LAB_ROOT/user/default/workflows" \
  "$LAB_ROOT/.cache/huggingface"

# The Kolors wrapper resolves models_dir directly rather than extra model paths.
# Keep that directory persistent without overwriting a populated container path.
if [[ -L "$COMFY_ROOT/models/diffusers" ]]; then
  ln -sfn "$LAB_ROOT/models/diffusers" "$COMFY_ROOT/models/diffusers"
elif [[ -d "$COMFY_ROOT/models/diffusers" ]] && [[ -z "$(find "$COMFY_ROOT/models/diffusers" -mindepth 1 -print -quit)" ]]; then
  rmdir "$COMFY_ROOT/models/diffusers"
  ln -s "$LAB_ROOT/models/diffusers" "$COMFY_ROOT/models/diffusers"
elif [[ ! -e "$COMFY_ROOT/models/diffusers" ]]; then
  ln -s "$LAB_ROOT/models/diffusers" "$COMFY_ROOT/models/diffusers"
else
  echo "ERROR: $COMFY_ROOT/models/diffusers is populated and cannot be redirected safely." >&2
  exit 1
fi

for workflow in /opt/model-lab/workflows/*.json; do
  cp -n "$workflow" "$LAB_ROOT/user/default/workflows/$(basename "$workflow")"
done

# RunPod no longer exposes a create-time termination flag. When configured,
# use the pod-scoped runpodctl credential injected by RunPod as a hard cost
# guard. The legacy command is intentional: pod-scoped self-removal currently
# works through this surface while the noun-verb equivalent is rejected.
if [[ -n "${SELF_TERMINATE_AFTER_SECONDS:-}" ]]; then
  if [[ ! "${SELF_TERMINATE_AFTER_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: SELF_TERMINATE_AFTER_SECONDS must be a positive integer." >&2
    exit 1
  fi
  if [[ -z "${RUNPOD_POD_ID:-}" ]]; then
    echo "ERROR: RUNPOD_POD_ID is required for the self-termination guard." >&2
    exit 1
  fi
  (
    sleep "${SELF_TERMINATE_AFTER_SECONDS}"
    echo "Self-termination deadline reached; removing Pod ${RUNPOD_POD_ID}."
    runpodctl remove pod "${RUNPOD_POD_ID}"
  ) >>"$LAB_ROOT/runs/self-terminate.log" 2>&1 &
  echo "Self-termination guard armed for ${SELF_TERMINATE_AFTER_SECONDS} seconds."
fi

if [[ "${AUTO_DOWNLOAD_MODELS:-0}" == "1" ]]; then
  python /opt/model-lab/scripts/download_models.py
fi

# Preserve the official RunPod base startup so SSH and the web terminal remain available.
/start.sh &

exec python -u "$COMFY_ROOT/main.py" \
  --listen 0.0.0.0 \
  --port "${COMFYUI_PORT:-8188}" \
  --input-directory "$LAB_ROOT/input" \
  --output-directory "$LAB_ROOT/output" \
  --user-directory "$LAB_ROOT/user" \
  --extra-model-paths-config /opt/model-lab/extra_model_paths.yaml \
  ${COMFYUI_ARGS:---preview-method auto}
