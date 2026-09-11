#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="${MODEL_LAB_ROOT:-/workspace/model-lab}"
COMFY_ROOT="${COMFYUI_ROOT:-/opt/ComfyUI}"

/opt/model-lab/scripts/initialize.sh

# Start the official RunPod services before any long-running model downloads.
# This makes SSH and, when JUPYTER_PASSWORD is configured, JupyterLab available
# while the persistent volume is being populated.
/start.sh >>"$LAB_ROOT/runs/runpod-services.log" 2>&1 &
echo "RunPod SSH/Jupyter services starting in the background."

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
  python /opt/model-lab/scripts/download_models.py \
    2>&1 | tee -a "$LAB_ROOT/runs/model-downloads.log"
fi

exec python -u "$COMFY_ROOT/main.py" \
  --listen 0.0.0.0 \
  --port "${COMFYUI_PORT:-8188}" \
  --input-directory "$LAB_ROOT/input" \
  --output-directory "$LAB_ROOT/output" \
  --user-directory "$LAB_ROOT/user" \
  --extra-model-paths-config /opt/model-lab/extra_model_paths.yaml \
  ${COMFYUI_ARGS:---preview-method auto}
